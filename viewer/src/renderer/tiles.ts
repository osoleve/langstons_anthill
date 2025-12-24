import type { GameState, Tile } from '../types/state.ts'
import { getStalledFlows } from './particles.ts'

export interface TilePosition {
  x: number
  y: number
  centerX: number
  centerY: number
}

const TILE_SIZE = 100
const TILE_GAP = 20
const OFFSET_X = 250
const OFFSET_Y = 150

// Store click handlers for cleanup
type TileClickHandler = (tileId: string, tile: Tile) => void
let currentClickHandler: TileClickHandler | null = null

export function setTileClickHandler(handler: TileClickHandler): void {
  currentClickHandler = handler
}

export function getTilePosition(tile: Tile): TilePosition {
  const x = tile.x * (TILE_SIZE + TILE_GAP) + OFFSET_X
  const y = tile.y * (TILE_SIZE + TILE_GAP) + OFFSET_Y
  return {
    x,
    y,
    centerX: x + TILE_SIZE / 2,
    centerY: y + TILE_SIZE / 2
  }
}

export function getTileCenter(tileId: string, tiles: Record<string, Tile>): { x: number; y: number } | null {
  const tile = tiles[tileId]
  if (!tile) return null
  const pos = getTilePosition(tile)
  return { x: pos.centerX, y: pos.centerY }
}

export function renderTiles(container: HTMLElement, state: GameState): void {
  // Clear existing tiles
  const existing = container.querySelector('.tiles-container')
  if (existing) existing.remove()

  const tilesContainer = document.createElement('div')
  tilesContainer.className = 'tiles-container'
  container.appendChild(tilesContainer)

  const tiles = state.map?.tiles ?? {}
  const systems = state.systems ?? {}
  const entities = state.entities ?? []
  const stalledFlows = getStalledFlows()

  // Check which tiles have bottlenecks
  const tilesWithBottlenecks = new Set<string>()
  for (const flowKey of stalledFlows) {
    const systemId = flowKey.split(':')[0]
    // Find tile for this system
    if (tiles[systemId]) {
      tilesWithBottlenecks.add(systemId)
    } else {
      // Check for tile suffix pattern
      const withSuffix = `${systemId}_tile`
      if (tiles[withSuffix]) {
        tilesWithBottlenecks.add(withSuffix)
      }
    }
  }

  for (const [id, tile] of Object.entries(tiles)) {
    const div = document.createElement('div')
    div.className = 'tile'
    div.dataset.tileId = id

    // System status
    const system = systems[id]
    if (system) {
      div.classList.add('has-system')
      if (system.generates && Object.keys(system.generates).length > 0) {
        div.classList.add('generating')
      }
    }

    // Bottleneck indicator
    if (tilesWithBottlenecks.has(id)) {
      div.classList.add('has-bottleneck')
    }

    // Blight
    if (tile.blighted) {
      div.classList.add('blighted')
    }

    // Antenna
    if (tile.type === 'antenna') {
      div.classList.add('antenna')
      if ((state.resources?.influence ?? 0) > 0.5) {
        div.classList.add('broadcasting')
      }
    }

    const pos = getTilePosition(tile)
    div.style.left = `${pos.x}px`
    div.style.top = `${pos.y}px`

    // Count entities
    const antsHere = entities.filter(e => e.tile === id && e.type !== 'visitor').length
    const visitorsHere = entities.filter(e => e.tile === id && e.type === 'visitor').length

    let entityInfo = ''
    if (antsHere > 0) {
      entityInfo += `<div class="ant-count">${antsHere} ant${antsHere > 1 ? 's' : ''}</div>`
    }
    if (visitorsHere > 0) {
      entityInfo += `<div class="ant-count visitor-count">${visitorsHere} visitor${visitorsHere > 1 ? 's' : ''}</div>`
    }

    div.innerHTML = `
      <div class="tile-name">${tile.name}</div>
      <div class="tile-info">${tile.type}</div>
      ${entityInfo}
    `

    // Click handler
    div.addEventListener('click', () => {
      if (currentClickHandler) {
        currentClickHandler(id, tile)
      }
    })

    tilesContainer.appendChild(div)
  }
}

export function drawConnections(
  ctx: CanvasRenderingContext2D,
  state: GameState
): void {
  const tiles = state.map?.tiles
  const connections = state.map?.connections
  if (!tiles || !connections) return

  ctx.strokeStyle = '#333'
  ctx.lineWidth = 1
  ctx.setLineDash([4, 4])

  for (const [from, to] of connections) {
    const fromCenter = getTileCenter(from, tiles)
    const toCenter = getTileCenter(to, tiles)
    if (fromCenter && toCenter) {
      ctx.beginPath()
      ctx.moveTo(fromCenter.x, fromCenter.y)
      ctx.lineTo(toCenter.x, toCenter.y)
      ctx.stroke()
    }
  }

  ctx.setLineDash([])
}
