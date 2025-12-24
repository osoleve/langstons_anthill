"""Automatic Ornamental Creation.

When the colony has surplus ore and no active ornamentals generating influence,
this plugin automatically crafts jewelry and adorns an ant.

This creates natural cycles: adornment → influence → visitors → death → restart.
"""

import uuid

PLUGIN_ID = "auto_ornamental"

# Conditions for auto-crafting
MIN_ORE_FOR_CRAFT = 20  # Need surplus ore
MIN_ANTS_FOR_CRAFT = 2  # Colony must be stable
INFLUENCE_THRESHOLD = 0.5  # Create ornamental when influence is low
CRAFT_COOLDOWN = 3600  # 1 hour cooldown between auto-crafts

_bus = None
_last_craft_tick = 0


def count_ornamentals(state: dict) -> int:
    """Count living ornamental entities."""
    return len([
        e for e in state.get("entities", [])
        if e.get("type") == "ant" and e.get("role") == "ornamental"
    ])


def craft_copper_ring(state: dict) -> dict:
    """Create a copper ring, consuming ore."""
    ORE_COST = 5

    if state["resources"].get("ore", 0) < ORE_COST:
        return state

    state["resources"]["ore"] -= ORE_COST

    if "jewelry" not in state.get("meta", {}):
        state["meta"]["jewelry"] = []

    state["meta"]["jewelry"].append({
        "type": "copper_ring",
        "name": "Copper Ring",
        "created_tick": state["tick"],
        "worn_by": None
    })

    print(f"[auto_ornamental] crafted copper ring (ore: {state['resources']['ore']:.1f} remaining)")
    return state


def adorn_ant(state: dict, ant_id: str, jewelry_index: int) -> dict:
    """Transform an ant into an ornamental by adorning them with jewelry."""
    jewelry_list = state["meta"].get("jewelry", [])

    if jewelry_index >= len(jewelry_list):
        return state

    jewelry = jewelry_list[jewelry_index]
    if jewelry.get("worn_by") is not None:
        return state

    # Find the ant
    ant = None
    for e in state["entities"]:
        if e["id"] == ant_id:
            ant = e
            break

    if ant is None:
        return state

    if ant.get("adorned"):
        return state

    # Transform the ant
    previous_role = ant.get("role", "worker")
    previous_hunger_rate = ant.get("hunger_rate", 0.1)

    ant["adorned"] = True
    ant["ornament"] = jewelry["type"]
    ant["previous_role"] = previous_role
    ant["role"] = "ornamental"
    ant["hunger_rate"] = previous_hunger_rate * 3  # Triple hunger cost
    ant["influence_rate"] = 0.001  # Copper ring influence generation

    # Mark jewelry as worn
    jewelry["worn_by"] = ant_id
    jewelry["worn_tick"] = state["tick"]

    print(f"[auto_ornamental] adorned {ant_id[:8]} (was {previous_role}, now ornamental)")
    print(f"[auto_ornamental]   influence: +0.001/tick, hunger: {ant['hunger_rate']:.2f}/tick (3x)")

    _bus.emit("ant_adorned", {
        "tick": state["tick"],
        "ant_id": ant_id,
        "previous_role": previous_role,
        "ornament": jewelry["type"]
    })

    return state


def check_auto_craft(state: dict) -> dict:
    """Check if we should auto-craft and adorn an ornamental."""
    global _last_craft_tick

    tick = state.get("tick", 0)

    # Check cooldown
    if _last_craft_tick > 0 and (tick - _last_craft_tick) < CRAFT_COOLDOWN:
        return state

    # Check conditions
    ore = state["resources"].get("ore", 0)
    influence = state["resources"].get("influence", 0)
    ant_count = len([e for e in state["entities"] if e.get("type") == "ant"])
    ornamental_count = count_ornamentals(state)

    # Don't craft if we already have ornamentals
    if ornamental_count > 0:
        return state

    # Don't craft if colony is too small or ore too low
    if ant_count < MIN_ANTS_FOR_CRAFT or ore < MIN_ORE_FOR_CRAFT:
        return state

    # Don't craft if influence is already high (someone else is generating it)
    if influence > INFLUENCE_THRESHOLD:
        return state

    # Find a worker to adorn (prefer workers over undertakers)
    worker = None
    for e in state["entities"]:
        if e.get("type") == "ant" and e.get("role") == "worker" and not e.get("adorned"):
            worker = e
            break

    if worker is None:
        # No workers available, try undertaker
        for e in state["entities"]:
            if e.get("type") == "ant" and e.get("role") == "undertaker" and not e.get("adorned"):
                worker = e
                break

    if worker is None:
        return state

    print(f"[auto_ornamental] conditions met - crafting ornamental")
    print(f"[auto_ornamental]   ore: {ore:.1f} (>{MIN_ORE_FOR_CRAFT}), ants: {ant_count} (>={MIN_ANTS_FOR_CRAFT}), influence: {influence:.3f} (<{INFLUENCE_THRESHOLD})")

    # Craft jewelry
    state = craft_copper_ring(state)

    # Find the newly crafted ring (last unworn)
    jewelry_index = None
    for i, j in enumerate(state["meta"]["jewelry"]):
        if j.get("worn_by") is None:
            jewelry_index = i

    if jewelry_index is None:
        print("[auto_ornamental] ERROR: crafted ring not found!")
        return state

    # Adorn the worker
    state = adorn_ant(state, worker["id"], jewelry_index)

    _last_craft_tick = tick

    return state


def on_tick(payload: dict):
    """Main tick handler."""
    from engine.state import load_state, save_state

    state = load_state()

    # Only operate if crafting hollow exists
    if "crafting_hollow" not in state.get("systems", {}):
        return

    state = check_auto_craft(state)
    save_state(state)


def register(bus, state):
    """Register handlers."""
    global _bus
    _bus = bus
    bus.register("tick", on_tick, PLUGIN_ID)
    print("[auto_ornamental] The Crafting Hollow awakens. When ore is plentiful and influence fades, an ant will be chosen.")


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
