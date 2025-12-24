//! Seeded random number generation for deterministic simulation.
//!
//! The simulation must be reproducible: same seed + same inputs = same outputs.
//! We use ChaCha8 for speed with cryptographic quality.

use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;
use serde::{Deserialize, Serialize};

/// A seeded random number generator for deterministic simulation
#[derive(Debug, Clone)]
pub struct SeededRng {
    rng: ChaCha8Rng,
    seed: u64,
    calls: u64, // Track how many times we've called for debugging
}

impl SeededRng {
    /// Create a new RNG from a seed
    pub fn new(seed: u64) -> Self {
        Self {
            rng: ChaCha8Rng::seed_from_u64(seed),
            seed,
            calls: 0,
        }
    }

    /// Create from the current tick (useful for per-tick seeding)
    pub fn from_tick(base_seed: u64, tick: u64) -> Self {
        // Combine base seed and tick to get deterministic per-tick seed
        Self::new(base_seed.wrapping_add(tick.wrapping_mul(2654435761)))
    }

    /// Get the original seed
    pub fn seed(&self) -> u64 {
        self.seed
    }

    /// Get the number of calls made
    pub fn calls(&self) -> u64 {
        self.calls
    }

    /// Generate a random boolean with given probability (0.0 to 1.0)
    pub fn chance(&mut self, probability: f64) -> bool {
        self.calls += 1;
        self.rng.gen_bool(probability.clamp(0.0, 1.0))
    }

    /// Generate a random float between 0.0 and 1.0
    pub fn random(&mut self) -> f64 {
        self.calls += 1;
        self.rng.gen()
    }

    /// Generate a random integer in range [min, max]
    pub fn range(&mut self, min: u64, max: u64) -> u64 {
        self.calls += 1;
        self.rng.gen_range(min..=max)
    }

    /// Choose a random index from a slice
    pub fn choose_index(&mut self, len: usize) -> Option<usize> {
        if len == 0 {
            return None;
        }
        self.calls += 1;
        Some(self.rng.gen_range(0..len))
    }

    /// Generate a random entity ID (8 hex chars)
    pub fn entity_id(&mut self) -> String {
        self.calls += 1;
        format!("{:08x}", self.rng.gen::<u32>())
    }

    /// Generate a visitor ID (v_ prefix + 6 hex chars)
    pub fn visitor_id(&mut self) -> String {
        self.calls += 1;
        format!("v_{:06x}", self.rng.gen::<u32>() & 0xFFFFFF)
    }
}

/// State that can be serialized to restore RNG position
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RngState {
    pub seed: u64,
    pub calls: u64,
}

impl From<&SeededRng> for RngState {
    fn from(rng: &SeededRng) -> Self {
        Self {
            seed: rng.seed,
            calls: rng.calls,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_determinism() {
        let mut rng1 = SeededRng::new(12345);
        let mut rng2 = SeededRng::new(12345);

        // Same seed should produce same sequence
        for _ in 0..100 {
            assert_eq!(rng1.random(), rng2.random());
        }
    }

    #[test]
    fn test_different_seeds() {
        let mut rng1 = SeededRng::new(12345);
        let mut rng2 = SeededRng::new(54321);

        // Different seeds should (almost certainly) produce different values
        let vals1: Vec<f64> = (0..10).map(|_| rng1.random()).collect();
        let vals2: Vec<f64> = (0..10).map(|_| rng2.random()).collect();

        assert_ne!(vals1, vals2);
    }

    #[test]
    fn test_from_tick() {
        let rng1 = SeededRng::from_tick(100, 1000);
        let rng2 = SeededRng::from_tick(100, 1000);
        let rng3 = SeededRng::from_tick(100, 1001);

        assert_eq!(rng1.seed, rng2.seed);
        assert_ne!(rng1.seed, rng3.seed);
    }

    #[test]
    fn test_entity_id() {
        let mut rng = SeededRng::new(42);
        let id1 = rng.entity_id();
        let id2 = rng.entity_id();

        assert_eq!(id1.len(), 8);
        assert_eq!(id2.len(), 8);
        assert_ne!(id1, id2);
    }

    #[test]
    fn test_chance() {
        let mut rng = SeededRng::new(42);

        // With many trials, ~30% should be true for 0.3 probability
        let trials = 10000;
        let trues: usize = (0..trials).filter(|_| rng.chance(0.3)).count();
        let ratio = trues as f64 / trials as f64;

        assert!(ratio > 0.25 && ratio < 0.35);
    }
}
