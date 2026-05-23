import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Upload, FileText, Image, Play, Download, Loader2, CheckCircle2, Square, ChevronRight, AlertCircle } from 'lucide-react'
import type { Project, ProjectFile, ProjectImage } from '../types'
import { useToast } from '../components/Toast'

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
        <h1 className="text-3xl font-bold text-slate-800 tracking-tight">{project.name}</h1>
        {project.description && (
          <p className="text-slate-500 text-sm mt-1.5">{project.description}</p>
        )}
      </div>

      {/* Action Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 mb-8 flex flex-wrap items-center gap-3 shadow-sm">
        <label className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium cursor-pointer transition-all ${uploading || isAnalyzing ? 'bg-slate-100 text-slate-400 cursor-not-allowed' : 'bg-slate-100 text-slate-700 hover:bg-slate-200 hover:scale-[1.02] active:scale-[0.98]'}`}>
          <Upload className="w-4 h-4" />
          {uploading ? '上传中...' : isAnalyzing ? '分析中...' : '上传文件'}
          <input type="file" multiple accept=".dxf,.dwg,.pdf,.png,.jpg,.jpeg,.webp" onChange={handleFileUpload} disabled={uploading || isAnalyzing} className="hidden" />
        </label>

        {isAnalyzing ? (
          <button onClick={stopAnalysis} disabled={stopping}
            className="flex items-center gap-2 px-5 py-2.5 bg-red-600 text-white rounded-xl text-sm font-medium hover:bg-red-700 disabled:opacity-40 transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-red-500/20">
            <Square className="w-4 h-4" /> {stopping ? '停止中...' : '停止分析'}
          </button>
        ) : (
          <button onClick={startAnalysis} disabled={!canAnalyze}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl text-sm font-medium hover:from-blue-700 hover:to-blue-600 disabled:opacity-40 transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-blue-500/20">
            <Play className="w-4 h-4" /> 开始分析
          </button>
        )}

        {project.status === 'completed' && (
          <Link to={`/project/${projectId}/analysis`} className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-green-600 to-emerald-500 text-white rounded-xl text-sm font-medium hover:from-green-700 hover:to-emerald-600 no-underline transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-green-500/20">
            <Download className="w-4 h-4" /> 查看报告
          </Link>
        )}
      </div>

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

      {/* Input Text Display */}
      {project.input_text && project.input_text.trim() && (
        <div className="mb-8 bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
            <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-500" />
              补充说明
            </h2>
          </div>
          <div className="p-5">
            <p className="text-sm text-slate-600 whitespace-pre-wrap leading-relaxed">{project.input_text}</p>
          </div>
        </div>
      )}

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
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}