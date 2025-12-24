"""Ornamentation system. The cost of beauty.

When an ant is adorned, they cease to be a tool.
They consume three times their share.
They exist solely to be observed.
In exchange for their uselessness, they generate Influence.
"""

PLUGIN_ID = "ornamentation"

# Jewelry types and their costs
JEWELRY = {
    "copper_ring": {
        "name": "Copper Ring",
        "cost": {"ore": 1},
        "influence_rate": 0.001,
        "description": "A simple band of copper, wrapped around an antenna"
    },
    "gold_band": {
        "name": "Gold Band",
        "cost": {"ore": 2},
        "influence_rate": 0.002,
        "description": "A heavier ring, catching light with every movement"
    },
    "jeweled_crown": {
        "name": "Jeweled Crown",
        "cost": {"ore": 3, "crystals": 1},
        "influence_rate": 0.005,
        "description": "Crystal fragments set in metal, worn like a halo"
    }
}

# The hunger multiplier for adorned ants
ADORNMENT_HUNGER_MULTIPLIER = 3

_bus = None


def can_craft_jewelry(state: dict, jewelry_type: str) -> bool:
    """Check if the colony can afford to craft jewelry."""
    if jewelry_type not in JEWELRY:
        return False

    jewelry = JEWELRY[jewelry_type]
    for resource, amount in jewelry["cost"].items():
        if state["resources"].get(resource, 0) < amount:
            return False

    return True


def craft_jewelry(state: dict, jewelry_type: str) -> dict:
    """Craft a piece of jewelry, consuming resources."""
    if not can_craft_jewelry(state, jewelry_type):
        return state

    jewelry = JEWELRY[jewelry_type]

    # Consume resources
    for resource, amount in jewelry["cost"].items():
        state["resources"][resource] -= amount

    # Add to jewelry inventory
    if "jewelry" not in state.get("meta", {}):
        if "meta" not in state:
            state["meta"] = {}
        state["meta"]["jewelry"] = []

    state["meta"]["jewelry"].append({
        "type": jewelry_type,
        "name": jewelry["name"],
        "created_tick": state["tick"],
        "worn_by": None
    })

    print(f"[ornamentation] crafted {jewelry['name']}")
    _bus.emit("jewelry_crafted", {
        "type": jewelry_type,
        "tick": state["tick"]
    })

    return state


def adorn_ant(state: dict, entity_id: str, jewelry_index: int) -> dict:
    """Adorn an ant with a piece of jewelry. They cease to be a tool."""
    meta = state.get("meta", {})
    jewelry_list = meta.get("jewelry", [])

    if jewelry_index >= len(jewelry_list):
        print(f"[ornamentation] no jewelry at index {jewelry_index}")
        return state

    jewelry = jewelry_list[jewelry_index]
    if jewelry.get("worn_by") is not None:
        print("[ornamentation] jewelry already worn")
        return state

    # Find the entity
    entity = None
    for e in state["entities"]:
        if e["id"] == entity_id:
            entity = e
            break

    if entity is None:
        print(f"[ornamentation] entity {entity_id} not found")
        return state

    if entity.get("adorned"):
        print(f"[ornamentation] entity {entity_id} already adorned")
        return state

    # The transformation
    # Note: We keep the original role (worker/undertaker) for Rust core compatibility
    # The 'adorned' flag indicates they've become ornamental
    entity["adorned"] = True
    entity["ornament"] = jewelry["type"]
    entity["hunger_rate"] = entity.get("hunger_rate", 0.1) * ADORNMENT_HUNGER_MULTIPLIER
    entity["influence_rate"] = JEWELRY[jewelry["type"]]["influence_rate"]

    # Mark jewelry as worn
    jewelry["worn_by"] = entity_id
    jewelry["worn_tick"] = state["tick"]

    original_role = entity.get("role", "worker")
    print(f"[ornamentation] {entity_id} adorned with {jewelry['name']}")
    print(f"[ornamentation] {entity_id} was {original_role}, now adorned (generates influence)")

    _bus.emit("ant_adorned", {
        "entity_id": entity_id,
        "jewelry_type": jewelry["type"],
        "original_role": original_role,
        "tick": state["tick"]
    })

    return state


def generate_influence(state: dict) -> dict:
    """Generate influence from adorned ants. Called each tick."""
    influence_generated = 0

    for entity in state["entities"]:
        if entity.get("adorned") and entity.get("influence_rate"):
            influence_generated += entity["influence_rate"]

    if influence_generated > 0:
        state["resources"]["influence"] = state["resources"].get("influence", 0) + influence_generated

    return state


def on_tick(payload: dict):
    """Process influence generation each tick."""
    from engine.state import load_state, save_state

    state = load_state()

    # Only process if we have adorned ants
    has_adorned = any(e.get("adorned") for e in state.get("entities", []))
    if has_adorned:
        state = generate_influence(state)
        save_state(state)


def register(bus, state):
    """Register handlers."""
    global _bus
    _bus = bus
    bus.register("tick", on_tick, PLUGIN_ID)

    # Initialize influence resource if not present
    if "influence" not in state.get("resources", {}):
        state["resources"]["influence"] = 0

    print("[ornamentation] The cost of beauty awaits")


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
