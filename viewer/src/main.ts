import { SSEClient, fetchInitialState } from './sse/client.ts'
import { setupCanvas, clearCanvas } from './renderer/canvas.ts'
import { renderTiles, drawConnections, setTileClickHandler } from './renderer/tiles.ts'
import { updateEntityDots, drawEntityDots, getEntityDots } from './renderer/entities.ts'
import { updateParticles, spawnResourceParticles, drawParticles } from './renderer/particles.ts'
import { updateSpirits, drawSpirits } from './renderer/spirits.ts'
import { renderAll, renderDecisions } from './ui/panels.ts'
import { initTooltip, handleTooltipHover, handleEntityClick } from './ui/tooltip.ts'
import { initModal, showTileModal, showEntityModal } from './ui/modal.ts'
import type { GameState, Decision } from './types/state.ts'

let currentState: GameState | null = null
let lastDecisionsFetch = 0

function main() {
  const mapContainer = document.getElementById('map')
  if (!mapContainer) {
    console.error('Map container not found')
    return
  }

  const container = mapContainer // Capture for closure
  const canvasContext = setupCanvas(container)
  const client = new SSEClient('/events')

  // Initialize UI systems
  initTooltip()
  initModal()

  // Set up tile click handler
  setTileClickHandler((tileId, tile) => {
    if (currentState) {
      showTileModal(tileId, tile, currentState)
    }
  })

  // Handle mouse events on canvas for entity interaction
  container.addEventListener('mousemove', (e) => {
    const entityDots = getEntityDots()
    handleTooltipHover(e, container, entityDots)
  })

  // Entity click handler
  container.addEventListener('click', (e) => {
    const entityDots = getEntityDots()
    const entity = handleEntityClick(e, container, entityDots)
    if (entity && currentState) {
      showEntityModal(entity, currentState)
    }
  })

  // Handle state updates
  function handleState(state: GameState) {
    currentState = state
    renderAll(state)
    renderTiles(container, state)
  }

  // Animation loop
  function animate() {
    if (currentState) {
      clearCanvas(canvasContext)

      // Draw connections behind everything
      drawConnections(canvasContext.ctx, currentState)

      // Update and draw spirits (corpse ghosts)
      updateSpirits(currentState)
      drawSpirits(canvasContext.ctx)

      // Update and draw entities
      updateEntityDots(currentState)
      drawEntityDots(canvasContext.ctx)

      // Spawn and draw particles
      spawnResourceParticles(currentState)
      updateParticles()
      drawParticles(canvasContext.ctx)
    }

    requestAnimationFrame(animate)
  }

  // Start
  client.onState(handleState)
  client.connect()
  animate()

  // Load initial state
  fetchInitialState().then(state => {
    if (state) handleState(state)
  })

  // Fetch decisions periodically (every 10 seconds)
  async function fetchDecisions() {
    try {
      const response = await fetch('/decisions')
      if (response.ok) {
        const decisions: Decision[] = await response.json()
        renderDecisions(decisions)
      }
    } catch (e) {
      console.error('Failed to fetch decisions:', e)
    }
  }

  // Initial fetch and periodic refresh
  fetchDecisions()
  setInterval(fetchDecisions, 10000)
}

// Wait for DOM
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', main)
} else {
  main()
}
