export default function RiskScoreWidget({ score = 58 }) {
  return (
    <div className="card risk-widget">
      <div className="card-header">
        <span className="card-title">Risk Score</span>
      </div>
      
      <div className="risk-score-value">{score}</div>
      <div className="risk-level-btn">HIGH RISK</div>
      
      <div className="risk-bar-container">
        <div className="risk-bar">
          <div className="risk-bar-fill" style={{ width: `${score}%` }}></div>
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
          <span style={{paddingLeft: '4px'}}>-8 pts from last week</span>
        </div>
        <span className="risk-time">5 min ago</span>
      </div>
    </div>
  )
}
