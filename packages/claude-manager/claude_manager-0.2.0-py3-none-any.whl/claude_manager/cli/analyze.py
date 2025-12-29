"""Analyze command - analyze project and recommend agents/MCP."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from claude_manager.models.analysis import AnalysisResult

if TYPE_CHECKING:
    from claude_manager.library.loader import LibraryLoader

console = Console()


def analyze(
    path: Path | None = typer.Argument(None, help="Chemin du projet (défaut: .)"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Afficher recommandations sans installer"
    ),
    auto_install: bool = typer.Option(False, "--auto-install", help="Installer sans confirmation"),
    agents_only: bool = typer.Option(False, "--agents", help="Recommander agents uniquement"),
    mcp_only: bool = typer.Option(False, "--mcp", help="Recommander MCP uniquement"),
    quick: bool = typer.Option(False, "--quick", "-q", help="Utiliser l'analyse statique rapide"),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Mode interactif (l'IA peut poser des questions)"
    ),
    model: str = typer.Option("sonnet", "--model", "-m", help="Modèle Claude (haiku/sonnet/opus)"),
) -> None:
    """Analyser un projet et recommander les agents/MCP adaptés."""
    project_path = (path or Path.cwd()).resolve()

    if not project_path.exists():
        console.print(f"[red]Erreur: Le chemin {project_path} n'existe pas[/red]")
        raise typer.Exit(1)

    if not project_path.is_dir():
        console.print(f"[red]Erreur: {project_path} n'est pas un répertoire[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Analyse du projet: {project_path}[/bold]\n")

    if quick:
        # Use static analysis
        _run_quick_analysis(project_path, agents_only, mcp_only, dry_run, auto_install)
    else:
        # Use AI-powered analysis
        _run_ai_analysis(
            project_path, agents_only, mcp_only, dry_run, auto_install, interactive, model
        )


def _run_quick_analysis(
    project_path: Path,
    agents_only: bool,
    mcp_only: bool,
    dry_run: bool,
    auto_install: bool,
) -> None:
    """Run the quick static analysis."""
    console.print("[dim]Mode rapide: analyse statique...[/dim]")
    detected = _quick_detect(project_path)

    console.print("\n[bold]Technologies détectées:[/bold]")
    if detected["languages"]:
        console.print(f"  Langages: {', '.join(detected['languages'])}")
    if detected["frameworks"]:
        console.print(f"  Frameworks: {', '.join(detected['frameworks'])}")
    if detected["tools"]:
        console.print(f"  Outils: {', '.join(detected['tools'])}")
    if detected["files"]:
        console.print(f"  Fichiers clés: {', '.join(detected['files'])}")

    # Get recommendations
    from claude_manager.library.loader import LibraryLoader

    loader = LibraryLoader()

    recommended_agents = []
    recommended_mcp = []

    if not mcp_only:
        console.print("\n[bold]Agents recommandés:[/bold]")
        recommended_agents = _get_recommended_agents(loader, detected)
        if recommended_agents:
            for agent in recommended_agents:
                console.print(
                    f"  [green]•[/green] {agent['name']} - {agent.get('description', '')}"
                )
        else:
            console.print("  [dim]Aucun agent spécifique recommandé[/dim]")

    if not agents_only:
        console.print("\n[bold]Serveurs MCP recommandés:[/bold]")
        recommended_mcp = _get_recommended_mcp(loader, detected)
        if recommended_mcp:
            for server in recommended_mcp:
                console.print(
                    f"  [green]•[/green] {server['name']} - {server.get('description', '')}"
                )
        else:
            console.print("  [dim]Aucun serveur MCP spécifique recommandé[/dim]")

    _handle_installation(
        dry_run,
        auto_install,
        recommended_agents if not mcp_only else None,
        recommended_mcp if not agents_only else None,
        project_path,
    )


def _run_ai_analysis(
    project_path: Path,
    agents_only: bool,
    mcp_only: bool,
    dry_run: bool,
    auto_install: bool,
    interactive: bool,
    model: str,
) -> None:
    """Run the AI-powered analysis using Claude Code."""
    from claude_manager.agent.analyzer import (
        AnalysisError,
        ClaudeAnalyzer,
        ClaudeNotFoundError,
    )

    console.print(f"[dim]Analyse IA avec Claude ({model})...[/dim]")

    try:
        if interactive:
            # Interactive mode with Q&A
            result = _run_interactive_analysis(project_path, model)
        else:
            # Standard AI analysis
            with console.status("[bold]Analyse du projet en cours...[/bold]"):
                analyzer = ClaudeAnalyzer(
                    project_path=project_path,
                    interactive=False,
                    model=model,
                )
                result = analyzer.analyze()

        # Display results
        _display_ai_analysis(result, agents_only, mcp_only)

        # Install recommendations
        _handle_installation(
            dry_run,
            auto_install,
            result.recommended_agents if not mcp_only else None,
            result.recommended_mcp if not agents_only else None,
            project_path,
        )

    except ClaudeNotFoundError as e:
        console.print(f"\n[red]Erreur: {e}[/red]")
        console.print("[dim]Basculement vers l'analyse rapide...[/dim]\n")
        _run_quick_analysis(project_path, agents_only, mcp_only, dry_run, auto_install)

    except AnalysisError as e:
        console.print(f"\n[red]Erreur d'analyse: {e}[/red]")
        console.print("[dim]Basculement vers l'analyse rapide...[/dim]\n")
        _run_quick_analysis(project_path, agents_only, mcp_only, dry_run, auto_install)


def _run_interactive_analysis(project_path: Path, model: str) -> AnalysisResult:
    """Run interactive analysis with Q&A."""
    from claude_manager.agent.interactive import InteractiveAnalyzer

    analyzer = InteractiveAnalyzer(project_path=project_path, model=model)
    return analyzer.run()


def _display_ai_analysis(result: AnalysisResult, agents_only: bool, mcp_only: bool) -> None:
    """Display the AI analysis results with rich formatting."""
    # Summary
    console.print(Panel(result.summary, title="[bold]Résumé[/bold]", border_style="blue"))

    # Technologies detected
    if result.technologies:
        console.print("\n[bold]Technologies détectées:[/bold]")
        tech_table = Table(show_header=True, header_style="bold")
        tech_table.add_column("Technologie")
        tech_table.add_column("Catégorie")
        tech_table.add_column("Confiance")

        confidence_colors = {"high": "green", "medium": "yellow", "low": "dim"}

        for tech in result.technologies:
            color = confidence_colors.get(tech.confidence, "white")
            tech_table.add_row(
                tech.name,
                tech.category,
                f"[{color}]{tech.confidence}[/]",
            )
        console.print(tech_table)

    # Complexity assessment
    console.print(f"\n[bold]Complexité:[/bold] {result.complexity.level}")
    for factor in result.complexity.factors:
        console.print(f"  • {factor}")

    # Agent recommendations
    if not mcp_only and result.recommended_agents:
        console.print("\n[bold]Agents recommandés:[/bold]")
        priority_icons = {
            "essential": "[red]★[/red]",
            "recommended": "[yellow]●[/yellow]",
            "optional": "[dim]○[/dim]",
        }
        for agent in result.recommended_agents:
            icon = priority_icons.get(agent.priority, "•")
            console.print(f"  {icon} [green]{agent.name}[/green]: {agent.reason}")

    # MCP recommendations
    if not agents_only and result.recommended_mcp:
        console.print("\n[bold]Serveurs MCP recommandés:[/bold]")
        priority_icons = {
            "essential": "[red]★[/red]",
            "recommended": "[yellow]●[/yellow]",
            "optional": "[dim]○[/dim]",
        }
        for mcp in result.recommended_mcp:
            icon = priority_icons.get(mcp.priority, "•")
            console.print(f"  {icon} [blue]{mcp.id}[/blue]: {mcp.reason}")

    # Special considerations
    if result.special_considerations:
        console.print("\n[bold]Considérations spéciales:[/bold]")
        for note in result.special_considerations:
            console.print(f"  [dim]• {note}[/dim]")

    # Questions (if any)
    if result.questions:
        console.print("\n[bold yellow]Questions de clarification:[/bold yellow]")
        for q in result.questions:
            console.print(f"  [yellow]?[/yellow] {q}")


def _handle_installation(
    dry_run: bool,
    auto_install: bool,
    recommended_agents: list[Any] | None = None,
    recommended_mcp: list[Any] | None = None,
    project_path: Path | None = None,
) -> None:
    """Handle the installation of recommended agents and MCP servers."""
    if dry_run:
        console.print("\n[dim]--dry-run: aucune modification effectuée[/dim]")
        return

    if not recommended_agents and not recommended_mcp:
        console.print("\n[dim]Aucune recommandation à installer[/dim]")
        return

    if not auto_install:
        if not typer.confirm("\nInstaller les agents et MCP recommandés ?"):
            console.print("[dim]Installation annulée[/dim]")
            return

    console.print("\n[bold]Installation...[/bold]\n")

    # Install agents
    if recommended_agents:
        _install_recommended_agents(recommended_agents, project_path)

    # Install MCP servers
    if recommended_mcp:
        _install_recommended_mcp(recommended_mcp, project_path)

    console.print("\n[green]Installation terminée ![/green]")


def _install_recommended_agents(
    recommended_agents: list[Any], project_path: Path | None = None
) -> None:
    """Install recommended agents."""
    from claude_manager.core.differ import DiffResult, DiffStatus
    from claude_manager.core.installer import Installer
    from claude_manager.core.paths import ClaudePaths
    from claude_manager.library.loader import LibraryLoader

    loader = LibraryLoader()
    paths = ClaudePaths()
    if project_path:
        paths = paths.with_project(project_path)

    installer = Installer(paths, loader)

    # Get agent index to lookup file paths
    agents_index = loader.get_agents_index()

    # Build lookup: name -> agent info
    agent_lookup: dict[str, Any] = {}
    for agent in agents_index.get("global", []):
        agent_lookup[agent["name"]] = {**agent, "scope": "global"}

    project = agents_index.get("project", {})
    for category, agents in project.get("categories", {}).items():
        for agent in agents:
            agent_lookup[agent["name"]] = {**agent, "scope": "project", "category": category}

    console.print("[dim]Agents:[/dim]")
    installed_count = 0

    for rec in recommended_agents:
        # Handle both dict (from quick mode) and AgentRecommendation (from AI mode)
        name = rec.name if hasattr(rec, "name") else rec.get("name")

        if name not in agent_lookup:
            console.print(f"  [yellow]?[/yellow] {name} (non trouvé dans la bibliothèque)")
            continue

        agent_info = agent_lookup[name]
        scope = agent_info.get("scope", "project")

        # Create a DiffResult for the installer
        diff = DiffResult(
            name=name,
            status=DiffStatus.NEW,
            scope=scope,
            library_file=agent_info.get("file"),
            library_version=agent_info.get("version", "1.0.0"),
            category=agent_info.get("category"),
        )

        success = installer.install_agent(diff, scope=scope)
        if success:
            console.print(f"  [green]✓[/green] {name} ({scope})")
            installed_count += 1
        else:
            console.print(f"  [red]✗[/red] {name} (échec)")

    console.print(f"  [dim]{installed_count} agent(s) installé(s)[/dim]")


def _install_recommended_mcp(recommended_mcp: list[Any], project_path: Path | None = None) -> None:
    """Install recommended MCP servers."""
    import json

    from claude_manager.core.paths import ClaudePaths
    from claude_manager.library.loader import LibraryLoader

    loader = LibraryLoader()
    catalog = loader.get_mcp_catalog()

    # Build lookup: id -> server info
    mcp_lookup: dict[str, Any] = {}
    for server in catalog.get("global", []):
        mcp_lookup[server["id"]] = {**server, "catalog_scope": "global"}
    for server in catalog.get("project", []):
        mcp_lookup[server["id"]] = {**server, "catalog_scope": "project"}

    paths = ClaudePaths()
    if project_path:
        paths = paths.with_project(project_path)

    console.print("\n[dim]Serveurs MCP:[/dim]")
    installed_count = 0

    for rec in recommended_mcp:
        # Handle both dict (from quick mode) and MCPRecommendation (from AI mode)
        server_id = rec.id if hasattr(rec, "id") else rec.get("id")

        if server_id not in mcp_lookup:
            console.print(f"  [yellow]?[/yellow] {server_id} (non trouvé dans le catalogue)")
            continue

        server = mcp_lookup[server_id]
        config_template = server.get("config_template", {})

        # Build env vars - skip prompts for automatic installation
        env_vars = {}
        needs_config = False
        for key, value in config_template.get("env", {}).items():
            if isinstance(value, str) and value.startswith("${prompt:"):
                # Mark that this server needs manual configuration
                needs_config = True
                env_vars[key] = f"<À CONFIGURER: {value[9:-1]}>"
            elif isinstance(value, str) and value.startswith("${env:"):
                env_vars[key] = value
            else:
                env_vars[key] = value

        # Build MCP config entry
        mcp_entry: dict[str, Any] = {
            "command": config_template.get("command", ""),
            "args": config_template.get("args", []),
        }
        if env_vars:
            mcp_entry["env"] = env_vars

        # Determine settings file based on catalog scope
        scope = server.get("catalog_scope", "global")
        if scope == "global":
            settings_file = paths.global_settings
        else:
            if paths.project_settings_local is None:
                console.print(f"  [yellow]![/yellow] {server_id} (projet non configuré)")
                continue
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

        if needs_config:
            console.print(f"  [yellow]✓[/yellow] {server_id} (installé - configuration requise)")
        else:
            console.print(f"  [green]✓[/green] {server_id}")
        installed_count += 1

    console.print(f"  [dim]{installed_count} serveur(s) MCP installé(s)[/dim]")


def _quick_detect(project_path: Path) -> dict[str, list[str]]:
    """Quick detection of project technologies using static analysis."""
    detected: dict[str, list[str]] = {
        "languages": [],
        "frameworks": [],
        "tools": [],
        "files": [],
    }

    # File markers - maps filename to what it indicates
    markers = {
        "package.json": {"lang": "javascript/typescript", "file": "package.json"},
        "pom.xml": {"lang": "java", "framework": "spring", "file": "pom.xml"},
        "build.gradle": {"lang": "java/kotlin", "framework": "spring", "file": "build.gradle"},
        "build.gradle.kts": {
            "lang": "kotlin",
            "framework": "spring",
            "file": "build.gradle.kts",
        },
        "go.mod": {"lang": "go", "file": "go.mod"},
        "Cargo.toml": {"lang": "rust", "file": "Cargo.toml"},
        "pyproject.toml": {"lang": "python", "file": "pyproject.toml"},
        "requirements.txt": {"lang": "python", "file": "requirements.txt"},
        "setup.py": {"lang": "python", "file": "setup.py"},
        "Dockerfile": {"tool": "docker", "file": "Dockerfile"},
        "docker-compose.yml": {"tool": "docker-compose", "file": "docker-compose.yml"},
        "docker-compose.yaml": {"tool": "docker-compose", "file": "docker-compose.yaml"},
        ".gitlab-ci.yml": {"tool": "gitlab-ci", "file": ".gitlab-ci.yml"},
        ".github": {"tool": "github-actions", "file": ".github"},
        "Makefile": {"tool": "make", "file": "Makefile"},
        "vite.config.ts": {"framework": "vite", "file": "vite.config.ts"},
        "vite.config.js": {"framework": "vite", "file": "vite.config.js"},
        "next.config.js": {"framework": "nextjs", "file": "next.config.js"},
        "next.config.mjs": {"framework": "nextjs", "file": "next.config.mjs"},
        "nuxt.config.ts": {"framework": "nuxt", "file": "nuxt.config.ts"},
        "angular.json": {"framework": "angular", "file": "angular.json"},
        "svelte.config.js": {"framework": "svelte", "file": "svelte.config.js"},
    }

    # Backend markers that should be searched in subdirectories
    backend_markers = {"Cargo.toml", "go.mod", "pom.xml", "build.gradle", "build.gradle.kts"}

    def _apply_marker(name: str, subdir: str | None = None) -> None:
        """Apply marker detection, optionally from a subdirectory."""
        if name in markers:
            info = markers[name]
            file_display = f"{subdir}/{info['file']}" if subdir else info["file"]
            if "lang" in info and info["lang"] not in detected["languages"]:
                detected["languages"].append(info["lang"])
            if "framework" in info and info["framework"] not in detected["frameworks"]:
                detected["frameworks"].append(info["framework"])
            if "tool" in info and info["tool"] not in detected["tools"]:
                detected["tools"].append(info["tool"])
            if file_display not in detected["files"]:
                detected["files"].append(file_display)

    # Scan root level
    for item in project_path.iterdir():
        name = item.name
        _apply_marker(name)

        # Scan subdirectories for backend markers
        if (
            item.is_dir()
            and not name.startswith(".")
            and name not in ("node_modules", "vendor", "target", "dist", "build")
        ):
            for subitem in item.iterdir():
                if subitem.name in backend_markers:
                    _apply_marker(subitem.name, name)

    # Check for specific framework in package.json
    package_json = project_path / "package.json"
    if package_json.exists():
        import json

        try:
            data = json.loads(package_json.read_text())
            deps = list(data.get("dependencies", {}).keys()) + list(
                data.get("devDependencies", {}).keys()
            )
            if "vue" in deps and "vue" not in detected["frameworks"]:
                detected["frameworks"].append("vue")
            if "react" in deps and "react" not in detected["frameworks"]:
                detected["frameworks"].append("react")
            if "svelte" in deps and "svelte" not in detected["frameworks"]:
                detected["frameworks"].append("svelte")
            if "@sveltejs/kit" in deps and "sveltekit" not in detected["frameworks"]:
                detected["frameworks"].append("sveltekit")
        except (json.JSONDecodeError, OSError):
            pass

    # Check for terraform files
    if any(f.suffix == ".tf" for f in project_path.glob("*.tf")):
        if "terraform" not in detected["tools"]:
            detected["tools"].append("terraform")
        if "*.tf" not in detected["files"]:
            detected["files"].append("*.tf")

    # Check for SQL files
    if any(f.suffix == ".sql" for f in project_path.glob("**/*.sql")):
        if "sql" not in detected["tools"]:
            detected["tools"].append("sql")
        if "*.sql" not in detected["files"]:
            detected["files"].append("*.sql")

    # Check git remote for gitlab/github
    git_config = project_path / ".git" / "config"
    if git_config.exists():
        try:
            content = git_config.read_text().lower()
            if "gitlab" in content and "gitlab" not in detected["tools"]:
                detected["tools"].append("gitlab")
            if "github" in content and "github" not in detected["tools"]:
                detected["tools"].append("github")
        except OSError:
            pass

    return detected


def _get_recommended_agents(
    loader: "LibraryLoader", detected: dict[str, list[str]]
) -> list[dict[str, Any]]:
    """Get recommended agents based on detected technologies."""
    recommended = []

    # Build a set of all detected items for matching
    all_detected = set()
    for lang in detected["languages"]:
        all_detected.add(lang.lower())
        for part in lang.split("/"):
            all_detected.add(part.lower())
    for fw in detected["frameworks"]:
        all_detected.add(fw.lower())
    for tool in detected["tools"]:
        all_detected.add(tool.lower())
    for f in detected["files"]:
        all_detected.add(f.lower())

    # Get agents index
    index = loader.get_agents_index()

    # Match agents by tags
    project = index.get("project", {})
    categories = project.get("categories", {})

    for category, agents in categories.items():
        for agent in agents:
            tags = [t.lower() for t in agent.get("tags", [])]
            matches = set(tags) & all_detected
            if matches:
                agent_with_meta = {**agent, "category": category, "matched": list(matches)}
                if agent_with_meta not in recommended:
                    recommended.append(agent_with_meta)

    return recommended


def _get_recommended_mcp(
    loader: "LibraryLoader", detected: dict[str, list[str]]
) -> list[dict[str, Any]]:
    """Get recommended MCP servers based on detected technologies."""
    recommended = []

    # Build detection set
    all_detected = set()
    for lang in detected["languages"]:
        all_detected.add(lang.lower())
        for part in lang.split("/"):
            all_detected.add(part.lower())
    for fw in detected["frameworks"]:
        all_detected.add(fw.lower())
    for tool in detected["tools"]:
        all_detected.add(tool.lower())
    for f in detected["files"]:
        all_detected.add(f.lower())

    # Get MCP catalog
    catalog = loader.get_mcp_catalog()

    # Match MCP servers by tags
    for server in catalog.get("project", []):
        tags = [t.lower() for t in server.get("tags", [])]
        matches = set(tags) & all_detected
        if matches:
            server_with_meta = {**server, "matched": list(matches)}
            if server_with_meta not in recommended:
                recommended.append(server_with_meta)

    return recommended
