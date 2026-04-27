import { useState, useEffect } from 'react'
import { useAuth } from '../AuthContext'
import API_BASE from '../apiBase'

const BACKEND = 'http://localhost:8000'

function getYouTubeId(url) {
  if (!url) return null
  const embedMatch = url.match(/youtube\.com\/embed\/([^?&]+)/)
  if (embedMatch) return embedMatch[1]
  const watchMatch = url.match(/[?&]v=([^&]+)/)
  if (watchMatch) return watchMatch[1]
  const shortsMatch = url.match(/shorts\/([^?&]+)/)
  if (shortsMatch) return shortsMatch[1]
  return null
}

function VideoCard({ contentUrl, title }) {
  const videoId = getYouTubeId(contentUrl)
  const thumbnailUrl = videoId ? `https://img.youtube.com/vi/${videoId}/mqdefault.jpg` : null
  const watchUrl = videoId ? `https://www.youtube.com/shorts/${videoId}` : contentUrl

  return (
    <div style={{ borderRadius: 10, overflow: 'hidden', border: '1px solid #1a2540', background: '#0d1625' }}>
      <div style={{ position: 'relative', cursor: 'pointer' }} onClick={() => window.open(watchUrl, '_blank')}>
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={title}
            style={{ width: '100%', display: 'block', aspectRatio: '16/9', objectFit: 'cover' }}
            onError={e => { e.target.style.display = 'none' }}
          />
        ) : (
          <div style={{ width: '100%', aspectRatio: '16/9', background: '#111827', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontSize: 32 }}>🎬</span>
          </div>
        )}
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(0,0,0,0.3)',
        }}>
          <div style={{
            width: 52, height: 52, borderRadius: '50%',
            background: 'rgba(255,255,255,0.9)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="#111827">
              <polygon points="5,3 19,12 5,21" />
            </svg>
          </div>
        </div>
      </div>
      <div style={{ padding: '10px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 11, color: '#475569', fontFamily: 'monospace' }}>
          🎬 Opens in YouTube
        </span>
        <button
          onClick={() => window.open(watchUrl, '_blank')}
          style={{
            padding: '6px 14px', background: '#ef4444',
            border: 'none', borderRadius: 6,
            color: '#fff', fontSize: 12, fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          ▶ Watch
        </button>
      </div>
    </div>
  )
}

export default function TrainingProgressSection({ userId: propUserId, token: propToken, refreshKey, onComplete }) {
  const { user } = useAuth()
  const userId = propUserId || user?.user_id
  const token = propToken || user?.token
  const isAgentView = !!propUserId

  const [modules, setModules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedModule, setSelectedModule] = useState(null)
  const [moduleDetail, setModuleDetail] = useState(null)
  const [isDetailLoading, setIsDetailLoading] = useState(false)

  async function loadModules() {
    if (!userId) return
    setLoading(true)
    try {
      const url = isAgentView
        ? `${BACKEND}/api/v1/admin/agent-training/${userId}`
        : `${API_BASE}/api/v1/users/${userId}/training`
      const headers = isAgentView ? {} : { Authorization: `Bearer ${token}` }
      const res = await fetch(url, { headers })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      const today = new Date()
      const mapped = (json.modules || []).map(m => {
        let status
        if (m.completed) status = 'complete'
        else if (m.progress > 0) status = 'in-progress'
        else if (m.due_date && new Date(m.due_date) < today) status = 'overdue'
        else status = 'not-started'
        return {
          id: m.module_id,
          title: m.title,
          category: m.bias_target,
          progress: m.progress || 0,
          status,
          dueDate: m.due_date,
          videoIndex: m.video_index ?? 0,  // ← from backend
        }
      })
      setModules(mapped)
      setError(null)
    } catch {
      setError('Failed to load training modules.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadModules() }, [userId])
  useEffect(() => { if (refreshKey > 0) loadModules() }, [refreshKey])

  const handleModuleClick = async (module) => {
    setSelectedModule(module)
    setIsDetailLoading(true)
    setModuleDetail(null)
    try {
      const url = isAgentView
        ? `${BACKEND}/api/v1/admin/training/${module.id}`
        : `${API_BASE}/api/v1/training/${module.id}`
      const headers = isAgentView ? {} : { Authorization: `Bearer ${token}` }
      const res = await fetch(url, { headers })
      if (!res.ok) throw new Error('Failed')
      setModuleDetail(await res.json())
    } catch {
      setModuleDetail({ title: module.title, bias_target: module.category, estimated_duration: '3 mins', content_url: null, video_urls: [] })
    } finally {
      setIsDetailLoading(false)
    }
  }

  const handleComplete = async () => {
    if (!selectedModule) return
    if (selectedModule.status === 'complete') return
    try {
      const url = isAgentView
        ? `${BACKEND}/api/v1/admin/agent-training/${userId}/${selectedModule.id}/complete`
        : `${API_BASE}/api/v1/users/${userId}/training/${selectedModule.id}/complete`
      const headers = isAgentView ? {} : { Authorization: `Bearer ${token}` }
      await fetch(url, { method: 'POST', headers })

      setModules(prev => prev.map(m => m.id === selectedModule.id ? { ...m, status: 'complete', progress: 100 } : m))
      setSelectedModule(prev => ({ ...prev, status: 'complete' }))

      await new Promise(r => setTimeout(r, 1000))
      if (onComplete) onComplete()
    } catch { }
  }

  function getVideoForModule(module, detail) {
    if (!detail) return null
    const allUrls = [detail.content_url, ...(detail.video_urls || []).filter(u => u !== detail.content_url)].filter(Boolean)
    const idx = Math.min(module.videoIndex ?? 0, allUrls.length - 1)
    return allUrls[idx] || null
  }

  const completedCount = modules.filter(m => m.status === 'complete').length
  const totalCount = modules.length
  const overallProgress = totalCount > 0 ? Math.round((modules.reduce((acc, m) => acc + m.progress, 0) / (totalCount * 100)) * 100) : 0

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
        <div style={{ display: 'flex', justifyContent: 'center', padding: '24px' }}><div className="loading-spinner" /></div>
      ) : error ? (
        <p style={{ padding: '16px', color: 'var(--risk-high)' }}>{error}</p>
      ) : modules.length === 0 ? (
        <p style={{ padding: '16px', color: 'var(--text-muted)' }}>No training assigned yet. Modules are assigned automatically after phishing simulations.</p>
      ) : (
        <div className="training-list">
          {modules.map(module => (
            <div key={module.id} className={`training-item ${module.status}`} onClick={() => handleModuleClick(module)}>
              <div className="training-icon">
                {module.status === 'complete' && <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-green)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>}
                {module.status === 'overdue' && <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-orange)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>}
                {module.status === 'not-started' && <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>}
                {module.status === 'in-progress' && <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>}
              </div>
              <div className="training-details">
                <div className="training-details-header">
                  <span className="training-module-title">{module.title}</span>
                  {module.status === 'overdue' ? <span className="training-date status-overdue">Due {module.dueDate}</span>
                    : module.status === 'complete' ? <span className="training-date status-complete">Completed</span>
                      : <span className="training-date">Due {module.dueDate}</span>}
                </div>
                <div className="training-category">{module.category}</div>
                <div className="training-module-progress">
                  <div className="training-bar-bg">
                    <div className={`training-bar-fill ${module.status === 'complete' ? 'fill-complete' : 'fill-default'}`} style={{ width: `${module.progress}%` }} />
                  </div>
                  <span className="training-pct">{module.progress}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <button className="risk-level-btn btn-full-width mt-4">Browse All Courses</button>

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
                  <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div className="modal-body">
              {isDetailLoading ? (
                <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>Loading module content...</p>
              ) : moduleDetail ? (
                <>
                  <div className="modal-meta">
                    <span><strong>Bias Target:</strong> {moduleDetail.bias_target}</span>
                  </div>
                  <div style={{ marginTop: 12 }}>
                    {getVideoForModule(selectedModule, moduleDetail) ? (
                      <VideoCard
                        contentUrl={getVideoForModule(selectedModule, moduleDetail)}
                        title={selectedModule.title}
                      />
                    ) : (
                      <p style={{ color: 'var(--text-muted)', textAlign: 'center' }}>No videos available for this module.</p>
                    )}
                  </div>
                </>
              ) : (
                <p style={{ textAlign: 'center', color: 'var(--risk-high)' }}>Failed to load module details.</p>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn-primary" onClick={handleComplete} disabled={selectedModule.status === 'complete' || isDetailLoading}>
                {selectedModule.status === 'complete' ? '✓ Completed' : 'Mark as Complete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}