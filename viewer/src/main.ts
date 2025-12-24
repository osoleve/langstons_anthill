import { SSEClient, fetchInitialState } from './sse/client.ts'
import { setupCanvas, clearCanvas } from './renderer/canvas.ts'
import { renderTiles, drawConnections } from './renderer/tiles.ts'
import { updateEntityDots, drawEntityDots } from './renderer/entities.ts'
import { updateParticles, spawnResourceParticles, drawParticles } from './renderer/particles.ts'
import { renderAll } from './ui/panels.ts'
import type { GameState } from './types/state.ts'

let currentState: GameState | null = null

function main() {
  const mapContainer = document.getElementById('map')
  if (!mapContainer) {
    console.error('Map container not found')
    return
  }

  const container = mapContainer // Capture for closure
  const canvasContext = setupCanvas(container)
  const client = new SSEClient('/events')

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
}

// Wait for DOM
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', main)
} else {
  main()
}
