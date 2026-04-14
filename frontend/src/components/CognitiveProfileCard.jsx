import { useState, useEffect } from 'react'
import { useAuth } from '../AuthContext'
import API_BASE from '../apiBase'

const BIAS_COLOR = {
  Urgency: 'var(--accent-purple)',
  Authority: 'var(--accent-blue)',
  Scarcity: 'var(--accent-orange)',
  SocialProof: '#334155',
}

const BIAS_LABEL = {
  Urgency: 'Urgency Bias',
  Authority: 'Authority Bias',
  Scarcity: 'Scarcity',
  SocialProof: 'Social Proof',
}

const DOMINANT_DESCRIPTIONS = {
  Urgency: 'You respond quickly to time-pressure cues. Attackers frequently exploit urgency framing to bypass careful decision-making.',
  Authority: 'You tend to comply with requests that appear to come from authority figures. Attackers impersonate executives and IT to exploit this.',
  Scarcity: 'Limited-time offers and exclusive access prompts lower your guard. Attackers use artificial scarcity to rush decisions.',
  SocialProof: 'You give weight to actions taken by others. Attackers fake social validation to make phishing links seem trustworthy.',
}

export default function CognitiveProfileCard() {
  const { user } = useAuth()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!user?.user_id || !user?.token) return
    fetch(`${API_BASE}/api/v1/users/${user.user_id}/profile`, {
      headers: { Authorization: `Bearer ${user.token}` },
    })
      .then(res => { if (!res.ok) throw new Error(`HTTP ${res.status}`); return res.json() })
      .then(json => { setData(json); setError(null) })
      .catch(() => setError('Failed to load vulnerability profile.'))
      .finally(() => setLoading(false))
  }, [user?.user_id])

  if (loading) {
    return (
      <div className="card cognitive-card">
        <div className="card-header"><span className="card-title">Cognitive Vulnerability Profile</span></div>
        <div className="loading-spinner" style={{ margin: '32px auto' }} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="card cognitive-card">
        <div className="card-header"><span className="card-title">Cognitive Vulnerability Profile</span></div>
        <p className="error-message" style={{ padding: '24px', color: 'var(--risk-high)' }}>{error}</p>
      </div>
    )
  }

  const biasScores = data?.bias_scores ?? {}
  const dominant = data?.dominant_cognitive_trait  // null if no data yet
  const hasData = dominant !== null && dominant !== undefined

  // Build display list in descending order of score
  const triggers = Object.entries(biasScores)
    .map(([key, value]) => ({
      key,
      name: BIAS_LABEL[key] ?? key,
      value: Math.round(value * 100),  // bias_score is 0–N clicks; normalise to percentage (cap 100)
      color: BIAS_COLOR[key] ?? '#334155',
    }))
    .sort((a, b) => b.value - a.value)

  // Normalise display values to max 100%
  const maxVal = Math.max(...triggers.map(t => t.value), 1)
  const normalised = triggers.map(t => ({ ...t, pct: Math.min(100, Math.round((t.value / maxVal) * 100)) }))

  return (
    <div className="card cognitive-card">
      <div className="card-header">
        <span className="card-title">Cognitive Vulnerability Profile</span>
      </div>

      {hasData ? (
        <>
          <div className="cognitive-main-bias">
            <span style={{ color: '#eab308' }}>⚡</span>
            {` High ${BIAS_LABEL[dominant] ?? dominant} Susceptibility`}
          </div>
          <p className="cognitive-desc">
            {DOMINANT_DESCRIPTIONS[dominant] ?? 'Your dominant bias has been identified from simulation results.'}
          </p>
        </>
      ) : (
        <p className="cognitive-desc" style={{ color: 'var(--text-muted)' }}>
          No bias data yet. Complete a phishing simulation to populate your profile.
        </p>
      )}

      <div className="trigger-list">
        {normalised.map(trigger => (
          <div className="trigger-item" key={trigger.key}>
            <div className="trigger-label">{trigger.name}</div>
            <div className="trigger-bar-bg">
              <div
                className="trigger-bar-fill"
                style={{ width: `${trigger.pct}%`, background: trigger.color }}
              />
            </div>
            <div className="trigger-value" style={{ color: trigger.color }}>{trigger.pct}%</div>
          </div>
        ))}
      </div>
    </div>
  )
}
