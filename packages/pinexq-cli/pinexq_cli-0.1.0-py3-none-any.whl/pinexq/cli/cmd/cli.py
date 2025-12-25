from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import typer.rich_utils  # important: import the module, not individual names

from .deploy import deploy as deploy_impl, DeployOptions
from .generate import generate_app
from .initialization import init_project
from ..docker_tools.client import load_docker_client
from ..pinexq_tools.project import get_project_meta


@dataclass
class CLIContext:
    pinexq_endpoint: Optional[str] = None
    verbose: bool = False


typer.rich_utils.STYLE_METAVAR = 'bold dark_orange'
typer.rich_utils.STYLE_USAGE = 'dark_orange'
typer.rich_utils.STYLE_OPTION_ENVVAR = 'dim dark_orange'
app = typer.Typer(
    name="pinexq",
    invoke_without_command=True,
    add_completion=False,
    no_args_is_help=True,
    suggest_commands=True,
    rich_markup_mode="rich",
)


@app.callback()
def _pinexq_callback(
        ctx: typer.Context,
        endpoint: Optional[str] = typer.Option(None, "--endpoint", envvar="PINEXQ_ENDPOINT", help="Pinexq endpoint"),
        verbose: bool = typer.Option(False, "--verbose", help="Debug output"),
):
    ctx.obj = CLIContext(pinexq_endpoint=endpoint, verbose=verbose)


@app.command(name="deploy", rich_help_panel="Deploy functions to Pinexq")
def deploy(
        dockerfile: str = typer.Option("./Dockerfile", "-D", "--dockerfile", show_default=True),
        context_dir: str = typer.Option("./", "--context-dir", show_default=True),
        api_key: str = typer.Option(None, "--api-key", envvar="PINEXQ_API_KEY", help="Pinexq API key"),
        functions: list[str] = typer.Option(None, "-f", "--function", help="Select functions to deploy"),
        secrets: list[str] = typer.Option(None, '--secret', help="Secrets to be passed to the docker build"),
        disable_attestation: bool = typer.Option(False, "--disable-attestation", help="Disable attestation"),
):
    """
    Deploy functions to [dark_orange]Pinexq[/dark_orange]. This builds and pushes an OCI-compatible image to Pinexq and registers the function with the API.
    """
    # TODO: use overrides for project_meta
    docker_client = load_docker_client()
    project_meta = get_project_meta()
    deploy_impl(DeployOptions(
        dockerfile=dockerfile,
        context_dir=context_dir,
        api_key=api_key or "",
        functions=list(functions or []),
        secrets=list(secrets or []),
    ), docker_client, project_meta)


@app.command(name="init")
def init(
        path: str = typer.Argument("./"),
        template: str = typer.Option("gh:data-cybernetics/pinexq-project-starter.git", "--template", show_default=True),
        version: str = typer.Option("latest", "--template-version", show_default=True),
):
    init_project(path, template, version)


# Register sub-apps
app.add_typer(generate_app, name="generate")

# Backwards-compatibility for type hints imported in other modules
# Export name `CLI` to represent the root context type
CLI = CLIContext

# For compatibility with the existing import name
pinexq = app
