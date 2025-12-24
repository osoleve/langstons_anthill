/**
 * Atmospheric Effects
 *
 * Creates ambient visual atmosphere based on colony state:
 * - Floating particles (dust, spores, energy motes)
 * - Environmental color shifts based on sanity/boredom
 * - Weather-like effects during crises
 */

import type { GameState } from '../types/state.ts'

interface AtmosphereParticle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  alpha: number
  color: string
  type: 'dust' | 'spore' | 'energy' | 'dread' | 'hope'
  wobble: number
  wobbleSpeed: number
}

interface AtmosphereState {
  particles: AtmosphereParticle[]
  colorShift: { r: number; g: number; b: number }
  intensity: number
  mood: 'calm' | 'anxious' | 'crisis' | 'hopeful'
}

let atmosphere: AtmosphereState = {
  particles: [],
  colorShift: { r: 0, g: 0, b: 0 },
  intensity: 0.5,
  mood: 'calm'
}

const MAX_PARTICLES = 100

export function initAtmosphere(width: number, height: number): void {
  atmosphere.particles = []

  // Seed with initial particles
  for (let i = 0; i < 30; i++) {
    spawnParticle(width, height, 'dust')
  }
}

function spawnParticle(width: number, height: number, type: AtmosphereParticle['type']): void {
  if (atmosphere.particles.length >= MAX_PARTICLES) return

  const colors: Record<AtmosphereParticle['type'], string[]> = {
    dust: ['#8b7355', '#6b5335', '#9b8365'],
    spore: ['#7a6a9a', '#5a4a7a', '#9a8aba'],
    energy: ['#aaccff', '#88aadd', '#ccddff'],
    dread: ['#aa4444', '#cc6666', '#884444'],
    hope: ['#88ff88', '#aaffaa', '#66dd66']
  }

  const colorList = colors[type]
  const color = colorList[Math.floor(Math.random() * colorList.length)]

  atmosphere.particles.push({
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - 0.5) * 0.3,
    vy: -0.1 - Math.random() * 0.2,
    size: 1 + Math.random() * 2,
    alpha: 0.1 + Math.random() * 0.3,
    color,
    type,
    wobble: Math.random() * Math.PI * 2,
    wobbleSpeed: 0.02 + Math.random() * 0.03
  })
}

export function updateAtmosphere(state: GameState, width: number, height: number): void {
  // Determine mood from state
  const sanity = state.meta.sanity ?? 100
  const boredom = state.meta.boredom ?? 0

  if (sanity < 20) {
    atmosphere.mood = 'crisis'
    atmosphere.intensity = 1.0
  } else if (sanity < 50 || boredom > 40) {
    atmosphere.mood = 'anxious'
    atmosphere.intensity = 0.7
  } else if (state.entities.length > 10 && sanity > 80) {
    atmosphere.mood = 'hopeful'
    atmosphere.intensity = 0.6
  } else {
    atmosphere.mood = 'calm'
    atmosphere.intensity = 0.4
  }

  // Color shift based on mood
  switch (atmosphere.mood) {
    case 'crisis':
      atmosphere.colorShift = { r: 30, g: -10, b: -10 }
      break
    case 'anxious':
      atmosphere.colorShift = { r: 10, g: 5, b: -5 }
      break
    case 'hopeful':
      atmosphere.colorShift = { r: -5, g: 10, b: 5 }
      break
    default:
      atmosphere.colorShift = { r: 0, g: 0, b: 0 }
  }

  // Spawn particles based on mood
  const spawnChance = atmosphere.intensity * 0.1
  if (Math.random() < spawnChance) {
    let type: AtmosphereParticle['type'] = 'dust'

    if (atmosphere.mood === 'crisis') {
      type = Math.random() < 0.5 ? 'dread' : 'dust'
    } else if (atmosphere.mood === 'hopeful') {
      type = Math.random() < 0.3 ? 'hope' : 'spore'
    } else if (atmosphere.mood === 'anxious') {
      type = Math.random() < 0.4 ? 'energy' : 'dust'
    } else {
      type = Math.random() < 0.3 ? 'spore' : 'dust'
    }

    spawnParticle(width, height, type)
  }

  // Update particles
  atmosphere.particles = atmosphere.particles.filter(p => {
    // Wobble
    p.wobble += p.wobbleSpeed
    p.x += p.vx + Math.sin(p.wobble) * 0.2
    p.y += p.vy

    // Fade in crisis
    if (atmosphere.mood === 'crisis' && p.type === 'dread') {
      p.alpha = Math.min(0.6, p.alpha + 0.01)
    }

    // Remove if off screen
    if (p.y < -10 || p.x < -10 || p.x > width + 10) {
      return false
    }

    return true
  })
}

export function drawAtmosphere(ctx: CanvasRenderingContext2D): void {
  // Draw overlay for mood
  if (atmosphere.mood !== 'calm') {
    ctx.save()
    const { r, g, b } = atmosphere.colorShift
    const overlayAlpha = atmosphere.intensity * 0.1

    ctx.fillStyle = `rgba(${128 + r}, ${128 + g}, ${128 + b}, ${overlayAlpha})`
    ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height)
    ctx.restore()
  }

  // Draw particles
  atmosphere.particles.forEach(p => {
    ctx.save()
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
    ctx.fillStyle = p.color
    ctx.globalAlpha = p.alpha

    if (p.type === 'energy' || p.type === 'hope' || p.type === 'dread') {
      ctx.shadowColor = p.color
      ctx.shadowBlur = 5
    }

    ctx.fill()
    ctx.restore()
  })
}

export function getAtmosphereMood(): string {
  return atmosphere.mood
}

export function getAtmosphereIntensity(): number {
  return atmosphere.intensity
}
