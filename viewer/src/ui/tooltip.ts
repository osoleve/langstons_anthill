import type { Entity } from '../types/state.ts'

interface EntityDot {
  x: number
  y: number
  entity: Entity
}

let tooltipEl: HTMLDivElement | null = null

export function initTooltip(): void {
  tooltipEl = document.createElement('div')
  tooltipEl.className = 'entity-tooltip'
  tooltipEl.style.display = 'none'
  document.body.appendChild(tooltipEl)
}

export function handleTooltipHover(
  e: MouseEvent,
  mapContainer: HTMLElement,
  entityDots: Map<string, EntityDot>
): void {
  if (!tooltipEl) return

  const rect = mapContainer.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top

  // Find nearest entity within range
  let nearestEntity: Entity | null = null
  let nearestDist = 20 // Detection radius in pixels

  for (const [_id, dot] of entityDots) {
    const dx = dot.x - mouseX
    const dy = dot.y - mouseY
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist < nearestDist) {
      nearestDist = dist
      nearestEntity = dot.entity
    }
  }

  if (nearestEntity) {
    showTooltip(nearestEntity, e.clientX, e.clientY)
  } else {
    hideTooltip()
  }
}

function showTooltip(entity: Entity, x: number, y: number): void {
  if (!tooltipEl) return

  const agePercent = ((entity.age / entity.max_age) * 100).toFixed(1)
  const hungerPercent = entity.hunger.toFixed(1)

  let content = `<div class="tooltip-header">`
  if (entity.type === 'visitor') {
    content += `<span class="tooltip-type visitor">${entity.name || entity.subtype || 'visitor'}</span>`
  } else {
    content += `<span class="tooltip-type">${entity.role || 'ant'}</span>`
    if (entity.adorned) {
      content += `<span class="tooltip-adorned">★</span>`
    }
  }
  content += `</div>`

  content += `<div class="tooltip-stats">`
  content += `<div class="tooltip-row"><span>age:</span><span>${agePercent}%</span></div>`
  content += `<div class="tooltip-row"><span>hunger:</span><span>${hungerPercent}</span></div>`
  content += `<div class="tooltip-row"><span>tile:</span><span>${entity.tile}</span></div>`

  if (entity.type === 'visitor' && entity.description) {
    content += `<div class="tooltip-desc">${entity.description}</div>`
  }

  if (entity.processing_corpse) {
    content += `<div class="tooltip-activity">processing corpse...</div>`
  }

  content += `</div>`

  tooltipEl.innerHTML = content
  tooltipEl.style.display = 'block'
  tooltipEl.style.left = `${x + 15}px`
  tooltipEl.style.top = `${y + 15}px`
}

function hideTooltip(): void {
  if (tooltipEl) {
    tooltipEl.style.display = 'none'
  }
}
