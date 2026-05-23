import { Link, Outlet, useLocation } from 'react-router-dom'
import { FolderOpen } from 'lucide-react'
import ToastProvider from './Toast'

export default function Layout() {
  const location = useLocation()

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
        <header className="bg-white/80 backdrop-blur-xl border-b border-slate-200/80 sticky top-0 z-50">
          <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2.5 no-underline group">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform duration-300">
                装
              </div>
              <span className="text-lg font-bold tracking-tight text-slate-800">
                装<span className="text-blue-500">闭</span>
              </span>
            </Link>
            <nav className="flex items-center gap-1">
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
            装闭 — 装修闭坑利器 · Powered by AI · 仅供参考，最终以专业设计师意见为准
          </div>
        </footer>
      </div>
    </ToastProvider>
  )
}
