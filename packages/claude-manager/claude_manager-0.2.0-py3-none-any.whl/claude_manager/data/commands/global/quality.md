# Pipeline Qualité Complet

Lancez un pipeline de qualité complet pour: **$ARGUMENTS**

## Instructions

Vous êtes le Tech Lead. Lancez un pipeline de validation qualité multi-dimensionnel EN PARALLÈLE.

### Lancement Parallèle

Utilisez le Task tool pour lancer SIMULTANÉMENT:

```
Task(subagent_type="custom-qa", prompt="Analyse qualité tests de [cible]:
1. Vérifier couverture tests (cible: >80% backend, >60% frontend)
2. Identifier tests manquants
3. Vérifier TDD compliance
4. Identifier edge cases non couverts
5. Vérifier qualité des tests (pas de tests flaky)")

Task(subagent_type="custom-code-reviewer", prompt="Review qualité code de [cible]:
1. Patterns et conventions respectés
2. Pas de code dupliqué
3. Typage strict (pas de any/Object)
4. Nommage cohérent
5. Fonctions courtes et focalisées")

Task(subagent_type="custom-security-auth", prompt="Scan sécurité rapide de [cible]:
1. Validation inputs
2. Pas de secrets exposés
3. Injections potentielles
4. npm audit / dependency check")

Task(subagent_type="custom-playwright", prompt="Vérification E2E de [cible]:
1. Tests E2E passent
2. Scénarios critiques couverts
3. Tests stables (pas flaky)
4. Performance acceptable")
```

### Consolidation

Après réception des rapports, créez une synthèse:

```markdown
## Rapport Qualité

### Score Global

| Dimension | Score | Cible | Statut |
|-----------|-------|-------|--------|
| Couverture Backend | X% | 80% | ✅/❌ |
| Couverture Frontend | X% | 60% | ✅/❌ |
| Tests E2E | X/Y | 100% | ✅/❌ |
| Code Review | X/5 | 4/5 | ✅/❌ |
| Sécurité | X/5 | 4/5 | ✅/❌ |

### Verdict: ✅ PASS / ❌ FAIL

### Tests (QA)

#### Couverture
- Backend: X% (cible: 80%)
- Frontend: X% (cible: 60%)

#### Tests Manquants
1. [Service/Component]: [test manquant]
2. ...

#### Edge Cases Non Couverts
1. [Scénario]
2. ...

### Code Review

#### Points Positifs
- ...

#### Issues Détectées
| Fichier | Ligne | Issue | Criticité |
|---------|-------|-------|-----------|
| ... | ... | ... | ... |

### Sécurité (Scan Rapide)

- [ ] Inputs validés
- [ ] Pas de secrets
- [ ] Dépendances OK

#### Alertes
1. ...

### E2E (Playwright)

- Tests passés: X/Y
- Tests échoués: [liste]
- Tests flaky: [liste]

### Actions Requises

#### Bloquantes (avant merge)
1. 🔴 ...

#### Recommandées
1. 🟡 ...

#### Nice to Have
1. 🟢 ...
```

### Critères de Validation

Pour qu'une feature soit considérée comme "qualité OK":

| Critère | Minimum | Cible |
|---------|---------|-------|
| Couverture Backend | 70% | 80% |
| Couverture Frontend | 50% | 60% |
| Tests E2E critiques | 80% | 100% |
| Code Review score | 3/5 | 4/5 |
| Sécurité score | 3/5 | 4/5 |
| Zéro bug critique | Obligatoire | - |

### Règles

- Lancez les 4 agents EN PARALLÈLE (ils sont indépendants)
- Une couverture < minimum BLOQUE le merge
- Un problème de sécurité critique BLOQUE le merge
- Proposez un plan de correction si critères non atteints
