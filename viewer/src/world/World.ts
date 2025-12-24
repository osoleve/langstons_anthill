/**
 * World - the container for all entities, tiles, and effects.
 *
 * The World reacts to state updates from SSE, manages entity lifecycles,
 * and orchestrates updates and rendering.
 */

import type { Vec2, ServerState, ResourceType } from '../types'
import { LAYOUT } from '../types'
import { Ant } from './Ant'
import { Tile } from './Tile'
import { Corpse } from './Corpse'

export class World {
  // Current state
  tick: number = 0
  resources: Map<ResourceType, number> = new Map()
  sanity: number = 100
  boredom: number = 0

  // Entities
  ants: Map<string, Ant> = new Map()
  tiles: Map<string, Tile> = new Map()
  corpses: Map<string, Corpse> = new Map()

  // Death tracking for ripple effects
  recentDeaths: { position: Vec2; time: number; role: string }[] = []

  // Bounds (computed from tiles)
  bounds: { minX: number; minY: number; maxX: number; maxY: number } = {
    minX: 0, minY: 0, maxX: 0, maxY: 0
  }

  /**
   * Apply a full state update from the server.
   * This is called on initial load and periodically to sync.
   */
  applyState(state: ServerState): void {
    const previousAntIds = new Set(this.ants.keys())

    this.tick = state.tick
    this.sanity = state.meta?.sanity ?? 100
    this.boredom = state.meta?.boredom ?? 0

    // Update resources
    this.resources.clear()
    for (const [key, value] of Object.entries(state.resources)) {
      this.resources.set(key as ResourceType, value)
    }

    // Update tiles (can be state.tiles or state.map.tiles)
    const tilesData = state.tiles || (state as any).map?.tiles || {}
    for (const [key, tileData] of Object.entries(tilesData)) {
      const existing = this.tiles.get(key)
      if (existing) {
        existing.updateFromServer(tileData)
      } else {
        this.tiles.set(key, new Tile(tileData))
      }
    }
    this.computeBounds()

    // Update ants
    const currentAntIds = new Set<string>()
    for (const entityData of state.entities) {
      if (entityData.type !== 'ant') continue

      // Resolve position from tile if x/y not provided
      let x = entityData.x
      let y = entityData.y
      if ((x === undefined || y === undefined) && entityData.tile) {
        const tile = this.tiles.get(entityData.tile)
        if (tile) {
          // Position at tile center with small random offset for visual variety
          x = tile.position.x * LAYOUT.tileSize + LAYOUT.tileSize / 2
          y = tile.position.y * LAYOUT.tileSize + LAYOUT.tileSize / 2
          // Add per-entity offset based on id hash
          const hash = entityData.id.charCodeAt(0) + entityData.id.charCodeAt(1) * 256
          x += ((hash % 30) - 15)
          y += (((hash >> 8) % 30) - 15)
        }
      }

      // Create augmented entity data with resolved position
      const resolvedData = { ...entityData, x: x ?? 0, y: y ?? 0 }

      currentAntIds.add(entityData.id)
      const existing = this.ants.get(entityData.id)

      if (existing) {
        existing.updateFromServer(resolvedData)
      } else {
        this.ants.set(entityData.id, new Ant(resolvedData))
      }
    }

    // Detect deaths
    for (const id of previousAntIds) {
      if (!currentAntIds.has(id)) {
        const deadAnt = this.ants.get(id)
        if (deadAnt) {
          this.recentDeaths.push({
            position: { ...deadAnt.visualPosition },
            time: performance.now(),
            role: deadAnt.role,
          })
          this.ants.delete(id)
        }
      }
    }

    // Clean old deaths (keep for 3 seconds for ripple effect)
    const now = performance.now()
    this.recentDeaths = this.recentDeaths.filter(d => now - d.time < 3000)

    // Update corpses (graveyard can be { corpses: [...] } or just [...])
    const currentCorpseIds = new Set<string>()
    const graveyard = state.graveyard as any
    const corpseList = Array.isArray(graveyard)
      ? graveyard
      : (graveyard?.corpses || [])
    for (const corpseData of corpseList) {
      currentCorpseIds.add(corpseData.id)
      const existing = this.corpses.get(corpseData.id)

      if (existing) {
        existing.updateFromServer(corpseData)
      } else {
        const corpse = new Corpse(corpseData)
        this.corpses.set(corpseData.id, corpse)

        // Record corpse on tile
        const tileKey = `${Math.floor(corpseData.x)},${Math.floor(corpseData.y)}`
        const tile = this.tiles.get(tileKey)
        if (tile) tile.recordCorpse()
      }
    }

    // Remove processed corpses
    for (const id of this.corpses.keys()) {
      if (!currentCorpseIds.has(id)) {
        this.corpses.delete(id)
      }
    }
  }

  /**
   * Per-frame update for animations.
   */
  update(dt: number): void {
    for (const ant of this.ants.values()) {
      ant.update(dt)
    }
    for (const tile of this.tiles.values()) {
      tile.update(dt)
    }
    for (const corpse of this.corpses.values()) {
      corpse.update(dt)
    }
  }

  /**
   * Get all ants as an array (for rendering, constellation, etc).
   */
  getAnts(): Ant[] {
    return Array.from(this.ants.values())
  }

  /**
   * Get all corpses as an array.
   */
  getCorpses(): Corpse[] {
    return Array.from(this.corpses.values())
  }

  /**
   * Get world center in screen coordinates.
   */
  getCenter(): Vec2 {
    return {
      x: ((this.bounds.minX + this.bounds.maxX) / 2) * LAYOUT.tileSize,
      y: ((this.bounds.minY + this.bounds.maxY) / 2) * LAYOUT.tileSize,
    }
  }

  /**
   * Get world size in screen coordinates.
   */
  getSize(): Vec2 {
    return {
      x: (this.bounds.maxX - this.bounds.minX + 1) * LAYOUT.tileSize,
      y: (this.bounds.maxY - this.bounds.minY + 1) * LAYOUT.tileSize,
    }
  }

  private computeBounds(): void {
    let minX = Infinity, minY = Infinity
    let maxX = -Infinity, maxY = -Infinity

    for (const tile of this.tiles.values()) {
      minX = Math.min(minX, tile.position.x)
      minY = Math.min(minY, tile.position.y)
      maxX = Math.max(maxX, tile.position.x)
      maxY = Math.max(maxY, tile.position.y)
    }

    // Default to a small area if no tiles
    if (!isFinite(minX)) {
      minX = -2; minY = -2; maxX = 2; maxY = 2
    }

    this.bounds = { minX, minY, maxX, maxY }
  }
}
