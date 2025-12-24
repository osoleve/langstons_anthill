/**
 * Core types for the anthill viewer.
 * These mirror the server state but add visual-only properties.
 */

// Basic geometry
export interface Vec2 {
  x: number
  y: number
}

// Resource types from the game
export type ResourceType =
  | 'nutrients' | 'fungus' | 'ore' | 'crystals' | 'dirt'
  | 'influence' | 'insight' | 'strange_matter'

// Entity roles (must match Rust core)
export type Role = 'worker' | 'undertaker'

// Entity types
export type EntityType = 'ant' | 'visitor' | 'corpse'

// Tile types
export type TileType =
  | 'empty' | 'dirt' | 'chamber' | 'tunnel'
  | 'mine' | 'farm' | 'graveyard' | 'receiver'
  | 'crafting_hollow' | 'resonance_chamber'

// Activity states for animation
export type Activity = 'idle' | 'walking' | 'working' | 'dying' | 'drifting'

// Raw server state (what SSE sends us)
export interface ServerEntity {
  id: string
  type: EntityType
  role?: Role
  tile?: string  // Tile key (e.g., "origin")
  x?: number     // Optional direct coordinates
  y?: number
  age: number
  hunger: number
  hunger_rate?: number
  max_age?: number
  adorned?: boolean
  ornament?: string
  influence_rate?: number
}

export interface ServerTile {
  type: TileType
  x: number
  y: number
  system?: string
  contaminated?: boolean
  blighted?: boolean
}

export interface ServerCorpse {
  id: string
  entity_id: string
  x: number
  y: number
  tick_created: number
  decomposition: number
  original_role?: Role
}

export interface ServerState {
  tick: number
  resources: Record<ResourceType, number>
  entities: ServerEntity[]
  tiles: Record<string, ServerTile>
  graveyard: ServerCorpse[]
  meta: {
    sanity: number
    boredom: number
    goals?: Record<string, unknown>
    jewelry?: unknown[]
  }
  systems: Record<string, unknown>
}

// Colors for the palette
export const COLORS = {
  // Background and atmosphere
  background: '#0a0a0f',
  backgroundCalm: '#0a0f12',
  backgroundCrisis: '#120a0a',

  // Entity colors
  worker: '#c4a574',
  undertaker: '#7a6b8a',
  adorned: '#ffd700',
  visitor: '#00ffcc',
  corpse: '#4a4a4a',

  // Tile colors
  empty: '#1a1a1a',
  dirt: '#3d2817',
  chamber: '#2a2520',
  tunnel: '#252015',
  mine: '#4a4040',
  farm: '#2a3a2a',
  graveyard: '#1a1520',
  receiver: '#1a2530',

  // Effects
  trail: 'rgba(196, 165, 116, 0.15)',
  trailAdorned: 'rgba(255, 215, 0, 0.2)',
  constellation: 'rgba(255, 255, 255, 0.08)',
  deathRipple: 'rgba(120, 80, 120, 0.4)',
  blessing: 'rgba(255, 255, 200, 0.6)',
  influence: 'rgba(255, 215, 0, 0.3)',

  // UI
  text: '#b0a090',
  textDim: '#605850',
  panelBg: 'rgba(20, 18, 15, 0.85)',
  panelBorder: 'rgba(80, 70, 60, 0.5)',
} as const

// Layout constants
export const LAYOUT = {
  tileSize: 60,
  entityRadius: 6,
  trailLength: 25,
  constellationDistance: 100,
} as const
