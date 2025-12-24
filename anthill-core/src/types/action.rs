//! Action queue types.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// An action in the queue
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Action {
    /// Unique identifier for this action
    pub id: String,

    /// Type of action
    #[serde(rename = "type")]
    pub action_type: String,

    /// Ticks remaining until completion
    pub ticks_remaining: u64,

    /// Effects to apply on completion
    #[serde(skip_serializing_if = "Option::is_none")]
    pub effects: Option<ActionEffects>,
}

/// Effects applied when an action completes
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActionEffects {
    /// Resource changes
    #[serde(skip_serializing_if = "Option::is_none")]
    pub resources: Option<HashMap<String, f64>>,
}

/// The queues for pending actions and events
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Queues {
    /// Pending actions
    #[serde(default)]
    pub actions: Vec<Action>,

    /// Pending events (for plugin layer)
    #[serde(default)]
    pub events: Vec<serde_json::Value>,
}

impl Queues {
    /// Add an action to the queue
    pub fn enqueue_action(&mut self, action: Action) {
        self.actions.push(action);
    }

    /// Check if there are pending actions
    pub fn has_actions(&self) -> bool {
        !self.actions.is_empty()
    }
}
