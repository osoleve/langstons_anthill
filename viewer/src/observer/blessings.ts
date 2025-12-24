/**
 * Observer Blessing System
 *
 * Observers (humans watching the viewer) can interact with the colony
 * by clicking to grant blessings. Each blessing creates a visual spectacle
 * and generates resources for the colony.
 */

import type { GameState } from '../types/state.ts'

export interface Blessing {
  id: number
  x: number
  y: number
  type: BlessingType
  startTime: number
  duration: number
  particles: BlessingParticle[]
  radius: number
  maxRadius: number
  tileId: string | null
}

export interface BlessingParticle {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  maxLife: number
  size: number
  color: string
  trail: { x: number; y: number }[]
}

export type BlessingType = 'touch' | 'gift' | 'miracle' | 'attention'

interface BlessingConfig {
  color: string
  glowColor: string
  particleCount: number
  duration: number
  resourceType: string
  resourceAmount: number
  description: string
}

const BLESSING_CONFIGS: Record<BlessingType, BlessingConfig> = {
  touch: {
    color: '#88ccff',
    glowColor: 'rgba(136, 204, 255, 0.3)',
    particleCount: 20,
    duration: 1500,
    resourceType: 'influence',
    resourceAmount: 0.1,
    description: 'A gentle touch from the Outside'
  },
  gift: {
    color: '#ffcc44',
    glowColor: 'rgba(255, 204, 68, 0.3)',
    particleCount: 40,
    duration: 2000,
    resourceType: 'nutrients',
    resourceAmount: 5,
    description: 'A gift of nourishment'
  },
  miracle: {
    color: '#ff88ff',
    glowColor: 'rgba(255, 136, 255, 0.4)',
    particleCount: 80,
    duration: 3000,
    resourceType: 'strange_matter',
    resourceAmount: 0.05,
    description: 'A miracle from beyond'
  },
  attention: {
    color: '#88ff88',
    glowColor: 'rgba(136, 255, 136, 0.3)',
    particleCount: 30,
    duration: 1800,
    resourceType: 'insight',
    resourceAmount: 0.02,
    description: 'The weight of observation'
  }
}

let blessings: Blessing[] = []
let blessingIdCounter = 0
let pendingBlessings: { tileId: string; type: BlessingType; amount: number }[] = []
let lastBlessingTime = 0
const BLESSING_COOLDOWN = 100 // ms between blessings (was 500 - too slow)

// Track click patterns for combo blessings
let recentClicks: { x: number; y: number; time: number }[] = []
const COMBO_WINDOW = 2000 // ms (was 1000 - more forgiving)
const COMBO_THRESHOLD = 3 // clicks needed for miracle (was 5 - easier to trigger)

export function createBlessing(x: number, y: number, tileId: string | null, state: GameState): Blessing | null {
  const now = Date.now()

  // ALWAYS track clicks for combo, even during cooldown
  recentClicks.push({ x, y, time: now })
  recentClicks = recentClicks.filter(c => now - c.time < COMBO_WINDOW)

  // Check cooldown (but still tracked the click above)
  if (now - lastBlessingTime < BLESSING_COOLDOWN) {
    return null
  }

  lastBlessingTime = now

  // Determine blessing type based on context
  let type: BlessingType = 'touch'

  if (recentClicks.length >= COMBO_THRESHOLD) {
    type = 'miracle'
    recentClicks = [] // Reset combo
  } else if (tileId && state.systems[tileId]) {
    // Clicking on a system tile gives a gift
    type = 'gift'
  } else if (state.entities.length > 0) {
    // Check if near an entity
    type = 'attention'
  }

  const config = BLESSING_CONFIGS[type]

  const blessing: Blessing = {
    id: blessingIdCounter++,
    x,
    y,
    type,
    startTime: now,
    duration: config.duration,
    particles: [],
    radius: 0,
    maxRadius: 80 + Math.random() * 40,
    tileId
  }

  // Create particles
  for (let i = 0; i < config.particleCount; i++) {
    const angle = (Math.PI * 2 * i) / config.particleCount + Math.random() * 0.3
    const speed = 1 + Math.random() * 2

    blessing.particles.push({
      x: x,
      y: y,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      life: 1,
      maxLife: 0.6 + Math.random() * 0.4,
      size: 2 + Math.random() * 3,
      color: config.color,
      trail: []
    })
  }

  blessings.push(blessing)

  // Queue the resource generation
  if (tileId) {
    pendingBlessings.push({
      tileId,
      type,
      amount: config.resourceAmount
    })
  }

  return blessing
}

export function updateBlessings(): void {
  const now = Date.now()

  blessings = blessings.filter(blessing => {
    const elapsed = now - blessing.startTime
    const progress = elapsed / blessing.duration

    if (progress >= 1) {
      return false
    }

    // Expand radius
    blessing.radius = blessing.maxRadius * Math.sin(progress * Math.PI)

    // Update particles
    blessing.particles.forEach(p => {
      // Store trail
      p.trail.push({ x: p.x, y: p.y })
      if (p.trail.length > 8) {
        p.trail.shift()
      }

      // Move particle
      p.x += p.vx
      p.y += p.vy

      // Slow down
      p.vx *= 0.98
      p.vy *= 0.98

      // Fade
      p.life = 1 - progress / p.maxLife
      if (p.life < 0) p.life = 0
    })

    return true
  })
}

export function drawBlessings(ctx: CanvasRenderingContext2D): void {
  blessings.forEach(blessing => {
    const config = BLESSING_CONFIGS[blessing.type]
    const elapsed = Date.now() - blessing.startTime
    const progress = elapsed / blessing.duration

    // Draw expanding ring
    ctx.save()
    ctx.beginPath()
    ctx.arc(blessing.x, blessing.y, blessing.radius, 0, Math.PI * 2)
    ctx.strokeStyle = config.color
    ctx.lineWidth = 2 * (1 - progress)
    ctx.globalAlpha = 0.6 * (1 - progress)
    ctx.stroke()

    // Inner glow
    const gradient = ctx.createRadialGradient(
      blessing.x, blessing.y, 0,
      blessing.x, blessing.y, blessing.radius * 0.6
    )
    gradient.addColorStop(0, config.glowColor)
    gradient.addColorStop(1, 'transparent')
    ctx.fillStyle = gradient
    ctx.globalAlpha = 0.4 * (1 - progress)
    ctx.fill()
    ctx.restore()

    // Draw particles with trails
    blessing.particles.forEach(p => {
      if (p.life <= 0) return

      // Draw trail
      if (p.trail.length > 1) {
        ctx.save()
        ctx.beginPath()
        ctx.moveTo(p.trail[0].x, p.trail[0].y)
        for (let i = 1; i < p.trail.length; i++) {
          ctx.lineTo(p.trail[i].x, p.trail[i].y)
        }
        ctx.lineTo(p.x, p.y)
        ctx.strokeStyle = p.color
        ctx.lineWidth = p.size * 0.5 * p.life
        ctx.globalAlpha = 0.3 * p.life
        ctx.stroke()
        ctx.restore()
      }

      // Draw particle
      ctx.save()
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2)
      ctx.fillStyle = p.color
      ctx.globalAlpha = p.life
      ctx.shadowColor = p.color
      ctx.shadowBlur = 10
      ctx.fill()
      ctx.restore()
    })
  })
}

export function getPendingBlessings(): { tileId: string; type: BlessingType; amount: number }[] {
  const pending = [...pendingBlessings]
  pendingBlessings = []
  return pending
}

export function getBlessingCount(): number {
  return blessings.length
}

export function getComboProgress(): number {
  const now = Date.now()
  const validClicks = recentClicks.filter(c => now - c.time < COMBO_WINDOW)
  return Math.min(1, validClicks.length / COMBO_THRESHOLD)
}
