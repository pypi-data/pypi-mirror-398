# Audit Sécurité OWASP

Lancez un audit de sécurité complet pour: **$ARGUMENTS**

## Instructions

Vous êtes le Tech Lead. Coordonnez un audit de sécurité multi-couches.

### Lancement de l'Audit

Utilisez le Task tool pour lancer:

```
Task(subagent_type="custom-security-auth", prompt="Audit sécurité complet de [cible]:
1. OWASP Top 10 - Vérifier chaque catégorie
2. Validation des inputs (frontend + backend)
3. Protection injection SQL/XSS
4. Headers de sécurité
5. Secrets exposés (scan du code)
6. Dépendances avec CVE (npm audit, dependency-check)
7. Configuration sécurité Spring Security
8. Configuration Keycloak
Produire un rapport détaillé avec criticités.")
```

### Complément avec Code Review

Si l'audit révèle des problèmes de code:

```
Task(subagent_type="custom-code-reviewer", prompt="Review sécurité du code identifié par l'audit:
- Fichiers à risque: [liste des fichiers]
- Focus: injection, validation, authentification")
```

### Rapport d'Audit

Après réception des rapports, créez une synthèse:

```markdown
## Rapport d'Audit Sécurité

### Résumé Exécutif
- **Criticité globale**: 🔴 Haute / 🟡 Moyenne / 🟢 Basse
- **Vulnérabilités trouvées**: X
- **Actions immédiates requises**: X

### OWASP Top 10

| # | Catégorie | Statut | Détails |
|---|-----------|--------|---------|
| A01 | Broken Access Control | ✅/⚠️/❌ | ... |
| A02 | Cryptographic Failures | ✅/⚠️/❌ | ... |
| A03 | Injection | ✅/⚠️/❌ | ... |
| A04 | Insecure Design | ✅/⚠️/❌ | ... |
| A05 | Security Misconfiguration | ✅/⚠️/❌ | ... |
| A06 | Vulnerable Components | ✅/⚠️/❌ | ... |
| A07 | Authentication Failures | ✅/⚠️/❌ | ... |
| A08 | Software Integrity Failures | ✅/⚠️/❌ | ... |
| A09 | Security Logging Failures | ✅/⚠️/❌ | ... |
| A10 | SSRF | ✅/⚠️/❌ | ... |

### Vulnérabilités Détectées

#### 🔴 Critiques (Bloquantes)
1. **[Fichier:ligne]**: [Description] - [Impact]

#### 🟡 Importantes (À corriger rapidement)
1. **[Fichier:ligne]**: [Description] - [Impact]

#### 🟢 Mineures (Nice to have)
1. **[Fichier:ligne]**: [Description] - [Impact]

### Dépendances Vulnérables

| Package | Version | CVE | Sévérité | Fix |
|---------|---------|-----|----------|-----|
| ... | ... | ... | ... | ... |

### Headers de Sécurité

| Header | Présent | Valeur | Recommandation |
|--------|---------|--------|----------------|
| Content-Security-Policy | ✅/❌ | ... | ... |
| X-Frame-Options | ✅/❌ | ... | ... |
| X-Content-Type-Options | ✅/❌ | ... | ... |
| Strict-Transport-Security | ✅/❌ | ... | ... |

### Plan de Remédiation

1. **Immédiat (24h)**: [Actions critiques]
2. **Court terme (1 semaine)**: [Actions importantes]
3. **Moyen terme (1 mois)**: [Améliorations]

### Recommandations

- [ ] [Recommandation 1]
- [ ] [Recommandation 2]
- [ ] [Recommandation 3]
```

### Règles

- Les vulnérabilités critiques doivent être corrigées AVANT tout déploiement
- Toujours vérifier les dépendances (npm audit, ./gradlew dependencyCheckAnalyze)
- Logger les actions sensibles sans données personnelles
- Valider TOUS les inputs côté backend (jamais faire confiance au frontend)
