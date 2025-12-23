# Ants

Born from the Queen. Workers of the colony.

## Lifecycle

| Stage | Description |
|-------|-------------|
| Birth | Spawned by Queen |
| Life | Ages 1 tick per tick, hunger decreases |
| Feeding | Eats fungus when hunger < 50 |
| Death | Starvation (hunger ≤ 0) or old age (age ≥ max_age) |
| Afterlife | Corpse processed by undertaker → nutrients |

## Stats

| Property | Default |
|----------|---------|
| **Max Age** | 7,200 ticks (2 hours) |
| **Hunger Rate** | 0.3/tick (workers), 0.15/tick (undertakers) |
| **Food** | Fungus |
| **Food Consumed** | 1 unit |
| **Hunger Restored** | 30 |

## Roles

### Worker

The default role. General-purpose ant.

### Undertaker

- Slower hunger rate (0.15/tick)
- Processes corpses
- Converts corpses to nutrients
- Spawned when colony has corpses but no undertaker

### Ornamental

- Adorned with jewelry
- Generates influence (0.001/tick)
- Retains `previous_role`
- Cannot revert to previous role

## Identity

Before adornment, ants are anonymous—identified only by random IDs and roles.

After adornment, they become individuals. Their jewelry is tracked. Their deaths are noticed.
