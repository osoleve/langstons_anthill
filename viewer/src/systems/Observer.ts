/**
 * Observer - the human presence watching the colony.
 *
 * Not a god—a presence that affects and is affected.
 * Clicking grants blessings. Attention is visible. Stats persist.
 */

import type { Vec2 } from '../types'
import { COLORS, LAYOUT } from '../types'
import { distance, withAlpha, easeOutCubic } from '../utils'
import { World } from '../world'
import type { Ant } from '../world/Ant'

interface Blessing {
  position: Vec2
  time: number
  type: 'gift' | 'attention' | 'touch'
  radius: number
}

interface ObserverStats {
  totalBlessings: number
  totalMiracles: number
  blessingsThisSession: number
  clicksThisSecond: number
  lastClickTime: number
}

export class Observer {
  // Cursor state
  cursorPosition: Vec2 = { x: 0, y: 0 }
  private cursorGlowPhase: number = 0

  // Blessings (visual effects)
  private blessings: Blessing[] = []
  private pendingBlessings: { type: string; position: Vec2 }[] = []

  // Click tracking for miracles
  private recentClicks: number[] = []
  private miracleThreshold = 5  // clicks per second for miracle

  // Persistent stats
  private stats: ObserverStats

  // Server communication
  private lastSendTime: number = 0
  private sendCooldown: number = 100  // ms between server calls

  constructor() {
    // Load stats from localStorage
    const saved = localStorage.getItem('observer_stats')
    if (saved) {
      this.stats = JSON.parse(saved)
      this.stats.blessingsThisSession = 0
      this.stats.clicksThisSecond = 0
    } else {
      this.stats = {
        totalBlessings: 0,
        totalMiracles: 0,
        blessingsThisSession: 0,
        clicksThisSecond: 0,
        lastClickTime: 0,
      }
    }
  }

  /**
   * Move cursor (in world coordinates).
   */
  moveCursor(position: Vec2): void {
    this.cursorPosition = position
  }

  /**
   * Handle click at world position.
   */
  click(position: Vec2, world: World): void {
    const now = performance.now()

    // Track recent clicks for miracle detection
    this.recentClicks.push(now)
    this.recentClicks = this.recentClicks.filter(t => now - t < 1000)

    // Determine blessing type based on what's nearby
    const type = this.determineBlessingType(position, world)

    // Create visual effect
    this.blessings.push({
      position: { ...position },
      time: now,
      type,
      radius: 0,
    })

    // Update stats
    this.stats.blessingsThisSession++
    this.stats.totalBlessings++
    this.stats.clicksThisSecond = this.recentClicks.length

    // Check for miracle (rapid clicking)
    if (this.recentClicks.length >= this.miracleThreshold) {
      this.triggerMiracle(position)
      this.recentClicks = []  // Reset after miracle
    }

    // Queue for server
    this.pendingBlessings.push({ type, position })

    // Save stats
    this.saveStats()

    // Send to server (with cooldown)
    this.maybeSendBlessings()
  }

  private determineBlessingType(position: Vec2, world: World): 'gift' | 'attention' | 'touch' {
    // Check if near an entity
    for (const ant of world.ants.values()) {
      if (distance(position, ant.visualPosition) < 30) {
        return 'attention'
      }
    }

    // Check if near a system tile
    for (const tile of world.tiles.values()) {
      const tileCenter = {
        x: tile.position.x * LAYOUT.tileSize + LAYOUT.tileSize / 2,
        y: tile.position.y * LAYOUT.tileSize + LAYOUT.tileSize / 2,
      }
      if (tile.system && distance(position, tileCenter) < LAYOUT.tileSize) {
        return 'gift'
      }
    }

    // Default: touch on empty space
    return 'touch'
  }

  private triggerMiracle(position: Vec2): void {
    this.stats.totalMiracles++
    this.saveStats()

    // Send miracle to server
    fetch('/bless', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'miracle',
        x: position.x,
        y: position.y,
      }),
    }).catch(() => {})  // Ignore errors
  }

  private async maybeSendBlessings(): Promise<void> {
    const now = performance.now()
    if (now - this.lastSendTime < this.sendCooldown) return
    if (this.pendingBlessings.length === 0) return

    this.lastSendTime = now
    const toSend = this.pendingBlessings.splice(0, 10)  // Send up to 10 at once

    try {
      await fetch('/bless', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'blessing',
          blessings: toSend.map(b => ({
            type: b.type,
            x: b.position.x,
            y: b.position.y,
          })),
        }),
      })
    } catch {
      // Ignore errors - blessings are visual first, server second
    }
  }

  private saveStats(): void {
    localStorage.setItem('observer_stats', JSON.stringify(this.stats))
  }

  /**
   * Update observer state.
   */
  update(dt: number): void {
    this.cursorGlowPhase += dt * 2

    // Update click rate
    const now = performance.now()
    this.recentClicks = this.recentClicks.filter(t => now - t < 1000)
    this.stats.clicksThisSecond = this.recentClicks.length

    // Remove old blessings
    this.blessings = this.blessings.filter(b => now - b.time < 1500)
  }

  /**
   * Render observer effects (in world space).
   */
  render(ctx: CanvasRenderingContext2D): void {
    this.renderCursorPresence(ctx)
    this.renderBlessings(ctx)
  }

  private renderCursorPresence(ctx: CanvasRenderingContext2D): void {
    const { x, y } = this.cursorPosition
    const pulse = Math.sin(this.cursorGlowPhase) * 0.3 + 0.7

    // Soft glow at cursor
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, 30)
    gradient.addColorStop(0, withAlpha('#ffffff', 0.05 * pulse))
    gradient.addColorStop(1, 'transparent')

    ctx.beginPath()
    ctx.arc(x, y, 30, 0, Math.PI * 2)
    ctx.fillStyle = gradient
    ctx.fill()
  }

  private renderBlessings(ctx: CanvasRenderingContext2D): void {
    const now = performance.now()

    for (const blessing of this.blessings) {
      const age = (now - blessing.time) / 1000
      const maxAge = 1.5
      const progress = age / maxAge

      if (progress >= 1) continue

      const eased = easeOutCubic(progress)
      const radius = 10 + eased * 60
      const alpha = (1 - progress) * 0.6

      // Color by type
      let color: string
      switch (blessing.type) {
        case 'gift': color = '#88ff88'; break
        case 'attention': color = '#ffff88'; break
        default: color = COLORS.blessing
      }

      // Expanding ring
      ctx.beginPath()
      ctx.arc(blessing.position.x, blessing.position.y, radius, 0, Math.PI * 2)
      ctx.strokeStyle = withAlpha(color, alpha)
      ctx.lineWidth = 2 - progress
      ctx.stroke()

      // Inner particles
      if (progress < 0.5) {
        const particleCount = 5
        for (let i = 0; i < particleCount; i++) {
          const angle = (i / particleCount) * Math.PI * 2 + age * 3
          const r = radius * 0.6
          const px = blessing.position.x + Math.cos(angle) * r
          const py = blessing.position.y + Math.sin(angle) * r

          ctx.beginPath()
          ctx.arc(px, py, 2 - progress * 2, 0, Math.PI * 2)
          ctx.fillStyle = withAlpha(color, alpha * 0.8)
          ctx.fill()
        }
      }
    }
  }

  /**
   * Render observer stats panel (in screen space).
   */
  renderStats(ctx: CanvasRenderingContext2D, canvasHeight: number): void {
    const padding = 15
    const lineHeight = 16

    const lines = [
      `observer`,
      `blessings: ${this.stats.blessingsThisSession}`,
      `miracles: ${this.stats.totalMiracles}`,
    ]

    // Combo indicator
    if (this.stats.clicksThisSecond >= 3) {
      lines.push(`combo: ${this.stats.clicksThisSecond}x`)
    }

    ctx.font = '12px monospace'
    const maxWidth = Math.max(...lines.map(l => ctx.measureText(l).width))

    const y = canvasHeight - padding - lines.length * lineHeight - 5

    // Background
    ctx.fillStyle = COLORS.panelBg
    ctx.fillRect(padding - 5, y - 5, maxWidth + 20, lines.length * lineHeight + 10)
    ctx.strokeStyle = COLORS.panelBorder
    ctx.lineWidth = 1
    ctx.strokeRect(padding - 5, y - 5, maxWidth + 20, lines.length * lineHeight + 10)

    // Text
    ctx.fillStyle = COLORS.textDim
    lines.forEach((line, i) => {
      if (i === 0) ctx.fillStyle = COLORS.text
      ctx.fillText(line, padding, y + 10 + i * lineHeight)
      ctx.fillStyle = COLORS.textDim
    })

    // Combo highlight
    if (this.stats.clicksThisSecond >= 3) {
      const comboColor = this.stats.clicksThisSecond >= 5 ? '#ffcc00' : '#aaaaaa'
      ctx.fillStyle = comboColor
      ctx.fillText(lines[lines.length - 1], padding, y + 10 + (lines.length - 1) * lineHeight)
    }
  }
}
