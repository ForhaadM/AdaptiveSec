import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

const inExtension = typeof chrome !== 'undefined' && !!chrome?.storage?.local

function storageGet(keys) {
  return new Promise(resolve => {
    if (inExtension) {
      chrome.storage.local.get(keys, resolve)
    } else {
      const result = {}
      keys.forEach(k => { result[k] = localStorage.getItem(k) })
      resolve(result)
    }
  })
}

function storageSet(obj) {
  if (inExtension) {
    chrome.storage.local.set(obj)
  } else {
    Object.entries(obj).forEach(([k, v]) => localStorage.setItem(k, v))
  }
}

function storageRemove(keys) {
  if (inExtension) {
    chrome.storage.local.remove(keys)
  } else {
    keys.forEach(k => localStorage.removeItem(k))
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    storageGet(['token', 'user_id', 'user_name', 'user_email']).then(result => {
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
    storageSet({
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
    storageRemove(['token', 'user_id', 'user_name', 'user_email'])
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
