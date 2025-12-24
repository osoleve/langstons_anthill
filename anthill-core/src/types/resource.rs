//! Resource management types.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Collection of all resources in the simulation
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Resources {
    #[serde(flatten)]
    pub amounts: HashMap<String, f64>,
}

impl Resources {
    /// Create empty resources
    pub fn new() -> Self {
        Self {
            amounts: HashMap::new(),
        }
    }

    /// Get the amount of a resource (0.0 if not present)
    pub fn get(&self, name: &str) -> f64 {
        self.amounts.get(name).copied().unwrap_or(0.0)
    }

    /// Set the amount of a resource
    pub fn set(&mut self, name: &str, amount: f64) {
        self.amounts.insert(name.to_string(), amount);
    }

    /// Add to a resource (can be negative)
    pub fn add(&mut self, name: &str, delta: f64) {
        let current = self.get(name);
        self.amounts.insert(name.to_string(), current + delta);
    }

    /// Subtract from a resource (returns false if insufficient)
    pub fn try_consume(&mut self, name: &str, amount: f64) -> bool {
        let current = self.get(name);
        if current >= amount {
            self.amounts.insert(name.to_string(), current - amount);
            true
        } else {
            false
        }
    }

    /// Check if we have at least this much of a resource
    pub fn has(&self, name: &str, amount: f64) -> bool {
        self.get(name) >= amount
    }

    /// Check if we can consume all resources in a map
    pub fn can_consume_all(&self, requirements: &HashMap<String, f64>) -> bool {
        requirements.iter().all(|(name, amount)| self.has(name, *amount))
    }

    /// Consume all resources in a map (returns false if any insufficient)
    pub fn try_consume_all(&mut self, requirements: &HashMap<String, f64>) -> bool {
        if !self.can_consume_all(requirements) {
            return false;
        }
        for (name, amount) in requirements {
            self.try_consume(name, *amount);
        }
        true
    }

    /// Add all resources from a map
    pub fn add_all(&mut self, additions: &HashMap<String, f64>) {
        for (name, amount) in additions {
            self.add(name, *amount);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_resource_operations() {
        let mut res = Resources::new();

        assert_eq!(res.get("dirt"), 0.0);

        res.add("dirt", 10.0);
        assert_eq!(res.get("dirt"), 10.0);

        assert!(res.try_consume("dirt", 3.0));
        assert_eq!(res.get("dirt"), 7.0);

        assert!(!res.try_consume("dirt", 10.0));
        assert_eq!(res.get("dirt"), 7.0);
    }
}
