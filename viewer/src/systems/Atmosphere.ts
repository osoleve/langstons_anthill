/**
 * Atmosphere - the mood of the colony made visible.
 *
 * Sanity, mortality, and prosperity affect the visual feel:
 * colors shift, particles drift, the world breathes.
 */

import type { Vec2 } from '../types'
import { COLORS } from '../types'
import { lerpColor, withAlpha, randomInRange, clamp } from '../utils'
import { World } from '../world'

interface AtmosphereParticle {
  x: number
  y: number
  vx: number
  vy: number
  alpha: number
  size: number
  life: number
  maxLife: number
}

export interface AtmosphereState {
  backgroundColor: string
  particleDensity: number
  lightLevel: number
  pulseRate: number
  mood: 'calm' | 'anxious' | 'crisis' | 'hopeful'
}

export class Atmosphere {
  private particles: AtmosphereParticle[] = []
  private state: AtmosphereState
  private pulsePhase: number = 0

  constructor() {
    this.state = {
      backgroundColor: COLORS.background,
      particleDensity: 0.3,
      lightLevel: 1.0,
      pulseRate: 1.0,
      mood: 'calm',
    }
  }

  /**
   * Compute atmosphere from world state.
   */
  compute(world: World): AtmosphereState {
    const sanity = world.sanity / 100
    const mortality = world.recentDeaths.length / Math.max(1, world.ants.size)
    const fungus = world.resources.get('fungus') || 0
    const prosperity = clamp(fungus / 100, 0, 1)

    // Determine mood
    let mood: AtmosphereState['mood']
    if (sanity < 0.2) {
      mood = 'crisis'
    } else if (sanity < 0.4 || mortality > 0.3) {
      mood = 'anxious'
    } else if (prosperity > 0.5 && sanity > 0.7) {
      mood = 'hopeful'
    } else {
      mood = 'calm'
    }

    // Compute visual properties
    const backgroundColor = this.computeBackgroundColor(sanity, mood)
    const particleDensity = this.computeParticleDensity(mortality, mood)
    const lightLevel = this.computeLightLevel(prosperity, sanity)
    const pulseRate = mood === 'crisis' ? 2.0 : mood === 'anxious' ? 1.5 : 1.0

    this.state = { backgroundColor, particleDensity, lightLevel, pulseRate, mood }
    return this.state
  }

  private computeBackgroundColor(sanity: number, mood: string): string {
    switch (mood) {
      case 'crisis':
        return lerpColor(COLORS.backgroundCrisis, COLORS.background, sanity)
      case 'hopeful':
        return COLORS.backgroundCalm
      case 'anxious':
        return lerpColor(COLORS.background, COLORS.backgroundCrisis, 0.3)
      default:
        return COLORS.background
    }
  }

  private computeParticleDensity(mortality: number, mood: string): number {
    // More deaths = more ambient particles (dust, spirits)
    let base = 0.3
    if (mood === 'crisis') base = 0.8
    else if (mood === 'anxious') base = 0.5
    return base + mortality * 0.3
  }

  private computeLightLevel(prosperity: number, sanity: number): number {
    // Prosperity and sanity brighten the world
    return 0.6 + prosperity * 0.2 + sanity * 0.2
  }

  /**
   * Update atmosphere particles.
   */
  update(dt: number, bounds: { width: number; height: number }): void {
    this.pulsePhase += dt * this.state.pulseRate

    // Spawn new particles based on density
    const targetCount = Math.floor(this.state.particleDensity * 30)
    while (this.particles.length < targetCount) {
      this.particles.push(this.createParticle(bounds))
    }

    // Update existing particles
    for (const p of this.particles) {
      p.x += p.vx * dt
      p.y += p.vy * dt
      p.life -= dt
      p.alpha = (p.life / p.maxLife) * 0.3
    }

    // Remove dead particles
    this.particles = this.particles.filter(p => p.life > 0)
  }

  private createParticle(bounds: { width: number; height: number }): AtmosphereParticle {
    const isRising = this.state.mood === 'crisis' || this.state.mood === 'anxious'

    return {
      x: randomInRange(0, bounds.width),
      y: isRising ? bounds.height + 10 : randomInRange(0, bounds.height),
      vx: randomInRange(-5, 5),
      vy: isRising ? randomInRange(-30, -10) : randomInRange(-5, 5),
      alpha: 0.3,
      size: randomInRange(1, 3),
      life: randomInRange(3, 8),
      maxLife: 8,
    }
  }

  /**
   * Render atmosphere effects.
   */
  render(ctx: CanvasRenderingContext2D, width: number, height: number): void {
    // Background gradient with pulse
    const pulse = Math.sin(this.pulsePhase) * 0.02
    const grad = ctx.createRadialGradient(
      width / 2, height / 2, 0,
      width / 2, height / 2, Math.max(width, height) * 0.7
    )
    grad.addColorStop(0, this.lighten(this.state.backgroundColor, 0.05 + pulse))
    grad.addColorStop(1, this.state.backgroundColor)

    ctx.fillStyle = grad
    ctx.fillRect(0, 0, width, height)

    // Particles
    for (const p of this.particles) {
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
      ctx.fillStyle = withAlpha('#ffffff', p.alpha * this.state.lightLevel)
      ctx.fill()
    }

    // Crisis vignette
    if (this.state.mood === 'crisis') {
      this.renderVignette(ctx, width, height, '#200000', 0.3)
    }
  }

  private renderVignette(ctx: CanvasRenderingContext2D, width: number, height: number, color: string, intensity: number): void {
    const grad = ctx.createRadialGradient(
      width / 2, height / 2, 0,
      width / 2, height / 2, Math.max(width, height) * 0.6
    )
    grad.addColorStop(0, 'transparent')
    grad.addColorStop(1, withAlpha(color, intensity))

    ctx.fillStyle = grad
    ctx.fillRect(0, 0, width, height)
  }

  private lighten(color: string, amount: number): string {
    let r: number, g: number, b: number

    // Parse hex or rgb color
    if (color.startsWith('#')) {
      r = parseInt(color.slice(1, 3), 16)
      g = parseInt(color.slice(3, 5), 16)
      b = parseInt(color.slice(5, 7), 16)
    } else if (color.startsWith('rgb')) {
      const match = color.match(/(\d+),\s*(\d+),\s*(\d+)/)
      if (match) {
        r = parseInt(match[1], 10)
        g = parseInt(match[2], 10)
        b = parseInt(match[3], 10)
      } else {
        return color  // Can't parse, return as-is
      }
    } else {
      return color
    }

    const nr = Math.min(255, Math.floor(r + (255 - r) * amount))
    const ng = Math.min(255, Math.floor(g + (255 - g) * amount))
    const nb = Math.min(255, Math.floor(b + (255 - b) * amount))

    return `#${nr.toString(16).padStart(2, '0')}${ng.toString(16).padStart(2, '0')}${nb.toString(16).padStart(2, '0')}`
  }

  getState(): AtmosphereState {
    return this.state
  }
}
