"""State management. Load, save, initialize."""

import json
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
            "rejected_ideas": []
        }
    }


def load_state() -> dict:
    """Load state from disk, or initialize if missing."""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return initial_state()


def save_state(state: dict):
    """Persist state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def reset_state():
    """Start over."""
    state = initial_state()
    save_state(state)
    return state
