import { useState, useEffect } from 'react';

const mockTrainingData = [
  {
    id: 1,
    title: 'Phishing Defense Basics',
    category: 'Core Curriculum',
    progress: 100,
    status: 'complete',
    completionDate: 'Oct 12, 2023',
    dueDate: 'Nov 01, 2023'
  },
  {
    id: 2,
    title: 'Advanced Spear Phishing',
    category: 'Targeted Training',
    progress: 60,
    status: 'in-progress',
    dueDate: 'Nov 15, 2023'
  },
  {
    id: 3,
    title: 'Social Engineering Tactics',
    category: 'Awareness',
    progress: 30,
    status: 'overdue',
    dueDate: 'Oct 20, 2023'
  },
  {
    id: 4,
    title: 'Handling Suspicious Attachments',
    category: 'Practical Drills',
    progress: 0,
    status: 'not-started',
    dueDate: 'Dec 05, 2023'
  }
];

export default function TrainingProgressSection({ userId }) {
  const [data, setData] = useState(mockTrainingData);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (userId) {
      setLoading(true);
      fetch(`/api/v1/users/${userId}/training`)
        .then(res => res.json())
        .then(apiData => {
          const today = new Date();
          const modules = (apiData.modules || []).map(m => {
            let status;
            if (m.completed) {
              status = 'complete';
            } else if (m.progress > 0) {
              status = 'in-progress';
            } else if (m.due_date && new Date(m.due_date) < today) {
              status = 'overdue';
            } else {
              status = 'not-started';
            }
            return {
              id: m.module_id,
              title: m.title,
              category: m.bias_target,
              progress: m.progress,
              status,
              dueDate: m.due_date,
              completionDate: m.due_date,
            };
          });
          setData(modules);
          setLoading(false);
        })
        .catch(err => {
          console.error("Failed to fetch training data", err);
          setData(mockTrainingData);
          setLoading(false);
        });
    }
  }, [userId]);

  const completedCount = data.filter(m => m.status === 'complete').length;
  const totalCount = data.length;
  
  const overallProgress = totalCount > 0 
    ? Math.round((data.reduce((acc, curr) => acc + curr.progress, 0) / (totalCount * 100)) * 100) 
    : 0;

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
            <div 
              className="training-bar-fill overall-fill" 
              style={{ width: `${overallProgress}%` }}
            ></div>
          </div>
      </div>

      {loading ? (
        <p className="training-loading">Loading...</p>
      ) : (
        <div className="training-list">
          {data.map(module => (
            <div key={module.id} className={`training-item ${module.status}`}>
              <div className="training-icon">
                {module.status === 'complete' && (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-green)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                )}
                {module.status === 'overdue' && (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-orange)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                  </svg>
                )}
                {module.status === 'not-started' && (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
                )}
                {module.status === 'in-progress' && (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                    <polyline points="22 4 12 14.01 9 11.01"></polyline>
                  </svg>
                )}
              </div>
              
              <div className="training-details">
                <div className="training-details-header">
                  <span className="training-module-title">{module.title}</span>
                  {module.status === 'complete' ? (
                     <span className="training-date status-complete">Completed on {module.completionDate}</span>
                  ) : module.status === 'overdue' ? (
                     <span className="training-date status-overdue">Due {module.dueDate}</span>
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
                    ></div>
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
    </div>
  );
}
