"""Event bus. Everything interesting happens through events."""

from collections import defaultdict
from typing import Callable, Any


class EventBus:
    def __init__(self):
        self.handlers = defaultdict(list)

    def register(self, event_type: str, handler: Callable, plugin_id: str):
        """Register a handler for an event type."""
        self.handlers[event_type].append((plugin_id, handler))

    def unregister(self, plugin_id: str):
        """Remove all handlers for a plugin."""
        for event_type in self.handlers:
            self.handlers[event_type] = [
                (pid, h) for pid, h in self.handlers[event_type]
                if pid != plugin_id
            ]

    def emit(self, event_type: str, payload: dict) -> list[Any]:
        """Emit an event to all registered handlers. Returns list of results."""
        results = []
        for plugin_id, handler in self.handlers[event_type]:
            try:
                result = handler(payload)
                if result is not None:
                    results.append((plugin_id, result))
            except Exception as e:
                print(f"[bus] handler {plugin_id} failed on {event_type}: {e}")
        return results

    def list_handlers(self) -> dict:
        """Debug: show what's registered."""
        return {
            event_type: [pid for pid, _ in handlers]
            for event_type, handlers in self.handlers.items()
            if handlers
        }


# Global bus instance
bus = EventBus()
