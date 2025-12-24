/**
 * Utility functions for geometry, interpolation, and common operations.
 */

import type { Vec2 } from './types'

// Vector operations
export function vec2(x: number, y: number): Vec2 {
  return { x, y }
}

export function add(a: Vec2, b: Vec2): Vec2 {
  return { x: a.x + b.x, y: a.y + b.y }
}

export function sub(a: Vec2, b: Vec2): Vec2 {
  return { x: a.x - b.x, y: a.y - b.y }
}

export function scale(v: Vec2, s: number): Vec2 {
  return { x: v.x * s, y: v.y * s }
}

export function length(v: Vec2): number {
  return Math.sqrt(v.x * v.x + v.y * v.y)
}

export function distance(a: Vec2, b: Vec2): number {
  return length(sub(a, b))
}

export function normalize(v: Vec2): Vec2 {
  const len = length(v)
  if (len === 0) return { x: 0, y: 0 }
  return { x: v.x / len, y: v.y / len }
}

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t
}

export function lerpVec2(a: Vec2, b: Vec2, t: number): Vec2 {
  return {
    x: lerp(a.x, b.x, t),
    y: lerp(a.y, b.y, t),
  }
}

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

// Color utilities
export function lerpColor(colorA: string, colorB: string, t: number): string {
  // Parse hex colors
  const parseHex = (hex: string) => {
    const h = hex.replace('#', '')
    return {
      r: parseInt(h.slice(0, 2), 16),
      g: parseInt(h.slice(2, 4), 16),
      b: parseInt(h.slice(4, 6), 16),
    }
  }

  const a = parseHex(colorA)
  const b = parseHex(colorB)

  const r = Math.round(lerp(a.r, b.r, t))
  const g = Math.round(lerp(a.g, b.g, t))
  const bl = Math.round(lerp(a.b, b.b, t))

  return `rgb(${r}, ${g}, ${bl})`
}

export function withAlpha(color: string, alpha: number): string {
  // Handle hex colors
  if (color.startsWith('#')) {
    const r = parseInt(color.slice(1, 3), 16)
    const g = parseInt(color.slice(3, 5), 16)
    const b = parseInt(color.slice(5, 7), 16)
    return `rgba(${r}, ${g}, ${b}, ${alpha})`
  }
  // Handle rgb colors
  if (color.startsWith('rgb(')) {
    return color.replace('rgb(', 'rgba(').replace(')', `, ${alpha})`)
  }
  // Handle rgba colors
  if (color.startsWith('rgba(')) {
    return color.replace(/,\s*[\d.]+\)$/, `, ${alpha})`)
  }
  return color
}

// Easing functions
export function easeOutQuad(t: number): number {
  return t * (2 - t)
}

export function easeInOutQuad(t: number): number {
  return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t
}

export function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3)
}

// Random utilities
export function randomInRange(min: number, max: number): number {
  return min + Math.random() * (max - min)
}

export function randomVec2InRadius(center: Vec2, radius: number): Vec2 {
  const angle = Math.random() * Math.PI * 2
  const r = Math.sqrt(Math.random()) * radius
  return {
    x: center.x + Math.cos(angle) * r,
    y: center.y + Math.sin(angle) * r,
  }
}

// Time utilities
export function formatTick(tick: number): string {
  const hours = Math.floor(tick / 3600)
  const minutes = Math.floor((tick % 3600) / 60)
  const seconds = tick % 60
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`
  }
  return `${seconds}s`
}
