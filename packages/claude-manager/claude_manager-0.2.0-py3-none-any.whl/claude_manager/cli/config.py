"""Config command - show and manage configuration."""

import typer
from rich.console import Console
from rich.panel import Panel

from claude_manager.core.paths import ClaudePaths

config_app = typer.Typer(help="Configuration", no_args_is_help=True)
console = Console()


@config_app.command("show")
def config_show() -> None:
    """Afficher la configuration actuelle."""
    from claude_manager import __version__

    console.print(Panel(f"[bold]Claude Manager v{__version__}[/bold]"))

    paths = ClaudePaths()

    console.print("\n[bold]Configuration:[/bold]")
    console.print(f"  Version: {__version__}")
    console.print(f"  Base globale: {paths.global_base}")


@config_app.command("paths")
def config_paths() -> None:
    """Afficher les chemins utilisés."""
    paths = ClaudePaths()

    console.print("\n[bold cyan]Chemins globaux[/bold cyan]")
    console.print(f"  Base:       {paths.global_base}")
    console.print(f"  Agents:     {paths.global_agents}")
    console.print(f"  Commands:   {paths.global_commands}")
    console.print(f"  Hooks:      {paths.global_hooks}")
    console.print(f"  Settings:   {paths.global_settings}")
    console.print(f"  Plugins:    {paths.global_plugins_config}")
    console.print(f"  État:       {paths.global_state_file}")

    console.print("\n[bold magenta]Chemins projet (non configuré)[/bold magenta]")
    console.print("  [dim]Utilisez 'claude-manager analyze <path>' pour configurer un projet[/dim]")

    # Check which paths exist
    console.print("\n[bold]Vérification des répertoires:[/bold]")

    checks = [
        ("Global base", paths.global_base),
        ("Agents", paths.global_agents),
        ("Commands", paths.global_commands),
        ("Hooks", paths.global_hooks),
    ]

    for name, path in checks:
        exists = path.exists()
        status = "[green]✓[/green]" if exists else "[red]✗[/red]"
        console.print(f"  {status} {name}: {path}")
