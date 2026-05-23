import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, FolderOpen, Loader2, Trash2, Upload, FileText, Image as ImageIcon, ArrowRight, Building2 } from 'lucide-react'
import type { Project } from '../types'
import ConfirmDialog from '../components/ConfirmDialog'

const API = '/api'

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [inputText, setInputText] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)
  const navigate = useNavigate()
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchProjects = useCallback(async () => {
    try {
      const res = await fetch(`${API}/projects`)
      if (res.ok) {
        const data = await res.json()
        setProjects(Array.isArray(data) ? data : data.projects || [])
      }
    } catch (err) { console.error(err) }
  }, [])

  useEffect(() => {
    const cancelled = { current: false }
    fetchProjects().finally(() => {
      if (!cancelled.current) setLoading(false)
    })
    return () => { cancelled.current = true }
  }, [])

  // Poll for status updates for analyzing projects
  useEffect(() => {
    const hasAnalyzing = projects.some((p) => p.status === 'analyzing')
    if (!hasAnalyzing) return
    pollRef.current = setInterval(fetchProjects, 3000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [projects, fetchProjects])

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    if (!e.target.files) return
    const newFiles = Array.from(e.target.files)
    setSelectedFiles((prev) => [...prev, ...newFiles])
    e.target.value = ''
  }

  function removeFile(index: number) {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index))
  }

  function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const hasContent = selectedFiles.length > 0 || inputText.trim().length > 0
  const canCreate = name.trim().length > 0 && !creating

  async function createProject() {
    if (!canCreate) return
    setCreating(true)
    try {
      const createRes = await fetch(`${API}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim() || undefined,
          input_text: inputText.trim() || undefined,
        }),
      })
      if (!createRes.ok) {
        console.error('Failed to create project')
        return
      }
      const p = await createRes.json()
      const projectId = p.id

      if (selectedFiles.length > 0) {
        const formData = new FormData()
        selectedFiles.forEach((f) => formData.append('files', f))
        await fetch(`${API}/projects/${projectId}/upload`, {
          method: 'POST',
          body: formData,
        })
      }

      setShowCreate(false)
      setName('')
      setDescription('')
      setSelectedFiles([])
      setInputText('')
      navigate(`/project/${projectId}`)
    } catch (err) { console.error(err) }
    finally { setCreating(false) }
  }

  async function deleteProject(id: string) {
    try {
      await fetch(`${API}/projects/${id}`, { method: 'DELETE' })
      setProjects((prev) => prev.filter((p) => p.id !== id))
      setDeleteConfirm(null)
    } catch (err) { console.error(err) }
  }

  const statusLabel: Record<string, string> = {
    pending: '待处理', parsing: '解析中', analyzing: '分析中', completed: '已完成', failed: '失败',
  }
  const statusColor: Record<string, string> = {
    pending: 'bg-slate-100 text-slate-500', parsing: 'bg-yellow-100 text-yellow-700',
    analyzing: 'bg-blue-100 text-blue-700', completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-800 tracking-tight">我的项目</h1>
            <p className="text-slate-500 text-sm mt-1.5">上传设计文件，AI 自动分析装修陷阱，规避施工风险</p>
          </div>
          <button onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl hover:from-blue-700 hover:to-blue-600 transition-all duration-300 text-sm font-medium shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 hover:scale-[1.02] active:scale-[0.98]">
            <Plus className="w-4 h-4" /> 新建项目
          </button>
        </div>

        {/* Create Form */}
        {showCreate && (
          <div className="mb-8 p-6 bg-white rounded-2xl border border-slate-200 shadow-xl shadow-slate-200/50 space-y-5">
            <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">+</div>
              新建项目
            </h2>

            <div>
              <label className="block text-sm font-medium text-slate-600 mb-1.5">项目名称 *</label>
              <input
                className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 bg-slate-50/50 transition-all"
                placeholder="例如：主卧装修方案"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-600 mb-1.5">描述（可选）</label>
              <input
                className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 bg-slate-50/50 transition-all"
                placeholder="简要描述你的装修需求"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-600 mb-1.5">
                上传文件（可选）
                <span className="text-slate-400 font-normal ml-1">支持图片、DXF、PDF 等设计文件</span>
              </label>
              <label className={`flex items-center gap-2 px-4 py-3.5 border-2 border-dashed rounded-xl cursor-pointer transition-all text-sm
                ${selectedFiles.length > 0 ? 'border-blue-300 bg-blue-50/50 text-blue-600' : 'border-slate-200 bg-slate-50/50 text-slate-400 hover:border-slate-300 hover:text-slate-500'}`}>
                <Upload className="w-4 h-4" />
                {selectedFiles.length > 0 ? `已选择 ${selectedFiles.length} 个文件` : '点击选择文件'}
                <input
                  type="file"
                  multiple
                  accept=".dxf,.dwg,.pdf,.png,.jpg,.jpeg,.webp,.txt,.docx,.md"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>

              {selectedFiles.length > 0 && (
                <div className="mt-2 space-y-1 max-h-32 overflow-y-auto">
                  {selectedFiles.map((f, i) => (
                    <div key={i} className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 rounded-lg text-sm">
                      {f.type.startsWith('image/') ? (
                        <ImageIcon className="w-3.5 h-3.5 text-purple-500 flex-shrink-0" />
                      ) : (
                        <FileText className="w-3.5 h-3.5 text-blue-500 flex-shrink-0" />
                      )}
                      <span className="text-slate-600 truncate flex-1">{f.name}</span>
                      <span className="text-slate-400 text-xs flex-shrink-0">{formatSize(f.size)}</span>
                      <button onClick={() => removeFile(i)} className="text-slate-300 hover:text-red-500 flex-shrink-0">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-600 mb-1.5">
                补充文本说明（可选）
                <span className="text-slate-400 font-normal ml-1">直接输入装修需求或注意事项</span>
              </label>
              <textarea
                className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 bg-slate-50/50 transition-all resize-none"
                rows={3}
                placeholder="例如：主卧需要独立衣帽间，卫生间要做干湿分离，厨房需要岛台..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                maxLength={2000}
              />
              <div className="text-right text-xs text-slate-400 mt-1">{inputText.length} / 2000</div>
            </div>

            <div className="flex gap-3 pt-1">
              <button
                onClick={createProject}
                disabled={!canCreate}
                className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl text-sm font-medium hover:from-blue-700 hover:to-blue-600 disabled:opacity-50 flex items-center gap-1.5 transition-all shadow-lg shadow-blue-500/20"
              >
                {creating && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                创建项目
              </button>
              <button onClick={() => {
                setShowCreate(false)
                setSelectedFiles([])
                setInputText('')
              }} className="px-5 py-2.5 bg-slate-100 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-200 transition-all">
                取消
              </button>
              {!hasContent && name.trim() && (
                <span className="text-xs text-amber-600 self-center ml-2">提示：建议上传文件或输入文本描述以获得更准确的分析</span>
              )}
            </div>
          </div>
        )}

        {/* Project List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-slate-300" />
          </div>
        ) : projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400">
            <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
              <Building2 className="w-8 h-8 text-slate-300" />
            </div>
            <p className="text-lg font-medium text-slate-500">尚无项目</p>
            <p className="text-sm text-slate-400 mt-1">点击"新建项目"开始分析你的设计</p>
          </div>
        ) : (
          <div className="grid gap-3">
            {projects.map((p) => (
              <div key={p.id}>
                <div
                  className="group bg-white rounded-2xl border border-slate-200 px-6 py-5 flex items-center justify-between hover:shadow-lg hover:shadow-slate-200/50 transition-all duration-300 cursor-pointer hover:border-blue-200/50"
                  onClick={() => navigate(`/project/${p.id}`)}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center text-blue-600 group-hover:scale-110 transition-transform duration-300">
                      <FolderOpen className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-slate-800 font-semibold group-hover:text-blue-600 transition-colors">{p.name}</p>
                      {p.description && <p className="text-slate-400 text-sm mt-0.5">{p.description}</p>}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusColor[p.status]}`}>
                      {statusLabel[p.status] || p.status}
                      {p.status === 'analyzing' && <Loader2 className="w-3 h-3 animate-spin inline ml-1" />}
                    </span>
                    <button
                      onClick={(e) => { e.stopPropagation(); setDeleteConfirm(p.id) }}
                      className="p-2 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-blue-400 group-hover:translate-x-1 transition-all" />
                  </div>
                </div>

                <ConfirmDialog
                  open={deleteConfirm === p.id}
                  title="确认删除"
                  message={`确定要删除项目「${p.name}」吗？此操作不可撤销。`}
                  confirmLabel="删除"
                  onConfirm={() => deleteProject(p.id)}
                  onCancel={() => setDeleteConfirm(null)}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}