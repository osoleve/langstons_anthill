"""Contributions plugin. Processes queued goal contributions from observers.

Observers use the /contribute endpoint to queue resource contributions to goals.
This plugin processes those contributions safely within the tick loop.
"""

import json
from pathlib import Path

PLUGIN_ID = "contributions"

CONTRIBUTIONS_FILE = Path(__file__).parent.parent / "state" / "contributions.json"

_bus = None


def load_contributions() -> list:
    """Load pending contributions."""
    if not CONTRIBUTIONS_FILE.exists():
        return []
    try:
        with open(CONTRIBUTIONS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("contributions", [])
    except (json.JSONDecodeError, IOError):
        return []


def clear_contributions():
    """Clear processed contributions."""
    with open(CONTRIBUTIONS_FILE, 'w') as f:
        json.dump({"contributions": []}, f)


def on_tick(payload: dict):
    """Process queued contributions."""
    from engine.state import load_state, save_state

    contributions = load_contributions()
    if not contributions:
        return

    state = load_state()
    goals = state.get("meta", {}).get("goals", {})
    resources = state.get("resources", {})

    processed = 0
    for contrib in contributions:
        goal_id = contrib.get("goal_id")
        resource = contrib.get("resource")
        amount = contrib.get("amount", 1)

        goal = goals.get(goal_id)
        if not goal or goal.get("built"):
            continue

        cost = goal.get("cost", {})
        if resource not in cost:
            continue

        # Check available resources
        available = resources.get(resource, 0)
        required = cost[resource]
        current_progress = goal.get("progress", {}).get(resource, 0)
        remaining = required - current_progress

        # Clamp contribution
        actual_amount = min(amount, available, remaining)

        if actual_amount <= 0:
            continue

        # Apply contribution
        resources[resource] -= actual_amount
        if "progress" not in goal:
            goal["progress"] = {}
        goal["progress"][resource] = current_progress + actual_amount
        processed += 1

        print(f"[contributions] {actual_amount:.1f} {resource} -> {goal.get('name', goal_id)}")

        # Check if goal is now complete
        all_complete = True
        for res, req in cost.items():
            if goal["progress"].get(res, 0) < req:
                all_complete = False
                break

        if all_complete:
            goal["built"] = True
            print(f"[contributions] GOAL COMPLETE: {goal.get('name', goal_id)}!")
            _bus.emit("goal_complete", {
                "tick": state["tick"],
                "goal_id": goal_id,
                "goal_name": goal.get("name", goal_id)
            })

    if processed > 0:
        state["resources"] = resources
        save_state(state)

    # Clear processed contributions
    clear_contributions()


def register(bus, state):
    """Register handlers."""
    global _bus
    _bus = bus
    bus.register("tick", on_tick, PLUGIN_ID)
    print("[contributions] Ready to process goal contributions")


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
