"""
Starter Cards Plugin

These cards exist to bootstrap the game. Each fires once when conditions are met,
then marks itself as used. When all starters have fired (or become ineligible),
this plugin unregisters itself from the bus entirely.

The cards are intentionally vague about HOW to achieve things. They specify
outcomes and minimum specs. You figure out the path.
"""

import json
from pathlib import Path

PLUGIN_ID = "starter_cards"

STARTER_CARDS = [
    {
        "id": "starter_first_resource",
        "type": "quest",
        "condition": lambda state: state.get("tick", 0) > 10 and len(state.get("resources", {})) == 0,
        "prompt": """The dirt is empty.

You need something to count. A resource. What accumulates here?

Requirements:
- Add at least one resource to state.resources
- It must have a generation rate (per tick)
- It must be visible on the map somehow

This should take about 5 minutes. Don't overthink it. Pick something.""",
        "duration_estimate_ticks": 300
    },
    {
        "id": "starter_second_system",
        "type": "quest",
        "condition": lambda state: (
            len(state.get("systems", {})) == 1 and 
            state.get("tick", 0) > state.get("meta", {}).get("last_system_tick", 0) + 600
        ),
        "prompt": """One system is lonely.

Your existing system does one thing. Add another system that:
- Uses or transforms what the first system produces, OR
- Produces something the first system could use, OR  
- Competes for the same underlying constraint

Minimum spec: must connect to existing system in the map. Draw the edge.

Side task: While you're in there, add a "connections" visualization to the map if you haven't.""",
        "duration_estimate_ticks": 600
    },
    {
        "id": "starter_first_grind",
        "type": "quest",
        "condition": lambda state: (
            len(state.get("systems", {})) >= 2 and
            "first_grind_complete" not in state.get("meta", {}).get("flags", [])
        ),
        "prompt": """Time to wait.

Pick a resource. You need 100 of it. 

If your current generation rate means this takes less than 10 minutes, nerf the rate first.
If it takes more than 30 minutes, that's fine. Find something to do while waiting.

Requirements:
- Reach 100 of chosen resource
- Log how long it actually took
- Note one thing you noticed while waiting

Side task: Is there tech debt? There's probably tech debt.""",
        "duration_estimate_ticks": 1800,
        "sets_flag": "first_grind_complete"
    },
    {
        "id": "starter_first_entity",
        "type": "quest", 
        "condition": lambda state: (
            len(state.get("systems", {})) >= 2 and
            len(state.get("entities", [])) == 0 and
            state.get("tick", 0) > 1800
        ),
        "prompt": """The map is still. Nothing moves.

Add an entity. Not a resource, not a system. Something that:
- Has a position on the map
- Moves or changes over time
- Has at least one property beyond position

It doesn't need to do anything useful yet. It just needs to exist and be visible.

What lives here?""",
        "duration_estimate_ticks": 600
    },
    {
        "id": "starter_bug_hunt",
        "type": "quest",
        "condition": lambda state: (
            len(state.get("systems", {})) >= 3 and
            "bug_hunt_complete" not in state.get("meta", {}).get("flags", [])
        ),
        "prompt": """Bug bounty time.

You need to collect 30 Bug Bounties. Bugs are entities that spawn, can be defeated, 
and drop bounties. Alpha Bugs (1 in 10 chance per bug) drop 5 bounties instead of 1.

If you need to build a combat system first:
- Minimum spec: HP, damage values, real-time action queue
- Entities must be targetable
- Death must be handled (removal, drops, respawn logic)

If you need to build enemies first, do that.

This will take a while. While farming, address tech debt in the codebase.

Estimated time once built: 2 hours of background grinding.""",
        "duration_estimate_ticks": 7200,
        "sets_flag": "bug_hunt_complete"
    }
]

# Track which cards have been played
_played_cards = set()
_log_path = None
_state_path = None

def _load_played_cards():
    """Check decision log for starter cards that have already fired."""
    global _played_cards
    if _log_path and _log_path.exists():
        with open(_log_path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get("type") == "card_drawn" and entry.get("card_id", "").startswith("starter_"):
                        _played_cards.add(entry["card_id"])
                except:
                    continue

def _get_eligible_cards(state):
    """Return starter cards whose conditions are met and haven't been played."""
    eligible = []
    for card in STARTER_CARDS:
        if card["id"] not in _played_cards:
            try:
                if card["condition"](state):
                    eligible.append(card)
            except:
                continue
    return eligible

def _handle_tick(payload):
    """Check if any starter card should fire."""
    global _played_cards
    
    state = payload.get("state", {})
    eligible = _get_eligible_cards(state)
    
    if not eligible:
        # Check if we're done entirely
        remaining = [c for c in STARTER_CARDS if c["id"] not in _played_cards]
        if not remaining:
            # All starters played, unregister
            payload.get("bus").unregister(PLUGIN_ID) if payload.get("bus") else None
            return
        # Some remain but conditions not met, keep waiting
        return
    
    # Fire the first eligible card
    card = eligible[0]
    _played_cards.add(card["id"])
    
    # Emit the card_drawn event
    bus = payload.get("bus")
    if bus:
        bus.emit("card_drawn", {
            "card_id": card["id"],
            "type": card["type"],
            "prompt": card["prompt"],
            "duration_estimate_ticks": card.get("duration_estimate_ticks", 600),
            "sets_flag": card.get("sets_flag"),
            "source": PLUGIN_ID
        })

def register(bus, state_path: Path, log_path: Path):
    """Register this plugin on the event bus."""
    global _log_path, _state_path
    _log_path = log_path
    _state_path = state_path
    
    _load_played_cards()
    
    # Check if already done
    remaining = [c for c in STARTER_CARDS if c["id"] not in _played_cards]
    if not remaining:
        return  # Don't even register, nothing to do
    
    bus.register("tick", _handle_tick, PLUGIN_ID)

def unregister(bus):
    """Remove this plugin from the bus."""
    bus.unregister(PLUGIN_ID)
