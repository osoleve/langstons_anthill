"""The Receiver. An antenna of bone and crystal that invites the Outside in.

Influence is not for hoarding. It is a signal broadcast into the void.
The Receiver listens for a response. When enough influence has accumulated,
something may answer.
"""

import uuid
import random

PLUGIN_ID = "receiver"

# Constants
SUMMON_COST = 2.0  # Influence required to attempt summoning
SUMMON_COOLDOWN = 600  # 10 minutes between attempts
SUMMON_CHANCE = 0.3  # 30% chance of success per attempt
LISTENING_DRAIN = 0.0005  # Passive influence consumption while listening

_bus = None
_last_summon_attempt = 0

VISITOR_TYPES = [
    {
        "subtype": "wanderer",
        "name": "A Wanderer",
        "description": "Passes through. Leaves something behind.",
        "lifespan": 1800,  # 30 minutes
        "gift_on_death": {"strange_matter": 1},
        "hunger_rate": 0,  # Does not eat
        "food": None
    },
    {
        "subtype": "observer",
        "name": "An Observer",
        "description": "Watches. Generates insight from the watching.",
        "lifespan": 3600,  # 1 hour
        "generates": {"insight": 0.001},
        "hunger_rate": 0.05,  # Eats slowly
        "food": "crystals"  # Consumes crystals, not fungus
    },
    {
        "subtype": "hungry",
        "name": "A Hungry Thing",
        "description": "Consumes. Transforms what it consumes.",
        "lifespan": 900,  # 15 minutes
        "hunger_rate": 0.5,  # Very hungry
        "food": "influence",  # Eats influence itself
        "transforms": True
    }
]


def spawn_visitor(state: dict, visitor_type: dict) -> dict:
    """Create a Visitor entity from outside."""
    visitor_id = "v_" + str(uuid.uuid4())[:6]

    visitor = {
        "id": visitor_id,
        "type": "visitor",
        "subtype": visitor_type["subtype"],
        "name": visitor_type["name"],
        "tile": "receiver",  # Appears at the receiver
        "age": 0,
        "hunger": 100,
        "hunger_rate": visitor_type.get("hunger_rate", 0),
        "max_age": visitor_type.get("lifespan", 3600),
        "food": visitor_type.get("food"),
        "from_outside": True,
        "description": visitor_type["description"]
    }

    # Add special properties
    if "gift_on_death" in visitor_type:
        visitor["gift_on_death"] = visitor_type["gift_on_death"]
    if "generates" in visitor_type:
        visitor["generates"] = visitor_type["generates"]
    if "transforms" in visitor_type:
        visitor["transforms"] = True

    state["entities"].append(visitor)
    print(f"[receiver] A VISITOR HAS ARRIVED: {visitor_type['name']} ({visitor_type['subtype']})")

    return state


def attempt_summoning(state: dict) -> dict:
    """Spend influence to attempt to summon a Visitor."""
    global _last_summon_attempt

    influence = state["resources"].get("influence", 0)

    if influence < SUMMON_COST:
        return state

    tick = state["tick"]

    # Check cooldown
    if _last_summon_attempt > 0 and (tick - _last_summon_attempt) < SUMMON_COOLDOWN:
        return state

    # Spend influence
    state["resources"]["influence"] -= SUMMON_COST
    _last_summon_attempt = tick

    print(f"[receiver] Spent {SUMMON_COST} influence. Broadcasting into the void...")

    _bus.emit("influence_spent", {
        "tick": tick,
        "amount": SUMMON_COST,
        "purpose": "summoning"
    })

    # Roll for success
    if random.random() < SUMMON_CHANCE:
        # Success - something answers
        visitor_type = random.choice(VISITOR_TYPES)
        state = spawn_visitor(state, visitor_type)

        _bus.emit("visitor_arrived", {
            "tick": tick,
            "visitor_type": visitor_type["subtype"],
            "name": visitor_type["name"]
        })
    else:
        print(f"[receiver] The void is silent. No response.")
        _bus.emit("summoning_failed", {"tick": tick})

    return state


def process_visitors(state: dict) -> dict:
    """Handle visitor-specific behaviors."""
    for entity in state["entities"]:
        if entity.get("type") != "visitor":
            continue

        # Visitors that generate resources
        if "generates" in entity:
            for resource, rate in entity["generates"].items():
                state["resources"][resource] = state["resources"].get(resource, 0) + rate

        # Hungry visitors that eat influence
        if entity.get("food") == "influence" and entity.get("hunger", 100) < 50:
            if state["resources"].get("influence", 0) >= 0.1:
                state["resources"]["influence"] -= 0.1
                entity["hunger"] = min(100, entity["hunger"] + 20)
                # Transforms influence into something else
                if entity.get("transforms"):
                    state["resources"]["strange_matter"] = state["resources"].get("strange_matter", 0) + 0.05

    return state


def handle_visitor_death(state: dict) -> dict:
    """Check for visitors that should die and handle their gifts."""
    surviving = []

    for entity in state["entities"]:
        if entity.get("type") != "visitor":
            surviving.append(entity)
            continue

        max_age = entity.get("max_age", 3600)
        died = entity.get("age", 0) >= max_age

        # Visitors don't starve (except hungry ones)
        if entity.get("food") == "influence" and entity.get("hunger", 100) <= 0:
            died = True

        if died:
            print(f"[receiver] Visitor {entity.get('name', 'unknown')} has departed")

            # Leave gift if they have one
            if "gift_on_death" in entity:
                for resource, amount in entity["gift_on_death"].items():
                    state["resources"][resource] = state["resources"].get(resource, 0) + amount
                    print(f"[receiver] They left behind: {amount} {resource}")

            _bus.emit("visitor_departed", {
                "tick": state["tick"],
                "visitor_id": entity["id"],
                "name": entity.get("name", "unknown"),
                "subtype": entity.get("subtype", "unknown")
            })
        else:
            surviving.append(entity)

    state["entities"] = surviving
    return state


def check_maintenance(state: dict) -> dict:
    """Check if Receiver needs maintenance, apply degradation if unmaintained."""
    tick = state["tick"]
    goals = state.get("meta", {}).get("goals", {})
    maint_goal = goals.get("receiver_maintenance", {})

    if not maint_goal:
        return state

    last_maintained = maint_goal.get("last_maintained", tick)
    interval = maint_goal.get("maintenance_interval_ticks", 3600)
    ticks_since_maint = tick - last_maintained

    # Auto-maintain if we have strange_matter
    if ticks_since_maint >= interval:
        strange_matter = state["resources"].get("strange_matter", 0)

        if strange_matter >= 1:
            # Consume strange_matter to maintain
            state["resources"]["strange_matter"] -= 1
            state["meta"]["goals"]["receiver_maintenance"]["last_maintained"] = tick
            print(f"[receiver] Consumed 1 strange_matter for maintenance. The antenna hums with power.")
        else:
            # No fuel - Receiver goes silent
            if "receiver_silent" not in state["meta"]:
                state["meta"]["receiver_silent"] = True
                state["meta"]["receiver_failed_tick"] = tick
                print(f"[receiver] WARNING: No strange_matter for maintenance. The antenna begins to fade...")

    # If silent and we now have strange_matter, allow manual reactivation
    if state["meta"].get("receiver_silent") and state["resources"].get("strange_matter", 0) >= 1:
        # Auto-restore if strange_matter becomes available
        state["resources"]["strange_matter"] -= 1
        state["meta"]["receiver_silent"] = False
        state["meta"]["goals"]["receiver_maintenance"]["last_maintained"] = tick
        print(f"[receiver] The antenna ROARS back to life! Connection restored.")

    return state


def check_bootstrap_mode(state: dict) -> dict:
    """Emergency bootstrap to restart a silent Receiver.

    Cost: 20 ore + 10 crystals + 20 sanity
    Only works when Receiver is silent.
    One-time emergency measure when the strange_matter loop is broken.
    """
    if not state.get("meta", {}).get("receiver_silent", False):
        return state  # Not silent, no bootstrap needed

    # Check if we have resources for bootstrap
    resources = state.get("resources", {})
    meta = state.get("meta", {})

    ore = resources.get("ore", 0)
    crystals = resources.get("crystals", 0)
    sanity = meta.get("sanity", 100)

    # Bootstrap requirements
    BOOTSTRAP_ORE = 20
    BOOTSTRAP_CRYSTALS = 10
    BOOTSTRAP_SANITY = 20

    if ore >= BOOTSTRAP_ORE and crystals >= BOOTSTRAP_CRYSTALS and sanity >= BOOTSTRAP_SANITY:
        # Check if enough time has passed since failure (prevent immediate spam)
        tick = state["tick"]
        failed_tick = meta.get("receiver_failed_tick", 0)
        last_bootstrap_tick = meta.get("receiver_bootstrap_tick", 0)

        # Prevent multiple bootstraps in same session
        # Must be silent for at least 5 minutes AND haven't bootstrapped in last hour
        if tick - failed_tick >= 300 and tick - last_bootstrap_tick >= 3600:
            # Perform bootstrap
            state["resources"]["ore"] -= BOOTSTRAP_ORE
            state["resources"]["crystals"] -= BOOTSTRAP_CRYSTALS
            state["meta"]["sanity"] -= BOOTSTRAP_SANITY
            state["meta"]["receiver_silent"] = False
            state["meta"]["receiver_bootstrap_tick"] = tick

            print(f"[receiver] EMERGENCY BOOTSTRAP ACTIVATED!")
            print(f"[receiver] Consumed: {BOOTSTRAP_ORE} ore, {BOOTSTRAP_CRYSTALS} crystals, {BOOTSTRAP_SANITY} sanity")
            print(f"[receiver] The antenna flickers, powered by desperation and precious metals.")
            print(f"[receiver] Connection to the Outside: RESTORED")

            # Update maintenance timer
            if "goals" in state["meta"] and "receiver_maintenance" in state["meta"]["goals"]:
                state["meta"]["goals"]["receiver_maintenance"]["last_maintained"] = tick

    return state


def on_tick(payload: dict):
    """Main tick handler for receiver system."""
    from engine.state import load_state, save_state

    state = load_state()

    # Only operate if receiver exists
    if "receiver" not in state.get("systems", {}):
        return

    # Check for emergency bootstrap opportunity
    state = check_bootstrap_mode(state)

    # Check maintenance status
    state = check_maintenance(state)

    # If receiver is silent (unmaintained), it doesn't work
    if state.get("meta", {}).get("receiver_silent", False):
        save_state(state)
        return

    # Passive listening drain (very small)
    if state["resources"].get("influence", 0) > LISTENING_DRAIN:
        state["resources"]["influence"] -= LISTENING_DRAIN

    # Attempt summoning if we have enough influence
    state = attempt_summoning(state)

    # Process visitor behaviors
    state = process_visitors(state)

    # Handle visitor deaths/departures
    state = handle_visitor_death(state)

    save_state(state)


def register(bus, state):
    """Register handlers."""
    global _bus
    _bus = bus
    bus.register("tick", on_tick, PLUGIN_ID)
    print("[receiver] The Receiver is listening...")


def unregister(bus):
    """Unregister handlers."""
    bus.unregister(PLUGIN_ID)
