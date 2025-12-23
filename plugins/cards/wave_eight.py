"""Wave eight cards. Volatility and consequence.

Stability is comfortable. Comfort is boring.
The game needs friction to be interesting.
"""

import random

PLUGIN_ID = "wave_eight"

# Random event timing
_last_event_tick = 0
EVENT_COOLDOWN = 600  # 10 minutes between events
EVENT_CHANCE = 0.005  # 0.5% per tick when off cooldown

RANDOM_EVENTS = [
    {
        "name": "tremor",
        "message": "A tremor shakes the tunnels. Loose dirt falls. The Crystal Mine yields double for 5 minutes.",
        "effect": "crystal_boost"
    },
    {
        "name": "mold_outbreak",
        "message": "Strange mold appears on the fungus farms. Production halved until addressed.",
        "effect": "fungus_penalty"
    },
    {
        "name": "ore_vein_discovery",
        "message": "A glittering vein is exposed. +5 ore immediately.",
        "effect": "ore_bonus"
    },
    {
        "name": "hungry_wind",
        "message": "A cold wind blows through the tunnels. All entities feel hungrier.",
        "effect": "hunger_spike"
    },
    {
        "name": "strange_dreams",
        "message": "The ornamental dreams of somewhere else. +0.5 influence.",
        "effect": "influence_bonus"
    }
]

CARDS = {
    "complacency_tax": {
        "id": "complacency_tax",
        "type": "warning",
        "prompt": "Resources stockpiled. Entities comfortable. Nothing threatened. This is the trap. Stable systems stagnate. What risk have you avoided? What growth have you prevented? The colony that never struggles never evolves. Consider: what would make this interesting again?",
        "requirements": {
            "minimum_specs": ["Add volatility to the game", "Or accept the stagnation"],
            "completion": {"decision_made": True}
        },
        "fires_once": False,  # Can fire multiple times
        "is_complacency_card": True,
        "condition": lambda state: (
            state["resources"].get("fungus", 0) > 20 and
            state["resources"].get("nutrients", 0) > 500 and
            len(state.get("entities", [])) >= 2
        )
    },
    "random_event": {
        "id": "random_event",
        "type": "event",
        "prompt": None,  # Set dynamically
        "requirements": {
            "minimum_specs": ["Respond to the event"],
            "completion": {"decision_made": True}
        },
        "fires_once": False,
        "is_random_event": True,
        "condition": lambda state: True  # Handled separately
    }
}

_bus = None
_complacency_cooldown = 0
COMPLACENCY_COOLDOWN = 3600  # 1 hour between complacency warnings


def apply_event_effect(state: dict, effect: str) -> dict:
    """Apply the effect of a random event."""
    from engine.state import load_state, save_state

    state = load_state()

    if effect == "crystal_boost":
        # Double crystal generation for a while (we'll just give bonus now)
        state["resources"]["crystals"] = state["resources"].get("crystals", 0) + 2
    elif effect == "fungus_penalty":
        # Reduce fungus by 20%
        state["resources"]["fungus"] = state["resources"].get("fungus", 0) * 0.8
    elif effect == "ore_bonus":
        state["resources"]["ore"] = state["resources"].get("ore", 0) + 5
    elif effect == "hunger_spike":
        for entity in state.get("entities", []):
            entity["hunger"] = max(0, entity.get("hunger", 50) - 20)
    elif effect == "influence_bonus":
        state["resources"]["influence"] = state["resources"].get("influence", 0) + 0.5

    save_state(state)
    return state


def on_tick(payload: dict):
    """Check card conditions and random events."""
    global _last_event_tick, _complacency_cooldown
    from engine.state import load_state, save_state

    state = payload
    bus = _bus
    tick = state.get("tick", 0)

    # Random event check
    if tick - _last_event_tick >= EVENT_COOLDOWN:
        if random.random() < EVENT_CHANCE:
            event = random.choice(RANDOM_EVENTS)
            _last_event_tick = tick

            card = CARDS["random_event"].copy()
            card["prompt"] = f"**Random Event: {event['name'].replace('_', ' ').title()}**\n\n{event['message']}"

            apply_event_effect(state, event["effect"])
            bus.emit("card_drawn", card)
            print(f"[wave_eight] random event: {event['name']}")

    # Complacency check
    if _complacency_cooldown > 0:
        _complacency_cooldown -= 1
    else:
        card = CARDS["complacency_tax"]
        try:
            if card["condition"](state):
                bus.emit("card_drawn", card)
                _complacency_cooldown = COMPLACENCY_COOLDOWN
                print("[wave_eight] complacency tax fired")
        except:
            pass


def register(bus, state):
    """Register card handlers."""
    global _bus
    _bus = bus
    bus.register("tick", on_tick, PLUGIN_ID)
    print("[wave_eight] Volatility awakens. Stability is suspect.")


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
