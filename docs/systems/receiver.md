# The Receiver

*"A jagged antenna of bone and crystal. It listens to frequencies the colony cannot hear."*

The Receiver is the colony's connection to the Outside.

## Stats

| Property | Value |
|----------|-------|
| **Type** | Antenna |
| **Location** | (4, 1) |

## Mechanics

- Consumes influence to attempt summoning
- **Threshold**: 2.0 influence
- **Success rate**: 30%
- **Cooldown**: 600 ticks (10 minutes)

## When Summoning Succeeds

A Visitor arrives:

- **Wanderer** (33%) - Leaves gifts, wanders
- **Observer** (33%) - Watches, generates insight
- **Hungry** (33%) - Eats influence, produces strange matter

## When Summoning Fails

- Influence is still consumed
- Nothing arrives
- `meta.failed_summons` increments

## Notes

The Receiver was built because something told the colony to build it. Who was speaking?

The void does not always answer. But sometimes it does.
