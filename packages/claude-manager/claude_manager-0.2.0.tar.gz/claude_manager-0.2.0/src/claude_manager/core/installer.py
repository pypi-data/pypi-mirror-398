"""Installer - copies templates from library to local installation."""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from claude_manager.core.differ import DiffResult, DiffStatus
from claude_manager.core.paths import ClaudePaths
from claude_manager.library.loader import LibraryLoader
from claude_manager.models.sync_state import (
    AgentInstallation,
    GlobalSyncState,
    ProjectSyncState,
)


class Installer:
    """Installs templates from library to local Claude Code directories."""

    def __init__(self, paths: ClaudePaths, loader: LibraryLoader | None = None) -> None:
        self.paths = paths
        self.loader = loader or LibraryLoader()

    def install_agent(self, diff: DiffResult, scope: str = "global") -> bool:
        """
        Install an agent from the library.

        Args:
            diff: DiffResult containing agent information
            scope: "global" or "project"

        Returns:
            True if installation succeeded.
        """
        if diff.status not in (DiffStatus.NEW, DiffStatus.OUTDATED, DiffStatus.MODIFIED):
            return False

        if not diff.library_file:
            return False

        # Get library content
        try:
            content = self.loader.get_agent_content(diff.library_file)
        except Exception:
            return False

        # Determine target directory
        if scope == "global":
            target_dir = self.paths.global_agents
        else:
            if self.paths.project_agents is None:
                return False
            target_dir = self.paths.project_agents

        # Ensure directory exists
        target_dir.mkdir(parents=True, exist_ok=True)

        # Write file
        target_file = target_dir / f"{diff.name}.md"
        target_file.write_text(content)

        # Update state
        self._update_state(diff, scope, content)

        return True

    def install_global_agents(self, diffs: list[DiffResult]) -> dict[str, bool]:
        """Install multiple global agents."""
        results = {}
        for diff in diffs:
            if diff.status in (DiffStatus.NEW, DiffStatus.OUTDATED, DiffStatus.MODIFIED):
                results[diff.name] = self.install_agent(diff, scope="global")
        return results

    def install_project_agents(self, diffs: list[DiffResult]) -> dict[str, bool]:
        """Install multiple project agents."""
        results = {}
        for diff in diffs:
            if diff.status in (DiffStatus.NEW, DiffStatus.OUTDATED, DiffStatus.MODIFIED):
                results[diff.name] = self.install_agent(diff, scope="project")
        return results

    def _update_state(self, diff: DiffResult, scope: str, content: str) -> None:
        """Update the sync state file after installation."""
        state_file = self.paths.get_state_file(scope)
        state_file.parent.mkdir(parents=True, exist_ok=True)

        agent_installation = AgentInstallation(
            library_version=diff.library_version or "1.0.0",
            content_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
            installed_at=datetime.now(),
        )

        # Load existing state or create new
        if scope == "global":
            global_state = self._load_global_state(state_file)
            global_state.agents[diff.name] = agent_installation
            global_state.last_updated = datetime.now()
            self._save_state(state_file, global_state.model_dump(mode="json"))
        else:
            project_state = self._load_project_state(state_file)
            project_state.agents[diff.name] = agent_installation
            self._save_state(state_file, project_state.model_dump(mode="json"))

    def _load_global_state(self, state_file: Path) -> GlobalSyncState:
        """Load global sync state from file."""
        if state_file.exists():
            import json

            data = json.loads(state_file.read_text())
            return GlobalSyncState(**data)
        return GlobalSyncState()

    def _load_project_state(self, state_file: Path) -> ProjectSyncState:
        """Load project sync state from file."""
        if state_file.exists():
            import json

            data = json.loads(state_file.read_text())
            return ProjectSyncState(**data)
        return ProjectSyncState(project_path=str(self.paths.project_root or "."))

    def _save_state(self, state_file: Path, data: dict[str, Any]) -> None:
        """Save state to file."""
        import json

        state_file.write_text(json.dumps(data, indent=2, default=str))

    def install_command(self, diff: DiffResult, scope: str = "global") -> bool:
        """Install a command from the library."""
        if diff.status not in (DiffStatus.NEW, DiffStatus.OUTDATED, DiffStatus.MODIFIED):
            return False

        if not diff.library_file:
            return False

        try:
            content = self.loader.get_command_content(diff.library_file)
        except Exception:
            return False

        if scope == "global":
            target_dir = self.paths.global_commands
        else:
            if self.paths.project_commands is None:
                return False
            target_dir = self.paths.project_commands

        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"{diff.name}.md"
        target_file.write_text(content)

        return True

    def install_hook(self, diff: DiffResult, scope: str = "global") -> bool:
        """Install a hook from the library."""
        if diff.status not in (DiffStatus.NEW, DiffStatus.OUTDATED, DiffStatus.MODIFIED):
            return False

        if not diff.library_file:
            return False

        try:
            content = self.loader.get_hook_content(diff.library_file)
        except Exception:
            return False

        if scope == "global":
            target_dir = self.paths.global_hooks
        else:
            return False  # Hooks are only global

        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"{diff.name}.sh"
        target_file.write_text(content)

        # Make the hook executable
        import os

        os.chmod(target_file, 0o755)

        return True

    def install_hooks_settings(self) -> bool:
        """Install hooks configuration in settings.json."""
        import json

        hooks_template = self.loader.get_hooks_settings_template()
        if not hooks_template:
            return False

        settings_file = self.paths.global_settings

        # Load existing settings or create new
        if settings_file.exists():
            try:
                settings = json.loads(settings_file.read_text())
            except json.JSONDecodeError:
                settings = {}
        else:
            settings = {}

        # Merge hooks configuration
        if "hooks" not in settings:
            settings["hooks"] = {}

        settings["hooks"] = hooks_template.get("hooks", {})

        # Write back
        settings_file.write_text(json.dumps(settings, indent=2))
        return True
