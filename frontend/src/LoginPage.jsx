import { useState } from 'react'
import { useAuth } from './AuthContext'

const BACKEND_URL = 'http://localhost:8000'

export default function LoginPage() {
  const { login } = useAuth()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleGoogleLogin() {
    setError('')
    setLoading(true)
    try {
      const googleToken = await new Promise((resolve, reject) => {
        chrome.identity.getAuthToken({ interactive: true }, (token) => {
          if (chrome.runtime.lastError) {
            reject(chrome.runtime.lastError)
          } else {
            resolve(token)
          }
        })
      })

      const res = await fetch(`${BACKEND_URL}/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: googleToken }),
      })

      if (!res.ok) {
        setError('Sign-in failed. Please try again.')
        return
      }

      const data = await res.json()
      login(data)
    } catch (err) {
      setError(err.message || 'Could not reach the server. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <span className="login-logo-letter">A</span>
        </div>
        <h1 className="login-title">AdaptiveSec</h1>
        <p className="login-subtitle">
          Sign in to monitor your security posture and complete assigned training.
        </p>

        <div className="google-btn-wrapper">
          <button
            onClick={handleGoogleLogin}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              background: '#fff',
              color: '#3c4043',
              border: '1px solid #dadce0',
              borderRadius: '4px',
              padding: '10px 20px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
            }}
          >
            <svg width="18" height="18" viewBox="0 0 48 48">
              <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
              <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
              <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
              <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.31-8.16 2.31-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
              <path fill="none" d="M0 0h48v48H0z"/>
            </svg>
            {loading ? 'Signing in…' : 'Sign in with Google'}
          </button>
        </div>

        {error && <p className="login-error">{error}</p>}
      </div>
    </div>
  )
}
