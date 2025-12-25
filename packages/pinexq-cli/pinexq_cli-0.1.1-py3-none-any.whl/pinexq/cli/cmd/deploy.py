from __future__ import annotations

import subprocess
from dataclasses import dataclass, field

from pinexq_client.core import ApiException
from pinexq_client.core.hco.upload_action_hco import UploadParameters
from pinexq_client.job_management import enter_jma, EntryPointHco, ProcessingStepsRootHco
from pinexq_client.job_management.model import CreateProcessingStepParameters, ConfigureDeploymentParameters, \
    ScalingConfiguration, ScalingBehaviours, AssignCodeHashParameters
from rich.console import Console

from pinexq.cli.docker_tools.client import ContainerClient
from pinexq.cli.pinexq_tools.client import get_client
from pinexq.cli.pinexq_tools.info import get_info
from pinexq.cli.pinexq_tools.manifest import generate_manifests
from pinexq.cli.pinexq_tools.project import PinexqProjectConfig
from pinexq.cli.utils.const import PINEXQ_PREFIX as PREFIX, PINEXQ_ERROR_PREFIX as ERROR_PREFIX

err_console = Console(stderr=True)
console = Console(highlight=False)


def is_uv_lockfile_up_to_date() -> bool:
    result = subprocess.run(
        ['uv', 'lock', '--check'],
        cwd='.',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.returncode == 0


@dataclass
class DeployOptions:
    dockerfile: str = "./Dockerfile"
    context_dir: str = "./"
    api_key: str = ""
    functions: list[str] = field(default_factory=list)
    secrets: list[str] = field(default_factory=list)


def deploy(deploy_command: DeployOptions, container_client: ContainerClient, config: PinexqProjectConfig):
    try:
        pinexq_client = get_client(config.project.endpoint, deploy_command.api_key)
        info = get_info(pinexq_client)
        if 'grant:codeContributor' not in info.user_grants and 'role:admin' not in info.user_grants:
            err_console.print(
                f'{ERROR_PREFIX} You do not have permission to deploy functions. Please ask your administrator or support to grant you the permission.')
            exit(1)
        if not is_uv_lockfile_up_to_date():
            err_console.print(f'{ERROR_PREFIX} uv lockfile is not up to date. Please run `uv lock` to update it.')
            exit(1)

        # Generate manifests
        # We are building the image for the current execution context to generate manifests
        # This will build for the local architecture to make sure the manifest generation can be executed locally
        base_image = container_client.pre_build_image(deploy_command.context_dir, deploy_command.dockerfile,
                                                      f'{config.project.name}:{config.project.version}',
                                                      secrets=deploy_command.secrets)
        if not base_image:
            console.print(f'{ERROR_PREFIX} Failed to build base image.')
            exit(1)
        container_functions = container_client.run_function_list(base_image, entrypoint=config.project.entrypoint)
        if not container_functions:
            err_console.print(f'{ERROR_PREFIX} Failed to list functions in procon.')
        console.print(f'{PREFIX} Found following functions in container: {container_functions}')
        if len(deploy_command.functions) == 0:
            functions = container_functions
        else:
            console.print(f'{PREFIX} Functions specified in command line: {deploy_command.functions}')
            functions = [f for f in container_functions if f in deploy_command.functions]
        manifests = generate_manifests(container_client, functions, base_image, config.project.entrypoint)
        if not manifests:
            err_console.print(f'{ERROR_PREFIX} Failed to list functions in procon.')
        console.print(f'{PREFIX} Deploying following functions: {functions}')

        # This will build the base image again for the destination architecture amd64
        base_image = container_client.build_base_image(deploy_command.context_dir, deploy_command.dockerfile,
                                                       f'{config.project.name}:{config.project.version}',
                                                       secrets=deploy_command.secrets)
        if not base_image:
            console.print(f'{ERROR_PREFIX} Failed to build base image.')
            exit(1)

        # Start registering the PS
        entrypoint: EntryPointHco = enter_jma(pinexq_client)
        console.print(f'{PREFIX} Registering function at {config.project.endpoint}')
        processing_step_root: ProcessingStepsRootHco = entrypoint.processing_step_root_link.navigate()

        processing_step = None
        for function_name in functions:
            version = manifests[function_name]['version']
            console.print(f'{PREFIX} Deploying function {function_name}:{version}')
            try:
                params = CreateProcessingStepParameters(FunctionName=function_name, Title=function_name,
                                                        Version=version)
                processing_step = processing_step_root.register_new_action.execute(params)
                processing_step.upload_configuration_action.execute(
                    UploadParameters(filename='UploadFile', mediatype='application/json',
                                     json=manifests[function_name]))
            except ApiException as e:
                if e.problem_details.detail == 'A processing step with the same function name already exists.':
                    console.print(
                        f'{PREFIX} Processing step for function {function_name}:{version} in version [bold dark_orange]{version}[/bold dark_orange] already exists. Skipping deployment.')
                    continue
                else:
                    err_console.print(
                        f'{ERROR_PREFIX} Error registering processing step for function {function_name}:{version}:')
                    exit(1)

            # Push image to registry
            if not container_client.tag_base_image_as_function(base_image, info, function_name, version):
                exit(1)
            digest = container_client.push_function_image(info, function_name, version)
            if not digest:
                console.print(f'{ERROR_PREFIX} Failed to push function image for {function_name}:{version}')
                exit(1)
            deployment = config.get_function_deployment(function_name)
            processing_step.self_link.navigate().assign_code_hash_action.execute(
                AssignCodeHashParameters(CodeHash=digest))
            processing_step.self_link.navigate().configure_deployment_action.execute(
                ConfigureDeploymentParameters(
                    ResourcePreset=deployment.resource_preset,
                    Entrypoint=config.project.entrypoint,
                    Scaling=ScalingConfiguration(
                        MaxReplicas=deployment.max_replicas,
                        Behaviour=ScalingBehaviours.balanced
                    ),
                )
            )


    except Exception as e:
        err_console.print(f'{ERROR_PREFIX} Error: {e}')
        exit(1)
