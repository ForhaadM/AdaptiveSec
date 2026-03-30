import { useState, useMemo } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

// Generate mock data mimicking daily risk scores.
const generateMockData = () => {
  const data = [];
  const now = new Date();
  let currentScore = 35; // base score (low risk)

  for (let i = 180; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    
    // add some random noise
    const noise = Math.floor(Math.random() * 8) - 4;
    currentScore = Math.max(0, Math.min(100, currentScore + noise));
    
    // Simulate some phishing test failures leading to spikes in risk score
    let isSpike = false;
    if (i === 150 || i === 110 || i === 75 || i === 42 || i === 15) {
      currentScore = Math.min(100, currentScore + 30 + Math.random() * 20);
      isSpike = true;
    }
    
    // Decay back down after a spike
    if (i === 149 || i === 109 || i === 74 || i === 41 || i === 14) {
      currentScore = Math.max(0, currentScore - 15);
    }
    if (i === 148 || i === 108 || i === 73 || i === 40 || i === 13) {
      currentScore = Math.max(0, currentScore - 10);
    }

    data.push({
      date: d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      score: Math.round(currentScore),
      isSpike,
      timestamp: d.getTime()
    });
  }
  return data;
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const dataPoint = payload[0].payload;
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
        <p style={{ 
          margin: '4px 0 0 0', 
          fontSize: '1.25rem', 
          fontWeight: 'bold', 
          color: dataPoint.isSpike ? 'var(--risk-high)' : 'var(--accent-blue)' 
        }}>
          Score: {dataPoint.score}
        </p>
        {dataPoint.isSpike && (
          <p style={{ margin: '4px 0 0 0', fontSize: '0.75rem', color: 'var(--risk-high)' }}>
            High Risk
          </p>
        )}
      </div>
    );
  }
  return null;
};


export default function HistoryChart() {
  const [timeRange, setTimeRange] = useState('30D');
  
  // Memoize data to prevent re-generating on every render
  const fullData = useMemo(() => generateMockData(), []);
  
  const displayData = useMemo(() => {
    if (timeRange === '30D') return fullData.slice(-30);
    if (timeRange === '90D') return fullData.slice(-90);
    return fullData; // Fallback for 'All'
  }, [fullData, timeRange]);

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
          <button 
            className={`chart-tab ${timeRange === '30D' ? 'active' : ''}`}
            onClick={() => setTimeRange('30D')}
          >
            30D
          </button>
          <button 
            className={`chart-tab ${timeRange === '90D' ? 'active' : ''}`}
            onClick={() => setTimeRange('90D')}
          >
            90D
          </button>
          <button 
            className={`chart-tab ${timeRange === 'All' ? 'active' : ''}`}
            onClick={() => setTimeRange('All')}
          >
            All
          </button>
        </div>
      </div>

      <div style={{ width: '100%', height: '250px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={displayData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--accent-blue)" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="var(--accent-blue)" stopOpacity={0}/>
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
      </div>
    </div>
  );
}
