import { Link, Outlet, useLocation } from 'react-router-dom'
import { FolderOpen, Plus } from 'lucide-react'
import ToastProvider from './Toast'
import DemoBanner from './DemoBanner'

export default function Layout() {
  const location = useLocation()
  const isDemo =
    import.meta.env.VITE_DEMO_MODE === 'true' ||
    import.meta.env.VITE_DEMO_MODE === '1'

  const navLinks = [
    { to: '/projects', label: '项目列表', icon: FolderOpen },
  ]

  const isActivePath = (path: string) => {
    if (path === '/projects') {
      return location.pathname.startsWith('/project') || location.pathname === '/projects'
    }
    return location.pathname === path
  }

  return (
    <ToastProvider>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 flex flex-col">
        <DemoBanner />
        <header className="bg-white/80 backdrop-blur-xl border-b border-slate-200/80 sticky z-50" style={{ top: isDemo ? '42px' : '0' }}>
          <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2.5 no-underline group">
              <img src="/favicon.svg" alt="装闭" className="w-8 h-8 group-hover:scale-105 transition-transform duration-300" />
              <span className="text-lg font-bold tracking-tight text-slate-800">
                装闭
              </span>
            </Link>
            <nav className="flex items-center gap-1">
              {location.pathname !== '/projects/new' && (import.meta.env.VITE_DEMO_MODE !== 'true' && import.meta.env.VITE_DEMO_MODE !== '1') && (
                <Link
                  to="/projects/new"
                  className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl text-sm font-medium hover:from-blue-700 hover:to-blue-600 no-underline transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-blue-500/20 mr-2"
                >
                  <Plus className="w-4 h-4" /> 创建项目
                </Link>
              )}
              {navLinks.map((link) => {
                const isActive = isActivePath(link.to)
                return (
                  <Link
                    key={link.to + link.label}
                    to={link.to}
                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 flex items-center gap-1.5 no-underline
                      ${isActive
                        ? 'bg-blue-50 text-blue-600 shadow-sm'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-800'}`}
                  >
                    <link.icon className="w-4 h-4" />
                    {link.label}
                  </Link>
                )
              })}
            </nav>
          </div>
        </header>

        <main className="flex-1">
          <Outlet />
        </main>

        <footer className="bg-white/80 backdrop-blur-xl border-t border-slate-200/80 py-6">
          <div className="max-w-6xl mx-auto px-4 text-center text-sm text-slate-400">
            装闭 — 站在消费者一边的AI装修闭坑分析器 · Powered by AI · 不做中立审查，只做消费者代言人
          </div>
        </footer>
      </div>
    </ToastProvider>
  )
}
