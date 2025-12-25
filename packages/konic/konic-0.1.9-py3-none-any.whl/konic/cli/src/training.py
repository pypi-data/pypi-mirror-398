"""CLI commands for managing training jobs on Konic Cloud Platform."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Annotated, Any

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from konic.cli.client import client
from konic.cli.decorators import error_handler, loading_indicator
from konic.cli.enums import SSEEventType, TrainingStatus
from konic.cli.env_keys import KonicCLIEnvVars
from konic.cli.utils import resolve_agent_identifier
from konic.common.errors import (
    KonicHTTPError,
    KonicTrainingJobError,
    KonicTrainingJobNotFoundError,
)

if TYPE_CHECKING:
    pass

app = typer.Typer(
    name="train",
    help="Manage training jobs on Konic Cloud Platform",
    no_args_is_help=True,
)

console = Console()


def _apply_host_override(host: str | None) -> None:
    """Apply host override if provided."""
    if host:
        client.set_base_url(host)


def _get_status_style(status: str) -> str:
    """Get Rich style for training status."""
    styles = {
        TrainingStatus.PENDING.value: "yellow",
        TrainingStatus.INITIALIZING.value: "cyan",
        TrainingStatus.RUNNING.value: "blue",
        TrainingStatus.COMPLETED.value: "green",
        TrainingStatus.FAILED.value: "red",
        TrainingStatus.CANCELLED.value: "dim",
    }
    return styles.get(status, "white")


def _format_duration(seconds: float | None) -> str:
    """Format duration in human-readable format."""
    if seconds is None:
        return "N/A"
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    hours = seconds / 3600
    return f"{hours:.1f}h"


def _display_job_table(jobs: list[dict]) -> None:
    """Display training jobs in a Rich table."""
    table = Table(
        title="Training Jobs",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Job ID", style="dim")
    table.add_column("Agent", style="cyan")
    table.add_column("Status")
    table.add_column("Progress", justify="right")
    table.add_column("Created At")

    for job in jobs:
        status = job.get("status", "unknown")
        iterations = job.get("iterations", 0)
        current = job.get("current_iteration", 0)
        progress = f"{current}/{iterations}" if iterations > 0 else "N/A"

        table.add_row(
            job.get("id", "N/A"),
            job.get("agent_name", "N/A"),
            f"[{_get_status_style(status)}]{status}[/]",
            progress,
            job.get("created_at", "N/A")[:19].replace("T", " "),
        )

    console.print(table)


def _display_job_detail(job: dict) -> None:
    """Display training job details in a Rich panel."""
    status = job.get("status", "unknown")

    content = f"""[bold cyan]Job ID:[/bold cyan] {job.get('id', 'N/A')}
[bold cyan]Agent:[/bold cyan] {job.get('agent_name', 'N/A')} ({job.get('agent_version', 'N/A')})
[bold cyan]Agent ID:[/bold cyan] {job.get('agent_id', 'N/A')}
[bold cyan]Status:[/bold cyan] [{_get_status_style(status)}]{status}[/]
[bold cyan]Progress:[/bold cyan] {job.get('current_iteration', 0)}/{job.get('iterations', 0)} iterations
[bold cyan]MLflow Run ID:[/bold cyan] {job.get('mlflow_run_id', 'N/A')}
[bold cyan]MLflow Experiment:[/bold cyan] {job.get('mlflow_experiment_id', 'N/A')}
[bold cyan]Container ID:[/bold cyan] {job.get('container_id', 'N/A') if job.get('container_id') else 'N/A'}
[bold cyan]Created:[/bold cyan] {job.get('created_at', 'N/A')[:19].replace('T', ' ')}
[bold cyan]Started:[/bold cyan] {job.get('started_at', 'N/A')[:19].replace('T', ' ') if job.get('started_at') else 'Not started'}
[bold cyan]Completed:[/bold cyan] {job.get('completed_at', 'N/A')[:19].replace('T', ' ') if job.get('completed_at') else 'Not completed'}"""

    if job.get("error_message"):
        content += f"\n\n[bold red]Error:[/bold red] {job.get('error_message')}"

    console.print(Panel(content, title="Training Job Details", border_style="blue"))


def _display_metrics_table(metrics: dict) -> None:
    """Display training metrics in a Rich table."""
    if not metrics.get("iterations"):
        console.print("[yellow]No metrics available yet.[/yellow]")
        return

    table = Table(
        title="Training Metrics",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Iteration", justify="right", style="dim")
    table.add_column("Return", justify="right", style="green")
    table.add_column("Episode Length", justify="right")
    table.add_column("FPS", justify="right", style="cyan")
    table.add_column("Time (s)", justify="right")
    table.add_column("Policy Loss", justify="right")
    table.add_column("Value Loss", justify="right")

    iterations = metrics.get("iterations", [])
    returns = metrics.get("episode_return_mean", [])
    lengths = metrics.get("episode_length_mean", [])
    fps_list = metrics.get("fps", [])
    times = metrics.get("time_total_s", [])
    policy_losses = metrics.get("policy_loss", [])
    value_losses = metrics.get("value_loss", [])

    for i in range(len(iterations)):
        table.add_row(
            str(iterations[i]) if i < len(iterations) else "N/A",
            f"{returns[i]:.2f}" if i < len(returns) else "N/A",
            f"{lengths[i]:.1f}" if i < len(lengths) else "N/A",
            f"{fps_list[i]:.0f}" if i < len(fps_list) else "N/A",
            f"{times[i]:.1f}" if i < len(times) else "N/A",
            f"{policy_losses[i]:.4f}" if i < len(policy_losses) else "N/A",
            f"{value_losses[i]:.4f}" if i < len(value_losses) else "N/A",
        )

    console.print(table)


def _create_live_display(job: dict, metrics: dict | None = None) -> Table:
    """Create a live training display table."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Label", style="bold cyan")
    table.add_column("Value")

    status = job.get("status", "unknown")
    current = job.get("current_iteration", 0)
    total = job.get("iterations", 0)

    table.add_row("Status", f"[{_get_status_style(status)}]{status}[/]")
    progress_str = (
        f"{current}/{total} iterations ({100*current/total:.1f}%)" if total > 0 else "N/A"
    )
    table.add_row("Progress", progress_str)

    if metrics:
        table.add_row("Episode Return", f"{metrics.get('episode_return_mean', 0):.2f}")
        table.add_row("Episode Length", f"{metrics.get('episode_length_mean', 0):.1f}")
        table.add_row("FPS", f"{metrics.get('fps', 0):.0f}")
        table.add_row("Total Steps", f"{metrics.get('num_env_steps_lifetime', 0):,}")
        table.add_row("Training Time", _format_duration(metrics.get("time_total_s")))

        learner = metrics.get("learner_metrics", {})
        if learner:
            for _learner_id, data in learner.items():
                if isinstance(data, dict):
                    if "policy_loss" in data:
                        table.add_row("Policy Loss", f"{data['policy_loss']:.4f}")
                    if "value_loss" in data:
                        table.add_row("Value Loss", f"{data['value_loss']:.4f}")
                    if "entropy" in data:
                        table.add_row("Entropy", f"{data['entropy']:.4f}")

    return table


def _watch_training(job_id: str) -> None:
    """Watch training progress with live updates."""
    latest_metrics: dict[str, Any] = {}

    try:
        with Live(console=console, refresh_per_second=4) as live:
            for event in client.stream_sse(f"/training/jobs/{job_id}/stream"):
                event_type = event.get("event")
                data = event.get("data", {})

                if event_type == SSEEventType.STATUS.value:
                    job_data = {
                        "status": data.get("status"),
                        "current_iteration": data.get("current_iteration", 0),
                        "iterations": data.get("iterations", 0),
                    }
                    table = _create_live_display(
                        job_data, latest_metrics if latest_metrics else None
                    )
                    live.update(Panel(table, title="Training Progress", border_style="cyan"))

                    status = data.get("status")
                    if status in (
                        TrainingStatus.COMPLETED.value,
                        TrainingStatus.FAILED.value,
                        TrainingStatus.CANCELLED.value,
                    ):
                        console.print(f"\n[{_get_status_style(status)}]Training {status}![/]")
                        break

                elif event_type == SSEEventType.METRICS.value:
                    latest_metrics = data
                    job_data = {
                        "status": "running",
                        "current_iteration": data.get("iteration", 0),
                        "iterations": latest_metrics.get("total_iterations", 0),
                    }
                    table = _create_live_display(job_data, latest_metrics)
                    live.update(Panel(table, title="Training Progress", border_style="cyan"))

                elif event_type == SSEEventType.ERROR.value:
                    console.print(f"\n[red]Error: {data.get('error', 'Unknown error')}[/red]")
                    break

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped watching. Training continues in background.[/yellow]")


@app.command(name="start")
@error_handler(exit_on_error=True)
@loading_indicator(message="Starting training job...")
def start_training(
    agent: Annotated[
        str,
        typer.Argument(
            help="Agent ID or name to train",
        ),
    ],
    iterations: Annotated[
        int,
        typer.Option(
            "--iterations",
            "-i",
            help="Number of training iterations",
        ),
    ] = 100,
    checkpoint_interval: Annotated[
        int,
        typer.Option(
            "--checkpoint-interval",
            "-c",
            help="Save checkpoint every N iterations (0 = only save final)",
        ),
    ] = 0,
    host: Annotated[
        str | None,
        typer.Option(
            "--host",
            "-h",
            help="Override the Konic API host URL",
            envvar=KonicCLIEnvVars.KONIC_HOST.value,
        ),
    ] = None,
    watch: Annotated[
        bool,
        typer.Option(
            "--watch",
            "-w",
            help="Watch training progress after starting",
        ),
    ] = False,
) -> None:
    """
    Start a new training job for an agent.

    This command initiates training for the specified agent on the
    Konic Cloud Platform. Training runs in an isolated Docker container
    with metrics tracked via MLflow.

    Checkpoints can be saved periodically during training using the
    --checkpoint-interval option. Set to 0 (default) to only save
    the final model.

    Example:
        konic train start my-agent --iterations 100
        konic train start my-agent -i 100 -c 25  # Save checkpoint every 25 iterations
        konic train start 550e8400-e29b-41d4-a716-446655440000 -i 500 --watch
    """
    _apply_host_override(host)

    agent_id = resolve_agent_identifier(client, agent)

    payload: dict[str, Any] = {"iterations": iterations}
    if checkpoint_interval > 0:
        payload["checkpoint_interval"] = checkpoint_interval

    result = client.post_json(
        f"/training/agents/{agent_id}/start",
        json=payload,
    )

    console.print("\n[bold green]✓[/bold green] Training job started successfully!")

    if checkpoint_interval > 0:
        console.print(f"  [cyan]Checkpoint interval:[/cyan] every {checkpoint_interval} iterations")
    else:
        console.print("  [cyan]Checkpoints:[/cyan] final model only")

    _display_job_detail(result)

    if watch:
        console.print("\n[cyan]Watching training progress...[/cyan] (Ctrl+C to stop watching)\n")
        _watch_training(result["id"])


@app.command(name="status")
@error_handler(exit_on_error=True)
@loading_indicator(message="Fetching training job status...")
def get_status(
    job_id: Annotated[
        str,
        typer.Argument(
            help="Training job ID",
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
) -> None:
    """
    Get the current status and details of a training job.

    Displays job information including status, progress, timing,
    and associated MLflow experiment details.

    Example:
        konic train status 550e8400-e29b-41d4-a716-446655440000
    """
    _apply_host_override(host)

    try:
        result = client.get_json(f"/training/jobs/{job_id}")
        _display_job_detail(result)
    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicTrainingJobNotFoundError(job_id)
        raise


@app.command(name="list")
@error_handler(exit_on_error=True)
@loading_indicator(message="Fetching training jobs...")
def list_jobs(
    agent: Annotated[
        str,
        typer.Argument(
            help="Agent ID or name",
        ),
    ],
    status: Annotated[
        str | None,
        typer.Option(
            "--status",
            "-s",
            help="Filter by status (pending, running, completed, failed, cancelled)",
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
    List all training jobs for a specific agent.

    Shows job ID, status, progress, and timestamps. Use --status
    to filter by job state (pending, running, completed, failed, cancelled).

    Example:
        konic train list my-agent
        konic train list my-agent --status running
        konic train list my-agent --status completed
    """
    _apply_host_override(host)

    agent_id = resolve_agent_identifier(client, agent)

    params = {}
    if status:
        params["status"] = status

    result = client.get_json(f"/training/agents/{agent_id}/jobs", params=params if params else None)

    if not result:
        console.print("[yellow]No training jobs found for this agent.[/yellow]")
        return

    _display_job_table(result)


@app.command(name="logs")
@error_handler(exit_on_error=True)
def get_logs(
    job_id: Annotated[
        str,
        typer.Argument(
            help="Training job ID",
        ),
    ],
    tail: Annotated[
        int,
        typer.Option(
            "--tail",
            "-t",
            help="Number of lines to show from the end",
        ),
    ] = 100,
    follow: Annotated[
        bool,
        typer.Option(
            "--follow",
            "-f",
            help="Follow log output (stream updates)",
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
    View training job logs.

    Displays the training logs from the job container. Use --tail to
    limit the number of lines shown, or --follow to stream logs in
    real-time as training progresses.

    Example:
        konic train logs 550e8400-e29b-41d4-a716-446655440000
        konic train logs 550e8400-e29b-41d4-a716-446655440000 --tail 50
        konic train logs 550e8400-e29b-41d4-a716-446655440000 --follow
    """
    _apply_host_override(host)

    try:
        if follow:
            console.print("[cyan]Following logs...[/cyan] (Ctrl+C to stop)\n")
            try:
                for event in client.stream_sse(f"/training/jobs/{job_id}/stream"):
                    event_type = event.get("event")
                    data = event.get("data", {})

                    if event_type == SSEEventType.ERROR.value:
                        console.print(f"[red]Error: {data.get('error', 'Unknown error')}[/red]")
                        break
                    elif event_type == SSEEventType.STATUS.value:
                        status = data.get("status")
                        if status in (
                            TrainingStatus.COMPLETED.value,
                            TrainingStatus.FAILED.value,
                            TrainingStatus.CANCELLED.value,
                        ):
                            console.print(f"\n[{_get_status_style(status)}]Training {status}[/]")
                            break
                    elif event_type == SSEEventType.METRICS.value:
                        iteration = data.get("iteration", "?")
                        ret = data.get("episode_return_mean", 0)
                        fps = data.get("fps", 0)
                        console.print(
                            f"[dim]Iteration {iteration}:[/dim] return={ret:.2f}, fps={fps:.0f}"
                        )
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopped following logs.[/yellow]")
        else:
            result = client.get_json(f"/training/jobs/{job_id}/logs", params={"tail": tail})
            logs = result.get("logs", "")
            if logs:
                console.print(logs)
            else:
                console.print("[yellow]No logs available yet.[/yellow]")

    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicTrainingJobNotFoundError(job_id)
        raise


@app.command(name="cancel")
@error_handler(exit_on_error=True)
@loading_indicator(message="Cancelling training job...")
def cancel_job(
    job_id: Annotated[
        str,
        typer.Argument(
            help="Training job ID to cancel",
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
    Cancel a running training job.

    Stops the training job and terminates the associated container.
    Any checkpoints saved before cancellation are preserved.
    Use --force to skip the confirmation prompt.

    Example:
        konic train cancel 550e8400-e29b-41d4-a716-446655440000
        konic train cancel 550e8400-e29b-41d4-a716-446655440000 --force
    """
    _apply_host_override(host)

    if not force:
        confirm = typer.confirm(f"Are you sure you want to cancel training job {job_id}?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit()

    try:
        result = client.post_json(f"/training/jobs/{job_id}/cancel")
        console.print("[bold green]✓[/bold green] Training job cancelled successfully!")
        _display_job_detail(result)
    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicTrainingJobNotFoundError(job_id)
        if e.status_code == 400:
            raise KonicTrainingJobError(str(e.message), job_id)
        raise


@app.command(name="delete")
@error_handler(exit_on_error=True)
@loading_indicator(message="Deleting training job...")
def delete_job(
    job_id: Annotated[
        str,
        typer.Argument(
            help="Training job ID to delete",
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
    Delete a training job and its associated data.

    Permanently removes the training job record. This does not delete
    artifacts (checkpoints/models) created during training.
    Use --force to skip the confirmation prompt.

    Example:
        konic train delete 550e8400-e29b-41d4-a716-446655440000
        konic train delete 550e8400-e29b-41d4-a716-446655440000 --force
    """
    _apply_host_override(host)

    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete training job {job_id}?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit()

    try:
        client.delete(f"/training/jobs/{job_id}")
        console.print(f"[bold green]✓[/bold green] Training job {job_id} deleted successfully!")
    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicTrainingJobNotFoundError(job_id)
        raise


@app.command(name="metrics")
@error_handler(exit_on_error=True)
@loading_indicator(message="Fetching training metrics...")
def get_metrics(
    job_id: Annotated[
        str,
        typer.Argument(
            help="Training job ID",
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
            "-j",
            help="Output metrics as JSON",
        ),
    ] = False,
) -> None:
    """
    View training metrics history for a job.

    Displays a table of metrics including episode return, episode length,
    FPS, policy loss, and value loss across training iterations.
    Use --json for programmatic access to the raw metrics data.

    Example:
        konic train metrics 550e8400-e29b-41d4-a716-446655440000
        konic train metrics 550e8400-e29b-41d4-a716-446655440000 --json
    """
    _apply_host_override(host)

    try:
        result = client.get_json(f"/training/jobs/{job_id}/metrics")

        if output_json:
            console.print_json(json.dumps(result))
        else:
            _display_metrics_table(result)
    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicTrainingJobNotFoundError(job_id)
        raise


@app.command(name="watch")
@error_handler(exit_on_error=True)
def watch_job(
    job_id: Annotated[
        str,
        typer.Argument(
            help="Training job ID to watch",
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
) -> None:
    """
    Watch live training progress.

    Connects to the training job stream and displays real-time
    metrics updates. Press Ctrl+C to stop watching (training
    continues in background).

    Example:
        konic train watch 550e8400-e29b-41d4-a716-446655440000
    """
    _apply_host_override(host)

    try:
        job = client.get_json(f"/training/jobs/{job_id}")
    except KonicHTTPError as e:
        if e.status_code == 404:
            raise KonicTrainingJobNotFoundError(job_id)
        raise

    status = job.get("status")
    if status in (
        TrainingStatus.COMPLETED.value,
        TrainingStatus.FAILED.value,
        TrainingStatus.CANCELLED.value,
    ):
        console.print(
            f"[yellow]Training job already {status}. "
            "Use 'konic train metrics' to view results.[/yellow]"
        )
        _display_job_detail(job)
        return

    console.print(f"[cyan]Watching training job {job_id}...[/cyan] (Ctrl+C to stop)\n")
    _watch_training(job_id)
