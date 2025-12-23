"""Wave five cards. Influence and prestige.

Influence accumulates from ornamental ants.
It cannot be spent on survival. It has no function.
But perhaps it has meaning.
"""

PLUGIN_ID = "wave_five"

CARDS = {
    "first_influence": {
        "id": "first_influence",
        "type": "milestone",
        "prompt": "One unit of influence has accumulated. It cannot be eaten. It cannot build. It cannot protect. And yet you kept generating it. The ornamentals exist. They are seen. That is the influence. What does a colony do with prestige it cannot spend?",
        "requirements": {
            "minimum_specs": ["Acknowledge the accumulation of influence"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: state["resources"].get("influence", 0) >= 1
    },
    "the_court": {
        "id": "the_court",
        "type": "observation",
        "prompt": "With two ornamentals, the Crafting Hollow has become something else. Not a workshop. A court. They do not work. They are observed. They consume. They persist. Is this parasitism or patronage? The colony feeds them. What do they give back?",
        "requirements": {
            "minimum_specs": ["Reflect on the ornamentals"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            sum(1 for e in state.get("entities", []) if e.get("adorned")) >= 2
        )
    },
    "influence_threshold": {
        "id": "influence_threshold",
        "type": "design_prompt",
        "prompt": "10 influence accumulated. A colony that generates prestige without purpose. Should influence have a use? Should it attract something? Enable something? Or is its uselessness the point?",
        "requirements": {
            "minimum_specs": ["Decide whether influence should have function"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: state["resources"].get("influence", 0) >= 10
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
                print(f"[wave_five] drew: {card_id}")
        except Exception as e:
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
    print("[wave_five] Influence awakens")


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
