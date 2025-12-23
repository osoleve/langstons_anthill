"""Wave two cards. Emerge after the tutorial."""

PLUGIN_ID = "wave_two"

CARDS = {
    "what_do_nutrients_do": {
        "id": "what_do_nutrients_do",
        "type": "design_prompt",
        "prompt": "You have nutrients accumulating. But what are they for? A resource without a sink is just a number. Design something that uses nutrients. Consider: growth, feeding, fertilizing, trade.",
        "requirements": {
            "minimum_specs": ["Create a system or mechanic that consumes nutrients"],
            "completion": {"nutrients_consumed": True}
        },
        "fires_once": True,
        "condition": lambda state: state["resources"].get("nutrients", 0) >= 50
    },
    "the_second_grind": {
        "id": "the_second_grind",
        "type": "quest",
        "prompt": "Reach 500 of any resource. The numbers are bigger now. Does that feel different? Is 500 more satisfying than 100? Or is it just... more?",
        "requirements": {
            "completion": {"any_resource": 500}
        },
        "side_task": "Consider: what would make large numbers meaningful?",
        "duration_estimate_ticks": 3000,
        "fires_once": True,
        "condition": lambda state: max(state["resources"].values(), default=0) >= 100 and max(state["resources"].values(), default=0) < 500
    },
    "something_alive": {
        "id": "something_alive",
        "type": "design_prompt",
        "prompt": "Everything so far is mechanical. Dirt, compost, nutrients. What if something was alive? An entity that moves, grows, dies. Ants are the obvious choice. But maybe something else.",
        "requirements": {
            "minimum_specs": ["Add an entity to the game", "It should have some lifecycle"],
            "completion": {"entities_count": 1}
        },
        "fires_once": True,
        "condition": lambda state: len(state["systems"]) >= 2 and len(state["entities"]) == 0
    },
    "the_map_is_flat": {
        "id": "the_map_is_flat",
        "type": "observation",
        "prompt": "The map is just tiles. There's no terrain, no elevation, no weather. Is that a problem? Or is flatness appropriate for an anthill? Consider what depth the map needs, if any.",
        "requirements": {
            "minimum_specs": ["Decide whether to add map complexity or not"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: len(state["map"]["tiles"]) >= 3 and state["tick"] > 5000
    },
    "efficiency_question": {
        "id": "efficiency_question",
        "type": "meta",
        "prompt": "Your systems generate at fixed rates. There's no optimization. No upgrades. No choices about efficiency. Is that a problem? Incremental games often live or die by their upgrade systems.",
        "requirements": {
            "minimum_specs": ["Consider whether to add upgrades or keep things flat"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: state["tick"] > 8000 and len(state["systems"]) >= 2
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

        if card["condition"](state):
            bus.emit("card_drawn", card)
            if card.get("fires_once"):
                mark_card_fired(state, card_id)
                any_fired = True
            print(f"[wave_two] drew: {card_id}")

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


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
