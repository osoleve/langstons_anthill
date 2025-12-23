"""Main entry point. Runs the tick engine with plugins loaded."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from engine.state import load_state, save_state, initial_state, STATE_FILE
from engine.bus import bus
from plugins.loader import load_all_plugins
from engine.tick import run


def main():
    # Initialize state if needed
    if not STATE_FILE.exists():
        print("[main] initializing fresh state")
        save_state(initial_state())

    # Load plugins
    print("[main] loading plugins")
    plugins = load_all_plugins()
    print(f"[main] loaded {len(plugins)} plugins: {plugins}")

    # Show registered handlers
    handlers = bus.list_handlers()
    print(f"[main] event handlers: {handlers}")

    # Run the engine
    print("[main] starting tick engine")
    run()


if __name__ == "__main__":
    main()
