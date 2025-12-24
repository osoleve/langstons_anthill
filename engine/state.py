"""State management. Load, save, initialize."""

import json
import time
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent / "state" / "game.json"


def initial_state() -> dict:
    """Fresh game state."""
    return {
        "tick": 0,
        "resources": {},
        "systems": {},
        "entities": [],
        "map": {
            "tiles": {
                "origin": {
                    "name": "The Starting Dirt",
                    "type": "empty",
                    "x": 0,
                    "y": 0
                }
            },
            "connections": []
        },
        "queues": {
            "actions": [],
            "events": []
        },
        "meta": {
            "boredom": 0,
            "recent_decisions": [],
            "rejected_ideas": [],
            "sanity": 100.0,
            "fired_cards": [],
            "decor": [],
            "jewelry": [],
            "goals": {},
            "reflections": []
        }
    }


def load_state() -> dict:
    """Load state from disk, or initialize if missing."""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return initial_state()


def save_state(state: dict):
    """Persist state to disk with timestamp using atomic write.

    Writes to a temp file first, then renames to avoid corruption
    from concurrent reads or interrupted writes.
    """
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["last_save_timestamp"] = time.time()

    # Write to temp file first
    temp_file = STATE_FILE.with_suffix('.json.tmp')
    with open(temp_file, 'w') as f:
        json.dump(state, f, indent=2)
        f.flush()  # Ensure data is written to OS buffer

    # Atomic rename (on most filesystems)
    temp_file.replace(STATE_FILE)


def reset_state():
    """Start over."""
    state = initial_state()
    save_state(state)
    return state
