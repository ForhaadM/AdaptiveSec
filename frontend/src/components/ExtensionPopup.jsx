import { useState, useEffect } from 'react'
import { useAuth } from '../AuthContext'

const BACKEND = 'http://localhost:8000'

function riskColor(label) {
  if (!label) return '#f97316'
  const l = label.toLowerCase()
  if (l === 'critical') return '#ef4444'
  if (l === 'high') return '#f97316'
  if (l === 'medium') return '#f59e0b'
  return '#22c55e'
}

function buildSparkPath(points) {
  if (!points || points.length < 2) return null
  const W = 362, H = 60
  const n = points.length
  const xs = points.map((_, i) => (i / (n - 1)) * W)
  const ys = points.map(p => H - (Math.min(100, Math.max(0, p.score)) / 100) * H)
  let line = `M ${xs[0].toFixed(1)} ${ys[0].toFixed(1)}`
  for (let i = 1; i < n; i++) {
    const cpx = ((xs[i - 1] + xs[i]) / 2).toFixed(1)
    line += ` C ${cpx} ${ys[i - 1].toFixed(1)}, ${cpx} ${ys[i].toFixed(1)}, ${xs[i].toFixed(1)} ${ys[i].toFixed(1)}`
  }
  const fill = `${line} L ${xs[n - 1].toFixed(1)} ${H} L ${xs[0].toFixed(1)} ${H} Z`
  return { line, fill, lastX: xs[n - 1], lastY: ys[n - 1] }
}

function timeAgo(date) {
  if (!date) return null
  const diff = Math.floor((Date.now() - date) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`
  return `${Math.floor(diff / 3600)}h ago`
}

function weekDelta(score, history) {
  if (!history || history.length < 2 || score === null) return null
  // Find the data point closest to 7 days ago
  const sevenDaysAgo = Date.now() - 7 * 24 * 60 * 60 * 1000
  let closest = history[0]
  let minDiff = Infinity
  for (const p of history) {
    const d = Math.abs(new Date(p.timestamp).getTime() - sevenDaysAgo)
    if (d < minDiff) { minDiff = d; closest = p }
  }
  return score - closest.score
}

function TrainingIcon({ completed, overdue, color }) {
  if (completed) {
    return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
    )
  }
  if (overdue) {
    return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
    )
  }
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polygon points="10 8 16 12 10 16 10 8" />
    </svg>
  )
}

export default function ExtensionPopup() {
  const { user, logout } = useAuth()
  const [risk, setRisk] = useState(null)
  const [training, setTraining] = useState(null)
  const [latestAlert, setLatestAlert] = useState(null)
  const [dashboard, setDashboard] = useState(null)
  const [history, setHistory] = useState(null)
  const [loadedAt, setLoadedAt] = useState(null)
  const [nudge, setNudge] = useState(null)

  // Load live alert from chrome.storage
  useEffect(() => {
    chrome.storage.local.get(['latest_alert'], ({ latest_alert }) => {
      if (latest_alert) setNudge(latest_alert)
    })
  }, [])

  // Fetch dashboard data
  useEffect(() => {
    if (!user) return
    const headers = { Authorization: `Bearer ${user.token}` }

    fetch(`${BACKEND}/api/v1/users/${user.user_id}/dashboard`, { headers })
      .then(r => r.json())
      .then(d => { setDashboard(d); setLoadedAt(new Date()) })
      .catch(() => { })

    fetch(`${BACKEND}/api/v1/users/${user.user_id}/training`, { headers })
      .then(r => r.json())
      .then(d => setTraining(d.modules || []))
      .catch(() => { })

    fetch(`${BACKEND}/api/v1/users/${user.user_id}/risk-history?range=30d`, { headers })
      .then(r => r.json())
      .then(d => setHistory(d.data_points || []))
      .catch(() => { })

    // read latest alert from background script
    chrome.storage.local.get(['latest_alert'], (result) => {
      if (result.latest_alert) {
        setLatestAlert(result.latest_alert)
      }
    })

    const storageListener = (changes, area) => {
      if (area === 'local' && changes.latest_alert) {
        setLatestAlert(changes.latest_alert.newValue)
      }
    }

    chrome.storage.onChanged.addListener(storageListener)

    return () => {
      chrome.storage.onChanged.removeListener(storageListener)
    }

  }, [user])

  function dismissNudge() {
    chrome.storage.local.remove(['latest_alert'])
    setNudge(null)
  }

  function openFullDashboard() {
    const url = chrome.runtime.getURL('popup.html') + '?full=1'
    chrome.tabs.create({ url })
  }

  const score = dashboard?.risk_score ?? null
  const label = dashboard?.risk_label ?? '—'
  const color = riskColor(dashboard?.risk_label)

  const vulns = dashboard?.vulnerability_profile_summary || []
  const dominant = vulns.length > 0
    ? vulns.reduce((a, b) => (b.bias_score > a.bias_score ? b : a))
    : null

  const spark = history ? buildSparkPath(history) : null
  const delta = weekDelta(score, history)
  const nudgeTrigger = nudge?.trigger_type || nudge?.cognitive_trigger || 'Urgency'

  return (
    <div style={{
      width: 390,
      height: 650,
      backgroundColor: '#080d18',
      color: '#e8eaed',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      fontFamily: 'IBM Plex Mono, monospace',
    }}>

      {/* ── Top bar ── */}
      <div style={{
        flexShrink: 0,
        height: 46,
        backgroundColor: '#060b15',
        padding: '0 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid #1a2540',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="#06B6D4">
            <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z" />
          </svg>
          <span style={{ fontSize: 13, fontWeight: 700, letterSpacing: '0.08em', color: '#06B6D4' }}>
            ADAPTIVESEC
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 11, color: '#22c55e', letterSpacing: '0.04em' }}>
            ● MONITORING
          </span>
          <button onClick={logout} style={{
            background: 'transparent',
            border: '1px solid #1a2540',
            color: '#64748b', fontSize: 10,
            fontFamily: 'IBM Plex Mono, monospace',
            padding: '2px 8px', borderRadius: 4, cursor: 'pointer',
          }}>Sign out</button>
        </div>
      </div>

      {/* ── Scrollable body ── */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '14px 16px 0' }}>

        {/* ── Welcome ── */}
        <div style={{ marginBottom: 12 }}>
          <span style={{ fontSize: 11, color: '#64748b' }}>Welcome back, </span>
          <span style={{ fontSize: 11, color: '#e2e8f0', fontWeight: 600 }}>
            {user?.name || user?.email?.split('@')[0] || 'User'}
          </span>
        </div>

        {/* ── JIT Nudge ── */}
        {nudge && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(245,158,11,0.10), rgba(239,68,68,0.07))',
            border: '1px solid rgba(245,158,11,0.35)',
            borderRadius: 10,
            padding: '12px 14px',
            marginBottom: 16,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 6 }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
              <span style={{ fontSize: 11, fontWeight: 700, color: '#f59e0b', letterSpacing: '0.02em' }}>
                Just-In-Time Training Nudge
              </span>
            </div>
            <p style={{
              fontSize: 11, color: '#cbd5e1', lineHeight: 1.6,
              marginBottom: 9, fontFamily: 'IBM Plex Sans, sans-serif', fontWeight: 400,
            }}>
              You just clicked a link from an <strong style={{ color: '#e8eaed' }}>unverified domain</strong>. This matches a pattern linked to your risk profile.
            </p>

            {/* Added risk details */}
            {latestAlert && (
              <div style={{ marginTop: 8, fontSize: 12 }}>
                <div><strong>Risk Change:</strong> +{latestAlert.score_delta}</div>
                <div><strong>Cognitive Bias:</strong> {latestAlert.bias_tag}</div>
                <div><strong>Updated Risk Score:</strong> {latestAlert.risk_score}</div>
              </div>
            )}

            <div style={{ marginBottom: 10 }}>
              <span style={{
                display: 'inline-flex', alignItems: 'center', gap: 4,
                backgroundColor: 'rgba(245,158,11,0.15)',
                borderRadius: 5, padding: '3px 9px',
                fontSize: 10, color: '#f59e0b',
              }}>
                ⚡ {nudgeTrigger} Bias Trigger
              </span>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={openFullDashboard} style={{
                flex: 1, height: 30,
                backgroundColor: '#f59e0b',
                border: 'none', borderRadius: 6,
                fontSize: 12, fontWeight: 700,
                color: '#000', cursor: 'pointer',
                fontFamily: 'IBM Plex Mono, monospace',
              }}>
                Watch 30s Lesson ▶
              </button>
              <button onClick={dismissNudge} style={{
                height: 30, padding: '0 14px',
                background: 'transparent',
                border: '1px solid #243050',
                borderRadius: 6, fontSize: 11,
                color: '#64748b', cursor: 'pointer',
                fontFamily: 'IBM Plex Mono, monospace',
              }}>
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* ── Risk score ── */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 18, marginBottom: 16 }}>
          {/* Circle */}
          <div style={{
            width: 68, height: 68, borderRadius: '50%', flexShrink: 0,
            border: `5px solid ${color}`,
            boxShadow: `0 0 16px ${color}55`,
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
          }}>
            <span style={{ fontSize: 22, fontWeight: 700, color, lineHeight: 1 }}>
              {score ?? '—'}
            </span>
            <span style={{ fontSize: 9, color: '#64748b', letterSpacing: '0.12em', marginTop: 2 }}>
              RISK
            </span>
          </div>

          {/* Label + delta + timestamp */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: 18, fontWeight: 700, color, lineHeight: 1 }}>
              {label}
            </span>
            {delta !== null && (
              <span style={{
                fontSize: 12, color: delta <= 0 ? '#10b981' : '#ef4444',
                display: 'flex', alignItems: 'center', gap: 4,
              }}>
                {delta <= 0 ? '↘' : '↗'} {Math.abs(Math.round(delta))} pts this week
              </span>
            )}
            <span style={{ fontSize: 10, color: '#64748b' }}>
              {loadedAt ? `Updated ${timeAgo(loadedAt)}` : 'Loading…'}
            </span>
          </div>
        </div>

        {/* ── Vulnerability profile ── */}
        {dominant && (
          <div style={{
            backgroundColor: 'rgba(139,92,246,0.10)',
            border: '1px solid rgba(139,92,246,0.22)',
            borderRadius: 10, marginBottom: 16,
            padding: '10px 14px',
            display: 'flex', alignItems: 'center', gap: 10,
          }}>
            <span style={{ fontSize: 18 }}>🧠</span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <span style={{ fontSize: 10, color: '#64748b', letterSpacing: '0.12em' }}>
                VULNERABILITY PROFILE
              </span>
              <span style={{ fontSize: 12, fontWeight: 700, color: '#a78bfa' }}>
                High {dominant.trigger} Susceptibility
              </span>
            </div>
          </div>
        )}

        {/* ── 30-day trend ── */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontSize: 11, color: '#64748b', letterSpacing: '0.12em' }}>30-DAY TREND</span>
            <button onClick={openFullDashboard} style={{
              background: 'transparent', border: 'none', cursor: 'pointer',
              fontSize: 11, color: '#06b6d4', fontFamily: 'IBM Plex Mono, monospace',
              padding: 0,
            }}>
              Full view →
            </button>
          </div>

          <div style={{
            backgroundColor: '#0d1625',
            borderRadius: 10, padding: '8px 10px',
            border: '1px solid #1a2540',
          }}>
            <svg width="100%" height="60" viewBox="0 0 362 60"
              fill="none" xmlns="http://www.w3.org/2000/svg"
              style={{ overflow: 'visible', display: 'block' }}>
              <defs>
                <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity="0.45" />
                  <stop offset="100%" stopColor={color} stopOpacity="0.02" />
                </linearGradient>
              </defs>
              {spark ? (
                <>
                  <path d={spark.fill} fill="url(#sparkGrad)" />
                  <path d={spark.line} fill="none" stroke={color} strokeWidth="2" />
                  <circle cx={spark.lastX} cy={spark.lastY} r="4" fill={color}
                    style={{ filter: `drop-shadow(0 0 4px ${color})` }} />
                </>
              ) : (
                <line x1="0" y1="30" x2="362" y2="30"
                  stroke="#1e293b" strokeWidth="1.5" strokeDasharray="6 4" />
              )}
            </svg>
          </div>
        </div>

        {/* ── Assigned training ── */}
        <span style={{ fontSize: 11, color: '#64748b', letterSpacing: '0.12em' }}>
          ASSIGNED TRAINING
        </span>

        <div style={{
          marginTop: 10,
          display: 'flex', flexDirection: 'column', gap: 12,
          paddingBottom: 16,
        }}>
          {training === null ? (
            <span style={{ fontSize: 11, color: '#64748b' }}>Loading…</span>
          ) : training.length === 0 ? (
            <span style={{ fontSize: 11, color: '#64748b' }}>No training assigned.</span>
          ) : training.map(m => {
            const pct = Math.round(m.progress || 0)
            const overdue = !m.completed && m.due_date && new Date(m.due_date) < new Date()
            const barColor = m.completed ? '#22c55e' : overdue ? '#f97316' : '#3b82f6'

            return (
              <div key={m.module_id} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                {/* Icon */}
                <div style={{
                  width: 32, height: 32, borderRadius: 8, flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  backgroundColor: `${barColor}20`,
                  border: `1px solid ${barColor}50`,
                }}>
                  <TrainingIcon completed={m.completed} overdue={overdue} color={barColor} />
                </div>

                {/* Title + bar */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 5 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{
                      fontSize: 12, color: '#e2e8f0', fontWeight: 600,
                      overflow: 'hidden', textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap', maxWidth: 200,
                    }}>
                      {m.title}{m.completed ? ' ✓' : ''}
                    </span>
                    <span style={{ fontSize: 11, color: barColor, fontWeight: 600 }}>
                      {pct}%
                    </span>
                  </div>
                  <div style={{ height: 4, backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 2 }}>
                    <div style={{
                      width: `${pct}%`, height: '100%',
                      backgroundColor: barColor, borderRadius: 2,
                      transition: 'width 0.4s ease',
                    }} />
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* ── Open Full Dashboard button ── */}
        <div style={{ padding: '20px 0 14px', borderTop: '1px solid #1a2540' }}>
          <button onClick={openFullDashboard} style={{
            width: '100%', height: 38,
            background: 'linear-gradient(135deg, #1d4ed8 0%, #0891b2 100%)',
            borderRadius: 8, border: 'none',
            fontSize: 13, fontWeight: 700, cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            gap: 8, fontFamily: 'IBM Plex Mono, monospace', color: '#fff',
            boxShadow: '0 2px 12px rgba(6,182,212,0.25)',
          }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
            </svg>
            Open Full Dashboard
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" />
            </svg>
          </button>
          <p style={{
            textAlign: 'center', fontSize: 9, color: '#334155',
            margin: '6px 0 0', letterSpacing: '0.04em',
          }}>
            Opens in new tab · AdaptiveSec Web App
          </p>
        </div>
      </div>
    </div>
  )
}
