"""CLI commands for managing inference servers on Konic Cloud Platform."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Annotated, Any

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from konic.cli.client import client
from konic.cli.decorators import error_handler, loading_indicator
from konic.cli.enums import InferenceServerStatus
from konic.cli.env_keys import KonicCLIEnvVars
from konic.common.errors import (
    KonicHTTPError,
    KonicInferenceServerNotFoundError,
)

app = typer.Typer(
    name="inference",
    help="Manage inference servers on Konic Cloud Platform",
    no_args_is_help=True,
)

console = Console()

WAIT_POLL_INTERVAL_SECONDS = 2
WAIT_DEFAULT_TIMEOUT_SECONDS = 300
WAIT_MAX_TIMEOUT_SECONDS = 600
LOGS_POLL_INTERVAL_SECONDS = 3
LOGS_DEFAULT_TAIL = 100


def _apply_host_override(host: str | None) -> None:
    """Apply host override if provided."""
    if host:
        client.set_base_url(host)


def _get_status_style(status: str) -> str:
    """Get Rich style for inference server status."""
    styles = {
        InferenceServerStatus.PENDING.value: "yellow",
        InferenceServerStatus.RUNNING.value: "blue",
        InferenceServerStatus.STOPPED.value: "dim",
        InferenceServerStatus.ERROR.value: "red",
    }
    return styles.get(status, "white")


def _format_uptime(seconds: float | None) -> str:
    """Format uptime in human-readable format (e.g., '1h 30m 45s')."""
    if seconds is None:
        return "N/A"

    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def _format_count(count: int | None) -> str:
    """Format count with thousands separator."""
    if count is None:
        return "N/A"
    return f"{count:,}"


def _get_external_client(server_id: str) -> tuple[httpx.Client, dict]:
    """
    Get an unauthenticated HTTP client for the inference container.

    Args:
        server_id: The inference server ID

    Returns:
        Tuple of (httpx.Client configured for external URL, server details dict)

    Raises:
        KonicInferenceServerNotFoundError: If server doesn't exist
        typer.Exit: If server is not running
    """
    try:
        server = client.get_json(f"/inference/{server_id}")
    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicInferenceServerNotFoundError(server_id)
        raise

    status = server.get("status", "unknown")
    if status != InferenceServerStatus.RUNNING.value:
        console.print(f"[red]✗ Error:[/red] Server is not running (status: {status})")
        raise typer.Exit(1)

    external_url = server.get("external_url")
    if not external_url:
        console.print("[red]✗ Error:[/red] Server has no external URL configured")
        raise typer.Exit(1)

    external_client = httpx.Client(
        base_url=external_url,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=30.0,
    )

    return external_client, server


def _wait_for_server_ready(server_id: str, timeout: int = WAIT_DEFAULT_TIMEOUT_SECONDS) -> bool:
    """
    Poll server status until running or terminal state.

    Args:
        server_id: The inference server ID
        timeout: Maximum seconds to wait (clamped to 600s)

    Returns:
        True if server is running, False otherwise
    """
    timeout = min(timeout, WAIT_MAX_TIMEOUT_SECONDS)
    start_time = time.time()

    console.print(f"[cyan]Waiting for server to be ready (timeout: {timeout}s)...[/cyan]")

    while (time.time() - start_time) < timeout:
        try:
            response = client.get_json(f"/inference/{server_id}/status")
            status = response.get("status", "unknown")

            if status == InferenceServerStatus.RUNNING.value:
                console.print("[bold green]✓[/bold green] Server is running!")
                return True
            elif status == InferenceServerStatus.ERROR.value:
                error_msg = response.get("error_message", "Unknown error")
                console.print(f"[red]✗ Server failed to start:[/red] {error_msg}")
                return False
            elif status == InferenceServerStatus.STOPPED.value:
                console.print("[yellow]Server was stopped unexpectedly[/yellow]")
                return False

            elapsed = int(time.time() - start_time)
            console.print(f"  Status: [yellow]{status}[/yellow] ({elapsed}s elapsed)", end="\r")
            time.sleep(WAIT_POLL_INTERVAL_SECONDS)

        except KonicHTTPError as e:
            if e.status_code == 404:
                console.print("[red]✗ Server not found[/red]")
                return False
            raise

    elapsed = int(time.time() - start_time)
    console.print(f"\n[yellow]Timeout after {elapsed}s - server still pending[/yellow]")
    return False


def _follow_logs(server_id: str, initial_tail: int = LOGS_DEFAULT_TAIL) -> None:
    """
    Follow inference server logs with deduplication.

    Polls logs every 3 seconds and prints new lines only.
    """
    seen_lines: set[str] = set()

    console.print("[cyan]Following logs...[/cyan] (Ctrl+C to stop)\n")

    try:
        response = client.get_json(f"/inference/{server_id}/logs", params={"tail": initial_tail})
        logs = response.get("logs", "")

        for line in logs.splitlines():
            line_hash = hashlib.md5(line.encode()).hexdigest()
            if line_hash not in seen_lines:
                seen_lines.add(line_hash)
                console.print(line)

        while True:
            time.sleep(LOGS_POLL_INTERVAL_SECONDS)

            try:
                status_response = client.get_json(f"/inference/{server_id}/status")
                status = status_response.get("status", "unknown")

                if status not in (
                    InferenceServerStatus.PENDING.value,
                    InferenceServerStatus.RUNNING.value,
                ):
                    console.print(f"\n[dim][Server {status}][/dim]")
                    break
            except KonicHTTPError:
                console.print("\n[dim][Server no longer available][/dim]")
                break

            response = client.get_json(
                f"/inference/{server_id}/logs",
                params={"tail": len(seen_lines) + 200},
            )
            logs = response.get("logs", "")

            for line in logs.splitlines():
                line_hash = hashlib.md5(line.encode()).hexdigest()
                if line_hash not in seen_lines:
                    seen_lines.add(line_hash)
                    console.print(line)

    except KeyboardInterrupt:
        console.print("\n[dim][Stopped following logs][/dim]")


def _display_server_table(servers: list[dict]) -> None:
    """Display inference servers in a Rich table."""
    table = Table(
        title="Inference Servers",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Server ID", style="dim")
    table.add_column("Agent", style="cyan")
    table.add_column("Artifact", style="dim")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Requests", justify="right")
    table.add_column("Created At")

    for server in servers:
        status = server.get("status", "unknown")
        server_type = server.get("server_type", "http")

        table.add_row(
            server.get("id", "N/A"),
            server.get("agent_name", "N/A"),
            server.get("artifact_id", "N/A")[:12] if server.get("artifact_id") else "N/A",
            server_type,
            f"[{_get_status_style(status)}]{status}[/]",
            _format_count(server.get("request_count")),
            server.get("created_at", "N/A")[:19].replace("T", " "),
        )

    console.print(table)


def _display_server_detail(server: dict) -> None:
    """Display inference server details in a Rich panel."""
    status = server.get("status", "unknown")
    server_type = server.get("server_type", "http")

    content = f"""[bold cyan]Server ID:[/bold cyan] {server.get('id', 'N/A')}
[bold cyan]Artifact ID:[/bold cyan] {server.get('artifact_id', 'N/A')}
[bold cyan]Agent:[/bold cyan] {server.get('agent_name', 'N/A')} ({server.get('agent_id', 'N/A')})
[bold cyan]Training Job:[/bold cyan] {server.get('training_job_id', 'N/A')}
[bold cyan]Iteration:[/bold cyan] {server.get('iteration', 'N/A')}
[bold cyan]Server Type:[/bold cyan] {server_type}
[bold cyan]Status:[/bold cyan] [{_get_status_style(status)}]{status}[/]
[bold cyan]Container:[/bold cyan] {server.get('container_name', 'N/A')}
[bold cyan]External URL:[/bold cyan] {server.get('external_url', 'N/A')}
[bold cyan]External Port:[/bold cyan] {server.get('external_port', 'N/A')}
[bold cyan]Auto-stop:[/bold cyan] {server.get('auto_stop_minutes', 'Disabled') or 'Disabled'} minutes
[bold cyan]Created:[/bold cyan] {server.get('created_at', 'N/A')[:19].replace('T', ' ') if server.get('created_at') else 'N/A'}
[bold cyan]Started:[/bold cyan] {server.get('started_at', 'N/A')[:19].replace('T', ' ') if server.get('started_at') else 'Not started'}
[bold cyan]Requests:[/bold cyan] {_format_count(server.get('request_count'))}"""

    if server.get("error_message"):
        content += f"\n\n[bold red]Error:[/bold red] {server.get('error_message')}"

    console.print(Panel(content, title="Inference Server Details", border_style="blue"))


def _display_status_detail(status_data: dict) -> None:
    """Display inference server status in a Rich panel."""
    status = status_data.get("status", "unknown")
    container_status = status_data.get("container_status", "unknown")

    content = f"""[bold cyan]Server ID:[/bold cyan] {status_data.get('id', 'N/A')}
[bold cyan]Status:[/bold cyan] [{_get_status_style(status)}]{status}[/]
[bold cyan]Container Status:[/bold cyan] {container_status}
[bold cyan]Internal URL:[/bold cyan] {status_data.get('internal_url', 'N/A')}
[bold cyan]External URL:[/bold cyan] {status_data.get('external_url', 'N/A')}
[bold cyan]Uptime:[/bold cyan] {_format_uptime(status_data.get('uptime_seconds'))}
[bold cyan]Last Request:[/bold cyan] {status_data.get('last_request_at', 'N/A')[:19].replace('T', ' ') if status_data.get('last_request_at') else 'Never'}
[bold cyan]Total Requests:[/bold cyan] {_format_count(status_data.get('request_count'))}"""

    console.print(Panel(content, title="Inference Server Status", border_style="cyan"))


def _display_model_info(info: dict, server_id: str) -> None:
    """Display model info in a Rich panel."""
    loaded = info.get("loaded", False)

    if not loaded:
        console.print("[yellow]No model currently loaded on this server.[/yellow]")
        return

    obs_space = info.get("observation_space", {})
    action_space = info.get("action_space", {})

    obs_str = json.dumps(obs_space) if obs_space else "N/A"
    action_str = json.dumps(action_space) if action_space else "N/A"

    content = f"""[bold cyan]Model Loaded:[/bold cyan] [green]Yes[/green]
[bold cyan]Artifact ID:[/bold cyan] {info.get('artifact_id', 'N/A')}
[bold cyan]Agent:[/bold cyan] {info.get('agent_name', 'N/A')} ({info.get('agent_id', 'N/A')})
[bold cyan]Training Job:[/bold cyan] {info.get('training_job_id', 'N/A')}
[bold cyan]Iteration:[/bold cyan] {info.get('iteration', 'N/A')}
[bold cyan]Artifact Type:[/bold cyan] {info.get('artifact_type', 'N/A')}
[bold cyan]Loaded At:[/bold cyan] {info.get('loaded_at', 'N/A')[:19].replace('T', ' ') if info.get('loaded_at') else 'N/A'}
[bold cyan]Observation Space:[/bold cyan] {obs_str}
[bold cyan]Action Space:[/bold cyan] {action_str}"""

    console.print(Panel(content, title="Model Information", border_style="green"))


@app.command(name="start")
@error_handler(exit_on_error=True)
@loading_indicator(message="Starting inference server...")
def start_server(
    artifact_id: Annotated[
        str,
        typer.Argument(
            help="Artifact ID of the trained model to deploy",
        ),
    ],
    server_type: Annotated[
        str,
        typer.Option(
            "--type",
            "-t",
            help="Server type: 'http' for REST API or 'websocket' for streaming",
        ),
    ] = "http",
    auto_stop: Annotated[
        int | None,
        typer.Option(
            "--auto-stop",
            help="Auto-stop after N minutes of inactivity (0 = disabled)",
        ),
    ] = None,
    wait: Annotated[
        bool,
        typer.Option(
            "--wait",
            "-w",
            help="Wait for server to be ready before returning",
        ),
    ] = False,
    timeout: Annotated[
        int,
        typer.Option(
            "--timeout",
            help="Timeout in seconds when using --wait (max 600)",
            min=1,
            max=600,
        ),
    ] = WAIT_DEFAULT_TIMEOUT_SECONDS,
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
    Start a new inference server for a trained model artifact.

    Creates and starts a Docker container that serves the model for
    real-time predictions via HTTP REST API or WebSocket.

    The server exposes endpoints for predictions at the external URL
    shown in the output.

    Example:
        konic inference start art_a1b2c3d4
        konic inference start art_a1b2c3d4 --type websocket
        konic inference start art_a1b2c3d4 --auto-stop 30 --wait
        konic inference start art_a1b2c3d4 -w --timeout 120
    """
    _apply_host_override(host)

    if server_type not in ("http", "websocket"):
        console.print(
            f"[red]✗ Error:[/red] Invalid server type '{server_type}'. Must be 'http' or 'websocket'."
        )
        raise typer.Exit(1)

    payload: dict[str, Any] = {
        "artifact_id": artifact_id,
        "server_type": server_type,
    }
    if auto_stop is not None and auto_stop > 0:
        payload["auto_stop_minutes"] = auto_stop

    result = client.post_json("/inference", json=payload)

    console.print("\n[bold green]✓[/bold green] Inference server started successfully!")

    if auto_stop and auto_stop > 0:
        console.print(f"  [cyan]Auto-stop:[/cyan] after {auto_stop} minutes of inactivity")

    _display_server_detail(result)

    if wait:
        console.print()
        success = _wait_for_server_ready(result["id"], timeout)
        if not success:
            raise typer.Exit(1)


@app.command(name="list")
@error_handler(exit_on_error=True)
@loading_indicator(message="Fetching inference servers...")
def list_servers(
    status: Annotated[
        str | None,
        typer.Option(
            "--status",
            "-s",
            help="Filter by status (pending/running/stopped/error)",
        ),
    ] = None,
    agent: Annotated[
        str | None,
        typer.Option(
            "--agent",
            help="Filter by agent ID or name",
        ),
    ] = None,
    artifact: Annotated[
        str | None,
        typer.Option(
            "--artifact",
            help="Filter by artifact ID",
        ),
    ] = None,
    server_type: Annotated[
        str | None,
        typer.Option(
            "--type",
            "-t",
            help="Filter by server type (http/websocket)",
        ),
    ] = None,
    active: Annotated[
        bool,
        typer.Option(
            "--active",
            help="Show only active servers (pending or running)",
        ),
    ] = False,
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            "-l",
            help="Maximum number of servers to return",
            min=1,
            max=100,
        ),
    ] = 50,
    offset: Annotated[
        int,
        typer.Option(
            "--offset",
            help="Number of servers to skip (for pagination)",
            min=0,
        ),
    ] = 0,
    order: Annotated[
        str,
        typer.Option(
            "--order",
            "-o",
            help="Sort order by created_at (asc/desc)",
        ),
    ] = "desc",
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
    List inference servers.

    By default, lists all inference servers. Use filters to narrow down
    the results.

    Example:
        konic inference list
        konic inference list --active
        konic inference list --status running
        konic inference list --type http --limit 10
        konic inference list --agent my-agent --order asc
        konic inference list --offset 10 --limit 20 --json
    """
    _apply_host_override(host)

    order_upper = order.upper()
    if order_upper not in ("ASC", "DESC"):
        console.print(f"[red]✗ Error:[/red] Invalid order '{order}'. Must be 'asc' or 'desc'.")
        raise typer.Exit(1)

    if server_type and server_type not in ("http", "websocket"):
        console.print(
            f"[red]✗ Error:[/red] Invalid server type '{server_type}'. Must be 'http' or 'websocket'."
        )
        raise typer.Exit(1)

    if active:
        servers = client.get_json("/inference/active")
    else:
        params: dict[str, Any] = {
            "_start": offset,
            "_end": offset + limit,
            "_order": order_upper,
        }
        if status:
            params["status"] = status
        if agent:
            params["agent_id"] = agent
        if artifact:
            params["artifact_id"] = artifact
        if server_type:
            params["server_type"] = server_type

        servers = client.get_json("/inference", params=params)

    if output_json:
        console.print_json(json.dumps(servers, indent=2))
        return

    if not servers:
        console.print("[yellow]No inference servers found.[/yellow]")
        return

    _display_server_table(servers)

    if len(servers) == limit:
        console.print(
            f"\n[dim]Showing {len(servers)} servers (offset: {offset}). Use --offset {offset + limit} to see more.[/dim]"
        )


@app.command(name="status")
@error_handler(exit_on_error=True)
@loading_indicator(message="Fetching server status...")
def get_status(
    server_id: Annotated[
        str,
        typer.Argument(
            help="Inference server ID",
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
    Get the status of an inference server.

    Shows real-time status including container health, uptime,
    and request statistics.

    Example:
        konic inference status a1b2c3d4e5f6
        konic inference status a1b2c3d4e5f6 --json
    """
    _apply_host_override(host)

    try:
        status_data = client.get_json(f"/inference/{server_id}/status")
    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicInferenceServerNotFoundError(server_id)
        raise

    if output_json:
        console.print_json(json.dumps(status_data, indent=2))
        return

    _display_status_detail(status_data)


@app.command(name="stop")
@error_handler(exit_on_error=True)
def stop_server(
    server_id: Annotated[
        str,
        typer.Argument(
            help="Inference server ID to stop",
        ),
    ],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Skip confirmation prompt",
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
    Stop and remove an inference server.

    This will stop the Docker container and remove the server.
    The action cannot be undone.

    Example:
        konic inference stop a1b2c3d4e5f6
        konic inference stop a1b2c3d4e5f6 --force
    """
    _apply_host_override(host)

    if not force:
        confirm = typer.confirm(f"Are you sure you want to stop inference server '{server_id}'?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    with console.status("[cyan]Stopping inference server...[/cyan]"):
        try:
            client.delete_json(f"/inference/{server_id}")
        except KonicHTTPError as e:
            if e.status_code == 404:
                raise KonicInferenceServerNotFoundError(server_id)
            raise

    console.print(
        f"[bold green]✓[/bold green] Inference server '{server_id}' stopped successfully!"
    )


@app.command(name="logs")
@error_handler(exit_on_error=True)
def get_logs(
    server_id: Annotated[
        str,
        typer.Argument(
            help="Inference server ID",
        ),
    ],
    tail: Annotated[
        int,
        typer.Option(
            "--tail",
            "-n",
            help="Number of log lines to retrieve",
        ),
    ] = LOGS_DEFAULT_TAIL,
    follow: Annotated[
        bool,
        typer.Option(
            "--follow",
            "-f",
            help="Follow log output continuously",
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
    Get logs from an inference server.

    Retrieves container logs from the inference server. Use --follow
    to continuously stream new log entries.

    Example:
        konic inference logs a1b2c3d4e5f6
        konic inference logs a1b2c3d4e5f6 --tail 500
        konic inference logs a1b2c3d4e5f6 --follow
        konic inference logs a1b2c3d4e5f6 -n 200 -f
    """
    _apply_host_override(host)

    if follow:
        _follow_logs(server_id, initial_tail=tail)
        return

    with console.status("[cyan]Fetching logs...[/cyan]"):
        try:
            result = client.get_json(f"/inference/{server_id}/logs", params={"tail": tail})
        except KonicHTTPError as e:
            if e.status_code == 404:
                raise KonicInferenceServerNotFoundError(server_id)
            raise

    logs = result.get("logs", "")
    if logs:
        console.print(logs)
    else:
        console.print("[dim]No logs available.[/dim]")


@app.command(name="predict")
@error_handler(exit_on_error=True)
def predict(
    server_id: Annotated[
        str,
        typer.Argument(
            help="Inference server ID",
        ),
    ],
    observation: Annotated[
        str | None,
        typer.Option(
            "--observation",
            "-o",
            help="Observation as JSON array (e.g., '[0.1, 0.2, 0.3, 0.4]')",
        ),
    ] = None,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-f",
            help="Read observation from JSON file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    deterministic: Annotated[
        bool,
        typer.Option(
            "--deterministic",
            help="Use deterministic action selection",
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
    Send a prediction request to a running inference server.

    Sends an observation to the inference server and returns the
    predicted action. Only works with HTTP-type servers.

    For WebSocket servers, use programmatic integration directly
    with the external URL.

    Example:
        konic inference predict a1b2c3d4e5f6 -o "[0.1, 0.2, 0.3, 0.4]"
        konic inference predict a1b2c3d4e5f6 --file observation.json
        konic inference predict a1b2c3d4e5f6 -o "[1, 2, 3]" --deterministic
    """
    _apply_host_override(host)

    if observation is None and file is None:
        console.print("[red]✗ Error:[/red] Must provide --observation or --file")
        raise typer.Exit(1)

    if observation is not None and file is not None:
        console.print("[red]✗ Error:[/red] Cannot use both --observation and --file")
        raise typer.Exit(1)

    try:
        if file:
            with open(file) as f:
                obs_data = json.load(f)
        else:
            obs_data = json.loads(observation)  # type: ignore
    except json.JSONDecodeError as e:
        console.print(f"[red]✗ Error:[/red] Invalid JSON: {e}")
        raise typer.Exit(1)

    with console.status("[cyan]Connecting to inference server...[/cyan]"):
        external_client, server = _get_external_client(server_id)

    server_type = server.get("server_type", "http")
    if server_type == "websocket":
        external_url = server.get("external_url", "N/A")
        console.print(
            f"[yellow]⚠ WebSocket servers require programmatic integration.[/yellow]\n"
            f"  Use the external URL directly: {external_url}/ws/predict"
        )
        raise typer.Exit(1)

    try:
        with console.status("[cyan]Sending prediction request...[/cyan]"):
            response = external_client.post(
                "/predict",
                json={
                    "observation": obs_data,
                    "deterministic": deterministic,
                },
            )
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPStatusError as e:
        console.print(f"[red]✗ Prediction failed:[/red] HTTP {e.response.status_code}")
        try:
            error_detail = e.response.json()
            console.print(f"  {error_detail}")
        except Exception:
            console.print(f"  {e.response.text}")
        raise typer.Exit(1)
    except httpx.RequestError as e:
        console.print(f"[red]✗ Connection error:[/red] {e}")
        raise typer.Exit(1)
    finally:
        external_client.close()

    console.print_json(json.dumps(result, indent=2))


@app.command(name="info")
@error_handler(exit_on_error=True)
def get_info(
    server_id: Annotated[
        str,
        typer.Argument(
            help="Inference server ID",
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
    Get model information from an inference server.

    Shows details about the loaded model including artifact ID,
    observation space, and action space.

    Example:
        konic inference info a1b2c3d4e5f6
        konic inference info a1b2c3d4e5f6 --json
    """
    _apply_host_override(host)

    with console.status("[cyan]Connecting to inference server...[/cyan]"):
        external_client, _server = _get_external_client(server_id)

    try:
        with console.status("[cyan]Fetching model info...[/cyan]"):
            response = external_client.get("/model/info")
            response.raise_for_status()
            info = response.json()
    except httpx.HTTPStatusError as e:
        console.print(f"[red]✗ Failed to get model info:[/red] HTTP {e.response.status_code}")
        raise typer.Exit(1)
    except httpx.RequestError as e:
        console.print(f"[red]✗ Connection error:[/red] {e}")
        raise typer.Exit(1)
    finally:
        external_client.close()

    if output_json:
        console.print_json(json.dumps(info, indent=2))
        return

    _display_model_info(info, server_id)
