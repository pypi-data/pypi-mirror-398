"""Root CLI command group."""
from typing import Optional

import typer
from rich.console import Console

from planecompose import __version__
from planecompose.utils.logger import setup_logger
from planecompose.config.settings import get_settings


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        console = Console()
        console.print(f"[bold cyan]plane[/bold cyan] version [green]{__version__}[/green]")
        raise typer.Exit()


app = typer.Typer(
    name="plane",
    help="Plane CLI - Scaffold and sync projects with Plane",
    no_args_is_help=True,
)
console = Console()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-V", callback=version_callback, is_eager=True,
        help="Show version and exit"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """Plane CLI - Scaffold and sync projects with Plane."""
    # Setup logging
    settings = get_settings()
    settings.verbose = verbose
    settings.debug = debug or verbose
    
    log_file = settings.config_dir / "plane.log" if debug else None
    setup_logger(verbose=settings.debug, log_file=log_file)


# Register subcommands using lazy imports for faster startup
# Commands are only imported when actually invoked

def _register_commands():
    """
    Register all CLI commands.
    
    PERFORMANCE: Uses a function to group imports together.
    Typer handles actual command execution lazily.
    """
    from planecompose.cli import init as init_cmd
    from planecompose.cli import schema as schema_cmd
    from planecompose.cli import auth as auth_cmd
    from planecompose.cli import push as push_cmd
    from planecompose.cli import pull as pull_cmd
    from planecompose.cli import clone as clone_cmd
    from planecompose.cli import status as status_cmd
    from planecompose.cli import rate_stats as rate_stats_cmd
    from planecompose.cli import automations as automations_cmd

    app.command(name="init")(init_cmd.init)
    app.add_typer(schema_cmd.app, name="schema")
    app.add_typer(auth_cmd.app, name="auth")
    app.command(name="push")(push_cmd.push)
    app.command(name="pull")(pull_cmd.pull)
    app.command(name="clone")(clone_cmd.clone)
    app.command(name="status")(status_cmd.status)
    app.add_typer(rate_stats_cmd.app, name="rate")
    app.add_typer(automations_cmd.app, name="automations")

_register_commands()
