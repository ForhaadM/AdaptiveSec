import { useState } from 'react'
import { useAuth } from '../AuthContext'
import RiskScoreWidget from './RiskScoreWidget'
import HistoryChart from './HistoryChart'
import CognitiveProfileCard from './CognitiveProfileCard'
import TrainingProgressSection from './TrainingProgressSection'
import ScoreChangeExplanations from './ScoreChangeExplanations'

export default function DashboardLayout() {
  // user contains { user_id, name, email, token } set after Google sign-in
  const { user, logout } = useAuth()
  const [riskScore, setRiskScore] = useState(58)

  return (
    <div className="dashboard-layout">
      <main className="main-wrapper">
        <header className="top-navbar" style={{ position: 'relative' }}>
          <div className="navbar-user">
            <span style={{ fontSize: '1.15rem', fontWeight: '500', letterSpacing: '-0.01em', background: 'linear-gradient(90deg, #a0aec0, #cbd5e0, var(--accent-blue) 80%, var(--accent-purple))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Welcome, {user?.name}
            </span>
          </div>
          <button className="logout-btn" onClick={logout} style={{ position: 'absolute', top: '12px', right: '24px' }}>Sign out</button>
        </header>

        <section className="main-content">
          <div className="dashboard-header">
            <h1 className="dashboard-title"><strong>Security</strong> Dashboard</h1>
            <p className="dashboard-subtitle">Monitor your posture · Complete assigned training · Understand your risk</p>
          </div>

          <div className="grid-layout">
            <RiskScoreWidget score={riskScore} />
            <CognitiveProfileCard />
            <ScoreChangeExplanations />
            <TrainingProgressSection userId={user?.user_id} onScoreUpdate={setRiskScore} />
            <HistoryChart />
          </div>
        </section>
      </main>
    </div>
  )
}
