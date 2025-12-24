//! Event types emitted by the tick engine.
//!
//! The core doesn't print, log, or make decisions about what's interesting.
//! It emits events. The layer above interprets them.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use crate::types::entity::{DeathCause, EntityId, VisitorType};

/// A single event emitted by the tick engine
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    /// The tick when this event occurred
    pub tick: u64,

    /// The kind of event
    pub kind: EventKind,
}

impl Event {
    pub fn new(tick: u64, kind: EventKind) -> Self {
        Self { tick, kind }
    }
}

/// All possible event kinds
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum EventKind {
    /// An entity died
    EntityDied {
        entity_id: EntityId,
        entity_type: String,
        cause: DeathCause,
        tile: String,
    },

    /// An entity ate food
    EntityAte {
        entity_id: EntityId,
        food: String,
        hunger_after: f64,
    },

    /// A resource threshold was crossed (going up)
    ThresholdCrossed {
        resource: String,
        threshold: f64,
        current: f64,
    },

    /// An action in the queue completed
    ActionComplete {
        action_id: String,
        action_type: String,
    },

    /// A system produced resources
    SystemProduced {
        system_id: String,
        produced: HashMap<String, f64>,
        consumed: HashMap<String, f64>,
    },

    /// A corpse was processed by an undertaker
    CorpseProcessed {
        undertaker_id: EntityId,
        total_processed: u64,
        contamination: f64,
    },

    /// Blight struck a tile
    BlightStruck {
        tile: String,
        contamination: f64,
        duration_ticks: u64,
    },

    /// Blight cleared from a tile
    BlightCleared {
        tile: String,
    },

    /// Entity killed by blight
    BlightKill {
        entity_id: EntityId,
        tile: String,
    },

    /// New ants were spawned
    AntsSpawned {
        worker_id: EntityId,
        undertaker_id: EntityId,
        nutrients_consumed: f64,
        fungus_consumed: f64,
    },

    /// Emergency spawn (colony was empty)
    EmergencySpawn {
        worker_id: EntityId,
        undertaker_id: EntityId,
    },

    /// A visitor arrived from outside
    VisitorArrived {
        visitor_id: EntityId,
        visitor_type: VisitorType,
        name: String,
    },

    /// A visitor departed (died)
    VisitorDeparted {
        visitor_id: EntityId,
        visitor_type: VisitorType,
        name: String,
        gift: Option<HashMap<String, f64>>,
    },

    /// Influence was spent on summoning
    InfluenceSpent {
        amount: f64,
        success: bool,
    },

    /// Summoning failed (no visitor arrived)
    SummoningFailed,

    /// Receiver went silent (no maintenance)
    ReceiverSilent,

    /// Receiver restored to operation
    ReceiverRestored,

    /// Resource was generated passively (by visitor)
    PassiveGeneration {
        entity_id: EntityId,
        resource: String,
        amount: f64,
    },

    /// A hungry visitor transformed influence
    InfluenceTransformed {
        visitor_id: EntityId,
        influence_consumed: f64,
        strange_matter_produced: f64,
    },

    /// Boredom threshold reached
    BoredomHigh {
        level: u64,
    },

    /// Sanity changed
    SanityChanged {
        delta: f64,
        new_value: f64,
        reason: String,
    },
}

/// Collection of events from a single tick
#[derive(Debug, Clone, Default)]
pub struct TickEvents {
    events: Vec<Event>,
}

impl TickEvents {
    pub fn new() -> Self {
        Self { events: Vec::new() }
    }

    /// Add an event
    pub fn push(&mut self, tick: u64, kind: EventKind) {
        self.events.push(Event::new(tick, kind));
    }

    /// Get all events
    pub fn events(&self) -> &[Event] {
        &self.events
    }

    /// Take all events (consuming self)
    pub fn into_events(self) -> Vec<Event> {
        self.events
    }

    /// Check if any events occurred
    pub fn is_empty(&self) -> bool {
        self.events.is_empty()
    }

    /// Count events
    pub fn len(&self) -> usize {
        self.events.len()
    }
}
