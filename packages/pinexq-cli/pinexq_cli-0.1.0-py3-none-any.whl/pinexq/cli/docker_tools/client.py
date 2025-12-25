import json
import os
import subprocess
from typing import Optional, Union

import docker
from docker import DockerClient
from docker.errors import APIError
from docker.models.images import Image
from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn, DownloadColumn, TransferSpeedColumn, \
    TaskID
from rich.console import Console

from pinexq.cli.pinexq_tools.info import Info
from pinexq.cli.utils.const import DOCKER_PREFIX as PREFIX

err_console = Console(stderr=True)
console = Console(highlight=False)


def print_stream_logs(logs):
    try:
        for chunk in logs or []:
            line = chunk.get('stream')
            if line and line != '\n':
                console.print(f"{line.rstrip()}")
    except Exception:
        pass


def print_push_logs(logs):
    """Render docker push logs using rich progress bars per layer id."""
    try:
        layer_tasks: dict[str, TaskID] = {}
        finished_layers: set[str] = set()

        progress = Progress(
            TextColumn("{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            transient=True,
        )

        with progress:
            for chunk in logs or []:
                status = chunk.get('status')
                layer_id = chunk.get('id')
                detail = chunk.get('progressDetail') or {}
                total = detail.get('total')
                current = detail.get('current')

                # If no layer id, print general status when not mid-push UI
                if not layer_id:
                    if status:
                        print(f"{status.rstrip()}")
                    continue

                # Ensure a task exists for this layer
                if layer_id not in layer_tasks:
                    desc = f"Waiting {layer_id}"
                    task_id = progress.add_task(desc, total=total if total else 1, completed=0)
                    layer_tasks[layer_id] = task_id

                task_id = layer_tasks[layer_id]

                if status == 'Waiting':
                    progress.update(task_id, description=f"Waiting {layer_id}")
                    continue

                if status == 'Pushing':
                    if total and current is not None:
                        progress.update(task_id, total=total, completed=current, description=f"Pushing {layer_id}")
                    elif current is not None:
                        # Unknown total; treat as indeterminate with growing total
                        progress.update(task_id, total=None, completed=current, description=f"Pushing {layer_id}")
                    else:
                        progress.update(task_id, description=f"Pushing {layer_id}")
                    continue

                if status == 'Pushed':
                    if total:
                        progress.update(task_id, total=total, completed=total, description=f"Pushed  {layer_id}")
                    else:
                        progress.update(task_id, total=1, completed=1, description=f"Pushed  {layer_id}")
                    finished_layers.add(layer_id)
                    continue

                if status == 'Layer already exists' or (isinstance(status, str) and status.startswith('Mounted from')):
                    progress.update(task_id, total=1, completed=1, description=f"Exists  {layer_id}")
                    finished_layers.add(layer_id)
                    continue

                # Fallback update to show any other status
                if status:
                    progress.update(task_id, description=f"{status} {layer_id}")
    except Exception as e:
        err_console.print(e)
        pass


class ContainerClient:
    def __init__(self, client: DockerClient):
        self.client = client

    def pre_build_image(self, context_dir: str, dockerfile: str, tag: str, verbose=True, secrets=None) -> \
            Optional[Image]:
        if secrets is None:
            secrets = []
        secrets_arg = [arg for secret in secrets for arg in ('--secret', secret)]
        command = ['docker', 'build', '--progress', 'plain', '-t', tag, '-f', dockerfile, *secrets_arg, context_dir]
        return self.build_image(command, tag, verbose)

    def build_base_image(self, context_dir: str, dockerfile: str, tag: str, verbose=True, secrets=None) -> Optional[
        Image]:
        # We need to directly build the docker image since buildkit is not supported by docker-py
        # https://github.com/docker/docker-py/issues/2230
        if secrets is None:
            secrets = []
        secrets_arg = [arg for secret in secrets for arg in ('--secret', secret)]
        command = ['docker', 'build', '--progress', 'plain',
                   '--platform', 'linux/amd64',
                   '-t', tag, '-f', dockerfile, *secrets_arg, context_dir]
        return self.build_image(command, tag, verbose)

    def build_image(self, command: list[str], tag: str, verbose=True) -> Optional[Image]:
        console.print(f"{PREFIX} Running docker build command: {' '.join(command)}")
        with subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=os.environ,
        ) as process:
            import time
            message = f"{PREFIX} [bold dodger_blue1]Waiting for docker...[/]"
            collected = [message]
            with console.status(message, spinner="dots") as status:
                def verbose_log():
                    for line in process.stdout:
                        collected.append(line.strip())
                        status.update('\n'.join(collected))
                        time.sleep(0.01)

                def log():
                    for line in process.stdout:
                        status.update(f'{message}: {line.strip()}')
                        time.sleep(0.01)

                verbose_log() if verbose else log()
            if verbose:
                console.print('\n'.join(collected))
        return_code = process.poll()
        if return_code == 0:
            return self.client.images.get(tag)
        else:
            err_console.print(f"{PREFIX} Docker build failed with return code {return_code}")
            return None

    @staticmethod
    def tag_base_image_as_function(image: Image, info: Info, function_name: str, function_version: str) -> bool:
        dist_tag = f"{info.registry_endpoint}/{info.get_context_id()}/{function_name}:{function_version}"
        try:
            image.tag(repository=dist_tag)
            console.print(f"{PREFIX} Tagged image {image.id} as {dist_tag}")
            return True
        except APIError as e:
            err_console.print(f"{PREFIX} Docker API error: {e}")
            return False

    def push_function_image(self, info: Info, function_name: str, function_version: str) -> Union[str, None]:
        repo = f"{info.registry_endpoint}/{info.get_context_id()}/{function_name}"
        try:
            push_logs = self.client.images.push(repo, tag=function_version, auth_config=info.get_docker_auth(),
                                                stream=True, decode=True)
            print_push_logs(push_logs)
            console.print(f"{PREFIX} Pushed function image {repo}:{function_version}")
            image = self.client.images.get(f'{repo}:{function_version}')
            return self.get_image_digest(image)
        except APIError as e:
            err_console.print(f"{PREFIX} Docker API error: {e}")
            return None

    def run_function_list(self, image: Image, entrypoint: str = 'main.py') -> list[str] | None:
        try:
            output_bytes = self.client.containers.run(image.id, f'{entrypoint} list -j', detach=False, remove=True)
            output_str = output_bytes.decode("utf-8").strip()
            return json.loads(output_str)
        except docker.errors.ContainerError as e:
            err_console.print(f"Container exited with non-zero exit code: {e.exit_status}")
            err_console.print(f"Stderr: {e.stderr}")
        except docker.errors.ImageNotFound:
            err_console.print("Image not found locally.")
        except docker.errors.APIError as e:
            err_console.print(f"Docker API Error: {e}")

    def run_manifest(self, image: Image, function: str, entrypoint: str = 'main.py') -> dict | None:
        try:
            output_bytes = self.client.containers.run(image.id, f'{entrypoint} signature --function {function} -j',
                                                      detach=False, remove=True)
            output_str = output_bytes.decode("utf-8").strip()
            return json.loads(output_str)
        except docker.errors.ContainerError as e:
            err_console.print(f"Container exited with non-zero exit code: {e.exit_status}")
            err_console.print(f"Stderr: {e.stderr}")
        except docker.errors.ImageNotFound:
            err_console.print("Image not found locally.")
        except docker.errors.APIError as e:
            err_console.print(f"Docker API Error: {e}")

    @staticmethod
    def get_image_digest(image: Image) -> str | None:
        # Hack to get the correct image digest for docker v2 manifests version
        repo_digests = image.attrs.get('RepoDigests')
        if not repo_digests:
            return image.id
        return repo_digests[0].split('@')[-1] if len(repo_digests) > 0 else image.id


def load_docker_client() -> ContainerClient:
    try:
        client = docker.from_env()
        return ContainerClient(client)
    except Exception as e:
        err_console.print(f'cannot connect to docker socket: {e}')
        exit(1)
