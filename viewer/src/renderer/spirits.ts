import type { GameState } from '../types/state.ts'
import { getTileCenter } from './tiles.ts'

interface Spirit {
  id: string
  x: number
  y: number
  baseY: number
  alpha: number
  phase: number
  isVisitor: boolean
}

const spirits: Map<string, Spirit> = new Map()

export function updateSpirits(state: GameState): void {
  const tiles = state.map?.tiles
  const corpses = state.graveyard?.corpses ?? []
  if (!tiles) return

  const corpseIds = new Set(corpses.map(c => c.entity_id))

  // Add new spirits for fresh corpses
  for (const corpse of corpses) {
    if (!spirits.has(corpse.entity_id)) {
      const center = getTileCenter(corpse.tile, tiles)
      if (center) {
        spirits.set(corpse.entity_id, {
          id: corpse.entity_id,
          x: center.x + (Math.random() - 0.5) * 40,
          y: center.y + (Math.random() - 0.5) * 40,
          baseY: center.y + (Math.random() - 0.5) * 40,
          alpha: 0.6,
          phase: Math.random() * Math.PI * 2,
          isVisitor: corpse.entity_type === 'visitor'
        })
      }
    }
  }

  // Update existing spirits - float upward slowly, fade
  for (const [id, spirit] of spirits) {
    spirit.phase += 0.02
    spirit.y = spirit.baseY + Math.sin(spirit.phase) * 5 - (spirit.phase * 0.3) // Drift upward
    spirit.alpha -= 0.0005 // Slow fade

    // Remove spirits that have faded or risen too high
    if (spirit.alpha <= 0 || spirit.y < spirit.baseY - 50) {
      spirits.delete(id)
    }
  }

  // Remove spirits for processed corpses
  for (const id of spirits.keys()) {
    if (!corpseIds.has(id)) {
      // Corpse was processed - accelerate fade
      const spirit = spirits.get(id)
      if (spirit) {
        spirit.alpha -= 0.02
        if (spirit.alpha <= 0) {
          spirits.delete(id)
        }
      }
    }
  }
}

export function drawSpirits(ctx: CanvasRenderingContext2D): void {
  for (const [_id, spirit] of spirits) {
    ctx.save()
    ctx.globalAlpha = spirit.alpha

    // Draw a wispy ghost shape
    const gradient = ctx.createRadialGradient(
      spirit.x, spirit.y, 0,
      spirit.x, spirit.y, 12
    )

    if (spirit.isVisitor) {
      // Visitor spirits are blue-tinged
      gradient.addColorStop(0, 'rgba(150, 180, 255, 0.8)')
      gradient.addColorStop(0.5, 'rgba(100, 130, 200, 0.4)')
      gradient.addColorStop(1, 'rgba(80, 100, 180, 0)')
    } else {
      // Ant spirits are pale amber
      gradient.addColorStop(0, 'rgba(220, 200, 180, 0.8)')
      gradient.addColorStop(0.5, 'rgba(180, 160, 140, 0.4)')
      gradient.addColorStop(1, 'rgba(150, 130, 110, 0)')
    }

    ctx.fillStyle = gradient
    ctx.beginPath()
    ctx.arc(spirit.x, spirit.y, 12, 0, Math.PI * 2)
    ctx.fill()

    // Small highlight
    ctx.beginPath()
    ctx.arc(spirit.x - 2, spirit.y - 2, 3, 0, Math.PI * 2)
    ctx.fillStyle = spirit.isVisitor ? 'rgba(200, 220, 255, 0.5)' : 'rgba(255, 250, 240, 0.5)'
    ctx.fill()

    ctx.restore()
  }
}
