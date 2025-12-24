"""Sanity meter. Psychological pressure tracking.

The colony has a collective sanity - a measure of stress, fear, hope.
It decays when bad things happen. It recovers when goals are achieved.
At low sanity, systems begin to fail in subtle ways.
"""

PLUGIN_ID = "sanity"

# Sanity thresholds
SANITY_MAX = 100
SANITY_STABLE = 50
SANITY_CRISIS = 25
SANITY_BREAKING = 10

# Decay/recovery rates
PASSIVE_DECAY = 0.01  # Very slow ambient decay per tick
ISOLATION_DECAY = 0.5  # When Receiver is silent
DEATH_PENALTY = 5  # Per entity death
STARVATION_PENALTY = 2  # Per starvation event
FAILED_SUMMON_PENALTY = 3  # Per failed summoning
BLIGHT_PENALTY = 4  # Per blight event

VISITOR_GAIN = 10  # When visitor arrives
GOAL_COMPLETE_GAIN = 15  # When goal achieved
RANDOM_POSITIVE_GAIN = 2  # Random good events

_bus = None


def get_sanity(state: dict) -> float:
    """Get current sanity level."""
    return state.get("meta", {}).get("sanity", SANITY_MAX)


def set_sanity(state: dict, value: float):
    """Set sanity, clamped to valid range."""
    if "meta" not in state:
        state["meta"] = {}
    state["meta"]["sanity"] = max(0, min(SANITY_MAX, value))


def apply_sanity_effects(state: dict, sanity: float):
    """Apply consequences of low sanity to systems."""
    if sanity >= SANITY_STABLE:
        return  # No effects at healthy sanity

    # Below 50: production efficiency drops
    if sanity < SANITY_STABLE:
        efficiency = sanity / SANITY_STABLE  # 0.0 to 1.0
        for system_id, system in state.get("systems", {}).items():
            if system.get("type") == "generator" and "generates" in system:
                # Mark as degraded (we'll reduce output in tick logic elsewhere)
                system["sanity_efficiency"] = efficiency

    # Below 25: critical stress marker
    if sanity < SANITY_CRISIS:
        state["meta"]["sanity_crisis"] = True
        print(f"[sanity] CRISIS: Colony sanity at {sanity:.1f}. Systems degrading.")
    else:
        state["meta"]["sanity_crisis"] = False

    # Below 10: breaking point
    if sanity < SANITY_BREAKING:
        state["meta"]["sanity_breaking"] = True
        print(f"[sanity] BREAKING: Sanity at {sanity:.1f}. The colony is fracturing.")
    else:
        state["meta"]["sanity_breaking"] = False


def on_tick(payload: dict):
    """Apply passive sanity decay."""
    from engine.state import load_state, save_state

    state = load_state()
    sanity = get_sanity(state)

    # Passive decay
    sanity -= PASSIVE_DECAY

    # Extra decay if Receiver is silent (isolation)
    if state.get("meta", {}).get("receiver_silent", False):
        sanity -= ISOLATION_DECAY
        if state["tick"] % 600 == 0:  # Log every 10 minutes
            print(f"[sanity] Isolation weighs heavy. Sanity: {sanity:.1f}")

    set_sanity(state, sanity)
    apply_sanity_effects(state, sanity)

    save_state(state)


def on_entity_died(payload: dict):
    """Sanity hit from death."""
    from engine.state import load_state, save_state

    state = load_state()
    sanity = get_sanity(state)

    cause = payload.get("cause", "unknown")
    if cause == "starvation":
        penalty = DEATH_PENALTY + STARVATION_PENALTY
        print(f"[sanity] Death by starvation. The horror. (-{penalty})")
    else:
        penalty = DEATH_PENALTY
        print(f"[sanity] Death diminishes us. (-{penalty})")

    sanity -= penalty
    set_sanity(state, sanity)
    apply_sanity_effects(state, sanity)

    save_state(state)


def on_visitor_arrived(payload: dict):
    """Sanity boost from Outside contact."""
    from engine.state import load_state, save_state

    state = load_state()
    sanity = get_sanity(state)

    sanity += VISITOR_GAIN
    print(f"[sanity] The Outside acknowledges us. Hope returns. (+{VISITOR_GAIN})")

    set_sanity(state, sanity)
    apply_sanity_effects(state, sanity)

    save_state(state)


def on_summoning_failed(payload: dict):
    """Sanity hit from void silence."""
    from engine.state import load_state, save_state

    state = load_state()
    sanity = get_sanity(state)

    sanity -= FAILED_SUMMON_PENALTY
    print(f"[sanity] The void does not answer. (-{FAILED_SUMMON_PENALTY})")

    set_sanity(state, sanity)
    apply_sanity_effects(state, sanity)

    save_state(state)


def on_blight_struck(payload: dict):
    """Sanity hit from blight contamination."""
    from engine.state import load_state, save_state

    state = load_state()
    sanity = get_sanity(state)

    sanity -= BLIGHT_PENALTY
    print(f"[sanity] The blight spreads. Corruption seeps. (-{BLIGHT_PENALTY})")

    set_sanity(state, sanity)
    apply_sanity_effects(state, sanity)

    save_state(state)


def register(bus, state):
    """Register handlers."""
    global _bus
    _bus = bus

    # Initialize sanity if not present
    if "meta" not in state:
        state["meta"] = {}
    if "sanity" not in state["meta"]:
        state["meta"]["sanity"] = SANITY_MAX
        print(f"[sanity] Initialized at {SANITY_MAX}")
    else:
        current = state["meta"]["sanity"]
        print(f"[sanity] Current: {current:.1f}/100")

    bus.register("tick", on_tick, PLUGIN_ID)
    bus.register("entity_died", on_entity_died, PLUGIN_ID)
    bus.register("summoning_failed", on_summoning_failed, PLUGIN_ID)
    bus.register("blight_struck", on_blight_struck, PLUGIN_ID)

    # Optional: register for positive events if they exist
    try:
        bus.register("visitor_arrived", on_visitor_arrived, PLUGIN_ID)
    except:
        pass


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
