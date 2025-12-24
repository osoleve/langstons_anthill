"""The Queen's Chamber. Reproduction and colony continuity.

A queen ant produces new workers and undertakers periodically,
consuming nutrients and fungus. Without a queen, the colony dies.
"""

import uuid

PLUGIN_ID = "queen"

# Constants
SPAWN_INTERVAL_TICKS = 1800  # 30 minutes between spawns
SPAWN_COST_NUTRIENTS = 10
SPAWN_COST_FUNGUS = 10
MIN_RESOURCES_TO_SPAWN = 15  # Safety buffer

_bus = None
_last_spawn_tick = 0


def spawn_ant(state: dict, role: str) -> dict:
    """Create a new ant entity."""
    ant_id = str(uuid.uuid4())[:8]

    ant = {
        "id": ant_id,
        "type": "ant",
        "role": role,
        "tile": "origin",  # Spawn at origin
        "age": 0,
        "hunger": 100,
        "hunger_rate": 0.15 if role == "undertaker" else 0.1,
        "max_age": 7200,
        "food": "fungus"
    }

    if role == "undertaker":
        ant["processing_corpse"] = False
        ant["processing_ticks"] = 0

    state["entities"].append(ant)
    print(f"[queen] spawned {role} {ant_id} at origin")

    return state


def check_queen_spawning(state: dict) -> dict:
    """Check if it's time to spawn new ants."""
    global _last_spawn_tick

    # Don't spawn if queen chamber doesn't exist
    if "queen_chamber" not in state["systems"]:
        return state

    tick = state["tick"]
    nutrients = state["resources"].get("nutrients", 0)
    fungus = state["resources"].get("fungus", 0)

    # Count only ants, not visitors
    ant_count = len([e for e in state.get("entities", []) if e.get("type") == "ant"])

    # Emergency spawn if no ants alive and has resources
    if ant_count == 0 and nutrients >= MIN_RESOURCES_TO_SPAWN and fungus >= MIN_RESOURCES_TO_SPAWN:
        print(f"[queen] EMERGENCY SPAWN - colony is empty")
        _last_spawn_tick = tick  # Set after emergency spawn
        # Fall through to spawn logic below
    else:
        # Check if enough time has passed
        if _last_spawn_tick == 0:
            _last_spawn_tick = tick  # Initialize on first run
            return state

        ticks_since_spawn = tick - _last_spawn_tick

        if ticks_since_spawn < SPAWN_INTERVAL_TICKS:
            return state

        # Check if enough resources
        if nutrients < MIN_RESOURCES_TO_SPAWN or fungus < MIN_RESOURCES_TO_SPAWN:
            print(f"[queen] insufficient resources to spawn (need {MIN_RESOURCES_TO_SPAWN} nutrients and fungus)")
            return state

    # Spawn new ants
    state = spawn_ant(state, "worker")
    state = spawn_ant(state, "undertaker")

    # Consume resources
    state["resources"]["nutrients"] -= SPAWN_COST_NUTRIENTS
    state["resources"]["fungus"] -= SPAWN_COST_FUNGUS

    _last_spawn_tick = tick

    print(f"[queen] spawned worker and undertaker, consumed {SPAWN_COST_NUTRIENTS} nutrients and {SPAWN_COST_FUNGUS} fungus")

    _bus.emit("ants_spawned", {
        "tick": tick,
        "count": 2,
        "nutrients_consumed": SPAWN_COST_NUTRIENTS,
        "fungus_consumed": SPAWN_COST_FUNGUS
    })

    return state


def on_tick(payload: dict):
    """Main tick handler for queen system."""
    from engine.state import load_state, save_state

    state = load_state()
    state = check_queen_spawning(state)
    save_state(state)


def register(bus, state):
    """Register handlers."""
    global _bus
    _bus = bus
    bus.register("tick", on_tick, PLUGIN_ID)
    print("[queen] The Queen's Chamber is ready")


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
