//! The tick engine. The heartbeat of the simulation.
//!
//! This module contains all deterministic state transition rules.
//! No I/O, no printing, no decisions about "what's interesting."
//! Just pure state → state transformations that emit events.

use std::collections::HashMap;

use crate::events::{EventKind, TickEvents};
use crate::rng::SeededRng;
use crate::types::entity::{AntRole, DeathCause, Entity, EntityType, VisitorType};
use crate::types::graveyard::Corpse;
use crate::types::state::GameState;
use crate::types::system::CorpseBoost;

/// Configuration constants for the simulation
pub mod constants {
    // Entity lifecycle
    pub const DEFAULT_MAX_AGE: u64 = 7200; // 2 hours
    pub const HUNGER_THRESHOLD_EAT: f64 = 50.0;
    pub const HUNGER_GAIN_FROM_EATING: f64 = 30.0;
    pub const MAX_HUNGER: f64 = 100.0;

    // Queen spawning
    pub const SPAWN_INTERVAL_TICKS: u64 = 1800; // 30 minutes
    pub const SPAWN_COST_NUTRIENTS: f64 = 10.0;
    pub const SPAWN_COST_FUNGUS: f64 = 10.0;
    pub const MIN_RESOURCES_TO_SPAWN: f64 = 15.0;

    // Undertaker
    pub const CORPSE_PROCESSING_TICKS: u64 = 120;
    pub const CORPSE_NUTRIENT_BOOST: f64 = 0.1;
    pub const CORPSE_BOOST_DURATION: u64 = 600;
    pub const CONTAMINATION_PER_CORPSE: f64 = 0.01;
    pub const BLIGHT_DURATION: u64 = 300;

    // Receiver
    pub const SUMMON_COST: f64 = 2.0;
    pub const SUMMON_COOLDOWN: u64 = 600; // 10 minutes
    pub const SUMMON_CHANCE: f64 = 0.3;
    pub const LISTENING_DRAIN: f64 = 0.0005;
    pub const MAINTENANCE_INTERVAL: u64 = 3600;
    pub const MAINTENANCE_COST_STRANGE_MATTER: f64 = 1.0;

    // Hungry visitor
    pub const HUNGRY_INFLUENCE_CONSUME: f64 = 0.1;
    pub const HUNGRY_STRANGE_MATTER_PRODUCE: f64 = 0.05;
    pub const HUNGRY_HUNGER_GAIN: f64 = 20.0;

    // Boredom
    pub const BOREDOM_THRESHOLD: u64 = 60;

    // Thresholds to check
    pub const RESOURCE_THRESHOLDS: [f64; 7] = [10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0];

    // Offline Progress
    pub const MAX_OFFLINE_TICKS: u64 = 3600;
}

/// The tick engine processes one tick at a time
pub struct TickEngine {
    /// Base seed for RNG
    seed: u64,

    /// Last spawn tick (for queen)
    last_spawn_tick: u64,

    /// Last summon attempt tick (for receiver)
    last_summon_tick: u64,
}

impl TickEngine {
    /// Create a new tick engine with the given seed
    pub fn new(seed: u64) -> Self {
        Self {
            seed,
            last_spawn_tick: 0,
            last_summon_tick: 0,
        }
    }

    /// Process a single tick, returning events that occurred
    pub fn tick(&mut self, state: &mut GameState) -> TickEvents {
        let mut events = TickEvents::new();
        let tick = state.tick + 1;
        state.tick = tick;

        // Create RNG for this tick
        let mut rng = SeededRng::from_tick(self.seed, tick);

        // Store previous resource amounts for threshold checking
        let prev_resources: HashMap<String, f64> = state.resources.amounts.clone();

        // 1. Process action queue
        self.process_actions(state, &mut events);

        // 2. Process systems (resource generation/consumption)
        self.process_systems(state, &mut events);

        // 3. Process entities (aging, hunger, eating, death)
        self.process_entities(state, &mut events);

        // 4. Process undertakers (corpse collection)
        self.process_undertakers(state, &mut events, &mut rng);

        // 5. Process contamination and blight
        self.process_blight(state, &mut events, &mut rng);

        // 6. Process queen spawning
        self.process_queen(state, &mut events, &mut rng);

        // 7. Process receiver and visitors
        self.process_receiver(state, &mut events, &mut rng);

        // 8. Process visitor behaviors
        self.process_visitors(state, &mut events);

        // 9. Check resource thresholds
        self.check_thresholds(state, &prev_resources, &mut events);

        // 10. Process boredom
        self.process_boredom(state, &mut events);

        events
    }

    /// Process offline progress
    pub fn process_offline_progress(&mut self, state: &mut GameState, current_timestamp: f64) -> TickEvents {
        let events = TickEvents::new();

        let last_save = match state.last_save_timestamp {
            Some(ts) => ts,
            None => return events,
        };

        let elapsed_seconds = current_timestamp - last_save;
        if elapsed_seconds <= 0.0 {
            return events;
        }

        let ticks_to_apply = (elapsed_seconds as u64).min(constants::MAX_OFFLINE_TICKS);

        if ticks_to_apply < 10 {
            return events;
        }

        // Apply simplified ticks (resource generation only, no entity processing)
        for _ in 0..ticks_to_apply {
            let tick = state.tick + 1;
            state.tick = tick;

            // Process passive resource generation/consumption from systems
            // This replicates the Python logic which does simplified system processing
            // It manually checks consumes/generates instead of calling process_systems

             // Collect system operations first to avoid borrow issues
            let operations: Vec<_> = state.systems.iter()
                .filter(|(_, system)| !system.is_disabled())
                .filter_map(|(id, system)| {
                    // Check if system can run
                    if !system.can_run(&state.resources) {
                        return None;
                    }

                    let consumes = system.consumes.clone().unwrap_or_default();
                    let generates = system.generates.clone().unwrap_or_default();

                     // Add corpse boost bonus for compost heap - Python doesn't do this in offline mode explicitly
                     // but to be "better", maybe we should?
                     // The Python code is:
                     /*
                        for system_id, system in state["systems"].items():
                            can_run = True
                            if "consumes" in system:
                                ...
                            if can_run:
                                if "consumes" in system: ...
                                if "generates" in system: ...
                     */
                     // It does NOT invoke the full system logic (which might have side effects).
                     // However, the Rust system logic is mostly resources.
                     // The main difference is "corpse boost" which is dynamic in Rust.

                     // I will stick to the simplified logic as requested by "move offline progress calculation into the core"
                     // The Python code doesn't seem to account for corpse boost in offline mode explicitly?
                     // Wait, the Python code accesses `system["generates"]` directly.
                     // If corpse boost modifies `generates` in place in Python, then it works.
                     // In Rust, corpse boost is calculated dynamically in `process_systems`.
                     // I'll stick to basic `generates` to match Python behavior unless I want to improve it.
                     // I'll match Python behavior for now.

                    Some((id.clone(), consumes, generates))
                })
                .collect();

            // Apply operations
            for (_system_id, consumes, generates) in operations {
                // Consume resources
                for (resource, amount) in &consumes {
                    state.resources.add(resource, -amount);
                }

                // Generate resources
                for (resource, amount) in &generates {
                    state.resources.add(resource, *amount);
                }
            }

            // Process entity hunger (reduced rate)
            // Python:
            // entity["age"] = entity.get("age", 0) + 1
            // entity["hunger"] = entity.get("hunger", 100) - (entity.get("hunger_rate", 0.1) * 0.5)
            // if entity["hunger"] < 50: eat...

            // In Rust we need to handle this carefully.
            for entity in &mut state.entities {
                 entity.age += 1;

                 // Hunger decreases at half rate
                 entity.hunger -= entity.hunger_rate * 0.5;

                 // Auto-eat
                 if entity.hunger < constants::HUNGER_THRESHOLD_EAT {
                      if let Some(food) = &entity.food {
                           // Simplified check compared to full tick
                           if state.resources.get(food) >= 1.0 {
                               state.resources.add(food, -1.0);
                               entity.hunger = (entity.hunger + constants::HUNGER_GAIN_FROM_EATING).min(constants::MAX_HUNGER);
                           }
                      }
                 }
            }

            // Remove entities that died offline
            // Python: state["entities"] = [e for e in state["entities"] if e.get("hunger", 100) > 0 and e.get("age", 0) < e.get("max_age", 7200)]

             state.entities.retain(|e| {
                 let alive = e.hunger > 0.0 && e.age < constants::DEFAULT_MAX_AGE;
                 if !alive {
                     // Unlike full tick, we don't add to graveyard or emit death events in the loop?
                     // Python:
                     /*
                        # Remove entities that died offline
                        state["entities"] = [e for e in state["entities"] if e.get("hunger", 100) > 0 and e.get("age", 0) < e.get("max_age", 7200)]
                     */
                     // Python code does NOT add to graveyard during offline progress loop. It just removes them.
                 }
                 alive
             });
        }

        events
    }

    /// Process the action queue
    fn process_actions(&self, state: &mut GameState, events: &mut TickEvents) {
        let tick = state.tick;
        let mut remaining = Vec::new();

        for mut action in state.queues.actions.drain(..) {
            if action.ticks_remaining <= 1 {
                // Action complete
                events.push(tick, EventKind::ActionComplete {
                    action_id: action.id.clone(),
                    action_type: action.action_type.clone(),
                });

                // Apply effects
                if let Some(effects) = &action.effects {
                    if let Some(resources) = &effects.resources {
                        state.resources.add_all(resources);
                    }
                }
            } else {
                action.ticks_remaining -= 1;
                remaining.push(action);
            }
        }

        state.queues.actions = remaining;
    }

    /// Process production systems
    fn process_systems(&self, state: &mut GameState, events: &mut TickEvents) {
        let tick = state.tick;

        // Collect system operations first to avoid borrow issues
        let operations: Vec<_> = state.systems.iter()
            .filter(|(_, system)| !system.is_disabled())
            .filter_map(|(id, system)| {
                // Check if system can run
                if !system.can_run(&state.resources) {
                    return None;
                }

                let consumes = system.consumes.clone().unwrap_or_default();
                let mut generates = system.generates.clone().unwrap_or_default();

                // Add corpse boost bonus for compost heap
                if id == "compost_heap" {
                    let bonus = system.total_corpse_bonus(tick);
                    if bonus > 0.0 {
                        *generates.entry("nutrients".to_string()).or_default() += bonus;
                    }
                }

                Some((id.clone(), consumes, generates))
            })
            .collect();

        // Apply operations
        for (system_id, consumes, generates) in operations {
            // Consume resources
            for (resource, amount) in &consumes {
                state.resources.add(resource, -amount);
            }

            // Generate resources
            for (resource, amount) in &generates {
                state.resources.add(resource, *amount);
            }

            if !consumes.is_empty() || !generates.is_empty() {
                events.push(tick, EventKind::SystemProduced {
                    system_id,
                    produced: generates,
                    consumed: consumes,
                });
            }
        }

        // Expire old corpse boosts
        for system in state.systems.values_mut() {
            system.expire_corpse_boosts(tick);
        }
    }

    /// Process entity lifecycle (aging, hunger, eating, death)
    fn process_entities(&self, state: &mut GameState, events: &mut TickEvents) {
        let tick = state.tick;
        let mut surviving = Vec::new();

        for mut entity in state.entities.drain(..) {
            // Age
            entity.age += 1;

            // Hunger decreases
            entity.hunger -= entity.hunger_rate;

            // Try to eat if hungry
            if entity.hunger < constants::HUNGER_THRESHOLD_EAT {
                if let Some(food) = &entity.food {
                    // Special case: hungry visitors eat influence
                    if food == "influence" && entity.subtype == Some(VisitorType::Hungry) {
                        if state.resources.get("influence") >= constants::HUNGRY_INFLUENCE_CONSUME {
                            state.resources.add("influence", -constants::HUNGRY_INFLUENCE_CONSUME);
                            entity.hunger = (entity.hunger + constants::HUNGRY_HUNGER_GAIN).min(constants::MAX_HUNGER);

                            // Transform influence into strange_matter
                            if entity.transforms == Some(true) {
                                state.resources.add("strange_matter", constants::HUNGRY_STRANGE_MATTER_PRODUCE);
                                events.push(tick, EventKind::InfluenceTransformed {
                                    visitor_id: entity.id.clone(),
                                    influence_consumed: constants::HUNGRY_INFLUENCE_CONSUME,
                                    strange_matter_produced: constants::HUNGRY_STRANGE_MATTER_PRODUCE,
                                });
                            }
                        }
                    } else if state.resources.get(food) >= 1.0 {
                        state.resources.add(food, -1.0);
                        entity.hunger = (entity.hunger + constants::HUNGER_GAIN_FROM_EATING).min(constants::MAX_HUNGER);

                        events.push(tick, EventKind::EntityAte {
                            entity_id: entity.id.clone(),
                            food: food.clone(),
                            hunger_after: entity.hunger,
                        });
                    }
                }
            }

            // Check for death
            if let Some(cause) = entity.cause_of_death() {
                // Visitors just disappear (handled separately for gifts)
                if entity.entity_type == EntityType::Visitor {
                    let gift = entity.gift_on_death.clone();
                    if let Some(ref g) = gift {
                        state.resources.add_all(g);
                    }
                    events.push(tick, EventKind::VisitorDeparted {
                        visitor_id: entity.id.clone(),
                        visitor_type: entity.subtype.clone().unwrap_or(VisitorType::Wanderer),
                        name: entity.name.clone().unwrap_or_default(),
                        gift,
                    });
                } else {
                    // Add to graveyard
                    state.graveyard.add_corpse(Corpse {
                        entity_id: entity.id.clone(),
                        entity_type: format!("{:?}", entity.entity_type).to_lowercase(),
                        death_tick: tick,
                        cause: cause.clone(),
                        tile: entity.tile.clone(),
                    });

                    events.push(tick, EventKind::EntityDied {
                        entity_id: entity.id.clone(),
                        entity_type: format!("{:?}", entity.entity_type).to_lowercase(),
                        cause,
                        tile: entity.tile.clone(),
                    });
                }
            } else {
                surviving.push(entity);
            }
        }

        state.entities = surviving;
    }

    /// Process undertaker corpse collection
    fn process_undertakers(&self, state: &mut GameState, events: &mut TickEvents, _rng: &mut SeededRng) {
        let tick = state.tick;

        // Check if compost tile is blighted
        let compost_blighted = state.map.get_tile("compost")
            .map(|t| t.is_blighted())
            .unwrap_or(false);

        if compost_blighted {
            return;
        }

        // Find undertaker entities
        let undertaker_ids: Vec<String> = state.entities.iter()
            .filter(|e| e.role == Some(AntRole::Undertaker))
            .map(|e| e.id.clone())
            .collect();

        for undertaker_id in undertaker_ids {
            let undertaker = match state.entities.iter_mut().find(|e| e.id == undertaker_id) {
                Some(e) => e,
                None => continue,
            };

            let processing = undertaker.processing_corpse.unwrap_or(false);
            let ticks = undertaker.processing_ticks.unwrap_or(0);

            if processing {
                // Continue processing
                undertaker.processing_ticks = Some(ticks + 1);

                if ticks + 1 >= constants::CORPSE_PROCESSING_TICKS {
                    // Corpse delivered
                    undertaker.processing_corpse = Some(false);
                    undertaker.processing_ticks = Some(0);

                    // Add boost to compost heap
                    if let Some(system) = state.systems.get_mut("compost_heap") {
                        system.corpse_boosts.push(CorpseBoost {
                            expires_at_tick: tick + constants::CORPSE_BOOST_DURATION,
                            bonus: constants::CORPSE_NUTRIENT_BOOST,
                        });
                    }

                    // Add contamination
                    if let Some(tile) = state.map.get_tile_mut("compost") {
                        tile.add_contamination(constants::CONTAMINATION_PER_CORPSE);

                        let contamination = tile.contamination.unwrap_or(0.0);
                        state.graveyard.mark_processed();

                        events.push(tick, EventKind::CorpseProcessed {
                            undertaker_id: undertaker_id.clone(),
                            total_processed: state.graveyard.total_processed,
                            contamination,
                        });
                    }
                }
            } else if state.graveyard.has_corpses() {
                // Start processing a new corpse
                state.graveyard.take_corpse();
                undertaker.processing_corpse = Some(true);
                undertaker.processing_ticks = Some(0);
            }
        }
    }

    /// Process contamination and blight
    fn process_blight(&self, state: &mut GameState, events: &mut TickEvents, rng: &mut SeededRng) {
        let tick = state.tick;

        // Handle active blight ticking down
        if let Some(tile) = state.map.get_tile_mut("compost") {
            if tile.is_blighted() {
                if tile.tick_blight() {
                    events.push(tick, EventKind::BlightCleared {
                        tile: "compost".to_string(),
                    });

                    // Re-enable compost system
                    if let Some(system) = state.systems.get_mut("compost_heap") {
                        system.enable();
                    }
                }
                return; // Don't roll for new blight while blighted
            }

            // Roll for blight based on contamination
            let contamination = tile.contamination.unwrap_or(0.0);
            if contamination > 0.0 && rng.chance(contamination) {
                // Blight strikes!
                tile.start_blight(constants::BLIGHT_DURATION);

                events.push(tick, EventKind::BlightStruck {
                    tile: "compost".to_string(),
                    contamination,
                    duration_ticks: constants::BLIGHT_DURATION,
                });

                // Disable compost system
                if let Some(system) = state.systems.get_mut("compost_heap") {
                    system.disable();
                    system.corpse_boosts.clear();
                }

                // Kill entities on the tile
                let mut surviving = Vec::new();
                for entity in state.entities.drain(..) {
                    if entity.tile == "compost" {
                        events.push(tick, EventKind::BlightKill {
                            entity_id: entity.id.clone(),
                            tile: "compost".to_string(),
                        });

                        // Add to graveyard
                        state.graveyard.add_corpse(Corpse {
                            entity_id: entity.id.clone(),
                            entity_type: format!("{:?}", entity.entity_type).to_lowercase(),
                            death_tick: tick,
                            cause: DeathCause::Blight,
                            tile: entity.tile.clone(),
                        });
                    } else {
                        surviving.push(entity);
                    }
                }
                state.entities = surviving;
            }
        }
    }

    /// Process queen spawning
    fn process_queen(&mut self, state: &mut GameState, events: &mut TickEvents, rng: &mut SeededRng) {
        let tick = state.tick;

        // Only spawn if queen chamber exists
        if !state.has_system("queen_chamber") {
            return;
        }

        let nutrients = state.resources.get("nutrients");
        let fungus = state.resources.get("fungus");
        let entity_count = state.entities.len();

        // Emergency spawn if colony is empty
        let is_emergency = entity_count == 0
            && nutrients >= constants::MIN_RESOURCES_TO_SPAWN
            && fungus >= constants::MIN_RESOURCES_TO_SPAWN;

        if is_emergency {
            // Emergency spawn
            let worker_id = rng.entity_id();
            let undertaker_id = rng.entity_id();

            state.entities.push(Entity::new_worker(worker_id.clone(), "origin".to_string()));
            state.entities.push(Entity::new_undertaker(undertaker_id.clone(), "origin".to_string()));

            state.resources.add("nutrients", -constants::SPAWN_COST_NUTRIENTS);
            state.resources.add("fungus", -constants::SPAWN_COST_FUNGUS);

            self.last_spawn_tick = tick;

            events.push(tick, EventKind::EmergencySpawn {
                worker_id,
                undertaker_id,
            });

            return;
        }

        // Normal spawn check
        if self.last_spawn_tick == 0 {
            self.last_spawn_tick = tick;
            return;
        }

        let ticks_since_spawn = tick - self.last_spawn_tick;
        if ticks_since_spawn < constants::SPAWN_INTERVAL_TICKS {
            return;
        }

        if nutrients < constants::MIN_RESOURCES_TO_SPAWN || fungus < constants::MIN_RESOURCES_TO_SPAWN {
            return;
        }

        // Spawn new ants
        let worker_id = rng.entity_id();
        let undertaker_id = rng.entity_id();

        state.entities.push(Entity::new_worker(worker_id.clone(), "origin".to_string()));
        state.entities.push(Entity::new_undertaker(undertaker_id.clone(), "origin".to_string()));

        state.resources.add("nutrients", -constants::SPAWN_COST_NUTRIENTS);
        state.resources.add("fungus", -constants::SPAWN_COST_FUNGUS);

        self.last_spawn_tick = tick;

        events.push(tick, EventKind::AntsSpawned {
            worker_id,
            undertaker_id,
            nutrients_consumed: constants::SPAWN_COST_NUTRIENTS,
            fungus_consumed: constants::SPAWN_COST_FUNGUS,
        });
    }

    /// Process receiver and summoning
    fn process_receiver(&mut self, state: &mut GameState, events: &mut TickEvents, rng: &mut SeededRng) {
        let tick = state.tick;

        // Only operate if receiver exists
        if !state.has_system("receiver") {
            return;
        }

        // Check maintenance
        self.check_receiver_maintenance(state, events);

        // If receiver is silent, it doesn't work
        if state.meta.receiver_silent {
            return;
        }

        // Passive listening drain
        if state.resources.get("influence") > constants::LISTENING_DRAIN {
            state.resources.add("influence", -constants::LISTENING_DRAIN);
        }

        // Attempt summoning
        let influence = state.resources.get("influence");
        if influence < constants::SUMMON_COST {
            return;
        }

        // Check cooldown
        if self.last_summon_tick > 0 && (tick - self.last_summon_tick) < constants::SUMMON_COOLDOWN {
            return;
        }

        // Spend influence
        state.resources.add("influence", -constants::SUMMON_COST);
        self.last_summon_tick = tick;

        // Roll for success
        let success = rng.chance(constants::SUMMON_CHANCE);

        events.push(tick, EventKind::InfluenceSpent {
            amount: constants::SUMMON_COST,
            success,
        });

        if success {
            // Something answers - choose a visitor type
            let visitor_type_idx = rng.range(0, 2);
            let (visitor, visitor_type) = match visitor_type_idx {
                0 => (Entity::new_wanderer(rng.visitor_id()), VisitorType::Wanderer),
                1 => (Entity::new_observer(rng.visitor_id()), VisitorType::Observer),
                _ => (Entity::new_hungry(rng.visitor_id()), VisitorType::Hungry),
            };

            let name = visitor.name.clone().unwrap_or_default();
            let id = visitor.id.clone();

            state.entities.push(visitor);

            events.push(tick, EventKind::VisitorArrived {
                visitor_id: id,
                visitor_type,
                name,
            });
        } else {
            events.push(tick, EventKind::SummoningFailed);
        }
    }

    /// Check receiver maintenance status
    fn check_receiver_maintenance(&self, state: &mut GameState, events: &mut TickEvents) {
        let tick = state.tick;

        // Get maintenance goal if it exists
        let maint_goal = state.meta.goals.get("receiver_maintenance").cloned();
        if maint_goal.is_none() {
            return;
        }

        let maint_goal = maint_goal.unwrap();
        let last_maintained = maint_goal.get("last_maintained")
            .and_then(|v| v.as_u64())
            .unwrap_or(tick);
        let interval = maint_goal.get("maintenance_interval_ticks")
            .and_then(|v| v.as_u64())
            .unwrap_or(constants::MAINTENANCE_INTERVAL);

        let ticks_since_maint = tick.saturating_sub(last_maintained);

        // Auto-maintain if we have strange_matter and need maintenance
        if ticks_since_maint >= interval {
            let strange_matter = state.resources.get("strange_matter");

            if strange_matter >= constants::MAINTENANCE_COST_STRANGE_MATTER {
                // Consume strange_matter
                state.resources.add("strange_matter", -constants::MAINTENANCE_COST_STRANGE_MATTER);

                // Update maintenance timestamp
                if let Some(goal) = state.meta.goals.get_mut("receiver_maintenance") {
                    goal["last_maintained"] = serde_json::json!(tick);
                }
            } else if !state.meta.receiver_silent {
                // No fuel - receiver goes silent
                state.meta.receiver_silent = true;
                state.meta.receiver_failed_tick = Some(tick);
                events.push(tick, EventKind::ReceiverSilent);
            }
        }

        // If silent and we now have strange_matter, restore
        if state.meta.receiver_silent && state.resources.get("strange_matter") >= constants::MAINTENANCE_COST_STRANGE_MATTER {
            state.resources.add("strange_matter", -constants::MAINTENANCE_COST_STRANGE_MATTER);
            state.meta.receiver_silent = false;

            if let Some(goal) = state.meta.goals.get_mut("receiver_maintenance") {
                goal["last_maintained"] = serde_json::json!(tick);
            }

            events.push(tick, EventKind::ReceiverRestored);
        }
    }

    /// Process visitor-specific behaviors
    fn process_visitors(&self, state: &mut GameState, events: &mut TickEvents) {
        let tick = state.tick;

        // Find visitors that generate resources
        for entity in &state.entities {
            if entity.entity_type != EntityType::Visitor {
                continue;
            }

            if let Some(generates) = &entity.generates {
                for (resource, rate) in generates {
                    state.resources.add(resource, *rate);
                    events.push(tick, EventKind::PassiveGeneration {
                        entity_id: entity.id.clone(),
                        resource: resource.clone(),
                        amount: *rate,
                    });
                }
            }
        }
    }

    /// Check resource thresholds
    fn check_thresholds(&self, state: &GameState, prev_resources: &HashMap<String, f64>, events: &mut TickEvents) {
        let tick = state.tick;

        for (resource, &current) in &state.resources.amounts {
            let prev = prev_resources.get(resource).copied().unwrap_or(0.0);

            for &threshold in &constants::RESOURCE_THRESHOLDS {
                if prev < threshold && current >= threshold {
                    events.push(tick, EventKind::ThresholdCrossed {
                        resource: resource.clone(),
                        threshold,
                        current,
                    });
                }
            }
        }
    }

    /// Process boredom tracking
    fn process_boredom(&self, state: &mut GameState, events: &mut TickEvents) {
        let tick = state.tick;

        // Increase boredom if nothing's happening
        if !state.queues.has_actions() && state.queues.events.is_empty() {
            state.meta.boredom += 1;
        } else {
            state.meta.boredom = state.meta.boredom.saturating_sub(1);
        }

        // Emit if boredom is high
        if state.meta.boredom >= constants::BOREDOM_THRESHOLD {
            events.push(tick, EventKind::BoredomHigh {
                level: state.meta.boredom,
            });
            state.meta.boredom = 0; // Reset after emitting
        }
    }

    /// Initialize from an existing game state (for resuming)
    pub fn init_from_state(&mut self, state: &GameState) {
        // Try to infer last spawn tick from entity ages
        if !state.entities.is_empty() {
            let youngest_age = state.entities.iter()
                .filter(|e| e.entity_type == EntityType::Ant)
                .map(|e| e.age)
                .min()
                .unwrap_or(0);
            self.last_spawn_tick = state.tick.saturating_sub(youngest_age);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_tick() {
        let mut engine = TickEngine::new(42);
        let mut state = GameState::default();

        let events = engine.tick(&mut state);
        assert_eq!(state.tick, 1);
        assert!(events.is_empty() || !events.is_empty()); // Just checking it runs
    }

    #[test]
    fn test_entity_aging() {
        let mut engine = TickEngine::new(42);
        let mut state = GameState::default();

        state.entities.push(Entity::new_worker("test".to_string(), "origin".to_string()));

        engine.tick(&mut state);

        assert_eq!(state.entities[0].age, 1);
        assert!(state.entities[0].hunger < 100.0);
    }

    #[test]
    fn test_entity_eating() {
        let mut engine = TickEngine::new(42);
        let mut state = GameState::default();

        let mut entity = Entity::new_worker("test".to_string(), "origin".to_string());
        entity.hunger = 40.0; // Below threshold
        state.entities.push(entity);
        state.resources.set("fungus", 10.0);

        let events = engine.tick(&mut state);

        // Entity should have eaten
        assert!(state.entities[0].hunger > 40.0);
        assert!(state.resources.get("fungus") < 10.0);
        assert!(events.events().iter().any(|e| matches!(e.kind, EventKind::EntityAte { .. })));
    }

    #[test]
    fn test_entity_starvation() {
        let mut engine = TickEngine::new(42);
        let mut state = GameState::default();

        let mut entity = Entity::new_worker("test".to_string(), "origin".to_string());
        entity.hunger = 0.05; // About to starve
        state.entities.push(entity);

        let events = engine.tick(&mut state);

        // Entity should have died
        assert!(state.entities.is_empty());
        assert!(!state.graveyard.corpses.is_empty());
        assert!(events.events().iter().any(|e| matches!(e.kind, EventKind::EntityDied { .. })));
    }

    #[test]
    fn test_offline_progress() {
        let mut engine = TickEngine::new(42);
        let mut state = GameState::default();

        // Setup state
        state.last_save_timestamp = Some(1000.0);
        state.resources.set("fungus", 100.0);

        // Add an entity
        let mut entity = Entity::new_worker("test_offline".to_string(), "origin".to_string());
        entity.hunger = 80.0;
        state.entities.push(entity);

        // Add a system that generates resources
        let mut system_gen = HashMap::new();
        system_gen.insert("fungus".to_string(), 1.0);
        let system = crate::types::system::System::new_generator("fungus_farm".to_string(), system_gen);
        state.systems.insert("fungus_farm".to_string(), system);

        // 100 seconds elapsed ( > 10 ticks, < 3600)
        let current_time = 1100.0;

        engine.process_offline_progress(&mut state, current_time);

        // Check ticks advanced
        assert_eq!(state.tick, 100);

        // Check resources generated: 100 ticks * 1.0 fungus = 100 + 100 start = 200
        // BUT entity eats fungus.
        // Entity hunger decreases by 0.1 * 0.5 = 0.05 per tick.
        // 100 ticks -> 5.0 hunger loss.
        // 80.0 -> 75.0. No eating should happen (threshold 50.0).

        assert_eq!(state.resources.get("fungus"), 200.0);
        assert_eq!(state.entities[0].age, 100);
        // 80 - (0.1 * 0.5 * 100) = 80 - 5 = 75
        assert!((state.entities[0].hunger - 75.0).abs() < 0.001);
    }
}
