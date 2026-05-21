import { Link, Outlet, useLocation } from 'react-router-dom'
import { Home, FolderOpen } from 'lucide-react'

export default function Layout() {
  const location = useLocation()

  const navLinks = [
    { to: '/', label: '首頁', icon: Home },
    { to: '/', label: '所有專案', icon: FolderOpen },
  ]

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-lg font-bold text-slate-800 no-underline">
            <span className="text-blue-600">🏗️</span>
            裝修避坑分析器
          </Link>
          <nav className="flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.to + link.label}
                to={link.to}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 no-underline
                  ${location.pathname === link.to ? 'bg-blue-50 text-blue-600' : 'text-slate-600 hover:bg-slate-100'}`}
              >
                <link.icon className="w-4 h-4" />
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="bg-white border-t border-slate-200 py-4">
        <div className="max-w-6xl mx-auto px-4 text-center text-sm text-slate-400">
          裝修避坑分析器 — Powered by AI · 僅供參考，最終以專業設計師意見為準
        </div>
      </footer>
    </div>
  )
}