"""Exploration plugin. Discover new tiles when resources allow."""

import random

PLUGIN_ID = "exploration"

# Possible discoveries
DISCOVERIES = [
    {
        "id": "crystal_cave",
        "name": "Crystal Cave",
        "type": "resource",
        "x": 2,
        "y": 0,
        "resource": "crystals",
        "description": "Strange formations glitter in the dark"
    },
    {
        "id": "water_source",
        "name": "Underground Spring",
        "type": "resource",
        "x": 0,
        "y": -1,
        "resource": "water",
        "description": "Clean water seeps from the rock"
    },
    {
        "id": "bone_pit",
        "name": "Ancient Bones",
        "type": "mystery",
        "x": -2,
        "y": 0,
        "resource": "bones",
        "description": "The remains of something large"
    },
    {
        "id": "root_network",
        "name": "Root Network",
        "type": "organic",
        "x": 0,
        "y": 2,
        "resource": "sap",
        "description": "Thick roots from the surface, dripping with sap"
    },
    {
        "id": "ore_vein",
        "name": "Glittering Vein",
        "type": "resource",
        "x": -1,
        "y": -1,
        "resource": "ore",
        "description": "Veins of copper and gold thread through the stone"
    }
]

_bus = None
_discovery_offered = False
_discovered_tiles = set()


def on_tick(payload: dict):
    """Check for exploration opportunities."""
    global _discovery_offered


    state = payload

    # Check if enough dirt to explore (every 1000 dirt unlocks a discovery)
    dirt = state["resources"].get("dirt", 0)
    discoveries_allowed = int(dirt // 1000)
    current_discoveries = len(_discovered_tiles)

    if discoveries_allowed > current_discoveries and not _discovery_offered:
        # Offer a discovery
        available = [d for d in DISCOVERIES if d["id"] not in _discovered_tiles]
        if available:
            discovery = random.choice(available)
            _discovery_offered = True

            _bus.emit("card_drawn", {
                "id": f"discover_{discovery['id']}",
                "type": "exploration",
                "prompt": f"The diggers have found something. At ({discovery['x']}, {discovery['y']}), there is {discovery['description'].lower()}. This could be {discovery['name']}. Do you claim this tile?",
                "discovery": discovery,
                "requirements": {
                    "minimum_specs": ["Decide whether to claim the tile"],
                    "completion": {"decision_made": True}
                }
            })
            print(f"[exploration] discovered: {discovery['name']}")


def claim_discovery(discovery_id: str, state: dict) -> dict:
    """Claim a discovered tile."""
    global _discovery_offered, _discovered_tiles

    discovery = next((d for d in DISCOVERIES if d["id"] == discovery_id), None)
    if not discovery:
        return state

    # Add tile to map
    state["map"]["tiles"][discovery["id"]] = {
        "name": discovery["name"],
        "type": discovery["type"],
        "x": discovery["x"],
        "y": discovery["y"],
        "resource": discovery["resource"],
        "description": discovery["description"]
    }

    # Connect to origin
    state["map"]["connections"].append(["origin", discovery["id"]])

    # Initialize the resource
    if discovery["resource"] not in state["resources"]:
        state["resources"][discovery["resource"]] = 0

    _discovered_tiles.add(discovery_id)
    _discovery_offered = False

    print(f"[exploration] claimed: {discovery['name']}")

    return state


def register(bus, state):
    """Register handlers."""
    global _bus, _discovered_tiles
    _bus = bus
    bus.register("tick", on_tick, PLUGIN_ID)

    # Track already discovered tiles
    for tile_id in state.get("map", {}).get("tiles", {}):
        if tile_id in [d["id"] for d in DISCOVERIES]:
            _discovered_tiles.add(tile_id)


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
