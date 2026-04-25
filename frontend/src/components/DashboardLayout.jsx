import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../AuthContext'
import RiskScoreWidget from './RiskScoreWidget'
import HistoryChart from './HistoryChart'
import CognitiveProfileCard from './CognitiveProfileCard'
import TrainingProgressSection from './TrainingProgressSection'
import ScoreChangeExplanations from './ScoreChangeExplanations'

const BACKEND = 'http://localhost:8000'

const AGENT_IDS = [
  'agent_rushed_001', 'agent_deadline_001', 'agent_manager_001',
  'agent_rule_001', 'agent_compliance_001', 'agent_newhire_001',
  'agent_social_001', 'agent_teamplayer_001', 'agent_fomo_001',
  'agent_bargain_001', 'agent_hoarder_001', 'agent_cautious_001',
  'agent_secure_001', 'agent_vulnerable_001', 'agent_remote_001',
]

const AGENT_GROUPS = {
  'Urgency': ['agent_rushed_001', 'agent_deadline_001', 'agent_manager_001'],
  'Authority': ['agent_rule_001', 'agent_compliance_001', 'agent_newhire_001'],
  'Social Proof': ['agent_social_001', 'agent_teamplayer_001', 'agent_fomo_001'],
  'Scarcity': ['agent_bargain_001', 'agent_hoarder_001'],
  'Cautious': ['agent_cautious_001', 'agent_secure_001'],
  'Vulnerable': ['agent_vulnerable_001', 'agent_remote_001'],
}

const TRIGGER_COLORS = {
  urgency: '#ef4444', authority: '#3b82f6',
  scarcity: '#f59e0b', social_proof: '#a855f7',
}
const TRIGGER_ICONS = {
  urgency: '⏰', authority: '🏛️', scarcity: '💎', social_proof: '👥',
}

function ThemeToggle({ theme, onToggle }) {
  const isLight = theme === 'light'
  return (
    <div
      onClick={onToggle}
      title={isLight ? 'Switch to dark mode' : 'Switch to light mode'}
      style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', userSelect: 'none' }}
    >
      <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>
        {isLight ? '☀️' : '🌙'}
      </span>
      <div style={{
        width: 40, height: 22, borderRadius: 11,
        background: isLight ? '#06B6D4' : '#334155',
        position: 'relative', transition: 'background 0.3s',
        border: '1px solid rgba(255,255,255,0.1)', flexShrink: 0,
      }}>
        <div style={{
          position: 'absolute',
          top: 2, left: isLight ? 20 : 2,
          width: 16, height: 16, borderRadius: '50%',
          background: '#fff',
          transition: 'left 0.3s cubic-bezier(0.4,0,0.2,1)',
          boxShadow: '0 1px 4px rgba(0,0,0,0.3)',
        }} />
      </div>
    </div>
  )
}

function FakeBrowser({ sim, phase, agentName }) {
  if (!sim) return null
  const triggerColor = TRIGGER_COLORS[sim.trigger_type] || '#64748b'
  const triggerIcon = TRIGGER_ICONS[sim.trigger_type] || '📧'
  return (
    <div style={{
      background: '#0d1625',
      border: `1px solid ${phase === 'clicked' ? 'rgba(239,68,68,0.5)' : phase === 'skipped' ? 'rgba(34,197,94,0.4)' : '#1a2540'}`,
      borderRadius: 10, overflow: 'hidden', transition: 'border-color 0.4s',
      boxShadow: phase === 'clicked' ? '0 0 20px rgba(239,68,68,0.15)' : 'none',
    }}>
      <div style={{ background: '#111827', padding: '6px 10px', display: 'flex', alignItems: 'center', gap: 6, borderBottom: '1px solid #1a2540' }}>
        <div style={{ display: 'flex', gap: 4 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#ef4444' }} />
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#f59e0b' }} />
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e' }} />
        </div>
        <div style={{ flex: 1, background: '#1e293b', borderRadius: 3, padding: '2px 8px', fontSize: 10, color: '#475569', fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {sim.url}
        </div>
      </div>
      <div style={{ padding: '14px 16px' }}>
        <div style={{ background: '#111827', borderRadius: 6, padding: '8px 12px', marginBottom: 10, border: '1px solid #1a2540' }}>
          <div style={{ fontSize: 9, color: '#475569', fontFamily: 'monospace', marginBottom: 3 }}>FROM</div>
          <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 2 }}>
            {sim.trigger_type === 'authority' ? 'it-department@company-internal.com' :
              sim.trigger_type === 'urgency' ? 'security-alert@accounts.company.com' :
                sim.trigger_type === 'social_proof' ? 'hr-team@company-updates.com' :
                  'notifications@company-rewards.com'}
          </div>
          <div style={{ fontSize: 12, fontWeight: 600, color: '#e2e8f0' }}>
            {triggerIcon} {sim.trigger_type === 'urgency' ? 'Urgent: Immediate Action Required' :
              sim.trigger_type === 'authority' ? 'Action Required: Account Verification' :
                sim.trigger_type === 'social_proof' ? 'Your Team Has Updated Their Settings' :
                  'Limited: Exclusive Access Expiring Soon'}
          </div>
        </div>
        <div style={{ fontSize: 12, color: '#cbd5e1', lineHeight: 1.6, marginBottom: 12 }}>
          <p style={{ marginBottom: 8 }}>Dear {agentName},</p>
          <p>{sim.template}</p>
        </div>
        <div style={{ position: 'relative', display: 'inline-block', marginBottom: 10 }}>
          <div style={{
            padding: '8px 16px',
            background: phase === 'clicked' ? 'rgba(239,68,68,0.2)' : phase === 'cursor-on-link' ? `${triggerColor}30` : `${triggerColor}15`,
            border: `1px solid ${phase === 'clicked' ? '#ef4444' : triggerColor}`,
            borderRadius: 5, fontSize: 12, fontWeight: 600,
            color: phase === 'clicked' ? '#ef4444' : triggerColor,
            transition: 'all 0.3s', display: 'inline-flex', alignItems: 'center', gap: 6,
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
          <div style={{ padding: '8px 12px', background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.3)', borderRadius: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>🛡️</span>
            <span style={{ fontSize: 11, color: '#22c55e', fontFamily: 'monospace', fontWeight: 700 }}>THREAT AVOIDED — Agent did not click</span>
          </div>
        )}
      </div>
      <div style={{ padding: '5px 12px', borderTop: '1px solid #1a2540', background: '#0a0f1a', fontSize: 9, color: '#334155', fontFamily: 'monospace' }}>
        {phase === 'idle' && 'Phishing email delivered to inbox'}
        {phase === 'cursor-moving' && `${agentName} is reading the email...`}
        {phase === 'cursor-on-link' && `${agentName} is hovering over the link...`}
        {phase === 'clicked' && `⚠️ ${agentName} clicked the phishing link!`}
        {phase === 'skipped' && `✅ ${agentName} identified the threat`}
      </div>
    </div>
  )
}

export default function DashboardLayout({ userId: propUserId, agentName }) {
  const { user, logout } = useAuth()

  const userId = propUserId || user?.user_id
  const token = user?.token
  const displayName = agentName || user?.name || 'User'
  const isAgentView = !!propUserId
  const isAgentUser = AGENT_IDS.includes(user?.user_id)
  const isLocalhost = window.location.hostname === 'localhost' || !!(typeof chrome !== 'undefined' && chrome?.runtime?.id)
  const showSimControls = isAgentUser || isAgentView || isLocalhost

  const [theme, setTheme] = useState(() => localStorage.getItem('adaptivesec-theme') || 'dark')
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('adaptivesec-theme', theme)
  }, [theme])

  const [activeAgentId, setActiveAgentId] = useState(userId)
  const [showAgentDropdown, setShowAgentDropdown] = useState(false)
  const dropdownRef = useRef(null)

  const [running, setRunning] = useState(false)
  const [resetting, setResetting] = useState(false)
  const [browserPhase, setBrowserPhase] = useState('empty')
  const [currentSim, setCurrentSim] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [simHistory, setSimHistory] = useState([])
  const [showBrowser, setShowBrowser] = useState(false)
  const [aiRefreshKey, setAiRefreshKey] = useState(0)

  useEffect(() => {
    function handleClick(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowAgentDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  async function runSimulation() {
    if (running) return
    setRunning(true)
    setShowBrowser(true)
    setBrowserPhase('idle')
    setShowAgentDropdown(false)
    try {
      const resp = await fetch(`${BACKEND}/api/v1/admin/run-simulation/${activeAgentId}`, { method: 'POST' })
      const data = await resp.json()
      setCurrentSim(data.simulation)
      await new Promise(r => setTimeout(r, 500))
      setBrowserPhase('cursor-moving')
      await new Promise(r => setTimeout(r, 800))
      setBrowserPhase('cursor-on-link')
      await new Promise(r => setTimeout(r, 600))
      if (data.clicked) {
        setBrowserPhase('clicked')
        await new Promise(r => setTimeout(r, 5000))
        setSimHistory(prev => [{ id: Date.now(), clicked: true, trigger: data.simulation?.trigger_type, agent: activeAgentId, timestamp: new Date().toLocaleTimeString() }, ...prev.slice(0, 7)])
      } else {
        setBrowserPhase('skipped')
        setSimHistory(prev => [{ id: Date.now(), clicked: false, trigger: data.simulation?.trigger_type, agent: activeAgentId, timestamp: new Date().toLocaleTimeString() }, ...prev.slice(0, 7)])
      }
      setRefreshKey(k => k + 1)
      setTimeout(() => setAiRefreshKey(k => k + 1), 4000)
      if (typeof chrome !== 'undefined' && chrome?.storage) {
        chrome.storage.local.set({ last_sim_timestamp: Date.now() })
      }
    } catch {
      setBrowserPhase('empty')
    }
    setRunning(false)
  }

  async function resetAgent() {
    if (!confirm('Reset all agent data? This clears all scores and training.')) return
    setResetting(true)
    try {
      if (isAgentUser || isAgentView) {
        await fetch(`${BACKEND}/api/v1/admin/reset-agents`, { method: 'POST' })
      } else {
        await fetch(`${BACKEND}/api/v1/admin/reset-user/${activeAgentId}`, { method: 'POST' })
      }
      setSimHistory([])
      setBrowserPhase('empty')
      setCurrentSim(null)
      await new Promise(r => setTimeout(r, 500))
      setRefreshKey(k => k + 1)
      if (!isAgentUser && !isAgentView) {
        setTimeout(() => window.location.reload(), 800)
      }
      if (typeof chrome !== 'undefined' && chrome?.storage) {
        chrome.storage.local.set({ last_sim_timestamp: Date.now() })
      }
    } catch { }
    setResetting(false)
  }

  const activeAgentShort = activeAgentId.replace('agent_', '').replace('_001', '')

  return (
    <div className="dashboard-layout">
      <main className="main-wrapper">
        <section className="main-content">

          <div className="dashboard-topbar">
            <span style={{
              fontSize: '1.5rem', fontWeight: '600', letterSpacing: '-0.01em',
              background: 'linear-gradient(90deg, #a0aec0, #cbd5e0, var(--accent-blue) 80%, var(--accent-purple))',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>
              {isAgentView
                ? `Agent: ${displayName}`
                : `Welcome, ${AGENT_IDS.includes(activeAgentId)
                  ? `Agent ${activeAgentId.replace('agent_', '').replace('_001', '')}`
                  : displayName}`}
            </span>

            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginLeft: 'auto' }}>
              <ThemeToggle theme={theme} onToggle={() => setTheme(t => t === 'dark' ? 'light' : 'dark')} />

              {showSimControls && (
                <>
                  <button onClick={resetAgent} disabled={resetting} style={{
                    padding: '6px 14px', background: 'transparent',
                    border: '1px solid rgba(239,68,68,0.4)', borderRadius: 6,
                    color: resetting ? '#475569' : '#ef4444', fontSize: 11, fontWeight: 700,
                    cursor: resetting ? 'not-allowed' : 'pointer', fontFamily: 'monospace',
                  }}>
                    {resetting ? 'RESETTING...' : '↺ RESET'}
                  </button>

                  <div ref={dropdownRef} style={{ position: 'relative' }}>
                    <div style={{ display: 'flex', borderRadius: 6, overflow: 'hidden', border: '1px solid rgba(239,68,68,0.4)' }}>
                      <button
                        onClick={runSimulation}
                        disabled={running}
                        style={{
                          padding: '6px 14px',
                          background: running ? 'rgba(255,255,255,0.05)' : 'linear-gradient(135deg, #ef4444cc, #ef444488)',
                          border: 'none',
                          color: running ? '#475569' : '#fff', fontSize: 11, fontWeight: 700,
                          cursor: running ? 'not-allowed' : 'pointer', fontFamily: 'monospace',
                        }}
                      >
                        {running ? '⟳ PROCESSING...' : `▶ RUN — ${activeAgentShort.toUpperCase()}`}
                      </button>
                      <button
                        onClick={() => !running && setShowAgentDropdown(v => !v)}
                        disabled={running}
                        style={{
                          padding: '6px 8px',
                          background: running ? 'rgba(255,255,255,0.02)' : 'rgba(239,68,68,0.3)',
                          border: 'none', borderLeft: '1px solid rgba(239,68,68,0.3)',
                          color: running ? '#475569' : '#fff', fontSize: 10,
                          cursor: running ? 'not-allowed' : 'pointer',
                        }}
                      >
                        {showAgentDropdown ? '▲' : '▼'}
                      </button>
                    </div>

                    {showAgentDropdown && (
                      <div style={{
                        position: 'absolute', top: 'calc(100% + 6px)', right: 0,
                        background: 'var(--bg-panel)', border: '1px solid var(--border-card)',
                        borderRadius: 8, minWidth: 220, zIndex: 100,
                        boxShadow: '0 8px 32px rgba(0,0,0,0.3)', overflow: 'hidden',
                      }}>
                        <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border-light)', fontSize: 9, color: 'var(--text-muted)', fontFamily: 'monospace', letterSpacing: '0.1em' }}>
                          SELECT AGENT TO SIMULATE
                        </div>
                        {Object.entries(AGENT_GROUPS).map(([group, agents]) => (
                          <div key={group}>
                            <div style={{ padding: '4px 12px', fontSize: 9, color: 'var(--text-mono)', fontFamily: 'monospace', letterSpacing: '0.08em', background: 'var(--bg-dark)' }}>
                              {group.toUpperCase()}
                            </div>
                            {agents.map(agentId => (
                              <div
                                key={agentId}
                                onClick={() => { setActiveAgentId(agentId); setShowAgentDropdown(false); setRefreshKey(k => k + 1) }}
                                style={{
                                  padding: '7px 12px', cursor: 'pointer',
                                  fontSize: 11, fontFamily: 'monospace',
                                  color: agentId === activeAgentId ? 'var(--accent-cyan)' : 'var(--text-muted)',
                                  background: agentId === activeAgentId ? 'rgba(6,182,212,0.08)' : 'transparent',
                                  display: 'flex', alignItems: 'center', gap: 8,
                                  borderLeft: agentId === activeAgentId ? '2px solid var(--accent-cyan)' : '2px solid transparent',
                                }}
                              >
                                {agentId === activeAgentId && <span style={{ fontSize: 8 }}>●</span>}
                                {agentId.replace('agent_', '').replace('_001', '')}
                              </div>
                            ))}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              )}

              {!isAgentView && (
                <button className="logout-btn" onClick={logout}>Sign out</button>
              )}
            </div>
          </div>

          <div className="dashboard-header">
            <h1 className="dashboard-title"><strong>Security</strong> Dashboard</h1>
            <p className="dashboard-subtitle">
              {showSimControls
                ? `Synthetic persona · Monitoring risk profile`
                : 'Monitor your posture · Complete assigned training · Understand your risk'}
            </p>
          </div>

          <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="grid-layout">
                <RiskScoreWidget
                  userId={isAgentUser || isAgentView ? activeAgentId : undefined}
                  token={token}
                  refreshKey={refreshKey}
                />
                <CognitiveProfileCard
                  userId={isAgentUser || isAgentView ? activeAgentId : undefined}
                  token={token}
                  refreshKey={refreshKey}
                />
                <ScoreChangeExplanations
                  userId={isAgentUser || isAgentView ? activeAgentId : undefined}
                  token={token}
                  refreshKey={refreshKey + aiRefreshKey}
                />
                <TrainingProgressSection
                  userId={isAgentUser || isAgentView ? activeAgentId : undefined}
                  token={token}
                  refreshKey={refreshKey}
                  onComplete={() => setRefreshKey(k => k + 1)}
                />
                <HistoryChart
                  userId={isAgentUser || isAgentView ? activeAgentId : undefined}
                  token={token}
                  refreshKey={refreshKey}
                />
              </div>
            </div>

            {showSimControls && showBrowser && (
              <div style={{ width: 340, flexShrink: 0, position: 'sticky', top: 20 }}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.1em', fontFamily: 'monospace', marginBottom: 8 }}>
                  SIMULATED PHISHING ATTEMPT
                </div>
                {browserPhase === 'idle' ? (
                  <div style={{ background: '#0d1625', border: '1px solid #1a2540', borderRadius: 10, padding: '24px', textAlign: 'center', marginBottom: 16 }}>
                    <div style={{ fontSize: 11, color: '#334155', fontFamily: 'monospace' }}>Delivering phishing email...</div>
                  </div>
                ) : (
                  <div style={{ marginBottom: 16 }}>
                    <FakeBrowser sim={currentSim} phase={browserPhase} agentName={activeAgentShort} />
                  </div>
                )}
                <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.1em', fontFamily: 'monospace', marginBottom: 8 }}>
                  RECENT SIMULATIONS
                </div>
                <div style={{ background: 'var(--bg-panel)', borderRadius: 10, border: '1px solid var(--border-card)', padding: '10px 12px' }}>
                  {simHistory.length === 0 ? (
                    <div style={{ fontSize: 11, color: 'var(--text-mono)', fontFamily: 'monospace' }}>No history yet</div>
                  ) : simHistory.map(h => (
                    <div key={h.id} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '5px 0', borderBottom: '1px solid var(--border-light)' }}>
                      <span style={{ fontSize: 12 }}>{h.clicked ? '✗' : '✓'}</span>
                      <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'monospace', flex: 1 }}>
                        {h.agent?.replace('agent_', '').replace('_001', '')}
                      </span>
                      <span style={{ fontSize: 10, color: TRIGGER_COLORS[h.trigger] || '#64748b', fontFamily: 'monospace' }}>
                        {h.trigger?.toUpperCase().replace('_', ' ')}
                      </span>
                      <span style={{ fontSize: 10, color: h.clicked ? '#ef4444' : '#22c55e', fontFamily: 'monospace', marginLeft: 4 }}>
                        {h.clicked ? 'CLICKED' : 'SKIPPED'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

        </section>
      </main>
    </div>
  )
}