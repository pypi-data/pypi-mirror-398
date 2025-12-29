"""Paths management for Claude Code configuration directories."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ClaudePaths:
    """
    Manages paths to Claude Code configuration directories.

    Supports both global paths (~/.claude/) and project-specific paths (./.claude/).
    """

    # Global paths (user-level)
    global_base: Path = field(default_factory=lambda: Path.home() / ".claude")

    # Project path (optional, set when working with a specific project)
    project_root: Path | None = None

    # --- Global paths ---

    @property
    def global_agents(self) -> Path:
        """Global agents directory (~/.claude/agents/)."""
        return self.global_base / "agents"

    @property
    def global_commands(self) -> Path:
        """Global commands directory (~/.claude/commands/)."""
        return self.global_base / "commands"

    @property
    def global_hooks(self) -> Path:
        """Global hooks directory (~/.claude/hooks/)."""
        return self.global_base / "hooks"

    @property
    def global_settings(self) -> Path:
        """Global settings file (~/.claude/settings.json)."""
        return self.global_base / "settings.json"

    @property
    def global_plugins_config(self) -> Path:
        """Global MCP plugins config (~/.claude/plugins/config.json)."""
        return self.global_base / "plugins" / "config.json"

    @property
    def global_state_dir(self) -> Path:
        """Claude manager state directory (~/.claude/.claude-manager/)."""
        return self.global_base / ".claude-manager"

    @property
    def global_state_file(self) -> Path:
        """Global sync state file (~/.claude/.claude-manager/state.json)."""
        return self.global_state_dir / "state.json"

    # --- Project paths ---

    @property
    def project_base(self) -> Path | None:
        """Project-specific Claude directory (./.claude/)."""
        if self.project_root is None:
            return None
        return self.project_root / ".claude"

    @property
    def project_agents(self) -> Path | None:
        """Project agents directory (./.claude/agents/)."""
        if self.project_base is None:
            return None
        return self.project_base / "agents"

    @property
    def project_commands(self) -> Path | None:
        """Project commands directory (./.claude/commands/)."""
        if self.project_base is None:
            return None
        return self.project_base / "commands"

    @property
    def project_settings_local(self) -> Path | None:
        """Project local settings (./.claude/settings.local.json)."""
        if self.project_base is None:
            return None
        return self.project_base / "settings.local.json"

    @property
    def project_state_dir(self) -> Path | None:
        """Project state directory (./.claude/.claude-manager/)."""
        if self.project_base is None:
            return None
        return self.project_base / ".claude-manager"

    @property
    def project_state_file(self) -> Path | None:
        """Project sync state file (./.claude/.claude-manager/state.json)."""
        if self.project_state_dir is None:
            return None
        return self.project_state_dir / "state.json"

    # --- Utility methods ---

    def ensure_global_dirs(self) -> None:
        """Create all global directories if they don't exist."""
        self.global_agents.mkdir(parents=True, exist_ok=True)
        self.global_commands.mkdir(parents=True, exist_ok=True)
        self.global_hooks.mkdir(parents=True, exist_ok=True)
        self.global_state_dir.mkdir(parents=True, exist_ok=True)
        (self.global_base / "plugins").mkdir(parents=True, exist_ok=True)

    def ensure_project_dirs(self) -> None:
        """Create all project directories if they don't exist."""
        if self.project_base is None:
            raise ValueError("project_root must be set before calling ensure_project_dirs")

        # Store in local variables to help mypy understand they're not None
        project_agents = self.project_agents
        project_commands = self.project_commands
        project_state_dir = self.project_state_dir

        if project_agents is not None:
            project_agents.mkdir(parents=True, exist_ok=True)
        if project_commands is not None:
            project_commands.mkdir(parents=True, exist_ok=True)
        if project_state_dir is not None:
            project_state_dir.mkdir(parents=True, exist_ok=True)

    def with_project(self, project_path: Path) -> "ClaudePaths":
        """Return a new ClaudePaths instance with project_root set."""
        return ClaudePaths(
            global_base=self.global_base,
            project_root=project_path.resolve(),
        )

    @classmethod
    def for_project(cls, project_path: Path) -> "ClaudePaths":
        """Create a ClaudePaths instance for a specific project."""
        return cls(project_root=project_path.resolve())

    def get_agents_dir(self, scope: str) -> Path:
        """Get agents directory for the given scope ('global' or 'project')."""
        if scope == "global":
            return self.global_agents
        elif scope == "project":
            if self.project_agents is None:
                raise ValueError("project_root must be set for project scope")
            return self.project_agents
        else:
            raise ValueError(f"Invalid scope: {scope}. Must be 'global' or 'project'")

    def get_commands_dir(self, scope: str) -> Path:
        """Get commands directory for the given scope ('global' or 'project')."""
        if scope == "global":
            return self.global_commands
        elif scope == "project":
            if self.project_commands is None:
                raise ValueError("project_root must be set for project scope")
            return self.project_commands
        else:
            raise ValueError(f"Invalid scope: {scope}. Must be 'global' or 'project'")

    def get_state_file(self, scope: str) -> Path:
        """Get state file for the given scope ('global' or 'project')."""
        if scope == "global":
            return self.global_state_file
        elif scope == "project":
            if self.project_state_file is None:
                raise ValueError("project_root must be set for project scope")
            return self.project_state_file
        else:
            raise ValueError(f"Invalid scope: {scope}. Must be 'global' or 'project'")
