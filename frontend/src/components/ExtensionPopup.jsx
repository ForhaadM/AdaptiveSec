import { useState, useEffect } from 'react'
import { useAuth } from '../AuthContext'

const BACKEND_URL = 'http://localhost:8000'

const RISK_COLOR = {
  low:    'var(--accent-green)',
  medium: 'var(--accent-orange)',
  high:   'var(--risk-high)',
}

function getRiskLevel(score) {
  if (score < 35) return 'low'
  if (score < 65) return 'medium'
  return 'high'
}

export default function ExtensionPopup() {
  const { user, logout } = useAuth()
  const [risk, setRisk]         = useState(null)
  const [training, setTraining] = useState(null)
  const [latestAlert, setLatestAlert] = useState(null)

  useEffect(() => {
    if (!user) return
    const headers = { Authorization: `Bearer ${user.token}` }

    fetch(`${BACKEND_URL}/api/v1/users/${user.user_id}/dashboard`, { headers })
      .then(r => r.json())
      .then(d => setRisk(d.risk_score ?? null))
      .catch(() => {})

    fetch(`${BACKEND_URL}/api/v1/users/${user.user_id}/training`, { headers })
      .then(r => r.json())
      .then(d => {
        const modules = d.modules || []
        const done    = modules.filter(m => m.completed).length
        const pct     = modules.length
          ? Math.round(modules.reduce((a, m) => a + (m.progress || 0), 0) / modules.length)
          : 0
        setTraining({ done, total: modules.length, pct })
      })
      .catch(() => {})
      
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

  function openFullDashboard() {
    const url = chrome.runtime.getURL('popup.html') + '?full=1'
    chrome.tabs.create({ url })
  }

  const score = risk ?? '—'
  const level = typeof risk === 'number' ? getRiskLevel(risk) : 'medium'
  const color = RISK_COLOR[level]

  return (
    <div style={{
      width: '360px',
      background: 'var(--bg-dark)',
      color: 'var(--text-main)',
      fontFamily: 'var(--font-sans)',
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '14px 16px',
        borderBottom: '1px solid var(--border-light)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '28px', height: '28px',
            background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))',
            borderRadius: '7px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: '700', fontSize: '0.85rem',
          }}>A</div>
          <span style={{ fontWeight: '600', fontSize: '0.95rem' }}>AdaptiveSec</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {user?.name || user?.email}
          </span>
          <button onClick={logout} style={{
            background: 'transparent',
            border: '1px solid var(--border-light)',
            color: 'var(--text-muted)',
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            padding: '3px 10px',
            borderRadius: '5px',
            cursor: 'pointer',
          }}>Sign out</button>
        </div>
      </div>

      {/* Body */}
      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px', flex: 1 }}>

        {/* Risk Score */}
        <div style={{
          background: 'var(--bg-panel)',
          border: '1px solid var(--border-card)',
          borderRadius: '10px',
          padding: '16px',
        }}>
          <div style={{
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: '10px',
          }}>Risk Score</div>

          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '12px', marginBottom: '12px' }}>
            <span style={{ fontSize: '3rem', fontWeight: '700', color, lineHeight: 1 }}>{score}</span>
            <span style={{
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
              color,
              background: `${color}18`,
              border: `1px solid ${color}44`,
              padding: '3px 10px',
              borderRadius: '4px',
              marginBottom: '6px',
              textTransform: 'uppercase',
            }}>{level} risk</span>
          </div>

          {/* Bar */}
          <div style={{
            height: '4px', background: '#333', borderRadius: '2px', position: 'relative',
          }}>
            <div style={{
              position: 'absolute', top: 0, left: 0, bottom: 0,
              width: typeof risk === 'number' ? `${risk}%` : '0%',
              background: `linear-gradient(90deg, var(--accent-green), var(--accent-orange) 50%, var(--risk-high))`,
              borderRadius: '2px',
              transition: 'width 0.4s ease',
            }} />
          </div>
          <div style={{
            display: 'flex', justifyContent: 'space-between',
            fontFamily: 'var(--font-mono)', fontSize: '0.65rem',
            color: 'var(--text-mono)', marginTop: '4px',
          }}>
            <span>0</span><span>50</span><span>100</span>
          </div>
        </div>

        {/* Real-Time Security Alert */}
        {latestAlert && (
        <div style={{
            background: 'rgba(255,165,0,0.08)',
            border: '1px solid rgba(255,165,0,0.25)',
            borderRadius: '10px',
            padding: '16px',
          }}>
            <div style={{
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--accent-orange)',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              marginBottom: '10px',
            }}>
              Recent Security Alert
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div>
                <strong>Risk Change:</strong> +{latestAlert.score_delta}
              </div>

              <div>
                <strong>Cognitive Bias:</strong> {latestAlert.bias_tag}
              </div>

              <div>
                <strong>Updated Risk Score:</strong> {latestAlert.risk_score}
              </div>

            </div>

          <div style={{
            marginTop: '10px',
            padding: '10px',
            borderRadius: '8px',
            background: 'rgba(255,255,255,0.04)',
            color: 'var(--text-muted)',
            lineHeight: '1.5',
          }}>
              {latestAlert.explanation}
            </div>
            <button
              onClick={() => chrome.tabs.create({ url: 'http://localhost:5173/training' })}
              style={{
                marginTop: '8px',
                padding: '10px',
                background: 'linear-gradient(135deg,var(--accent-blue),var(--accent-purple))',
                border: 'none',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '0.85rem',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              Start Training
            </button>
              </div>
          )}

        {/* Training Progress */}
        <div style={{
          background: 'var(--bg-panel)',
          border: '1px solid var(--border-card)',
          borderRadius: '10px',
          padding: '16px',
        }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            marginBottom: '10px',
          }}>
            <div style={{
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
            }}>Training Progress</div>
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: '0.85rem',
              fontWeight: '700', color: 'var(--text-main)',
            }}>
              {training ? `${training.done}/${training.total}` : '—'}
            </span>
          </div>

          <div style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px' }}>
            <div style={{
              height: '100%', borderRadius: '3px',
              width: training ? `${training.pct}%` : '0%',
              background: 'linear-gradient(90deg, var(--accent-blue), var(--accent-purple))',
              transition: 'width 0.4s ease',
            }} />
          </div>
          <div style={{
            marginTop: '6px', textAlign: 'right',
            fontFamily: 'var(--font-mono)', fontSize: '0.75rem',
            color: 'var(--text-muted)',
          }}>
            {training ? `${training.pct}% complete` : 'Loading…'}
          </div>
        </div>

      </div>

      {/* Footer — Open Dashboard button */}
      <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border-light)' }}>
        <button onClick={openFullDashboard} style={{
          width: '100%',
          padding: '10px',
          background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))',
          border: 'none',
          borderRadius: '8px',
          color: '#fff',
          fontFamily: 'var(--font-sans)',
          fontSize: '0.9rem',
          fontWeight: '600',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
        }}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
            <polyline points="15 3 21 3 21 9"/>
            <line x1="10" y1="14" x2="21" y2="3"/>
          </svg>
          Open Full Dashboard
        </button>
      </div>
    </div>
  )
}
