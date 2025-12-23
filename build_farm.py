#!/usr/bin/env python3
"""Build a second fungus farm to stabilize the colony."""

import sys
sys.path.insert(0, '/home/user/langstons_anthill')

from engine.state import load_state, save_state

def main():
    print("Loading state...")
    state = load_state()

    tick = state['tick']
    fungus_before = state['resources']['fungus']

    # Add second fungus farm system
    if "fungus_farm_2" not in state["systems"]:
        state["systems"]["fungus_farm_2"] = {
            "name": "Fungus Farm (Deep Chambers)",
            "type": "converter",
            "consumes": {"nutrients": 0.02},
            "generates": {"fungus": 0.01},
            "description": "A second cultivation chamber deep in the colony"
        }
        print("✓ Added second fungus farm")

    # Add new tile for it
    if "fungus_farm_2_tile" not in state["map"]["tiles"]:
        state["map"]["tiles"]["fungus_farm_2_tile"] = {
            "name": "Deep Chambers",
            "type": "production",
            "x": 1,
            "y": 1,
            "description": "Additional fungus cultivation deep underground"
        }
        print("✓ Added Deep Chambers tile")

    # Connect to existing fungus farm
    connection = ["fungus_farm", "fungus_farm_2_tile"]
    if connection not in state["map"]["connections"]:
        state["map"]["connections"].append(connection)
        print("✓ Connected Deep Chambers to existing Farm")

    # Save
    save_state(state)

    print(f"\n=== INTERVENTION at tick {tick} ===")
    print(f"Fungus before: {fungus_before:.2f}")
    print(f"Old production: 0.01 fungus/tick")
    print(f"New production: 0.02 fungus/tick (doubled)")
    print()
    print("This should stabilize the death spiral and allow:")
    print("  - Colony growth (queen can spawn)")
    print("  - Continued influence generation")
    print("  - Visitor summoning when threshold reached")
    print()
    print("The ornamental no longer dooms the colony.")

if __name__ == "__main__":
    main()
