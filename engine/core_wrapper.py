"""Wrapper around the Rust core."""
import json
import os
import sys

# Try to import the compiled extension
try:
    # When running from repo root
    import anthill_core
except ImportError:
    # Try looking in the target directory
    lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "anthill-core/target/release")
    sys.path.append(lib_path)
    try:
        import anthill_core
    except ImportError:
        # Fallback for when running in different environments
        # Note: In production, the .so/.pyd should be installed in site-packages
        # or alongside the python files
        try:
            # Look for anthill_core.so in the current directory (where main.py might be running)
            sys.path.append(os.getcwd())
            import anthill_core
        except ImportError:
            print("WARNING: Could not import anthill_core Rust extension. Falling back to what? (Panic)")
            raise

class CoreEngine:
    """Wrapper for the Rust TickEngine."""

    def __init__(self, seed: int = 42):
        self._engine = anthill_core.PyTickEngine(seed)

    def tick(self, state_json: str) -> tuple[str, list]:
        """Run one tick.

        Args:
            state_json: JSON string representation of the game state.

        Returns:
            Tuple of (new_state_json, events_list)
        """
        # Load state into Rust
        # Note: In a real efficient implementation, we would keep the state in Rust
        # and only pass inputs/outputs. But the current Python architecture expects
        # to hold the state as a dict.
        #
        # OPTIMIZATION: We are converting JSON -> Rust -> JSON every tick.
        # This is fine for 1 tick/sec, but if we want 1000s/sec we need to refactor
        # to keep state in Rust.

        state = anthill_core.PyGameState.from_json(state_json)

        # Run tick
        events_json = self._engine.tick(state)

        # Get new state back
        new_state_json = state.to_json()

        return new_state_json, json.loads(events_json)

class StateManager:
    """Wrapper for Rust GameState."""

    @staticmethod
    def create_default() -> str:
        state = anthill_core.PyGameState()
        return state.to_json()

    @staticmethod
    def validate(state_json: str) -> bool:
        try:
            anthill_core.PyGameState.from_json(state_json)
            return True
        except ValueError:
            return False
