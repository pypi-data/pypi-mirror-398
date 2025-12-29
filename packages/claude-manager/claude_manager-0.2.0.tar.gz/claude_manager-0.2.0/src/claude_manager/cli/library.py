"""Library command - explore the embedded library."""

from typing import Any

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

library_app = typer.Typer(help="Explorer la bibliothèque", no_args_is_help=True)
console = Console()


@library_app.command("list")
def library_list(
    scope: str = typer.Option("all", "--scope", "-s", help="Scope: global, project, all"),
    category: str | None = typer.Option(None, "--category", "-c", help="Filtrer par catégorie"),
) -> None:
    """Lister les templates de la bibliothèque."""
    from claude_manager.library.loader import LibraryLoader

    loader = LibraryLoader()
    index = loader.get_agents_index()

    # Global agents
    if scope in ("global", "all"):
        console.print("\n[bold cyan]Agents globaux[/bold cyan]")
        table = Table()
        table.add_column("Nom")
        table.add_column("Modèle")
        table.add_column("Version")
        table.add_column("Description")

        for agent in index.get("global", []):
            table.add_row(
                agent["name"],
                agent.get("model", "sonnet"),
                agent.get("version", "-"),
                agent.get("description", "")[:50],
            )

        console.print(table)

    # Project agents
    if scope in ("project", "all"):
        console.print("\n[bold magenta]Agents projet[/bold magenta]")

        project = index.get("project", {})
        categories = project.get("categories", {})

        for cat_name, agents in categories.items():
            if category and cat_name != category:
                continue

            console.print(f"\n[bold]{cat_name}[/bold]")
            table = Table()
            table.add_column("Nom")
            table.add_column("Modèle")
            table.add_column("Version")
            table.add_column("Tags")

            for agent in agents:
                table.add_row(
                    agent["name"],
                    agent.get("model", "sonnet"),
                    agent.get("version", "-"),
                    ", ".join(agent.get("tags", [])),
                )

            console.print(table)


@library_app.command("search")
def library_search(
    query: str = typer.Argument(..., help="Terme de recherche (tags, nom, description)"),
) -> None:
    """Rechercher dans la bibliothèque."""
    from claude_manager.library.loader import LibraryLoader

    loader = LibraryLoader()
    index = loader.get_agents_index()
    query_lower = query.lower()

    results = []

    # Search global agents
    for agent in index.get("global", []):
        if _matches_search(agent, query_lower):
            results.append({"scope": "global", **agent})

    # Search project agents
    project = index.get("project", {})
    for category, agents in project.get("categories", {}).items():
        for agent in agents:
            if _matches_search(agent, query_lower):
                results.append({"scope": "project", "category": category, **agent})

    if not results:
        console.print(f"[dim]Aucun résultat pour '{query}'[/dim]")
        return

    console.print(f"\n[bold]Résultats pour '{query}':[/bold]\n")

    table = Table()
    table.add_column("Nom")
    table.add_column("Scope")
    table.add_column("Catégorie")
    table.add_column("Modèle")
    table.add_column("Description")

    for result in results:
        table.add_row(
            result["name"],
            result["scope"],
            result.get("category", "-"),
            result.get("model", "sonnet"),
            result.get("description", "")[:40],
        )

    console.print(table)


@library_app.command("info")
def library_info(
    name: str = typer.Argument(..., help="Nom du template"),
) -> None:
    """Afficher les détails d'un template."""
    from claude_manager.library.loader import LibraryLoader

    loader = LibraryLoader()
    index = loader.get_agents_index()

    # Find agent
    agent = None
    scope = None
    category = None

    # Check global
    for a in index.get("global", []):
        if a["name"] == name:
            agent = a
            scope = "global"
            break

    # Check project
    if not agent:
        project = index.get("project", {})
        for cat, agents in project.get("categories", {}).items():
            for a in agents:
                if a["name"] == name:
                    agent = a
                    scope = "project"
                    category = cat
                    break
            if agent:
                break

    if not agent:
        console.print(f"[red]Agent '{name}' non trouvé[/red]")
        raise typer.Exit(1)

    # Display info
    info_text = f"""
**Nom:** {agent["name"]}
**Scope:** {scope}
**Catégorie:** {category or "-"}
**Version:** {agent.get("version", "-")}
**Modèle:** {agent.get("model", "sonnet")}
**Tags:** {", ".join(agent.get("tags", []))}

**Description:**
{agent.get("description", "Aucune description")}

**Fichier:** {agent.get("file", "-")}
"""

    console.print(Panel(Markdown(info_text), title=f"Agent: {name}"))

    # Try to show content preview
    try:
        content = loader.get_agent_content(agent["file"])
        console.print("\n[bold]Aperçu du contenu:[/bold]")
        preview = content[:500] + "..." if len(content) > 500 else content
        console.print(Panel(preview, title="Contenu"))
    except Exception:
        pass


def _matches_search(agent: dict[str, Any], query: str) -> bool:
    """Check if agent matches search query."""
    # Check name
    if query in agent.get("name", "").lower():
        return True

    # Check description
    if query in agent.get("description", "").lower():
        return True

    # Check tags
    for tag in agent.get("tags", []):
        if query in tag.lower():
            return True

    return False
