import { useState } from 'react';

const ENTRIES = [
    {
        id: 1,
        delta: -8,
        scoreFrom: 66,
        scoreTo: 58,
        type: 'Training',
        title: 'Score dropped after completing "Password Security Best Practices"',
        counterfactual: 'Without this training, your score would remain 8 points higher.',
        cognitiveTag: 'Urgency Bias',
        timestamp: '5 min ago',
    },
    {
        id: 2,
        delta: +5,
        scoreFrom: 61,
        scoreTo: 66,
        type: 'Alert',
        title: 'Urgency trigger fired: "Suspicious Login Attempt Detected"',
        counterfactual: 'Addressing this alert immediately would have prevented the 5-point increase.',
        cognitiveTag: 'Urgency Bias',
        timestamp: '2h ago',
    },
    {
        id: 3,
        delta: +7,
        scoreFrom: 57,
        scoreTo: 64,
        type: 'Threat',
        title: 'Multiple failed authentication attempts from new device',
        counterfactual: 'Earlier threat detection would have reduced score impact by ~4 points.',
        cognitiveTag: 'Authority Bias',
        timestamp: '1d ago',
    },
    {
        id: 4,
        delta: -5,
        scoreFrom: 62,
        scoreTo: 57,
        type: 'Behavior',
        title: '5 days of safe browsing improved baseline score',
        counterfactual: 'Continuing this pattern will reduce your score by ~2 pts/week.',
        cognitiveTag: 'Time-Decay',
        timestamp: '2d ago',
    },
    {
        id: 5,
        delta: +3,
        scoreFrom: 54,
        scoreTo: 57,
        type: 'Threat',
        title: 'Phishing email link clicked before sandbox catch',
        counterfactual: 'Identifying the phishing attempt earlier would have limited impact to +1 pt.',
        cognitiveTag: 'Confirmation Bias',
        timestamp: '3d ago',
    },
];

const VISIBLE_BY_DEFAULT = 5;

function EntryIcon({ delta, type }) {
    const isPositive = delta > 0;
    const isThreat = type === 'Threat';

    let iconClass = 'sce-icon';
    if (isThreat) iconClass += ' sce-icon--threat';
    else if (isPositive) iconClass += ' sce-icon--positive';
    else iconClass += ' sce-icon--negative';

    return (
        <div className={iconClass}>
            {isPositive ? (
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                    <polyline points="2,14 6,10 10,12 16,4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                    <polyline points="12,4 16,4 16,8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                </svg>
            ) : (
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                    <polyline points="2,4 6,8 10,6 16,14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                    <polyline points="12,14 16,14 16,10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                </svg>
            )}
        </div>
    );
}

function TypeBadge({ type }) {
    const classMap = {
        Training: 'sce-type-badge--training',
        Alert: 'sce-type-badge--alert',
        Threat: 'sce-type-badge--threat',
        Behavior: 'sce-type-badge--behavior',
    };
    return (
        <span className={`sce-type-badge ${classMap[type] ?? ''}`}>{type}</span>
    );
}

function ScoreChangeEntry({ entry }) {
    const isPositive = entry.delta > 0;
    const deltaLabel = isPositive ? `+${entry.delta}` : `−${Math.abs(entry.delta)}`;

    return (
        <div className="sce-entry-card">
            <div className="sce-entry">
                <div className="sce-entry-left">
                    <EntryIcon delta={entry.delta} type={entry.type} />
                </div>
                <div className="sce-entry-body">
                    <div className="sce-entry-top">
                        <div className={`sce-delta ${isPositive ? 'sce-delta--positive' : 'sce-delta--negative'}`}>
                            <span className="sce-delta-value">{deltaLabel}</span>
                            <span className="sce-score-range">({entry.scoreFrom} → {entry.scoreTo})</span>
                        </div>
                        <TypeBadge type={entry.type} />
                    </div>
                    <p className="sce-event-title">{entry.title}</p>
                    <p className="sce-counterfactual">{entry.counterfactual}</p>
                    <div className="sce-entry-footer">
                        <span className="sce-tag">{entry.cognitiveTag}</span>
                        <span className="sce-timestamp">{entry.timestamp}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function ScoreChangeExplanations() {
    const [showAll, setShowAll] = useState(false);
    const visibleEntries = showAll ? ENTRIES : ENTRIES.slice(0, VISIBLE_BY_DEFAULT);

    return (
        <div className="card score-change-panel">
            <div className="card-header">
                <span className="card-title">Score Change Explanations</span>
                <div className="sce-header-right">
                    <button className="sce-view-all-btn" onClick={() => setShowAll(prev => !prev)}>
                        {showAll ? 'Show less' : `${ENTRIES.length} recent changes`}
                    </button>
                </div>
            </div>
            <div className="sce-feed">
                {visibleEntries.map(entry => (
                    <ScoreChangeEntry key={entry.id} entry={entry} />
                ))}
            </div>
        </div>
    );
}
