# Entities

Entities are the living (and visiting) things in the colony.

## Ants

Born from the Queen, ants are the colony's workers and maintainers.

### Roles

| Role | Description |
|------|-------------|
| **Worker** | General-purpose ant |
| **Undertaker** | Processes corpses, hungry slower |
| **Ornamental** | Adorned with jewelry, generates influence |

### Lifecycle

- **Max age**: 7,200 ticks (2 hours)
- **Hunger**: Decreases over time, eat fungus when < 50
- **Death causes**: Starvation or old age
- **After death**: Corpse → Undertaker → Nutrients

See [Ants](ants.md) for details.

## Visitors

Visitors come from the Outside via the Receiver. They are not born from the Queen.

| Type | Behavior |
|------|----------|
| **Wanderer** | Leaves gifts |
| **Observer** | Watches, generates insight |
| **Hungry** | Eats influence, produces strange_matter |

See [Visitors](visitors.md) for details.
