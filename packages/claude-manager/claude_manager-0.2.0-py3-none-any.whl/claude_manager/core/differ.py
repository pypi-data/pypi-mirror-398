"""Library differ - compares local installation with library templates."""

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from claude_manager.core.paths import ClaudePaths
from claude_manager.library.loader import LibraryLoader


class DiffStatus(str, Enum):
    """Status of a template compared to library."""

    NEW = "new"  # In library but not installed
    SYNCED = "synced"  # Installed and matches library
    MODIFIED = "modified"  # Installed but differs from library
    OUTDATED = "outdated"  # Installed but older version
    CUSTOM = "custom"  # Installed but not in library


@dataclass
class DiffResult:
    """Result of comparing a template with the library."""

    name: str
    status: DiffStatus
    scope: str  # "global" or "project"
    category: str | None = None
    local_path: Path | None = None
    library_file: str | None = None
    local_version: str | None = None
    library_version: str | None = None
    local_hash: str | None = None
    library_hash: str | None = None


class LibraryDiffer:
    """Compares local installation with library templates."""

    def __init__(self, paths: ClaudePaths, loader: LibraryLoader) -> None:
        self.paths = paths
        self.loader = loader

    def diff_agents(self, scope: str = "global") -> list[DiffResult]:
        """
        Compare installed agents with library.

        Args:
            scope: "global" or "project"

        Returns:
            List of DiffResult for each agent.
        """
        results = []

        if scope == "global":
            results.extend(self._diff_global_agents())
        elif scope == "project":
            results.extend(self._diff_project_agents())
        else:
            raise ValueError(f"Invalid scope: {scope}")

        return results

    def _diff_global_agents(self) -> list[DiffResult]:
        """Compare global agents."""
        results = []
        local_dir = self.paths.global_agents

        # Get library agents
        library_agents = self.loader.list_global_agents()

        # Check each library agent
        for agent in library_agents:
            name = agent["name"]
            library_file = agent.get("file", "")
            library_version = agent.get("version", "1.0.0")

            # Expected local file name (use the agent name + .md)
            local_file = local_dir / f"{name}.md"

            if local_file.exists():
                # Compare content
                try:
                    library_content = self.loader.get_agent_content(library_file)
                    local_content = local_file.read_text()

                    library_hash = self._hash_content(library_content)
                    local_hash = self._hash_content(local_content)

                    if library_hash == local_hash:
                        status = DiffStatus.SYNCED
                    else:
                        status = DiffStatus.MODIFIED
                except Exception:
                    status = DiffStatus.MODIFIED
                    library_hash = None
                    local_hash = self._hash_content(local_file.read_text())
            else:
                status = DiffStatus.NEW
                library_hash = None
                local_hash = None

            results.append(
                DiffResult(
                    name=name,
                    status=status,
                    scope="global",
                    local_path=local_file if local_file.exists() else None,
                    library_file=library_file,
                    local_version=None,  # Would need to parse frontmatter
                    library_version=library_version,
                    local_hash=local_hash,
                    library_hash=library_hash,
                )
            )

        # Check for custom agents (in local but not in library)
        if local_dir.exists():
            library_names = {a["name"] for a in library_agents}
            for local_file in local_dir.glob("*.md"):
                name = local_file.stem
                if name not in library_names:
                    results.append(
                        DiffResult(
                            name=name,
                            status=DiffStatus.CUSTOM,
                            scope="global",
                            local_path=local_file,
                            local_hash=self._hash_content(local_file.read_text()),
                        )
                    )

        return results

    def _diff_project_agents(self) -> list[DiffResult]:
        """Compare project agents."""
        results: list[DiffResult] = []

        if self.paths.project_agents is None:
            return results

        local_dir = self.paths.project_agents
        library_agents = self.loader.list_project_agents()

        for agent in library_agents:
            name = agent["name"]
            category = agent.get("category")
            library_file = agent.get("file", "")
            library_version = agent.get("version", "1.0.0")

            local_file = local_dir / f"{name}.md"

            if local_file.exists():
                try:
                    library_content = self.loader.get_agent_content(library_file)
                    local_content = local_file.read_text()

                    library_hash = self._hash_content(library_content)
                    local_hash = self._hash_content(local_content)

                    if library_hash == local_hash:
                        status = DiffStatus.SYNCED
                    else:
                        status = DiffStatus.MODIFIED
                except Exception:
                    status = DiffStatus.MODIFIED
                    library_hash = None
                    local_hash = self._hash_content(local_file.read_text())
            else:
                status = DiffStatus.NEW
                library_hash = None
                local_hash = None

            results.append(
                DiffResult(
                    name=name,
                    status=status,
                    scope="project",
                    category=category,
                    local_path=local_file if local_file.exists() else None,
                    library_file=library_file,
                    library_version=library_version,
                    local_hash=local_hash,
                    library_hash=library_hash,
                )
            )

        return results

    def diff_commands(self, scope: str = "global") -> list[DiffResult]:
        """Compare installed commands with library."""
        if scope != "global":
            return []  # Only global commands for now

        results = []
        local_dir = self.paths.global_commands

        library_commands = self.loader.list_global_commands()

        for command in library_commands:
            name = command["name"]
            library_file = command.get("file", "")
            library_version = command.get("version", "1.0.0")

            local_file = local_dir / f"{name}.md"

            if local_file.exists():
                try:
                    library_content = self.loader.get_command_content(library_file)
                    local_content = local_file.read_text()

                    library_hash = self._hash_content(library_content)
                    local_hash = self._hash_content(local_content)

                    if library_hash == local_hash:
                        status = DiffStatus.SYNCED
                    else:
                        status = DiffStatus.MODIFIED
                except Exception:
                    status = DiffStatus.MODIFIED
                    library_hash = None
                    local_hash = self._hash_content(local_file.read_text())
            else:
                status = DiffStatus.NEW
                library_hash = None
                local_hash = None

            results.append(
                DiffResult(
                    name=name,
                    status=status,
                    scope="global",
                    local_path=local_file if local_file.exists() else None,
                    library_file=library_file,
                    library_version=library_version,
                    local_hash=local_hash,
                    library_hash=library_hash,
                )
            )

        return results

    def diff_hooks(self, scope: str = "global") -> list[DiffResult]:
        """Compare installed hooks with library."""
        if scope != "global":
            return []  # Only global hooks for now

        results = []
        local_dir = self.paths.global_hooks

        library_hooks = self.loader.list_global_hooks()

        for hook in library_hooks:
            name = hook["name"]
            library_file = hook.get("file", "")
            library_version = hook.get("version", "1.0.0")

            # Hook files are shell scripts
            local_file = local_dir / f"{name}.sh"

            if local_file.exists():
                try:
                    library_content = self.loader.get_hook_content(library_file)
                    local_content = local_file.read_text()

                    library_hash = self._hash_content(library_content)
                    local_hash = self._hash_content(local_content)

                    if library_hash == local_hash:
                        status = DiffStatus.SYNCED
                    else:
                        status = DiffStatus.MODIFIED
                except Exception:
                    status = DiffStatus.MODIFIED
                    library_hash = None
                    local_hash = self._hash_content(local_file.read_text())
            else:
                status = DiffStatus.NEW
                library_hash = None
                local_hash = None

            results.append(
                DiffResult(
                    name=name,
                    status=status,
                    scope="global",
                    local_path=local_file if local_file.exists() else None,
                    library_file=library_file,
                    library_version=library_version,
                    local_hash=local_hash,
                    library_hash=library_hash,
                )
            )

        return results

    @staticmethod
    def _hash_content(content: str) -> str:
        """Generate SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
