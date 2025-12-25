import json
import os
from pathlib import Path

from docker.models.images import Image

from pinexq.cli.docker_tools.client import ContainerClient


def generate_manifest_signature(container_client: ContainerClient, base_image: Image, function_name: str,
                                entrypoint: str) -> dict:
    return container_client.run_manifest(base_image, function_name, entrypoint=entrypoint)


def generate_manifests(container_client: ContainerClient, functions: list[str], base_image: Image,
                       entrypoint: str) -> dict:
    manifests = {}
    for function_name in functions:
        signature = generate_manifest_signature(container_client, base_image, function_name, entrypoint)
        manifests[function_name] = signature
        os.makedirs('.manifests', exist_ok=True)
        manifest_path = Path('.manifests') / f"{signature['function_name']}.json"
        with open(manifest_path, 'w') as f:
            json.dump(signature, f, indent=2)
    return manifests
