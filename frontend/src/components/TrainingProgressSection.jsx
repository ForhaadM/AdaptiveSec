import { useState, useEffect } from 'react'
import { useAuth } from '../AuthContext'
import API_BASE from '../apiBase'

export default function TrainingProgressSection() {
  const { user } = useAuth()
  const [modules, setModules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedModule, setSelectedModule] = useState(null);
  const [moduleDetail, setModuleDetail] = useState(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  useEffect(() => {
    if (!user?.user_id || !user?.token) return
    setLoading(true)
    fetch(`${API_BASE}/api/v1/users/${user.user_id}/training`, {
      headers: { Authorization: `Bearer ${user.token}` },
    })
      .then(res => { if (!res.ok) throw new Error(`HTTP ${res.status}`); return res.json() })
      .then(json => {
        const today = new Date()
        const mapped = (json.modules || []).map(m => {
          let status
          if (m.completed) {
            status = 'complete'
          } else if (m.progress > 0) {
            status = 'in-progress'
          } else if (m.due_date && new Date(m.due_date) < today) {
            status = 'overdue'
          } else {
            status = 'not-started'
          }
          return {
            id: m.module_id,
            title: m.title,
            category: m.bias_target,
            progress: m.progress,
            status,
            dueDate: m.due_date,
          }
        })
        setModules(mapped)
        setError(null)
      })
      .catch(() => setError('Failed to load training modules.'))
      .finally(() => setLoading(false))
  }, [user?.user_id])

  const handleModuleClick = async (module) => {
    setSelectedModule(module)
    setIsDetailLoading(true)
    setModuleDetail(null)
    try {
      const res = await fetch(`${API_BASE}/api/v1/training/${module.id}`, {
        headers: { Authorization: `Bearer ${user.token}` },
      })
      if (!res.ok) throw new Error('Failed to fetch detail')
      const detail = await res.json()
      setModuleDetail(detail)
    } catch {
      setModuleDetail({
        title: module.title,
        category: module.category,
        bias_target: module.category,
        estimated_duration: '10 mins',
        content_url: 'https://archive.org/embed/BigBuckBunny_124'
      })
    } finally {
      setIsDetailLoading(false)
    }
  }

  const handleComplete = async () => {
    if (!selectedModule) return
    try {
      const res = await fetch(`${API_BASE}/api/v1/users/${user?.user_id}/training/${selectedModule.id}/complete`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${user.token}` },
      })
      if (!res.ok) throw new Error('Completion failed')
    } catch {
      // silent fail
    }
    setModules(prev => prev.map(m =>
      m.id === selectedModule.id ? { ...m, status: 'complete', progress: 100 } : m
    ))
    setSelectedModule(prev => ({ ...prev, status: 'complete' }))
  }

  const completedCount = modules.filter(m => m.status === 'complete').length
  const totalCount = modules.length
  const overallProgress = totalCount > 0
    ? Math.round((modules.reduce((acc, m) => acc + m.progress, 0) / (totalCount * 100)) * 100)
    : 0

  return (
    <div className="card training-card">
      <div className="card-header border-bottom-light">
        <div>
          <h3 className="card-title">Training Progress</h3>
          <p className="training-subtitle">{completedCount} / {totalCount} done</p>
        </div>
        <div className="training-overall-pct">{overallProgress}%</div>
      </div>

      <div className="training-overall-bar-container">
        <div className="training-bar-bg mb-4">
          <div className="training-bar-fill overall-fill" style={{ width: `${overallProgress}%` }} />
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '24px' }}>
          <div className="loading-spinner" />
        </div>
      ) : error ? (
        <p style={{ padding: '16px', color: 'var(--risk-high)' }}>{error}</p>
      ) : modules.length === 0 ? (
        <p style={{ padding: '16px', color: 'var(--text-muted)' }}>
          No training assigned yet. Modules are assigned automatically after phishing simulations.
        </p>
      ) : (
        <div className="training-list">
          {modules.map(module => (
            <div key={module.id} className={`training-item ${module.status}`} onClick={() => handleModuleClick(module)}>
              <div className="training-icon">
                {module.status === 'complete' && (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-green)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                )}
                {module.status === 'overdue' && (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-orange)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                )}
                {module.status === 'not-started' && (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
                  </svg>
                )}
                {module.status === 'in-progress' && (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" />
                  </svg>
                )}
              </div>

              <div className="training-details">
                <div className="training-details-header">
                  <span className="training-module-title">{module.title}</span>
                  {module.status === 'overdue' ? (
                    <span className="training-date status-overdue">Due {module.dueDate}</span>
                  ) : module.status === 'complete' ? (
                    <span className="training-date status-complete">Completed</span>
                  ) : (
                    <span className="training-date">Due {module.dueDate}</span>
                  )}
                </div>
                <div className="training-category">{module.category}</div>
                <div className="training-module-progress">
                  <div className="training-bar-bg">
                    <div
                      className={`training-bar-fill ${module.status === 'complete' ? 'fill-complete' : 'fill-default'}`}
                      style={{ width: `${module.progress}%` }}
                    />
                  </div>
                  <span className="training-pct">{module.progress}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <button className="risk-level-btn btn-full-width mt-4">
        Browse All Courses
      </button>

      {/* Modal Overlay */}
      {selectedModule && (
        <div className="modal-overlay" onClick={() => setSelectedModule(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-group">
                <h3>{selectedModule.title}</h3>
                <div className="modal-category">{selectedModule.category}</div>
              </div>
              <button className="modal-close-btn" onClick={() => setSelectedModule(null)}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            
            <div className="modal-body">
              {isDetailLoading ? (
                <p style={{textAlign: 'center', color: 'var(--text-muted)'}}>Loading module content...</p>
              ) : moduleDetail ? (
                <>
                  <div className="modal-meta">
                    <span><strong>Bias Target:</strong> {moduleDetail.bias_target}</span>
                    <span><strong>Duration:</strong> {moduleDetail.estimated_duration}</span>
                  </div>
                  
                  <div className="video-container">
                    <iframe 
                      src={moduleDetail.content_url} 
                      title={moduleDetail.title}
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                      allowFullScreen
                    ></iframe>
                  </div>
                </>
              ) : (
                <p style={{textAlign: 'center', color: 'var(--risk-high)'}}>Failed to load module details.</p>
              )}
            </div>

            <div className="modal-footer">
              <button 
                className="btn-primary" 
                onClick={handleComplete} 
                disabled={selectedModule.status === 'complete' || isDetailLoading}
              >
                {selectedModule.status === 'complete' ? 'Completed' : 'Mark as Complete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
