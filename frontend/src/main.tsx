import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

// ─── Demo Mode ──────────────────────────────────────────────────────────
// If VITE_DEMO_MODE=true, intercept all API calls with hardcoded demo data
// so the app is fully functional standalone without a backend.
//
// Cloudflare Pages deployment should set this env var in its build config.
if (
  import.meta.env.VITE_DEMO_MODE === 'true' ||
  import.meta.env.VITE_DEMO_MODE === '1'
) {
  console.log('[RenoPit] Demo mode: API calls will be served from built-in demo data.')
  const { enableMockApi } = await import('./demo/mockApi')
  enableMockApi()
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)