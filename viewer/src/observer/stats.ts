/**
 * Observer Stats Tracking
 *
 * Tracks observer contributions and displays them in the UI.
 * Persists to localStorage so observers can see their cumulative impact.
 */

export interface ObserverStats {
  totalBlessings: number
  resourcesGenerated: Record<string, number>
  miraclesGranted: number
  sessionStart: number
  longestWatchStreak: number
  currentWatchStreak: number
  lastActiveTime: number
}

const STORAGE_KEY = 'langstons_anthill_observer_stats'
const STREAK_TIMEOUT = 60000 // 1 minute of inactivity breaks streak

let stats: ObserverStats = loadStats()
let statsPanel: HTMLElement | null = null

function loadStats(): ObserverStats {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      return JSON.parse(saved)
    }
  } catch {
    // Ignore errors
  }

  return {
    totalBlessings: 0,
    resourcesGenerated: {},
    miraclesGranted: 0,
    sessionStart: Date.now(),
    longestWatchStreak: 0,
    currentWatchStreak: 0,
    lastActiveTime: Date.now()
  }
}

function saveStats(): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stats))
  } catch {
    // Ignore errors
  }
}

export function recordBlessing(type: string, resourceType: string, amount: number): void {
  stats.totalBlessings++
  stats.resourcesGenerated[resourceType] = (stats.resourcesGenerated[resourceType] || 0) + amount

  if (type === 'miracle') {
    stats.miraclesGranted++
  }

  // Update streak
  const now = Date.now()
  if (now - stats.lastActiveTime > STREAK_TIMEOUT) {
    stats.currentWatchStreak = 0
  }
  stats.currentWatchStreak++
  stats.lastActiveTime = now

  if (stats.currentWatchStreak > stats.longestWatchStreak) {
    stats.longestWatchStreak = stats.currentWatchStreak
  }

  saveStats()
  updateStatsPanel()
}

export function initStatsPanel(): void {
  // Create stats panel in bottom-left
  statsPanel = document.createElement('div')
  statsPanel.id = 'observer-stats'
  statsPanel.innerHTML = `
    <div class="observer-title">👁 Observer</div>
    <div class="observer-stat">
      <span class="stat-label">Blessings:</span>
      <span class="stat-value" id="stat-blessings">0</span>
    </div>
    <div class="observer-stat">
      <span class="stat-label">Miracles:</span>
      <span class="stat-value" id="stat-miracles">0</span>
    </div>
    <div class="observer-stat">
      <span class="stat-label">Streak:</span>
      <span class="stat-value" id="stat-streak">0</span>
    </div>
    <div class="observer-resources" id="stat-resources"></div>
    <div class="observer-hint">Click the map to bless the colony</div>
    <div class="combo-bar">
      <div class="combo-fill" id="combo-fill"></div>
    </div>
    <div class="combo-hint" id="combo-hint">Click rapidly for miracles</div>
  `

  document.body.appendChild(statsPanel)
  updateStatsPanel()
}

export function updateStatsPanel(): void {
  if (!statsPanel) return

  const blessingsEl = document.getElementById('stat-blessings')
  const miraclesEl = document.getElementById('stat-miracles')
  const streakEl = document.getElementById('stat-streak')
  const resourcesEl = document.getElementById('stat-resources')

  if (blessingsEl) blessingsEl.textContent = stats.totalBlessings.toString()
  if (miraclesEl) miraclesEl.textContent = stats.miraclesGranted.toString()
  if (streakEl) streakEl.textContent = stats.currentWatchStreak.toString()

  if (resourcesEl) {
    const resourceHtml = Object.entries(stats.resourcesGenerated)
      .map(([resource, amount]) => {
        const formatted = amount < 1 ? amount.toFixed(2) : Math.floor(amount).toString()
        return `<span class="resource-contrib">${resource}: +${formatted}</span>`
      })
      .join('')
    resourcesEl.innerHTML = resourceHtml || '<span class="no-resources">No contributions yet</span>'
  }
}

export function updateComboProgress(progress: number): void {
  const comboFill = document.getElementById('combo-fill')
  const comboHint = document.getElementById('combo-hint')

  if (comboFill) {
    comboFill.style.width = `${progress * 100}%`

    if (progress > 0.8) {
      comboFill.style.background = '#ff88ff'
      comboFill.style.boxShadow = '0 0 10px #ff88ff'
    } else if (progress > 0.5) {
      comboFill.style.background = '#ffcc44'
      comboFill.style.boxShadow = '0 0 5px #ffcc44'
    } else {
      comboFill.style.background = '#88ccff'
      comboFill.style.boxShadow = 'none'
    }
  }

  if (comboHint) {
    if (progress > 0.8) {
      comboHint.textContent = '✨ Almost a miracle!'
      comboHint.style.color = '#ff88ff'
    } else if (progress > 0.5) {
      comboHint.textContent = 'Building power...'
      comboHint.style.color = '#ffcc44'
    } else if (progress > 0) {
      comboHint.textContent = 'Click rapidly for miracles'
      comboHint.style.color = '#666'
    } else {
      comboHint.textContent = 'Click rapidly for miracles'
      comboHint.style.color = '#444'
    }
  }
}

export function getStats(): ObserverStats {
  return { ...stats }
}

export function resetStats(): void {
  stats = {
    totalBlessings: 0,
    resourcesGenerated: {},
    miraclesGranted: 0,
    sessionStart: Date.now(),
    longestWatchStreak: 0,
    currentWatchStreak: 0,
    lastActiveTime: Date.now()
  }
  saveStats()
  updateStatsPanel()
}
