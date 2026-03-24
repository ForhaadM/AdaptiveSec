export default function CognitiveProfileCard() {
  const triggers = [
    { name: 'Urgency Bias', value: 82, color: 'var(--accent-purple)' },
    { name: 'Authority Bias', value: 54, color: 'var(--accent-blue)' },
    { name: 'Social Proof', value: 37, color: '#334155' },
    { name: 'Scarcity', value: 21, color: 'var(--accent-orange)' },
  ];

  return (
    <div className="card cognitive-card">
      <div className="card-header">
        <span className="card-title">Cognitive Vulnerability Profile</span>
      </div>

      <div className="cognitive-main-bias">
        <span style={{ color: '#eab308' }}>⚡</span>
        High Urgency Susceptibility
      </div>

      <p className="cognitive-desc">
        You respond quickly to time-pressure cues. Attackers frequently exploit urgency framing to bypass careful decision-making.
      </p>

      <div className="trigger-list">
        {triggers.map(trigger => (
          <div className="trigger-item" key={trigger.name}>
            <div className="trigger-label">{trigger.name}</div>
            <div className="trigger-bar-bg">
              <div className="trigger-bar-fill" style={{ width: `${trigger.value}%`, background: trigger.color }}></div>
            </div>
            <div className="trigger-value" style={{ color: trigger.color }}>{trigger.value}%</div>
          </div>
        ))}
      </div>
    </div>
  )
}
