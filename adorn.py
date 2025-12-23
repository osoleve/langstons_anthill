#!/usr/bin/env python3
"""Script to craft jewelry and adorn an ant."""

import sys
sys.path.insert(0, '/home/user/langstons_anthill')

from engine.state import load_state, save_state

def main():
    print("Loading state...")
    state = load_state()

    # Show current ants
    print(f"\nCurrent ants:")
    for e in state["entities"]:
        adorned = " (ADORNED)" if e.get("adorned") else ""
        print(f"  {e['id'][:8]} - {e['role']} (age: {e['age']}, hunger: {e.get('hunger', 0):.1f}){adorned}")

    # Show current resources
    print(f"\nResources:")
    print(f"  Ore: {state['resources'].get('ore', 0):.2f}")
    print(f"  Influence: {state['resources'].get('influence', 0):.10f}")

    # Manually craft a copper ring
    print(f"\nCrafting copper ring...")
    ore_cost = 1
    if state['resources'].get('ore', 0) < ore_cost:
        print("Not enough ore!")
        return

    state['resources']['ore'] -= ore_cost

    # Add to jewelry inventory
    if "jewelry" not in state.get("meta", {}):
        state["meta"]["jewelry"] = []

    state["meta"]["jewelry"].append({
        "type": "copper_ring",
        "name": "Copper Ring",
        "created_tick": state["tick"],
        "worn_by": None
    })
    print(f"  Created Copper Ring (ore: {state['resources']['ore']:.2f} remaining)")

    # Find a worker to adorn
    worker = None
    for e in state["entities"]:
        if e["role"] == "worker" and not e.get("adorned"):
            worker = e
            break

    if not worker:
        print("No unadorned worker found!")
        return

    # Find the newly crafted jewelry (last unworn)
    jewelry_index = None
    for i, j in enumerate(state["meta"]["jewelry"]):
        if j.get("worn_by") is None:
            jewelry_index = i
            break

    if jewelry_index is None:
        print("No unworn jewelry found!")
        return

    jewelry = state["meta"]["jewelry"][jewelry_index]

    # Adorn the worker
    print(f"\nAdorning {worker['id'][:8]} with {jewelry['name']}...")

    previous_role = worker.get("role", "worker")
    previous_hunger_rate = worker.get("hunger_rate", 0.1)

    worker["adorned"] = True
    worker["ornament"] = "copper_ring"
    worker["previous_role"] = previous_role
    worker["role"] = "ornamental"
    worker["hunger_rate"] = previous_hunger_rate * 3  # Triple hunger
    worker["influence_rate"] = 0.001  # Copper ring influence rate

    jewelry["worn_by"] = worker["id"]
    jewelry["worn_tick"] = state["tick"]

    print(f"  {worker['id'][:8]} ceased to be a {previous_role}")
    print(f"  Now: ornamental (hunger rate: {worker['hunger_rate']:.2f}, influence: 0.001/tick)")

    # Save state
    print(f"\nSaving state...")
    save_state(state)

    print(f"\n✓ Done! The worker is now ornamental.")
    print(f"  Influence will accumulate at 0.001/tick")
    print(f"  Food consumption: 3x (this ant will eat 3 fungus when hungry)")
    print(f"  The ore is permanently committed - if this ant dies, the ring becomes ghost jewelry")

if __name__ == "__main__":
    main()
