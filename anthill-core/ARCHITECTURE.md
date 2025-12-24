# Anthill Core Architecture

The Rust core of Langston's Anthill. Immutable, deterministic, embeddable.

## Design Principles

1. **Determinism above all.** Same seed + same inputs = same outputs. Every time.
2. **Data-oriented.** Entities are rows in a table, not objects with methods.
3. **Events as interface.** The core outputs events; it never prints, logs, or decides.
4. **No I/O.** Pure computation. All I/O happens in the calling layer.
5. **Minimal dependencies.** serde, rand_chacha, thiserror. Nothing more.

## What's In The Core

Everything that must be deterministic and immutable during a session:

| Component | Description |
|-----------|-------------|
| **State types** | Entities, resources, tiles, systems, graveyard |
| **Tick engine** | Deterministic state transitions |
| **Event emission** | All state changes reported as typed events |
| **Seeded RNG** | Reproducible randomness via ChaCha8 |
| **Serialization** | JSON-compatible state persistence |

## What Stays Outside

Everything that involves I/O, decisions, or session-specific behavior:

| Component | Why Outside |
|-----------|-------------|
| File I/O | The core doesn't touch disk |
| Event bus / handlers | Plugin logic is session-mutable |
| Card system | Prompts and decisions are observer-layer |
| Reflection / boredom detection | "What's interesting" is subjective |
| Viewer / visualization | I/O |
| Python glue | FFI layer, not core logic |

## Module Structure

```
anthill-core/
├── Cargo.toml
├── ARCHITECTURE.md        # This file
├── src/
│   ├── lib.rs             # Public API re-exports
│   ├── engine.rs          # Tick engine (the heart)
│   ├── events.rs          # Event types
│   ├── rng.rs             # Seeded RNG wrapper
│   └── types/
│       ├── mod.rs
│       ├── state.rs       # GameState (the world)
│       ├── entity.rs      # Ants, visitors
│       ├── resource.rs    # Resource management
│       ├── tile.rs        # Map tiles
│       ├── system.rs      # Production systems
│       ├── graveyard.rs   # Corpse tracking
│       └── action.rs      # Action queue
└── tests/
    ├── determinism.rs     # Reproducibility tests
    └── compatibility.rs   # JSON compatibility tests
```

## The Tick Engine

The engine processes one tick at a time, returning events:

```rust
let mut engine = TickEngine::new(seed);
let events = engine.tick(&mut state);
```

### Tick Phases (in order)

1. **Action queue** - Decrement timers, complete actions, apply effects
2. **Systems** - Resource generation/consumption from buildings
3. **Entities** - Aging, hunger, eating, death
4. **Undertakers** - Corpse collection and processing
5. **Blight** - Contamination rolls, blight spread/clear
6. **Queen** - Spawning new ants (if resources permit)
7. **Receiver** - Maintenance, summoning attempts
8. **Visitors** - Passive generation, transformation
9. **Thresholds** - Resource milestone checks
10. **Boredom** - Staleness tracking

Each phase emits events but never reads from external sources.

## State Structure

```rust
pub struct GameState {
    pub tick: u64,              // Current tick number
    pub resources: Resources,    // All colony resources
    pub systems: HashMap<String, System>,  // Production buildings
    pub entities: Vec<Entity>,   // Living beings
    pub map: GameMap,           // Tiles and connections
    pub queues: Queues,         // Pending actions/events
    pub meta: Meta,             // Boredom, sanity, goals
    pub graveyard: Graveyard,   // The dead
}
```

## Events

All state changes emit typed events:

```rust
pub enum EventKind {
    EntityDied { entity_id, cause, tile },
    EntityAte { entity_id, food, hunger_after },
    ThresholdCrossed { resource, threshold },
    AntsSpawned { worker_id, undertaker_id },
    VisitorArrived { visitor_id, visitor_type, name },
    BlightStruck { tile, contamination },
    // ... 20+ event types
}
```

The calling layer (Python, future Picotron) interprets these events.

## Determinism

Reproducibility is enforced by:

1. **Seeded RNG** - ChaCha8 with per-tick seeding
2. **No external I/O** - State in, events out
3. **Ordered processing** - Same phases, same order, every tick
4. **Comprehensive tests** - Determinism tests run identical simulations

```rust
let mut engine = TickEngine::new(seed);
// Same seed always produces same results
```

## Usage from Python (Future)

The core is designed for PyO3 bindings:

```python
import anthill_core

state = anthill_core.GameState.from_json(json_str)
engine = anthill_core.TickEngine(seed=42)

events = engine.tick(state)
for event in events:
    print(f"[{event.tick}] {event.kind}")
```

Build with maturin:
```bash
maturin develop
```

## Constants

All magic numbers live in `engine::constants`:

```rust
// Entity lifecycle
DEFAULT_MAX_AGE: 7200          // 2 hours
HUNGER_THRESHOLD_EAT: 50.0
HUNGER_GAIN_FROM_EATING: 30.0

// Queen spawning
SPAWN_INTERVAL_TICKS: 1800     // 30 minutes
SPAWN_COST_NUTRIENTS: 10.0
SPAWN_COST_FUNGUS: 10.0

// Undertaker
CORPSE_PROCESSING_TICKS: 120
CONTAMINATION_PER_CORPSE: 0.01
BLIGHT_DURATION: 300

// Receiver
SUMMON_COST: 2.0
SUMMON_COOLDOWN: 600           // 10 minutes
SUMMON_CHANCE: 0.3             // 30%
```

## Testing

```bash
cargo test              # All tests
cargo test determinism  # Reproducibility tests
cargo test compatibility # JSON loading tests
```

The determinism tests verify:
- Same seed → same events
- Same seed → same final state
- Different seeds → different outcomes
- Entity lifecycle is reproducible
- Visitor summoning is reproducible

## Future Work

- [ ] PyO3 bindings via maturin
    - [ ] Add `pyo3` dependency and configuration to `Cargo.toml`
    - [ ] Implement `From<GameState>` for Python dict conversion
    - [ ] Expose `TickEngine.tick()` as a Python-callable function
- [ ] C FFI for other languages
- [ ] Benchmark suite
- [ ] Offline progress simulation
- [ ] State migration between versions

---

*The core is frozen during a session. Changes require recompilation. This is a feature.*
