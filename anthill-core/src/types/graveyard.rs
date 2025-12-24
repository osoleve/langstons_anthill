//! Graveyard and corpse management.

use serde::{Deserialize, Serialize};
use super::entity::DeathCause;

/// A corpse in the graveyard
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Corpse {
    /// ID of the entity that died
    pub entity_id: String,

    /// Type of entity (ant, visitor)
    pub entity_type: String,

    /// Tick when death occurred
    pub death_tick: u64,

    /// Cause of death
    pub cause: DeathCause,

    /// Tile where death occurred
    pub tile: String,
}

/// The graveyard tracks dead entities
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Graveyard {
    /// Unprocessed corpses
    pub corpses: Vec<Corpse>,

    /// Total corpses ever processed
    pub total_processed: u64,
}

impl Graveyard {
    /// Add a corpse to the graveyard
    pub fn add_corpse(&mut self, corpse: Corpse) {
        self.corpses.push(corpse);
    }

    /// Take the next corpse for processing
    pub fn take_corpse(&mut self) -> Option<Corpse> {
        if self.corpses.is_empty() {
            None
        } else {
            Some(self.corpses.remove(0))
        }
    }

    /// Peek at the next corpse without removing
    pub fn peek_corpse(&self) -> Option<&Corpse> {
        self.corpses.first()
    }

    /// Mark a corpse as processed
    pub fn mark_processed(&mut self) {
        self.total_processed += 1;
    }

    /// Check if there are unprocessed corpses
    pub fn has_corpses(&self) -> bool {
        !self.corpses.is_empty()
    }
}
