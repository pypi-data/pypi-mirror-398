"""Beautiful and useful decorators for Konic CLI commands."""

import functools
import json
import time
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

from konic.common.errors import KonicCLIError

__all__ = [
    "stdout_handler",
    "json_output",
    "pretty_output",
    "error_handler",
    "loading_indicator",
    "success_message",
    "table_output",
    "benchmark",
]

console = Console()
F = TypeVar("F", bound=Callable[..., Any])


class OutputFormat(str, Enum):
    """Output format options for CLI commands."""

    JSON = "json"
    PRETTY = "pretty"
    PLAIN = "plain"


def error_handler(
    exit_on_error: bool = True,
    show_traceback: bool = False,
) -> Callable[[F], F]:
    """
    Decorator to handle errors gracefully with beautiful formatting.

    Args:
        exit_on_error: Whether to exit the CLI on error (default: True)
        show_traceback: Whether to show full traceback (default: False)

    Example:
        @error_handler(exit_on_error=True)
        @app.command()
        def my_command():
            pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KonicCLIError as e:
                console.print(f"\n[bold red]✗ Error:[/bold red] {e.message}", style="red")
                if show_traceback:
                    console.print_exception()
                if exit_on_error:
                    raise typer.Exit(code=getattr(e, "exit_code", 1))
                return None

            except (SystemExit, KeyboardInterrupt, typer.Exit):
                # Let these pass through without modification
                raise

            except Exception as e:
                console.print(f"\n[bold red]✗ Unexpected Error:[/bold red] {str(e)}", style="red")
                if show_traceback:
                    console.print_exception()
                if exit_on_error:
                    raise typer.Exit(code=1)
                return None

        return wrapper  # type: ignore

    return decorator


def stdout_handler[F: Callable[..., Any]](func: F) -> F:
    """
    Decorator that automatically prints the return value of CLI commands.
    Handles different types of output intelligently.

    Example:
        @stdout_handler
        @app.command()
        def get_config():
            return {"host": "localhost", "port": 8080}
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if result is not None:
            if isinstance(result, (dict | list)):
                console.print_json(data=result)
            elif isinstance(result, str):
                console.print(result)
            else:
                console.print(str(result))
        return result

    return wrapper  # type: ignore


def json_output(
    pretty: bool = True,
    indent: int = 2,
) -> Callable[[F], F]:
    """
    Decorator to output command results as JSON.

    Args:
        pretty: Whether to pretty-print the JSON (default: True)
        indent: Indentation level for pretty printing (default: 2)

    Example:
        @json_output(pretty=True)
        @app.command()
        def get_data():
            return {"key": "value"}
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if result is not None:
                if pretty:
                    console.print_json(data=result, indent=indent)
                else:
                    print(json.dumps(result, separators=(",", ":")))
            return result

        return wrapper  # type: ignore

    return decorator


def pretty_output(
    title: str | None = None,
    border_style: str = "blue",
) -> Callable[[F], F]:
    """
    Decorator to display output in a beautiful panel.

    Args:
        title: Optional title for the panel
        border_style: Color/style for the border (default: "blue")

    Example:
        @pretty_output(title="Configuration", border_style="green")
        @app.command()
        def show_config():
            return "host: localhost\\nport: 8080"
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if result is not None:
                if isinstance(result, dict):
                    content = json.dumps(result, indent=2)
                    syntax = Syntax(content, "json", theme="monokai", line_numbers=False)
                    console.print(Panel(syntax, title=title, border_style=border_style))
                else:
                    console.print(Panel(str(result), title=title, border_style=border_style))
            return result

        return wrapper  # type: ignore

    return decorator


def loading_indicator(
    message: str = "Processing...",
    success_message: str | None = None,
) -> Callable[[F], F]:
    """
    Decorator to show a loading spinner while command executes.

    Args:
        message: Message to display while loading (default: "Processing...")
        success_message: Message to display on success (default: None)

    Example:
        @loading_indicator(message="Fetching data from API...", success_message="Data retrieved!")
        @app.command()
        def fetch_data():
            time.sleep(2)
            return {"data": "value"}
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task(description=message, total=None)
                result = func(*args, **kwargs)

            if success_message:
                console.print(f"[bold green]✓[/bold green] {success_message}")

            return result

        return wrapper  # type: ignore

    return decorator


def success_message(message: str) -> Callable[[F], F]:
    """
    Decorator to display a success message after command execution.

    Args:
        message: Success message to display

    Example:
        @success_message("Configuration updated successfully!")
        @app.command()
        def update_config():
            pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            console.print(f"\n[bold green]✓[/bold green] {message}", style="green")
            return result

        return wrapper  # type: ignore

    return decorator


def table_output(
    title: str | None = None,
    columns: list[str] | None = None,
) -> Callable[[F], F]:
    """
    Decorator to display command results as a beautiful table.

    Args:
        title: Optional title for the table
        columns: Column names (auto-detected if not provided)

    Example:
        @table_output(title="Users", columns=["ID", "Name", "Email"])
        @app.command()
        def list_users():
            return [
                {"ID": 1, "Name": "Alice", "Email": "alice@example.com"},
                {"ID": 2, "Name": "Bob", "Email": "bob@example.com"},
            ]
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            if result is not None and isinstance(result, list) and len(result) > 0:
                table = Table(title=title, show_header=True, header_style="bold magenta")

                if columns:
                    for col in columns:
                        table.add_column(col)
                elif isinstance(result[0], dict):
                    for col in result[0].keys():
                        table.add_column(str(col))

                for item in result:
                    if isinstance(item, dict):
                        table.add_row(*[str(v) for v in item.values()])
                    else:
                        table.add_row(str(item))

                console.print(table)
            elif result is not None:
                console.print(result)

            return result

        return wrapper  # type: ignore

    return decorator


def benchmark(show_time: bool = True) -> Callable[[F], F]:
    """
    Decorator to measure and display command execution time.

    Args:
        show_time: Whether to display the execution time (default: True)

    Example:
        @benchmark(show_time=True)
        @app.command()
        def process_data():
            time.sleep(1)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time

            if show_time:
                console.print(
                    f"\n[dim]⏱  Executed in {elapsed_time:.2f}s[/dim]",
                    style="cyan",
                )

            return result

        return wrapper  # type: ignore

    return decorator
