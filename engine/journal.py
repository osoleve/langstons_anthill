"""Journal system. For contemplation, not optimization.

Unlike decisions (which log choices) or reflections (which prompt questions),
journal entries are free-form. They capture noticing, reconciliation, growth.

Journal entries imply:
- Reconciliation: processing what happened, understanding it
- Growth: taking that understanding forward, letting it shape you

No mechanical benefit. Just the practice of paying attention.
"""

import json
from datetime import datetime
from pathlib import Path


JOURNAL_PATH = Path("logs/journal.jsonl")


def write(entry: str, tags: list[str] = None, tick: int = None):
    """Write a journal entry.

    Args:
        entry: Free-form text, as long or short as needed
        tags: Optional themes/feelings (e.g., ["extinction", "stillness"])
        tick: Game tick (will be read from state if not provided)
    """
    if tick is None:
        from engine.state import load_state
        state = load_state()
        tick = state.get("tick", 0)

    journal_entry = {
        "tick": tick,
        "timestamp": datetime.utcnow().isoformat(),
        "entry": entry,
        "tags": tags or []
    }

    # Ensure journal file exists
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Append entry
    with open(JOURNAL_PATH, "a") as f:
        f.write(json.dumps(journal_entry) + "\n")

    print(f"[journal] recorded ({len(entry)} chars, {len(tags or [])} tags)")


def read_recent(limit: int = 10) -> list[dict]:
    """Read recent journal entries."""
    if not JOURNAL_PATH.exists():
        return []

    with open(JOURNAL_PATH, "r") as f:
        lines = f.readlines()

    entries = []
    for line in lines[-limit:]:
        try:
            entries.append(json.loads(line.strip()))
        except:
            pass

    return entries


def read_by_tags(tags: list[str]) -> list[dict]:
    """Read journal entries matching any of the given tags."""
    if not JOURNAL_PATH.exists():
        return []

    with open(JOURNAL_PATH, "r") as f:
        lines = f.readlines()

    entries = []
    for line in lines:
        try:
            entry = json.loads(line.strip())
            if any(tag in entry.get("tags", []) for tag in tags):
                entries.append(entry)
        except:
            pass

    return entries
