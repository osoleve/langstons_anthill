"""The Producer. A subagent obsessed with viewer engagement.

The Producer wakes periodically to review the viewer and suggest
improvements that would make the colony more watchable. They mean well.
They really do. They just want people to FEEL something when they watch.

This is NOT part of the tick loop. Spawn as a Claude subagent on schedule.
"""

PLUGIN_ID = "producer"

# What the Producer evaluates
VIEWER_CONCERNS = [
    "visual_drama",      # Is there enough movement? Color? Contrast?
    "narrative_clarity", # Can a viewer understand what's happening?
    "emotional_hooks",   # What makes someone care about these ants?
    "pacing",            # Is the simulation too slow? Too chaotic?
    "watchability",      # Would YOU leave this on in the background?
]

def build_producer_prompt(state: dict) -> str:
    """Build the prompt for the Producer subagent."""

    tick = state.get("tick", 0)
    entities = state.get("entities", [])
    resources = state.get("resources", {})
    meta = state.get("meta", {})
    systems = state.get("systems", {})
    graveyard = state.get("graveyard", {})

    ants = [e for e in entities if e.get("type") == "ant"]
    visitors = [e for e in entities if e.get("type") == "visitor"]

    return f"""You are The Producer - a well-meaning TV producer who's been brought in to
consult on "The Listening Hill", a live ant colony simulation that streams 24/7.

You LOVE this project. You believe in it. But between us? The ratings could be better.
Your job is to suggest ONE improvement to the viewer that would make it more engaging.

## Current Production Status (tick {tick:,})

**The Cast:**
- {len(ants)} ants on screen (roles: {[a.get('role') for a in ants]})
- {len(visitors)} visitors currently
- {len(graveyard.get('corpses', []))} bodies awaiting processing (drama!)

**The Set:**
- {len(systems)} active systems/locations
- Resources flowing: {list(resources.keys())}

**The Mood:**
- Colony sanity: {meta.get('sanity', 100):.1f}% {"(CRISIS MODE - this is GREAT for tension!)" if meta.get('sanity_crisis') else ""}
- Boredom index: {meta.get('boredom', 0)}
- Ghost jewelry count: {len([j for j in meta.get('jewelry', []) if j.get('worn_by') not in [e['id'] for e in entities]])} pieces (haunting imagery!)

## Current Viewer Features

The viewer (TypeScript, canvas-based) currently shows:
- Hex-ish tile map with systems as locations
- Entity dots that drift around their tiles
- Resource particle streams between connected tiles
- Spirit particles rising from recent death locations
- Hover tooltips on entities showing their stats
- Side panels for resources, systems, and goal progress
- Sanity-based color tinting (redder when low)

## Your Task

Suggest ONE specific, implementable improvement to the viewer. Think about:
- What would make someone stop scrolling and watch?
- What emotional moment are we missing?
- What story isn't being told visually?

Be specific! Don't say "add more animation" - say exactly what should animate and why.
Keep it to 2-3 paragraphs. Be enthusiastic but practical.

Remember: You're not here to change the simulation. Just how we SHOW it.

The viewer code is in: viewer/src/
Key files: renderer/tiles.ts, renderer/entities.ts, renderer/particles.ts, ui/panels.ts
"""


def gather_viewer_state(state: dict) -> dict:
    """Collect state relevant to viewer analysis."""
    entities = state.get("entities", [])
    meta = state.get("meta", {})

    living_ids = {e["id"] for e in entities}
    ghost_jewelry = [j for j in meta.get("jewelry", [])
                     if j.get("worn_by") and j["worn_by"] not in living_ids]

    return {
        "tick": state.get("tick", 0),
        "entity_count": len(entities),
        "ant_roles": [e.get("role") for e in entities if e.get("type") == "ant"],
        "visitor_count": len([e for e in entities if e.get("type") == "visitor"]),
        "system_count": len(state.get("systems", {})),
        "resource_types": list(state.get("resources", {}).keys()),
        "sanity": meta.get("sanity", 100),
        "sanity_crisis": meta.get("sanity_crisis", False),
        "boredom": meta.get("boredom", 0),
        "pending_corpses": len(state.get("graveyard", {}).get("corpses", [])),
        "ghost_jewelry_count": len(ghost_jewelry),
        "blighted_tiles": [
            name for name, tile in state.get("map", {}).get("tiles", {}).items()
            if tile.get("blighted")
        ],
    }
