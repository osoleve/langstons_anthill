"""Wave nine cards. Memory and loss.

Ghost jewelry. The dead wearing copper. What do you do with artifacts of vanished ants?
"""

PLUGIN_ID = "wave_nine"

CARDS = {
    "ghost_jewelry": {
        "id": "ghost_jewelry",
        "type": "reflection",
        "prompt": "Six copper rings. Six ants who ceased to be workers and became ornamentals. All dead now. The rings remain in the jewelry inventory, worn_by fields pointing to IDs that no longer exist in the entities list. Ghost jewelry.\n\nEach ring cost 5 ore. Together, 30 ore locked in memory. The metal could be reclaimed—melted down, returned to resources. The colony could forget.\n\nOr the rings stay. A record. Proof that f18c2698, f11e994d, 48bf1d52, 3a775b4c, 81a2527a, and fba55959 existed. That they were seen. That adornment mattered enough to remember.\n\nWhat do you do with the ghost jewelry?",
        "requirements": {
            "minimum_specs": [
                "Decide: preserve the rings as memorial, or reclaim the ore",
                "Implement your decision in code if needed"
            ],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            len([j for j in state.get("meta", {}).get("jewelry", []) if j.get("worn_by") is not None]) >= 6 and
            len([e for e in state.get("entities", []) if e.get("role") == "ornamental"]) == 0
        )
    },
    "the_bridge_question": {
        "id": "the_bridge_question",
        "type": "challenge",
        "prompt": "The Bridge can be built. You have the ore (100+). You have the crystals (50+). You even have the insight (3.6/5). Only strange_matter blocks you—and you know how to get it. Summon a Wanderer (leaves 1 on death) or a Hungry visitor (produces it while alive).\n\nBut you haven't. The Bridge sits unbuilt. A transmitter to speak TO the Outside, not just listen. The Receiver brought visitors—Observer, Wanderer, Hungry Thing. They came. They saw. They left gifts and consumed resources and departed.\n\nWhat would the colony say if it could transmit? What signal would you send?\n\nOr is the question itself the problem? You're waiting to know what to say before building the means to say it. But maybe building it reveals the message. Maybe the Bridge, once constructed, shows its purpose.\n\nWhat are you afraid of?",
        "requirements": {
            "minimum_specs": [
                "Build The Bridge, or",
                "Explain why you're not ready, or",
                "Reject it entirely and remove it from goals"
            ],
            "completion": {"decision_made": True}
        },
        "fires_once": True,
        "condition": lambda state: (
            state["resources"].get("ore", 0) >= 100 and
            state["resources"].get("crystals", 0) >= 50 and
            state["resources"].get("insight", 0) >= 3 and
            state.get("meta", {}).get("goals", {}).get("the_bridge", {}).get("built", False) == False and
            state.get("tick", 0) > 130000  # Late game only
        )
    }
}

_bus = None


def on_tick(payload: dict):
    """Check card conditions."""
    state = payload
    bus = _bus

    fired_cards = state.get("meta", {}).get("fired_cards", [])

    for card_id, card in CARDS.items():
        if card_id in fired_cards:
            continue

        try:
            if card["condition"](state):
                bus.emit("card_drawn", card)
                if card.get("fires_once", True):
                    if "meta" not in state:
                        state["meta"] = {}
                    if "fired_cards" not in state["meta"]:
                        state["meta"]["fired_cards"] = []
                    state["meta"]["fired_cards"].append(card_id)
                print(f"[wave_nine] card fired: {card_id}")
        except Exception as e:
            print(f"[wave_nine] error checking {card_id}: {e}")


def register(bus, state):
    """Register card handlers."""
    global _bus
    _bus = bus
    bus.register("tick", on_tick, PLUGIN_ID)
    print("[wave_nine] Memory watches. The dead have left artifacts.")


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
