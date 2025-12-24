/**
 * Renderer - orchestrates all drawing to the canvas.
 *
 * Layers: atmosphere → tiles → corpses → effects → ants → UI overlay
 */

import { World } from '../world'
import { Camera } from './Camera'
import { Atmosphere } from './Atmosphere'
import { Observer } from './Observer'
import { COLORS, LAYOUT } from '../types'
import { distance, withAlpha } from '../utils'

export class Renderer {
  private canvas: HTMLCanvasElement
  private ctx: CanvasRenderingContext2D
  private world: World
  private camera: Camera
  private atmosphere: Atmosphere
  private observer: Observer

  private width: number = 0
  private height: number = 0

  constructor(canvas: HTMLCanvasElement, world: World) {
    this.canvas = canvas
    this.ctx = canvas.getContext('2d')!
    this.world = world
    this.camera = new Camera()
    this.atmosphere = new Atmosphere()
    this.observer = new Observer()

    this.setupCanvas()
    this.setupEventListeners()
  }

  private setupCanvas(): void {
    const resize = () => {
      const dpr = window.devicePixelRatio || 1
      const rect = this.canvas.getBoundingClientRect()

      this.width = rect.width
      this.height = rect.height

      this.canvas.width = rect.width * dpr
      this.canvas.height = rect.height * dpr

      this.ctx.scale(dpr, dpr)
      this.camera.setViewport(this.width, this.height)
    }

    resize()
    window.addEventListener('resize', resize)
  }

  private setupEventListeners(): void {
    // Pan with mouse drag
    let isDragging = false
    let lastX = 0, lastY = 0

    this.canvas.addEventListener('mousedown', (e) => {
      if (e.button === 0) {
        isDragging = true
        lastX = e.clientX
        lastY = e.clientY
      }
    })

    window.addEventListener('mousemove', (e) => {
      if (isDragging) {
        const dx = e.clientX - lastX
        const dy = e.clientY - lastY
        this.camera.pan(dx, dy)
        lastX = e.clientX
        lastY = e.clientY
      }
    })

    window.addEventListener('mouseup', () => {
      isDragging = false
    })

    // Zoom with wheel
    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault()
      const delta = -e.deltaY * 0.001
      const rect = this.canvas.getBoundingClientRect()
      this.camera.zoomAt(e.clientX - rect.left, e.clientY - rect.top, delta)
    })

    // Click to bless
    this.canvas.addEventListener('click', (e) => {
      if (isDragging) return  // Don't bless on drag end

      const rect = this.canvas.getBoundingClientRect()
      const screenPos = { x: e.clientX - rect.left, y: e.clientY - rect.top }
      const worldPos = this.camera.screenToWorld(screenPos)

      this.observer.click(worldPos, this.world)
    })

    // Track mouse for observer presence
    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect()
      const screenPos = { x: e.clientX - rect.left, y: e.clientY - rect.top }
      this.observer.moveCursor(this.camera.screenToWorld(screenPos))
    })
  }

  /**
   * Initialize camera to fit the world.
   */
  focusOnWorld(): void {
    this.camera.focusOnWorld(this.world)
  }

  /**
   * Main update loop.
   */
  update(dt: number): void {
    this.camera.update(dt)
    this.atmosphere.compute(this.world)
    this.atmosphere.update(dt, { width: this.width, height: this.height })
    this.observer.update(dt)
  }

  /**
   * Main render loop.
   */
  render(): void {
    const ctx = this.ctx

    // Clear and draw atmosphere (screen space)
    ctx.save()
    this.atmosphere.render(ctx, this.width, this.height)
    ctx.restore()

    // World space rendering
    ctx.save()
    this.camera.applyTransform(ctx)

    this.renderTiles(ctx)
    this.renderCorpses(ctx)
    this.renderDeathRipples(ctx)
    this.renderConstellations(ctx)
    this.renderAnts(ctx)
    this.renderObserver(ctx)

    ctx.restore()

    // Screen space UI overlay
    this.renderUI(ctx)
  }

  private renderTiles(ctx: CanvasRenderingContext2D): void {
    for (const tile of this.world.tiles.values()) {
      tile.render(ctx, this.world.tick)
    }
  }

  private renderCorpses(ctx: CanvasRenderingContext2D): void {
    for (const corpse of this.world.corpses.values()) {
      corpse.render(ctx)
    }
  }

  private renderAnts(ctx: CanvasRenderingContext2D): void {
    for (const ant of this.world.ants.values()) {
      ant.render(ctx)
    }
  }

  private renderConstellations(ctx: CanvasRenderingContext2D): void {
    const ants = this.world.getAnts()
    if (ants.length < 2) return

    ctx.strokeStyle = COLORS.constellation
    ctx.lineWidth = 1

    for (let i = 0; i < ants.length; i++) {
      for (let j = i + 1; j < ants.length; j++) {
        const a = ants[i]
        const b = ants[j]
        const d = distance(a.visualPosition, b.visualPosition)

        if (d < LAYOUT.constellationDistance) {
          const alpha = 1 - d / LAYOUT.constellationDistance
          ctx.globalAlpha = alpha * 0.15

          ctx.beginPath()
          ctx.moveTo(a.visualPosition.x, a.visualPosition.y)
          ctx.lineTo(b.visualPosition.x, b.visualPosition.y)
          ctx.stroke()
        }
      }
    }

    ctx.globalAlpha = 1
  }

  private renderDeathRipples(ctx: CanvasRenderingContext2D): void {
    const now = performance.now()

    for (const death of this.world.recentDeaths) {
      const age = (now - death.time) / 1000  // seconds
      const maxAge = 3

      if (age >= maxAge) continue

      const progress = age / maxAge
      const radius = 20 + progress * 80
      const alpha = (1 - progress) * 0.4

      ctx.beginPath()
      ctx.arc(death.position.x, death.position.y, radius, 0, Math.PI * 2)
      ctx.strokeStyle = withAlpha(COLORS.deathRipple, alpha)
      ctx.lineWidth = 2 - progress
      ctx.stroke()

      // Inner ripple
      if (progress < 0.5) {
        const innerRadius = radius * 0.5
        const innerAlpha = alpha * 0.5
        ctx.beginPath()
        ctx.arc(death.position.x, death.position.y, innerRadius, 0, Math.PI * 2)
        ctx.strokeStyle = withAlpha(COLORS.deathRipple, innerAlpha)
        ctx.stroke()
      }
    }
  }

  private renderObserver(ctx: CanvasRenderingContext2D): void {
    this.observer.render(ctx)
  }

  private renderUI(ctx: CanvasRenderingContext2D): void {
    // Minimal info overlay in top-left
    const padding = 15
    const lineHeight = 18

    ctx.font = '13px monospace'
    ctx.fillStyle = COLORS.text

    const lines = [
      `tick ${this.world.tick}`,
      `${this.world.ants.size} ants`,
      `sanity ${this.world.sanity.toFixed(1)}`,
    ]

    // Add resource counts
    const resources = ['fungus', 'ore', 'influence'] as const
    for (const r of resources) {
      const val = this.world.resources.get(r) || 0
      if (val > 0 || r === 'influence') {
        lines.push(`${r}: ${val.toFixed(r === 'influence' ? 3 : 1)}`)
      }
    }

    // Background panel
    const maxWidth = Math.max(...lines.map(l => ctx.measureText(l).width))
    ctx.fillStyle = COLORS.panelBg
    ctx.fillRect(padding - 5, padding - 5, maxWidth + 20, lines.length * lineHeight + 10)
    ctx.strokeStyle = COLORS.panelBorder
    ctx.lineWidth = 1
    ctx.strokeRect(padding - 5, padding - 5, maxWidth + 20, lines.length * lineHeight + 10)

    // Text
    ctx.fillStyle = COLORS.text
    lines.forEach((line, i) => {
      ctx.fillText(line, padding, padding + 12 + i * lineHeight)
    })

    // Atmosphere mood indicator
    const mood = this.atmosphere.getState().mood
    if (mood !== 'calm') {
      ctx.fillStyle = mood === 'crisis' ? '#ff4444' : mood === 'anxious' ? '#ffaa44' : '#44ff88'
      ctx.fillText(`[${mood}]`, padding + maxWidth + 30, padding + 12)
    }

    // Observer stats in bottom-left
    this.observer.renderStats(ctx, this.height)
  }

  getCamera(): Camera {
    return this.camera
  }

  getObserver(): Observer {
    return this.observer
  }
}
