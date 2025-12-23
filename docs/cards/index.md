# Cards

Cards are prompts that fire when conditions are met. They drive the game forward by forcing decisions and building.

## How Cards Work

1. Cards register on the event bus
2. Each tick, conditions are checked
3. When conditions are met, the card fires
4. Claude responds by making decisions or building systems
5. Most cards fire once; some can repeat

## Card Types

| Type | Purpose |
|------|---------|
| **Question** | Philosophical prompts |
| **Quest** | Tasks requiring grinding or building |
| **Observation** | Notices about the colony state |
| **Design Prompt** | Requests to build something new |
| **Milestone** | Markers of progress |
| **Warning** | Alerts about problems |
| **Audit** | Engineering reviews |

## Card Waves

Cards are organized into waves that unlock as the game progresses:

1. **Starter Cards** - Bootstrap the colony
2. **Wave Two** - The death economy
3. **Wave Three** - Quiet contemplation
4. **Wave Four** - Purpose and beauty
5. **Wave Five** - Adornment and influence
6. **Wave Six** - The Outside

## Fired Cards

Cards that have fired are tracked in `meta.fired_cards`. Most cannot fire again.

## Rare Cards

Some cards (like WWCD) have special firing conditions:

- Cooldown periods
- Random chance per tick
- Can fire multiple times
