# Implémentation Parallèle (TDD)

Lancez une implémentation parallèle front/back/db pour: **$ARGUMENTS**

## Instructions

Vous êtes le Tech Lead. Lancez SIMULTANÉMENT les agents spécialisés avec approche TDD.

### Analyse Rapide

Identifiez ce qui doit être fait sur chaque couche:
- **Database**: Nouvelles tables? Modifications schéma? Index?
- **Backend (Spring Boot)**: Nouveaux endpoints? Modifications services?
- **Frontend (Vue 3)**: Nouvelles pages/composants? Modifications UI?
- **Auth (Keycloak)**: Nouveaux rôles? Permissions?

### Phase 1: Tests First

Lancez EN PARALLÈLE les tests pour chaque couche:

```
Task(subagent_type="qa", prompt="Écrire les tests backend pour: [spec]")
Task(subagent_type="qa", prompt="Écrire les tests frontend pour: [spec]")
Task(subagent_type="playwright", prompt="Écrire les tests E2E pour: [spec]")
```

### Phase 2: Implémentation

Lancez EN PARALLÈLE l'implémentation:

```
Task(subagent_type="database-sonnet", prompt="[tâche DB spécifique]")
Task(subagent_type="backend-sonnet", prompt="[tâche backend spécifique]")
Task(subagent_type="frontend", prompt="[tâche frontend spécifique]")
```

### Règles de Parallélisation

**OK en parallèle:**
- Schéma DB + DTOs backend + Types frontend
- Tests unitaires de chaque couche
- Composants frontend indépendants

**Séquentiel obligatoire:**
- Migration DB → Service backend (si dépendance)
- Service backend → Appel frontend (si nouvelle API)
- Keycloak config → Backend security (si nouveaux rôles)

### Phase 3: Validation

Lancez EN PARALLÈLE:
```
Task(subagent_type="playwright", prompt="Exécuter tests E2E")
Task(subagent_type="qa", prompt="Vérifier couverture tests")
```

### Rapport

À la fin, consolidez les résultats:

```markdown
## Résumé Implémentation

### Tests Créés (TDD)
- Backend: X tests
- Frontend: X tests
- E2E: X tests

### Fichiers par Couche
**Database:**
- migration/V1__xxx.sql

**Backend:**
- controller/XxxController.java
- service/XxxService.java
- dto/XxxDto.java

**Frontend:**
- app/xxx/page.tsx
- components/Xxx.tsx
- stores/xxx.ts

### Points d'Intégration
1. API: GET/POST /api/xxx
2. Auth: role 'xxx' required
3. Store: useXxxStore

### Couverture
- Backend: X%
- Frontend: X%
```
