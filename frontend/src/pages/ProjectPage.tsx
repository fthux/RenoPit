import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Upload, FileText, Image, Play, Loader2, CheckCircle2, Square, ChevronRight, AlertCircle, Pencil, Check, X, FileSearch, RefreshCw, Download, Eye, Trash2 } from 'lucide-react'
import type { Project, ProjectFile, ProjectImage } from '../types'
import { useToast } from '../components/Toast'
import ConfirmDialog from '../components/ConfirmDialog'

const API = '/api'

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>()
  const projectId = id ?? ''
  const navigate = useNavigate()
  const { showToast } = useToast()

  const [project, setProject] = useState<Project | null>(null)
  const [files, setFiles] = useState<ProjectFile[]>([])
  const [images, setImages] = useState<ProjectImage[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [stopping, setStopping] = useState(false)
  const [sseProgress, setSseProgress] = useState(0)
  const [sseMessage, setSseMessage] = useState('')
  const eventSourceRef = useRef<EventSource | null>(null)

  // Inline editing state
  const [editingField, setEditingField] = useState<'name' | 'description' | 'input_text' | null>(null)
  const [editValue, setEditValue] = useState('')
  const [saving, setSaving] = useState(false)

  // Re-analysis confirmation
  const [showReanalyzeConfirm, setShowReanalyzeConfirm] = useState(false)

  // Preview state
  const [previewImage, setPreviewImage] = useState<ProjectImage | null>(null)
  const [previewFileContent, setPreviewFileContent] = useState<{ name: string; content: string } | null>(null)

  const fetchProject = useCallback(async () => {
    const res = await fetch(`${API}/projects/${projectId}`)
    if (res.ok) {
      return await res.json()
    }
    return null
  }, [projectId])

  const fetchFiles = useCallback(async () => {
    const res = await fetch(`${API}/projects/${projectId}/files`)
    if (res.ok) setFiles(await res.json())
  }, [projectId])

  const fetchImages = useCallback(async () => {
    const res = await fetch(`${API}/projects/${projectId}/images`)
    if (res.ok) setImages(await res.json())
  }, [projectId])

  useEffect(() => {
    let cancelled = false
    let es: EventSource | null = null

    const loadAll = async () => {
      const p = await fetchProject()
      if (cancelled) return
      if (p) {
        setProject(p)
        if (p.status === 'analyzing') {
          es = new EventSource(`${API}/projects/${projectId}/analyze/stream`)
          eventSourceRef.current = es
          setAnalyzing(true)
          setSseProgress(5)
          setSseMessage('已连接，等待分析完成...')

          es.addEventListener('progress', (e) => {
            try {
              const msg = JSON.parse(e.data)
              setSseProgress(msg.progress)
              setSseMessage(msg.message)
            } catch { /* ignore */ }
          })
          es.addEventListener('completed', () => {
            setSseProgress(100)
            setSseMessage('分析完成！')
            setAnalyzing(false)
            es?.close()
            fetchProject().then(p => p && setProject(p))
            showToast('success', '分析完成！正在跳转报告...')
            setTimeout(() => navigate(`/project/${projectId}/analysis`), 800)
          })
          es.addEventListener('failed', (e) => {
            try {
              const msg = JSON.parse(e.data)
              const errorMsg = msg.error_detail || msg.error || '分析失败'
              setSseMessage(errorMsg)
              showToast('error', errorMsg)
            } catch {
              setSseMessage('分析失败')
              showToast('error', '分析失败，请重试')
            }
            setAnalyzing(false)
            es?.close()
            fetchProject().then(p => p && setProject(p))
          })
          es.addEventListener('stopped', () => {
            setSseMessage('分析已停止')
            setAnalyzing(false)
            es?.close()
            fetchProject().then(p => p && setProject(p))
            showToast('info', '分析已停止')
          })
          es.onerror = () => { }
        }
      }

      const [filesRes, imagesRes] = await Promise.all([
        fetch(`${API}/projects/${projectId}/files`),
        fetch(`${API}/projects/${projectId}/images`),
      ])
      if (cancelled) return
      if (filesRes.ok) setFiles(await filesRes.json())
      if (imagesRes.ok) setImages(await imagesRes.json())
      setLoading(false)
    }

    loadAll()
    return () => {
      cancelled = true
      es?.close()
      eventSourceRef.current?.close()
    }
  }, [projectId])

  function startSSE() {
    setAnalyzing(true)
    setSseProgress(5)
    setSseMessage('正在连接...')

    eventSourceRef.current?.close()

    const es = new EventSource(`${API}/projects/${projectId}/analyze/stream`)
    eventSourceRef.current = es

    es.addEventListener('progress', (e) => {
      try {
        const msg = JSON.parse(e.data)
        setSseProgress(msg.progress)
        setSseMessage(msg.message)
      } catch { /* ignore */ }
    })

    es.addEventListener('completed', () => {
      setSseProgress(100)
      setSseMessage('分析完成！')
      setAnalyzing(false)
      es.close()
      fetchProject().then(p => p && setProject(p))
      showToast('success', '分析完成！正在跳转报告...')
      setTimeout(() => navigate(`/project/${projectId}/analysis`), 800)
    })

    es.addEventListener('failed', (e) => {
      try {
        const msg = JSON.parse(e.data)
        const errorMsg = msg.error_detail || msg.error || '分析失败'
        setSseMessage(errorMsg)
        showToast('error', errorMsg)
      } catch {
        setSseMessage('分析失败')
        showToast('error', '分析失败，请重试')
      }
      setAnalyzing(false)
      es.close()
      fetchProject().then(p => p && setProject(p))
    })

    es.addEventListener('stopped', () => {
      setSseMessage('分析已停止')
      setAnalyzing(false)
      es.close()
      fetchProject().then(p => p && setProject(p))
      showToast('info', '分析已停止')
    })

    es.onerror = () => { }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const fileList = e.target.files
    if (!fileList || fileList.length === 0) return
    setUploading(true)
    try {
      const formData = new FormData()
      Array.from(fileList).forEach((f) => formData.append('files', f))
      const res = await fetch(`${API}/projects/${projectId}/upload`, { method: 'POST', body: formData })
      if (res.ok) {
        const data = await res.json()
        showToast('success', `上传成功（${(data.files || 0) + (data.images || 0)} 个文件）`)
        await Promise.all([fetchFiles(), fetchImages()])
        const p = await fetchProject()
        if (p) setProject(p)
      } else {
        showToast('error', '上传失败，请检查文件格式')
      }
    } catch {
      showToast('error', '上传失败，请重试')
    }
    finally { setUploading(false); e.target.value = '' }
  }

  const startAnalysis = useCallback(async () => {
    try {
      const res = await fetch(`${API}/projects/${projectId}/analyze`, { method: 'POST' })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: '无法启动分析' }))
        showToast('error', err.detail || '无法启动分析')
        return
      }
      showToast('info', '分析已启动，请稍候...')
      const p = await fetchProject()
      if (p) setProject(p)
      startSSE()
    } catch {
      showToast('error', '启动分析失败，请重试')
    }
  }, [projectId])

  async function stopAnalysis() {
    setStopping(true)
    try {
      const res = await fetch(`${API}/projects/${projectId}/stop`, { method: 'POST' })
      if (res.ok) {
        showToast('info', '正在停止分析...')
      } else {
        const err = await res.json().catch(() => ({ detail: '无法停止' }))
        showToast('warning', err.detail || '无法停止分析')
        setStopping(false)
      }
    } catch {
      showToast('error', '停止分析失败')
      setStopping(false)
    }
  }

  function startEditing(field: 'name' | 'description' | 'input_text', currentValue: string) {
    setEditingField(field)
    setEditValue(currentValue)
  }

  async function deleteFile(fileId: string) {
    try {
      const res = await fetch(`${API}/projects/${projectId}/files/${fileId}`, { method: 'DELETE' })
      if (res.ok) {
        showToast('success', '文件已删除')
        await Promise.all([fetchFiles(), fetchProject().then(p => p && setProject(p))])
      } else {
        showToast('error', '删除失败')
      }
    } catch {
      showToast('error', '删除失败，请重试')
    }
  }

  async function deleteImage(imageId: string) {
    try {
      const res = await fetch(`${API}/projects/${projectId}/images/${imageId}`, { method: 'DELETE' })
      if (res.ok) {
        showToast('success', '图片已删除')
        await Promise.all([fetchImages(), fetchProject().then(p => p && setProject(p))])
      } else {
        showToast('error', '删除失败')
      }
    } catch {
      showToast('error', '删除失败，请重试')
    }
  }

  function cancelEditing() {
    setEditingField(null)
    setEditValue('')
  }

  async function saveEditing() {
    if (!editingField || !project) return

    // 标题不能为空
    if (editingField === 'name' && !editValue.trim()) {
      showToast('error', '标题不能为空')
      return
    }

    setSaving(true)
    try {
      const body: Record<string, string> = {}
      body[editingField] = editValue
      const res = await fetch(`${API}/projects/${projectId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (res.ok) {
        const updated = await res.json()
        setProject(updated)
        showToast('success', editingField === 'name' ? '标题已更新' : editingField === 'description' ? '描述已更新' : '补充说明已更新')
        setEditingField(null)
        setEditValue('')
      } else {
        const err = await res.json().catch(() => ({ detail: '保存失败' }))
        showToast('error', err.detail || '保存失败')
      }
    } catch {
      showToast('error', '保存失败，请重试')
    } finally {
      setSaving(false)
    }
  }

  if (loading && !project) {
    return <div className="flex items-center justify-center min-h-[70vh]"><Loader2 className="w-8 h-8 animate-spin text-slate-300" /></div>
  }
  if (!project) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex flex-col items-center justify-center min-h-[50vh] text-slate-400">
          <AlertCircle className="w-12 h-12 mb-3 text-slate-300" />
          <p className="text-lg font-medium text-slate-500">找不到此项目</p>
        </div>
      </div>
    )
  }

  const totalFiles = files.length + images.length
  const hasInputText = project.input_text && project.input_text.trim().length > 0
  const canAnalyze = (totalFiles > 0 || hasInputText) && !analyzing && project.status !== 'analyzing'
  const isAnalyzing = analyzing || project.status === 'analyzing'

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 mb-8">
        <Link to="/projects" className="text-slate-400 hover:text-slate-600 no-underline flex items-center gap-1 text-sm transition-colors">
          <ArrowLeft className="w-4 h-4" />
          项目列表
        </Link>
        <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
        <span className="text-sm text-slate-600 font-medium">{project.name}</span>
      </div>

      {/* Project Header */}
      <div className="mb-8">
        {/* Title */}
        {editingField === 'name' ? (
          <div className="flex items-center gap-2 mb-1">
            <input
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') saveEditing(); if (e.key === 'Escape') cancelEditing() }}
              className="text-3xl font-bold text-slate-800 bg-white border-2 border-blue-400 rounded-xl px-3 py-1.5 outline-none focus:border-blue-500 w-full max-w-xl"
              autoFocus
              disabled={saving}
              maxLength={255}
            />
            <button onClick={saveEditing} disabled={saving} className="p-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors disabled:opacity-50" title="保存">
              <Check className="w-4 h-4" />
            </button>
            <button onClick={cancelEditing} disabled={saving} className="p-2 rounded-lg bg-slate-100 text-slate-500 hover:bg-slate-200 transition-colors disabled:opacity-50" title="取消">
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <h1
            className="text-3xl font-bold text-slate-800 tracking-tight group flex items-center gap-2 cursor-pointer hover:text-blue-600 transition-colors"
            onClick={() => startEditing('name', project.name)}
            title="点击编辑标题"
          >
            {project.name}
            <Pencil className="w-4 h-4 text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity" />
          </h1>
        )}

        {/* Description */}
        {editingField === 'description' ? (
          <div className="flex items-center gap-2 mt-2">
            <textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={(e) => { if ((e.key === 'Enter' && e.metaKey) || (e.key === 'Enter' && e.ctrlKey)) saveEditing(); if (e.key === 'Escape') cancelEditing() }}
              className="text-sm text-slate-500 bg-white border-2 border-blue-400 rounded-xl px-3 py-2 outline-none focus:border-blue-500 w-full max-w-xl resize-none"
              rows={2}
              autoFocus
              disabled={saving}
              maxLength={300}
              placeholder="项目描述（选填，最多300字）"
            />
            <div className="flex items-center gap-1">
              <button onClick={saveEditing} disabled={saving} className="p-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors disabled:opacity-50" title="保存">
                <Check className="w-4 h-4" />
              </button>
              <button onClick={cancelEditing} disabled={saving} className="p-2 rounded-lg bg-slate-100 text-slate-500 hover:bg-slate-200 transition-colors disabled:opacity-50" title="取消">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          <p
            className="text-slate-500 text-sm mt-1.5 group flex items-center gap-1 cursor-pointer hover:text-blue-500 transition-colors min-h-[1.25rem]"
            onClick={() => startEditing('description', project.description || '')}
            title="点击编辑描述"
          >
            {project.description || (
              <span className="text-slate-300 italic group-hover:text-blue-400">添加描述...</span>
            )}
            <Pencil className="w-3.5 h-3.5 text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity" />
          </p>
        )}
      </div>

      {/* Action Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 mb-8 flex flex-wrap items-center gap-3 shadow-sm">
        <label className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium cursor-pointer transition-all ${uploading || isAnalyzing ? 'bg-slate-100 text-slate-400 cursor-not-allowed' : 'bg-slate-100 text-slate-700 hover:bg-slate-200 hover:scale-[1.02] active:scale-[0.98]'}`}>
          <Upload className="w-4 h-4" />
          {uploading ? '上传中...' : isAnalyzing ? '分析中...' : '上传文件'}
          <input type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.webp,.txt,.docx,.md" onChange={handleFileUpload} disabled={uploading || isAnalyzing} className="hidden" />
        </label>

        {isAnalyzing ? (
          <button onClick={stopAnalysis} disabled={stopping}
            className="flex items-center gap-2 px-5 py-2.5 bg-red-600 text-white rounded-xl text-sm font-medium hover:bg-red-700 disabled:opacity-40 transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-red-500/20">
            <Square className="w-4 h-4" /> {stopping ? '停止中...' : '停止分析'}
          </button>
        ) : (
          <button
            onClick={() => {
              if (project?.status === 'completed') {
                setShowReanalyzeConfirm(true)
              } else {
                startAnalysis()
              }
            }}
            disabled={!canAnalyze}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl text-sm font-medium hover:from-blue-700 hover:to-blue-600 disabled:opacity-40 transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-blue-500/20"
          >
            {project?.status === 'completed' ? (
              <><RefreshCw className="w-4 h-4" /> 重新分析</>
            ) : (
              <><Play className="w-4 h-4" /> 开始分析</>
            )}
          </button>
        )}

        {project.status === 'completed' && (
          <Link to={`/project/${projectId}/analysis`} className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-green-600 to-emerald-500 text-white rounded-xl text-sm font-medium hover:from-green-700 hover:to-emerald-600 no-underline transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-green-500/20">
            <FileSearch className="w-4 h-4" /> 查看报告
          </Link>
        )}
      </div>

      {/* Re-analysis Confirm Dialog */}
      <ConfirmDialog
        open={showReanalyzeConfirm}
        title="确认重新分析"
        message="即将对当前项目重新执行分析，之前的分析报告将会被覆盖。确定要继续吗？"
        confirmLabel="重新分析"
        onConfirm={() => {
          setShowReanalyzeConfirm(false)
          startAnalysis()
        }}
        onCancel={() => setShowReanalyzeConfirm(false)}
      />

      {/* SSE Progress */}
      {isAnalyzing && (
        <div className="mb-8 p-5 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200/50 rounded-2xl">
          <div className="flex items-center gap-2 text-blue-700 text-sm font-medium mb-3">
            <Loader2 className="w-4 h-4 animate-spin" />
            {sseMessage}
          </div>
          <div className="w-full h-2.5 bg-blue-200/60 rounded-full overflow-hidden shadow-inner">
            <div className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-500 shadow-lg shadow-blue-500/20" style={{ width: `${sseProgress}%` }} />
          </div>
          <div className="flex justify-between items-center mt-2">
            <span className="text-xs text-blue-500 font-medium">{sseProgress}%</span>
            <span className="text-xs text-blue-400">{sseMessage}</span>
          </div>
        </div>
      )}

      {/* Input Text Section */}
      <div className="mb-8 bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-500" />
            补充说明
          </h2>
        </div>
        <div className="p-5">
          {editingField === 'input_text' ? (
            <div className="flex items-start gap-2">
              <textarea
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onKeyDown={(e) => { if ((e.key === 'Enter' && e.metaKey) || (e.key === 'Enter' && e.ctrlKey)) saveEditing(); if (e.key === 'Escape') cancelEditing() }}
                className="text-sm text-slate-600 bg-white border-2 border-blue-400 rounded-xl px-3 py-2 outline-none focus:border-blue-500 w-full resize-none"
                rows={6}
                autoFocus
                disabled={saving}
                maxLength={5000}
                placeholder="任何你需要补充的都可以写在这里（最多5000字）"
              />
              <div className="flex items-center gap-1">
                <button onClick={saveEditing} disabled={saving} className="p-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors disabled:opacity-50" title="保存">
                  <Check className="w-4 h-4" />
                </button>
                <button onClick={cancelEditing} disabled={saving} className="p-2 rounded-lg bg-slate-100 text-slate-500 hover:bg-slate-200 transition-colors disabled:opacity-50" title="取消">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : project.input_text && project.input_text.trim() ? (
            <p
              className="text-sm text-slate-600 whitespace-pre-wrap leading-relaxed group cursor-pointer hover:text-blue-500 transition-colors"
              onClick={() => startEditing('input_text', project.input_text || '')}
              title="点击编辑补充说明"
            >
              {project.input_text}
              <Pencil className="w-3.5 h-3.5 inline-block ml-2 text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity" />
            </p>
          ) : (
            <p
              className="text-sm text-slate-300 italic group flex items-center gap-1 cursor-pointer hover:text-blue-400 transition-colors"
              onClick={() => startEditing('input_text', '')}
              title="点击添加补充说明"
            >
              添加补充说明...
              <Pencil className="w-3.5 h-3.5 text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity" />
            </p>
          )}
        </div>
      </div>

      {/* File List */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
          <h2 className="text-sm font-semibold text-slate-700">已上传文件（{totalFiles}）</h2>
          <p className="text-xs text-slate-400 mt-0.5">支持 DXF、PDF 平面图，以及现场照片</p>
        </div>

        {totalFiles === 0 && !hasInputText ? (
          <div className="p-12 text-center">
            <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-3">
              <Upload className="w-7 h-7 text-slate-300" />
            </div>
            <p className="text-slate-500 font-medium">尚无文件</p>
            <p className="text-sm text-slate-400 mt-1">请上传设计图、现场照片或填写补充说明</p>
          </div>
        ) : totalFiles === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            <p>尚无文件，使用文本说明开始分析</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {files.map((f) => (
              <div key={f.id} className="px-6 py-4 flex items-center gap-3 hover:bg-slate-50/50 transition-colors">
                <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
                  <FileText className="w-5 h-5 text-blue-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700 font-medium truncate">{f.original_name}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{formatSize(f.file_size)}{f.file_type ? ` · ${f.file_type.toUpperCase()}` : ''}</p>
                </div>
                {f.parsed_content && <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />}
                <div className="flex items-center gap-1 flex-shrink-0">
                  {(f.file_type === 'txt' || f.file_type === 'md') && (
                    <button
                      onClick={async () => {
                        try {
                          const res = await fetch(`${API}/projects/${projectId}/files/${f.id}`)
                          if (res.ok) {
                            const text = await res.text()
                            setPreviewFileContent({ name: f.original_name, content: text })
                          }
                        } catch { /* ignore */ }
                      }}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                      title="预览内容"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  )}
                  <a
                    href={`${API}/projects/${projectId}/files/${f.id}`}
                    download
                    className="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                    title="下载文件"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                  <button
                    onClick={() => deleteFile(f.id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                    title="删除文件"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
            {images.map((img) => (
              <div key={img.id} className="px-6 py-4 flex items-center gap-3 hover:bg-slate-50/50 transition-colors">
                <div className="w-9 h-9 rounded-lg bg-purple-50 flex items-center justify-center flex-shrink-0">
                  <Image className="w-5 h-5 text-purple-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700 font-medium truncate">{img.original_name}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{formatSize(img.file_size)}{img.width && img.height ? ` · ${img.width}x${img.height}` : ''}</p>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    onClick={() => setPreviewImage(img)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-purple-600 hover:bg-purple-50 transition-colors"
                    title="预览图片"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  <a
                    href={`${API}/projects/${projectId}/images/${img.id}`}
                    download
                    className="p-1.5 rounded-lg text-slate-400 hover:text-purple-600 hover:bg-purple-50 transition-colors"
                    title="下载图片"
                  >
                    <Download className="w-4 h-4" />
                  </a>
                  <button
                    onClick={() => deleteImage(img.id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                    title="删除图片"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Document Risk Analysis Panel */}

      {/* Image Preview Modal */}
      {previewImage && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={() => setPreviewImage(null)}>
          <div className="relative max-w-[90vw] max-h-[90vh]" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => setPreviewImage(null)}
              className="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-white shadow-lg flex items-center justify-center text-slate-500 hover:text-slate-700 transition-colors z-10"
            >
              <X className="w-4 h-4" />
            </button>
            <img
              src={`${API}/projects/${projectId}/images/${previewImage.id}`}
              alt={previewImage.original_name}
              className="max-w-[90vw] max-h-[85vh] rounded-xl shadow-2xl object-contain"
            />
            <p className="text-white text-sm text-center mt-3 font-medium">{previewImage.original_name}</p>
          </div>
        </div>
      )}

      {/* Text Preview Modal */}
      {previewFileContent && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={() => setPreviewFileContent(null)}>
          <div
            className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100">
              <h3 className="text-sm font-semibold text-slate-700 truncate">{previewFileContent.name}</h3>
              <button
                onClick={() => setPreviewFileContent(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-5 overflow-auto flex-1">
              <pre className="text-sm text-slate-700 whitespace-pre-wrap font-mono leading-relaxed">{previewFileContent.content}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}