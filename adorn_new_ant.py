#!/usr/bin/env python3
"""One-off script to craft jewelry and adorn an ant."""

import json
import sys

def load_state():
    with open("state/game.json") as f:
        return json.load(f)

def save_state(state):
    with open("state/game.json", "w") as f:
        json.dump(state, f, indent=2)

def craft_copper_ring(state):
    """Craft a copper ring, consuming 5 ore."""
    if state["resources"].get("ore", 0) < 5:
        print("Not enough ore")
        return state

    state["resources"]["ore"] -= 5

    if "jewelry" not in state.get("meta", {}):
        state["meta"]["jewelry"] = []

    state["meta"]["jewelry"].append({
        "type": "copper_ring",
        "name": "Copper Ring",
        "created_tick": state["tick"],
        "worn_by": None
    })

    print(f"[craft] created copper ring (ore remaining: {state['resources']['ore']})")
    return state

def adorn_ant(state, entity_id, jewelry_index):
    """Adorn an ant with jewelry."""
    jewelry_list = state["meta"].get("jewelry", [])

    if jewelry_index >= len(jewelry_list):
        print(f"No jewelry at index {jewelry_index}")
        return state

    jewelry = jewelry_list[jewelry_index]
    if jewelry.get("worn_by") is not None:
        print(f"Jewelry already worn by {jewelry['worn_by']}")
        return state

    # Find entity
    entity = None
    for e in state["entities"]:
        if e["id"] == entity_id:
            entity = e
            break

    if entity is None:
        print(f"Entity {entity_id} not found")
        return state

    if entity.get("adorned"):
        print(f"Entity already adorned")
        return state

    # Transform
    previous_role = entity.get("role", "worker")
    entity["adorned"] = True
    entity["ornament"] = jewelry["type"]
    entity["previous_role"] = previous_role
    entity["role"] = "ornamental"
    entity["hunger_rate"] = entity.get("hunger_rate", 0.1) * 3  # ADORNMENT_HUNGER_MULTIPLIER
    entity["influence_rate"] = 0.001  # copper_ring influence rate

    # Mark jewelry as worn
    jewelry["worn_by"] = entity_id
    jewelry["worn_tick"] = state["tick"]

    print(f"[adorn] {entity_id} is now ornamental, wearing {jewelry['name']}")
    return state

if __name__ == "__main__":
    state = load_state()

    # Show current entities
    print(f"\nTick {state['tick']}")
    print(f"Ore: {state['resources']['ore']}")
    print("\nEntities:")
    for e in state["entities"]:
        print(f"  {e['id']} - {e['role']} (age {e['age']})")

    # Craft new ring
    state = craft_copper_ring(state)

    # Find a worker to adorn
    worker = None
    for e in state["entities"]:
        if e.get("role") == "worker" and not e.get("adorned"):
            worker = e
            break

    if worker is None:
        print("No worker found to adorn")
        sys.exit(1)

    # Find the new ring (last one with worn_by=None)
    jewelry_index = None
    for i, j in enumerate(state["meta"]["jewelry"]):
        if j.get("worn_by") is None:
            jewelry_index = i

    if jewelry_index is None:
        print("No unworn jewelry found")
        sys.exit(1)

    # Adorn
    state = adorn_ant(state, worker["id"], jewelry_index)

    # Save
    save_state(state)
    print("\nState saved. The colony now has an ornamental.")
    print("Influence generation will resume.")
