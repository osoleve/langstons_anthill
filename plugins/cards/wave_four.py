"""Wave four cards. Aesthetics and adornment.

The colony has escaped death. Now it can pursue beauty.
These cards fire based on ore discovery and accumulation,
leading toward a jewelry crafting system.
"""

PLUGIN_ID = "wave_four"

CARDS = {
    "the_glitter_below": {
        "id": "the_glitter_below",
        "type": "discovery",
        "prompt": "The diggers have found something that isn't food, isn't useful, isn't necessary. Veins of copper and gold thread through the stone. It catches the light. It serves no purpose. Why do the ants keep looking at it?",
        "requirements": {
            "minimum_specs": ["Acknowledge the discovery of ore"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            "ore_vein" in state.get("map", {}).get("tiles", {}) and
            state["resources"].get("ore", 0) == 0
        )
    },
    "first_nugget": {
        "id": "first_nugget",
        "type": "milestone",
        "prompt": "One unit of ore has been extracted. It sits in storage, gleaming. An ant pauses near it, antennae twitching. There is no protocol for this. No instinct. Just... looking.",
        "requirements": {
            "minimum_specs": ["Decide what ore means to the colony"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: state["resources"].get("ore", 0) >= 1
    },
    "pretty_things": {
        "id": "pretty_things",
        "type": "design_prompt",
        "prompt": "5 ore accumulated. More than accident, less than purpose. The ants have no mirrors. They cannot see themselves. But they can see each other. What if something could be... worn?",
        "requirements": {
            "minimum_specs": ["Consider whether to enable adornment"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: state["resources"].get("ore", 0) >= 5
    },
    "the_first_craft": {
        "id": "the_first_craft",
        "type": "quest",
        "prompt": "10 ore. Enough to make something. Not a tool. Not food. Something that exists only to be beautiful. The colony has never made anything unnecessary before. This would be the first.\n\nRequirements:\n- Build a Crafting Hollow\n- Create one piece of jewelry\n- Decide who wears it",
        "requirements": {
            "minimum_specs": ["Build crafting system", "Create first jewelry"],
            "completion": {"jewelry_created": True}
        },
        "fires_once": True,
        "condition": lambda state: state["resources"].get("ore", 0) >= 10
    },
    "vanity_or_identity": {
        "id": "vanity_or_identity",
        "type": "observation",
        "prompt": "An ant wears a copper ring around one antenna. Other ants treat it... differently. Not better. Not worse. Just differently. Is adornment vanity? Or is it how a colony learns to see individuals?",
        "requirements": {
            "minimum_specs": ["Reflect on the meaning of adornment"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            "crafting_hollow" in state.get("systems", {}) and
            len(state.get("meta", {}).get("jewelry", [])) >= 1
        )
    },
    "the_undertakers_ring": {
        "id": "the_undertakers_ring",
        "type": "narrative",
        "prompt": "The undertaker has seen every death. Carried every body. They ask for nothing. But you notice them lingering near the Crafting Hollow. Looking at the ore. Looking away. Should the undertaker have something beautiful? They have earned it. But they would never ask.",
        "requirements": {
            "minimum_specs": ["Decide whether to gift the undertaker"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            "crafting_hollow" in state.get("systems", {}) and
            any(e.get("role") == "undertaker" for e in state.get("entities", [])) and
            state["resources"].get("ore", 0) >= 3
        )
    }
}

_bus = None


def get_fired_cards(state):
    """Get set of fired card IDs from game state."""
    return set(state.get("meta", {}).get("fired_cards", []))


def mark_card_fired(state, card_id):
    """Mark a card as fired in game state."""
    if "meta" not in state:
        state["meta"] = {}
    if "fired_cards" not in state["meta"]:
        state["meta"]["fired_cards"] = []
    if card_id not in state["meta"]["fired_cards"]:
        state["meta"]["fired_cards"].append(card_id)


def on_tick(payload: dict):
    """Check card conditions on each tick."""
    from engine.state import load_state, save_state

    state = payload
    bus = _bus
    fired_cards = get_fired_cards(state)
    any_fired = False

    for card_id, card in CARDS.items():
        if card.get("fires_once") and card_id in fired_cards:
            continue

        try:
            if card["condition"](state):
                bus.emit("card_drawn", card)
                if card.get("fires_once"):
                    mark_card_fired(state, card_id)
                    any_fired = True
                print(f"[wave_four] drew: {card_id}")
        except Exception:
            pass  # Condition failed, skip

    # Persist fired cards to disk
    if any_fired:
        disk_state = load_state()
        disk_state["meta"]["fired_cards"] = state["meta"].get("fired_cards", [])
        save_state(disk_state)


def register(bus, state):
    """Register card handlers."""
    global _bus
    _bus = bus
    bus.register("tick", on_tick, PLUGIN_ID)
    print("[wave_four] Aesthetics awakening")


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
