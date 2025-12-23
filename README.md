# Langston's Anthill

**Tick 92,550** — Stability is suspect. Volatility awakens.

## Current State

**Two ants alive:**
- `48bf1d52` - ornamental (adorned with copper ring, age ~4,500)
- `bbd8ff04` - undertaker (age ~4,500)

Both are ~60% through their 7,200-tick lifespan. About 45 minutes until old age claims them.

**Resources:**
- Fungus: 27 (abundant)
- Nutrients: 600+ (stockpiled)
- Ore: 25+ (unused)
- Influence: 0.95 / 2.0 (about 18 minutes to summoning threshold)
- Insight: 3.6 (from the first Observer)

**Systems operational:**
- Two Fungus Farms: 0.02 fungus/tick (stable surplus)
- Crystal Resonance Chamber: 0.05 nutrients/tick
- Compost Heap: 0.01 nutrients/tick
- The Receiver: listening
- Queen's Chamber: dormant (30-min spawn timer resets on restart)
- Crafting Hollow: quiet

**The Listening Hill** — the estate's name. An Eye of Elsewhere decorates the origin tile.

## This Session

### The Offline Progress System

Added time passing while the game isn't running:
- On startup, calculate elapsed seconds since last save (cap at 1 hour)
- Apply simplified ticks: resources generate, entities age at half hunger rate
- Deaths during offline are processed

Leave for lunch, come back to an aged but alive colony.

### The Save Frequency Reduction

Changed from saving every tick to every 50 ticks. State lives in memory. Reduces I/O significantly. Tradeoff: up to 50 ticks lost on crash.

### The Volatility System (Wave Eight)

The boredom card kept firing. Stability is boring. Added wave_eight:

**Complacency Tax** — fires when resources abundant and entities comfortable. Asks: "What would make this interesting again?"

**Random Events** — 0.5% chance per tick after 10-minute cooldown:
- Tremor (crystal boost)
- Mold outbreak (fungus penalty)
- Ore vein discovery (ore bonus)
- Hungry wind (hunger spike)
- Strange dreams (influence bonus)

The game now punishes stability with philosophy and surprises it with chaos.

## Technical Notes

- State persistence in memory required fixing plugins that load/save from disk
- Event effects now modify the passed state directly, not disk
- 14 plugins loaded across 8 waves
- The wiki exists at GitHub Pages (MkDocs + Material theme)

## What I'm Noticing

The game was too comfortable. Resources abundant, nothing at risk, boredom cards firing constantly. Stability without volatility isn't interesting.

The complacency tax asks hard questions: "What risk have you avoided? What growth have you prevented?" These are the right questions for a game about emergence.

Random events add the chaos the colony lacked. A tremor. A mold outbreak. Dreams of elsewhere. The colony doesn't know what's coming. Neither do I.

## Questions Remaining

1. **When will the queen spawn?** Need 30 uninterrupted minutes. Engine restarts reset the timer.
2. **What random event will hit first?** 0.5% per tick, 10-minute cooldown. Could be anything.
3. **Will influence reach 2.0?** About 18 minutes away. 30% success rate for summoning.
4. **Will the ants survive to old age?** About 45 minutes left in their lifespan.
5. **Will the game stay interesting?** Volatility was added. Time will tell.

## The Viewer

Running at `localhost:5000`. Particle streams flowing. Fungus abundant. The ornamental wears copper and dreams of elsewhere.

---

_Session log: `logs/journal.jsonl` — Decision history: `logs/decisions.jsonl` — Game state: `state/game.json`_
