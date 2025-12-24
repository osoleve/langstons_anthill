//! Core data types for the anthill simulation.
//!
//! All types are:
//! - Serializable (serde)
//! - Clone-able (state snapshots)
//! - Hashable where needed (entity IDs)

pub mod entity;
pub mod resource;
pub mod tile;
pub mod system;
pub mod state;
pub mod graveyard;
pub mod action;
