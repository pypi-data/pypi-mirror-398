import typer
from copier import run_copy, CopierAnswersInterrupt
from copier.errors import CopierError
from rich.console import Console

generate_app = typer.Typer(name="generate", no_args_is_help=True)

# REUSABLE OPTIONS
Template = typer.Option("gh:data-cybernetics/pinexq-project-starter.git", "--template", show_default=True)
Version = typer.Option("latest", "--template-version", show_default=True)
Path = typer.Option("./", "--path", show_default=True)

err_console = Console(stderr=True)


@generate_app.command(name="project-toml", help="Generate project.toml")
def generate_project_toml(
        template: str = Template,
        version: str = Version,
        path: str = Path,
):
    generate_project_file(path, template, version, target_file="pinexq.toml")


@generate_app.command(name="dockerfile", help="Generate Dockerfile")
def generate_dockerfile(
        template: str = Template,
        version: str = Version,
        path: str = Path,
):
    generate_project_file(path, template, version, target_file="Dockerfile", data={'project_name': 'dummy', 'pinexq_endpoint': 'dummy'})


def generate_project_file(path: str, template: str, template_version: str, target_file: str = "pinexq.toml", data: dict = None):
    try:
        run_copy(
            template,
            path,
            vcs_ref=template_version if template_version != "latest" else None,
            exclude=["*", f"!{target_file}"],
            data=data
        )
    except CopierAnswersInterrupt:
        err_console.print("Project generation aborted")
    except CopierError as e:
        err_console.print(f"Error during project generation: {e}")
