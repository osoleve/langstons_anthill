"""Simulation helpers. Advance time without waiting."""

from .state import load_state, save_state
from .bus import bus
from .tick import apply_tick, check_thresholds, check_boredom


def advance(ticks: int = 1, verbose: bool = True):
    """Advance the game by N ticks instantly."""
    for i in range(ticks):
        prev_state = load_state()
        state = load_state()

        state = apply_tick(state)
        save_state(state)

        # Emit events
        bus.emit("tick", state)
        check_thresholds(state, prev_state)
        check_boredom(state)

        if verbose and (i + 1) % 10 == 0:
            print(f"[sim] tick {state['tick']}")

    final_state = load_state()
    if verbose:
        print(f"[sim] advanced to tick {final_state['tick']}")
        if final_state['resources']:
            print(f"[sim] resources: {final_state['resources']}")
        if final_state['queues']['actions']:
            print(f"[sim] actions: {[a['name'] for a in final_state['queues']['actions']]}")

    return final_state


def fast_forward(ticks: int = 1, verbose: bool = True):
    """Fast simulation - no events, minimal I/O. For long grinds."""
    state = load_state()

    for i in range(ticks):
        state = apply_tick(state)
        if verbose and (i + 1) % 1000 == 0:
            print(f"[ff] tick {state['tick']}")

    save_state(state)

    if verbose:
        print(f"[ff] fast-forwarded to tick {state['tick']}")
        if state['resources']:
            print(f"[ff] resources: {state['resources']}")

    return state


def status():
    """Print current game status."""
    state = load_state()
    print(f"Tick: {state['tick']}")
    print(f"Resources: {state['resources']}")
    print(f"Systems: {list(state['systems'].keys())}")
    actions_str = [a['name'] + ' (' + str(a['ticks_remaining']) + 't)' for a in state['queues']['actions']]
    print(f"Actions: {actions_str}")
    print(f"Tiles: {list(state['map']['tiles'].keys())}")
    print(f"Boredom: {state['meta']['boredom']}")
    return state
