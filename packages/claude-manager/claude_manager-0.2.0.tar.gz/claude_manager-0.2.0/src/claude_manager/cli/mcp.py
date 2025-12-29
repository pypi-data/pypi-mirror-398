"""MCP command - manage Model Context Protocol servers."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

mcp_app = typer.Typer(help="Gérer les serveurs MCP", no_args_is_help=True)
console = Console()


@mcp_app.command("list")
def mcp_list(
    scope: str = typer.Option("all", "--scope", "-s", help="Scope: global, project, all"),
    installed: bool = typer.Option(False, "--installed", "-i", help="Uniquement installés"),
    available: bool = typer.Option(False, "--available", "-a", help="Uniquement disponibles"),
) -> None:
    """Lister les serveurs MCP."""
    from claude_manager.library.loader import LibraryLoader

    loader = LibraryLoader()
    catalog = loader.get_mcp_catalog()

    table = Table(title="Serveurs MCP")
    table.add_column("ID")
    table.add_column("Nom")
    table.add_column("Scope")
    table.add_column("Source")
    table.add_column("Tags")

    # Global servers
    if scope in ("global", "all"):
        for server in catalog.get("global", []):
            table.add_row(
                server["id"],
                server["name"],
                "[cyan]global[/cyan]",
                server["source"]["type"],
                ", ".join(server.get("tags", [])),
            )

    # Project servers
    if scope in ("project", "all"):
        for server in catalog.get("project", []):
            table.add_row(
                server["id"],
                server["name"],
                "[magenta]project[/magenta]",
                server["source"]["type"],
                ", ".join(server.get("tags", [])),
            )

    console.print(table)


@mcp_app.command("install")
def mcp_install(
    server_id: str | None = typer.Argument(None, help="ID du serveur à installer"),
    scope: str = typer.Option("global", "--scope", "-s", help="Scope: global, project"),
) -> None:
    """Installer un serveur MCP."""
    import json

    from claude_manager.core.paths import ClaudePaths
    from claude_manager.library.loader import LibraryLoader

    loader = LibraryLoader()
    catalog = loader.get_mcp_catalog()

    # Build list of all servers
    all_servers = {}
    for server in catalog.get("global", []):
        all_servers[server["id"]] = {**server, "catalog_scope": "global"}
    for server in catalog.get("project", []):
        all_servers[server["id"]] = {**server, "catalog_scope": "project"}

    # If no server_id, show available servers
    if not server_id:
        console.print("\n[bold]Serveurs MCP disponibles:[/bold]\n")
        table = Table()
        table.add_column("ID")
        table.add_column("Nom")
        table.add_column("Description")

        for sid, server in all_servers.items():
            table.add_row(sid, server["name"], server.get("description", ""))

        console.print(table)
        console.print("\n[dim]Usage: claude-manager mcp install <server_id>[/dim]")
        return

    # Check if server exists
    if server_id not in all_servers:
        console.print(f"[red]Erreur: Serveur '{server_id}' non trouvé[/red]")
        console.print("\nServeurs disponibles:")
        for sid in all_servers:
            console.print(f"  - {sid}")
        raise typer.Exit(1)

    server = all_servers[server_id]
    console.print(f"\n[bold]Installation de {server['name']}[/bold]\n")

    # Get config template
    config_template = server.get("config_template", {})

    # Handle environment variables that need prompts
    env_vars = {}
    for key, value in config_template.get("env", {}).items():
        if isinstance(value, str) and value.startswith("${prompt:"):
            prompt_text = value[9:-1]  # Extract text between ${prompt: and }
            user_value = typer.prompt(f"  {prompt_text}")
            env_vars[key] = user_value
        elif isinstance(value, str) and value.startswith("${env:"):
            # Reference to environment variable
            env_vars[key] = value
        else:
            env_vars[key] = value

    # Build MCP config entry
    mcp_entry = {
        "command": config_template.get("command", ""),
        "args": config_template.get("args", []),
    }
    if env_vars:
        mcp_entry["env"] = env_vars

    # Write to settings file
    paths = ClaudePaths()

    if scope == "global":
        settings_file = paths.global_settings
    else:
        if paths.project_settings_local is None:
            console.print("[red]Erreur: Pas de projet configuré pour le scope 'project'[/red]")
            raise typer.Exit(1)
        settings_file = paths.project_settings_local

    # Load existing settings
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
        except json.JSONDecodeError:
            settings = {}
    else:
        settings = {}

    # Add MCP server
    if "mcpServers" not in settings:
        settings["mcpServers"] = {}

    settings["mcpServers"][server_id] = mcp_entry

    # Write back
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.write_text(json.dumps(settings, indent=2))

    console.print(f"[green]✓[/green] {server['name']} installé")
    console.print(f"[dim]Configuration ajoutée à {settings_file}[/dim]")


@mcp_app.command("update")
def mcp_update(
    server_id: str | None = typer.Argument(None, help="ID du serveur (tous si non spécifié)"),
    scope: str = typer.Option("global", "--scope", "-s", help="Scope: global, project"),
) -> None:
    """Mettre à jour les serveurs MCP depuis le catalogue."""
    import json

    from claude_manager.core.paths import ClaudePaths
    from claude_manager.library.loader import LibraryLoader

    paths = ClaudePaths()
    loader = LibraryLoader()
    catalog = loader.get_mcp_catalog()

    # Build catalog lookup
    catalog_servers = {}
    for server in catalog.get("global", []):
        catalog_servers[server["id"]] = server
    for server in catalog.get("project", []):
        catalog_servers[server["id"]] = server

    # Determine settings file
    if scope == "global":
        settings_file = paths.global_settings
    else:
        if paths.project_settings_local is None:
            console.print("[red]Erreur: Pas de projet configuré pour le scope 'project'[/red]")
            raise typer.Exit(1)
        settings_file = paths.project_settings_local

    # Load existing settings
    if not settings_file.exists():
        console.print("[dim]Aucun serveur MCP installé[/dim]")
        return

    try:
        settings = json.loads(settings_file.read_text())
    except json.JSONDecodeError:
        settings = {}

    installed = settings.get("mcpServers", {})
    if not installed:
        console.print("[dim]Aucun serveur MCP installé[/dim]")
        return

    # Determine which servers to update
    if server_id:
        if server_id not in installed:
            console.print(f"[red]Erreur: Serveur '{server_id}' non installé[/red]")
            raise typer.Exit(1)
        servers_to_update = [server_id]
    else:
        servers_to_update = list(installed.keys())

    console.print("\n[bold]Mise à jour des serveurs MCP[/bold]\n")

    updated_count = 0
    skipped_count = 0

    for sid in servers_to_update:
        if sid not in catalog_servers:
            console.print(f"  [dim]⊘ {sid}[/dim] (hors catalogue, ignoré)")
            skipped_count += 1
            continue

        server = catalog_servers[sid]
        config_template = server.get("config_template", {})

        # Preserve existing env vars if they exist
        existing_env = installed[sid].get("env", {})
        new_env = {}

        for key, value in config_template.get("env", {}).items():
            if key in existing_env:
                # Keep existing value
                new_env[key] = existing_env[key]
            elif isinstance(value, str) and value.startswith("${prompt:"):
                # Prompt for new value
                prompt_text = value[9:-1]
                user_value = typer.prompt(f"  {sid} - {prompt_text}")
                new_env[key] = user_value
            else:
                new_env[key] = value

        # Build updated config
        mcp_entry = {
            "command": config_template.get("command", ""),
            "args": config_template.get("args", []),
        }
        if new_env:
            mcp_entry["env"] = new_env

        settings["mcpServers"][sid] = mcp_entry
        console.print(f"  [green]✓ {sid}[/green] mis à jour")
        updated_count += 1

    # Write back
    settings_file.write_text(json.dumps(settings, indent=2))

    console.print(f"\n[green]{updated_count} serveur(s) mis à jour[/green]")
    if skipped_count:
        console.print(f"[dim]{skipped_count} serveur(s) ignoré(s) (hors catalogue)[/dim]")


@mcp_app.command("check")
def mcp_check(
    scope: str = typer.Option("all", "--scope", "-s", help="Scope: global, project, all"),
) -> None:
    """Vérifier les mises à jour disponibles."""
    import json

    from claude_manager.core.paths import ClaudePaths
    from claude_manager.library.loader import LibraryLoader

    paths = ClaudePaths()
    loader = LibraryLoader()
    catalog = loader.get_mcp_catalog()

    # Build catalog lookup
    catalog_servers = {}
    for server in catalog.get("global", []):
        catalog_servers[server["id"]] = server
    for server in catalog.get("project", []):
        catalog_servers[server["id"]] = server

    console.print("\n[bold]Vérification des serveurs MCP installés...[/bold]\n")

    def check_settings_file(settings_file: Path, scope_name: str) -> None:
        if not settings_file.exists():
            console.print(f"[dim]{scope_name}: Aucun fichier de configuration[/dim]")
            return

        try:
            settings = json.loads(settings_file.read_text())
        except json.JSONDecodeError:
            console.print(f"[yellow]{scope_name}: Erreur lecture configuration[/yellow]")
            return

        installed = settings.get("mcpServers", {})
        if not installed:
            console.print(f"[dim]{scope_name}: Aucun serveur installé[/dim]")
            return

        console.print(f"[bold]{scope_name}:[/bold]")
        table = Table()
        table.add_column("ID")
        table.add_column("Statut")
        table.add_column("Source")

        for server_id in installed:
            if server_id in catalog_servers:
                cat_server = catalog_servers[server_id]
                source = cat_server.get("source", {})
                source_type = source.get("type", "unknown")

                # Check if config matches catalog template
                installed_config = installed[server_id]
                template_config = cat_server.get("config_template", {})

                if installed_config.get("command") == template_config.get("command"):
                    table.add_row(
                        server_id,
                        "[green]✓ à jour[/green]",
                        f"{source_type}: {source.get('package', source.get('repo', '-'))}",
                    )
                else:
                    table.add_row(
                        server_id,
                        "[yellow]↑ config différente[/yellow]",
                        f"{source_type}: {source.get('package', source.get('repo', '-'))}",
                    )
            else:
                table.add_row(
                    server_id,
                    "[dim]◆ custom (hors catalogue)[/dim]",
                    "-",
                )

        console.print(table)
        console.print()

    if scope in ("global", "all"):
        check_settings_file(paths.global_settings, "Global (~/.claude)")

    if scope in ("project", "all"):
        if paths.project_settings_local:
            check_settings_file(paths.project_settings_local, "Projet (./.claude)")


@mcp_app.command("remove")
def mcp_remove(
    server_id: str | None = typer.Argument(None, help="ID du serveur à désinstaller"),
    scope: str = typer.Option("global", "--scope", "-s", help="Scope: global, project"),
) -> None:
    """Désinstaller un serveur MCP."""
    import json

    from claude_manager.core.paths import ClaudePaths

    paths = ClaudePaths()

    # Determine settings file
    if scope == "global":
        settings_file = paths.global_settings
    else:
        if paths.project_settings_local is None:
            console.print("[red]Erreur: Pas de projet configuré pour le scope 'project'[/red]")
            raise typer.Exit(1)
        settings_file = paths.project_settings_local

    # Load existing settings
    if not settings_file.exists():
        console.print("[dim]Aucun serveur MCP installé[/dim]")
        return

    try:
        settings = json.loads(settings_file.read_text())
    except json.JSONDecodeError:
        settings = {}

    installed = settings.get("mcpServers", {})

    if not installed:
        console.print("[dim]Aucun serveur MCP installé[/dim]")
        return

    # If no server_id, show installed servers
    if not server_id:
        console.print("\n[bold]Serveurs MCP installés:[/bold]\n")
        table = Table()
        table.add_column("ID")
        table.add_column("Command")

        for sid, config in installed.items():
            cmd = config.get("command", "")
            args = " ".join(config.get("args", [])[:2])
            table.add_row(sid, f"{cmd} {args}...")

        console.print(table)
        console.print("\n[dim]Usage: claude-manager mcp remove <server_id>[/dim]")
        return

    # Check if server is installed
    if server_id not in installed:
        console.print(f"[red]Erreur: Serveur '{server_id}' non installé[/red]")
        console.print("\nServeurs installés:")
        for sid in installed:
            console.print(f"  - {sid}")
        raise typer.Exit(1)

    # Remove server
    del settings["mcpServers"][server_id]

    # Clean up empty mcpServers
    if not settings["mcpServers"]:
        del settings["mcpServers"]

    # Write back
    settings_file.write_text(json.dumps(settings, indent=2))

    console.print(f"[green]✓[/green] Serveur '{server_id}' désinstallé")
    console.print(f"[dim]Configuration mise à jour dans {settings_file}[/dim]")
