//! Determinism tests for the anthill core.
//!
//! The core rule: Same seed + same inputs = same outputs, always.

use anthill_core::{GameState, TickEngine, Entity, Event, EventKind};
use pretty_assertions::assert_eq;
use std::collections::HashMap;

/// Run N ticks and collect all events
fn run_ticks(engine: &mut TickEngine, state: &mut GameState, n: usize) -> Vec<Event> {
    let mut all_events = Vec::new();
    for _ in 0..n {
        let events = engine.tick(state);
        all_events.extend(events.into_events());
    }
    all_events
}

/// Compare two event sequences for equality (ignoring order within same tick)
fn events_equal(a: &[Event], b: &[Event]) -> bool {
    if a.len() != b.len() {
        return false;
    }

    // Group by tick
    let mut a_by_tick: HashMap<u64, Vec<_>> = HashMap::new();
    let mut b_by_tick: HashMap<u64, Vec<_>> = HashMap::new();

    for event in a {
        a_by_tick.entry(event.tick).or_default().push(format!("{:?}", event.kind));
    }
    for event in b {
        b_by_tick.entry(event.tick).or_default().push(format!("{:?}", event.kind));
    }

    // Compare
    for (tick, mut a_events) in a_by_tick {
        match b_by_tick.get_mut(&tick) {
            Some(b_events) => {
                a_events.sort();
                b_events.sort();
                if a_events != *b_events {
                    return false;
                }
            }
            None => return false,
        }
    }

    true
}

#[test]
fn test_determinism_basic() {
    // Run the same simulation twice with the same seed
    let seed = 12345u64;

    let mut state1 = GameState::default();
    state1.resources.set("nutrients", 100.0);
    state1.resources.set("fungus", 100.0);
    state1.entities.push(Entity::new_worker("w1".to_string(), "origin".to_string()));

    let mut state2 = state1.clone();

    let mut engine1 = TickEngine::new(seed);
    let mut engine2 = TickEngine::new(seed);

    let events1 = run_ticks(&mut engine1, &mut state1, 100);
    let events2 = run_ticks(&mut engine2, &mut state2, 100);

    // States should be identical
    assert_eq!(state1.tick, state2.tick);
    assert_eq!(state1.resources.amounts, state2.resources.amounts);
    assert_eq!(state1.entities.len(), state2.entities.len());

    // Events should be equivalent
    assert!(events_equal(&events1, &events2), "Events differ between runs");
}

#[test]
fn test_determinism_with_spawning() {
    // Test with queen chamber active
    let seed = 42u64;

    let mut state1 = GameState::default();
    state1.resources.set("nutrients", 200.0);
    state1.resources.set("fungus", 200.0);
    state1.systems.insert("queen_chamber".to_string(), anthill_core::types::system::System {
        name: "Queen's Chamber".to_string(),
        system_type: anthill_core::types::system::SystemType::Spawner,
        generates: None,
        consumes: None,
        description: Some("The queen produces new ants".to_string()),
        corpse_boosts: Vec::new(),
        original_generates: None,
        original_consumes: None,
    });

    let mut state2 = state1.clone();

    let mut engine1 = TickEngine::new(seed);
    let mut engine2 = TickEngine::new(seed);

    // Run for 2000 ticks (past spawn interval)
    let events1 = run_ticks(&mut engine1, &mut state1, 2000);
    let events2 = run_ticks(&mut engine2, &mut state2, 2000);

    // Check that spawning happened and was deterministic
    let spawns1: Vec<_> = events1.iter()
        .filter(|e| matches!(e.kind, EventKind::AntsSpawned { .. } | EventKind::EmergencySpawn { .. }))
        .collect();
    let spawns2: Vec<_> = events2.iter()
        .filter(|e| matches!(e.kind, EventKind::AntsSpawned { .. } | EventKind::EmergencySpawn { .. }))
        .collect();

    assert!(!spawns1.is_empty(), "Expected spawning events");
    assert_eq!(spawns1.len(), spawns2.len(), "Spawn counts differ");

    // Entity counts should match
    assert_eq!(state1.entities.len(), state2.entities.len());
}

#[test]
fn test_determinism_with_receiver() {
    // Test visitor summoning determinism
    let seed = 99999u64;

    let mut state1 = GameState::default();
    state1.resources.set("influence", 50.0);
    state1.resources.set("fungus", 100.0);
    state1.systems.insert("receiver".to_string(), anthill_core::types::system::System {
        name: "The Receiver".to_string(),
        system_type: anthill_core::types::system::SystemType::Antenna,
        generates: None,
        consumes: None,
        description: Some("Listens to the Outside".to_string()),
        corpse_boosts: Vec::new(),
        original_generates: None,
        original_consumes: None,
    });

    let mut state2 = state1.clone();

    let mut engine1 = TickEngine::new(seed);
    let mut engine2 = TickEngine::new(seed);

    // Run for 3000 ticks (enough for multiple summon attempts)
    let events1 = run_ticks(&mut engine1, &mut state1, 3000);
    let events2 = run_ticks(&mut engine2, &mut state2, 3000);

    // Check visitor arrivals are deterministic
    let arrivals1: Vec<_> = events1.iter()
        .filter(|e| matches!(e.kind, EventKind::VisitorArrived { .. }))
        .collect();
    let arrivals2: Vec<_> = events2.iter()
        .filter(|e| matches!(e.kind, EventKind::VisitorArrived { .. }))
        .collect();

    assert_eq!(arrivals1.len(), arrivals2.len(), "Visitor arrival counts differ");

    // Compare visitor types
    for (a1, a2) in arrivals1.iter().zip(arrivals2.iter()) {
        if let (
            EventKind::VisitorArrived { visitor_type: t1, .. },
            EventKind::VisitorArrived { visitor_type: t2, .. }
        ) = (&a1.kind, &a2.kind) {
            assert_eq!(t1, t2, "Visitor types differ at tick {}", a1.tick);
        }
    }
}

#[test]
fn test_different_seeds_diverge() {
    // Different seeds should produce different results
    let mut state1 = GameState::default();
    state1.resources.set("influence", 50.0);
    state1.systems.insert("receiver".to_string(), anthill_core::types::system::System {
        name: "The Receiver".to_string(),
        system_type: anthill_core::types::system::SystemType::Antenna,
        generates: None,
        consumes: None,
        description: None,
        corpse_boosts: Vec::new(),
        original_generates: None,
        original_consumes: None,
    });

    let mut state2 = state1.clone();

    let mut engine1 = TickEngine::new(11111);
    let mut engine2 = TickEngine::new(22222);

    run_ticks(&mut engine1, &mut state1, 3000);
    run_ticks(&mut engine2, &mut state2, 3000);

    // Resource amounts should differ (due to different random summoning outcomes)
    // Note: This could theoretically fail if both RNG sequences happen to produce identical results,
    // but with 3000 ticks that's astronomically unlikely
    assert_ne!(
        state1.resources.get("influence"),
        state2.resources.get("influence"),
        "Different seeds should produce different influence levels"
    );
}

#[test]
fn test_resource_generation_determinism() {
    let seed = 55555u64;

    let mut generates = HashMap::new();
    generates.insert("dirt".to_string(), 0.02);

    let mut consumes = HashMap::new();
    consumes.insert("dirt".to_string(), 0.005);

    let mut generates2 = HashMap::new();
    generates2.insert("nutrients".to_string(), 0.01);

    let mut state1 = GameState::default();
    state1.resources.set("dirt", 50.0);
    state1.systems.insert("dig_site".to_string(), anthill_core::types::system::System::new_generator(
        "Dig Site".to_string(),
        generates.clone(),
    ));
    state1.systems.insert("compost_heap".to_string(), anthill_core::types::system::System::new_converter(
        "Compost Heap".to_string(),
        consumes.clone(),
        generates2.clone(),
    ));

    let mut state2 = state1.clone();

    let mut engine1 = TickEngine::new(seed);
    let mut engine2 = TickEngine::new(seed);

    run_ticks(&mut engine1, &mut state1, 1000);
    run_ticks(&mut engine2, &mut state2, 1000);

    // Resource amounts should be identical
    assert_eq!(state1.resources.get("dirt"), state2.resources.get("dirt"));
    assert_eq!(state1.resources.get("nutrients"), state2.resources.get("nutrients"));

    // Calculate expected values
    // dig_site: +0.02 dirt per tick
    // compost_heap: -0.005 dirt, +0.01 nutrients per tick
    // Net dirt: +0.015 per tick
    // Net nutrients: +0.01 per tick
    let expected_dirt = 50.0 + (1000.0 * 0.015);
    let expected_nutrients = 1000.0 * 0.01;

    assert!((state1.resources.get("dirt") - expected_dirt).abs() < 0.001);
    assert!((state1.resources.get("nutrients") - expected_nutrients).abs() < 0.001);
}

#[test]
fn test_entity_lifecycle_determinism() {
    let seed = 77777u64;

    let mut state1 = GameState::default();
    state1.resources.set("fungus", 5.0); // Limited food

    // Add some entities with varying hunger
    for i in 0..5 {
        let mut entity = Entity::new_worker(format!("w{}", i), "origin".to_string());
        entity.hunger = 50.0 - (i as f64 * 10.0); // 50, 40, 30, 20, 10
        state1.entities.push(entity);
    }

    let mut state2 = state1.clone();

    let mut engine1 = TickEngine::new(seed);
    let mut engine2 = TickEngine::new(seed);

    run_ticks(&mut engine1, &mut state1, 500);
    run_ticks(&mut engine2, &mut state2, 500);

    // Same number of survivors
    assert_eq!(state1.entities.len(), state2.entities.len());

    // Same graveyard state
    assert_eq!(state1.graveyard.corpses.len(), state2.graveyard.corpses.len());

    // Same resource state
    assert_eq!(state1.resources.get("fungus"), state2.resources.get("fungus"));
}
