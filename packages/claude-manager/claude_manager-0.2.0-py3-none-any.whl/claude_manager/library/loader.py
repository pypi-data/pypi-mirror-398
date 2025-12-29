"""Library loader - loads templates from the embedded package data."""

from importlib.resources import as_file, files
from pathlib import Path
from typing import Any, cast

import yaml


class LibraryLoader:
    """Loads templates from the embedded library data."""

    def __init__(self) -> None:
        """Initialize the library loader."""
        self._data_package = "claude_manager.data"

    def _get_data_path(self) -> Path:
        """Get the path to the data directory."""
        data_files = files(self._data_package)
        # For development, get the actual path
        with as_file(data_files) as data_path:
            return Path(data_path)

    def get_agents_index(self) -> dict[str, Any]:
        """Load the agents index file."""
        data_files = files(self._data_package)
        index_file = data_files.joinpath("agents").joinpath("_index.yaml")

        try:
            content = index_file.read_text()
            return yaml.safe_load(content) or {}
        except FileNotFoundError:
            return {
                "version": "1.0.0",
                "global": [],
                "project": {"categories": {}},
                "detection_rules": [],
            }

    def get_mcp_catalog(self) -> dict[str, Any]:
        """Load the MCP servers catalog."""
        data_files = files(self._data_package)
        catalog_file = data_files.joinpath("mcp_servers").joinpath("_catalog.yaml")

        try:
            content = catalog_file.read_text()
            return yaml.safe_load(content) or {}
        except FileNotFoundError:
            return {"version": "1.0.0", "global": [], "project": [], "detection_rules": []}

    def get_commands_index(self) -> dict[str, Any]:
        """Load the commands index file."""
        data_files = files(self._data_package)
        index_file = data_files.joinpath("commands").joinpath("_index.yaml")

        try:
            content = index_file.read_text()
            return yaml.safe_load(content) or {}
        except FileNotFoundError:
            return {"version": "1.0.0", "global": [], "project": []}

    def get_hooks_index(self) -> dict[str, Any]:
        """Load the hooks index file."""
        data_files = files(self._data_package)
        index_file = data_files.joinpath("hooks").joinpath("_index.yaml")

        try:
            content = index_file.read_text()
            return yaml.safe_load(content) or {}
        except FileNotFoundError:
            return {"version": "1.0.0", "global": []}

    def get_agent_content(self, relative_path: str) -> str:
        """Get the content of an agent template file.

        Args:
            relative_path: Path relative to data/agents/ (e.g., 'global/commit.md')

        Returns:
            The content of the agent file.
        """
        data_files = files(self._data_package)
        agent_file = data_files.joinpath("agents").joinpath(relative_path)

        return agent_file.read_text()

    def get_command_content(self, relative_path: str) -> str:
        """Get the content of a command template file."""
        data_files = files(self._data_package)
        command_file = data_files.joinpath("commands").joinpath(relative_path)

        return command_file.read_text()

    def get_hook_content(self, relative_path: str) -> str:
        """Get the content of a hook template file."""
        data_files = files(self._data_package)
        hook_file = data_files.joinpath("hooks").joinpath(relative_path)

        return hook_file.read_text()

    def list_global_agents(self) -> list[dict[str, Any]]:
        """List all global agents from the index."""
        index = self.get_agents_index()
        return cast(list[dict[str, Any]], index.get("global", []))

    def list_project_agents(self, category: str | None = None) -> list[dict[str, Any]]:
        """List project agents, optionally filtered by category."""
        index = self.get_agents_index()
        project = cast(dict[str, Any], index.get("project", {}))
        categories = cast(dict[str, list[dict[str, Any]]], project.get("categories", {}))

        if category:
            return categories.get(category, [])

        # Return all agents from all categories
        all_agents: list[dict[str, Any]] = []
        for cat_name, agents in categories.items():
            for agent in agents:
                all_agents.append({**agent, "category": cat_name})
        return all_agents

    def get_agent_by_name(self, name: str) -> dict[str, Any] | None:
        """Find an agent by name in the library."""
        # Check global agents
        for agent in self.list_global_agents():
            if agent.get("name") == name:
                return {**agent, "scope": "global"}

        # Check project agents
        for agent in self.list_project_agents():
            if agent.get("name") == name:
                return {**agent, "scope": "project"}

        return None

    def get_detection_rules(self) -> list[dict[str, Any]]:
        """Get agent detection rules."""
        index = self.get_agents_index()
        return cast(list[dict[str, Any]], index.get("detection_rules", []))

    def get_mcp_detection_rules(self) -> list[dict[str, Any]]:
        """Get MCP detection rules."""
        catalog = self.get_mcp_catalog()
        return cast(list[dict[str, Any]], catalog.get("detection_rules", []))

    def list_global_commands(self) -> list[dict[str, Any]]:
        """List all global commands from the index."""
        index = self.get_commands_index()
        return cast(list[dict[str, Any]], index.get("global", []))

    def list_global_hooks(self) -> list[dict[str, Any]]:
        """List all global hooks from the index."""
        index = self.get_hooks_index()
        return cast(list[dict[str, Any]], index.get("global", []))

    def get_hooks_settings_template(self) -> dict[str, Any]:
        """Get the hooks settings.json template."""
        index = self.get_hooks_index()
        return cast(dict[str, Any], index.get("settings_template", {}))
