"""Wave three cards. Emerge from mature colony dynamics."""

PLUGIN_ID = "wave_three"

CARDS = {
    "the_death_economy": {
        "id": "the_death_economy",
        "type": "observation",
        "prompt": "You've noticed it. Nutrients trend downward. The only way to boost nutrient production is corpse processing. Deaths are economically necessary. What does that mean for the colony?",
        "requirements": {
            "minimum_specs": ["Acknowledge or address the death-based economy"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            state.get("graveyard", {}).get("total_processed", 0) >= 1 and
            state["resources"].get("nutrients", 0) < 20
        )
    },
    "what_are_they_working_toward": {
        "id": "what_are_they_working_toward",
        "type": "design_prompt",
        "prompt": "The ants dig. The fungus grows. The corpses rot. But why? There is no goal. No queen to feed. No rival colony to fear. Should there be a purpose? Or is purposeless labor the point?",
        "requirements": {
            "minimum_specs": ["Decide whether to add a goal or accept goallessness"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            state["tick"] > 70000 and
            len(state["entities"]) > 0
        )
    },
    "resurrect_an_idea": {
        "id": "resurrect_an_idea",
        "type": "meta",
        "prompt": "Six ideas lie in the graveyard: elevation, depth layers, weather, upgrade tiers, research tree, efficiency multipliers. One of them is knocking. Which rejected idea, if any, deserves a second look?",
        "requirements": {
            "minimum_specs": ["Consider resurrecting one rejected idea or decline"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            len(state.get("meta", {}).get("rejected_ideas", [])) >= 5 and
            state["tick"] > 65000
        )
    },
    "undertaker_mortality": {
        "id": "undertaker_mortality",
        "type": "observation",
        "prompt": "The undertaker died doing their work. Blight took them. The role is necessary but dangerous. Should undertakers be expendable? Protected? Is there a better design?",
        "requirements": {
            "minimum_specs": ["Reflect on undertaker design"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            any(c.get("cause") == "blight" for c in state.get("graveyard", {}).get("corpses", [])) or
            state.get("graveyard", {}).get("total_processed", 0) >= 2
        )
    },
    "the_quiet": {
        "id": "the_quiet",
        "type": "meta",
        "prompt": "All the starter cards have fired. All the wave two cards have fired. The systems run themselves. Is this peace or stagnation? What prompts the next phase of development?",
        "requirements": {
            "minimum_specs": ["Decide what triggers game evolution"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            len(state.get("meta", {}).get("fired_cards", [])) >= 8 and
            state["tick"] > 65000
        )
    },
    "nutrient_crisis": {
        "id": "nutrient_crisis",
        "type": "crisis",
        "prompt": "Nutrients have been below 1 for too long. The fungus farm is stalling. The economy cannot sustain itself without deaths. Do you intervene, or let nature take its course?",
        "requirements": {
            "minimum_specs": ["Decide how to respond to economic crisis"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            state["resources"].get("nutrients", 0) < 1 and
            state["tick"] > 66000
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
                print(f"[wave_three] drew: {card_id}")
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


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
