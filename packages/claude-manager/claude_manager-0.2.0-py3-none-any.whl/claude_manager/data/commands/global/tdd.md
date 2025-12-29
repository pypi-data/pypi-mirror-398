# TDD Workflow

Développez en TDD (Test Driven Development): **$ARGUMENTS**

## Instructions

Vous êtes le Tech Lead. Appliquez strictement le cycle TDD: **Red → Green → Refactor**

### Cycle TDD

```
┌─────────┐     ┌─────────┐     ┌──────────┐
│   RED   │────▶│  GREEN  │────▶│ REFACTOR │
│  Test   │     │  Code   │     │ Improve  │
│ Fails   │     │ Passes  │     │ Quality  │
└─────────┘     └─────────┘     └──────────┘
     ▲                                │
     └────────────────────────────────┘
```

### Phase 1: Analyse & Spécification

1. **Comprendre le besoin** et définir:
   - Comportement attendu (Given/When/Then)
   - Cas nominaux
   - Cas d'erreur
   - Edge cases

2. **Identifier les composants**:
   - Backend: Controllers, Services, Repositories
   - Frontend: Components, Composables, Stores
   - E2E: User flows

### Phase 2: RED - Écrire les Tests

Lancez les agents pour écrire les tests AVANT le code:

**Backend (qa agent)**:
```java
@Test
void should_return_metrics_when_authenticated() {
    // Given
    // When
    // Then
    fail("Not implemented yet"); // RED
}
```

**Frontend (qa agent)**:
```typescript
it('should display loading state initially', () => {
    // Arrange
    // Act
    // Assert
    expect(true).toBe(false) // RED
})
```

**E2E (playwright agent)**:
```typescript
test('user can view dashboard', async ({ page }) => {
    // Arrange
    // Act
    // Assert
    await expect(page.locator('h1')).toHaveText('Dashboard')
})
```

### Phase 3: GREEN - Implémentation Minimale

Lancez les agents d'implémentation pour:
- Écrire le code **minimal** qui fait passer les tests
- Pas d'optimisation prématurée
- Pas de fonctionnalités supplémentaires

### Phase 4: REFACTOR - Amélioration

Après que tous les tests passent:
- Supprimer la duplication
- Améliorer la lisibilité
- Optimiser si nécessaire
- **Les tests doivent toujours passer**

### Phase 5: Validation

Lancez EN PARALLÈLE:
```
playwright → Tests E2E complets
qa → Couverture et qualité
architect → Review structure
```

## Règles Strictes TDD

1. **Jamais de code sans test** (sauf configuration)
2. **Un test à la fois**
3. **Code minimal** pour faire passer le test
4. **Refactor** seulement après GREEN
5. **Tests = Documentation** vivante

## Patterns de Test

### Given/When/Then (BDD)
```java
@Test
void should_calculate_total_with_discount() {
    // Given (Arrange)
    Order order = new Order(100.0);
    order.applyDiscount(10);

    // When (Act)
    double total = order.getTotal();

    // Then (Assert)
    assertThat(total).isEqualTo(90.0);
}
```

### AAA Pattern
```typescript
it('should filter active users', () => {
    // Arrange
    const store = useUsersStore()
    store.users = [
        { id: '1', active: true },
        { id: '2', active: false }
    ]

    // Act
    const result = store.activeUsers

    // Assert
    expect(result).toHaveLength(1)
})
```

## Couverture Cible

| Couche | Cible | Minimum |
|--------|-------|---------|
| Backend Services | 90% | 80% |
| Backend Controllers | 80% | 70% |
| Frontend Components | 70% | 60% |
| E2E Critical Paths | 100% | 80% |
