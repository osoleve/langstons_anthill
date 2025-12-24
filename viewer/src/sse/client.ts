import type { GameState } from '../types/state.ts'

export type StateHandler = (state: GameState) => void

export class SSEClient {
  private eventSource: EventSource | null = null
  private handlers: Set<StateHandler> = new Set()
  private lastState: GameState | null = null

  constructor(private url: string = '/events') {}

  connect(): void {
    this.eventSource = new EventSource(this.url)

    this.eventSource.onmessage = (event) => {
      try {
        const state = JSON.parse(event.data) as GameState
        this.lastState = state
        this.handlers.forEach(handler => handler(state))
      } catch (e) {
        console.error('Failed to parse state:', e)
      }
    }

    this.eventSource.onerror = () => {
      console.error('SSE connection error, reconnecting...')
      this.reconnect()
    }
  }

  private reconnect(): void {
    this.disconnect()
    setTimeout(() => this.connect(), 2000)
  }

  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
  }

  onState(handler: StateHandler): () => void {
    this.handlers.add(handler)
    // If we already have state, call handler immediately
    if (this.lastState) {
      handler(this.lastState)
    }
    return () => this.handlers.delete(handler)
  }

  getLastState(): GameState | null {
    return this.lastState
  }
}

// Fetch initial state
export async function fetchInitialState(): Promise<GameState | null> {
  try {
    const response = await fetch('/state')
    return await response.json() as GameState
  } catch {
    return null
  }
}
