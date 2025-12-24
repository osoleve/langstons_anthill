//! Entity types: ants, visitors, and their properties.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Unique identifier for an entity
pub type EntityId = String;

/// The type of entity
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EntityType {
    Ant,
    Visitor,
}

/// Role of an ant in the colony
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AntRole {
    Worker,
    Undertaker,
}

/// Type of visitor from the Outside
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum VisitorType {
    Wanderer,
    Observer,
    Hungry,
}

/// A living entity in the simulation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Entity {
    /// Unique identifier
    pub id: EntityId,

    /// What kind of entity
    #[serde(rename = "type")]
    pub entity_type: EntityType,

    /// Role (for ants) - None for visitors
    #[serde(skip_serializing_if = "Option::is_none")]
    pub role: Option<AntRole>,

    /// Visitor subtype (for visitors) - None for ants
    #[serde(skip_serializing_if = "Option::is_none")]
    pub subtype: Option<VisitorType>,

    /// Display name (mainly for visitors)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,

    /// Current tile location
    pub tile: String,

    /// Age in ticks
    #[serde(default)]
    pub age: u64,

    /// Current hunger (0-100, dies at 0)
    #[serde(default = "default_hunger")]
    pub hunger: f64,

    /// Hunger decrease per tick
    #[serde(default = "default_hunger_rate")]
    pub hunger_rate: f64,

    /// Maximum age before death (ticks)
    #[serde(default = "default_max_age")]
    pub max_age: u64,

    /// What resource this entity eats
    #[serde(skip_serializing_if = "Option::is_none")]
    pub food: Option<String>,

    /// For undertakers: currently processing a corpse?
    #[serde(skip_serializing_if = "Option::is_none")]
    pub processing_corpse: Option<bool>,

    /// For undertakers: ticks spent processing current corpse
    #[serde(skip_serializing_if = "Option::is_none")]
    pub processing_ticks: Option<u64>,

    /// Visitor flag: came from outside
    #[serde(skip_serializing_if = "Option::is_none")]
    pub from_outside: Option<bool>,

    /// Description (mainly for visitors)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,

    /// Gift left on death (for wanderers)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub gift_on_death: Option<HashMap<String, f64>>,

    /// Resources generated per tick (for observers)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub generates: Option<HashMap<String, f64>>,

    /// Does this entity transform what it eats? (hungry visitors)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub transforms: Option<bool>,
}

fn default_hunger() -> f64 {
    100.0
}

fn default_hunger_rate() -> f64 {
    0.1
}

fn default_max_age() -> u64 {
    7200 // 2 hours
}

impl Entity {
    /// Create a new worker ant
    pub fn new_worker(id: EntityId, tile: String) -> Self {
        Self {
            id,
            entity_type: EntityType::Ant,
            role: Some(AntRole::Worker),
            subtype: None,
            name: None,
            tile,
            age: 0,
            hunger: 100.0,
            hunger_rate: 0.1,
            max_age: 7200,
            food: Some("fungus".to_string()),
            processing_corpse: None,
            processing_ticks: None,
            from_outside: None,
            description: None,
            gift_on_death: None,
            generates: None,
            transforms: None,
        }
    }

    /// Create a new undertaker ant
    pub fn new_undertaker(id: EntityId, tile: String) -> Self {
        Self {
            id,
            entity_type: EntityType::Ant,
            role: Some(AntRole::Undertaker),
            subtype: None,
            name: None,
            tile,
            age: 0,
            hunger: 100.0,
            hunger_rate: 0.15, // Undertakers are hungrier
            max_age: 7200,
            food: Some("fungus".to_string()),
            processing_corpse: Some(false),
            processing_ticks: Some(0),
            from_outside: None,
            description: None,
            gift_on_death: None,
            generates: None,
            transforms: None,
        }
    }

    /// Create a wanderer visitor
    pub fn new_wanderer(id: EntityId) -> Self {
        let mut gift = HashMap::new();
        gift.insert("strange_matter".to_string(), 1.0);

        Self {
            id,
            entity_type: EntityType::Visitor,
            role: None,
            subtype: Some(VisitorType::Wanderer),
            name: Some("A Wanderer".to_string()),
            tile: "receiver".to_string(),
            age: 0,
            hunger: 100.0,
            hunger_rate: 0.0,
            max_age: 1800, // 30 minutes
            food: None,
            processing_corpse: None,
            processing_ticks: None,
            from_outside: Some(true),
            description: Some("Passes through. Leaves something behind.".to_string()),
            gift_on_death: Some(gift),
            generates: None,
            transforms: None,
        }
    }

    /// Create an observer visitor
    pub fn new_observer(id: EntityId) -> Self {
        let mut generates = HashMap::new();
        generates.insert("insight".to_string(), 0.001);

        Self {
            id,
            entity_type: EntityType::Visitor,
            role: None,
            subtype: Some(VisitorType::Observer),
            name: Some("An Observer".to_string()),
            tile: "receiver".to_string(),
            age: 0,
            hunger: 100.0,
            hunger_rate: 0.05,
            max_age: 3600, // 1 hour
            food: Some("crystals".to_string()),
            processing_corpse: None,
            processing_ticks: None,
            from_outside: Some(true),
            description: Some("Watches. Generates insight from the watching.".to_string()),
            gift_on_death: None,
            generates: Some(generates),
            transforms: None,
        }
    }

    /// Create a hungry visitor
    pub fn new_hungry(id: EntityId) -> Self {
        Self {
            id,
            entity_type: EntityType::Visitor,
            role: None,
            subtype: Some(VisitorType::Hungry),
            name: Some("A Hungry Thing".to_string()),
            tile: "receiver".to_string(),
            age: 0,
            hunger: 100.0,
            hunger_rate: 0.5,
            max_age: 900, // 15 minutes
            food: Some("influence".to_string()),
            processing_corpse: None,
            processing_ticks: None,
            from_outside: Some(true),
            description: Some("Consumes. Transforms what it consumes.".to_string()),
            gift_on_death: None,
            generates: None,
            transforms: Some(true),
        }
    }

    /// Check if entity is dead (starvation or old age)
    pub fn is_dead(&self) -> bool {
        self.hunger <= 0.0 || self.age >= self.max_age
    }

    /// Get cause of death if dead
    pub fn cause_of_death(&self) -> Option<DeathCause> {
        if self.hunger <= 0.0 {
            Some(DeathCause::Starvation)
        } else if self.age >= self.max_age {
            Some(DeathCause::OldAge)
        } else {
            None
        }
    }
}

/// Cause of entity death
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DeathCause {
    Starvation,
    OldAge,
    Blight,
}
