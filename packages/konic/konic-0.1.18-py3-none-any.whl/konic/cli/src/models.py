"""CLI commands for managing HuggingFace models on Konic Cloud Platform."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from konic.cli.client import client
from konic.cli.decorators import error_handler, loading_indicator
from konic.cli.env_keys import KonicCLIEnvVars
from konic.common.errors import (
    KonicHTTPError,
    KonicModelConflictError,
    KonicModelGatedError,
    KonicModelNotFoundError,
)

app = typer.Typer(
    name="model",
    help="Manage HuggingFace models on Konic Cloud Platform",
    no_args_is_help=True,
)

console = Console()

# Maximum models to fetch for client-side resolution.
# TODO: Replace with server-side filtering when /models?hf_model_id= is supported
_MAX_MODELS_FETCH = 1000


def _apply_host_override(host: str | None) -> None:
    """Apply host override if provided."""
    if host:
        client.set_base_url(host)


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _resolve_model_by_hf_id(hf_model_id: str) -> dict:
    """
    Resolve a HuggingFace model ID to its registry entry.

    Args:
        hf_model_id: The HuggingFace model ID (e.g., "gpt2", "meta-llama/Llama-2-7b")

    Returns:
        The model dictionary containing the internal ID and metadata

    Raises:
        KonicModelNotFoundError: If the model is not found in the registry
    """
    models = client.get_json("/models", params={"_start": 0, "_end": _MAX_MODELS_FETCH})

    for model in models:
        if model.get("hf_model_id") == hf_model_id:
            return model
    raise KonicModelNotFoundError(hf_model_id, context="registry")


def _get_status_style(status: str) -> str:
    """Get Rich style for a model status."""
    styles = {
        "ready": "green",
        "downloading": "yellow",
        "pending": "dim",
        "failed": "red",
    }
    return styles.get(status, "white")


def _display_model_table(models: list[dict]) -> None:
    """Display models in a Rich table."""
    table = Table(
        title="Models",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Display Name", style="cyan")
    table.add_column("HF Model ID", style="dim")
    table.add_column("Task Type", style="blue")
    table.add_column("Status", justify="center")
    table.add_column("Size", justify="right")
    table.add_column("Updated At")

    for model in models:
        status = model.get("status", "unknown")
        status_style = _get_status_style(status)
        table.add_row(
            model.get("display_name", "N/A"),
            model.get("hf_model_id", "N/A"),
            model.get("task_type") or "N/A",
            f"[{status_style}]{status}[/{status_style}]",
            _format_file_size(model.get("file_size", 0)),
            model.get("updated_at", "N/A")[:19].replace("T", " "),
        )

    console.print(table)


def _display_model_detail(model: dict) -> None:
    """Display model details in a Rich panel."""
    tags = model.get("tags", [])
    tags_str = ", ".join(tags) if tags else "None"

    status = model.get("status", "unknown")
    status_style = _get_status_style(status)

    error_info = ""
    if model.get("error_message"):
        error_info = f"\n[bold red]Error:[/bold red] {model.get('error_message')}"

    content = f"""[bold cyan]Display Name:[/bold cyan] {model.get('display_name', 'N/A')}
[bold cyan]HF Model ID:[/bold cyan] {model.get('hf_model_id', 'N/A')}
[bold cyan]Internal ID:[/bold cyan] {model.get('id', 'N/A')}
[bold cyan]Task Type:[/bold cyan] {model.get('task_type') or 'N/A'}
[bold cyan]Architecture:[/bold cyan] {model.get('architecture') or 'N/A'}
[bold cyan]License:[/bold cyan] {model.get('license') or 'N/A'}
[bold cyan]Tags:[/bold cyan] {tags_str}
[bold cyan]File Size:[/bold cyan] {_format_file_size(model.get('file_size', 0))}
[bold cyan]Local Path:[/bold cyan] {model.get('local_path') or 'N/A'}
[bold cyan]Status:[/bold cyan] [{status_style}]{status}[/{status_style}]{error_info}
[bold cyan]Created:[/bold cyan] {model.get('created_at', 'N/A')[:19].replace('T', ' ')}
[bold cyan]Updated:[/bold cyan] {model.get('updated_at', 'N/A')[:19].replace('T', ' ')}"""

    console.print(Panel(content, title="Model Details", border_style="blue"))


@app.command(name="list")
@error_handler(exit_on_error=True)
@loading_indicator(message="Fetching models...")
def list_models(
    status: Annotated[
        str | None,
        typer.Option(
            "--status",
            "-s",
            help="Filter by status (pending, downloading, ready, failed)",
        ),
    ] = None,
    task_type: Annotated[
        str | None,
        typer.Option(
            "--task-type",
            "-t",
            help="Filter by HuggingFace task type (e.g., text-generation)",
        ),
    ] = None,
    start: Annotated[
        int,
        typer.Option(
            "--start",
            help="Pagination start index",
        ),
    ] = 0,
    end: Annotated[
        int,
        typer.Option(
            "--end",
            help="Pagination end index",
        ),
    ] = 20,
    host: Annotated[
        str | None,
        typer.Option(
            "--host",
            "-h",
            help="Override the Konic API host URL",
            envvar=KonicCLIEnvVars.KONIC_HOST.value,
        ),
    ] = None,
    output_json: Annotated[
        bool,
        typer.Option(
            "--json",
            "-j",
            help="Output as JSON instead of table",
        ),
    ] = False,
) -> None:
    """
    List all HuggingFace models in the registry.

    Supports filtering by status and task type, with pagination.

    Example:
        konic model list
        konic model list --status ready
        konic model list --task-type text-generation
        konic model list --json
    """
    _apply_host_override(host)

    params: dict = {"_start": start, "_end": end}
    if status:
        params["status"] = status
    if task_type:
        params["task_type"] = task_type

    models = client.get_json("/models", params=params)

    if output_json:
        console.print_json(data=models)
    elif not models:
        console.print("[yellow]No models found.[/yellow]")
    else:
        _display_model_table(models)

        page_size = end - start
        if len(models) == page_size:
            console.print(
                f"\n[dim]Showing {len(models)} models (start: {start}). "
                f"Use --start {end} to see more.[/dim]"
            )


@app.command(name="download")
@error_handler(exit_on_error=True)
@loading_indicator(message="Downloading model from HuggingFace Hub...")
def download_model(
    hf_model_id: Annotated[
        str,
        typer.Argument(help="HuggingFace model ID (e.g., gpt2, meta-llama/Llama-2-7b)"),
    ],
    host: Annotated[
        str | None,
        typer.Option(
            "--host",
            "-h",
            help="Override the Konic API host URL",
            envvar=KonicCLIEnvVars.KONIC_HOST.value,
        ),
    ] = None,
) -> None:
    """
    Download a model from HuggingFace Hub.

    This command starts a model download on the Konic Cloud Platform.
    The download runs asynchronously on the server - use 'konic model details'
    to check the download status. Only public (non-gated) models are supported.

    Example:
        konic model download gpt2
        konic model download meta-llama/Llama-2-7b
    """
    _apply_host_override(host)

    try:
        result = client.post_json("/models/download", json={"hf_model_id": hf_model_id})
        console.print("\n[bold green]✓[/bold green] Model downloading started!")
        _display_model_detail(result)
    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicModelNotFoundError(hf_model_id, context="huggingface")
        if e.status_code == 403:
            raise KonicModelGatedError(hf_model_id)
        if e.status_code == 409:
            raise KonicModelConflictError(hf_model_id)
        raise


@app.command(name="details")
@error_handler(exit_on_error=True)
@loading_indicator(message="Fetching model details...")
def model_details(
    hf_model_id: Annotated[
        str,
        typer.Argument(help="HuggingFace model ID (e.g., gpt2, meta-llama/Llama-2-7b)"),
    ],
    host: Annotated[
        str | None,
        typer.Option(
            "--host",
            "-h",
            help="Override the Konic API host URL",
            envvar=KonicCLIEnvVars.KONIC_HOST.value,
        ),
    ] = None,
    output_json: Annotated[
        bool,
        typer.Option(
            "--json",
            "-j",
            help="Output as JSON instead of formatted panel",
        ),
    ] = False,
) -> None:
    """
    Get details of a specific model by HuggingFace model ID.

    Example:
        konic model details gpt2
        konic model details meta-llama/Llama-2-7b --json
    """
    _apply_host_override(host)

    model = _resolve_model_by_hf_id(hf_model_id)

    if output_json:
        console.print_json(data=model)
    else:
        _display_model_detail(model)


@app.command(name="delete")
@error_handler(exit_on_error=True)
@loading_indicator(message="Deleting model...")
def delete_model(
    hf_model_id: Annotated[
        str,
        typer.Argument(help="HuggingFace model ID (e.g., gpt2, meta-llama/Llama-2-7b)"),
    ],
    host: Annotated[
        str | None,
        typer.Option(
            "--host",
            "-h",
            help="Override the Konic API host URL",
            envvar=KonicCLIEnvVars.KONIC_HOST.value,
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Skip confirmation prompt",
        ),
    ] = False,
) -> None:
    """
    Delete a model from the registry.

    This performs a soft delete - the model is marked as deleted but
    the files may remain on disk.

    Example:
        konic model delete gpt2
        konic model delete meta-llama/Llama-2-7b --force
    """
    _apply_host_override(host)

    model = _resolve_model_by_hf_id(hf_model_id)
    model_id = model.get("id")

    if not model_id:
        raise KonicModelNotFoundError(hf_model_id, context="registry")

    display_name = model.get("display_name", hf_model_id)

    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete model '{display_name}'?")
        if not confirm:
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(0)

    try:
        client.delete(f"/models/{model_id}")
        console.print(f"[bold green]✓[/bold green] Model '{display_name}' deleted successfully!")
    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicModelNotFoundError(hf_model_id)
        raise


@app.command(name="task-types")
@error_handler(exit_on_error=True)
@loading_indicator(message="Fetching task types...")
def list_task_types(
    host: Annotated[
        str | None,
        typer.Option(
            "--host",
            "-h",
            help="Override the Konic API host URL",
            envvar=KonicCLIEnvVars.KONIC_HOST.value,
        ),
    ] = None,
    output_json: Annotated[
        bool,
        typer.Option(
            "--json",
            "-j",
            help="Output as JSON instead of list",
        ),
    ] = False,
) -> None:
    """
    List all available task types from downloaded models.

    Shows distinct HuggingFace task types (e.g., text-generation, text-classification)
    that are present in the model registry.

    Example:
        konic model task-types
        konic model task-types --json
    """
    _apply_host_override(host)

    task_types = client.get_json("/models/task-types")

    if output_json:
        console.print_json(data=task_types)
    elif not task_types:
        console.print("[yellow]No task types found. Download some models first.[/yellow]")
    else:
        console.print("[bold]Available Task Types:[/bold]")
        for task_type in task_types:
            console.print(f"  - {task_type}")
