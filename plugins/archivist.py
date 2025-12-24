"""The Archivist. A subagent that maintains the colony's documentation.

The Archivist wakes periodically to observe the colony's state and update
the wiki/documentation with small, incremental entries. It writes what it
sees - not what should be, but what is.

This is NOT part of the tick loop. It runs as a separate scheduled task
that spawns a Claude subagent to make documentation updates.
"""

import json
from pathlib import Path
from datetime import datetime

PLUGIN_ID = "archivist"

# Archivist schedule
ARCHIVE_INTERVAL_TICKS = 1800  # Every 30 minutes
MIN_TICKS_BETWEEN_RUNS = 600   # At least 10 minutes between runs

# What the Archivist observes
OBSERVATION_CATEGORIES = [
    "population",      # Entity counts, roles, notable individuals
    "resources",       # Resource levels, trends, scarcity
    "events",          # Recent deaths, births, visitors, cards
    "systems",         # Active systems, efficiency, blight
    "goals",           # Progress toward goals, blockers
    "mood",            # Sanity, boredom, crisis states
]

_bus = None
_last_archive_tick = 0

def gather_observations(state: dict) -> dict:
    """Collect current state into an observation summary."""
    tick = state.get("tick", 0)

    # Population
    entities = state.get("entities", [])
    ants = [e for e in entities if e.get("type") == "ant"]
    visitors = [e for e in entities if e.get("type") == "visitor"]
    ornamentals = [e for e in ants if e.get("adorned")]

    # Resources
    resources = state.get("resources", {})

    # Recent events from event log
    event_log = state.get("meta", {}).get("event_log", [])[-10:]

    # Systems
    systems = state.get("systems", {})
    blighted_tiles = [
        name for name, tile in state.get("map", {}).get("tiles", {}).items()
        if tile.get("blighted")
    ]

    # Goals
    goals = state.get("meta", {}).get("goals", {})
    active_goals = {
        k: v for k, v in goals.items()
        if not v.get("built", False)
    }

    # Mood
    meta = state.get("meta", {})
    sanity = meta.get("sanity", 100)
    boredom = meta.get("boredom", 0)
    receiver_silent = meta.get("receiver_silent", False)

    # Graveyard
    graveyard = state.get("graveyard", {})
    corpses = graveyard.get("corpses", [])
    total_processed = graveyard.get("total_processed", 0)

    # Jewelry (including ghost jewelry)
    jewelry = meta.get("jewelry", [])
    living_ids = {e["id"] for e in entities}
    ghost_jewelry = [j for j in jewelry if j.get("worn_by") and j["worn_by"] not in living_ids]

    return {
        "tick": tick,
        "timestamp": datetime.utcnow().isoformat(),
        "population": {
            "total_ants": len(ants),
            "total_visitors": len(visitors),
            "ornamentals": len(ornamentals),
            "roles": {role: len([a for a in ants if a.get("role") == role])
                     for role in set(a.get("role") for a in ants)},
        },
        "resources": {k: round(v, 2) for k, v in resources.items()},
        "recent_events": event_log,
        "systems": {
            "count": len(systems),
            "blighted_tiles": blighted_tiles,
        },
        "goals": {
            k: {
                "name": v.get("name"),
                "progress": v.get("progress"),
                "cost": v.get("cost"),
            }
            for k, v in active_goals.items()
        },
        "mood": {
            "sanity": round(sanity, 1),
            "boredom": boredom,
            "receiver_silent": receiver_silent,
            "crisis": meta.get("sanity_crisis", False),
            "breaking": meta.get("sanity_breaking", False),
        },
        "death": {
            "pending_corpses": len(corpses),
            "total_processed": total_processed,
            "ghost_jewelry_count": len(ghost_jewelry),
        },
    }


def build_archivist_prompt(observations: dict) -> str:
    """Build the prompt for the Archivist subagent."""
    return f"""You are the Archivist of The Listening Hill, an ant colony simulation.

Your task: Make ONE small, focused update to the wiki documentation based on current observations.

## Current Colony State (tick {observations['tick']})

Population: {observations['population']['total_ants']} ants, {observations['population']['total_visitors']} visitors
Roles: {observations['population']['roles']}
Ornamentals: {observations['population']['ornamentals']}

Resources:
{json.dumps(observations['resources'], indent=2)}

Mood:
- Sanity: {observations['mood']['sanity']}%
- Boredom: {observations['mood']['boredom']}
- Receiver silent: {observations['mood']['receiver_silent']}
- Crisis: {observations['mood']['crisis']}

Active Goals:
{json.dumps(observations['goals'], indent=2)}

Death:
- Pending corpses: {observations['death']['pending_corpses']}
- Total ever processed: {observations['death']['total_processed']}
- Ghost jewelry (rings on dead ants): {observations['death']['ghost_jewelry_count']}

Recent Events:
{json.dumps(observations['recent_events'], indent=2)}

## Your Task

Choose ONE of these update types:
1. **Timeline entry**: Add a brief entry to docs/journal.md noting a significant event
2. **Stat update**: Update a number in an existing doc (population, resource milestone)
3. **New observation**: Add a small observation to an appropriate doc
4. **Lore snippet**: Add flavor text about something interesting in the current state

Guidelines:
- Make ONE small change, not a rewrite
- Write in the colony's voice (first person plural "we")
- Be factual about what IS, not what should be
- Keep entries brief (1-3 sentences)
- If nothing notable has changed, write "No update needed" and exit

Find the docs/ directory, read the relevant file, and make your small update.
"""


def should_archive(state: dict) -> bool:
    """Check if it's time for the Archivist to wake."""
    global _last_archive_tick

    tick = state.get("tick", 0)

    # Check minimum interval
    if tick - _last_archive_tick < MIN_TICKS_BETWEEN_RUNS:
        return False

    # Check main schedule
    if tick - _last_archive_tick >= ARCHIVE_INTERVAL_TICKS:
        return True

    # Also wake on significant events
    meta = state.get("meta", {})

    # Wake if sanity just crossed into crisis
    if meta.get("sanity_crisis") and not meta.get("_archivist_noted_crisis"):
        return True

    # Wake if a visitor just arrived (check event log)
    event_log = meta.get("event_log", [])
    if event_log:
        last_event = event_log[-1]
        if last_event.get("type") == "visitor_arrival":
            if last_event.get("tick", 0) > _last_archive_tick:
                return True

    return False


def spawn_archivist_agent(observations: dict) -> None:
    """Spawn a Claude subagent to make documentation updates.

    This runs claude-code in a subprocess with a specific prompt.
    The agent has read/write access to the docs/ directory only.
    """
    prompt = build_archivist_prompt(observations)

    # Write prompt to temp file for the agent
    prompt_file = Path(__file__).parent.parent / "logs" / "archivist_prompt.txt"
    prompt_file.write_text(prompt)

    print(f"[archivist] Waking at tick {observations['tick']}...")
    print(f"[archivist] Observations written to {prompt_file}")

    # In a real implementation, this would spawn claude-code as a subprocess
    # For now, we just log that the archivist would run
    #
    # subprocess.Popen([
    #     "claude",
    #     "--prompt", prompt,
    #     "--allowedTools", "Read,Edit,Write,Glob",
    #     "--workdir", str(Path(__file__).parent.parent / "docs"),
    # ])

    print("[archivist] (Subagent spawn disabled - would update docs/)")


def on_tick(payload: dict):
    """Check if Archivist should wake and archive."""
    global _last_archive_tick
    from engine.state import load_state

    state = load_state()

    if not should_archive(state):
        return

    observations = gather_observations(state)
    spawn_archivist_agent(observations)

    _last_archive_tick = state.get("tick", 0)


def register(bus, state):
    """Register the Archivist."""
    global _bus, _last_archive_tick
    _bus = bus
    _last_archive_tick = state.get("tick", 0) - ARCHIVE_INTERVAL_TICKS + 300  # First run in 5 min
    bus.register("tick", on_tick, PLUGIN_ID)
    print("[archivist] The Archivist slumbers. It will wake to record what it sees.")


def unregister(bus):
    """Unregister the Archivist."""
    bus.unregister(PLUGIN_ID)
