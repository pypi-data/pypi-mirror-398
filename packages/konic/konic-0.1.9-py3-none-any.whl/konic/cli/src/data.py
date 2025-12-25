"""CLI commands for managing data registry on Konic Cloud Platform."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from konic.cli.client import client
from konic.cli.decorators import error_handler, loading_indicator
from konic.cli.env_keys import KonicCLIEnvVars
from konic.cli.utils import find_entrypoint_file
from konic.common.errors import (
    KonicDataConflictError,
    KonicDataNotFoundError,
    KonicDataValidationError,
    KonicHTTPError,
    KonicValidationError,
)

app = typer.Typer(
    name="data",
    help="Manage data registry on Konic Cloud Platform",
    no_args_is_help=True,
)

console = Console()

NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def _apply_host_override(host: str | None) -> None:
    """Apply host override if provided."""
    if host:
        client.set_base_url(host)


def _validate_name(name: str) -> None:
    """Validate dataset name format."""
    if not name:
        raise KonicDataValidationError("Dataset name is required.", field="name")
    if len(name) > 100:
        raise KonicDataValidationError("Dataset name must be 100 characters or less.", field="name")
    if not NAME_PATTERN.match(name):
        raise KonicDataValidationError(
            "Dataset name must contain only alphanumeric characters, hyphens, and underscores.",
            field="name",
        )


def _validate_version(version: str) -> None:
    """Validate version string."""
    if not version:
        raise KonicDataValidationError("Version is required.", field="version")
    if len(version) > 50:
        raise KonicDataValidationError("Version must be 50 characters or less.", field="version")


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _display_data_table(datasets: list[dict]) -> None:
    """Display datasets in a Rich table."""
    table = Table(
        title="Datasets",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Name", style="cyan")
    table.add_column("Current Version", style="green")
    table.add_column("Size", justify="right")
    table.add_column("Versions", justify="right")
    table.add_column("Created At")

    for data in datasets:
        versions_count = len(data.get("versions", []))
        table.add_row(
            data.get("name", "N/A"),
            data.get("current_version", "N/A"),
            _format_file_size(data.get("file_size", 0)),
            str(versions_count),
            data.get("created_at", "N/A")[:19].replace("T", " "),
        )

    console.print(table)


def _display_data_detail(data: dict, version_info: dict | None = None) -> None:
    """Display dataset details in a Rich panel."""
    versions_info = ""
    if data.get("versions"):
        versions_info = "\n\n[bold]Versions:[/bold]\n"
        for v in data["versions"]:
            versions_info += (
                f"  • {v['version']} ({_format_file_size(v.get('file_size', 0))}) - "
                f"{v.get('created_at', 'N/A')[:19]}\n"
            )

    content = f"""[bold cyan]Name:[/bold cyan] {data.get('name', 'N/A')}
[bold cyan]ID:[/bold cyan] {data.get('id', 'N/A')}
[bold cyan]Description:[/bold cyan] {data.get('description', 'N/A') or 'No description'}
[bold cyan]Current Version:[/bold cyan] {data.get('current_version', 'N/A')}
[bold cyan]File Size:[/bold cyan] {_format_file_size(data.get('file_size', 0))}
[bold cyan]Content Type:[/bold cyan] {data.get('content_type', 'N/A')}
[bold cyan]Original Filename:[/bold cyan] {data.get('original_filename', 'N/A')}
[bold cyan]Checksum (SHA256):[/bold cyan] {data.get('checksum_sha256', 'N/A')}
[bold cyan]Created:[/bold cyan] {data.get('created_at', 'N/A')[:19].replace('T', ' ')}
[bold cyan]Updated:[/bold cyan] {data.get('updated_at', 'N/A')[:19].replace('T', ' ')}{versions_info}"""

    if version_info:
        content += f"""

[bold yellow]Selected Version Details:[/bold yellow]
  Version: {version_info.get('version', 'N/A')}
  Size: {_format_file_size(version_info.get('file_size', 0))}
  Checksum: {version_info.get('checksum_sha256', 'N/A')}
  Created: {version_info.get('created_at', 'N/A')[:19].replace('T', ' ')}"""

    console.print(Panel(content, title="Dataset Details", border_style="blue"))


def _resolve_data_identifier(data_identifier: str) -> dict[str, Any]:
    """
    Resolve a data identifier (name or ID) to dataset info.

    Args:
        data_identifier: Dataset name or ID

    Returns:
        Dataset info dictionary

    Raises:
        KonicDataNotFoundError: If dataset not found
    """
    try:
        return client.get_json(f"/data/by-name/{data_identifier}")
    except KonicHTTPError as e:
        if e.status_code != 404:
            raise

    try:
        return client.get_json(f"/data/{data_identifier}")
    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicDataNotFoundError(data_identifier)
        raise


@app.command(name="push")
@error_handler(exit_on_error=True)
def push_data(
    file_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the data file to upload",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    name: Annotated[
        str,
        typer.Option(
            "--name",
            "-n",
            help="Unique name for the dataset (alphanumeric, hyphens, underscores)",
        ),
    ],
    version: Annotated[
        str,
        typer.Option(
            "--version",
            "-v",
            help="Version string (e.g., '1.0.0', 'v1', '2024-01-15')",
        ),
    ],
    description: Annotated[
        str | None,
        typer.Option(
            "--description",
            "-d",
            help="Description of the dataset",
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
) -> None:
    """
    Upload a data file to the registry.

    This command uploads a data file to the Konic Cloud Platform data registry.
    Each dataset can have multiple versions, and versions are immutable once uploaded.

    Example:
        konic data push ./data/prices.csv --name stock-prices --version 1.0.0
        konic data push ./data/prices.csv -n stock-prices -v 1.0.1 -d "Updated Q4 data"
    """
    _apply_host_override(host)

    _validate_name(name)
    _validate_version(version)

    if file_path.stat().st_size == 0:
        raise KonicDataValidationError("File is empty.", field="file")

    console.print(f"[cyan]Uploading {file_path.name}...[/cyan]\n")

    form_data: dict[str, str] = {
        "name": name,
        "version": version,
    }
    if description:
        form_data["description"] = description

    try:
        result = client.upload_file_with_progress(
            "/data/upload",
            file_path,
            form_data,
        )

        console.print("\n[bold green]✓[/bold green] Dataset uploaded successfully!")
        console.print(f"  [cyan]Name:[/cyan] {result.get('name')}")
        console.print(f"  [cyan]Version:[/cyan] {result.get('current_version')}")
        console.print(f"  [cyan]Size:[/cyan] {_format_file_size(result.get('file_size', 0))}")
        console.print(f"  [cyan]Checksum:[/cyan] {result.get('checksum_sha256')}")

    except KonicHTTPError as e:
        if e.status_code == 409:
            raise KonicDataConflictError(name, version)
        if e.status_code == 400:
            raise KonicDataValidationError(str(e.message), field="file")
        raise


@app.command(name="list")
@error_handler(exit_on_error=True)
@loading_indicator(message="Fetching datasets...")
def list_data(
    name: Annotated[
        str | None,
        typer.Option(
            "--name",
            "-n",
            help="Filter datasets by name (partial match)",
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
            "-j",
            help="Output as JSON",
        ),
    ] = False,
) -> None:
    """
    List all datasets in the registry.

    Example:
        konic data list
        konic data list --name stock
        konic data list --json
    """
    _apply_host_override(host)

    params: dict[str, Any] = {
        "_start": 0,
        "_end": 100,
        "_sort": "created_at",
        "_order": "DESC",
    }
    if name:
        params["name"] = name

    result = client.get_json("/data", params=params)

    if output_json:
        console.print_json(json.dumps(result))
        return

    if not result:
        console.print("[yellow]No datasets found.[/yellow]")
        return

    _display_data_table(result)


@app.command(name="show")
@error_handler(exit_on_error=True)
@loading_indicator(message="Fetching dataset details...")
def show_data(
    name: Annotated[
        str,
        typer.Argument(
            help="Dataset name or ID",
        ),
    ],
    version: Annotated[
        str | None,
        typer.Option(
            "--version",
            "-v",
            help="Show details for a specific version",
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
            "-j",
            help="Output as JSON",
        ),
    ] = False,
) -> None:
    """
    Show details of a dataset.

    Example:
        konic data show stock-prices
        konic data show stock-prices --version 1.0.0
        konic data show stock-prices --json
    """
    _apply_host_override(host)

    data = _resolve_data_identifier(name)

    version_info = None
    if version:
        try:
            version_info = client.get_json(f"/data/by-name/{data.get('name')}/versions/{version}")
        except KonicHTTPError as e:
            if e.status_code == 404:
                raise KonicDataNotFoundError(f"{name} version {version}")
            raise

    if output_json:
        output = data
        if version_info:
            output["selected_version"] = version_info
        console.print_json(json.dumps(output))
        return

    _display_data_detail(data, version_info)


@app.command(name="pull")
@error_handler(exit_on_error=True)
def pull_data(
    name: Annotated[
        str,
        typer.Argument(
            help="Dataset name",
        ),
    ],
    version: Annotated[
        str | None,
        typer.Option(
            "--version",
            "-v",
            help="Version to download (default: latest)",
        ),
    ] = None,
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
    Download a dataset from the registry.

    Downloads the specified version of a dataset (or latest if not specified)
    and verifies the SHA256 checksum by default.

    Example:
        konic data pull stock-prices
        konic data pull stock-prices --version 1.0.0
        konic data pull stock-prices -o ./local-data/
        konic data pull stock-prices --skip-verify
    """
    _apply_host_override(host)

    params = {}
    if version:
        params["version"] = version

    try:
        download_info = client.get_json(f"/data/by-name/{name}/download", params=params)
    except KonicHTTPError as e:
        if e.status_code == 404:
            if version:
                raise KonicDataNotFoundError(f"{name} version {version}")
            raise KonicDataNotFoundError(name)
        raise

    output_dir = output or Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / download_info.get("original_filename", f"{name}.data")

    console.print(f"[cyan]Downloading {name} v{download_info.get('version')}...[/cyan]\n")

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


@app.command(name="delete")
@error_handler(exit_on_error=True)
@loading_indicator(message="Deleting dataset...")
def delete_data(
    name: Annotated[
        str,
        typer.Argument(
            help="Dataset name to delete",
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
    Delete a dataset from the registry.

    This will delete all versions of the dataset. This action cannot be undone.

    Example:
        konic data delete stock-prices
        konic data delete stock-prices --force
    """
    _apply_host_override(host)

    data = _resolve_data_identifier(name)
    data_name = data.get("name", name)

    if not force:
        versions_count = len(data.get("versions", []))
        confirm = typer.confirm(
            f"Are you sure you want to delete dataset '{data_name}' "
            f"and all {versions_count} version(s)?"
        )
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit()

    try:
        client.delete(f"/data/by-name/{data_name}")
        console.print(f"[bold green]✓[/bold green] Dataset '{data_name}' deleted successfully!")
    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicDataNotFoundError(name)
        raise


@app.command(name="check")
@error_handler(exit_on_error=True)
def check_data(
    agent_path: Annotated[
        Path | None,
        typer.Option(
            "--agent-path",
            "-p",
            help="Path to agent directory (default: current directory)",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
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
) -> None:
    """
    Verify data dependencies are available before training.

    This command loads the agent from the specified path and checks that
    all registered data dependencies exist in the Konic Cloud Platform.

    Example:
        konic data check
        konic data check --agent-path ./my-agent
    """
    _apply_host_override(host)

    path = agent_path or Path.cwd()

    entrypoint = find_entrypoint_file(path)
    if not entrypoint:
        raise KonicValidationError(
            f"No entrypoint file found in {path}. "
            "Ensure your agent calls 'register_agent()' in a Python file.",
            field="agent_path",
        )

    console.print(f"[cyan]Loading agent from {entrypoint}...[/cyan]\n")

    sys.path.insert(0, str(path))

    try:
        from konic.runtime.data import clear_registered_data

        clear_registered_data()

        with open(entrypoint) as f:
            code = compile(f.read(), entrypoint, "exec")
            exec(code, {"__name__": "__main__", "__file__": str(entrypoint)})

        from konic.runtime import get_registered_data

        dependencies = get_registered_data()

        if not dependencies:
            console.print("[yellow]No data dependencies registered.[/yellow]")
            return

        console.print(f"[bold]Checking {len(dependencies)} data dependencies...[/bold]\n")

        all_satisfied = True
        for dep in dependencies:
            params = {}
            if dep.version != "latest":
                params["version"] = dep.version

            try:
                result = client.get_json(
                    f"/data/by-name/{dep.cloud_name}/exists",
                    params=params if params else None,
                )

                if result.get("exists"):
                    actual_version = result.get("version", dep.version)
                    console.print(
                        f"[green]✓[/green] {dep.cloud_name} v{actual_version} " f"-> ${dep.env_var}"
                    )
                else:
                    all_satisfied = False
                    version_str = f" v{dep.version}" if dep.version != "latest" else ""
                    console.print(f"[red]✗[/red] {dep.cloud_name}{version_str} - not found")

            except KonicHTTPError as e:
                all_satisfied = False
                console.print(f"[red]✗[/red] {dep.cloud_name} - error: {e.message}")

        console.print()
        if all_satisfied:
            console.print("[bold green]All dependencies satisfied![/bold green]")
        else:
            console.print(
                "[bold red]Some dependencies are missing.[/bold red]\n"
                "Use 'konic data push' to upload the missing datasets."
            )
            raise typer.Exit(1)

    finally:
        if str(path) in sys.path:
            sys.path.remove(str(path))
