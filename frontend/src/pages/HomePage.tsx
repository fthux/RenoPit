import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, FolderOpen, Loader2, Trash2 } from 'lucide-react'
import type { Project } from '../types'

const API = '/api'

export default function HomePage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const navigate = useNavigate()

  const fetchProjects = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/projects`)
      if (res.ok) {
        const data = await res.json()
        setProjects(Array.isArray(data) ? data : data.projects || [])
      }
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { void fetchProjects() }, [fetchProjects])

  async function createProject() {
    if (!name.trim()) return
    setCreating(true)
    try {
      const res = await fetch(`${API}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), description: description.trim() || undefined }),
      })
      if (res.ok) {
        const p = await res.json()
        setShowCreate(false)
        setName('')
        setDescription('')
        navigate(`/project/${p.id}`)
      }
    } catch (err) { console.error(err) }
    finally { setCreating(false) }
  }

  async function deleteProject(id: string) {
    try {
      await fetch(`${API}/projects/${id}`, { method: 'DELETE' })
      setProjects((prev) => prev.filter((p) => p.id !== id))
    } catch (err) { console.error(err) }
  }

  const statusLabel: Record<string, string> = {
    pending: '待處理', parsing: '解析中', analyzing: '分析中', completed: '已完成', failed: '失敗',
  }
  const statusColor: Record<string, string> = {
    pending: 'bg-slate-100 text-slate-500', parsing: 'bg-yellow-100 text-yellow-700',
    analyzing: 'bg-blue-100 text-blue-700', completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">我的專案</h1>
          <p className="text-slate-500 text-sm mt-1">上傳設計檔案，AI 自動分析裝修陷阱</p>
        </div>
        <button onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
          <Plus className="w-4 h-4" /> 新建專案
        </button>
      </div>

      {showCreate && (
        <div className="mb-6 p-5 bg-white rounded-xl border border-slate-200 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-800 mb-3">新建專案</h2>
          <input className="w-full px-3 py-2 border border-slate-300 rounded-lg mb-2 text-sm" placeholder="專案名稱 *" value={name} onChange={(e) => setName(e.target.value)} />
          <input className="w-full px-3 py-2 border border-slate-300 rounded-lg mb-3 text-sm" placeholder="描述（可選）" value={description} onChange={(e) => setDescription(e.target.value)} />
          <div className="flex gap-2">
            <button onClick={createProject} disabled={creating || !name.trim()} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5">
              {creating && <Loader2 className="w-3.5 h-3.5 animate-spin" />} 創建
            </button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 bg-slate-100 text-slate-600 rounded-lg text-sm hover:bg-slate-200">取消</button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-slate-400" /></div>
      ) : projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400">
          <FolderOpen className="w-12 h-12 mb-3" />
          <p className="text-lg">尚無專案</p>
          <p className="text-sm">點擊「新建專案」開始分析你的設計</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {projects.map((p) => (
            <div key={p.id} className="bg-white rounded-xl border border-slate-200 px-5 py-4 flex items-center justify-between hover:shadow-md transition-shadow">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600"><FolderOpen className="w-5 h-5" /></div>
                <div>
                  <Link to={`/project/${p.id}`} className="text-slate-800 font-medium hover:text-blue-600 no-underline">{p.name}</Link>
                  {p.description && <p className="text-slate-400 text-xs mt-0.5">{p.description}</p>}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${statusColor[p.status]}`}>{statusLabel[p.status]}</span>
                <button onClick={() => deleteProject(p.id)} className="p-1.5 text-slate-300 hover:text-red-500 transition-colors"><Trash2 className="w-4 h-4" /></button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}