"""The Undertaker's Gambit. Necrotic recycling with contamination risk.

Dead ants go to the graveyard. Undertakers move corpses to compost.
Each corpse boosts nutrients but adds contamination.
Contamination risks blight events that shut down the tile.
"""

import random

PLUGIN_ID = "undertaker"

# Constants
CORPSE_PROCESSING_TICKS = 120  # How long to move one corpse
CORPSE_NUTRIENT_BOOST = 0.1    # Extra nutrients per tick from corpse
CORPSE_BOOST_DURATION = 600    # How long the boost lasts
CONTAMINATION_PER_CORPSE = 0.01  # 1% blight chance per corpse processed
BLIGHT_DURATION = 300          # How long blight lasts
UNDERTAKER_STARVATION_PENALTY = 0.05  # Extra hunger rate for undertakers

_bus = None


def on_entity_died(payload: dict):
    """Log when an entity dies. Corpse is added to graveyard in tick.py."""
    entity = payload.get("entity", {})
    cause = payload.get("cause", "unknown")
    print(f"[undertaker] {entity.get('type')} died of {cause}")


def process_undertakers(state: dict) -> dict:
    """Process undertaker ants moving corpses."""
    if "graveyard" not in state:
        return state

    graveyard = state["graveyard"]
    corpses = graveyard.get("corpses", [])
    compost_system = state["systems"].get("compost_heap", {})
    compost_tile = state["map"]["tiles"].get("compost", {})

    # Skip if tile is blighted
    if compost_tile.get("blighted", False):
        return state

    # Find undertaker ants
    undertakers = [e for e in state["entities"]
                   if e.get("type") == "ant" and e.get("role") == "undertaker"]

    for undertaker in undertakers:
        # Check if undertaker is currently processing
        if undertaker.get("processing_corpse"):
            undertaker["processing_ticks"] = undertaker.get("processing_ticks", 0) + 1

            if undertaker["processing_ticks"] >= CORPSE_PROCESSING_TICKS:
                # Corpse delivered to compost
                corpse_boosts = compost_system.get("corpse_boosts", [])
                corpse_boosts.append({
                    "expires_at_tick": state["tick"] + CORPSE_BOOST_DURATION,
                    "bonus": CORPSE_NUTRIENT_BOOST
                })
                compost_system["corpse_boosts"] = corpse_boosts

                # Add contamination
                compost_tile["contamination"] = compost_tile.get("contamination", 0) + CONTAMINATION_PER_CORPSE

                graveyard["total_processed"] = graveyard.get("total_processed", 0) + 1

                undertaker["processing_corpse"] = False
                undertaker["processing_ticks"] = 0

                print(f"[undertaker] corpse processed, contamination now {compost_tile['contamination']:.1%}")

                _bus.emit("corpse_processed", {
                    "tick": state["tick"],
                    "total_processed": graveyard["total_processed"],
                    "contamination": compost_tile["contamination"]
                })

        elif corpses:
            # Start processing a corpse
            corpse = corpses.pop(0)
            undertaker["processing_corpse"] = True
            undertaker["processing_ticks"] = 0
            print(f"[undertaker] {undertaker['id']} collecting corpse from graveyard")

    return state


def process_contamination(state: dict) -> dict:
    """Check for blight events based on contamination."""
    compost_tile = state["map"]["tiles"].get("compost", {})
    compost_system = state["systems"].get("compost_heap", {})

    # Handle active blight
    if compost_tile.get("blighted", False):
        compost_tile["blight_ticks_remaining"] = compost_tile.get("blight_ticks_remaining", 0) - 1

        if compost_tile["blight_ticks_remaining"] <= 0:
            compost_tile["blighted"] = False
            compost_tile["contamination"] = 0  # Reset after blight
            print("[undertaker] blight has cleared from The Heap")
            _bus.emit("blight_cleared", {"tick": state["tick"], "tile": "compost"})

        return state

    # Roll for blight based on contamination
    contamination = compost_tile.get("contamination", 0)
    if contamination > 0 and random.random() < contamination:
        # Blight strikes!
        compost_tile["blighted"] = True
        compost_tile["blight_ticks_remaining"] = BLIGHT_DURATION

        # Kill any ants on the tile
        survivors = []
        for entity in state["entities"]:
            if entity.get("tile") == "compost":
                print(f"[undertaker] BLIGHT kills {entity.get('type')} {entity.get('id')} on The Heap")
                _bus.emit("entity_died", {
                    "entity": entity,
                    "cause": "blight",
                    "tick": state["tick"]
                })
            else:
                survivors.append(entity)
        state["entities"] = survivors

        # Clear corpse boosts
        compost_system["corpse_boosts"] = []

        print(f"[undertaker] BLIGHT EVENT on The Heap! Tile disabled for {BLIGHT_DURATION} ticks")
        _bus.emit("blight_struck", {
            "tick": state["tick"],
            "tile": "compost",
            "contamination": contamination
        })

    return state


def process_corpse_boosts(state: dict) -> dict:
    """Apply and expire corpse nutrient boosts."""
    compost_system = state["systems"].get("compost_heap", {})
    compost_tile = state["map"]["tiles"].get("compost", {})

    # Skip if blighted
    if compost_tile.get("blighted", False):
        return state

    boosts = compost_system.get("corpse_boosts", [])
    active_boosts = []
    total_bonus = 0

    for boost in boosts:
        if boost["expires_at_tick"] > state["tick"]:
            active_boosts.append(boost)
            total_bonus += boost["bonus"]

    compost_system["corpse_boosts"] = active_boosts

    # Apply bonus nutrients
    if total_bonus > 0:
        state["resources"]["nutrients"] = state["resources"].get("nutrients", 0) + total_bonus

    return state


def check_compost_disabled(state: dict) -> dict:
    """Disable compost production during blight."""
    compost_tile = state["map"]["tiles"].get("compost", {})
    compost_system = state["systems"].get("compost_heap", {})

    if compost_tile.get("blighted", False):
        # Store original rates if not stored
        if "original_generates" not in compost_system:
            compost_system["original_generates"] = compost_system.get("generates", {}).copy()
            compost_system["original_consumes"] = compost_system.get("consumes", {}).copy()
            compost_system["generates"] = {}
            compost_system["consumes"] = {}
    else:
        # Restore original rates if stored
        if "original_generates" in compost_system:
            compost_system["generates"] = compost_system.pop("original_generates")
            compost_system["consumes"] = compost_system.pop("original_consumes")

    return state


def on_tick(payload: dict):
    """Main tick handler for undertaker system."""
    from engine.state import load_state, save_state

    state = load_state()

    state = process_undertakers(state)
    state = process_corpse_boosts(state)
    state = process_contamination(state)
    state = check_compost_disabled(state)

    save_state(state)


def register(bus, state):
    """Register handlers."""
    global _bus
    _bus = bus
    bus.register("entity_died", on_entity_died, PLUGIN_ID)
    bus.register("tick", on_tick, PLUGIN_ID)
    print("[undertaker] The Undertaker's Gambit is active")


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
