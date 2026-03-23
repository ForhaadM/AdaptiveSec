import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'

document.body.style.margin = '0'
document.body.style.padding = '0'
document.body.style.overflow = 'hidden'
document.documentElement.style.margin = '0'
document.documentElement.style.padding = '0'

const root = document.getElementById('root')
root.style.margin = '0'
root.style.padding = '0'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
