import { SSEClient, fetchInitialState } from './sse/client.ts'
import { setupCanvas, clearCanvas } from './renderer/canvas.ts'
import { renderTiles, drawConnections, setTileClickHandler, getTileAtPosition } from './renderer/tiles.ts'
import { updateEntityDots, drawEntityDots, getEntityDots } from './renderer/entities.ts'
import { updateParticles, spawnResourceParticles, drawParticles } from './renderer/particles.ts'
import { updateSpirits, drawSpirits } from './renderer/spirits.ts'
import { renderAll, renderDecisions } from './ui/panels.ts'
import { initTooltip, handleTooltipHover, handleEntityClick } from './ui/tooltip.ts'
import { initModal, showTileModal, showEntityModal } from './ui/modal.ts'
import { createBlessing, updateBlessings, drawBlessings, getComboProgress } from './observer/blessings.ts'
import { initAtmosphere, updateAtmosphere, drawAtmosphere, getAtmosphereMood } from './observer/atmosphere.ts'
import { initStatsPanel, recordBlessing, updateComboProgress } from './observer/stats.ts'
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
  initStatsPanel()
  initAtmosphere(canvasContext.width, canvasContext.height)

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

  // Blessing click handler - clicks anywhere on map create blessings
  container.addEventListener('click', (e) => {
    const rect = container.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    // ALWAYS try to create a blessing first (this is the main interaction!)
    if (currentState) {
      const tileId = getTileAtPosition(x, y, currentState)
      const blessing = createBlessing(x, y, tileId, currentState)

      if (blessing) {
        // Flash effect
        container.classList.add('blessing-flash')
        setTimeout(() => container.classList.remove('blessing-flash'), 300)

        // Record stats IMMEDIATELY (don't wait for state update)
        const resourceTypes: Record<string, string> = {
          touch: 'influence',
          gift: 'nutrients',
          attention: 'insight',
          miracle: 'strange_matter'
        }
        const amounts: Record<string, number> = {
          touch: 0.1,
          gift: 5,
          attention: 0.02,
          miracle: 0.05
        }
        recordBlessing(blessing.type, resourceTypes[blessing.type], amounts[blessing.type])

        // Also send to server immediately
        fetch('/bless', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            blessings: [{
              type: blessing.type,
              tileId: blessing.tileId,
              amount: amounts[blessing.type]
            }]
          })
        }).catch(() => {})
      }
    }

    // ALSO check if clicking on an entity (shift-click for modal)
    if (e.shiftKey) {
      const entityDots = getEntityDots()
      const entity = handleEntityClick(e, container, entityDots)
      if (entity && currentState) {
        showEntityModal(entity, currentState)
      }
    }
  })

  // Handle state updates
  function handleState(state: GameState) {
    currentState = state
    renderAll(state)
    renderTiles(container, state)
  }

  // Update mood indicator
  function updateMoodIndicator() {
    const mood = getAtmosphereMood()
    const moodEl = document.getElementById('mood-indicator')
    if (moodEl) {
      moodEl.textContent = mood
      moodEl.className = mood
    }
  }

  // Animation loop
  function animate() {
    if (currentState) {
      clearCanvas(canvasContext)

      // Draw atmosphere first (behind everything)
      updateAtmosphere(currentState, canvasContext.width, canvasContext.height)
      drawAtmosphere(canvasContext.ctx)

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

      // Update and draw blessings (on top)
      updateBlessings()
      drawBlessings(canvasContext.ctx)

      // Update combo progress
      updateComboProgress(getComboProgress())

      // Update mood indicator periodically
      updateMoodIndicator()
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
