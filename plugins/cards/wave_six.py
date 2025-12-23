"""Wave six cards. The Outside.

Something answered. The Receiver is built.
Visitors come and go. They bring things the colony cannot make.
The walls of reality are breached.
"""

import random

PLUGIN_ID = "wave_six"

# WWCD cooldown tracking
_last_wwcd_tick = 0
WWCD_COOLDOWN = 3600  # 1 hour between possible fires
WWCD_CHANCE = 0.001  # 0.1% per tick when off cooldown (~once per 1000 ticks when eligible)

CARDS = {
    "the_receiver_built": {
        "id": "the_receiver_built",
        "type": "milestone",
        "prompt": "The Receiver stands at the colony's edge. A jagged antenna of bone and crystal. It listens to frequencies you cannot hear. Influence drains slowly into it, a signal screaming into the black static. You built this because something told you to. Did you stop to ask who was speaking?",
        "requirements": {
            "minimum_specs": ["Acknowledge the Receiver"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: "receiver" in state.get("systems", {})
    },
    "first_visitor": {
        "id": "first_visitor",
        "type": "observation",
        "prompt": "Something came. Not an ant. Not born from the queen. It appeared at the Receiver and now it moves among the colony. The ants do not know what to do with it. Neither do you. Watch what happens. Note what it leaves behind when it goes.",
        "requirements": {
            "minimum_specs": ["Observe the visitor"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: any(
            e.get("type") == "visitor" for e in state.get("entities", [])
        )
    },
    "visitor_departed": {
        "id": "visitor_departed",
        "type": "observation",
        "prompt": "The visitor is gone. They were never meant to stay. But something remains - a new resource, a new possibility. Strange matter. Insight. Things the colony could not produce on its own. Is this trade? Communion? Parasitism in reverse? The walls are thinner now.",
        "requirements": {
            "minimum_specs": ["Consider what the visitor left behind"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            state["resources"].get("strange_matter", 0) > 0 or
            state["resources"].get("insight", 0) > 0
        )
    },
    "the_hungry_one": {
        "id": "the_hungry_one",
        "type": "warning",
        "prompt": "A Hungry Thing has come. It does not eat fungus. It eats influence itself. Your prestige. Your signal. It transforms what it consumes into strange matter. You invited this. The colony cannot uninvite it. Watch your influence drain. Decide if the transformation is worth the cost.",
        "requirements": {
            "minimum_specs": ["Observe the hungry visitor"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: any(
            e.get("type") == "visitor" and e.get("subtype") == "hungry"
            for e in state.get("entities", [])
        )
    },
    "observer_insight": {
        "id": "observer_insight",
        "type": "observation",
        "prompt": "An Observer watches. And from the watching, insight accumulates. A resource you cannot generate, cannot mine, cannot farm. It comes from being seen by something outside. What does the colony look like from outside? What does the Observer understand that you do not?",
        "requirements": {
            "minimum_specs": ["Consider the nature of insight"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: state["resources"].get("insight", 0) >= 0.5
    },
    "strange_matter_threshold": {
        "id": "strange_matter_threshold",
        "type": "design_prompt",
        "prompt": "10 strange matter accumulated. A resource from outside reality. It does nothing - yet. Should it enable something the colony could not otherwise build? A structure that exists between states? An entity that is both visitor and ant? The colony has materials it did not earn. What will you make of them?",
        "requirements": {
            "minimum_specs": ["Decide what strange matter enables"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: state["resources"].get("strange_matter", 0) >= 10
    },
    "multiple_visitors": {
        "id": "multiple_visitors",
        "type": "observation",
        "prompt": "More than one visitor at once. The colony is becoming a waystation. A place things pass through. The ants are outnumbered by visitors. Or will be. What happens to a colony when more entities come from outside than are born within?",
        "requirements": {
            "minimum_specs": ["Observe the visitors"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            sum(1 for e in state.get("entities", []) if e.get("type") == "visitor") >= 2
        )
    },
    "the_void_is_silent": {
        "id": "the_void_is_silent",
        "type": "observation",
        "prompt": "Three summoning attempts. No response. The influence spent into the void. The void does not always answer. Perhaps it is busy. Perhaps it is testing your patience. Perhaps you are screaming into nothing. Keep spending influence. See what persists.",
        "requirements": {
            "minimum_specs": ["Acknowledge the silence"],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            state.get("meta", {}).get("failed_summons", 0) >= 3
        )
    },
    "wwcd": {
        "id": "wwcd",
        "type": "audit",
        "prompt": "What Would Carmack Do? Look at what you have built with an engineer's eye. What is wasteful? What is overbuilt? What doesn't actually work? What would you cut? What would you optimize? The colony does not need more features. It needs the features it has to work well. Audit. Simplify. Ship.",
        "requirements": {
            "minimum_specs": ["Perform an engineering audit", "Identify one thing to fix or cut"],
            "completion": {"decision_made": True}
        },
        "fires_once": False,  # Can fire multiple times
        "is_rare": True,  # Special handling in on_tick
        "condition": lambda state: True  # Always eligible, rarity handled separately
    }
}

_bus = None
_failed_summons = 0


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


def on_summoning_failed(payload: dict):
    """Track failed summoning attempts."""
    global _failed_summons
    _failed_summons += 1

    from engine.state import load_state, save_state
    state = load_state()
    if "meta" not in state:
        state["meta"] = {}
    state["meta"]["failed_summons"] = _failed_summons
    save_state(state)


def on_tick(payload: dict):
    """Check card conditions on each tick."""
    global _last_wwcd_tick
    from engine.state import load_state, save_state

    state = payload
    bus = _bus
    fired_cards = get_fired_cards(state)
    any_fired = False
    tick = state.get("tick", 0)

    for card_id, card in CARDS.items():
        if card.get("fires_once") and card_id in fired_cards:
            continue

        # Special handling for rare cards (like WWCD)
        if card.get("is_rare"):
            # Check cooldown
            if tick - _last_wwcd_tick < WWCD_COOLDOWN:
                continue
            # Roll for rare event
            if random.random() > WWCD_CHANCE:
                continue
            # Passed all checks - fire the rare card
            _last_wwcd_tick = tick
            bus.emit("card_drawn", card)
            print(f"[wave_six] RARE EVENT: {card_id}")
            continue

        try:
            if card["condition"](state):
                bus.emit("card_drawn", card)
                if card.get("fires_once"):
                    mark_card_fired(state, card_id)
                    any_fired = True
                print(f"[wave_six] drew: {card_id}")
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
    bus.register("summoning_failed", on_summoning_failed, PLUGIN_ID)
    print("[wave_six] The Outside awaits")


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
