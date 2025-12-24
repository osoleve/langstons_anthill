//! # Anthill Core
//!
//! The immutable simulation core of Langston's Anthill.
//!
//! This crate provides:
//! - **State types**: Entities, resources, tiles, systems
//! - **Tick engine**: Deterministic state transitions
//! - **Event emission**: All changes reported as events
//! - **Serialization**: JSON-compatible state persistence
//!
//! ## Design Principles
//!
//! 1. **Determinism**: Same inputs + same seed = same outputs, always
//! 2. **Data-oriented**: Entities are data, not objects with methods
//! 3. **Events as interface**: The core outputs events, never prints or decides
//! 4. **No I/O**: Pure computation, all I/O happens in the calling layer
//!
//! ## What Stays Outside
//!
//! - Plugin logic (cards, reflection, exploration)
//! - I/O (file saves, network, display)
//! - "What's interesting" decisions (that's for the Observer layer)

pub mod types;
pub mod events;
pub mod engine;
pub mod rng;

// Re-export main types for convenience
pub use types::state::GameState;
pub use types::entity::{Entity, EntityType, AntRole, VisitorType};
pub use types::resource::Resources;
pub use types::tile::{Tile, TileType};
pub use types::system::{System, SystemType};
pub use events::{Event, EventKind};
pub use engine::TickEngine;
pub use rng::SeededRng;
