import { useAuth } from '../AuthContext'
import RiskScoreWidget from './RiskScoreWidget'
import HistoryChart from './HistoryChart'
import CognitiveProfileCard from './CognitiveProfileCard'
import TrainingProgressSection from './TrainingProgressSection'
import ScoreChangeExplanations from './ScoreChangeExplanations'

export default function DashboardLayout() {
  // user contains { user_id, name, email, token } set after Google sign-in
  const { user, logout } = useAuth()

  return (
    <div className="dashboard-layout">
      <main className="main-wrapper">
        <section className="main-content">
          <div className="dashboard-topbar">
            <span style={{ fontSize: '1.15rem', fontWeight: '500', letterSpacing: '-0.01em', background: 'linear-gradient(90deg, #a0aec0, #cbd5e0, var(--accent-blue) 80%, var(--accent-purple))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Welcome, {user?.name}
            </span>
            <button className="logout-btn" onClick={logout}>Sign out</button>
          </div>
          <div className="dashboard-header">
            <h1 className="dashboard-title"><strong>Security</strong> Dashboard</h1>
            <p className="dashboard-subtitle">Monitor your posture · Complete assigned training · Understand your risk</p>
          </div>

          <div className="grid-layout">
            <RiskScoreWidget />
            <CognitiveProfileCard />
            <ScoreChangeExplanations />
            <TrainingProgressSection userId={user?.user_id} />
            <HistoryChart />
          </div>
        </section>
      </main>
    </div>
  )
}
