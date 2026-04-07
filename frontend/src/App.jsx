import { AuthProvider, useAuth } from './AuthContext'
import DashboardLayout from './components/DashboardLayout'
import ExtensionPopup from './components/ExtensionPopup'
import LoginPage from './LoginPage'
import './index.css'

const isFullMode = new URLSearchParams(window.location.search).get('full') === '1'

function AppContent() {
  const { user, loading } = useAuth()

  if (loading) return null

  if (!user) return <LoginPage />

  return isFullMode ? <DashboardLayout /> : <ExtensionPopup />
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
