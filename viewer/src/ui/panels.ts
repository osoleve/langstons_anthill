import type { GameState, Entity, Decision } from '../types/state.ts'

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

export function renderGoals(state: GameState): void {
  const el = document.getElementById('goals')
  if (!el) return

  const goals = state.meta?.goals ?? {}
  const resources = state.resources ?? {}

  // Filter to unbuilt goals with cost (show all goals with costs, not just those with progress)
  const activeGoals = Object.entries(goals).filter(
    ([_id, goal]) => !goal.built && goal.cost !== undefined
  )

  if (activeGoals.length === 0) {
    el.innerHTML = '<div class="empty">no active goals</div>'
    return
  }

  el.innerHTML = activeGoals
    .map(([id, goal]) => {
      const costEntries = Object.entries(goal.cost as Record<string, number>)
      const progressBars = costEntries.map(([resource, required]) => {
        const current = resources[resource] ?? 0
        const progress = goal.progress?.[resource] ?? 0
        const progressPct = Math.min(100, (progress / required) * 100)
        const canContribute = current > 0 && progress < required

        return `
          <div class="goal-resource ${canContribute ? 'clickable' : ''}"
               data-goal-id="${id}"
               data-resource="${resource}">
            <div class="goal-resource-header">
              <span class="goal-resource-name">${resource}</span>
              <span class="goal-resource-count">${Math.floor(progress)}/${required}</span>
            </div>
            <div class="goal-bar" title="${canContribute ? 'Click to contribute 10' : ''}">
              <div class="goal-bar-fill ${canContribute ? 'can-contribute' : ''}" style="width: ${progressPct}%"></div>
            </div>
          </div>
        `
      }).join('')

      const totalProgress = costEntries.reduce((sum, [resource, required]) => {
        const progress = goal.progress?.[resource] ?? 0
        return sum + (progress / required)
      }, 0) / costEntries.length * 100

      return `
        <div class="goal-card" data-goal-id="${id}">
          <div class="goal-header">
            <span class="goal-name">${goal.name}</span>
            <span class="goal-pct">${totalProgress.toFixed(0)}%</span>
          </div>
          <div class="goal-desc">${goal.description}</div>
          <div class="goal-resources">
            ${progressBars}
          </div>
        </div>
      `
    })
    .join('')

  // Attach click handlers for contributing
  el.querySelectorAll('.goal-resource.clickable').forEach(resourceEl => {
    resourceEl.addEventListener('click', async () => {
      const goalId = resourceEl.getAttribute('data-goal-id')
      const resource = resourceEl.getAttribute('data-resource')

      if (!goalId || !resource) return

      try {
        const response = await fetch('/contribute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            goal_id: goalId,
            resource: resource,
            amount: 10 // Contribute 10 at a time
          })
        })

        if (response.ok) {
          const result = await response.json()
          console.log(`Contributed ${result.amount} ${resource} to ${goalId}`)

          // Visual feedback
          resourceEl.classList.add('contributed')
          setTimeout(() => resourceEl.classList.remove('contributed'), 500)
        }
      } catch (e) {
        console.error('Failed to contribute:', e)
      }
    })
  })
}

export function renderDecisions(decisions: Decision[]): void {
  const el = document.getElementById('decisions')
  if (!el) return

  if (decisions.length === 0) {
    el.innerHTML = '<div class="empty">no decisions logged</div>'
    return
  }

  // Show most recent first
  const recent = [...decisions].reverse()

  el.innerHTML = recent
    .map(d => `
      <div class="decision-entry">
        <div class="decision-tick">t${d.tick}<span class="decision-type">${d.type}</span></div>
        <div class="decision-choice">${d.choice}</div>
        ${d.why ? `<div class="decision-why">${d.why}</div>` : ''}
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
  renderGoals(state)
}
