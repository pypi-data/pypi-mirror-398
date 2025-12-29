"""Hook command - manage Claude Code hooks."""

from typing import Any

import typer
from rich.console import Console
from rich.table import Table

hook_app = typer.Typer(help="Gérer les hooks", no_args_is_help=True)
console = Console()


@hook_app.command("list")
def hook_list(
    installed: bool = typer.Option(False, "--installed", "-i", help="Uniquement installés"),
    available: bool = typer.Option(False, "--available", "-a", help="Uniquement disponibles"),
) -> None:
    """Lister les hooks disponibles et installés."""
    import json

    from claude_manager.core.paths import ClaudePaths
    from claude_manager.library.loader import LibraryLoader

    loader = LibraryLoader()
    paths = ClaudePaths()

    # Load hooks index
    hooks_index = loader.get_hooks_index()
    global_hooks = hooks_index.get("global", [])
    optional_hooks = hooks_index.get("optional", [])

    # Load installed hooks from settings.json
    installed_hooks = set()
    if paths.global_settings.exists():
        try:
            settings = json.loads(paths.global_settings.read_text())
            hooks_config = settings.get("hooks", {})
            for event_hooks in hooks_config.values():
                for hook_group in event_hooks:
                    for hook in hook_group.get("hooks", []):
                        cmd = hook.get("command", "")
                        # Extract hook name from command
                        if "~/.claude/hooks/" in cmd:
                            name = cmd.split("/")[-1].replace(".sh", "").replace("bash ", "")
                            installed_hooks.add(name)
        except (json.JSONDecodeError, KeyError):
            pass

    if not installed and not available:
        # Show all
        console.print("\n[bold]Hooks standards (installés par défaut):[/bold]")
        _show_hooks_table(global_hooks, installed_hooks, show_status=True)

        console.print("\n[bold]Hooks optionnels:[/bold]")
        _show_hooks_table(optional_hooks, installed_hooks, show_status=True)
    elif installed:
        console.print("\n[bold]Hooks installés:[/bold]")
        all_hooks = global_hooks + optional_hooks
        installed_list = [h for h in all_hooks if h["name"] in installed_hooks]
        _show_hooks_table(installed_list, installed_hooks, show_status=False)
    else:
        console.print("\n[bold]Hooks disponibles (non installés):[/bold]")
        not_installed = [h for h in optional_hooks if h["name"] not in installed_hooks]
        _show_hooks_table(not_installed, installed_hooks, show_status=False)


def _show_hooks_table(
    hooks: list[dict[str, Any]], installed_hooks: set[str], show_status: bool = True
) -> None:
    """Display hooks in a table."""
    if not hooks:
        console.print("[dim]Aucun hook[/dim]")
        return

    table = Table()
    table.add_column("Nom")
    if show_status:
        table.add_column("Statut")
    table.add_column("Event")
    table.add_column("Description")

    for hook in hooks:
        name = hook["name"]
        is_installed = name in installed_hooks
        status = "[green]✓ installé[/green]" if is_installed else "[dim]disponible[/dim]"

        row = [name]
        if show_status:
            row.append(status)
        row.extend([hook.get("event", "-"), hook.get("description", "")[:50]])
        table.add_row(*row)

    console.print(table)


@hook_app.command("install")
def hook_install(
    hook_name: str | None = typer.Argument(None, help="Nom du hook à installer"),
) -> None:
    """Installer un hook optionnel."""
    import json

    from claude_manager.core.paths import ClaudePaths
    from claude_manager.library.loader import LibraryLoader

    loader = LibraryLoader()
    paths = ClaudePaths()

    # Load hooks index
    hooks_index = loader.get_hooks_index()
    optional_hooks = {h["name"]: h for h in hooks_index.get("optional", [])}

    # If no hook_name, show available optional hooks
    if not hook_name:
        console.print("\n[bold]Hooks optionnels disponibles:[/bold]\n")
        table = Table()
        table.add_column("Nom")
        table.add_column("Event")
        table.add_column("Description")

        for name, hook in optional_hooks.items():
            table.add_row(name, hook.get("event", "-"), hook.get("description", ""))

        console.print(table)
        console.print("\n[dim]Usage: claude-manager hook install <hook_name>[/dim]")
        return

    # Check if hook exists in optional
    if hook_name not in optional_hooks:
        console.print(f"[red]Erreur: Hook '{hook_name}' non trouvé dans les hooks optionnels[/red]")
        console.print("\nHooks optionnels disponibles:")
        for name in optional_hooks:
            console.print(f"  - {name}")
        raise typer.Exit(1)

    hook = optional_hooks[hook_name]

    # Install hook script
    hook_file = hook["file"]
    try:
        content = loader.get_hook_content(hook_file)
    except Exception as e:
        console.print(f"[red]Erreur: Impossible de charger le hook: {e}[/red]")
        raise typer.Exit(1) from None

    # Write hook script
    target_file = paths.global_hooks / f"{hook_name}.sh"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(content)

    # Make executable
    import os

    os.chmod(target_file, 0o755)

    # Update settings.json
    settings_file = paths.global_settings
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
        except json.JSONDecodeError:
            settings = {}
    else:
        settings = {}

    if "hooks" not in settings:
        settings["hooks"] = {}

    event = hook["event"]
    matcher = hook.get("matcher")

    if event not in settings["hooks"]:
        settings["hooks"][event] = []

    # Build hook entry
    hook_entry = {"type": "command", "command": f"bash ~/.claude/hooks/{hook_name}.sh"}

    # Find or create matcher group
    if matcher:
        # Find existing group with same matcher
        found = False
        for group in settings["hooks"][event]:
            if group.get("matcher") == matcher:
                # Add to existing group if not already there
                existing_commands = [h.get("command") for h in group.get("hooks", [])]
                if hook_entry["command"] not in existing_commands:
                    group["hooks"].append(hook_entry)
                found = True
                break

        if not found:
            # Create new group
            settings["hooks"][event].append({"matcher": matcher, "hooks": [hook_entry]})
    else:
        # No matcher - add to hooks list
        found = False
        for group in settings["hooks"][event]:
            if "matcher" not in group:
                existing_commands = [h.get("command") for h in group.get("hooks", [])]
                if hook_entry["command"] not in existing_commands:
                    group["hooks"].append(hook_entry)
                found = True
                break

        if not found:
            settings["hooks"][event].append({"hooks": [hook_entry]})

    # Write settings
    settings_file.write_text(json.dumps(settings, indent=2))

    console.print(f"[green]✓[/green] Hook '{hook_name}' installé")
    console.print(f"[dim]Script: {target_file}[/dim]")
    console.print(f"[dim]Configuration ajoutée à {settings_file}[/dim]")


@hook_app.command("remove")
def hook_remove(
    hook_name: str | None = typer.Argument(None, help="Nom du hook à désinstaller"),
) -> None:
    """Désinstaller un hook."""
    import json

    from claude_manager.core.paths import ClaudePaths

    paths = ClaudePaths()

    # Load installed hooks from settings.json
    settings_file = paths.global_settings
    if not settings_file.exists():
        console.print("[dim]Aucun hook installé[/dim]")
        return

    try:
        settings = json.loads(settings_file.read_text())
    except json.JSONDecodeError:
        console.print("[red]Erreur: settings.json invalide[/red]")
        raise typer.Exit(1) from None

    hooks_config = settings.get("hooks", {})

    # Find all installed hooks
    installed_hooks = {}
    for event, event_hooks in hooks_config.items():
        for group in event_hooks:
            for hook in group.get("hooks", []):
                cmd = hook.get("command", "")
                if "~/.claude/hooks/" in cmd:
                    name = cmd.split("/")[-1].replace(".sh", "").replace("bash ", "")
                    installed_hooks[name] = {"event": event, "command": cmd}

    if not installed_hooks:
        console.print("[dim]Aucun hook installé[/dim]")
        return

    # If no hook_name, show installed hooks
    if not hook_name:
        console.print("\n[bold]Hooks installés:[/bold]\n")
        table = Table()
        table.add_column("Nom")
        table.add_column("Event")

        for name, info in installed_hooks.items():
            table.add_row(name, info["event"])

        console.print(table)
        console.print("\n[dim]Usage: claude-manager hook remove <hook_name>[/dim]")
        return

    # Check if hook is installed
    if hook_name not in installed_hooks:
        console.print(f"[red]Erreur: Hook '{hook_name}' non installé[/red]")
        console.print("\nHooks installés:")
        for name in installed_hooks:
            console.print(f"  - {name}")
        raise typer.Exit(1)

    hook_command = f"bash ~/.claude/hooks/{hook_name}.sh"

    # Remove from settings.json
    for event, event_hooks in hooks_config.items():
        for group in event_hooks:
            group["hooks"] = [h for h in group.get("hooks", []) if h.get("command") != hook_command]
        # Remove empty groups
        hooks_config[event] = [g for g in event_hooks if g.get("hooks")]

    # Remove empty events
    settings["hooks"] = {e: h for e, h in hooks_config.items() if h}

    # Write settings
    settings_file.write_text(json.dumps(settings, indent=2))

    # Optionally remove script file
    script_file = paths.global_hooks / f"{hook_name}.sh"
    if script_file.exists():
        script_file.unlink()
        console.print(f"[green]✓[/green] Hook '{hook_name}' désinstallé")
        console.print(f"[dim]Script supprimé: {script_file}[/dim]")
    else:
        console.print(f"[green]✓[/green] Hook '{hook_name}' désinstallé de la configuration")

    console.print(f"[dim]Configuration mise à jour dans {settings_file}[/dim]")
