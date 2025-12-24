import type { GameState, Entity } from '../types/state.ts'

export function renderTick(state: GameState): void {
  const el = document.getElementById('tick')
  if (el) {
    el.textContent = `tick: ${state.tick}`
  }
}

export function renderResources(state: GameState): void {
  const el = document.getElementById('resources')
  if (!el) return

  const resources = state.resources ?? {}
  if (Object.keys(resources).length === 0) {
    el.innerHTML = '<div class="empty">nothing yet</div>'
    return
  }

  el.innerHTML = Object.entries(resources)
    .map(([name, value]) => `
      <div class="resource">
        <span class="resource-name">${name}</span>
        <span class="resource-value">${Math.floor(value ?? 0)}</span>
      </div>
    `)
    .join('')
}

export function renderEntities(state: GameState): void {
  const el = document.getElementById('entities')
  if (!el) return

  const entities = state.entities ?? []
  if (entities.length === 0) {
    el.innerHTML = '<div class="empty">no entities</div>'
    return
  }

  // Group by role
  const byRole: Record<string, number> = {}
  const visitors: Entity[] = []

  for (const e of entities) {
    if (e.type === 'visitor') {
      visitors.push(e)
    } else {
      const role = e.role ?? e.type ?? 'unknown'
      byRole[role] = (byRole[role] ?? 0) + 1
    }
  }

  let html = Object.entries(byRole)
    .map(([role, count]) => `
      <div class="stat-row">
        <span class="stat-label">${role}</span>
        <span class="stat-value">${count}</span>
      </div>
    `)
    .join('')

  // Show visitors separately
  for (const v of visitors) {
    html += `
      <div class="stat-row visitor-row">
        <span class="stat-label">${v.name ?? v.subtype ?? 'visitor'}</span>
        <span class="stat-value visitor-subtype">${v.subtype ?? ''}</span>
      </div>
    `
  }

  el.innerHTML = html
}

export function renderBoredom(state: GameState): void {
  const fill = document.getElementById('boredom-fill')
  if (!fill) return

  const boredom = state.meta?.boredom ?? 0
  const pct = Math.min(100, (boredom / 60) * 100)
  fill.style.width = `${pct}%`
}

export function renderSanity(state: GameState): void {
  const fill = document.getElementById('sanity-fill')
  const value = document.getElementById('sanity-value')
  if (!fill || !value) return

  const sanity = state.meta?.sanity ?? 100
  fill.style.width = `${sanity}%`
  value.textContent = `${sanity.toFixed(1)}%`

  // Color based on level
  if (sanity < 30) {
    fill.style.background = '#a44'
  } else if (sanity < 60) {
    fill.style.background = '#a84'
  } else {
    fill.style.background = '#484'
  }
}

export function renderContamination(state: GameState): void {
  const fill = document.getElementById('contamination-fill')
  const status = document.getElementById('contamination-status')
  if (!fill || !status) return

  const compostTile = state.map?.tiles?.compost
  const contamination = compostTile?.contamination ?? 0

  fill.style.width = `${contamination * 100}%`

  if (compostTile?.blighted) {
    status.textContent = `BLIGHTED (${compostTile.blight_ticks_remaining}t remaining)`
    status.style.color = '#a55'
  } else if (contamination > 0) {
    status.textContent = `${(contamination * 100).toFixed(1)}% blight chance`
    status.style.color = '#755'
  } else {
    status.textContent = 'clean'
    status.style.color = '#555'
  }
}

export function renderSystems(state: GameState): void {
  const el = document.getElementById('systems')
  if (!el) return

  const systems = state.systems ?? {}
  if (Object.keys(systems).length === 0) {
    el.innerHTML = '<div class="empty">no systems</div>'
    return
  }

  el.innerHTML = Object.entries(systems)
    .map(([id, system]) => {
      let output = ''
      if (system.generates && Object.keys(system.generates).length > 0) {
        output = Object.entries(system.generates)
          .map(([r, v]) => `+${v}/tick ${r}`)
          .join(', ')
      }
      return `
        <div class="system">
          <div class="system-name">${system.name ?? id}</div>
          <div class="system-output">${output || 'idle'}</div>
        </div>
      `
    })
    .join('')
}

export function renderCorpses(state: GameState): void {
  const el = document.getElementById('corpses')
  if (!el) return

  const graveyard = state.graveyard ?? { corpses: [], total_processed: 0 }
  const corpses = graveyard.corpses ?? []
  const processed = graveyard.total_processed ?? 0

  if (corpses.length === 0 && processed === 0) {
    el.innerHTML = '<div class="empty">none</div>'
    return
  }

  el.innerHTML = `
    <div class="stat-row">
      <span class="stat-label">awaiting</span>
      <span class="stat-value">${corpses.length}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">processed</span>
      <span class="stat-value">${processed}</span>
    </div>
  `
}

export function renderRejectedIdeas(state: GameState): void {
  const el = document.getElementById('rejected')
  if (!el) return

  const rejected = state.meta?.rejected_ideas ?? []
  if (rejected.length === 0) {
    el.innerHTML = '<div class="empty">empty</div>'
    return
  }

  el.innerHTML = rejected
    .map(idea => `<div class="graveyard-item">${idea}</div>`)
    .join('')
}

export function renderEventLog(state: GameState): void {
  const el = document.getElementById('event-log')
  if (!el) return

  const log = state.meta?.event_log ?? []
  if (log.length === 0) {
    el.innerHTML = '<div class="empty">no events yet</div>'
    return
  }

  // Show last 10 events, most recent first
  const recent = log.slice(-10).reverse()

  el.innerHTML = recent
    .map(event => `
      <div class="event-entry event-type-${event.type}">
        <div class="event-tick">t${event.tick}</div>
        <div class="event-message">${event.message}</div>
      </div>
    `)
    .join('')
}

export function renderAll(state: GameState): void {
  renderTick(state)
  renderResources(state)
  renderEntities(state)
  renderBoredom(state)
  renderSanity(state)
  renderContamination(state)
  renderSystems(state)
  renderCorpses(state)
  renderRejectedIdeas(state)
  renderEventLog(state)
}
