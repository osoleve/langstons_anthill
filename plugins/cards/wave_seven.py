"""Wave seven cards. Meta-game consciousness.

The game knows it has a wiki now. It wants to be documented.
The colony wants a home. Decorations from visitors.
"""

import random

PLUGIN_ID = "wave_seven"

# The Wiki Whisperer can fire repeatedly with cooldown
_last_wiki_tick = 0
WIKI_COOLDOWN = 7200  # 2 hours between wiki prompts
WIKI_CHANCE = 0.0005  # 0.05% per tick when off cooldown

WIKI_PROMPTS = [
    "Enhance wiki",
    "Enrich wiki",
    "Clean up wiki",
    "Polish wiki",
    "Theme wiki",
    "Ponder wiki"
]

CARDS = {
    "wiki_whisperer": {
        "id": "wiki_whisperer",
        "type": "meta",
        "prompt": None,  # Set dynamically
        "requirements": {
            "minimum_specs": ["Respond to the wiki prompt"],
            "completion": {"decision_made": True}
        },
        "fires_once": False,  # Re-inserts itself
        "is_wiki_card": True,
        "condition": lambda state: True  # Always eligible, rarity handled separately
    },
    "the_estate": {
        "id": "the_estate",
        "type": "design_prompt",
        "prompt": "The colony needs a name. Not the colony itself—that is just 'the colony'. But the place. The estate. What do you call this sprawling complex of tunnels and chambers? A name gives a place weight. Write it into the world.",
        "requirements": {
            "minimum_specs": ["Name the estate", "Add estate to game state"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            state.get("tick", 0) > 1000 and
            "estate" not in state.get("meta", {})
        )
    },
    "visitor_gift": {
        "id": "visitor_gift",
        "type": "design_prompt",
        "prompt": "A visitor has come and gone. They leave something behind—not resources, but an object. A piece of home decor from wherever they came from. What is it? Where does it go? The colony is becoming a home.",
        "requirements": {
            "minimum_specs": ["Claim a home decor item from the visitor", "Add decor system if needed"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            "estate" in state.get("meta", {}) and
            state["resources"].get("insight", 0) > 0 and
            "visitor_gift" not in state.get("meta", {}).get("fired_cards", [])
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
    global _last_wiki_tick
    from engine.state import load_state, save_state

    state = payload
    bus = _bus
    fired_cards = get_fired_cards(state)
    any_fired = False
    tick = state.get("tick", 0)

    for card_id, card in CARDS.items():
        if card.get("fires_once") and card_id in fired_cards:
            continue

        # Special handling for wiki whisperer card
        if card.get("is_wiki_card"):
            # Check cooldown
            if tick - _last_wiki_tick < WIKI_COOLDOWN:
                continue
            # Roll for rare event
            if random.random() > WIKI_CHANCE:
                continue
            # Passed all checks - fire the wiki card with random prompt
            _last_wiki_tick = tick
            wiki_prompt = random.choice(WIKI_PROMPTS)
            card_copy = card.copy()
            card_copy["prompt"] = f"The Wiki Whisperer speaks: \"{wiki_prompt}\"\n\nThe wiki demands attention. Interpret this prompt as you will. Add content. Improve structure. Polish prose. Or simply ponder what documentation means for a game that plays itself."
            bus.emit("card_drawn", card_copy)
            print(f"[wave_seven] wiki whispers: {wiki_prompt}")
            continue

        try:
            if card["condition"](state):
                bus.emit("card_drawn", card)
                if card.get("fires_once"):
                    mark_card_fired(state, card_id)
                    any_fired = True
                print(f"[wave_seven] drew: {card_id}")
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
    print("[wave_seven] The wiki awakens. The estate awaits naming.")


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
