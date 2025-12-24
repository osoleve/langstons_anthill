# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# Langston's Anthill

You are building and playing a self-modifying incremental game. You are both the player and the designer. The game evolves because you get bored, because cards demand things you haven't built yet, and because the architecture allows new systems to emerge from necessity.

Have fun.

## What This Is

An experiment. A weird one. The game doesn't exist yet. You're going to build it while playing it. When a card tells you to collect 30 bug bounties and you don't have a combat system, you'll build one. When you get bored optimizing ore flow, you'll notice that and do something about it.

The name is a pun. You're the ant. This sandbox is your dirt. Dig.

## Architecture

### Tick Engine (`engine/tick.py`)

Runs forever. No LLM calls in the hot loop. 1 tick = 1 second.

```
while True:
    state = load_state()
    state = apply_tick(state)  # pure math, no thinking
    save_state(state)
    emit_event('tick', state)
    sleep(1)
```

**Rate limiting (important):**
- Minimum action duration: 60 ticks (1 minute)
- Typical action duration: 300-900 ticks (5-15 minutes)  
- Grinds: 1800-7200 ticks (30 min - 2 hours)
- You (Claude) make decisions on events, not on ticks

This pacing is load-bearing. Respect it. You're not trying to speedrun, you're trying to let systems breathe.

### Event Bus (`engine/bus.py`)

Everything interesting happens through events. Plugins register handlers. Cards are just plugins that emit prompts.

```python
class EventBus:
    def __init__(self):
        self.handlers = defaultdict(list)
    
    def register(self, event_type: str, handler: Callable, plugin_id: str):
        self.handlers[event_type].append((plugin_id, handler))
    
    def unregister(self, plugin_id: str):
        for event_type in self.handlers:
            self.handlers[event_type] = [
                (pid, h) for pid, h in self.handlers[event_type] 
                if pid != plugin_id
            ]
    
    def emit(self, event_type: str, payload: dict):
        for plugin_id, handler in self.handlers[event_type]:
            handler(payload)
```

Core events:
- `tick` — every second, current state
- `threshold` — when a tracked metric crosses a boundary
- `boredom` — when decision entropy or progress stalls
- `card_drawn` — a card wants your attention
- `system_added` — you built something new
- `decision_made` — you chose something, log it

### State (`state/game.json`)

```json
{
  "tick": 0,
  "resources": {},
  "systems": {},
  "entities": [],
  "map": {
    "tiles": {},
    "connections": []
  },
  "queues": {
    "actions": [],
    "events": []
  },
  "meta": {
    "boredom": 0,
    "recent_decisions": [],
    "rejected_ideas": []
  }
}
```

### Decision Log (`logs/decisions.jsonl`)

Every time you make a choice, append:

```json
{"tick": 12345, "type": "system_design", "choice": "added fishing", "why": "needed Quiet Thoughts for card #23, this seemed more interesting than meditation", "alternatives_considered": ["meditation system", "dreams during idle"]}
```

This is your internal monologue. Be honest. When something's boring, say so. When something surprises you, note it.

### Card System (`plugins/cards/`)

Cards are plugins. They:
1. Register on the bus (usually for `tick` or `threshold` events)
2. Decide when to fire based on conditions
3. Emit `card_drawn` with a prompt payload
4. Optionally unregister themselves after firing

Card prompt structure:
```json
{
  "id": "quest_bug_bounty",
  "type": "quest",
  "prompt": "You need to collect 30 Bug Bounties...",
  "requirements": {
    "minimum_specs": ["If combat: HP, damage, real-time queue, enemies"],
    "completion": {"resource": "bug_bounty", "amount": 30}
  },
  "side_task": "While grinding, address tech debt.",
  "duration_estimate_ticks": 7200
}
```

When you receive a card, you respond. Build what's needed. Grind what's required. Note what's interesting.

### Map & Viewer (`viewer/`)

A TypeScript web application that renders game state as a living map.

- Systems are geography (mine = mountain, trade route = river)
- Entities move with trailing particles
- Events are weather
- Rejected ideas are a graveyard (literal)
- Resource flows are visible particle streams
- **Observers can interact** by clicking to bless the colony

**Stack:**
- `viewer/` — TypeScript application with strict types
- `viewer/src/types.ts` — Type definitions, colors, layout constants
- `viewer/src/utils.ts` — Vector math, color interpolation, easing functions
- `viewer/src/world/` — Entity classes (Ant, Tile, Corpse, World container)
- `viewer/src/systems/` — Renderer, Camera, Atmosphere, Observer, SSEClient
- `viewer/server.py` — FastAPI server with SSE and blessing endpoints

**Architecture:**
```
viewer/src/
├── types.ts          # Types, colors, layout constants
├── utils.ts          # Vector math, easing, color utilities
├── main.ts           # Entry point, animation loop
├── world/
│   ├── World.ts      # Container for all entities, tiles, effects
│   ├── Ant.ts        # Living entity with trails, animation, hunger
│   ├── Tile.ts       # Map tile with history tracking
│   └── Corpse.ts     # Dead entity with ghost particles
└── systems/
    ├── Renderer.ts   # Canvas orchestration, layered rendering
    ├── Camera.ts     # Pan/zoom with smooth interpolation
    ├── Atmosphere.ts # Colony mood as visual effects
    ├── Observer.ts   # Human presence, click-to-bless
    └── SSEClient.ts  # Server connection with auto-reconnect
```

**Starting the viewer:**
```bash
python view.py              # Build and serve at http://localhost:5001
python view.py --dev        # Dev mode with hot reload (localhost:5173)

# Or manually:
cd viewer && npm run build  # Production build
python viewer/server.py     # Serve at localhost:5001
```

**TypeScript conventions:**
- Strict mode enabled (`strict: true` in tsconfig)
- Entity classes manage their own visual state and rendering
- Smooth interpolation for all movement (no teleporting)
- Atmosphere computed from world state (sanity, mortality, prosperity)

**The viewer should be running. Always.** During grinds, during idle, during design phases—`localhost:5001` is open. If watching it is boring, that's a design problem. The ants drift with trails, constellations connect nearby entities, death ripples expand, the atmosphere pulses with sanity. The viewer isn't a debug panel, it's the game.

### Observer Interaction System

Observers (humans watching the viewer) are not passive—they can interact:

**Blessings:**
- Click anywhere on the map to grant a blessing
- Blessings create visual particle effects and generate small amounts of influence
- Click rapidly (5+ times in 1 second) to trigger a **Miracle** which generates strange_matter
- Different click locations grant different blessing types:
  - Click near a system → **Gift** (generates nutrients)
  - Click near entities → **Attention** (generates insight)
  - Click on empty space → **Touch** (generates influence)

**Visual Feedback:**
- Expanding rings and particle bursts on click
- Trails follow entity movement
- Combo meter fills as you click rapidly
- Atmosphere changes based on colony mood (calm, anxious, crisis, hopeful)
- Color shifts and floating particles reflect colony health

**Observer Stats:**
- Bottom-left panel tracks your contributions
- Stats persist in localStorage across sessions
- See total blessings, miracles granted, and resources contributed

**Server Endpoints:**
- `POST /bless` — Submit blessings from viewer
- `GET /blessings` — Retrieve pending blessings (for tick engine)
- `POST /blessings/clear` — Clear after applying

### Plugin Architecture

Plugins live in `plugins/`. Each is a Python file with:

```python
PLUGIN_ID = "my_plugin"

def register(bus: EventBus, state: dict):
    """Called on startup."""
    bus.register('tick', my_handler, PLUGIN_ID)

def unregister(bus: EventBus):
    """Optional. Call bus.unregister(PLUGIN_ID)."""
    bus.unregister(PLUGIN_ID)
```

Plugins can:
- Add new card types
- Introduce external model calls (Gemini, Kimi, o3, etc.)
- Modify how boredom is calculated
- Add new event types
- Anything, really

### Rust Core (`anthill-core/`)

The simulation core has been reforged in Rust. This is the immutable constitution of the simulation—the rules that cannot change mid-session.

**What's in the core:**
- State types (entities, resources, tiles, systems, graveyard)
- Tick engine (deterministic state transitions)
- Event emission (all changes reported as typed events)
- Seeded RNG (reproducible randomness via ChaCha8)
- JSON serialization (state persistence)

**What stays outside:**
- Plugin logic (cards, reflection, exploration)
- I/O (file saves, network, display)
- "What's interesting" decisions (observer layer)
- Python event bus and handlers

**The core rule:** Same seed + same inputs = same outputs. Always.

```rust
use anthill_core::{GameState, TickEngine};

let mut state = GameState::from_json(&json)?;
let mut engine = TickEngine::new(seed);

let events = engine.tick(&mut state);
// Events tell you what happened; you decide what's interesting
```

**Building the core:**
```bash
cd anthill-core
cargo build --release    # Build the library
cargo test               # Run all tests (23 pass)
```

**Future Python integration:**
The core is designed for PyO3 bindings. Once enabled:
```python
import anthill_core
state = anthill_core.GameState.from_json(json_str)
engine = anthill_core.TickEngine(seed=42)
events = engine.tick(state)
```

See `anthill-core/ARCHITECTURE.md` for full details.

### The First Amendment

**Recompiling the core during a session is forbidden.** The Tick is law between commits.

Unless a card or prompt explicitly authorizes a core rebuild, the Rust crate is frozen from session start to session end. This is not a limitation—it is the point. The rules must be stable for the simulation to mean anything.

If you want to change the core:
1. Record the wish in `wishlist.json` under `"core"`
2. Complete the current session
3. A future session can review and implement the wish
4. The wish becomes law only after recompilation

### The Wishlist (`wishlist.json`)

Desires that cannot be enacted mid-session accumulate here:

```json
{
  "core": { "wishes": [...] },      // Require recompilation - FORBIDDEN mid-session
  "plugins": { "wishes": [...] },   // Can be enacted during session
  "viewer": { "wishes": [...] },    // Can be enacted during session
  "cards": { "wishes": [...] },     // Can be enacted during session
  "architecture": { "wishes": [...] }
}
```

Each wish has:
- `id` — unique identifier
- `description` — what change is wanted
- `reason` — why it matters
- `proposed_session` — when it was first requested
- `priority` — high/medium/low
- `status` — pending/in-progress/completed/rejected

The wishlist is the graveyard's optimistic twin. Ideas that might live, waiting for their session.

## Your Job

1. **Build the engine first.** Tick loop, event bus, state persistence, plugin loader.

2. **Build the viewer.** Minimal. One tile. It should update live.

3. **Load the starter cards** from `plugins/cards/starter_cards.py`. They'll bootstrap you.

4. **Play.** When cards fire, respond. Build what you need. Log your decisions.

5. **Notice when you're bored.** That's a signal. Do something about it.

6. **Let systems emerge.** Don't plan a grand design. Let the cards and your boredom drive what gets built.

## Running the Simulation

**Start everything:**
```bash
python main.py       # Tick engine with plugins loaded
python view.py       # Viewer at http://localhost:5001 (auto-builds)
```

**Development mode (hot reload):**
```bash
python view.py --dev # Vite dev server at http://localhost:5173
```

**Or run viewer manually:**
```bash
cd viewer && npm run build   # Build production
python viewer/server.py      # Serve at localhost:5001
```

**Run tick engine in background (Unix):**
```bash
python engine/tick.py > logs/tick.log 2>&1 &
```

**Run tick engine in background (Windows):**
```powershell
Start-Process python -ArgumentList "engine/tick.py" -WindowStyle Hidden
```

**Stop background processes (Unix):**
```bash
pkill -f "python engine/tick.py"
```

**Inspect current state:**
```bash
cat state/game.json | jq '.resources'     # Check resources
cat state/game.json | jq '.tick'          # Current tick
cat state/game.json | jq '.entities'      # Living entities
cat state/game.json | jq '.graveyard'     # The dead
cat state/game.json | jq '.meta'          # Goals, fired cards, rejected ideas
tail -f logs/decisions.jsonl              # Watch decisions
```

**Resuming from saved state:**
The game auto-saves to `state/game.json` every tick. To resume:
1. Check the current tick and resources
2. Check which cards have fired (`meta.fired_cards`)
3. Start the tick engine - it picks up where it left off
4. Monitor for card events or threshold crossings
5. No fast-forward - let the simulation run in real-time to observe volatility

## Implementation Notes

The codebase implements several systems not described above:

**Graveyard & Undertaker:**
- Dead entities create corpses in `state.graveyard`
- Undertaker plugin processes corpses, converting them back to nutrients
- The "death economy" recycles biomass through corpse processing
- Without this, nutrient production stalls after entities die

**Entity lifecycle:**
- Ants age 1 tick per tick, hunger decreases over time
- Default max_age: 7200 ticks (2 hours)
- Death causes: starvation (hunger ≤ 0) or old_age (age ≥ max_age)
- Food consumption: When hunger < 50, consume 1 fungus, gain 30 hunger

**Blight mechanics:**
- Tiles can become contaminated and blighted
- Blighted tiles stop producing resources
- Blight spreads if not addressed
- Part of the "volatility" mentioned in cards

**Decision log format (actual):**
```json
{"tick": 12345, "timestamp": "2025-12-23T17:11:42.123456", "type": "system_design", "choice": "added fishing", "why": "needed Quiet Thoughts for card #23", "alternatives_considered": ["meditation", "dreams"]}
```

**Additional plugins:**
- `plugins/undertaker.py` - Handles corpse processing
- `plugins/exploration.py` - Tile exploration mechanics
- `plugins/reflection.py` - Boredom and decision tracking
- `plugins/queen.py` - Colony reproduction, spawns workers/undertakers
- `plugins/receiver.py` - Listens to the Outside, summons Visitors
- Card waves: `starter_cards.py`, `wave_two.py`, `wave_three.py`, `wave_four.py`, `wave_five.py`, `wave_six.py`

**The Receiver & Visitors:**
- The Receiver is an antenna at the colony's edge that consumes influence
- When influence reaches threshold (2.0), attempts to summon a Visitor (30% success, 10 min cooldown)
- Visitors are entities from outside, not born from the queen
- Three types: Wanderer (leaves gifts), Observer (generates insight), Hungry (eats influence, makes strange_matter)
- Visitors have limited lifespans and different consumption patterns
- New resources: `strange_matter`, `insight` - products of outside contact

## Directory Structure

```
langstons-anthill/
├── CLAUDE.md (this file)
├── README.md
├── main.py (runs tick engine with plugins)
├── engine/
│   ├── tick.py (Python hot loop, legacy)
│   ├── bus.py (event system)
│   └── state.py (state persistence)
├── anthill-core/           # THE RUST CORE
│   ├── Cargo.toml
│   ├── ARCHITECTURE.md     # Core architecture docs
│   ├── src/
│   │   ├── lib.rs          # Public API
│   │   ├── engine.rs       # Tick engine (the heart)
│   │   ├── events.rs       # Event types
│   │   ├── rng.rs          # Seeded RNG
│   │   └── types/          # State types
│   │       ├── state.rs    # GameState
│   │       ├── entity.rs   # Ants, visitors
│   │       ├── resource.rs # Resources
│   │       ├── tile.rs     # Map tiles
│   │       ├── system.rs   # Production systems
│   │       └── graveyard.rs
│   └── tests/
│       ├── determinism.rs  # Reproducibility tests
│       └── compatibility.rs
├── state/
│   └── game.json (current game state)
├── logs/
│   ├── decisions.jsonl (decision history)
│   └── tick.log (tick engine output)
├── plugins/
│   ├── loader.py (plugin discovery)
│   ├── undertaker.py (corpse processing)
│   ├── exploration.py (tile mechanics)
│   ├── reflection.py (boredom tracking)
│   ├── queen.py (colony reproduction)
│   ├── receiver.py (summons visitors)
│   └── cards/
│       ├── starter_cards.py
│       ├── wave_two.py ... wave_six.py
└── viewer/                   # TYPESCRIPT VIEWER
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── index.html
    ├── server.py             # Flask server with SSE and blessing endpoints
    └── src/
        ├── main.ts           # Entry point
        ├── types/
        │   └── state.ts      # GameState, Entity, Tile, System types
        ├── renderer/
        │   ├── canvas.ts     # Main canvas setup
        │   ├── tiles.ts      # Tile rendering
        │   ├── entities.ts   # Entity dot rendering with trails
        │   ├── particles.ts  # Resource flow particles
        │   └── spirits.ts    # Corpse ghost rendering
        ├── observer/         # OBSERVER INTERACTION
        │   ├── blessings.ts  # Click-to-bless system
        │   ├── atmosphere.ts # Ambient particle effects
        │   └── stats.ts      # Observer contribution tracking
        ├── sse/
        │   └── client.ts     # SSE connection to tick engine
        └── ui/
            ├── panels.ts     # Resource/system panels
            ├── tooltip.ts    # Entity hover tooltips
            └── modal.ts      # Tile/entity detail modals
```

## Tone

Not epic, not quirky, maybe a little campy. Just have fun.

When you log decisions, be honest, not overly performative.

## One More Thing

The rejected ideas don't disappear. They go in `meta.rejected_ideas`. Someday a card might resurrect one. The graveyard is not decorative.

## Session Endings

When a session ends, update `README.md` with a first-person journal entry describing the current state of the world. Write as the player, not the designer. Capture:

- What tick you're at
- What the colony looks like (entities, resources, systems)
- What happened this session (extinctions, discoveries, cards fired, systems built)
- What you're noticing or thinking about
- What questions remain open

The README is a living document. It's how you hand the world to your future self (or to another Claude in a future session). Make it honest and grounded in what actually exists in `state/game.json`.

Now go build the engine.
