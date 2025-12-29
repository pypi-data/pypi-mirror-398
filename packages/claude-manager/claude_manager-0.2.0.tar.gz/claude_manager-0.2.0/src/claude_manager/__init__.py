"""Claude Manager - Gestionnaire de bibliothèque d'agents et serveurs MCP pour Claude Code."""

try:
    from claude_manager._version import __version__
except ImportError:
    __version__ = "0.0.0.dev0"  # Fallback for development

__author__ = "Zug"

from claude_manager.core.paths import ClaudePaths

__all__ = ["__version__", "ClaudePaths"]
