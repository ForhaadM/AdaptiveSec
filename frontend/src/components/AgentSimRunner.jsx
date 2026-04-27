import { useState, useEffect } from 'react'
import DashboardLayout from './DashboardLayout'
import { AuthProvider } from '../AuthContext'

const BACKEND = 'http://localhost:8000'

const AGENTS = [
    { user_id: 'agent_rushed_001', persona: 'Rushed Employee', dominant: 'URGENCY', group: 'urgency', deterministic: false },
    { user_id: 'agent_deadline_001', persona: 'Deadline Chaser', dominant: 'URGENCY', group: 'urgency', deterministic: false },
    { user_id: 'agent_manager_001', persona: 'Overloaded Manager', dominant: 'URGENCY', group: 'urgency', deterministic: false },
    { user_id: 'agent_rule_001', persona: 'Rule Follower', dominant: 'AUTHORITY', group: 'authority', deterministic: false },
    { user_id: 'agent_compliance_001', persona: 'Compliance Officer', dominant: 'AUTHORITY', group: 'authority', deterministic: false },
    { user_id: 'agent_newhire_001', persona: 'New Hire', dominant: 'AUTHORITY', group: 'authority', deterministic: false },
    { user_id: 'agent_social_001', persona: 'Social User', dominant: 'SOCIAL PROOF', group: 'social', deterministic: false },
    { user_id: 'agent_teamplayer_001', persona: 'Team Player', dominant: 'SOCIAL PROOF', group: 'social', deterministic: false },
    { user_id: 'agent_fomo_001', persona: 'FOMO User', dominant: 'SOCIAL PROOF', group: 'social', deterministic: false },
    { user_id: 'agent_bargain_001', persona: 'Bargain Hunter', dominant: 'SCARCITY', group: 'scarcity', deterministic: false },
    { user_id: 'agent_hoarder_001', persona: 'Resource Hoarder', dominant: 'SCARCITY', group: 'scarcity', deterministic: false },
    { user_id: 'agent_cautious_001', persona: 'Cautious User', dominant: 'CONTROL', group: 'cautious', deterministic: true },
    { user_id: 'agent_secure_001', persona: 'Security Aware', dominant: 'CONTROL', group: 'cautious', deterministic: true },
    { user_id: 'agent_vulnerable_001', persona: 'Vulnerable User', dominant: 'ALL TRIGGERS', group: 'vulnerable', deterministic: true },
    { user_id: 'agent_remote_001', persona: 'Distracted Remote', dominant: 'URGENCY', group: 'vulnerable', deterministic: false },
]

const GROUP_COLORS = {
    urgency: { accent: '#ef4444', bg: 'rgba(239,68,68,0.10)', border: 'rgba(239,68,68,0.25)' },
    authority: { accent: '#3b82f6', bg: 'rgba(59,130,246,0.10)', border: 'rgba(59,130,246,0.25)' },
    social: { accent: '#a855f7', bg: 'rgba(168,85,247,0.10)', border: 'rgba(168,85,247,0.25)' },
    scarcity: { accent: '#f59e0b', bg: 'rgba(245,158,11,0.10)', border: 'rgba(245,158,11,0.25)' },
    cautious: { accent: '#22c55e', bg: 'rgba(34,197,94,0.10)', border: 'rgba(34,197,94,0.25)' },
    vulnerable: { accent: '#f97316', bg: 'rgba(249,115,22,0.10)', border: 'rgba(249,115,22,0.25)' },
}

const TRIGGER_COLORS = {
    urgency: '#ef4444', authority: '#3b82f6',
    scarcity: '#f59e0b', social_proof: '#a855f7',
}

const TRIGGER_ICONS = {
    urgency: '⏰', authority: '🏛️', scarcity: '💎', social_proof: '👥',
}

function scoreColor(score) {
    if (score >= 75) return '#ef4444'
    if (score >= 50) return '#f97316'
    if (score >= 25) return '#f59e0b'
    return '#22c55e'
}

function FakeBrowser({ sim, phase, agent, clickProb, scoreBefore, scoreAfter }) {
    const triggerColor = TRIGGER_COLORS[sim?.trigger_type] || '#64748b'
    const triggerIcon = TRIGGER_ICONS[sim?.trigger_type] || '📧'

    return (
        <div style={{
            background: '#0d1625',
            border: `1px solid ${phase === 'clicked' ? 'rgba(239,68,68,0.4)' : phase === 'skipped' ? 'rgba(34,197,94,0.4)' : '#1a2540'}`,
            borderRadius: 10, overflow: 'hidden',
            transition: 'border-color 0.4s',
            boxShadow: phase === 'clicked' ? '0 0 16px rgba(239,68,68,0.12)' : 'none',
        }}>
            <div style={{ background: '#111827', padding: '6px 10px', display: 'flex', alignItems: 'center', gap: 6, borderBottom: '1px solid #1a2540' }}>
                <div style={{ display: 'flex', gap: 4 }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#ef4444' }} />
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#f59e0b' }} />
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e' }} />
                </div>
                <div style={{ flex: 1, background: '#1e293b', borderRadius: 3, padding: '2px 8px', fontSize: 9, color: '#475569', fontFamily: 'var(--font-mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {sim?.url || 'http://adaptive-sec-sim/...'}
                </div>
            </div>

            <div style={{ padding: '12px 14px' }}>
                <div style={{ background: '#111827', borderRadius: 6, padding: '8px 12px', marginBottom: 10, border: '1px solid #1a2540' }}>
                    <div style={{ fontSize: 9, color: '#475569', fontFamily: 'var(--font-mono)', marginBottom: 3 }}>FROM</div>
                    <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 2 }}>
                        {sim?.trigger_type === 'authority' ? 'it-department@company-internal.com' :
                            sim?.trigger_type === 'urgency' ? 'security-alert@accounts.company.com' :
                                sim?.trigger_type === 'social_proof' ? 'hr-team@company-updates.com' :
                                    'notifications@company-rewards.com'}
                    </div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: '#e2e8f0' }}>
                        {triggerIcon} {sim?.trigger_type === 'authority' ? 'Action Required: Account Verification' :
                            sim?.trigger_type === 'urgency' ? 'Urgent: Immediate Action Required' :
                                sim?.trigger_type === 'social_proof' ? 'Your Team Has Completed Security Update' :
                                    'Limited: Exclusive Access Expiring Soon'}
                    </div>
                </div>

                <div style={{ fontSize: 12, color: '#cbd5e1', lineHeight: 1.6, marginBottom: 12 }}>
                    <p style={{ marginBottom: 8 }}>Dear {agent},</p>
                    <p>{sim?.template}</p>
                </div>

                <div style={{ position: 'relative', display: 'inline-block', marginBottom: 10 }}>
                    <div style={{
                        padding: '8px 16px',
                        background: phase === 'clicked' ? 'rgba(239,68,68,0.2)' : phase === 'cursor-on-link' ? `${triggerColor}30` : `${triggerColor}15`,
                        border: `1px solid ${phase === 'clicked' ? '#ef4444' : triggerColor}`,
                        borderRadius: 5, fontSize: 12, fontWeight: 600,
                        color: phase === 'clicked' ? '#ef4444' : triggerColor,
                        transition: 'all 0.3s',
                        display: 'inline-flex', alignItems: 'center', gap: 6,
                    }}>
                        {phase === 'clicked' ? '🔓 Link Opened — Credentials Captured' : `${triggerIcon} Click Here to Verify →`}
                    </div>
                    {(phase === 'cursor-moving' || phase === 'cursor-on-link' || phase === 'clicked') && (
                        <div style={{
                            position: 'absolute',
                            top: phase === 'cursor-moving' ? -30 : 6,
                            left: phase === 'cursor-moving' ? -40 : 20,
                            fontSize: phase === 'clicked' ? 18 : 16,
                            transition: 'all 0.6s cubic-bezier(0.34,1.56,0.64,1)',
                            filter: phase === 'clicked' ? 'drop-shadow(0 0 5px #ef4444)' : 'none',
                            pointerEvents: 'none', zIndex: 10,
                        }}>
                            {phase === 'clicked' ? '👆' : '🖱️'}
                        </div>
                    )}
                </div>

                {phase === 'skipped' && (
                    <div style={{ padding: '8px 12px', background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.3)', borderRadius: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span>🛡️</span>
                        <span style={{ fontSize: 11, color: '#22c55e', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>THREAT AVOIDED — Agent did not click</span>
                    </div>
                )}
            </div>

            <div style={{ padding: '6px 12px', borderTop: '1px solid #1a2540', background: '#0a0f1a', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 9, color: '#334155', fontFamily: 'var(--font-mono)' }}>
                    {phase === 'idle' && 'Email delivered'}
                    {phase === 'cursor-moving' && `${agent} reading...`}
                    {phase === 'cursor-on-link' && `${agent} hovering over link...`}
                    {phase === 'clicked' && `⚠️ ${agent} clicked!`}
                    {phase === 'skipped' && `✅ Threat identified`}
                </span>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    {clickProb && <span style={{ fontSize: 9, color: '#334155', fontFamily: 'var(--font-mono)' }}>prob: {clickProb}</span>}
                    {scoreAfter !== null && phase === 'clicked' && (
                        <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                            <span style={{ color: '#475569' }}>{scoreBefore}</span>
                            <span style={{ color: '#475569' }}>→</span>
                            <span style={{ color: scoreColor(scoreAfter) }}>{scoreAfter}</span>
                        </span>
                    )}
                </div>
            </div>
        </div>
    )
}

export default function AgentSimRunner() {
    const [selected, setSelected] = useState(AGENTS[0])
    const [allScores, setAllScores] = useState({})
    const [running, setRunning] = useState(false)
    const [resetting, setResetting] = useState(false)
    const [refreshKey, setRefreshKey] = useState(0)
    const [browserPhase, setBrowserPhase] = useState('empty')
    const [currentSim, setCurrentSim] = useState(null)
    const [clickResult, setClickResult] = useState(null)
    const [simHistory, setSimHistory] = useState([])

    async function fetchAllScores() {
        try {
            const resp = await fetch(`${BACKEND}/api/v1/admin/agent-scores`)
            const data = await resp.json()
            setAllScores(data.agents || {})
        } catch (e) { }
    }

    async function runSimulation() {
        if (running) return
        setRunning(true)
        setBrowserPhase('idle')
        setClickResult(null)
        const scoreBefore = allScores[selected.user_id] ?? 0

        try {
            const resp = await fetch(`${BACKEND}/api/v1/admin/run-simulation/${selected.user_id}`, { method: 'POST' })
            const data = await resp.json()
            setCurrentSim(data.simulation)

            await new Promise(r => setTimeout(r, 500))
            setBrowserPhase('cursor-moving')
            await new Promise(r => setTimeout(r, 800))
            setBrowserPhase('cursor-on-link')
            await new Promise(r => setTimeout(r, 600))

            if (data.clicked) {
                setBrowserPhase('clicked')
                await new Promise(r => setTimeout(r, 1500))
                await fetchAllScores()
                const newScores = await fetch(`${BACKEND}/api/v1/admin/agent-scores`).then(r => r.json())
                const scoreAfter = Math.round(newScores.agents?.[selected.user_id] ?? 0)
                setClickResult({ clicked: true, click_prob: data.click_prob, score_before: scoreBefore, score_after: scoreAfter })
                setAllScores(newScores.agents || {})
                setSimHistory(prev => [{
                    id: Date.now(), agent: selected.persona, group: selected.group,
                    sim: data.simulation, clicked: true,
                    score_before: scoreBefore, score_after: scoreAfter,
                    click_prob: data.click_prob, timestamp: new Date().toLocaleTimeString(),
                }, ...prev.slice(0, 9)])
            } else {
                setBrowserPhase('skipped')
                setClickResult({ clicked: false, click_prob: data.click_prob, score_before: scoreBefore, score_after: scoreBefore })
                setSimHistory(prev => [{
                    id: Date.now(), agent: selected.persona, group: selected.group,
                    sim: data.simulation, clicked: false,
                    score_before: scoreBefore, score_after: scoreBefore,
                    click_prob: data.click_prob, timestamp: new Date().toLocaleTimeString(),
                }, ...prev.slice(0, 9)])
            }
            setRefreshKey(k => k + 1)
        } catch (e) {
            setBrowserPhase('empty')
        }
        setRunning(false)
    }

    async function resetAllAgents() {
        if (!confirm('Reset all agent data? This clears all scores and training.')) return
        setResetting(true)
        try {
            await fetch(`${BACKEND}/api/v1/admin/reset-agents`, { method: 'POST' })
            setAllScores({})
            setSimHistory([])
            setCurrentSim(null)
            setBrowserPhase('empty')
            setClickResult(null)
            setRefreshKey(k => k + 1)
            await fetchAllScores()
        } catch (e) { }
        setResetting(false)
    }

    useEffect(() => {
        fetchAllScores()
        const interval = setInterval(fetchAllScores, 5000)
        return () => clearInterval(interval)
    }, [])

    useEffect(() => {
        setBrowserPhase('empty')
        setCurrentSim(null)
        setClickResult(null)
    }, [selected.user_id])

    const gc = GROUP_COLORS[selected.group]

    return (
        <div style={{ display: 'flex', height: '100vh', background: 'var(--bg-dark)', overflow: 'hidden' }}>

            {/* ── Sidebar ── */}
            <div style={{
                width: 200, flexShrink: 0, background: '#060b15',
                borderRight: '1px solid rgba(255,255,255,0.06)',
                display: 'flex', flexDirection: 'column',
                overflowY: 'auto', overflowX: 'hidden',
            }}>
                <div style={{ padding: '14px 12px 10px', borderBottom: '1px solid rgba(255,255,255,0.05)', flexShrink: 0 }}>
                    <div style={{ fontSize: 10, color: '#06b6d4', letterSpacing: '0.1em', fontFamily: 'var(--font-mono)', marginBottom: 6 }}>AGENT SIMULATOR</div>
                    <button onClick={resetAllAgents} disabled={resetting} style={{
                        width: '100%', padding: '5px 0', background: 'transparent',
                        border: '1px solid rgba(239,68,68,0.3)', borderRadius: 5,
                        color: resetting ? '#475569' : '#ef4444', fontSize: 10, fontWeight: 700,
                        cursor: resetting ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-mono)',
                    }}>
                        {resetting ? 'RESETTING...' : '↺ RESET ALL'}
                    </button>
                </div>
                {['urgency', 'authority', 'social', 'scarcity', 'cautious', 'vulnerable'].map(group => {
                    const gc2 = GROUP_COLORS[group]
                    return (
                        <div key={group}>
                            <div style={{ padding: '7px 12px 2px', fontSize: 9, color: gc2.accent, letterSpacing: '0.1em', fontFamily: 'var(--font-mono)' }}>
                                {group.toUpperCase()}
                            </div>
                            {AGENTS.filter(a => a.group === group).map(agent => {
                                const score = allScores[agent.user_id] ?? 0
                                const isSelected = selected.user_id === agent.user_id
                                return (
                                    <div key={agent.user_id} onClick={() => setSelected(agent)} style={{
                                        padding: '6px 12px', cursor: 'pointer',
                                        background: isSelected ? gc2.bg : 'transparent',
                                        borderLeft: isSelected ? `2px solid ${gc2.accent}` : '2px solid transparent',
                                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                        transition: 'all 0.15s',
                                    }}>
                                        <span style={{ fontSize: 11, color: isSelected ? '#e2e8f0' : '#64748b' }}>{agent.persona}</span>
                                        <span style={{ fontSize: 11, fontWeight: 700, color: score > 0 ? scoreColor(score) : '#1e293b', fontFamily: 'var(--font-mono)' }}>
                                            {score > 0 ? Math.round(score) : '—'}
                                        </span>
                                    </div>
                                )
                            })}
                        </div>
                    )
                })}
            </div>

            {/* ── Main content ── */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

                {/* Action bar */}
                <div style={{
                    padding: '10px 20px', flexShrink: 0,
                    borderBottom: '1px solid rgba(255,255,255,0.06)',
                    background: '#060b15',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 13, fontWeight: 700, color: '#e2e8f0' }}>{selected.persona}</span>
                        <span style={{ fontSize: 10, padding: '2px 7px', borderRadius: 4, background: gc.bg, border: `1px solid ${gc.border}`, color: gc.accent, fontFamily: 'var(--font-mono)', letterSpacing: '0.06em' }}>
                            {selected.dominant}
                        </span>
                        {selected.deterministic && (
                            <span style={{ fontSize: 10, padding: '2px 7px', borderRadius: 4, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                                DETERMINISTIC
                            </span>
                        )}
                    </div>
                    <button onClick={runSimulation} disabled={running} style={{
                        padding: '8px 20px',
                        background: running ? 'rgba(255,255,255,0.05)' : `linear-gradient(135deg, ${gc.accent}cc, ${gc.accent}88)`,
                        border: `1px solid ${gc.border}`, borderRadius: 7,
                        color: running ? '#475569' : '#fff', fontSize: 12, fontWeight: 700,
                        cursor: running ? 'not-allowed' : 'pointer',
                        fontFamily: 'var(--font-mono)', letterSpacing: '0.04em',
                    }}>
                        {running ? '⟳ PROCESSING...' : '▶ RUN SIMULATION'}
                    </button>
                </div>

                {/* Body */}
                <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

                    {/* Dashboard — only this scrolls */}
                    <div style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden' }} key={`${selected.user_id}-${refreshKey}`}>
                        <AuthProvider>
                            <DashboardLayout userId={selected.user_id} agentName={selected.persona} />
                        </AuthProvider>
                    </div>

                    {/* Right panel */}
                    <div style={{
                        width: 340, flexShrink: 0,
                        borderLeft: '1px solid rgba(255,255,255,0.06)',
                        background: '#060b15',
                        display: 'flex', flexDirection: 'column',
                        overflow: 'hidden',
                    }}>
                        {/* Browser */}
                        <div style={{ padding: '10px 12px', borderBottom: '1px solid rgba(255,255,255,0.05)', flexShrink: 0, overflow: 'hidden' }}>
                            <div style={{ fontSize: 10, color: '#475569', letterSpacing: '0.1em', fontFamily: 'var(--font-mono)', marginBottom: 8 }}>
                                SIMULATED PHISHING ATTEMPT
                            </div>
                            {browserPhase === 'empty' ? (
                                <div style={{ background: '#0d1625', border: '1px solid #1a2540', borderRadius: 10, padding: '24px 16px', textAlign: 'center' }}>
                                    <div style={{ fontSize: 28, marginBottom: 8 }}>🎯</div>
                                    <div style={{ fontSize: 11, color: '#334155', fontFamily: 'var(--font-mono)' }}>
                                        Press RUN SIMULATION to send a phishing attempt to {selected.persona}
                                    </div>
                                </div>
                            ) : (
                                <FakeBrowser
                                    sim={currentSim}
                                    phase={browserPhase}
                                    agent={selected.persona}
                                    clickProb={clickResult?.click_prob}
                                    scoreBefore={clickResult?.score_before}
                                    scoreAfter={clickResult?.score_after}
                                />
                            )}
                        </div>

                        {/* History */}
                        <div style={{ flex: 1, overflowY: 'auto', padding: '10px 12px' }}>
                            <div style={{ fontSize: 10, color: '#475569', letterSpacing: '0.1em', fontFamily: 'var(--font-mono)', marginBottom: 8 }}>
                                RECENT SIMULATIONS
                            </div>
                            {simHistory.length === 0 ? (
                                <div style={{ fontSize: 11, color: '#1e293b', fontFamily: 'var(--font-mono)' }}>No history yet</div>
                            ) : simHistory.map(h => {
                                const gc3 = GROUP_COLORS[h.group]
                                const tc = TRIGGER_COLORS[h.sim?.trigger_type] || '#64748b'
                                return (
                                    <div key={h.id} style={{
                                        display: 'flex', alignItems: 'center', gap: 6,
                                        padding: '5px 8px', marginBottom: 4,
                                        background: '#0d1625', borderRadius: 6,
                                        border: `1px solid ${h.clicked ? 'rgba(239,68,68,0.2)' : 'rgba(34,197,94,0.15)'}`,
                                    }}>
                                        <span style={{ fontSize: 11 }}>{h.clicked ? '✗' : '✓'}</span>
                                        <span style={{ fontSize: 10, color: gc3.accent, fontFamily: 'var(--font-mono)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {h.agent}
                                        </span>
                                        <span style={{ fontSize: 10, color: tc, fontFamily: 'var(--font-mono)', flexShrink: 0 }}>
                                            {h.sim?.trigger_type?.toUpperCase().replace('_', ' ')}
                                        </span>
                                        {h.clicked && (
                                            <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: scoreColor(h.score_after), flexShrink: 0 }}>
                                                {Math.round(h.score_before)}→{Math.round(h.score_after)}
                                            </span>
                                        )}
                                        <span style={{ fontSize: 9, color: '#334155', flexShrink: 0 }}>{h.timestamp}</span>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}