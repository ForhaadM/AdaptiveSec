import { AuthProvider, useAuth } from './AuthContext'
import DashboardLayout from './components/DashboardLayout'
import ExtensionPopup from './components/ExtensionPopup'
import AgentSimRunner from './components/AgentSimRunner'
import LoginPage from './LoginPage'
import './index.css'

const inExtension = typeof chrome !== 'undefined' && !!chrome?.runtime?.id
const isFullMode = !inExtension || new URLSearchParams(window.location.search).get('full') === '1'
const isSimMode = new URLSearchParams(window.location.search).get('sim') === '1'

function AppContent() {
  const { user, loading } = useAuth()

  if (loading) return null

  if (!user) return <LoginPage />

  return isFullMode ? <DashboardLayout /> : <ExtensionPopup />
}

function App() {
  // AgentSimRunner runs outside AuthProvider — no auth needed
  if (isSimMode) return <AgentSimRunner />

  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App