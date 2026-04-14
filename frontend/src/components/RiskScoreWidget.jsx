import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../AuthContext'
import API_BASE from '../apiBase'

const BACKEND = 'http://localhost:8000'

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

export default function RiskScoreWidget({ userId: propUserId, token: propToken, refreshKey }) {
  const { user } = useAuth()
  const userId = propUserId || user?.user_id
  const token = propToken || user?.token
  const isAgentView = !!propUserId

  const [displayScore, setDisplayScore] = useState(0)
  const [activeAlerts, setActiveAlerts] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  const prevScoreRef = useRef(0)
  const timerRef = useRef(null)
  const wsRef = useRef(null)

  function animateTo(end) {
    const start = prevScoreRef.current
    if (start === end) return
    if (timerRef.current) clearInterval(timerRef.current)
    const steps = 24
    const duration = 800
    let step = 0
    timerRef.current = setInterval(() => {
      step++
      setDisplayScore(Math.round(start + ((end - start) / steps) * step))
      if (step >= steps) {
        clearInterval(timerRef.current)
        setDisplayScore(end)
        prevScoreRef.current = end
      }
    }, duration / steps)
  }

  async function loadScore() {
    if (!userId) return
    try {
      if (isAgentView) {
        const res = await fetch(`${BACKEND}/api/v1/admin/agent-scores`)
        const json = await res.json()
        const s = Math.round(json.agents?.[userId] ?? 0)
        animateTo(s)
      } else {
        const res = await fetch(`${API_BASE}/api/v1/users/${userId}/dashboard`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const json = await res.json()
        const s = Math.round(json.risk_score ?? 0)
        animateTo(s)
        setActiveAlerts(json.active_alerts ?? 0)
      }
      setLastUpdated(new Date())
      setError(null)
    } catch {
      setError('Failed to load risk score.')
    } finally {
      setLoading(false)
    }
  }

  function initWebSocket() {
    if (isAgentView || !userId || !token) return
    const wsBase = API_BASE ? API_BASE.replace('http', 'ws') : 'ws://localhost:8000'
    const ws = new WebSocket(`${wsBase}/ws/v1/alerts/${userId}?token=${token}`)
    wsRef.current = ws
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'risk_update' && msg.risk_score !== undefined) {
          animateTo(Math.round(msg.risk_score))
          setLastUpdated(new Date())
        }
      } catch { }
    }
    ws.onclose = () => {
      setTimeout(() => { if (wsRef.current === ws) initWebSocket() }, 5000)
    }
  }

  useEffect(() => {
    loadScore()
    initWebSocket()
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      if (wsRef.current) { wsRef.current.onclose = null; wsRef.current.close() }
    }
  }, [userId])

  // Re-fetch when refreshKey changes (after simulation)
  useEffect(() => {
    if (refreshKey > 0) {
      // Fetch immediately then again after pipeline processes
      loadScore()
      setTimeout(() => loadScore(), 3500)
    }
  }, [refreshKey])

  function formatLastUpdated(date) {
    if (!date) return ''
    const diff = Math.round((Date.now() - date.getTime()) / 1000)
    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.round(diff / 60)}m ago`
    return date.toLocaleTimeString()
  }

  if (loading) return (
    <div className="card risk-widget">
      <div className="card-header"><span className="card-title">Risk Score</span></div>
      <div className="loading-spinner" style={{ margin: '32px auto' }} />
    </div>
  )

  if (error) return (
    <div className="card risk-widget">
      <div className="card-header"><span className="card-title">Risk Score</span></div>
      <p style={{ padding: '24px', color: 'var(--risk-high)' }}>{error}</p>
    </div>
  )

  return (
    <div className="card risk-widget">
      <div className="card-header"><span className="card-title">Risk Score</span></div>
      <div className="risk-score-value" style={{ transition: 'color 0.4s' }}>{displayScore}</div>
      <div className={riskLabelClass(displayScore)}>{riskLabel(displayScore)}</div>
      <div className="risk-bar-container">
        <div className="risk-bar">
          <div className="risk-bar-fill" style={{ width: `${displayScore}%`, transition: 'width 0.8s cubic-bezier(0.4,0,0.2,1)' }} />
        </div>
      </div>
      <div className="risk-scale">
        <span>0</span><span>25</span><span>50</span><span>75</span><span>100</span>
      </div>
      <div className="risk-footer">
        <div className="risk-change">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
          <span style={{ paddingLeft: '4px' }}>
            {isAgentView
              ? (displayScore === 0 ? 'No activity yet' : `Score: ${displayScore}/100`)
              : (activeAlerts > 0 ? `${activeAlerts} active alert${activeAlerts > 1 ? 's' : ''}` : 'No active alerts')}
          </span>
        </div>
        <span className="risk-time">{formatLastUpdated(lastUpdated)}</span>
      </div>
    </div>
  )
}