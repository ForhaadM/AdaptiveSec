import RiskScoreWidget from './RiskScoreWidget'
import HistoryChart from './HistoryChart'
import CognitiveProfileCard from './CognitiveProfileCard'
import TrainingProgressSection from './TrainingProgressSection'

export default function DashboardLayout() {
  return (
    <div className="dashboard-layout">
      {/*
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">A</div>
          AdaptiveSec
        </div>
        <nav>
          <div className="nav-item active">Dashboard</div>
          <div className="nav-item">Something</div>
        </nav>
      </aside> 
      */}

      <main className="main-wrapper">
        <header className="top-navbar">
          {/* <input type="text" className="search-bar" placeholder="Search..." /> */}
        </header>

        <section className="main-content">
          <div className="dashboard-header">
            <h1 className="dashboard-title"><strong>Security</strong> Dashboard</h1>
            <p className="dashboard-subtitle">Monitor your posture · Complete assigned training · Understand your risk</p>
          </div>

          <div className="grid-layout">
            <RiskScoreWidget />
            <CognitiveProfileCard />
            <TrainingProgressSection />
            <HistoryChart />
          </div>
        </section>
      </main>
    </div>
  )
}
