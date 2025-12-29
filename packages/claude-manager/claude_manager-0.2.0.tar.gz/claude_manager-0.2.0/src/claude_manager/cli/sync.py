"""Sync command - synchronize library with local installation."""

from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.table import Table

from claude_manager.core.paths import ClaudePaths

if TYPE_CHECKING:
    from claude_manager.core.differ import DiffResult

sync_app = typer.Typer(
    help="Synchroniser la bibliothèque avec l'installation locale",
    no_args_is_help=True,
)
console = Console()


@sync_app.command("global")
def sync_global(
    force: bool = typer.Option(False, "--force", "-f", help="Forcer sans confirmation"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simuler sans appliquer"),
) -> None:
    """Synchroniser les agents/commandes/hooks globaux vers ~/.claude/."""
    from claude_manager.core.differ import LibraryDiffer
    from claude_manager.core.installer import Installer
    from claude_manager.library.loader import LibraryLoader

    paths = ClaudePaths()
    loader = LibraryLoader()
    differ = LibraryDiffer(paths, loader)
    installer = Installer(paths, loader)

    console.print("\n[bold]Synchronisation globale[/bold]\n")

    # Get diffs for all types
    agent_diffs = differ.diff_agents(scope="global")
    command_diffs = differ.diff_commands(scope="global")
    hook_diffs = differ.diff_hooks(scope="global")

    # Filter to only show items needing sync
    agent_changes = [d for d in agent_diffs if d.status in ("new", "outdated", "modified")]
    command_changes = [d for d in command_diffs if d.status in ("new", "outdated", "modified")]
    hook_changes = [d for d in hook_diffs if d.status in ("new", "outdated", "modified")]

    if not agent_changes and not command_changes and not hook_changes:
        console.print("[green]Tout est synchronisé ![/green]")
        return

    # Show proposed changes
    if agent_changes:
        console.print("[bold]Agents:[/bold]")
        _show_diffs(agent_changes)

    if command_changes:
        console.print("\n[bold]Commandes:[/bold]")
        _show_diffs(command_changes)

    if hook_changes:
        console.print("\n[bold]Hooks:[/bold]")
        _show_diffs(hook_changes)

    if dry_run:
        console.print("\n[dim]--dry-run: aucune modification effectuée[/dim]")
        return

    # Confirm
    if not force:
        if not typer.confirm("\nAppliquer ces changements ?"):
            console.print("[dim]Opération annulée[/dim]")
            return

    # Apply changes
    console.print("\n[bold]Installation...[/bold]")

    if agent_changes:
        console.print("\n[dim]Agents:[/dim]")
        for diff in agent_changes:
            installer.install_agent(diff, scope="global")
            console.print(f"  [green]✓[/green] {diff.name}")

    if command_changes:
        console.print("\n[dim]Commandes:[/dim]")
        for diff in command_changes:
            installer.install_command(diff, scope="global")
            console.print(f"  [green]✓[/green] {diff.name}")

    if hook_changes:
        console.print("\n[dim]Hooks:[/dim]")
        for diff in hook_changes:
            installer.install_hook(diff, scope="global")
            console.print(f"  [green]✓[/green] {diff.name}")

        # Also update settings.json with hooks configuration
        console.print("\n[dim]Configuration hooks dans settings.json...[/dim]")
        if installer.install_hooks_settings():
            console.print("  [green]✓[/green] settings.json mis à jour")
        else:
            console.print("  [yellow]![/yellow] Pas de template hooks à appliquer")

    console.print("\n[green]Synchronisation terminée ![/green]")


@sync_app.command("project")
def sync_project(
    path: Path | None = typer.Argument(None, help="Chemin du projet (défaut: .)"),
    force: bool = typer.Option(False, "--force", "-f", help="Forcer sans confirmation"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simuler sans appliquer"),
) -> None:
    """Synchroniser les agents projet vers ./.claude/."""
    project_path = path or Path.cwd()

    if not project_path.exists():
        console.print(f"[red]Erreur: Le chemin {project_path} n'existe pas[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Synchronisation projet: {project_path}[/bold]\n")
    console.print(
        "[yellow]Utilisez 'claude-manager analyze' pour détecter automatiquement les agents adaptés[/yellow]"
    )


@sync_app.command("all")
def sync_all(
    path: Path | None = typer.Argument(None, help="Chemin du projet (défaut: .)"),
    force: bool = typer.Option(False, "--force", "-f", help="Forcer sans confirmation"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simuler sans appliquer"),
) -> None:
    """Synchroniser global + projet."""
    sync_global(force=force, dry_run=dry_run)
    sync_project(path=path, force=force, dry_run=dry_run)


@sync_app.command("status")
def sync_status(
    scope: str = typer.Option("all", "--scope", "-s", help="Scope: global, project, all"),
) -> None:
    """Afficher l'état de synchronisation."""
    from claude_manager.core.differ import LibraryDiffer
    from claude_manager.library.loader import LibraryLoader

    paths = ClaudePaths()
    loader = LibraryLoader()
    differ = LibraryDiffer(paths, loader)

    if scope in ("global", "all"):
        console.print("\n[bold]État global (~/.claude/)[/bold]")

        # Agents
        agent_diffs = differ.diff_agents(scope="global")
        if agent_diffs:
            console.print("\n[dim]Agents:[/dim]")
            _show_status_table(agent_diffs)

        # Commands
        command_diffs = differ.diff_commands(scope="global")
        if command_diffs:
            console.print("\n[dim]Commandes:[/dim]")
            _show_status_table(command_diffs)

        # Hooks
        hook_diffs = differ.diff_hooks(scope="global")
        if hook_diffs:
            console.print("\n[dim]Hooks:[/dim]")
            _show_status_table(hook_diffs)

    if scope in ("project", "all"):
        console.print("\n[bold]État projet (./.claude/)[/bold]\n")
        console.print(
            "[dim]Aucun projet configuré. Utilisez 'claude-manager analyze .' pour analyser.[/dim]"
        )


def _show_diffs(diffs: "list[DiffResult]") -> None:
    """Display proposed changes."""
    console.print("[bold]Changements proposés:[/bold]\n")
    for diff in diffs:
        if diff.status == "new":
            console.print(f"  [green]+ {diff.name}[/green] (nouveau)")
        elif diff.status == "outdated":
            console.print(
                f"  [yellow]↑ {diff.name}[/yellow] ({diff.local_version} → {diff.library_version})"
            )
        elif diff.status == "modified":
            console.print(f"  [blue]~ {diff.name}[/blue] (modifié localement)")


def _show_status_table(diffs: "list[DiffResult]") -> None:
    """Display status as a table."""
    table = Table()
    table.add_column("Nom")
    table.add_column("Statut")
    table.add_column("Version")

    status_display = {
        "new": ("⬇ à installer", "green"),
        "outdated": ("↑ mise à jour", "yellow"),
        "modified": ("~ modifié", "blue"),
        "custom": ("◆ custom", "dim"),
        "synced": ("✓ synchronisé", "green"),
    }

    for diff in diffs:
        # Get status value (handle both string and enum)
        status_key = diff.status.value if hasattr(diff.status, "value") else str(diff.status)
        display, color = status_display.get(status_key, (status_key, "white"))

        # Show version (library version, or local if custom)
        version = diff.library_version or diff.local_version or "-"

        table.add_row(
            diff.name,
            f"[{color}]{display}[/]",
            version,
        )

    if diffs:
        console.print(table)
    else:
        console.print("[dim]Aucun élément à afficher[/dim]")
