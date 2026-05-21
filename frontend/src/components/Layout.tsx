import { Link, Outlet, useLocation } from 'react-router-dom'
import { FolderOpen } from 'lucide-react'
import ToastProvider from './Toast'

export default function Layout() {
  const location = useLocation()

  const navLinks = [
    { to: '/', label: '所有项目', icon: FolderOpen },
  ]

  return (
    <ToastProvider>
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
          <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2 text-lg font-bold text-slate-800 no-underline">
              <span className="text-blue-600">🏗️</span>
              装修避坑分析器
            </Link>
            <nav className="flex items-center gap-1">
              {navLinks.map((link) => {
                const isActive = link.label === '所有项目'
                  ? location.pathname === '/' || location.pathname === link.to
                  : location.pathname === link.to || location.pathname.startsWith(link.to + '/')
                return (
                  <Link
                    key={link.to + link.label}
                    to={link.to}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 no-underline
                  ${isActive ? 'bg-blue-50 text-blue-600' : 'text-slate-600 hover:bg-slate-100'}`}
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

        <footer className="bg-white border-t border-slate-200 py-4">
          <div className="max-w-6xl mx-auto px-4 text-center text-sm text-slate-400">
            装修避坑分析器 — Powered by AI · 仅供参考，最终以专业设计师意见为准
          </div>
        </footer>
      </div>
    </ToastProvider>
  )
}
