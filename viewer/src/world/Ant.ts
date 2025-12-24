/**
 * Ant entity - a living, animated presence in the colony.
 *
 * Unlike the old viewer where ants were just data points,
 * each Ant is an actor with its own visual state, movement
 * interpolation, and rendering behavior.
 */

import type { Vec2, ServerEntity, Role, Activity } from '../types'
import { COLORS, LAYOUT } from '../types'
import { lerpVec2, distance, sub, normalize, withAlpha, easeOutQuad } from '../utils'

export class Ant {
  // Identity
  readonly id: string
  role: Role

  // Server state (updated from SSE)
  position: Vec2
  hunger: number
  age: number
  maxAge: number
  adorned: boolean
  ornament: string | null
  influenceRate: number

  // Visual state (local interpolation)
  visualPosition: Vec2
  facing: number  // radians, direction of movement
  activity: Activity
  trail: Vec2[]

  // Animation state
  private bobPhase: number
  private glowPhase: number
  private targetPosition: Vec2

  constructor(data: ServerEntity) {
    this.id = data.id
    this.role = data.role || 'worker'

    this.position = { x: data.x ?? 0, y: data.y ?? 0 }
    this.hunger = data.hunger
    this.age = data.age
    this.maxAge = data.max_age || 7200
    this.adorned = data.adorned || false
    this.ornament = data.ornament || null
    this.influenceRate = data.influence_rate || 0

    // Start visual position at actual position
    this.visualPosition = { ...this.position }
    this.targetPosition = { ...this.position }
    this.facing = Math.random() * Math.PI * 2
    this.activity = 'idle'
    this.trail = []

    this.bobPhase = Math.random() * Math.PI * 2
    this.glowPhase = Math.random() * Math.PI * 2
  }

  /**
   * Update from server state.
   * Only updates the target - visual state lerps toward it.
   */
  updateFromServer(data: ServerEntity): void {
    const oldPosition = { ...this.position }
    this.position = { x: data.x ?? 0, y: data.y ?? 0 }
    this.hunger = data.hunger
    this.age = data.age
    this.adorned = data.adorned || false
    this.ornament = data.ornament || null
    this.influenceRate = data.influence_rate || 0

    // If position changed significantly, update activity and facing
    const moved = distance(oldPosition, this.position)
    if (moved > 0.5) {
      this.activity = this.adorned ? 'drifting' : 'walking'
      const dir = sub(this.position, oldPosition)
      this.facing = Math.atan2(dir.y, dir.x)
    } else {
      this.activity = this.adorned ? 'drifting' : 'idle'
    }
  }

  /**
   * Per-frame update for smooth animation.
   * @param dt Delta time in seconds
   */
  update(dt: number): void {
    // Smooth movement toward actual position
    const lerpSpeed = this.adorned ? 1.5 : 3.0  // Adorned ants drift slowly
    this.visualPosition = lerpVec2(
      this.visualPosition,
      this.position,
      1 - Math.pow(0.01, dt * lerpSpeed)
    )

    // Update trail
    this.trail.push({ ...this.visualPosition })
    const maxTrail = this.adorned ? LAYOUT.trailLength * 1.5 : LAYOUT.trailLength
    while (this.trail.length > maxTrail) {
      this.trail.shift()
    }

    // Animation phases
    this.bobPhase += dt * (this.activity === 'walking' ? 8 : 2)
    this.glowPhase += dt * 1.5
  }

  /**
   * Render this ant to the canvas.
   */
  render(ctx: CanvasRenderingContext2D): void {
    this.renderTrail(ctx)
    this.renderBody(ctx)
    if (this.adorned) {
      this.renderInfluenceGlow(ctx)
      this.renderOrnament(ctx)
    }
  }

  private renderTrail(ctx: CanvasRenderingContext2D): void {
    if (this.trail.length < 2) return

    const trailColor = this.adorned ? COLORS.trailAdorned : COLORS.trail

    ctx.beginPath()
    ctx.moveTo(this.trail[0].x, this.trail[0].y)

    for (let i = 1; i < this.trail.length; i++) {
      const t = i / this.trail.length
      ctx.lineTo(this.trail[i].x, this.trail[i].y)
    }

    // Gradient stroke from transparent to trail color
    const gradient = ctx.createLinearGradient(
      this.trail[0].x, this.trail[0].y,
      this.visualPosition.x, this.visualPosition.y
    )
    gradient.addColorStop(0, 'transparent')
    gradient.addColorStop(1, trailColor)

    ctx.strokeStyle = gradient
    ctx.lineWidth = this.adorned ? 3 : 2
    ctx.lineCap = 'round'
    ctx.stroke()
  }

  private renderBody(ctx: CanvasRenderingContext2D): void {
    const { x, y } = this.visualPosition
    const bob = Math.sin(this.bobPhase) * (this.activity === 'walking' ? 1 : 0.3)

    // Base color by role
    const roleColor = this.role === 'worker' ? COLORS.worker : COLORS.undertaker

    // Health indicator (darker when hungry)
    const healthFactor = Math.max(0.4, this.hunger / 100)
    const r = parseInt(roleColor.slice(1, 3), 16)
    const g = parseInt(roleColor.slice(3, 5), 16)
    const b = parseInt(roleColor.slice(5, 7), 16)
    let baseColor = `rgb(${Math.floor(r * healthFactor)}, ${Math.floor(g * healthFactor)}, ${Math.floor(b * healthFactor)})`

    // Adorned ants get a golden tint
    if (this.adorned) {
      baseColor = COLORS.adorned as string
    }

    // Body circle
    ctx.beginPath()
    ctx.arc(x, y + bob, LAYOUT.entityRadius, 0, Math.PI * 2)
    ctx.fillStyle = baseColor
    ctx.fill()

    // Subtle outline
    ctx.strokeStyle = withAlpha(baseColor, 0.3)
    ctx.lineWidth = 1
    ctx.stroke()

    // Direction indicator (small notch)
    const headX = x + Math.cos(this.facing) * LAYOUT.entityRadius * 0.8
    const headY = y + bob + Math.sin(this.facing) * LAYOUT.entityRadius * 0.8
    ctx.beginPath()
    ctx.arc(headX, headY, 2, 0, Math.PI * 2)
    ctx.fillStyle = withAlpha('#ffffff', 0.3)
    ctx.fill()
  }

  private renderInfluenceGlow(ctx: CanvasRenderingContext2D): void {
    const { x, y } = this.visualPosition
    const pulseSize = 1 + Math.sin(this.glowPhase) * 0.2
    const radius = LAYOUT.entityRadius * 3 * pulseSize

    const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius)
    gradient.addColorStop(0, withAlpha(COLORS.influence, 0.4))
    gradient.addColorStop(0.5, withAlpha(COLORS.influence, 0.15))
    gradient.addColorStop(1, 'transparent')

    ctx.beginPath()
    ctx.arc(x, y, radius, 0, Math.PI * 2)
    ctx.fillStyle = gradient
    ctx.fill()
  }

  private renderOrnament(ctx: CanvasRenderingContext2D): void {
    const { x, y } = this.visualPosition
    const bob = Math.sin(this.bobPhase) * 0.3

    // Simple ring indicator above the ant
    ctx.beginPath()
    ctx.arc(x, y + bob - LAYOUT.entityRadius - 4, 3, 0, Math.PI * 2)
    ctx.strokeStyle = COLORS.adorned
    ctx.lineWidth = 1.5
    ctx.stroke()
  }

  /**
   * Get the ant's color for constellation drawing.
   */
  getColor(): string {
    if (this.adorned) return COLORS.adorned
    return this.role === 'worker' ? COLORS.worker : COLORS.undertaker
  }

  /**
   * Is this ant close to dying?
   */
  isDying(): boolean {
    return this.hunger < 20 || this.age > this.maxAge * 0.9
  }
}
