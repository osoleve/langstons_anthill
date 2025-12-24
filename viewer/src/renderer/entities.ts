import type { GameState, Entity, Tile } from '../types/state.ts'
import { getTileCenter } from './tiles.ts'

interface TrailPoint {
  x: number
  y: number
  age: number
}

interface EntityDot {
  x: number
  y: number
  targetX: number
  targetY: number
  type: 'ant' | 'visitor'
  subtype?: string
  adorned?: boolean
  entity: Entity
  trail: TrailPoint[]
  pulsePhase: number
}

// Death ripple effect
interface DeathRipple {
  x: number
  y: number
  radius: number
  maxRadius: number
  alpha: number
  color: string
  startTime: number
}

const entityDots: Map<string, EntityDot> = new Map()
const deathRipples: DeathRipple[] = []
const TRAIL_LENGTH = 12
const TRAIL_RECORD_INTERVAL = 3 // frames between trail points
const CONSTELLATION_DISTANCE = 100 // max distance for constellation lines
const CONSTELLATION_ALPHA = 0.15

// Expose positions for tooltip system
export function getEntityDots(): Map<string, EntityDot> {
  return entityDots
}

let frameCount = 0

export function updateEntityDots(state: GameState): void {
  const tiles = state.map?.tiles
  const entities = state.entities
  if (!tiles || !entities) return

  frameCount++

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
        adorned: entity.adorned,
        entity: entity,
        trail: [],
        pulsePhase: Math.random() * Math.PI * 2
      }
      entityDots.set(entity.id, dot)
    }

    // Record trail position periodically
    if (frameCount % TRAIL_RECORD_INTERVAL === 0) {
      dot.trail.push({ x: dot.x, y: dot.y, age: 0 })
      if (dot.trail.length > TRAIL_LENGTH) {
        dot.trail.shift()
      }
    }

    // Age trail points
    for (const point of dot.trail) {
      point.age++
    }

    // Slowly drift toward target
    dot.x += (dot.targetX - dot.x) * 0.02
    dot.y += (dot.targetY - dot.y) * 0.02

    // Pick new target occasionally
    if (Math.random() < 0.01) {
      dot.targetX = tileCenter.x + (Math.random() - 0.5) * 60
      dot.targetY = tileCenter.y + (Math.random() - 0.5) * 60
    }

    // Update pulse phase
    dot.pulsePhase += 0.05

    // Update entity properties
    dot.type = entity.type
    dot.subtype = entity.subtype
    dot.adorned = entity.adorned
    dot.entity = entity
  }

  // Remove dots for dead entities - spawn death ripples
  const livingIds = new Set(entities.map(e => e.id))
  for (const id of entityDots.keys()) {
    if (!livingIds.has(id)) {
      const deadDot = entityDots.get(id)!
      // Spawn a death ripple at the entity's last position
      const color = getEntityColor(deadDot)
      deathRipples.push({
        x: deadDot.x,
        y: deadDot.y,
        radius: 0,
        maxRadius: deadDot.type === 'visitor' ? 80 : 50,
        alpha: 0.8,
        color: color,
        startTime: Date.now()
      })
      entityDots.delete(id)
    }
  }

  // Update death ripples
  const now = Date.now()
  for (let i = deathRipples.length - 1; i >= 0; i--) {
    const ripple = deathRipples[i]
    const elapsed = now - ripple.startTime
    const duration = 1500 // 1.5 seconds
    const progress = elapsed / duration

    if (progress >= 1) {
      deathRipples.splice(i, 1)
    } else {
      ripple.radius = ripple.maxRadius * Math.sin(progress * Math.PI * 0.5)
      ripple.alpha = 0.8 * (1 - progress)
    }
  }
}

function getEntityColor(dot: EntityDot): string {
  if (dot.type === 'visitor') {
    return dot.subtype === 'hungry' ? '#f88' : '#8af'
  } else if (dot.adorned) {
    return '#ca8'
  }
  return '#a85'
}

export function drawEntityDots(ctx: CanvasRenderingContext2D): void {
  // Draw death ripples first (behind everything)
  for (const ripple of deathRipples) {
    ctx.save()

    // Outer ring
    ctx.beginPath()
    ctx.arc(ripple.x, ripple.y, ripple.radius, 0, Math.PI * 2)
    ctx.strokeStyle = ripple.color
    ctx.lineWidth = 2
    ctx.globalAlpha = ripple.alpha
    ctx.stroke()

    // Inner glow
    const gradient = ctx.createRadialGradient(
      ripple.x, ripple.y, 0,
      ripple.x, ripple.y, ripple.radius * 0.6
    )
    gradient.addColorStop(0, ripple.color)
    gradient.addColorStop(1, 'transparent')
    ctx.fillStyle = gradient
    ctx.globalAlpha = ripple.alpha * 0.3
    ctx.beginPath()
    ctx.arc(ripple.x, ripple.y, ripple.radius * 0.6, 0, Math.PI * 2)
    ctx.fill()

    // Secondary ring (echo effect)
    if (ripple.radius > 10) {
      ctx.beginPath()
      ctx.arc(ripple.x, ripple.y, ripple.radius * 0.5, 0, Math.PI * 2)
      ctx.strokeStyle = ripple.color
      ctx.lineWidth = 1
      ctx.globalAlpha = ripple.alpha * 0.5
      ctx.stroke()
    }

    ctx.restore()
  }

  // Draw constellation connections between nearby entities
  const dots = Array.from(entityDots.values())
  for (let i = 0; i < dots.length; i++) {
    for (let j = i + 1; j < dots.length; j++) {
      const a = dots[i]
      const b = dots[j]
      const dx = b.x - a.x
      const dy = b.y - a.y
      const dist = Math.sqrt(dx * dx + dy * dy)

      if (dist < CONSTELLATION_DISTANCE) {
        // Closer = brighter connection
        const strength = 1 - (dist / CONSTELLATION_DISTANCE)
        const alpha = CONSTELLATION_ALPHA * strength * strength

        // Use blend of both entity colors
        const colorA = getEntityColor(a)
        const colorB = getEntityColor(b)

        ctx.save()
        ctx.beginPath()
        ctx.moveTo(a.x, a.y)
        ctx.lineTo(b.x, b.y)

        // Gradient line between the two
        const gradient = ctx.createLinearGradient(a.x, a.y, b.x, b.y)
        gradient.addColorStop(0, colorA)
        gradient.addColorStop(1, colorB)
        ctx.strokeStyle = gradient
        ctx.lineWidth = 1 + strength
        ctx.globalAlpha = alpha
        ctx.stroke()

        // Midpoint glow for strong connections
        if (strength > 0.6) {
          const midX = (a.x + b.x) / 2
          const midY = (a.y + b.y) / 2
          ctx.beginPath()
          ctx.arc(midX, midY, 2 * strength, 0, Math.PI * 2)
          ctx.fillStyle = '#fff'
          ctx.globalAlpha = alpha * 0.5
          ctx.fill()
        }

        ctx.restore()
      }
    }
  }

  // Draw trails first (behind entities)
  for (const [_id, dot] of entityDots) {
    if (dot.trail.length < 2) continue

    const color = getEntityColor(dot)

    ctx.save()
    ctx.beginPath()
    ctx.moveTo(dot.trail[0].x, dot.trail[0].y)

    for (let i = 1; i < dot.trail.length; i++) {
      ctx.lineTo(dot.trail[i].x, dot.trail[i].y)
    }
    ctx.lineTo(dot.x, dot.y)

    ctx.strokeStyle = color
    ctx.lineWidth = dot.type === 'visitor' ? 2 : 1.5
    ctx.globalAlpha = 0.3
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.stroke()
    ctx.restore()

    // Draw fading trail dots
    for (let i = 0; i < dot.trail.length; i++) {
      const point = dot.trail[i]
      const progress = i / dot.trail.length
      const alpha = progress * 0.4

      ctx.save()
      ctx.beginPath()
      ctx.arc(point.x, point.y, 1 + progress, 0, Math.PI * 2)
      ctx.fillStyle = color
      ctx.globalAlpha = alpha
      ctx.fill()
      ctx.restore()
    }
  }

  // Draw entity dots
  for (const [_id, dot] of entityDots) {
    const baseSize = dot.adorned ? 5 : 4
    const pulse = Math.sin(dot.pulsePhase) * 0.3
    const size = baseSize + (dot.type === 'visitor' ? pulse : 0)

    ctx.save()
    ctx.beginPath()

    const color = getEntityColor(dot)

    if (dot.type === 'visitor') {
      // Visitors have pulsing glow
      ctx.arc(dot.x, dot.y, size, 0, Math.PI * 2)
      ctx.fillStyle = color
      ctx.shadowColor = color
      ctx.shadowBlur = 8 + pulse * 4
    } else if (dot.adorned) {
      // Adorned ants have golden glow
      ctx.arc(dot.x, dot.y, size, 0, Math.PI * 2)
      ctx.fillStyle = color
      ctx.shadowColor = color
      ctx.shadowBlur = 6
    } else {
      // Regular ants - subtle glow based on health
      const hunger = dot.entity.hunger ?? 100
      const healthGlow = hunger > 70 ? 3 : hunger > 30 ? 1 : 0

      ctx.arc(dot.x, dot.y, size - 1, 0, Math.PI * 2)
      ctx.fillStyle = color

      if (healthGlow > 0) {
        ctx.shadowColor = '#8a6'
        ctx.shadowBlur = healthGlow
      }
    }

    ctx.fill()
    ctx.restore()

    // Draw hunger indicator for low hunger
    const hunger = dot.entity.hunger ?? 100
    if (hunger < 30 && dot.type !== 'visitor') {
      ctx.save()
      ctx.beginPath()
      ctx.arc(dot.x, dot.y - 8, 2, 0, Math.PI * 2)
      ctx.fillStyle = hunger < 15 ? '#f44' : '#fa4'
      ctx.globalAlpha = 0.6 + Math.sin(dot.pulsePhase * 2) * 0.4
      ctx.fill()
      ctx.restore()
    }
  }
}
