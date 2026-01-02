from typer import Typer

from konic.cli.client import client
from konic.cli.decorators import error_handler, json_output, loading_indicator

app = Typer(
    name="health",
    help="Check the health and connectivity of the Konic Cloud Platform API.",
    no_args_is_help=True,
)


@app.command(name="check")
@error_handler(exit_on_error=True, show_traceback=False)
@loading_indicator(message="Checking Konic API health...", success_message="Konic API is healthy!")
@json_output(pretty=True)
def health_check():
    """
    Verify connectivity to the Konic Cloud Platform API.

    Sends a health check request to the API and displays the
    connection status and API version information.

    Example:
        konic health check
    """
    return client.get_json("/health")
