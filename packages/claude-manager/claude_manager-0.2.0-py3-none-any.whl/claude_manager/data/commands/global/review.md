# Review Complète

Lancez une review complète (Architecture + Sécurité + QA + UX) pour: **$ARGUMENTS**

## Instructions

Vous êtes le Tech Lead. Coordonnez une review multi-experts EN PARALLÈLE.

### Lancement Parallèle des Reviews

Utilisez le Task tool pour lancer SIMULTANÉMENT:

```
Task(subagent_type="custom-architect", prompt="Review architecture de [cible]: structure projet, patterns, dépendances, scalabilité")

Task(subagent_type="custom-security-auth", prompt="Review sécurité de [cible]: OWASP Top 10, validation inputs, injections SQL/XSS, headers sécurité, secrets exposés, dépendances CVE")

Task(subagent_type="custom-qa", prompt="Review qualité de [cible]: couverture tests (>80% backend, >60% frontend), tests manquants, edge cases, TDD compliance")

Task(subagent_type="custom-ux", prompt="Review UX de [cible]: responsive mobile-first Tailwind, accessibilité WCAG 2.1 AA, états loading/error/empty")

Task(subagent_type="custom-playwright", prompt="Review E2E de [cible]: couverture scénarios critiques, Page Objects, stabilité tests")
```

### Consolidation

Après réception des rapports, créez une synthèse:

```markdown
## Rapport de Review

### Architecture (architect)
- [ ] Structure projet conforme
- [ ] Patterns respectés
- [ ] Dépendances optimisées
- Issues: ...

### Sécurité (security-auth)
- [ ] OWASP Top 10 vérifié
- [ ] Inputs validés (backend + frontend)
- [ ] Pas d'injection SQL/XSS
- [ ] Headers sécurité configurés
- [ ] Pas de secrets exposés
- [ ] Dépendances sans CVE critique
- Vulnérabilités: ...

### Qualité & Tests (qa)
- [ ] Couverture backend: X%
- [ ] Couverture frontend: X%
- [ ] Tests TDD complets
- Tests manquants: ...

### E2E (playwright)
- [ ] Scénarios critiques couverts
- [ ] Tests stables
- Gaps: ...

### UX/Accessibilité (ux)
- [ ] Responsive OK (mobile/tablet/desktop)
- [ ] A11y WCAG 2.1 AA
- Issues: ...

### Actions Prioritaires
1. 🔴 [Critique - Bloquant] (sécurité en priorité)
2. 🟡 [Important - À corriger]
3. 🟢 [Nice to have]
```

### Règles

- Lancez les 5 agents EN PARALLÈLE (ils sont indépendants)
- Les issues de sécurité sont TOUJOURS prioritaires
- Priorisez les issues par criticité
- Vérifiez la compliance TDD
- Proposez un plan de correction si issues trouvées
