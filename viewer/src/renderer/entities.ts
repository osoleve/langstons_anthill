import type { GameState, Entity, Tile } from '../types/state.ts'
import { getTileCenter } from './tiles.ts'

interface EntityDot {
  x: number
  y: number
  targetX: number
  targetY: number
  type: 'ant' | 'visitor'
  subtype?: string
  adorned?: boolean
}

const entityDots: Map<string, EntityDot> = new Map()

export function updateEntityDots(state: GameState): void {
  const tiles = state.map?.tiles
  const entities = state.entities
  if (!tiles || !entities) return

  // Update or create dots for each entity
  for (const entity of entities) {
    const tileCenter = getTileCenter(entity.tile, tiles)
    if (!tileCenter) continue

    let dot = entityDots.get(entity.id)
    if (!dot) {
      // Create new dot with random offset within tile
      dot = {
        x: tileCenter.x + (Math.random() - 0.5) * 60,
        y: tileCenter.y + (Math.random() - 0.5) * 60,
        targetX: tileCenter.x + (Math.random() - 0.5) * 60,
        targetY: tileCenter.y + (Math.random() - 0.5) * 60,
        type: entity.type,
        subtype: entity.subtype,
        adorned: entity.adorned
      }
      entityDots.set(entity.id, dot)
    }

    // Slowly drift toward target
    dot.x += (dot.targetX - dot.x) * 0.02
    dot.y += (dot.targetY - dot.y) * 0.02

    // Pick new target occasionally
    if (Math.random() < 0.01) {
      dot.targetX = tileCenter.x + (Math.random() - 0.5) * 60
      dot.targetY = tileCenter.y + (Math.random() - 0.5) * 60
    }

    // Update entity properties
    dot.type = entity.type
    dot.subtype = entity.subtype
    dot.adorned = entity.adorned
  }

  // Remove dots for dead entities
  const livingIds = new Set(entities.map(e => e.id))
  for (const id of entityDots.keys()) {
    if (!livingIds.has(id)) {
      entityDots.delete(id)
    }
  }
}

export function drawEntityDots(ctx: CanvasRenderingContext2D): void {
  for (const [_id, dot] of entityDots) {
    ctx.beginPath()
    const size = dot.adorned ? 5 : 4

    if (dot.type === 'visitor') {
      // Visitors glow blue (or red if hungry)
      const color = dot.subtype === 'hungry' ? '#f88' : '#8af'
      ctx.arc(dot.x, dot.y, size, 0, Math.PI * 2)
      ctx.fillStyle = color
      ctx.shadowColor = color
      ctx.shadowBlur = 8
    } else if (dot.adorned) {
      // Adorned ants have golden glow
      ctx.arc(dot.x, dot.y, size, 0, Math.PI * 2)
      ctx.fillStyle = '#ca8'
      ctx.shadowColor = '#ca8'
      ctx.shadowBlur = 6
    } else {
      // Regular ants
      ctx.arc(dot.x, dot.y, size - 1, 0, Math.PI * 2)
      ctx.fillStyle = '#a85'
      ctx.shadowBlur = 0
    }

    ctx.fill()
    ctx.shadowBlur = 0
  }
}
