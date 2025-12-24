"""Tick engine. Runs forever. No LLM calls in the hot loop."""

import time
import json
from .state import load_state, save_state
from .bus import bus
from .core_wrapper import CoreEngine, StateManager


def process_offline_progress(state_dict: dict, engine: CoreEngine) -> dict:
    """Apply catch-up ticks for time passed while offline.

    Caps at 3600 ticks (1 hour) to prevent massive state jumps.
    """
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
    print("[tick] engine starting (Rust Core)")

    # Initialize Rust engine
    # Use current time as seed
    engine = CoreEngine(int(time.time()))

    # Load initial state
    state_dict = load_state()

    # Validate and repair state if needed
    try:
        # Check if we can round-trip through Rust
        state_json = json.dumps(state_dict)
        if not StateManager.validate(state_json):
             print("[tick] WARNING: Loaded state is not compatible with Rust core. Starting fresh.")
             state_dict = json.loads(StateManager.create_default())
    except Exception as e:
        print(f"[tick] ERROR loading state: {e}. Starting fresh.")
        state_dict = json.loads(StateManager.create_default())

    # Apply offline progress
    state_dict = process_offline_progress(state_dict, engine)
    save_state(state_dict)

    state_json = json.dumps(state_dict)

    tick_count = 0
    state_dict = None  # Only parse when needed

    while True:
        loop_start = time.time()

        # Run tick in Rust
        try:
            state_json, events = engine.tick(state_json)
        except Exception as e:
            print(f"[tick] CRITICAL ERROR in Rust core: {e}")
            time.sleep(1)
            continue

        # Emit events from Rust (lightweight, no state parsing needed)
        for event in events:
            event_type = event.get("type", "unknown_event")
            bus.emit(event_type, event)

        # Only parse state when we need to save or emit tick events
        # Parse once and reuse for both operations when needed
        should_save = tick_count % 50 == 0
        should_emit_tick = True  # Could optimize this based on handler registration

        if should_save or should_emit_tick:
            state_dict = json.loads(state_json)
            state_dict["last_save_timestamp"] = time.time()

            if should_save:
                save_state(state_dict)

            if should_emit_tick:
                bus.emit("tick", state_dict)

            # Update state_json with timestamp for next iteration
            state_json = json.dumps(state_dict)

        tick_count += 1

        # Sleep to maintain 1 tick/second
        elapsed = time.time() - loop_start
        sleep_time = max(0.0, 1.0 - elapsed)
        time.sleep(sleep_time)


if __name__ == "__main__":
    run()
