import { useState, useEffect } from 'react'
import { useAuth } from '../AuthContext'
import API_BASE from '../apiBase'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

const RANGE_PARAM = { '30D': '30d', '90D': '90d', 'All': 'all' }

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const pt = payload[0].payload
  const isHigh = pt.score >= 60
  return (
    <div style={{
      background: 'var(--bg-panel)',
      border: '1px solid var(--border-light)',
      padding: '12px',
      borderRadius: '8px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
      fontFamily: 'var(--font-mono)',
    }}>
      <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>{label}</p>
      <p style={{ margin: '4px 0 0 0', fontSize: '1.25rem', fontWeight: 'bold', color: isHigh ? 'var(--risk-high)' : 'var(--accent-blue)' }}>
        Score: {pt.score}
      </p>
      {pt.reason && (
        <p style={{ margin: '4px 0 0 0', fontSize: '0.75rem', color: 'var(--text-muted)' }}>{pt.reason}</p>
      )}
    </div>
  )
}

export default function HistoryChart() {
  const { user } = useAuth()
  const [timeRange, setTimeRange] = useState('30D')
  const [chartData, setChartData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!user?.user_id || !user?.token) return
    setLoading(true)
    setError(null)
    const param = RANGE_PARAM[timeRange]
    fetch(`${API_BASE}/api/v1/users/${user.user_id}/risk-history?range=${param}`, {
      headers: { Authorization: `Bearer ${user.token}` },
    })
      .then(res => { if (!res.ok) throw new Error(`HTTP ${res.status}`); return res.json() })
      .then(json => {
        const points = (json.data_points || []).map(p => ({
          date: new Date(p.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          score: p.score,
          delta: p.delta,
          reason: p.reason,
        }))
        setChartData(points)
      })
      .catch(() => setError('Failed to load risk history.'))
      .finally(() => setLoading(false))
  }, [user?.user_id, timeRange])

  return (
    <div className="card history-chart">
      <div className="card-header" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <span className="card-title">Risk Score History</span>
        </div>
        <span className="chart-link">Export CSV</span>
      </div>

      <div className="chart-controls">
        <div className="chart-tabs">
          {['30D', '90D', 'All'].map(r => (
            <button
              key={r}
              className={`chart-tab ${timeRange === r ? 'active' : ''}`}
              onClick={() => setTimeRange(r)}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      <div style={{ width: '100%', height: '250px' }}>
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <div className="loading-spinner" />
          </div>
        ) : error ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <p style={{ color: 'var(--risk-high)' }}>{error}</p>
          </div>
        ) : chartData.length === 0 ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <p style={{ color: 'var(--text-muted)' }}>No history yet. Scores will appear after your first simulation.</p>
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
              <XAxis
                dataKey="date"
                axisLine={false}
                tickLine={false}
                tick={{ fill: 'var(--text-muted)', fontSize: 12, fontFamily: 'var(--font-mono)' }}
                minTickGap={60}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: 'var(--text-muted)', fontSize: 12, fontFamily: 'var(--font-mono)' }}
                domain={[0, 100]}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.1)' }} />
              <Line
                type="monotone"
                dataKey="score"
                stroke="var(--accent-blue)"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6, fill: 'var(--accent-cyan)', stroke: 'var(--bg-panel)', strokeWidth: 2 }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
