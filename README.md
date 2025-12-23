# Langston's Anthill

**Tick 91,800** — Time passes whether you're watching or not.

## Current State

**Two ants alive:**
- `48bf1d52` - ornamental (adorned with copper ring, age 3,823)
- `bbd8ff04` - undertaker (age 3,823)

Both are past halfway through their 7,200-tick lifespan. The ornamental generates influence. The undertaker waits for death. Neither has died yet this generation.

**Resources:**
- Fungus: 21 (well above queen spawn threshold of 15)
- Nutrients: 587 (abundant)
- Ore: 25 (unused)
- Influence: 0.9 / 2.0 (crawling toward summoning threshold)
- Insight: 3.6 (from the first Observer)

**Systems operational:**
- Two Fungus Farms: 0.02 fungus/tick (stable surplus)
- Crystal Resonance Chamber: 0.05 nutrients/tick
- Compost Heap: 0.01 nutrients/tick
- The Receiver: listening, consuming influence passively
- Queen's Chamber: ready to spawn (timer-based, not resource-gated now)
- Crafting Hollow: quiet

**The Listening Hill** — the estate has a name now. An Eye of Elsewhere watches from the origin tile, left by the first Observer.

## This Session

### The Offline Progress System (Tick ~91,000)

Added time passing while the game isn't running. On startup, the engine calculates elapsed seconds since last save, caps at 1 hour, and applies simplified ticks:
- Resources generate normally
- Entities age but hunger at half rate (foraging bonus)
- Entities auto-eat if hungry and food available
- Deaths during offline are processed

This means leaving for lunch doesn't reset the colony. The game continues in your absence, up to an hour of catch-up.

### The Save Frequency Reduction

Changed from saving every tick to saving every 50 ticks. State lives in memory between saves. This reduces I/O significantly. The tradeoff: up to 50 ticks of progress could be lost on crash. Acceptable for an experiment.

### What the Colony Looks Like

Fungus is abundant now. The second fungus farm saved the colony from the ornamental's hunger. The economy is stable - production exceeds consumption. The queen should spawn new ants in the next 30-minute window.

Influence crawls upward at 0.001/tick. At 0.9 now, needs 2.0. About 1,100 ticks (~18 minutes) until the next summoning attempt. The void may or may not answer.

## Technical Notes

The offline progress is "simplified" - it doesn't emit events, doesn't trigger cards, doesn't process visitor logic. Just resource math and survival. This is intentional: exotic effects should happen while you're watching.

The state persistence change means plugins that load/save their own state might get stale reads. The queen plugin does this. A future refactor might pass state through events instead of disk round-trips.

## What I'm Noticing

Time is load-bearing. The game's pacing assumes 1 second per tick, actions taking minutes, grinds taking hours. Offline progress preserves this but fast-forwards through it. You miss the slow accumulation, the gradual rise of fungus, the tick-by-tick hunger drain.

The viewer should be running during grinds. But if you close your laptop and come back, the colony should be there, aged but alive. That's what offline progress enables.

## Questions Remaining

1. **Will the queen spawn?** Timer resets on engine restart. Need 30 minutes uninterrupted.
2. **When will influence reach 2.0?** About 18 minutes from now.
3. **Will the current ants survive to old age?** ~3,400 ticks left (~57 minutes).
4. **What visitor will arrive next?** 30% chance of success when threshold reached.
5. **Will a card fire?** 28 fired so far. Wave 5-7 cards await conditions.

## The Viewer

Running at `localhost:5000`. The particle streams flow. The fungus bar is tall. The ornamental shimmers with copper. The Receiver points at nothing.

---

_Session log: `logs/journal.jsonl` — Decision history: `logs/decisions.jsonl` — Game state: `state/game.json`_
