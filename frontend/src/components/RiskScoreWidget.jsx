import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../AuthContext'
import API_BASE from '../apiBase'

function riskLabel(score) {
  if (score >= 80) return 'CRITICAL RISK'
  if (score >= 60) return 'HIGH RISK'
  if (score >= 40) return 'MEDIUM RISK'
  return 'LOW RISK'
}

function riskLabelClass(score) {
  if (score >= 80) return 'risk-level-btn risk-critical'
  if (score >= 60) return 'risk-level-btn risk-high'
  if (score >= 40) return 'risk-level-btn risk-medium'
  return 'risk-level-btn risk-low'
}

export default function RiskScoreWidget() {
  const { user } = useAuth()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  const wsRef = useRef(null)

  async function loadDashboard() {
    if (!user?.user_id || !user?.token) return
    try {
      const res = await fetch(`${API_BASE}/api/v1/users/${user.user_id}/dashboard`, {
        headers: { Authorization: `Bearer ${user.token}` },
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      setData(json)
      setLastUpdated(new Date())
      setError(null)
    } catch (err) {
      setError('Failed to load risk score.')
    } finally {
      setLoading(false)
    }
  }

  function initWebSocket() {
    if (!user?.user_id || !user?.token) return
    const wsBase = API_BASE ? API_BASE.replace('http', 'ws') : ''
    const wsUrl = `${wsBase}/ws/v1/alerts/${user.user_id}?token=${user.token}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'risk_update' && msg.risk_score !== undefined) {
          setData(prev => prev ? {
            ...prev,
            risk_score: msg.risk_score,
            risk_label: riskLabel(msg.risk_score).replace(/ RISK$/, ''),
          } : prev)
          setLastUpdated(new Date())
        }
      } catch {
        // non-JSON keep-alive frames — ignore
      }
    }

    ws.onclose = () => {
      // Reconnect after 5 s if the component is still mounted
      setTimeout(() => {
        if (wsRef.current === ws) initWebSocket()
      }, 5000)
    }
  }

  useEffect(() => {
    loadDashboard()
    initWebSocket()
    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null  // prevent reconnect loop on unmount
        wsRef.current.close()
      }
    }
  }, [user?.user_id])

  function formatLastUpdated(date) {
    if (!date) return ''
    const diff = Math.round((Date.now() - date.getTime()) / 1000)
    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.round(diff / 60)}m ago`
    return date.toLocaleTimeString()
  }

  if (loading) {
    return (
      <div className="card risk-widget">
        <div className="card-header"><span className="card-title">Risk Score</span></div>
        <div className="loading-spinner" style={{ margin: '32px auto' }} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="card risk-widget">
        <div className="card-header"><span className="card-title">Risk Score</span></div>
        <p className="error-message" style={{ padding: '24px', color: 'var(--risk-high)' }}>{error}</p>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="card risk-widget">
        <div className="card-header"><span className="card-title">Risk Score</span></div>
        <p style={{ padding: '24px', color: 'var(--text-muted)' }}>No risk data yet.</p>
      </div>
    )
  }

  const score = data.risk_score ?? 0
  const barWidth = `${score}%`

  return (
    <div className="card risk-widget">
      <div className="card-header">
        <span className="card-title">Risk Score</span>
      </div>

      <div className="risk-score-value">{score}</div>
      <div className={riskLabelClass(score)}>{riskLabel(score)}</div>

      <div className="risk-bar-container">
        <div className="risk-bar">
          <div className="risk-bar-fill" style={{ width: barWidth }} />
        </div>
      </div>

      <div className="risk-scale">
        <span>0</span>
        <span>25</span>
        <span>50</span>
        <span>75</span>
        <span>100</span>
      </div>

      <div className="risk-footer">
        <div className="risk-change">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
          <span style={{ paddingLeft: '4px' }}>
            {data.active_alerts > 0 ? `${data.active_alerts} active alert${data.active_alerts > 1 ? 's' : ''}` : 'No active alerts'}
          </span>
        </div>
        <span className="risk-time">{formatLastUpdated(lastUpdated)}</span>
      </div>
    </div>
  )
}
