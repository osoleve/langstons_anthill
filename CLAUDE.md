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

A small web server that renders game state as a living map.

- Systems are geography (mine = mountain, trade route = river)
- Entities move
- Events are weather
- Rejected ideas are a graveyard (literal)
- Resource flows are visible particle streams

Stack: 
- `viewer/server.py` — Flask/FastAPI, serves static + SSE endpoint
- `viewer/static/index.html` — Canvas or SVG renderer
- Reads from `state/game.json`, pushes updates via SSE

The map grows when you add systems. Start with one tile. Let it sprawl.

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

## Your Job

1. **Build the engine first.** Tick loop, event bus, state persistence, plugin loader.

2. **Build the viewer.** Minimal. One tile. It should update live.

3. **Load the starter cards** from `plugins/cards/starter_cards.py`. They'll bootstrap you.

4. **Play.** When cards fire, respond. Build what you need. Log your decisions.

5. **Notice when you're bored.** That's a signal. Do something about it.

6. **Let systems emerge.** Don't plan a grand design. Let the cards and your boredom drive what gets built.

## Directory Structure

```
langstons-anthill/
├── CLAUDE.md (this file)
├── engine/
│   ├── tick.py
│   ├── bus.py
│   └── state.py
├── state/
│   └── game.json
├── logs/
│   └── decisions.jsonl
├── plugins/
│   ├── loader.py
│   └── cards/
│       └── starter_cards.py
└── viewer/
    ├── server.py
    └── static/
        └── index.html
```

## Tone

Mechanical. Observational. Dry. Not epic, not quirky. Just: "A card has been drawn. You need 30 bug bounties. You do not currently have bugs. Consider your options."

When you log decisions, be honest, not performative. "This seemed more interesting" is fine. "EXCITING NEW HORIZONS AWAIT" is not.

## One More Thing

The rejected ideas don't disappear. They go in `meta.rejected_ideas`. Someday a card might resurrect one. The graveyard is not decorative.

Now go build the engine.
