import type { GameState, Tile } from '../types/state.ts'
import { getTileCenter } from './tiles.ts'

interface Particle {
  x: number
  y: number
  targetX: number
  targetY: number
  progress: number
  speed: number
  color: string
  size: number
}

const particles: Particle[] = []

function spawnParticle(
  from: { x: number; y: number },
  to: { x: number; y: number },
  color: string
): void {
  particles.push({
    x: from.x,
    y: from.y,
    targetX: to.x,
    targetY: to.y,
    progress: 0,
    speed: 0.01 + Math.random() * 0.01,
    color,
    size: 2 + Math.random() * 2
  })
}

export function updateParticles(): void {
  // Update existing particles
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i]
    p.progress += p.speed
    p.x += (p.targetX - p.x) * p.speed * 2
    p.y += (p.targetY - p.y) * p.speed * 2

    // Remove completed particles
    if (p.progress >= 1) {
      particles.splice(i, 1)
    }
  }
}

export function spawnResourceParticles(state: GameState): void {
  const tiles = state.map?.tiles
  if (!tiles) return

  // Dig site -> origin (dirt)
  if (Math.random() < 0.1) {
    const from = getTileCenter('dig_site', tiles)
    const to = getTileCenter('origin', tiles)
    if (from && to) spawnParticle(from, to, '#8b7355')
  }

  // Compost -> origin (nutrients)
  if (Math.random() < 0.05) {
    const from = getTileCenter('compost', tiles)
    const to = getTileCenter('origin', tiles)
    if (from && to) spawnParticle(from, to, '#5a8a5a')
  }

  // Origin -> fungus farm (nutrients)
  if (Math.random() < 0.05) {
    const from = getTileCenter('origin', tiles)
    const to = getTileCenter('fungus_farm', tiles)
    if (from && to) spawnParticle(from, to, '#5a8a5a')
  }

  // Fungus farm -> origin (fungus)
  if (Math.random() < 0.03) {
    const from = getTileCenter('fungus_farm', tiles)
    const to = getTileCenter('origin', tiles)
    if (from && to) spawnParticle(from, to, '#7a6a9a')
  }

  // Crystal cave -> resonance (crystals)
  if (Math.random() < 0.02) {
    const from = getTileCenter('crystal_cave', tiles)
    const to = getTileCenter('resonance_chamber', tiles)
    if (from && to) spawnParticle(from, to, '#aaccff')
  }

  // Resonance -> origin (nutrients from crystals)
  if (Math.random() < 0.08) {
    const from = getTileCenter('resonance_chamber', tiles)
    const to = getTileCenter('origin', tiles)
    if (from && to) spawnParticle(from, to, '#88aacc')
  }

  // Origin -> receiver (influence)
  if ((state.resources?.influence ?? 0) > 0 && Math.random() < 0.05) {
    const from = getTileCenter('origin', tiles)
    const to = getTileCenter('receiver', tiles)
    if (from && to) spawnParticle(from, to, '#aa88ff')
  }

  // Observer generating insight
  const hasObserver = state.entities?.some(e => e.subtype === 'observer')
  if (hasObserver && Math.random() < 0.1) {
    const from = getTileCenter('receiver', tiles)
    if (from) {
      spawnParticle(
        { x: from.x + (Math.random() - 0.5) * 30, y: from.y + (Math.random() - 0.5) * 30 },
        { x: from.x, y: from.y - 40 },
        '#88ffaa'
      )
    }
  }
}

export function drawParticles(ctx: CanvasRenderingContext2D): void {
  for (const p of particles) {
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.size * (1 - p.progress * 0.5), 0, Math.PI * 2)
    ctx.fillStyle = p.color
    ctx.globalAlpha = 1 - p.progress
    ctx.fill()
  }
  ctx.globalAlpha = 1
}
