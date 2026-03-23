import ChromeExtensionView from "./components/extension/chromeExtensionView"
import DashboardLayout from "./components/extension/layout/DashboardLayout"
import RiskScoreWidget from "./components/extension/widgets/RiskScoreWidget"

export default function App() {
  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: 'white' }}>
      <div style={{ width: '306px', flexShrink: 0 }}>
        <ChromeExtensionView />
      </div>

      <div style={{ flex: 1, marginLeft: '50px', marginTop: '10px' }}>
        <RiskScoreWidget />
      </div>
    </div>
  )
}