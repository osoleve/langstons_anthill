"""Entity helpers."""

import uuid
from .state import load_state, save_state


def spawn_entity(entity_type: str, tile: str = "origin", **kwargs):
    """Spawn a new entity."""
    state = load_state()

    entity = {
        "id": str(uuid.uuid4())[:8],
        "type": entity_type,
        "tile": tile,
        "age": 0,
        "hunger": 100,
        **kwargs
    }

    state["entities"].append(entity)
    save_state(state)

    print(f"[entities] spawned: {entity_type} ({entity['id']}) at {tile}")
    return entity


def spawn_ant(tile: str = "origin", role: str = "worker"):
    """Spawn an ant. Roles: worker, undertaker."""
    # Undertakers have higher hunger rate (the work is repulsive)
    hunger_rate = 0.05 if role != "undertaker" else 0.075

    return spawn_entity(
        entity_type="ant",
        tile=tile,
        role=role,
        food="fungus",
        hunger_rate=hunger_rate,
        max_age=7200,  # 2 hours lifespan
        state="idle"
    )


def count_entities(entity_type: str = None) -> int:
    """Count entities, optionally by type."""
    state = load_state()
    if entity_type:
        return sum(1 for e in state["entities"] if e.get("type") == entity_type)
    return len(state["entities"])


def list_entities() -> list:
    """Get all entities."""
    state = load_state()
    return state["entities"]
