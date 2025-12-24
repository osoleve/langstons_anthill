"""Tick engine. Runs forever. No LLM calls in the hot loop."""

import time
from .state import load_state, save_state
from .bus import bus


def apply_tick(state: dict) -> dict:
    """Pure math. No thinking. Process one tick."""
    state["tick"] += 1

    # Process action queue
    remaining_actions = []
    for action in state["queues"]["actions"]:
        action["ticks_remaining"] -= 1
        if action["ticks_remaining"] <= 0:
            # Action complete - emit event
            bus.emit("action_complete", {
                "action": action,
                "tick": state["tick"]
            })
            # Apply action effects
            if "effects" in action:
                for resource, delta in action["effects"].get("resources", {}).items():
                    state["resources"][resource] = state["resources"].get(resource, 0) + delta
        else:
            remaining_actions.append(action)
    state["queues"]["actions"] = remaining_actions

    # Process passive resource generation/consumption from systems
    for system_id, system in state["systems"].items():
        # Check if system can run (has required resources to consume)
        can_run = True
        if "consumes" in system:
            for resource, rate in system["consumes"].items():
                if state["resources"].get(resource, 0) < rate:
                    can_run = False
                    break

        if can_run:
            # Consume resources
            if "consumes" in system:
                for resource, rate in system["consumes"].items():
                    state["resources"][resource] = state["resources"].get(resource, 0) - rate

            # Generate resources
            if "generates" in system:
                for resource, rate in system["generates"].items():
                    state["resources"][resource] = state["resources"].get(resource, 0) + rate

    # Process entities
    surviving_entities = []
    for entity in state["entities"]:
        entity["age"] = entity.get("age", 0) + 1

        # Hunger decreases over time
        entity["hunger"] = entity.get("hunger", 100) - entity.get("hunger_rate", 0.1)

        # Try to eat if hungry
        if entity["hunger"] < 50:
            food_type = entity.get("food", "fungus")
            if state["resources"].get(food_type, 0) >= 1:
                state["resources"][food_type] -= 1
                entity["hunger"] = min(100, entity["hunger"] + 30)
                bus.emit("entity_ate", {"entity": entity, "food": food_type, "tick": state["tick"]})

        # Check for death
        max_age = entity.get("max_age", 3600)  # 1 hour default lifespan
        died = False
        cause = None

        if entity["hunger"] <= 0:
            died = True
            cause = "starvation"
        elif entity["age"] >= max_age:
            died = True
            cause = "old_age"

        if died:
            # Add to graveyard directly (pure state mutation)
            if "graveyard" not in state:
                state["graveyard"] = {"corpses": [], "total_processed": 0}
            state["graveyard"]["corpses"].append({
                "entity_id": entity.get("id", "unknown"),
                "entity_type": entity.get("type", "unknown"),
                "death_tick": state["tick"],
                "cause": cause,
                "tile": entity.get("tile", "origin")
            })
            bus.emit("entity_died", {"entity": entity, "cause": cause, "tick": state["tick"]})
        else:
            surviving_entities.append(entity)

    state["entities"] = surviving_entities

    return state


def check_thresholds(state: dict, prev_state: dict):
    """Emit threshold events when metrics cross boundaries."""
    # Check resource thresholds
    for resource, amount in state["resources"].items():
        prev_amount = prev_state.get("resources", {}).get(resource, 0)
        # Check common thresholds: 10, 25, 50, 100, 250, 500, 1000
        for threshold in [10, 25, 50, 100, 250, 500, 1000]:
            if prev_amount < threshold <= amount:
                bus.emit("threshold", {
                    "type": "resource",
                    "resource": resource,
                    "threshold": threshold,
                    "tick": state["tick"]
                })


def check_boredom(state: dict):
    """Detect stalls. Emit boredom events."""
    meta = state["meta"]

    # Increase boredom if nothing's happening
    if not state["queues"]["actions"] and not state["queues"]["events"]:
        meta["boredom"] = meta.get("boredom", 0) + 1
    else:
        meta["boredom"] = max(0, meta.get("boredom", 0) - 1)

    # Emit if boredom is high
    if meta["boredom"] >= 60:  # 1 minute of nothing
        bus.emit("boredom", {
            "level": meta["boredom"],
            "tick": state["tick"]
        })
        meta["boredom"] = 0  # Reset after emitting


def process_offline_progress(state: dict) -> dict:
    """Apply catch-up ticks for time passed while offline.

    Caps at 3600 ticks (1 hour) to prevent massive state jumps.
    Applies simplified tick logic (resources only, no entity deaths).
    """
    import time

    last_save = state.get("last_save_timestamp")
    if not last_save:
        print("[tick] no previous timestamp, skipping offline progress")
        return state

    elapsed_seconds = int(time.time() - last_save)
    if elapsed_seconds <= 0:
        return state

    # Cap at 1 hour of offline progress
    max_offline_ticks = 3600
    ticks_to_apply = min(elapsed_seconds, max_offline_ticks)

    if ticks_to_apply < 10:  # Skip if trivial
        return state

    print(f"[tick] applying {ticks_to_apply} offline ticks ({elapsed_seconds}s elapsed, capped at {max_offline_ticks})")

    # Apply simplified ticks (resource generation only, no entity processing)
    for _ in range(ticks_to_apply):
        state["tick"] += 1

        # Process passive resource generation/consumption from systems
        for system_id, system in state["systems"].items():
            can_run = True
            if "consumes" in system:
                for resource, rate in system["consumes"].items():
                    if state["resources"].get(resource, 0) < rate:
                        can_run = False
                        break

            if can_run:
                if "consumes" in system:
                    for resource, rate in system["consumes"].items():
                        state["resources"][resource] = state["resources"].get(resource, 0) - rate
                if "generates" in system:
                    for resource, rate in system["generates"].items():
                        state["resources"][resource] = state["resources"].get(resource, 0) + rate

        # Process entity hunger (reduced rate - they forage while you're away)
        for entity in state["entities"]:
            # Age normally
            entity["age"] = entity.get("age", 0) + 1
            # Hunger decreases at half rate offline (foraging bonus)
            entity["hunger"] = entity.get("hunger", 100) - (entity.get("hunger_rate", 0.1) * 0.5)
            # Auto-eat if hungry and food available
            if entity["hunger"] < 50:
                food_type = entity.get("food", "fungus")
                if state["resources"].get(food_type, 0) >= 1:
                    state["resources"][food_type] -= 1
                    entity["hunger"] = min(100, entity["hunger"] + 30)

        # Remove entities that died offline
        state["entities"] = [e for e in state["entities"] if e.get("hunger", 100) > 0 and e.get("age", 0) < e.get("max_age", 7200)]

    print(f"[tick] offline progress complete. Now at tick {state['tick']}")
    return state


def run():
    """Main loop. 1 tick = 1 second."""
    print("[tick] engine starting")

    # Process any offline progress before starting main loop
    state = load_state()
    state = process_offline_progress(state)
    save_state(state)

    # Keep state in memory, only save periodically

    while True:
        prev_state = {k: v for k, v in state.items()}  # Shallow copy for comparison
        prev_state["resources"] = dict(state.get("resources", {}))

        state = apply_tick(state)

        # Save every 50 ticks to reduce I/O
        if state["tick"] % 50 == 0:
            save_state(state)

        # Emit tick event
        bus.emit("tick", state)

        # Check for threshold crossings
        check_thresholds(state, prev_state)

        # Check for boredom
        check_boredom(state)

        time.sleep(1)


if __name__ == "__main__":
    run()
