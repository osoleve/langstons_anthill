/**
 * Corpse - a dead entity awaiting processing.
 *
 * Corpses linger visually, slowly fading as they decompose.
 * They emit subtle ghost particles and darken the tile beneath them.
 */

import type { Vec2, ServerCorpse, Role } from '../types'
import { COLORS, LAYOUT } from '../types'
import { withAlpha, lerp } from '../utils'

export class Corpse {
  readonly id: string
  readonly entityId: string
  readonly originalRole: Role

  position: Vec2
  decomposition: number  // 0.0 to 1.0

  // Visual state
  private ghostPhase: number
  private fadeAlpha: number

  constructor(data: ServerCorpse) {
    this.id = data.id
    this.entityId = data.entity_id
    this.originalRole = data.original_role || 'worker'
    this.position = { x: data.x, y: data.y }
    this.decomposition = data.decomposition

    this.ghostPhase = Math.random() * Math.PI * 2
    this.fadeAlpha = 1.0
  }

  updateFromServer(data: ServerCorpse): void {
    this.decomposition = data.decomposition
    // Fade as decomposition increases
    this.fadeAlpha = 1.0 - this.decomposition * 0.7
  }

  update(dt: number): void {
    this.ghostPhase += dt * 0.5
  }

  render(ctx: CanvasRenderingContext2D): void {
    const { x, y } = this.position
    const alpha = this.fadeAlpha

    // Dark stain beneath
    const stainRadius = LAYOUT.entityRadius * (1.5 + this.decomposition)
    const stainGradient = ctx.createRadialGradient(x, y, 0, x, y, stainRadius)
    stainGradient.addColorStop(0, withAlpha('#1a1015', alpha * 0.5))
    stainGradient.addColorStop(1, 'transparent')
    ctx.beginPath()
    ctx.arc(x, y, stainRadius, 0, Math.PI * 2)
    ctx.fillStyle = stainGradient
    ctx.fill()

    // Ghost silhouette (rises slightly as it decomposes)
    const rise = this.decomposition * 5
    const wobble = Math.sin(this.ghostPhase) * 2

    ctx.beginPath()
    ctx.arc(x + wobble, y - rise, LAYOUT.entityRadius * 0.8, 0, Math.PI * 2)
    ctx.fillStyle = withAlpha(COLORS.corpse, alpha * 0.6)
    ctx.fill()

    // Subtle upward particles (soul leaving)
    if (this.decomposition > 0.3) {
      const particleCount = Math.floor(this.decomposition * 3)
      for (let i = 0; i < particleCount; i++) {
        const phase = this.ghostPhase + i * 1.5
        const px = x + Math.sin(phase * 2) * 4
        const py = y - rise - 10 - Math.abs(Math.sin(phase)) * 15
        const pAlpha = (1 - (py - (y - rise - 10)) / 20) * alpha * 0.3

        ctx.beginPath()
        ctx.arc(px, py, 1.5, 0, Math.PI * 2)
        ctx.fillStyle = withAlpha('#8a7a9a', pAlpha)
        ctx.fill()
      }
    }
  }
}
