export default function HistoryChart() {
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
          <button className="chart-tab active">30D</button>
          <button className="chart-tab">90D</button>
          <button className="chart-tab">All</button>
        </div>
      </div>

      <div className="chart-placeholder" style={{
        height: '250px',
        border: 'none',
        background: 'transparent',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--text-muted)',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.85rem'
      }}>
        [ Graph component will be placed here ]
      </div>
    </div>
  )
}
