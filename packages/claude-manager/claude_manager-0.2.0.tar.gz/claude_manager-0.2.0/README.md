# Claude Manager

Gestionnaire de bibliothèque d'agents et serveurs MCP pour Claude Code.

## Installation

```bash
pip install claude-manager
```

## Usage

### Synchroniser les agents globaux

```bash
# Installer tous les agents globaux
claude-manager sync global

# Voir l'état de synchronisation
claude-manager sync status
```

### Analyser un projet

```bash
# Analyser le projet courant et recommander des agents
claude-manager analyze .

# Dry-run : voir les recommandations sans installer
claude-manager analyze . --dry-run
```

### Gérer les serveurs MCP

```bash
# Lister les serveurs disponibles
claude-manager mcp list

# Installer un serveur
claude-manager mcp install github

# Vérifier les mises à jour
claude-manager mcp check
```

### Explorer la bibliothèque

```bash
# Lister tous les templates
claude-manager library list

# Rechercher par tags
claude-manager library search vue

# Voir les détails d'un agent
claude-manager library info spring-boot
```

## Architecture

### Agents

- **Globaux** (`~/.claude/agents/`) : Toujours disponibles pour tous les projets
- **Projet** (`./.claude/agents/`) : Installés selon le contexte du projet

### Serveurs MCP

- **Globaux** : Configurés dans `~/.claude/plugins/config.json`
- **Projet** : Configurés dans `./.claude/settings.local.json`

## Développement

```bash
# Cloner le repo
git clone https://gitlab.com/ratatosk42-group/claude-manager.git
cd claude-manager

# Créer un venv
python -m venv .venv
source .venv/bin/activate

# Installer en mode développement
pip install -e ".[dev]"

# Lancer les tests
pytest

# Linter
ruff check src/
mypy src/
```

## License

This project is licensed under the GNU General Public License v3.0 or later (GPLv3+).
See [LICENSE.md](LICENSE.md) for details.
