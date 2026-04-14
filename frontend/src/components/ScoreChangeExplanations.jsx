import { useState, useEffect } from 'react'
import { useAuth } from '../AuthContext'
import API_BASE from '../apiBase'

const BACKEND = 'http://localhost:8000'
const VISIBLE_BY_DEFAULT = 5

function classifyType(reason) {
  if (!reason) return 'Event'
  if (reason.startsWith('training_completed')) return 'Training'
  if (reason.includes('urgency') || reason.includes('authority') || reason.includes('scarcity') || reason.includes('social')) return 'Alert'
  return 'Threat'
}

function cognitiveTag(reason) {
  if (!reason) return 'Unknown'
  if (reason.includes('urgency') || reason.includes('Urgency')) return 'Urgency Bias'
  if (reason.includes('authority') || reason.includes('Authority')) return 'Authority Bias'
  if (reason.includes('scarcity') || reason.includes('Scarcity')) return 'Scarcity Bias'
  if (reason.includes('social') || reason.includes('Social')) return 'Social Proof'
  if (reason.startsWith('training_completed')) return 'Training'
  return 'General'
}

function buildTitle(entry) {
  if (entry.type === 'Training') return `Risk score reduced after completing module ${entry.reason.replace('training_completed:', '')}`
  if (entry.delta > 0) return `Risk score increased — ${entry.cognitiveTag} trigger detected`
  return `Risk score decreased — positive behaviour recorded`
}

function buildCounterfactual(entry) {
  if (entry.delta < 0) return `Completing this training reduced your exposure by ${Math.abs(entry.delta)} points.`
  return `Recognising this trigger earlier could have limited the impact to ${Math.round(Math.abs(entry.delta) / 2)} pts.`
}

function EntryIcon({ delta, type }) {
  const isPositive = delta > 0
  const isThreat = type === 'Threat'
  let iconClass = 'sce-icon'
  if (isThreat) iconClass += ' sce-icon--threat'
  else if (isPositive) iconClass += ' sce-icon--positive'
  else iconClass += ' sce-icon--negative'
  return (
    <div className={iconClass}>
      {isPositive ? (
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <polyline points="2,14 6,10 10,12 16,4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          <polyline points="12,4 16,4 16,8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ) : (
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <polyline points="2,4 6,8 10,6 16,14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          <polyline points="12,14 16,14 16,10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
    </div>
  )
}

function TypeBadge({ type }) {
  const classMap = { Training: 'sce-type-badge--training', Alert: 'sce-type-badge--alert', Threat: 'sce-type-badge--threat', Behavior: 'sce-type-badge--behavior', Event: 'sce-type-badge--behavior' }
  return <span className={`sce-type-badge ${classMap[type] ?? ''}`}>{type}</span>
}

function formatRelativeTime(isoString) {
  if (!isoString) return ''
  const diff = Date.now() - new Date(isoString).getTime()
  const mins = Math.round(diff / 60000)
  if (mins < 2) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.round(hrs / 24)}d ago`
}

function ScoreChangeEntry({ entry }) {
  const isPositive = entry.delta > 0
  const deltaLabel = isPositive ? `+${entry.delta}` : `−${Math.abs(entry.delta)}`
  return (
    <div className="sce-entry-card">
      <div className="sce-entry">
        <div className="sce-entry-left"><EntryIcon delta={entry.delta} type={entry.type} /></div>
        <div className="sce-entry-body">
          <div className="sce-entry-top">
            <div className={`sce-delta ${isPositive ? 'sce-delta--positive' : 'sce-delta--negative'}`}>
              <span className="sce-delta-value">{deltaLabel}</span>
              <span className="sce-score-range">→ {entry.score}</span>
            </div>
            <TypeBadge type={entry.type} />
          </div>
          <p className="sce-event-title">{entry.title}</p>
          <p className="sce-counterfactual">{entry.counterfactual}</p>
          <div className="sce-entry-footer">
            <span className="sce-tag">{entry.cognitiveTag}</span>
            <span className="sce-timestamp">{formatRelativeTime(entry.timestamp)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function ScoreChangeExplanations({ userId: propUserId, token: propToken, refreshKey }) {
  const { user } = useAuth()
  const userId = propUserId || user?.user_id
  const token = propToken || user?.token
  const isAgentView = !!propUserId

  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showAll, setShowAll] = useState(false)

  async function loadHistory() {
    if (!userId) return
    setLoading(true)
    try {
      let url, headers
      if (isAgentView) {
        url = `${BACKEND}/api/v1/admin/agent-history/${userId}?range=all`
        headers = {}
      } else {
        url = `${API_BASE}/api/v1/users/${userId}/risk-history?range=all`
        headers = { Authorization: `Bearer ${token}` }
      }

      const res = await fetch(url, { headers })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      const points = [...(json.data_points || [])].reverse()
      const built = points
        .filter(p => p.delta !== 0)
        .map((p, i) => {
          const type = classifyType(p.reason)
          const tag = cognitiveTag(p.reason)
          const entry = { id: i, score: p.score, delta: p.delta, reason: p.reason, timestamp: p.timestamp, type, cognitiveTag: tag }
          entry.title = buildTitle(entry)
          entry.counterfactual = buildCounterfactual(entry)
          return entry
        })
      setEntries(built)
      setError(null)
    } catch {
      setError('Failed to load score changes.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadHistory() }, [userId])
  useEffect(() => { if (refreshKey > 0) loadHistory() }, [refreshKey])

  const visible = showAll ? entries : entries.slice(0, VISIBLE_BY_DEFAULT)

  return (
    <div className="card score-change-panel">
      <div className="card-header">
        <span className="card-title">Score Change Explanations</span>
        {!loading && !error && entries.length > 0 && (
          <div className="sce-header-right">
            <button className="sce-view-all-btn" onClick={() => setShowAll(prev => !prev)}>
              {showAll ? 'Show less' : `${entries.length} recent changes`}
            </button>
          </div>
        )}
      </div>
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '24px' }}><div className="loading-spinner" /></div>
      ) : error ? (
        <p style={{ padding: '16px', color: 'var(--risk-high)' }}>{error}</p>
      ) : entries.length === 0 ? (
        <p style={{ padding: '16px', color: 'var(--text-muted)' }}>No score changes yet. Changes will appear here after phishing simulations or completed training.</p>
      ) : (
        <div className="sce-feed">
          {visible.map(entry => <ScoreChangeEntry key={entry.id} entry={entry} />)}
        </div>
      )}
    </div>
  )
}