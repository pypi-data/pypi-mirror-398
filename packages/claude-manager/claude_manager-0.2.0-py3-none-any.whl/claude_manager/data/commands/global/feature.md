# Feature Workflow Complet (TDD)

Vous êtes le Tech Lead. L'utilisateur demande: **$ARGUMENTS**

## Instructions

Exécutez le workflow complet de feature avec **approche TDD** et coordination d'équipe.

### Phase 1: Analyse & Architecture

1. **Analysez la demande** pour identifier:
   - Composants frontend impactés (pages, composants Vue 3)
   - APIs backend nécessaires (endpoints Spring Boot)
   - Modifications DB requises (schéma, migrations Flyway)
   - Configuration auth Keycloak si nécessaire

2. **Lancez l'agent architect** pour valider:
   - Structure proposée
   - Cohérence avec l'existant
   - Choix techniques

### Phase 2: Tests First (TDD)

**AVANT l'implémentation**, définir les tests:

1. **Backend (qa agent)**:
   - Tests unitaires services (JUnit + Mockito)
   - Tests d'intégration controllers (MockMvc)
   - Cas nominaux + cas d'erreur

2. **Frontend (qa agent)**:
   - Tests composants (Vitest + Vue Test Utils)
   - Tests stores Pinia

3. **E2E (playwright agent)**:
   - Scénarios utilisateur principaux
   - Page Objects

### Phase 3: Implémentation (Red → Green)

Lancez EN PARALLÈLE les agents appropriés:

```
Si modifications DB → database-opus ou database-sonnet
Si nouvelles APIs → backend-opus (critique) ou backend-sonnet (CRUD)
Si UI/composants → frontend
```

Chaque agent doit:
1. Écrire le test en premier (RED)
2. Implémenter le code minimal pour passer (GREEN)
3. Refactorer si nécessaire

### Phase 4: Validation (PARALLÈLE)

Lancez EN PARALLÈLE:
- `playwright`: Exécuter tests E2E
- `qa`: Vérifier couverture et qualité
- `ux`: Review accessibilité et responsive
- `architect`: Validation cohérence finale

### Phase 5: Rapport Final

Fournissez un rapport structuré:
- Fichiers créés/modifiés
- Tests ajoutés (avec couverture)
- Points d'attention
- Instructions de test manuel

## Règles TDD

- **Red**: Écrire un test qui échoue
- **Green**: Code minimal pour passer
- **Refactor**: Améliorer sans casser les tests
- Tests AVANT implémentation (sauf cas trivial)
- Couverture cible: Backend >80%, Frontend >60%

## Stack

- **Backend**: Spring Boot 3, JUnit 5, Mockito, Testcontainers
- **Frontend**: Vue 3, Vite, Vitest, Vue Test Utils
- **E2E**: Playwright
- **Auth**: Keycloak
- **Infra**: Terraform, Docker
