export default function RiskScoreWidget() {
    const score = 58;

    return (
        <div className="risk-score-widget" style={{
            height: '334px',
            width: '344px',
            border: '1px solid #f9731633',
            borderRadius: '10px',
            padding: '20px',
            transition: 'border-color 0.2s ease',
            backgroundColor: '#080d18',
        }}>

            <div className="risk-score-header" style={{
                fontSize: '12px',
                fontFamily: "IBM Plex Mono, monospace",
                letterSpacing: '0.1em',
                color: '#94a3b8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '16px',
            }}>
                RISK SCORE
            </div>
            <div className="risk-score" style={{
                fontFamily: "IBM Plex Mono, monospace",
                fontSize: '64px',
                fontWeight: 'bold',
                color: '#f97316',
                lineHeight: '1',
                letterSpacing: '-0.03em',
                marginBottom: '4px',
            }}>
                {score}
            </div>
            <div className="score-level" style={{
                display: 'inline-block',
                fontSize: '12px',
                fontFamily: "IBM Plex Mono, monospace",
                padding: '3px 5px',
                borderRadius: '5px',
                backgroundColor: "#f9731633",
                color: '#f97316',
                border: '1px solid #f9731633',
                marginBottom: '12px',
            }}>
                HIGH RISK
            </div>

            {/* Gradient Bar */}
            <div className="score-bar-track" style={{
                position: 'relative',
                background: `linear-gradient(to right, #10b981, #eab308, #f97316, #ef4444)`,
                borderRadius: '2px',
                height: '4px',
                marginBottom: '8px',
                overflow: 'hidden',
            }}>
                {/* Dark overlay to dim the portion after the score */}
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: `${score}%`,
                    right: 0,
                    bottom: 0,
                    backgroundColor: 'rgba(0,0,0,0.6)',
                }} />
            </div>

            {/* Markers */}
            <div className="score-markers" style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '9px',
                fontFamily: "IBM Plex Mono, monospace",
                color: '#374151',
                marginBottom: '12px',
            }}>
                {[0, 25, 50, 75, 100].map(n => (
                    <span key={n}>{n}</span>
                ))}
            </div>
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginTop: '-6px',
            }}>
                <span style={{
                    fontSize: "11px",
                    color: "#10b981",
                    fontFamily: "IBM Plex Mono, monospace",
                }}>
                    ↘ -8 pts this week
                </span>
                <span style={{
                    fontSize: "11px",
                    color: "#94a3b8",
                    fontFamily: "IBM Plex Mono, monospace",
                }}>
                    8 min ago
                </span>
            </div>

        </div>
    );
}