# Commit avec Code Review & Security Check

Arguments utilisateur: **$ARGUMENTS**

## Instructions

Cette commande orchestre trois vérifications en séquence avant commit.

### Étape 1: Code Review (sauf si --skip-review)

**Si `--skip-review` n'est PAS dans les arguments**, utiliser l'outil Task pour lancer le code-reviewer:

```
Tool: Task
subagent_type: "custom-code-reviewer"
description: "Code review pre-commit"
prompt: |
  Effectue une revue de code sur les changements Git non commités.

  1. Exécuter: git diff
  2. Analyser qualité, sécurité, performance
  3. Produire un rapport avec verdict: APPROVED / CHANGES_REQUESTED

  Si issues de criticité Haute, indiquer clairement CHANGES_REQUESTED.
```

**Après réception du rapport**:
- Si `APPROVED` ou issues Moyenne/Basse uniquement → passer à l'étape 2
- Si `CHANGES_REQUESTED` avec issues Haute → ARRÊTER et informer l'utilisateur

---

### Étape 2: Security Check Rapide (sauf si --skip-security)

**Si `--skip-security` n'est PAS dans les arguments**, utiliser l'outil Task pour lancer un scan sécurité rapide:

```
Tool: Task
subagent_type: "custom-security-auth"
description: "Security check pre-commit"
prompt: |
  Effectue un scan de sécurité RAPIDE sur les changements Git non commités.

  1. Exécuter: git diff
  2. Vérifier:
     - Pas de secrets exposés (API keys, passwords, tokens)
     - Pas de credentials hardcodés
     - Inputs validés si nouveau code backend
     - Pas d'injection SQL évidente
     - Pas de v-html avec données utilisateur (frontend)
  3. Produire un rapport CONCIS avec verdict: SECURE / SECURITY_ISSUE

  Focus sur les NOUVELLES lignes uniquement. Scan rapide, pas audit complet.
  Si problème de sécurité critique (secret exposé, injection), indiquer SECURITY_ISSUE.
```

**Après réception du rapport**:
- Si `SECURE` → passer à l'étape 3
- Si `SECURITY_ISSUE` → ARRÊTER et informer l'utilisateur

---

### Étape 3: Commits Atomiques

Utiliser l'outil Task pour lancer l'agent commit:

```
Tool: Task
subagent_type: "custom-commit"
description: "Commits atomiques"
prompt: |
  Créer des commits atomiques pour les changements suivants.
  Arguments utilisateur: $ARGUMENTS

  1. Analyser git status et git diff
  2. Regrouper les changements par logique (feature, scope, type)
  3. Pour chaque groupe: git add + git commit avec message Conventional Commits
  4. Si --push dans les arguments: git push à la fin

  Format des messages: type(scope): description
  Types: feat, fix, refactor, test, docs, style, chore
```

---

## Arguments Supportés

| Argument | Action |
|----------|--------|
| (vide) | Code review + security check + commits atomiques |
| `--push` | Inclure push après les commits |
| `--skip-review` | Passer la code review |
| `--skip-security` | Passer le security check |
| `--skip-all` | Passer directement aux commits (équivalent --skip-review --skip-security) |
| `--dry-run` | Afficher sans exécuter |
