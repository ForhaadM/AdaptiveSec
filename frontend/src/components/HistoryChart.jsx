import { useState, useEffect } from 'react'
import { useAuth } from '../AuthContext'
import API_BASE from '../apiBase'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

const BACKEND = 'http://localhost:8000'
const RANGE_PARAM = { '30D': '30d', '90D': '90d', 'All': 'all' }

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const pt = payload[0].payload
  const isUp = pt.delta > 0
  return (
    <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-light)', padding: '12px', borderRadius: '8px', boxShadow: '0 4px 20px rgba(0,0,0,0.5)', fontFamily: 'var(--font-mono)', minWidth: 180 }}>
      <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>{label} · {pt.time}</p>
      <p style={{ margin: '6px 0 2px 0', fontSize: '1.2rem', fontWeight: 'bold', color: pt.score >= 60 ? 'var(--risk-high)' : 'var(--accent-blue)' }}>
        Score: {pt.score}
      </p>
      <p style={{ margin: '2px 0', fontSize: '0.8rem', color: isUp ? '#ef4444' : '#22c55e', fontWeight: 700 }}>
        {isUp ? '▲' : '▼'} {Math.abs(pt.delta)} pts ({pt.scoreBefore} → {pt.score})
      </p>
      {pt.reason && (
        <p style={{ margin: '4px 0 0 0', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {pt.reason.replace('_', ' ')}
        </p>
      )}
    </div>
  )
}

export default function HistoryChart({ userId: propUserId, token: propToken, refreshKey }) {
  const { user } = useAuth()
  const userId = propUserId || user?.user_id
  const token = propToken || user?.token
  const isAgentView = !!propUserId

  const [timeRange, setTimeRange] = useState('30D')
  const [chartData, setChartData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  async function loadHistory() {
    if (!userId) return
    setLoading(true)
    setError(null)
    const param = RANGE_PARAM[timeRange]

    try {
      let url, headers
      if (isAgentView) {
        // No-auth admin endpoint for agents
        url = `${BACKEND}/api/v1/admin/agent-history/${userId}?range=${param}`
        headers = {}
      } else {
        url = `${API_BASE}/api/v1/users/${userId}/risk-history?range=${param}`
        headers = { Authorization: `Bearer ${token}` }
      }

      const res = await fetch(url, { headers })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      const points = (json.data_points || []).map((p, i, arr) => {
        const d = new Date(p.timestamp)
        const firstDate = new Date(arr[0].timestamp).toDateString()
        const lastDate = new Date(arr[arr.length - 1].timestamp).toDateString()
        const sameDay = firstDate === lastDate
        return {
          date: sameDay
            ? d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
            : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          time: d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          score: p.score,
          scoreBefore: i > 0 ? arr[i - 1].score : p.score - (p.delta || 0),
          delta: p.delta,
          reason: p.reason,
        }
      })
      setChartData(points)
    } catch {
      setError('Failed to load risk history.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadHistory() }, [userId, timeRange])
  useEffect(() => { if (refreshKey > 0) loadHistory() }, [refreshKey])

  return (
    <div className="card history-chart">
      <div className="card-header" style={{ marginBottom: '16px' }}>
        <span className="card-title">Risk Score History</span>
        <span className="chart-link">Export CSV</span>
      </div>
      <div className="chart-controls">
        <div className="chart-tabs">
          {['30D', '90D', 'All'].map(r => (
            <button key={r} className={`chart-tab ${timeRange === r ? 'active' : ''}`} onClick={() => setTimeRange(r)}>{r}</button>
          ))}
        </div>
      </div>
      <div style={{ width: '100%', height: '250px' }}>
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}><div className="loading-spinner" /></div>
        ) : error ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}><p style={{ color: 'var(--risk-high)' }}>{error}</p></div>
        ) : chartData.length === 0 ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <p style={{ color: 'var(--text-muted)' }}>No history yet. Scores will appear after the first simulation.</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent-blue)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="var(--accent-blue)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-light)" />
              <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 12, fontFamily: 'var(--font-mono)' }} minTickGap={60} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 12, fontFamily: 'var(--font-mono)' }} domain={[0, 100]} />
              <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.1)' }} />
              <Line type="monotone" dataKey="score" stroke="var(--accent-blue)" strokeWidth={2} dot={false} activeDot={{ r: 6, fill: 'var(--accent-cyan)', stroke: 'var(--bg-panel)', strokeWidth: 2 }} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}