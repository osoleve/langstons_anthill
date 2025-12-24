import type { GameState, Tile, System } from '../types/state.ts'
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
  resource: string
  stalled: boolean
}

// Resource color palette - extensible for new resource types
const RESOURCE_COLORS: Record<string, string> = {
  dirt: '#8b7355',
  nutrients: '#5a8a5a',
  fungus: '#7a6a9a',
  crystals: '#aaccff',
  ore: '#c9a959',
  influence: '#aa88ff',
  insight: '#88ffaa',
  strange_matter: '#ff88aa',
}

function getResourceColor(resource: string): string {
  return RESOURCE_COLORS[resource] ?? '#888888'
}

const particles: Particle[] = []

// Track which flows are stalled (no resources to consume)
const stalledFlows: Set<string> = new Set()

export function getStalledFlows(): Set<string> {
  return stalledFlows
}

function spawnParticle(
  from: { x: number; y: number },
  to: { x: number; y: number },
  resource: string,
  stalled: boolean = false
): void {
  particles.push({
    x: from.x,
    y: from.y,
    targetX: to.x,
    targetY: to.y,
    progress: 0,
    speed: 0.01 + Math.random() * 0.01,
    color: getResourceColor(resource),
    size: 2 + Math.random() * 2,
    resource,
    stalled
  })
}

export function updateParticles(): void {
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i]
    p.progress += p.speed
    p.x += (p.targetX - p.x) * p.speed * 2
    p.y += (p.targetY - p.y) * p.speed * 2

    if (p.progress >= 1) {
      particles.splice(i, 1)
    }
  }
}

// Find tile that hosts a given system
function findSystemTile(systemId: string, tiles: Record<string, Tile>): string | null {
  // Direct match: system ID matches tile ID
  if (tiles[systemId]) return systemId

  // Common patterns: system "foo_bar" might be on tile "foo_bar_tile"
  const withTileSuffix = `${systemId}_tile`
  if (tiles[withTileSuffix]) return withTileSuffix

  // Check for partial matches (e.g., "dig_site" system on "dig_site" tile)
  for (const tileId of Object.keys(tiles)) {
    if (tileId.includes(systemId) || systemId.includes(tileId)) {
      return tileId
    }
  }

  return null
}

// Find connected tile that could be a consumer/producer destination
function findConnectedTile(
  fromTileId: string,
  connections: [string, string][],
  tiles: Record<string, Tile>,
  preferOrigin: boolean = true
): string | null {
  // Find all connections involving this tile
  const connected: string[] = []
  for (const [a, b] of connections) {
    if (a === fromTileId) connected.push(b)
    if (b === fromTileId) connected.push(a)
  }

  // Prefer origin as central hub
  if (preferOrigin && connected.includes('origin')) return 'origin'

  return connected[0] ?? null
}

export function spawnResourceParticles(state: GameState): void {
  const tiles = state.map?.tiles
  const systems = state.systems
  const connections = state.map?.connections
  const resources = state.resources ?? {}

  if (!tiles || !systems || !connections) return

  stalledFlows.clear()

  // Iterate over all systems and spawn particles based on their generates/consumes
  for (const [systemId, system] of Object.entries(systems)) {
    const sourceTileId = findSystemTile(systemId, tiles)
    if (!sourceTileId) continue

    const sourcePos = getTileCenter(sourceTileId, tiles)
    if (!sourcePos) continue

    // Systems that GENERATE resources: particles flow FROM this tile
    if (system.generates) {
      for (const [resource, rate] of Object.entries(system.generates)) {
        if (rate <= 0) continue

        // Spawn probability proportional to generation rate
        // Base: 0.01/tick = 5% spawn chance, 0.1/tick = 50% spawn chance
        const spawnChance = Math.min(0.5, rate * 5)

        if (Math.random() < spawnChance) {
          // Find destination - prefer origin as central resource hub
          const destTileId = findConnectedTile(sourceTileId, connections, tiles, true)
          if (destTileId) {
            const destPos = getTileCenter(destTileId, tiles)
            if (destPos) {
              spawnParticle(sourcePos, destPos, resource)
            }
          } else {
            // No connection - particles rise up and dissipate (resource accumulating locally)
            spawnParticle(
              sourcePos,
              { x: sourcePos.x, y: sourcePos.y - 40 },
              resource
            )
          }
        }
      }
    }

    // Systems that CONSUME resources: particles flow TO this tile
    if (system.consumes) {
      for (const [resource, rate] of Object.entries(system.consumes)) {
        if (rate <= 0) continue

        const currentAmount = resources[resource] ?? 0
        const isStalled = currentAmount < rate * 10 // Low on this resource

        if (isStalled) {
          stalledFlows.add(`${systemId}:${resource}`)
        }

        const spawnChance = Math.min(0.3, rate * 3)

        if (Math.random() < spawnChance) {
          // Find source - prefer origin as central resource hub
          const srcTileId = findConnectedTile(sourceTileId, connections, tiles, true)
          if (srcTileId) {
            const srcPos = getTileCenter(srcTileId, tiles)
            if (srcPos) {
              spawnParticle(srcPos, sourcePos, resource, isStalled)
            }
          }
        }
      }
    }
  }

  // Special: Observer entities generate insight particles
  const hasObserver = state.entities?.some(e => e.subtype === 'observer')
  if (hasObserver && Math.random() < 0.1) {
    const receiverPos = getTileCenter('receiver', tiles)
    if (receiverPos) {
      spawnParticle(
        { x: receiverPos.x + (Math.random() - 0.5) * 30, y: receiverPos.y + (Math.random() - 0.5) * 30 },
        { x: receiverPos.x, y: receiverPos.y - 40 },
        'insight'
      )
    }
  }

  // Special: Influence flowing to receiver when present
  if ((resources.influence ?? 0) > 0.5 && Math.random() < 0.05) {
    const originPos = getTileCenter('origin', tiles)
    const receiverPos = getTileCenter('receiver', tiles)
    if (originPos && receiverPos) {
      spawnParticle(originPos, receiverPos, 'influence')
    }
  }
}

export function drawParticles(ctx: CanvasRenderingContext2D): void {
  for (const p of particles) {
    ctx.beginPath()
    const size = p.size * (1 - p.progress * 0.5)
    ctx.arc(p.x, p.y, size, 0, Math.PI * 2)
    ctx.fillStyle = p.color
    ctx.globalAlpha = 1 - p.progress

    if (p.stalled) {
      // Stalled particles pulse and have a warning glow
      const pulse = 0.5 + Math.sin(Date.now() / 200) * 0.3
      ctx.globalAlpha *= pulse
      ctx.shadowColor = '#ff4444'
      ctx.shadowBlur = 8
    }

    ctx.fill()
    ctx.shadowBlur = 0
  }
  ctx.globalAlpha = 1
}
