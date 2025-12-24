import type { GameState, Tile, System, Entity } from '../types/state.ts'
import { getStalledFlows } from '../renderer/particles.ts'

let modalEl: HTMLDivElement | null = null
let backdropEl: HTMLDivElement | null = null

export function initModal(): void {
  // Create backdrop
  backdropEl = document.createElement('div')
  backdropEl.className = 'modal-backdrop'
  backdropEl.style.display = 'none'
  backdropEl.addEventListener('click', hideModal)
  document.body.appendChild(backdropEl)

  // Create modal container
  modalEl = document.createElement('div')
  modalEl.className = 'modal'
  modalEl.style.display = 'none'
  modalEl.addEventListener('click', (e) => e.stopPropagation())
  document.body.appendChild(modalEl)
}

export function hideModal(): void {
  if (modalEl) modalEl.style.display = 'none'
  if (backdropEl) backdropEl.style.display = 'none'
}

function showModal(content: string, title: string): void {
  if (!modalEl || !backdropEl) return

  modalEl.innerHTML = `
    <div class="modal-header">
      <span class="modal-title">${title}</span>
      <button class="modal-close">&times;</button>
    </div>
    <div class="modal-body">
      ${content}
    </div>
  `

  const closeBtn = modalEl.querySelector('.modal-close')
  closeBtn?.addEventListener('click', hideModal)

  backdropEl.style.display = 'block'
  modalEl.style.display = 'block'
}

export function showTileModal(tileId: string, tile: Tile, state: GameState): void {
  const system = state.systems?.[tileId]
  const entities = state.entities?.filter(e => e.tile === tileId) ?? []
  const connections = state.map?.connections ?? []
  const stalledFlows = getStalledFlows()

  // Find connected tiles
  const connectedTiles: string[] = []
  for (const [a, b] of connections) {
    if (a === tileId) connectedTiles.push(b)
    if (b === tileId) connectedTiles.push(a)
  }

  let content = `<div class="modal-section">`
  content += `<div class="modal-row"><span class="modal-label">Type:</span><span>${tile.type}</span></div>`
  if (tile.description) {
    content += `<div class="modal-desc">${tile.description}</div>`
  }
  if (tile.resource) {
    content += `<div class="modal-row"><span class="modal-label">Resource:</span><span>${tile.resource}</span></div>`
  }
  content += `</div>`

  // Contamination/blight status
  if (tile.contamination !== undefined || tile.blighted) {
    content += `<div class="modal-section">`
    content += `<h3>Status</h3>`
    if (tile.blighted) {
      content += `<div class="modal-warning">BLIGHTED - ${tile.blight_ticks_remaining} ticks remaining</div>`
    } else if (tile.contamination && tile.contamination > 0) {
      content += `<div class="modal-row"><span class="modal-label">Contamination:</span><span>${(tile.contamination * 100).toFixed(1)}%</span></div>`
    } else {
      content += `<div class="modal-row"><span class="modal-label">Contamination:</span><span>clean</span></div>`
    }
    content += `</div>`
  }

  // System information
  if (system) {
    content += `<div class="modal-section">`
    content += `<h3>System: ${system.name}</h3>`
    if (system.description) {
      content += `<div class="modal-desc">${system.description}</div>`
    }

    if (system.generates && Object.keys(system.generates).length > 0) {
      content += `<div class="modal-subsection"><strong>Produces:</strong></div>`
      for (const [resource, rate] of Object.entries(system.generates)) {
        content += `<div class="modal-row"><span class="modal-label">${resource}</span><span class="modal-value-good">+${rate}/tick</span></div>`
      }
    }

    if (system.consumes && Object.keys(system.consumes).length > 0) {
      content += `<div class="modal-subsection"><strong>Consumes:</strong></div>`
      for (const [resource, rate] of Object.entries(system.consumes)) {
        const isStalled = stalledFlows.has(`${tileId}:${resource}`)
        const stalledClass = isStalled ? 'modal-value-warning' : ''
        content += `<div class="modal-row"><span class="modal-label">${resource}</span><span class="modal-value-bad ${stalledClass}">-${rate}/tick${isStalled ? ' (LOW)' : ''}</span></div>`
      }
    }

    if (system.sanity_efficiency !== undefined) {
      const pct = (system.sanity_efficiency * 100).toFixed(1)
      content += `<div class="modal-row"><span class="modal-label">Sanity efficiency:</span><span>${pct}%</span></div>`
    }

    content += `</div>`
  }

  // Connected tiles
  if (connectedTiles.length > 0) {
    content += `<div class="modal-section">`
    content += `<h3>Connections</h3>`
    content += `<div class="modal-tags">`
    for (const id of connectedTiles) {
      const connTile = state.map?.tiles?.[id]
      content += `<span class="modal-tag">${connTile?.name ?? id}</span>`
    }
    content += `</div></div>`
  }

  // Entities present
  if (entities.length > 0) {
    content += `<div class="modal-section">`
    content += `<h3>Entities Here (${entities.length})</h3>`
    for (const entity of entities) {
      const agePercent = ((entity.age / entity.max_age) * 100).toFixed(0)
      const icon = entity.type === 'visitor' ? '👁' : entity.adorned ? '★' : '•'
      const label = entity.type === 'visitor'
        ? (entity.name ?? entity.subtype ?? 'visitor')
        : (entity.role ?? 'ant')
      content += `<div class="modal-entity">`
      content += `<span class="modal-entity-icon">${icon}</span>`
      content += `<span class="modal-entity-name">${label}</span>`
      content += `<span class="modal-entity-stat">age ${agePercent}%</span>`
      content += `<span class="modal-entity-stat">hunger ${entity.hunger.toFixed(0)}</span>`
      content += `</div>`
    }
    content += `</div>`
  }

  showModal(content, tile.name)
}

export function showEntityModal(entity: Entity, state: GameState): void {
  const tile = state.map?.tiles?.[entity.tile]
  const jewelry = state.meta?.jewelry?.find(j => j.worn_by === entity.id)

  let content = `<div class="modal-section">`

  // Basic info
  const entityType = entity.type === 'visitor'
    ? (entity.subtype ?? 'visitor')
    : (entity.role ?? 'ant')
  content += `<div class="modal-row"><span class="modal-label">Type:</span><span>${entityType}</span></div>`
  content += `<div class="modal-row"><span class="modal-label">ID:</span><span class="modal-id">${entity.id}</span></div>`
  content += `<div class="modal-row"><span class="modal-label">Location:</span><span>${tile?.name ?? entity.tile}</span></div>`

  if (entity.description) {
    content += `<div class="modal-desc">${entity.description}</div>`
  }
  content += `</div>`

  // Vital stats
  content += `<div class="modal-section">`
  content += `<h3>Vitals</h3>`

  const agePercent = (entity.age / entity.max_age) * 100
  const ageColor = agePercent > 80 ? 'modal-value-warning' : ''
  content += `<div class="modal-row"><span class="modal-label">Age:</span><span class="${ageColor}">${entity.age} / ${entity.max_age} ticks (${agePercent.toFixed(1)}%)</span></div>`

  const hungerColor = entity.hunger < 30 ? 'modal-value-warning' : ''
  content += `<div class="modal-row"><span class="modal-label">Hunger:</span><span class="${hungerColor}">${entity.hunger.toFixed(1)}</span></div>`
  content += `<div class="modal-row"><span class="modal-label">Hunger rate:</span><span>-${entity.hunger_rate}/tick</span></div>`
  content += `<div class="modal-row"><span class="modal-label">Food:</span><span>${entity.food}</span></div>`

  // Time until death estimates
  const ticksUntilStarvation = entity.hunger / entity.hunger_rate
  const ticksUntilOldAge = entity.max_age - entity.age
  const ticksUntilDeath = Math.min(ticksUntilStarvation, ticksUntilOldAge)
  const deathCause = ticksUntilStarvation < ticksUntilOldAge ? 'starvation' : 'old age'
  content += `<div class="modal-row"><span class="modal-label">Est. lifespan:</span><span>~${Math.floor(ticksUntilDeath)} ticks (${deathCause})</span></div>`

  content += `</div>`

  // Special attributes
  if (entity.adorned || jewelry || entity.processing_corpse || entity.generates) {
    content += `<div class="modal-section">`
    content += `<h3>Special</h3>`

    if (entity.adorned && jewelry) {
      content += `<div class="modal-row"><span class="modal-label">Wearing:</span><span class="modal-value-special">${jewelry.name}</span></div>`
      content += `<div class="modal-row"><span class="modal-label">Adorned at:</span><span>tick ${jewelry.worn_tick}</span></div>`
    }

    if (entity.processing_corpse) {
      content += `<div class="modal-row"><span class="modal-label">Activity:</span><span>Processing corpse (${entity.processing_ticks} ticks)</span></div>`
    }

    if (entity.previous_role) {
      content += `<div class="modal-row"><span class="modal-label">Previous role:</span><span>${entity.previous_role}</span></div>`
    }

    if (entity.generates) {
      content += `<div class="modal-subsection"><strong>Generates:</strong></div>`
      for (const [resource, rate] of Object.entries(entity.generates)) {
        content += `<div class="modal-row"><span class="modal-label">${resource}</span><span class="modal-value-good">+${rate}/tick</span></div>`
      }
    }

    if (entity.influence_rate) {
      content += `<div class="modal-row"><span class="modal-label">Influence rate:</span><span>${entity.influence_rate}/tick</span></div>`
    }

    content += `</div>`
  }

  // Visitor specific
  if (entity.type === 'visitor' && entity.from_outside) {
    content += `<div class="modal-section">`
    content += `<div class="modal-note">This entity came from the Outside.</div>`
    content += `</div>`
  }

  const title = entity.name ?? (entity.adorned ? `★ ${entityType}` : entityType)
  showModal(content, title)
}
