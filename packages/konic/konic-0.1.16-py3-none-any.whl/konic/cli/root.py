import os
from pathlib import Path

from cookiecutter.main import cookiecutter
from typer import Typer

from konic.cli.decorators import error_handler, pretty_output
from konic.cli.enums import BoilerplateOptions
from konic.cli.env_keys import KonicCLIEnvVars
from konic.cli.src import agents, artifacts, data, health, inference, models, training
from konic.cli.utils import compile_artifact

app = Typer(
    name="konic",
    help="Official Konic Agent Development Toolkit",
    no_args_is_help=True,
)

app.add_typer(health.app, name="health")
app.add_typer(agents.app, name="agent")
app.add_typer(training.app, name="train")
app.add_typer(data.app, name="data")
app.add_typer(artifacts.app, name="artifact")
app.add_typer(inference.app, name="inference")
app.add_typer(models.app, name="model")


@app.command(name="get-host")
@error_handler(exit_on_error=True)
@pretty_output(title="Konic Host Configuration", border_style="cyan")
def get_host() -> str:
    """
    Display the currently configured Konic API host URL.

    Shows the KONIC_HOST environment variable value, or indicates
    if it has not been configured.

    Example:
        konic get-host
    """
    host = os.environ.get(KonicCLIEnvVars.KONIC_HOST.value, "")
    return host if host else "Not configured"


@app.command(name="init")
@error_handler(exit_on_error=True)
def create_boilerplate(template: BoilerplateOptions = BoilerplateOptions.basic):
    """
    Initialize a new Konic agent project from a template.

    Creates a new agent project directory with boilerplate code
    and configuration files to help you get started quickly.

    Example:
        konic init
        konic init --template basic
    """
    path = Path(__file__).parent / "boilerplates" / template.value
    cookiecutter(str(path))


@app.command(name="compile")
@error_handler(exit_on_error=True)
def compile(filepath: str):
    """
    Compile an agent directory into a deployable artifact.

    Creates a zip archive containing your agent code ready for
    upload to the Konic Cloud Platform.

    Example:
        konic compile ./my-agent
    """
    compile_artifact(filepath)
