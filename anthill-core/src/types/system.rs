//! Production system types.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Type of production system
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SystemType {
    Generator,
    Converter,
    Spawner,
    Crafting,
    Antenna,
}

/// A boost from processed corpses
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CorpseBoost {
    /// When this boost expires
    pub expires_at_tick: u64,

    /// Bonus nutrients per tick
    pub bonus: f64,
}

/// A production system in the colony
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct System {
    /// Display name
    pub name: String,

    /// System type
    #[serde(rename = "type")]
    pub system_type: SystemType,

    /// Resources generated per tick
    #[serde(skip_serializing_if = "Option::is_none")]
    pub generates: Option<HashMap<String, f64>>,

    /// Resources consumed per tick
    #[serde(skip_serializing_if = "Option::is_none")]
    pub consumes: Option<HashMap<String, f64>>,

    /// Description
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,

    /// Active corpse boosts (for compost heap)
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub corpse_boosts: Vec<CorpseBoost>,

    /// Original generates (stored during blight)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub original_generates: Option<HashMap<String, f64>>,

    /// Original consumes (stored during blight)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub original_consumes: Option<HashMap<String, f64>>,
}

impl System {
    /// Create a basic generator system
    pub fn new_generator(name: String, generates: HashMap<String, f64>) -> Self {
        Self {
            name,
            system_type: SystemType::Generator,
            generates: Some(generates),
            consumes: None,
            description: None,
            corpse_boosts: Vec::new(),
            original_generates: None,
            original_consumes: None,
        }
    }

    /// Create a converter system (consumes and generates)
    pub fn new_converter(
        name: String,
        consumes: HashMap<String, f64>,
        generates: HashMap<String, f64>,
    ) -> Self {
        Self {
            name,
            system_type: SystemType::Converter,
            generates: Some(generates),
            consumes: Some(consumes),
            description: None,
            corpse_boosts: Vec::new(),
            original_generates: None,
            original_consumes: None,
        }
    }

    /// Check if system can run (has required resources)
    pub fn can_run(&self, resources: &super::resource::Resources) -> bool {
        if let Some(consumes) = &self.consumes {
            resources.can_consume_all(consumes)
        } else {
            true
        }
    }

    /// Get the total corpse boost bonus
    pub fn total_corpse_bonus(&self, current_tick: u64) -> f64 {
        self.corpse_boosts
            .iter()
            .filter(|b| b.expires_at_tick > current_tick)
            .map(|b| b.bonus)
            .sum()
    }

    /// Remove expired corpse boosts
    pub fn expire_corpse_boosts(&mut self, current_tick: u64) {
        self.corpse_boosts.retain(|b| b.expires_at_tick > current_tick);
    }

    /// Disable system (store original rates)
    pub fn disable(&mut self) {
        if self.original_generates.is_none() {
            self.original_generates = self.generates.take();
            self.original_consumes = self.consumes.take();
        }
    }

    /// Re-enable system (restore original rates)
    pub fn enable(&mut self) {
        if let Some(orig) = self.original_generates.take() {
            self.generates = Some(orig);
        }
        if let Some(orig) = self.original_consumes.take() {
            self.consumes = Some(orig);
        }
    }

    /// Check if system is disabled
    pub fn is_disabled(&self) -> bool {
        self.original_generates.is_some()
    }
}
