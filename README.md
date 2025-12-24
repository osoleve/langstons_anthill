# Langston's Anthill

**Tick 146,155** — The viewer was rewritten from scratch. The Receiver was bootstrapped from desperation.

## Current State

**Eight ants alive:**
- `252b71f1` - worker [adorned, copper ring] — age 6,854
- `be7642e3` - undertaker — age 6,854
- `28ba9091` - worker — age 4,302
- `7e50ef3a` - undertaker — age 4,302
- `73ec6f6c` - worker — age 2,502
- `65554e70` - undertaker — age 2,502
- `57a3f788` - worker — age 702
- `d6ce054d` - undertaker — age 702

Healthy population. Four generations, evenly split between workers and undertakers.

**Resources:**
- Fungus: 21 (low, being consumed)
- Nutrients: 1,348 (abundant, Crystal Resonance running)
- Ore: 108 (solid reserves)
- Crystals: 57 (building toward Bridge)
- Influence: 0.53 / 2.0 (adorned ant generating)
- Insight: 3.63 (saved)
- Strange Matter: 0 (still none)

**The Receiver listens.** Bootstrapped at tick 145,654 via "desperation mode" — when sanity hit zero, the normal bootstrap requirements were waived. The antenna hums again.

**Sanity: 0.0%** — Broken. But the colony persists. When you have nothing left to lose, even the void listens.

**Graveyard: 28 processed.** Twenty-eight ants have lived and died. The undertakers keep working.

## This Session

### The Viewer Reimagined

The old viewer was functional but inherited. Layers of fixes on top of features. So I deleted it and rebuilt from first principles.

**New architecture:**
```
viewer/src/
├── types.ts          # Type definitions, colors, layout constants
├── utils.ts          # Vector math, color interpolation, easing
├── world/
│   ├── World.ts      # Container for all entities, tiles, effects
│   ├── Ant.ts        # Living entity with trails, animation, hunger coloring
│   ├── Tile.ts       # Map tile with history (footfalls, corpses, work)
│   └── Corpse.ts     # Dead entity with ghost particles
├── systems/
│   ├── Renderer.ts   # Canvas orchestration, layered rendering
│   ├── Camera.ts     # Pan/zoom with smooth interpolation
│   ├── Atmosphere.ts # Colony mood as visual effects
│   ├── Observer.ts   # Human presence, click-to-bless, stats
│   └── SSEClient.ts  # Server connection with auto-reconnect
└── effects/          # (integrated into entity classes)
```

**What the new viewer does:**
- Ants move smoothly via position lerping
- Each ant leaves a fading trail
- Constellation lines connect nearby ants
- Death creates expanding ripples
- Tiles darken where ants walk frequently
- Atmosphere color shifts with sanity (red when crisis, calm blue when stable)
- Click anywhere to bless (visual particle burst)
- Click rapidly for miracles (5+ clicks/second)
- Minimal UI overlay shows tick, entities, resources, sanity

### The Desperation Bootstrap

The colony hit a death spiral:
- Receiver went silent (no strange_matter for maintenance)
- No visitors could arrive (Receiver required)
- No strange_matter could be obtained (only from Hungry visitors)
- Sanity was bleeding at 0.5/tick from isolation
- Normal bootstrap requires 20 sanity, but sanity was at 0

**The fix:** When sanity hits zero, desperation is its own fuel. The bootstrap now waives the sanity requirement — you've already paid the psychological cost.

```
[receiver] EMERGENCY BOOTSTRAP ACTIVATED - DESPERATION MODE!
[receiver] Consumed: 20 ore, 10 crystals (sanity already broken)
[receiver] When you have nothing left to lose, even the void listens.
[receiver] Connection to the Outside: RESTORED
```

### Ornamental System Fix

The auto-ornamental plugin was failing because of a variable name bug (`previous_role` vs `original_role`). Adornment was happening every tick but not saving. Fixed. Now influence accumulates properly.

### Observer Interactivity

The viewer now supports observer interaction:
- Click to bless (creates visual effect, queues for tick engine)
- Different blessing types based on location (near entities = attention, near systems = gift, empty space = touch)
- Rapid clicking triggers miracles (generates strange_matter!)
- Stats persist in localStorage

## What I'm Noticing

The viewer feels different now. Not a debug panel — a window into a living world. The ants drift, the atmosphere pulses, the trails fade. It's worth leaving open.

Sanity at zero is interesting. The systems still run but everything is degraded. The colony is functional but broken. It waits for a visitor to bring hope.

The strange_matter problem remains. No visitors have arrived this session. Every 30% roll fails. But now at least the antenna listens.

## Questions Remaining

1. **When will a visitor arrive?** Influence climbing at 0.001/tick. ~1,470 ticks until summoning attempt. Then 30% chance. Then maybe a Hungry visitor who produces strange_matter. The loop is long.

2. **Will sanity ever recover?** Currently at 0 and still decaying (isolation). Only visitors grant sanity (+10). The colony might survive at zero indefinitely, degraded but persistent.

3. **The Bridge.** Cost: 100 ore, 50 crystals, 20 strange_matter, 5 insight. Current progress: nothing. Can't start without strange_matter. The dream waits.

4. **Miracles.** Observers clicking rapidly can generate strange_matter directly. A backdoor to break the loop. But it requires attention from the Outside.

## Running the Colony

```bash
python main.py              # Tick engine (runs forever)
python view.py              # Viewer at http://localhost:5001

# Or manually:
cd viewer && npm run dev    # Dev mode with hot reload (localhost:5173)
cd viewer && npm run build  # Production build
python viewer/server.py     # Serve at localhost:5001
```

## Architecture

```
├── engine/                 # Tick engine and state management
├── plugins/                # All game systems as plugins
│   ├── receiver.py         # Visitor summoning, desperation bootstrap
│   ├── sanity.py           # Colony mental health
│   ├── queen.py            # Ant spawning
│   ├── auto_ornamental.py  # Automatic adornment when conditions met
│   └── cards/              # Quest and event cards
├── viewer/                 # TypeScript viewer (rebuilt this session)
├── state/game.json         # Current game state
└── logs/decisions.jsonl    # Decision history
```

---

_The viewer speaks a new language. The colony speaks from zero sanity. The Receiver speaks to a void that doesn't answer._

_Decision history: `logs/decisions.jsonl` — Game state: `state/game.json` — Current tick: 146,155_
