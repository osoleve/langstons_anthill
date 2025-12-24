//! Complete game state.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use super::entity::Entity;
use super::resource::Resources;
use super::tile::GameMap;
use super::system::System;
use super::graveyard::Graveyard;
use super::action::Queues;

/// Metadata about the game (non-simulation state)
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Meta {
    /// Boredom counter (increments when nothing happens)
    #[serde(default)]
    pub boredom: u64,

    /// Recent decision log (for reflection)
    #[serde(default)]
    pub recent_decisions: Vec<serde_json::Value>,

    /// Ideas that were rejected (the graveyard of concepts)
    #[serde(default)]
    pub rejected_ideas: Vec<String>,

    /// Cards that have fired
    #[serde(default)]
    pub fired_cards: Vec<String>,

    /// Estate information
    #[serde(skip_serializing_if = "Option::is_none")]
    pub estate: Option<serde_json::Value>,

    /// Decorations placed in the colony
    #[serde(default)]
    pub decor: Vec<serde_json::Value>,

    /// Jewelry created
    #[serde(default)]
    pub jewelry: Vec<serde_json::Value>,

    /// Goals and projects
    #[serde(default)]
    pub goals: HashMap<String, serde_json::Value>,

    /// Reflections (philosophical musings)
    #[serde(default)]
    pub reflections: Vec<serde_json::Value>,

    /// Colony sanity level
    #[serde(default = "default_sanity")]
    pub sanity: f64,

    /// Is the receiver silent?
    #[serde(default)]
    pub receiver_silent: bool,

    /// When did the receiver fail?
    #[serde(skip_serializing_if = "Option::is_none")]
    pub receiver_failed_tick: Option<u64>,
}

fn default_sanity() -> f64 {
    100.0
}

/// The complete game state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameState {
    /// Current tick number
    pub tick: u64,

    /// All resources
    pub resources: Resources,

    /// Production systems
    pub systems: HashMap<String, System>,

    /// Living entities
    pub entities: Vec<Entity>,

    /// The map
    pub map: GameMap,

    /// Action and event queues
    pub queues: Queues,

    /// Metadata
    pub meta: Meta,

    /// The graveyard
    #[serde(default)]
    pub graveyard: Graveyard,

    /// Last save timestamp (for offline progress)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub last_save_timestamp: Option<f64>,
}

impl Default for GameState {
    fn default() -> Self {
        Self {
            tick: 0,
            resources: Resources::new(),
            systems: HashMap::new(),
            entities: Vec::new(),
            map: GameMap::default(),
            queues: Queues::default(),
            meta: Meta::default(),
            graveyard: Graveyard::default(),
            last_save_timestamp: None,
        }
    }
}

impl GameState {
    /// Create a fresh game state
    pub fn new() -> Self {
        Self::default()
    }

    /// Load state from JSON
    pub fn from_json(json: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(json)
    }

    /// Serialize state to JSON
    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string(self)
    }

    /// Serialize state to pretty JSON
    pub fn to_json_pretty(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(self)
    }

    /// Get an entity by ID
    pub fn get_entity(&self, id: &str) -> Option<&Entity> {
        self.entities.iter().find(|e| e.id == id)
    }

    /// Get a mutable entity by ID
    pub fn get_entity_mut(&mut self, id: &str) -> Option<&mut Entity> {
        self.entities.iter_mut().find(|e| e.id == id)
    }

    /// Count entities by type
    pub fn count_entities_by_type(&self, entity_type: &super::entity::EntityType) -> usize {
        self.entities.iter().filter(|e| &e.entity_type == entity_type).count()
    }

    /// Count ants by role
    pub fn count_ants_by_role(&self, role: &super::entity::AntRole) -> usize {
        self.entities.iter()
            .filter(|e| e.role.as_ref() == Some(role))
            .count()
    }

    /// Get all entities on a tile
    pub fn entities_on_tile(&self, tile: &str) -> Vec<&Entity> {
        self.entities.iter().filter(|e| e.tile == tile).collect()
    }

    /// Check if a system exists
    pub fn has_system(&self, system_id: &str) -> bool {
        self.systems.contains_key(system_id)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_state() {
        let state = GameState::default();
        assert_eq!(state.tick, 0);
        assert!(state.entities.is_empty());
        assert!(state.map.tiles.contains_key("origin"));
    }

    #[test]
    fn test_serialization_roundtrip() {
        let state = GameState::default();
        let json = state.to_json().unwrap();
        let restored = GameState::from_json(&json).unwrap();
        assert_eq!(restored.tick, state.tick);
    }
}
