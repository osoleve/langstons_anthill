"""Action helpers. Queue actions, apply effects."""

from .state import load_state, save_state


def queue_action(name: str, duration_ticks: int, effects: dict = None, metadata: dict = None):
    """Add an action to the queue."""
    state = load_state()

    action = {
        "name": name,
        "ticks_remaining": duration_ticks,
        "started_at_tick": state["tick"],
        "effects": effects or {},
        "metadata": metadata or {}
    }

    state["queues"]["actions"].append(action)
    save_state(state)

    print(f"[actions] queued: {name} ({duration_ticks} ticks)")
    return action


def get_active_actions():
    """Get all currently running actions."""
    state = load_state()
    return state["queues"]["actions"]


def add_resource(resource: str, amount: float):
    """Directly add a resource (for immediate effects)."""
    state = load_state()
    state["resources"][resource] = state["resources"].get(resource, 0) + amount
    save_state(state)
    print(f"[actions] +{amount} {resource}")


def add_system(system_id: str, system: dict):
    """Add a new system to the game."""
    state = load_state()
    state["systems"][system_id] = system
    save_state(state)
    print(f"[actions] added system: {system_id}")


def add_tile(tile_id: str, tile: dict, connect_to: str = None):
    """Add a tile to the map."""
    state = load_state()
    state["map"]["tiles"][tile_id] = tile
    if connect_to:
        state["map"]["connections"].append([connect_to, tile_id])
    save_state(state)
    print(f"[actions] added tile: {tile_id}")


def reject_idea(idea: str):
    """Send an idea to the graveyard."""
    state = load_state()
    if idea not in state["meta"]["rejected_ideas"]:
        state["meta"]["rejected_ideas"].append(idea)
        save_state(state)
        print(f"[actions] rejected: {idea}")
