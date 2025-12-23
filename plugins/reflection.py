"""Reflection plugin. Prompts for contemplation, not action.

Unlike cards, reflections don't demand decisions. They ask for noticing.
Reflections fire after significant events, or when stillness accumulates.
"""

import random

PLUGIN_ID = "reflection"

# Open questions for reflection
PROMPTS = [
    "What is the colony's rhythm right now?",
    "What surprised you since the last reflection?",
    "What pattern are you noticing?",
    "What feels different than before?",
    "What are you waiting for?",
    "What would you miss if it disappeared?",
    "What is the sound of this moment?",
    "Where is the tension?",
    "What is the colony teaching you?",
    "What question should be asked that hasn't been?",
]

# Reflection triggers
STILLNESS_THRESHOLD = 3000  # ticks of no significant events
POST_EVENT_DELAY = 300  # ticks after significant event before reflecting

_bus = None
_last_significant_event = 0
_last_reflection = 0
_pending_reflection = False


def on_tick(payload: dict):
    """Check if reflection is due."""
    global _pending_reflection, _last_reflection

    from engine.state import load_state, save_state

    state = payload
    tick = state["tick"]

    # Don't reflect too often
    if tick - _last_reflection < STILLNESS_THRESHOLD:
        return

    # Check for stillness or post-event reflection
    ticks_since_event = tick - _last_significant_event

    should_reflect = False
    trigger = None

    if ticks_since_event >= STILLNESS_THRESHOLD:
        should_reflect = True
        trigger = "stillness"
    elif _pending_reflection and ticks_since_event >= POST_EVENT_DELAY:
        should_reflect = True
        trigger = "aftermath"
        _pending_reflection = False

    if should_reflect:
        prompt = random.choice(PROMPTS)
        _last_reflection = tick

        # Store the reflection prompt in state
        disk_state = load_state()
        if "reflections" not in disk_state["meta"]:
            disk_state["meta"]["reflections"] = []

        reflection = {
            "tick": tick,
            "trigger": trigger,
            "prompt": prompt,
            "response": None  # To be filled by player
        }
        disk_state["meta"]["reflections"].append(reflection)
        save_state(disk_state)

        _bus.emit("reflection_prompt", {
            "tick": tick,
            "trigger": trigger,
            "prompt": prompt
        })

        print(f"[reflection] ({trigger}) {prompt}")


def on_entity_died(payload: dict):
    """Mark death as significant event."""
    global _last_significant_event, _pending_reflection
    _last_significant_event = payload.get("tick", 0)
    _pending_reflection = True


def on_blight_struck(payload: dict):
    """Mark blight as significant event."""
    global _last_significant_event, _pending_reflection
    _last_significant_event = payload.get("tick", 0)
    _pending_reflection = True


def on_blight_cleared(payload: dict):
    """Mark blight clearing as significant event."""
    global _last_significant_event, _pending_reflection
    _last_significant_event = payload.get("tick", 0)
    _pending_reflection = True


def on_threshold(payload: dict):
    """Mark major thresholds as significant."""
    global _last_significant_event, _pending_reflection
    threshold = payload.get("threshold", 0)
    if threshold >= 100:  # Only major thresholds
        _last_significant_event = payload.get("tick", 0)
        _pending_reflection = True


def record_reflection(tick: int, response: str):
    """Record a reflection response."""
    from engine.state import load_state, save_state

    state = load_state()
    reflections = state["meta"].get("reflections", [])

    # Find the most recent unanswered reflection
    for r in reversed(reflections):
        if r["response"] is None:
            r["response"] = response
            break

    save_state(state)
    print(f"[reflection] recorded: {response[:50]}...")


def register(bus, state):
    """Register handlers."""
    global _bus, _last_significant_event, _last_reflection
    _bus = bus

    # Initialize from state
    _last_significant_event = state.get("tick", 0)
    reflections = state.get("meta", {}).get("reflections", [])
    if reflections:
        _last_reflection = reflections[-1].get("tick", 0)

    bus.register("tick", on_tick, PLUGIN_ID)
    bus.register("entity_died", on_entity_died, PLUGIN_ID)
    bus.register("blight_struck", on_blight_struck, PLUGIN_ID)
    bus.register("blight_cleared", on_blight_cleared, PLUGIN_ID)
    bus.register("threshold", on_threshold, PLUGIN_ID)

    print("[reflection] Contemplation is now possible")


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
