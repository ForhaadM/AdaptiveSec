import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    chrome.storage.local.get(['token', 'user_id', 'user_name', 'user_email'], (result) => {
      if (result.token && result.user_id) {
        setUser({
          token: result.token,
          user_id: result.user_id,
          name: result.user_name,
          email: result.user_email,
        })
      }
      setLoading(false)
    })
  }, [])

  function login(data) {
    chrome.storage.local.set({
      token: data.access_token,
      user_id: data.user_id,
      user_name: data.name,
      user_email: data.email,
    })
    setUser({
      token: data.access_token,
      user_id: data.user_id,
      name: data.name,
      email: data.email,
    })
  }

  function logout() {
    chrome.storage.local.remove(['token', 'user_id', 'user_name', 'user_email'])
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
