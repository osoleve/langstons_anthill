//! Compatibility tests - verify the core can load existing game state.

use anthill_core::GameState;

const SAMPLE_STATE: &str = r#"{
  "tick": 104100,
  "resources": {
    "dirt": 1589.854999995136,
    "nutrients": 816.2699999998252,
    "fungus": 101.78159999997631,
    "crystals": 22.023000000003464,
    "ore": 55.326000000014766,
    "influence": 1.9935000000002725,
    "insight": 3.5999999999997145
  },
  "systems": {
    "compost_heap": {
      "name": "Compost Heap",
      "type": "generator",
      "generates": {
        "nutrients": 0.01
      },
      "consumes": {
        "dirt": 0.005
      },
      "description": "Dirt slowly breaks down into nutrients",
      "corpse_boosts": []
    },
    "dig_site": {
      "name": "Dig Site",
      "type": "generator",
      "generates": {
        "dirt": 0.02
      },
      "description": "Ants slowly dig up dirt"
    }
  },
  "entities": [
    {
      "id": "81a2527a",
      "type": "ant",
      "role": "worker",
      "tile": "origin",
      "age": 0,
      "hunger": 100,
      "hunger_rate": 0.1,
      "max_age": 7200,
      "food": "fungus"
    },
    {
      "id": "539a5906",
      "type": "ant",
      "role": "undertaker",
      "tile": "origin",
      "age": 0,
      "hunger": 100,
      "hunger_rate": 0.15,
      "max_age": 7200,
      "food": "fungus",
      "processing_corpse": false,
      "processing_ticks": 0
    }
  ],
  "map": {
    "tiles": {
      "origin": {
        "name": "The Starting Dirt",
        "type": "empty",
        "x": 0,
        "y": 0
      },
      "compost": {
        "name": "The Heap",
        "type": "compost",
        "x": 1,
        "y": 0,
        "contamination": 0.01,
        "blighted": false,
        "blight_ticks_remaining": 0
      }
    },
    "connections": [
      ["origin", "compost"]
    ]
  },
  "queues": {
    "actions": [],
    "events": []
  },
  "meta": {
    "boredom": 28,
    "recent_decisions": [],
    "fired_cards": ["what_do_nutrients_do", "the_second_grind"],
    "sanity": 80.1,
    "receiver_silent": true,
    "receiver_failed_tick": 104100
  },
  "graveyard": {
    "corpses": [],
    "total_processed": 17
  },
  "last_save_timestamp": 1766544426.5494697
}"#;

#[test]
fn test_load_sample_state() {
    let state = GameState::from_json(SAMPLE_STATE).expect("Failed to parse sample state");

    assert_eq!(state.tick, 104100);
    assert!((state.resources.get("dirt") - 1589.854999995136).abs() < 0.001);
    assert_eq!(state.entities.len(), 2);
    assert_eq!(state.graveyard.total_processed, 17);
    assert!(state.meta.receiver_silent);
}

#[test]
fn test_roundtrip_sample_state() {
    let state = GameState::from_json(SAMPLE_STATE).expect("Failed to parse sample state");
    let json = state.to_json_pretty().expect("Failed to serialize state");
    let restored = GameState::from_json(&json).expect("Failed to parse serialized state");

    assert_eq!(state.tick, restored.tick);
    assert_eq!(state.entities.len(), restored.entities.len());
    assert!((state.resources.get("dirt") - restored.resources.get("dirt")).abs() < 0.001);
}

#[test]
fn test_tick_sample_state() {
    use anthill_core::TickEngine;

    let mut state = GameState::from_json(SAMPLE_STATE).expect("Failed to parse sample state");
    let initial_dirt = state.resources.get("dirt");
    let mut engine = TickEngine::new(42);

    // Tick forward 100 times
    for _ in 0..100 {
        engine.tick(&mut state);
    }

    assert_eq!(state.tick, 104200);

    // Resources should have changed from system processing
    // dig_site: +0.02 dirt per tick
    // compost_heap: -0.005 dirt, +0.01 nutrients per tick
    // Net dirt: +0.015 per tick

    let new_dirt = state.resources.get("dirt");
    let dirt_delta = new_dirt - initial_dirt;

    // Should have gained about 1.5 dirt (100 ticks * 0.015)
    assert!(dirt_delta > 1.0 && dirt_delta < 2.0,
        "Expected dirt delta ~1.5, got {}", dirt_delta);

    // Entities should still be alive (they had plenty of fungus)
    assert!(!state.entities.is_empty(), "Entities should survive with plenty of food");
}

#[test]
fn test_entity_types() {
    let state = GameState::from_json(SAMPLE_STATE).expect("Failed to parse sample state");

    let worker = state.entities.iter().find(|e| e.id == "81a2527a").unwrap();
    assert_eq!(worker.entity_type, anthill_core::EntityType::Ant);
    assert_eq!(worker.role, Some(anthill_core::AntRole::Worker));
    assert_eq!(worker.tile, "origin");

    let undertaker = state.entities.iter().find(|e| e.id == "539a5906").unwrap();
    assert_eq!(undertaker.entity_type, anthill_core::EntityType::Ant);
    assert_eq!(undertaker.role, Some(anthill_core::AntRole::Undertaker));
    assert_eq!(undertaker.processing_corpse, Some(false));
}

#[test]
fn test_map_structure() {
    let state = GameState::from_json(SAMPLE_STATE).expect("Failed to parse sample state");

    assert!(state.map.tiles.contains_key("origin"));
    assert!(state.map.tiles.contains_key("compost"));
    assert!(state.map.are_connected("origin", "compost"));

    let compost = state.map.get_tile("compost").unwrap();
    assert!(!compost.is_blighted());
    assert!((compost.contamination.unwrap() - 0.01).abs() < 0.001);
}
