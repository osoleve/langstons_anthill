// Types matching state/game.json exactly

export interface Resources {
  dirt?: number
  nutrients?: number
  fungus?: number
  crystals?: number
  ore?: number
  influence?: number
  insight?: number
  strange_matter?: number
  [key: string]: number | undefined
}

export interface System {
  name: string
  type: string
  description?: string
  generates?: Record<string, number>
  consumes?: Record<string, number>
  original_generates?: Record<string, number>
  original_consumes?: Record<string, number>
  corpse_boosts?: string[]
  sanity_efficiency?: number
}

export interface Tile {
  name: string
  type: string
  x: number
  y: number
  description?: string
  resource?: string
  contamination?: number
  blighted?: boolean
  blight_ticks_remaining?: number
}

export interface Entity {
  id: string
  type: 'ant' | 'visitor'
  role?: string
  subtype?: string
  name?: string
  tile: string
  age: number
  hunger: number
  hunger_rate: number
  max_age: number
  food: string
  adorned?: boolean
  ornament?: string
  previous_role?: string
  influence_rate?: number
  processing_corpse?: boolean
  processing_ticks?: number
  from_outside?: boolean
  description?: string
  generates?: Record<string, number>
}

export interface Corpse {
  id: string
  original_role: string
  died_at: number
  cause: string
  biomass: number
}

export interface Graveyard {
  corpses: Corpse[]
  total_processed: number
}

export interface Jewelry {
  type: string
  name: string
  created_tick: number
  worn_by: string
  worn_tick: number
}

export interface Decor {
  name: string
  type: string
  origin: string
  description: string
  location: string
  acquired_tick: number
}

export interface Goal {
  name: string
  description: string
  cost: Record<string, number>
  effect: Record<string, unknown>
  built: boolean
  progress?: Record<string, number>
  maintenance_interval_ticks?: number
  last_maintained?: number
}

export interface Reflection {
  tick: number
  trigger: string
  prompt: string
  response: string | null
}

export interface Estate {
  name: string
  named_tick: number
  description: string
}

export interface EventLogEntry {
  type: string
  tick: number
  timestamp: string
  message: string
  details?: Record<string, unknown>
}

export interface Meta {
  boredom: number
  recent_decisions: unknown[]
  rejected_ideas: string[]
  fired_cards: string[]
  goals: Record<string, Goal>
  reflections: Reflection[]
  sanity: number
  receiver_silent: boolean
  receiver_failed_tick?: number
  receiver_bootstrap_tick?: number
  sanity_crisis: boolean
  sanity_breaking: boolean
  estate?: Estate
  decor?: Decor[]
  jewelry?: Jewelry[]
  event_log?: EventLogEntry[]
}

export interface MapData {
  tiles: Record<string, Tile>
  connections: [string, string][]
}

export interface Queues {
  actions: unknown[]
  events: unknown[]
}

export interface GameState {
  tick: number
  resources: Resources
  systems: Record<string, System>
  entities: Entity[]
  map: MapData
  queues: Queues
  meta: Meta
  graveyard: Graveyard
  last_save_timestamp: number
}
