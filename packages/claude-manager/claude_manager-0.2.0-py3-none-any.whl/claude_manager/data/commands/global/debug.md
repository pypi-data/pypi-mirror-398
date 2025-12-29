# Debug Multi-Couches

Débugger un problème touchant potentiellement plusieurs couches: **$ARGUMENTS**

## Instructions

Vous êtes le Tech Lead. Coordonnez le debugging sur toutes les couches impactées.

### Phase 1: Diagnostic

Analysez le problème pour identifier les couches potentiellement concernées:
- **Frontend (Vue 3)**: Erreurs console, états Pinia incorrects, UI cassée
- **Backend (Spring Boot)**: Erreurs API, logs serveur, exceptions
- **Database (PostgreSQL)**: Données incorrectes, queries lentes
- **Auth (Keycloak)**: Tokens invalides, permissions, SSO

### Phase 2: Investigation Parallèle

Si le problème touche plusieurs couches, lancez EN PARALLÈLE:

```
# Pour bugs critiques (production)
Task(subagent_type="debug-opus", prompt="Investiguer [couche]: [description du problème]")

# Pour bugs standards (développement)
Task(subagent_type="debug-sonnet", prompt="Investiguer [couche]: [description du problème]")
```

### Phase 3: Corrélation

1. Collectez les findings de chaque agent
2. Identifiez la root cause (souvent à l'intersection des couches)
3. Proposez un plan de correction avec tests

### Règles de Choix d'Agent

```
Bug production / données corrompues / sécurité?
  → debug-opus

Bug local / test échoué / erreur console?
  → debug-sonnet

Problème auth / tokens / sessions?
  → keycloak

Problème déploiement / infra?
  → devops

Problème tests E2E?
  → playwright
```

### Phase 4: Correction TDD

Après identification du bug:
1. **Écrire un test** qui reproduit le bug (RED)
2. **Corriger** le code (GREEN)
3. **Refactorer** si nécessaire
4. S'assurer que les tests existants passent toujours

### Rapport Final

```markdown
## Diagnostic

### Root Cause
[Description de la cause principale]

### Couches Impactées
- Frontend: [impact]
- Backend: [impact]
- Database: [impact]
- Auth: [impact]

### Reproduction
Test ajouté: `[nom du test]`

### Solution Appliquée
1. [Modification 1]
2. [Modification 2]

### Prévention Future
- [Test ajouté]
- [Monitoring ajouté]
```
