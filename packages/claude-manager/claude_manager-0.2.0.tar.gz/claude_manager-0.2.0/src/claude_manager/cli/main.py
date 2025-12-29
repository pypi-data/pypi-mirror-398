"""Main CLI entry point for claude-manager."""

import typer
from rich.console import Console

from claude_manager import __version__

app = typer.Typer(
    name="claude-manager",
    help="Gestionnaire de bibliothèque d'agents et serveurs MCP pour Claude Code",
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"claude-manager version {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Afficher la version",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Claude Manager - Gestionnaire de bibliothèque d'agents et serveurs MCP."""
    pass


# Import and register sub-commands
from claude_manager.cli.analyze import analyze
from claude_manager.cli.config import config_app
from claude_manager.cli.hook import hook_app
from claude_manager.cli.library import library_app
from claude_manager.cli.mcp import mcp_app
from claude_manager.cli.sync import sync_app

app.add_typer(sync_app, name="sync", help="Synchroniser la bibliothèque")
app.add_typer(mcp_app, name="mcp", help="Gérer les serveurs MCP")
app.add_typer(hook_app, name="hook", help="Gérer les hooks")
app.command(name="analyze")(analyze)
app.add_typer(library_app, name="library", help="Explorer la bibliothèque")
app.add_typer(config_app, name="config", help="Configuration")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
