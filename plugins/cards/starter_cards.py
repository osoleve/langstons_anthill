"""Starter cards. Bootstrap the game."""

import json
from pathlib import Path
from datetime import datetime

PLUGIN_ID = "starter_cards"

DECISIONS_LOG = Path(__file__).parent.parent.parent / "logs" / "decisions.jsonl"


def log_decision(tick: int, decision_type: str, choice: str, why: str, alternatives: list = None):
    """Append to decisions log."""
    DECISIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "tick": tick,
        "timestamp": datetime.now().isoformat(),
        "type": decision_type,
        "choice": choice,
        "why": why,
        "alternatives_considered": alternatives or []
    }
    with open(DECISIONS_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def emit_card(bus, card: dict):
    """Emit a card_drawn event."""
    bus.emit("card_drawn", card)


# Card definitions
CARDS = {
    "first_dig": {
        "id": "first_dig",
        "type": "tutorial",
        "prompt": "You're standing on dirt. Nothing exists yet. You need to start somewhere. Consider: what's the simplest resource you could gather? Dig.",
        "requirements": {
            "completion": {"resource": "dirt", "amount": 10}
        },
        "fires_once": True,
        "condition": lambda state: state["tick"] == 1
    },
    "first_system": {
        "id": "first_system",
        "type": "milestone",
        "prompt": "You have dirt. Dirt is not interesting. What could you build with it? Or: what could generate something more interesting than dirt? You need your first system.",
        "requirements": {
            "minimum_specs": ["A system that generates or transforms resources"],
            "completion": {"systems_count": 1}
        },
        "fires_once": True,
        "condition": lambda state: state["resources"].get("dirt", 0) >= 10 and len(state["systems"]) == 0
    },
    "the_grind_begins": {
        "id": "the_grind_begins",
        "type": "quest",
        "prompt": "Your first system exists. Now you wait. Let it run. Watch the numbers. This is what an incremental game is. If you get bored, that's information.",
        "requirements": {
            "completion": {"any_resource": 100}
        },
        "side_task": "Notice what you're thinking while waiting.",
        "duration_estimate_ticks": 600,
        "fires_once": True,
        "condition": lambda state: len(state["systems"]) >= 1 and max(state["resources"].values(), default=0) < 100
    },
    "boredom_acknowledged": {
        "id": "boredom_acknowledged",
        "type": "meta",
        "prompt": "You're bored. The boredom detector fired. What does that mean? Maybe the current systems aren't interesting. Maybe you need a goal. Maybe you need friction. What would make this less boring?",
        "requirements": {
            "minimum_specs": ["Do something about the boredom"],
            "completion": {"meta.boredom": 0}
        },
        "fires_once": False,
        "condition": lambda state: False  # Triggered by boredom event, not tick
    },
    "expansion": {
        "id": "expansion",
        "type": "quest",
        "prompt": "The map has one tile. That's limiting. Add geography. Where does a new system go? What connects to what? Build outward.",
        "requirements": {
            "minimum_specs": ["Add a new tile to the map", "Connect it to existing tiles"],
            "completion": {"tiles_count": 3}
        },
        "fires_once": True,
        "condition": lambda state: len(state["systems"]) >= 1 and len(state["map"]["tiles"]) < 3
    }
}

# Track which cards have fired
fired_cards = set()


def on_tick(payload: dict):
    """Check card conditions on each tick."""
    state = payload
    bus = _bus  # Captured during register

    for card_id, card in CARDS.items():
        if card.get("fires_once") and card_id in fired_cards:
            continue

        if card["condition"](state):
            emit_card(bus, card)
            if card.get("fires_once"):
                fired_cards.add(card_id)
            print(f"[cards] drew: {card_id}")


def on_boredom(payload: dict):
    """Handle boredom events."""
    bus = _bus
    card = CARDS["boredom_acknowledged"]
    emit_card(bus, card)
    print(f"[cards] drew: boredom_acknowledged (level: {payload.get('level')})")


_bus = None


def register(bus, state):
    """Register card handlers."""
    global _bus
    _bus = bus
    bus.register("tick", on_tick, PLUGIN_ID)
    bus.register("boredom", on_boredom, PLUGIN_ID)


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
