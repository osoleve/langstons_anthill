/**
 * Langston's Anthill Viewer
 *
 * A living window into the colony.
 * Not a debug panel. Not a dashboard.
 * A world that breathes.
 */

import { World } from './world'
import { Renderer } from './systems'
import { SSEClient } from './systems/SSEClient'

class App {
  private world: World
  private renderer: Renderer
  private sse: SSEClient

  private lastTime: number = 0
  private running: boolean = false

  constructor() {
    // Create canvas
    const canvas = document.getElementById('canvas') as HTMLCanvasElement
    if (!canvas) {
      throw new Error('No canvas element found')
    }

    // Initialize world and renderer
    this.world = new World()
    this.renderer = new Renderer(canvas, this.world)

    // Connect to server
    this.sse = new SSEClient()

    this.sse.onState((state) => {
      this.world.applyState(state)
    })

    this.sse.onConnection((connected) => {
      console.log(`[App] Connection: ${connected ? 'online' : 'offline'}`)
    })
  }

  async start(): Promise<void> {
    console.log('[App] Starting...')

    // Fetch initial state
    const initialState = await this.sse.fetchState()
    if (initialState) {
      this.world.applyState(initialState)
      this.renderer.focusOnWorld()
    }

    // Start SSE connection
    this.sse.connect()

    // Start render loop
    this.running = true
    this.lastTime = performance.now()
    requestAnimationFrame((t) => this.loop(t))

    console.log('[App] Running')
  }

  private loop(time: number): void {
    if (!this.running) return

    const dt = Math.min((time - this.lastTime) / 1000, 0.1)  // Cap at 100ms
    this.lastTime = time

    // Update
    this.world.update(dt)
    this.renderer.update(dt)

    // Render
    this.renderer.render()

    requestAnimationFrame((t) => this.loop(t))
  }

  stop(): void {
    this.running = false
    this.sse.disconnect()
  }
}

// Boot
const app = new App()
app.start().catch(console.error)
