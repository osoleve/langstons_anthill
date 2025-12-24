//! Map tile types.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Type of map tile
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TileType {
    Empty,
    Compost,
    Extraction,
    Production,
    Resource,
    Special,
    Aesthetic,
    Antenna,
}

/// A tile on the map
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Tile {
    /// Display name
    pub name: String,

    /// Tile type
    #[serde(rename = "type")]
    pub tile_type: TileType,

    /// X coordinate
    pub x: i32,

    /// Y coordinate
    pub y: i32,

    /// Contamination level (0.0 to 1.0) for compost tiles
    #[serde(skip_serializing_if = "Option::is_none")]
    pub contamination: Option<f64>,

    /// Is this tile currently blighted?
    #[serde(skip_serializing_if = "Option::is_none")]
    pub blighted: Option<bool>,

    /// Ticks remaining of blight
    #[serde(skip_serializing_if = "Option::is_none")]
    pub blight_ticks_remaining: Option<u64>,

    /// Resource type for resource tiles
    #[serde(skip_serializing_if = "Option::is_none")]
    pub resource: Option<String>,

    /// Description
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

impl Tile {
    /// Create a basic empty tile
    pub fn new_empty(name: String, x: i32, y: i32) -> Self {
        Self {
            name,
            tile_type: TileType::Empty,
            x,
            y,
            contamination: None,
            blighted: None,
            blight_ticks_remaining: None,
            resource: None,
            description: None,
        }
    }

    /// Create the origin tile
    pub fn origin() -> Self {
        Self::new_empty("The Starting Dirt".to_string(), 0, 0)
    }

    /// Create a compost tile
    pub fn new_compost(name: String, x: i32, y: i32) -> Self {
        Self {
            name,
            tile_type: TileType::Compost,
            x,
            y,
            contamination: Some(0.0),
            blighted: Some(false),
            blight_ticks_remaining: Some(0),
            resource: None,
            description: None,
        }
    }

    /// Check if tile is blighted
    pub fn is_blighted(&self) -> bool {
        self.blighted.unwrap_or(false)
    }

    /// Add contamination to tile
    pub fn add_contamination(&mut self, amount: f64) {
        let current = self.contamination.unwrap_or(0.0);
        self.contamination = Some((current + amount).min(1.0));
    }

    /// Start a blight event
    pub fn start_blight(&mut self, duration_ticks: u64) {
        self.blighted = Some(true);
        self.blight_ticks_remaining = Some(duration_ticks);
    }

    /// Process one tick of blight (returns true if blight just cleared)
    pub fn tick_blight(&mut self) -> bool {
        if !self.is_blighted() {
            return false;
        }

        let remaining = self.blight_ticks_remaining.unwrap_or(0);
        if remaining <= 1 {
            self.blighted = Some(false);
            self.blight_ticks_remaining = Some(0);
            self.contamination = Some(0.0); // Reset after blight
            true
        } else {
            self.blight_ticks_remaining = Some(remaining - 1);
            false
        }
    }
}

/// The game map
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameMap {
    /// All tiles by ID
    pub tiles: HashMap<String, Tile>,

    /// Connections between tiles (bidirectional)
    pub connections: Vec<(String, String)>,
}

impl Default for GameMap {
    fn default() -> Self {
        let mut tiles = HashMap::new();
        tiles.insert("origin".to_string(), Tile::origin());

        Self {
            tiles,
            connections: Vec::new(),
        }
    }
}

impl GameMap {
    /// Get a tile by ID
    pub fn get_tile(&self, id: &str) -> Option<&Tile> {
        self.tiles.get(id)
    }

    /// Get a mutable tile by ID
    pub fn get_tile_mut(&mut self, id: &str) -> Option<&mut Tile> {
        self.tiles.get_mut(id)
    }

    /// Check if two tiles are connected
    pub fn are_connected(&self, a: &str, b: &str) -> bool {
        self.connections.iter().any(|(x, y)| {
            (x == a && y == b) || (x == b && y == a)
        })
    }

    /// Get all tiles connected to a given tile
    pub fn neighbors(&self, tile_id: &str) -> Vec<&str> {
        self.connections.iter()
            .filter_map(|(a, b)| {
                if a == tile_id {
                    Some(b.as_str())
                } else if b == tile_id {
                    Some(a.as_str())
                } else {
                    None
                }
            })
            .collect()
    }
}
