/**
 * Tile - a living space in the colony that remembers its history.
 *
 * Tiles aren't just colored rectangles. They accumulate wear from
 * footfalls, darken from decomposition, and show the passage of time.
 */

import type { Vec2, ServerTile, TileType } from '../types'
import { COLORS, LAYOUT } from '../types'
import { withAlpha, lerp, clamp } from '../utils'

// Tile type colors and properties
const TILE_CONFIG: Record<TileType, { color: string; workable: boolean }> = {
  empty: { color: COLORS.empty, workable: false },
  dirt: { color: COLORS.dirt, workable: false },
  chamber: { color: COLORS.chamber, workable: false },
  tunnel: { color: COLORS.tunnel, workable: false },
  mine: { color: COLORS.mine, workable: true },
  farm: { color: COLORS.farm, workable: true },
  graveyard: { color: COLORS.graveyard, workable: true },
  receiver: { color: COLORS.receiver, workable: true },
  crafting_hollow: { color: '#2a2a25', workable: true },
  resonance_chamber: { color: '#252535', workable: true },
}

export class Tile {
  readonly key: string  // "x,y" for map lookup
  type: TileType
  position: Vec2
  system: string | null
  contaminated: boolean
  blighted: boolean

  // Accumulated history (visual only, not persisted)
  footfalls: number = 0
  lastWorked: number = 0
  corpseCount: number = 0

  // Visual state
  private pulsePhase: number

  constructor(data: ServerTile) {
    this.key = `${data.x},${data.y}`
    this.type = data.type
    this.position = { x: data.x, y: data.y }
    this.system = data.system || null
    this.contaminated = data.contaminated || false
    this.blighted = data.blighted || false

    this.pulsePhase = Math.random() * Math.PI * 2
  }

  updateFromServer(data: ServerTile): void {
    this.type = data.type
    this.system = data.system || null
    this.contaminated = data.contaminated || false
    this.blighted = data.blighted || false
  }

  /**
   * Called when an entity moves onto this tile.
   */
  recordFootfall(): void {
    this.footfalls++
  }

  /**
   * Called when a corpse is placed here.
   */
  recordCorpse(): void {
    this.corpseCount++
  }

  /**
   * Called when work is performed (mining, farming, etc).
   */
  recordWork(tick: number): void {
    this.lastWorked = tick
  }

  update(dt: number): void {
    this.pulsePhase += dt * 0.5
  }

  /**
   * Render this tile to the canvas.
   */
  render(ctx: CanvasRenderingContext2D, currentTick: number): void {
    const config = TILE_CONFIG[this.type] || TILE_CONFIG.empty
    const size = LAYOUT.tileSize
    const x = this.position.x * size
    const y = this.position.y * size

    // Base color
    let baseColor = config.color

    // Apply wear (paths form where ants walk)
    const wearLevel = clamp(this.footfalls / 500, 0, 1)
    if (wearLevel > 0.1) {
      // Worn paths are slightly lighter, more packed
      baseColor = this.blendColor(baseColor, '#3a3530', wearLevel * 0.3)
    }

    // Apply fertility from corpses (darker, richer soil)
    const fertility = clamp(this.corpseCount * 0.1, 0, 0.5)
    if (fertility > 0) {
      baseColor = this.blendColor(baseColor, '#1a1020', fertility)
    }

    // Blight overlay
    if (this.blighted) {
      baseColor = this.blendColor(baseColor, '#200810', 0.6)
    } else if (this.contaminated) {
      baseColor = this.blendColor(baseColor, '#201010', 0.3)
    }

    // Draw base tile
    ctx.fillStyle = baseColor
    ctx.fillRect(x, y, size, size)

    // Subtle border
    ctx.strokeStyle = withAlpha('#000000', 0.2)
    ctx.lineWidth = 1
    ctx.strokeRect(x + 0.5, y + 0.5, size - 1, size - 1)

    // Work activity indicator (pulse when recently worked)
    if (config.workable && currentTick - this.lastWorked < 60) {
      const recentness = 1 - (currentTick - this.lastWorked) / 60
      const pulse = Math.sin(this.pulsePhase * 4) * 0.5 + 0.5
      ctx.fillStyle = withAlpha('#ffffff', recentness * pulse * 0.1)
      ctx.fillRect(x, y, size, size)
    }

    // System icon hint (if this tile has a system)
    if (this.system) {
      this.renderSystemHint(ctx, x, y, size)
    }

    // Blight visual
    if (this.blighted) {
      this.renderBlight(ctx, x, y, size)
    }
  }

  private renderSystemHint(ctx: CanvasRenderingContext2D, x: number, y: number, size: number): void {
    // Small icon in corner indicating system type
    const iconSize = 8
    const padding = 4
    const ix = x + size - iconSize - padding
    const iy = y + padding

    ctx.fillStyle = withAlpha('#ffffff', 0.15)

    // Different shapes for different systems
    switch (this.type) {
      case 'mine':
        // Pickaxe shape (triangle)
        ctx.beginPath()
        ctx.moveTo(ix, iy + iconSize)
        ctx.lineTo(ix + iconSize / 2, iy)
        ctx.lineTo(ix + iconSize, iy + iconSize)
        ctx.closePath()
        ctx.fill()
        break
      case 'farm':
        // Mushroom shape (circle on stem)
        ctx.beginPath()
        ctx.arc(ix + iconSize / 2, iy + 3, 4, 0, Math.PI * 2)
        ctx.fill()
        ctx.fillRect(ix + iconSize / 2 - 1, iy + 4, 2, 4)
        break
      case 'graveyard':
        // Cross
        ctx.fillRect(ix + iconSize / 2 - 1, iy, 2, iconSize)
        ctx.fillRect(ix, iy + 3, iconSize, 2)
        break
      case 'receiver':
        // Antenna (vertical line with circle)
        ctx.fillRect(ix + iconSize / 2 - 1, iy + 2, 2, iconSize - 2)
        ctx.beginPath()
        ctx.arc(ix + iconSize / 2, iy + 2, 2, 0, Math.PI * 2)
        ctx.fill()
        break
      default:
        // Generic dot
        ctx.beginPath()
        ctx.arc(ix + iconSize / 2, iy + iconSize / 2, 3, 0, Math.PI * 2)
        ctx.fill()
    }
  }

  private renderBlight(ctx: CanvasRenderingContext2D, x: number, y: number, size: number): void {
    // Pulsing corruption effect
    const pulse = Math.sin(this.pulsePhase) * 0.5 + 0.5

    // Dark tendrils from edges
    ctx.strokeStyle = withAlpha('#400020', 0.3 + pulse * 0.2)
    ctx.lineWidth = 2
    ctx.beginPath()

    // Random-ish tendrils based on position
    const seed = this.position.x * 7 + this.position.y * 13
    for (let i = 0; i < 3; i++) {
      const startEdge = (seed + i * 3) % 4
      let sx: number, sy: number, ex: number, ey: number

      switch (startEdge) {
        case 0: sx = x + (seed * i) % size; sy = y; ex = x + size / 2; ey = y + size / 2; break
        case 1: sx = x + size; sy = y + (seed * i) % size; ex = x + size / 2; ey = y + size / 2; break
        case 2: sx = x + (seed * i) % size; sy = y + size; ex = x + size / 2; ey = y + size / 2; break
        default: sx = x; sy = y + (seed * i) % size; ex = x + size / 2; ey = y + size / 2;
      }

      ctx.moveTo(sx, sy)
      ctx.quadraticCurveTo(
        (sx + ex) / 2 + Math.sin(this.pulsePhase + i) * 10,
        (sy + ey) / 2 + Math.cos(this.pulsePhase + i) * 10,
        ex, ey
      )
    }
    ctx.stroke()
  }

  private blendColor(color1: string, color2: string, t: number): string {
    const parse = (hex: string) => ({
      r: parseInt(hex.slice(1, 3), 16),
      g: parseInt(hex.slice(3, 5), 16),
      b: parseInt(hex.slice(5, 7), 16),
    })

    const c1 = parse(color1)
    const c2 = parse(color2)

    const r = Math.round(lerp(c1.r, c2.r, t))
    const g = Math.round(lerp(c1.g, c2.g, t))
    const b = Math.round(lerp(c1.b, c2.b, t))

    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
  }
}
