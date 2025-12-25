from typing import Tuple, Union
import click
import tomli
from pinexq_client.job_management.model import DeploymentResourcePresets
from pydantic import BaseModel, Field, field_validator

from pinexq.cli.utils.const import PINEXQ_ERROR_PREFIX as ERROR_PREFIX


class PinexqDeploymentSetting(BaseModel):
    resource_preset: DeploymentResourcePresets
    max_replicas: int


class PinexqProjectDetails(BaseModel):
    name: str = Field(None, alias="name")
    endpoint: str = Field(None, alias="pinexq_endpoint")
    entrypoint: str = Field('main.py')
    version: str = Field(None)

    @field_validator('entrypoint')
    @classmethod
    def validate_entrypoint(cls, v: str) -> str:
        if not v.endswith(('.py', '.pyc')):
            raise ValueError("entrypoint must have a python extension")
        return v


class PinexqProjectConfig(BaseModel):
    # read from pinexq.toml
    project: PinexqProjectDetails = Field(None)
    deployment: PinexqDeploymentSetting = Field(None)
    functions: dict[str, PinexqDeploymentSetting] = Field({}, alias="function")

    # read from pyproject.toml

    def get_function_deployment(self, function_name: str) -> PinexqDeploymentSetting:
        function_config = self.functions.get(function_name)
        resource_preset = function_config.resource_preset if function_config else self.deployment.resource_preset
        max_replicas = function_config.max_replicas if function_config else self.deployment.max_replicas
        return PinexqDeploymentSetting(resource_preset=resource_preset, max_replicas=max_replicas)


def get_project_meta() -> PinexqProjectConfig:
    [py_project_name, version] = _read_pyproject_toml()
    ctx = click.get_current_context()
    try:
        pinexq_config = _read_pinexq_toml()
        project_override = {}
        if ctx.obj.pinexq_endpoint:
            project_override = {'pinexq_endpoint': ctx.obj.pinexq_endpoint}
        project_config = {**{'version': version, 'name': py_project_name}, **pinexq_config['project'], **project_override}
        config = PinexqProjectConfig(**{**pinexq_config, **{'project': project_config}})
    except ValueError as e:
        print(f'{ERROR_PREFIX} Error reading pinexq.toml: {str(e)}')
        exit(1)
    return config


def _read_pinexq_toml() -> dict[str, Union[str, int]]:
    try:
        with open("pinexq.toml", "rb") as f:
            toml_dict = tomli.load(f)
            return toml_dict
    except FileNotFoundError:
        print(f'{ERROR_PREFIX} pinexq.toml file not found in current directory')
        exit(1)
    except Exception as e:
        print(f'{ERROR_PREFIX} Error reading pinexq.toml: {str(e)}')
        exit(1)


def _read_pyproject_toml() -> Tuple[str, str]:
    try:
        with open("pyproject.toml", "rb") as f:
            toml_dict = tomli.load(f)

        project_name = toml_dict.get("project", {}).get("name", "")
        version = toml_dict.get("project", {}).get("version", "0.0.0")

        return project_name, version
    except FileNotFoundError:
        print(f'{ERROR_PREFIX} pyproject.toml file not found in current directory')
        exit(1)
    except Exception as e:
        print(f'{ERROR_PREFIX} Error reading pyproject.toml: {str(e)}')
        exit(1)
