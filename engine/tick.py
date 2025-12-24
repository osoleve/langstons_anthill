"""Tick engine. Runs forever. No LLM calls in the hot loop."""

import time
import json
from .state import load_state, save_state
from .bus import bus

# Try Rust core, fallback to Python-only
USE_RUST_CORE = True
try:
    from .core_wrapper import CoreEngine, StateManager
except ImportError:
    USE_RUST_CORE = False
    print("[tick] Rust core not available, using Python-only mode")


def python_tick(state: dict) -> tuple[dict, list]:
    """Pure Python tick implementation (fallback when Rust can't handle state).

    This is simpler than Rust - just increments tick and applies basic entity aging.
    Plugins handle most game logic anyway.
    """
    state["tick"] += 1
    events = []

    # Age entities
    surviving = []
    for entity in state.get("entities", []):
        entity["age"] = entity.get("age", 0) + 1

        # Check hunger
        hunger = entity.get("hunger", 100)
        hunger_rate = entity.get("hunger_rate", 0.1)
        entity["hunger"] = hunger - hunger_rate

        # Check death
        max_age = entity.get("max_age", 7200)
        died = False
        cause = None

        if entity["hunger"] <= 0:
            died = True
            cause = "starvation"
        elif entity["age"] >= max_age:
            died = True
            cause = "old_age"

        if died:
            events.append({
                "type": "entity_death",
                "entity_id": entity["id"],
                "cause": cause,
                "tick": state["tick"]
            })
        else:
            surviving.append(entity)

    state["entities"] = surviving

    # Increment boredom
    meta = state.setdefault("meta", {})
    meta["boredom"] = meta.get("boredom", 0) + 1

    return state, events


def process_offline_progress(state_dict: dict, engine) -> dict:
    """Apply catch-up ticks for time passed while offline.

    Caps at 3600 ticks (1 hour) to prevent massive state jumps.
    """
    # TEMPORARILY DISABLED - offline progress was destroying state
    print("[tick] offline progress DISABLED for debugging")
    return state_dict

    last_save = state_dict.get("last_save_timestamp")
    if not last_save:
        print("[tick] no previous timestamp, skipping offline progress")
        return state_dict

    elapsed_seconds = int(time.time() - last_save)
    if elapsed_seconds <= 0:
        return state_dict

    # Cap at 1 hour of offline progress
    max_offline_ticks = 3600
    ticks_to_apply = min(elapsed_seconds, max_offline_ticks)

    if ticks_to_apply < 10:  # Skip if trivial
        return state_dict

    print(f"[tick] applying {ticks_to_apply} offline ticks ({elapsed_seconds}s elapsed, capped at {max_offline_ticks})")

    # Run ticks in a loop
    # We don't emit events during catch-up to avoid flooding the bus/logs
    # But we do need to update the state

    state_json = json.dumps(state_dict)

    # Process in batches to avoid locking up too long if it's slow (though Rust is fast)
    batch_size = 100
    total_processed = 0

    start_time = time.time()

    while total_processed < ticks_to_apply:
        current_batch = min(batch_size, ticks_to_apply - total_processed)

        for _ in range(current_batch):
            state_json, _ = engine.tick(state_json)

        total_processed += current_batch

    duration = time.time() - start_time
    print(f"[tick] offline progress complete. Processed {total_processed} ticks in {duration:.3f}s")

    return json.loads(state_json)


def run():
    """Main loop. 1 tick = 1 second."""
    # Load initial state
    state_dict = load_state()
    print(f"[tick] State tick: {state_dict.get('tick')}", flush=True)
    print(f"[tick] State has {len(state_dict.get('entities', []))} entities", flush=True)

    # Try to use Rust core, fall back to Python if it can't handle the state
    use_rust = USE_RUST_CORE
    engine = None

    if use_rust:
        try:
            state_json = json.dumps(state_dict)
            valid = StateManager.validate(state_json)
            if valid:
                engine = CoreEngine(int(time.time()))
                print("[tick] Using Rust Core", flush=True)
            else:
                use_rust = False
                print("[tick] State not Rust-compatible, using Python mode", flush=True)
        except Exception as e:
            use_rust = False
            print(f"[tick] Rust validation failed ({e}), using Python mode", flush=True)
    else:
        print("[tick] Using Python-only mode", flush=True)

    save_state(state_dict)

    tick_count = 0

    while True:
        loop_start = time.time()

        # Run tick (Rust or Python)
        try:
            if use_rust and engine:
                state_json = json.dumps(state_dict) if state_dict else state_json
                state_json, events = engine.tick(state_json)
                state_dict = json.loads(state_json)
            else:
                # Python-only mode
                if state_dict is None:
                    state_dict = load_state()
                state_dict, events = python_tick(state_dict)
        except Exception as e:
            print(f"[tick] CRITICAL ERROR: {e}")
            time.sleep(1)
            continue

        # Emit events
        for event in events:
            event_type = event.get("type", "unknown_event")
            bus.emit(event_type, event)

        # Always keep state_dict updated and emit tick for plugins
        state_dict["last_save_timestamp"] = time.time()

        # Save every 50 ticks
        if tick_count % 50 == 0:
            save_state(state_dict)

        # Emit tick event for plugins
        bus.emit("tick", state_dict)

        tick_count += 1

        # Sleep to maintain 1 tick/second
        elapsed = time.time() - loop_start
        sleep_time = max(0.0, 1.0 - elapsed)
        time.sleep(sleep_time)


if __name__ == "__main__":
    run()
