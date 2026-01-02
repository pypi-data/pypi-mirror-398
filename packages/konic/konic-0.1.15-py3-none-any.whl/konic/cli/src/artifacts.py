"""CLI commands for managing artifacts on Konic Cloud Platform."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from konic.cli.client import client
from konic.cli.decorators import error_handler, loading_indicator
from konic.cli.env_keys import KonicCLIEnvVars
from konic.cli.utils import resolve_agent_identifier
from konic.common.errors import (
    KonicArtifactNotFoundError,
    KonicHTTPError,
)

app = typer.Typer(
    name="artifact",
    help="Manage training artifacts (checkpoints and models) on Konic Cloud Platform",
    no_args_is_help=True,
)

console = Console()


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


def _get_artifact_type_style(artifact_type: str) -> str:
    """Get Rich style for artifact type."""
    styles = {
        "final": "bold green",
        "checkpoint": "cyan",
    }
    return styles.get(artifact_type, "white")


def _display_artifact_table(artifacts: list[dict], agent_name: str | None = None) -> None:
    """Display artifacts in a Rich table."""
    title = "Artifacts"
    if agent_name:
        title = f"Artifacts for agent '{agent_name}'"

    table = Table(
        title=title,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("ID", style="dim")
    table.add_column("Type")
    table.add_column("Iteration", justify="right")
    table.add_column("Job ID", style="dim")
    table.add_column("Size", justify="right")
    table.add_column("Created At")

    for artifact in artifacts:
        artifact_type = artifact.get("artifact_type", "unknown")
        job_id = artifact.get("training_job_id", "N/A")
        job_id_display = job_id

        table.add_row(
            artifact.get("id", "N/A"),
            f"[{_get_artifact_type_style(artifact_type)}]{artifact_type}[/]",
            str(artifact.get("iteration", "N/A")),
            job_id_display,
            _format_file_size(artifact.get("file_size", 0)),
            artifact.get("created_at", "N/A")[:19].replace("T", " "),
        )

    console.print(table)


def _display_artifact_detail(artifact: dict) -> None:
    """Display artifact details in a Rich panel."""
    artifact_type = artifact.get("artifact_type", "unknown")

    content = f"""[bold cyan]ID:[/bold cyan] {artifact.get('id', 'N/A')}
[bold cyan]Agent:[/bold cyan] {artifact.get('agent_name', 'N/A')} ({artifact.get('agent_id', 'N/A')})
[bold cyan]Job ID:[/bold cyan] {artifact.get('training_job_id', 'N/A')}
[bold cyan]Type:[/bold cyan] [{_get_artifact_type_style(artifact_type)}]{artifact_type}[/]
[bold cyan]Iteration:[/bold cyan] {artifact.get('iteration', 'N/A')}
[bold cyan]Size:[/bold cyan] {_format_file_size(artifact.get('file_size', 0))}
[bold cyan]Checksum (SHA256):[/bold cyan] {artifact.get('checksum_sha256', 'N/A')}
[bold cyan]Created:[/bold cyan] {artifact.get('created_at', 'N/A')[:19].replace('T', ' ')}"""

    console.print(Panel(content, title="Artifact Details", border_style="blue"))


@app.command(name="list")
@error_handler(exit_on_error=True)
@loading_indicator(message="Fetching artifacts...")
def list_artifacts(
    agent: Annotated[
        str,
        typer.Argument(
            help="Agent ID or name",
        ),
    ],
    job_id: Annotated[
        str | None,
        typer.Option(
            "--job-id",
            "-j",
            help="Filter by training job ID",
        ),
    ] = None,
    artifact_type: Annotated[
        str | None,
        typer.Option(
            "--type",
            "-t",
            help="Filter by artifact type (checkpoint or final)",
        ),
    ] = None,
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
            help="Output as JSON",
        ),
    ] = False,
) -> None:
    """
    List training artifacts (checkpoints and models) for an agent.

    Shows all artifacts including checkpoint saves and final trained
    models. Filter by training job or artifact type to narrow results.

    Artifact types:
        - checkpoint: Intermediate model saves during training
        - final: The completed trained model

    Example:
        konic artifact list my-agent
        konic artifact list my-agent --type final
        konic artifact list my-agent --job-id 692bba9e30c77da5144f5a95
    """
    _apply_host_override(host)

    agent_id = resolve_agent_identifier(client, agent)

    try:
        agent_info = client.get_json(f"/agents/{agent_id}")
        agent_name = agent_info.get("agent_name", agent)
    except KonicHTTPError:
        agent_name = agent

    if job_id:
        result = client.get_json(f"/artifacts/by-job/{job_id}")
    else:
        result = client.get_json(f"/artifacts/by-agent/{agent_id}")

    if artifact_type:
        result = [a for a in result if a.get("artifact_type") == artifact_type]

    if output_json:
        console.print_json(json.dumps(result))
        return

    if not result:
        console.print("[yellow]No artifacts found.[/yellow]")
        return

    _display_artifact_table(result, agent_name)


@app.command(name="show")
@error_handler(exit_on_error=True)
@loading_indicator(message="Fetching artifact details...")
def show_artifact(
    artifact_id: Annotated[
        str,
        typer.Argument(
            help="Artifact ID",
        ),
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
            help="Output as JSON",
        ),
    ] = False,
) -> None:
    """
    Display detailed information about an artifact.

    Shows artifact metadata including type, iteration, file size,
    checksum, and associated agent/training job information.

    Example:
        konic artifact show artifact-abc12345-1701388800
        konic artifact show artifact-abc12345-1701388800 --json
    """
    _apply_host_override(host)

    try:
        result = client.get_json(f"/artifacts/{artifact_id}")

        if output_json:
            console.print_json(json.dumps(result))
            return

        _display_artifact_detail(result)
    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicArtifactNotFoundError(artifact_id)
        raise


@app.command(name="download")
@error_handler(exit_on_error=True)
def download_artifact(
    artifact_id: Annotated[
        str,
        typer.Argument(
            help="Artifact ID to download",
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output directory (default: current directory)",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = None,
    skip_verify: Annotated[
        bool,
        typer.Option(
            "--skip-verify",
            help="Skip SHA256 checksum verification",
        ),
    ] = False,
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
    Download a training artifact (checkpoint or model).

    Downloads the artifact zip file to the specified directory.
    By default, verifies the SHA256 checksum after download to
    ensure file integrity. Use --skip-verify to disable this check.

    Example:
        konic artifact download artifact-abc12345-1701388800
        konic artifact download artifact-abc12345-1701388800 --output ./checkpoints/
        konic artifact download artifact-abc12345-1701388800 --skip-verify
    """
    _apply_host_override(host)

    try:
        download_info = client.get_json(f"/artifacts/{artifact_id}/download")
    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicArtifactNotFoundError(artifact_id)
        raise

    output_dir = output or Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)

    artifact_type = download_info.get("artifact_type", "artifact")
    iteration = download_info.get("iteration", 0)
    filename = f"{artifact_type}_{iteration:06d}.zip"
    output_path = output_dir / filename

    console.print(f"[cyan]Downloading {artifact_type} artifact (iteration {iteration})...[/cyan]\n")

    try:
        downloaded_path, checksum = client.download_file_with_progress(
            url=download_info["download_url"],
            output_path=output_path,
            expected_size=download_info.get("file_size"),
            expected_checksum=download_info.get("checksum_sha256"),
            verify_checksum=not skip_verify,
        )

        console.print("\n[bold green]✓[/bold green] Downloaded successfully!")
        console.print(f"  [cyan]File:[/cyan] {downloaded_path}")
        console.print(
            f"  [cyan]Size:[/cyan] {_format_file_size(download_info.get('file_size', 0))}"
        )
        console.print(f"  [cyan]Checksum:[/cyan] {checksum}")

        if skip_verify:
            console.print("  [yellow]⚠ Checksum verification was skipped[/yellow]")
        else:
            console.print("  [green]✓ Checksum verified[/green]")

    except ValueError as e:
        console.print(f"\n[bold red]✗[/bold red] {e}")
        raise typer.Exit(1)
