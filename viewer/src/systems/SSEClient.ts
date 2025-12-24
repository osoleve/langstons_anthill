/**
 * SSEClient - connects to the tick engine via Server-Sent Events.
 *
 * Receives state updates and translates them into world changes.
 * Handles reconnection gracefully.
 */

import type { ServerState } from '../types'

type StateCallback = (state: ServerState) => void
type ConnectionCallback = (connected: boolean) => void

export class SSEClient {
  private eventSource: EventSource | null = null
  private stateCallbacks: StateCallback[] = []
  private connectionCallbacks: ConnectionCallback[] = []
  private reconnectTimeout: number | null = null
  private isConnected: boolean = false

  private baseUrl: string

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl
  }

  /**
   * Start listening for state updates.
   */
  connect(): void {
    if (this.eventSource) {
      this.eventSource.close()
    }

    console.log('[SSE] Connecting...')
    this.eventSource = new EventSource(`${this.baseUrl}/events`)

    this.eventSource.onopen = () => {
      console.log('[SSE] Connected')
      this.isConnected = true
      this.notifyConnection(true)
    }

    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        // Handle both wrapped format { type: 'state', state: {...} }
        // and raw state format { tick: ..., entities: [...], ... }
        if (data.type === 'state' && data.state) {
          this.notifyState(data.state)
        } else if (data.tick !== undefined && data.entities !== undefined) {
          // Raw state format
          this.notifyState(data)
        }
      } catch (e) {
        console.error('[SSE] Parse error:', e)
      }
    }

    this.eventSource.onerror = () => {
      console.log('[SSE] Disconnected, reconnecting...')
      this.isConnected = false
      this.notifyConnection(false)
      this.eventSource?.close()
      this.eventSource = null

      // Reconnect after delay
      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout)
      }
      this.reconnectTimeout = window.setTimeout(() => {
        this.connect()
      }, 2000)
    }
  }

  /**
   * Fetch current state directly (for initial load).
   */
  async fetchState(): Promise<ServerState | null> {
    try {
      const response = await fetch(`${this.baseUrl}/state`)
      if (!response.ok) return null
      return await response.json()
    } catch {
      return null
    }
  }

  /**
   * Register a callback for state updates.
   */
  onState(callback: StateCallback): void {
    this.stateCallbacks.push(callback)
  }

  /**
   * Register a callback for connection changes.
   */
  onConnection(callback: ConnectionCallback): void {
    this.connectionCallbacks.push(callback)
  }

  /**
   * Disconnect and stop reconnecting.
   */
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
    this.isConnected = false
  }

  /**
   * Check if currently connected.
   */
  getConnectionStatus(): boolean {
    return this.isConnected
  }

  private notifyState(state: ServerState): void {
    for (const callback of this.stateCallbacks) {
      callback(state)
    }
  }

  private notifyConnection(connected: boolean): void {
    for (const callback of this.connectionCallbacks) {
      callback(connected)
    }
  }
}
