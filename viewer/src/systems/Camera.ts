/**
 * Camera - controls the view into the world.
 *
 * Handles panning, zooming, and keeping the colony in view.
 * Uses smooth interpolation for all movements.
 */

import type { Vec2 } from '../types'
import { lerp, lerpVec2, clamp } from '../utils'
import { World } from '../world'

export class Camera {
  // Current camera state
  position: Vec2 = { x: 0, y: 0 }  // center of view
  zoom: number = 1.0

  // Target state (for smooth interpolation)
  private targetPosition: Vec2 = { x: 0, y: 0 }
  private targetZoom: number = 1.0

  // Constraints
  private minZoom = 0.3
  private maxZoom = 2.0

  // Viewport size (set by renderer)
  viewportWidth: number = 800
  viewportHeight: number = 600

  /**
   * Set the viewport size.
   */
  setViewport(width: number, height: number): void {
    this.viewportWidth = width
    this.viewportHeight = height
  }

  /**
   * Focus on a world position.
   */
  focusOn(worldPos: Vec2): void {
    this.targetPosition = { ...worldPos }
  }

  /**
   * Focus on the world center with appropriate zoom.
   */
  focusOnWorld(world: World): void {
    const center = world.getCenter()
    const size = world.getSize()

    // Calculate zoom to fit world in viewport with padding
    const padding = 100
    const zoomX = (this.viewportWidth - padding * 2) / Math.max(size.x, 100)
    const zoomY = (this.viewportHeight - padding * 2) / Math.max(size.y, 100)
    const fitZoom = Math.min(zoomX, zoomY)

    this.targetPosition = center
    this.targetZoom = clamp(fitZoom, this.minZoom, this.maxZoom)
  }

  /**
   * Pan the camera by a delta (in screen coordinates).
   */
  pan(dx: number, dy: number): void {
    this.targetPosition.x -= dx / this.zoom
    this.targetPosition.y -= dy / this.zoom
  }

  /**
   * Zoom toward a screen point.
   */
  zoomAt(screenX: number, screenY: number, delta: number): void {
    const oldZoom = this.targetZoom
    this.targetZoom = clamp(this.targetZoom * (1 + delta), this.minZoom, this.maxZoom)

    // Adjust position to zoom toward the mouse point
    const zoomRatio = this.targetZoom / oldZoom
    const worldX = this.screenToWorld({ x: screenX, y: screenY }).x
    const worldY = this.screenToWorld({ x: screenX, y: screenY }).y

    this.targetPosition.x = worldX - (worldX - this.targetPosition.x) * zoomRatio
    this.targetPosition.y = worldY - (worldY - this.targetPosition.y) * zoomRatio
  }

  /**
   * Update camera interpolation.
   */
  update(dt: number): void {
    const smoothing = 1 - Math.pow(0.001, dt)
    this.position = lerpVec2(this.position, this.targetPosition, smoothing)
    this.zoom = lerp(this.zoom, this.targetZoom, smoothing)
  }

  /**
   * Apply camera transform to canvas context.
   */
  applyTransform(ctx: CanvasRenderingContext2D): void {
    ctx.translate(this.viewportWidth / 2, this.viewportHeight / 2)
    ctx.scale(this.zoom, this.zoom)
    ctx.translate(-this.position.x, -this.position.y)
  }

  /**
   * Convert screen coordinates to world coordinates.
   */
  screenToWorld(screen: Vec2): Vec2 {
    return {
      x: (screen.x - this.viewportWidth / 2) / this.zoom + this.position.x,
      y: (screen.y - this.viewportHeight / 2) / this.zoom + this.position.y,
    }
  }

  /**
   * Convert world coordinates to screen coordinates.
   */
  worldToScreen(world: Vec2): Vec2 {
    return {
      x: (world.x - this.position.x) * this.zoom + this.viewportWidth / 2,
      y: (world.y - this.position.y) * this.zoom + this.viewportHeight / 2,
    }
  }
}
