"""Event Logger. Tracks significant events in a circular buffer.

Solves mysteries like "where did that influence come from?" by maintaining
a visible history of what happened.
"""

from collections import deque
from datetime import datetime

PLUGIN_ID = "event_logger"

# Maximum events to keep
MAX_EVENTS = 50

_bus = None
_event_buffer = deque(maxlen=MAX_EVENTS)


def log_event(event_type: str, tick: int, message: str, details: dict = None):
    """Add an event to the log buffer."""
    event = {
        "type": event_type,
        "tick": tick,
        "timestamp": datetime.now().isoformat(),
        "message": message
    }
    if details:
        event["details"] = details

    _event_buffer.append(event)
    print(f"[event_log] {message}")


def on_tick(payload: dict):
    """Persist event log to state every 50 ticks."""
    from engine.state import load_state, save_state

    state = payload
    tick = state.get("tick", 0)

    # Only update state periodically to reduce I/O
    if tick % 50 == 0:
        state = load_state()
        if "event_log" not in state.get("meta", {}):
            state["meta"]["event_log"] = []

        # Store the buffer as a list
        state["meta"]["event_log"] = list(_event_buffer)
        save_state(state)


def on_ants_spawned(payload: dict):
    """Log ant spawning."""
    tick = payload.get("tick", 0)
    count = payload.get("count", 0)
    nutrients = payload.get("nutrients_consumed", 0)
    fungus = payload.get("fungus_consumed", 0)

    log_event(
        "spawn",
        tick,
        f"Queen spawned {count} ants (consumed {nutrients} nutrients, {fungus} fungus)"
    )


def on_entity_death(payload: dict):
    """Log entity deaths."""
    tick = payload.get("tick", 0)
    entity_id = payload.get("entity_id", "unknown")
    entity_type = payload.get("entity_type", "unknown")
    cause = payload.get("cause", "unknown")

    log_event(
        "death",
        tick,
        f"{entity_type} {entity_id[:8]} died ({cause})"
    )


def on_visitor_arrived(payload: dict):
    """Log visitor arrivals."""
    tick = payload.get("tick", 0)
    name = payload.get("name", "Unknown")
    visitor_type = payload.get("visitor_type", "unknown")

    log_event(
        "visitor_arrival",
        tick,
        f"Visitor arrived: {name} ({visitor_type})",
        {"visitor_type": visitor_type}
    )


def on_visitor_departed(payload: dict):
    """Log visitor departures."""
    tick = payload.get("tick", 0)
    name = payload.get("name", "Unknown")

    log_event(
        "visitor_departure",
        tick,
        f"Visitor departed: {name}"
    )


def on_influence_spent(payload: dict):
    """Log influence expenditure."""
    tick = payload.get("tick", 0)
    amount = payload.get("amount", 0)
    purpose = payload.get("purpose", "unknown")

    log_event(
        "influence_spent",
        tick,
        f"Spent {amount} influence for {purpose}"
    )


def on_summoning_failed(payload: dict):
    """Log failed summoning attempts."""
    tick = payload.get("tick", 0)

    log_event(
        "summoning_failed",
        tick,
        "Summoning failed - the void is silent"
    )


def on_card_drawn(payload: dict):
    """Log card firings."""
    tick = payload.get("tick", 0)
    card_id = payload.get("id", "unknown")
    card_type = payload.get("type", "unknown")

    log_event(
        "card_drawn",
        tick,
        f"Card fired: {card_id} ({card_type})"
    )


def register(bus, state):
    """Register event handlers."""
    global _bus, _event_buffer
    _bus = bus

    # Initialize from state if it exists
    existing_log = state.get("meta", {}).get("event_log", [])
    if existing_log:
        _event_buffer = deque(existing_log, maxlen=MAX_EVENTS)

    # Register handlers for all interesting events
    bus.register("tick", on_tick, PLUGIN_ID)
    bus.register("ants_spawned", on_ants_spawned, PLUGIN_ID)
    bus.register("entity_death", on_entity_death, PLUGIN_ID)
    bus.register("visitor_arrived", on_visitor_arrived, PLUGIN_ID)
    bus.register("visitor_departed", on_visitor_departed, PLUGIN_ID)
    bus.register("influence_spent", on_influence_spent, PLUGIN_ID)
    bus.register("summoning_failed", on_summoning_failed, PLUGIN_ID)
    bus.register("card_drawn", on_card_drawn, PLUGIN_ID)

    print("[event_logger] Now watching. All significant events will be recorded.")


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
