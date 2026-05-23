import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Upload, FileText, Image, Play, Download, Loader2, CheckCircle2, Square } from 'lucide-react'
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
            // 自动跳转到结果页面
            setTimeout(() => navigate(`/project/${projectId}/analysis`), 800)
          })
          es.addEventListener('failed', (e) => {
            try {
              const msg = JSON.parse(e.data)
              // 优先使用 error_detail (包含完整错误信息), 其次使用 error
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
      // 自动跳转到结果页面
      setTimeout(() => navigate(`/project/${projectId}/analysis`), 800)
    })

    es.addEventListener('failed', (e) => {
      try {
        const msg = JSON.parse(e.data)
        // 优先使用 error_detail (包含完整错误信息), 其次使用 error
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

    es.onerror = () => {
      // EventSource will auto-reconnect; don't set analyzing=false
    }
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
    return <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-slate-400" /></div>
  }
  if (!project) {
    return <div className="max-w-6xl mx-auto px-4 py-8 text-center text-slate-400">找不到此项目</div>
  }

  const totalFiles = files.length + images.length
  const hasInputText = project.input_text && project.input_text.trim().length > 0
  const canAnalyze = (totalFiles > 0 || hasInputText) && !analyzing && project.status !== 'analyzing'
  const isAnalyzing = analyzing || project.status === 'analyzing'

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-3 mb-6">
        <Link to="/" className="text-slate-400 hover:text-slate-600 no-underline"><ArrowLeft className="w-5 h-5" /></Link>
        <div>
          <h1 className="text-2xl font-bold text-slate-800">{project.name}</h1>
          {project.description && <p className="text-slate-500 text-sm mt-0.5">{project.description}</p>}
        </div>
      </div>

      {/* Action Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-6 flex flex-wrap items-center gap-3">
        <label className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium cursor-pointer transition-colors ${uploading || isAnalyzing ? 'bg-slate-100 text-slate-400 cursor-not-allowed' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}>
          <Upload className="w-4 h-4" />
          {uploading ? '上传中...' : isAnalyzing ? '分析中...' : '上传文件'}
          <input type="file" multiple accept=".dxf,.dwg,.pdf,.png,.jpg,.jpeg,.webp" onChange={handleFileUpload} disabled={uploading || isAnalyzing} className="hidden" />
        </label>

        {isAnalyzing ? (
          <button onClick={stopAnalysis} disabled={stopping}
            className="flex items-center gap-2 px-5 py-2.5 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-40 transition-colors">
            <Square className="w-4 h-4" /> {stopping ? '停止中...' : '停止分析'}
          </button>
        ) : (
          <button onClick={startAnalysis} disabled={!canAnalyze}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40 transition-colors">
            <Play className="w-4 h-4" /> 开始分析
          </button>
        )}

        {project.status === 'completed' && (
          <Link to={`/project/${projectId}/analysis`} className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 no-underline">
            <Download className="w-4 h-4" /> 查看报告
          </Link>
        )}
      </div>

      {/* SSE Progress */}
      {isAnalyzing && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl">
          <div className="flex items-center gap-2 text-blue-700 text-sm font-medium mb-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            {sseMessage}
          </div>
          <div className="w-full h-2 bg-blue-200 rounded-full overflow-hidden">
            <div className="h-full bg-blue-600 rounded-full transition-all duration-500" style={{ width: `${sseProgress}%` }} />
          </div>
          <div className="text-right text-xs text-blue-500 mt-1">{sseProgress}%</div>
        </div>
      )}

      {/* Input Text Display (if any) */}
      {project.input_text && project.input_text.trim() && (
        <div className="mb-6 bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
            <h2 className="text-sm font-semibold text-slate-700">补充说明</h2>
          </div>
          <div className="p-4">
            <p className="text-sm text-slate-600 whitespace-pre-wrap">{project.input_text}</p>
          </div>
        </div>
      )}

      {/* File List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
          <h2 className="text-sm font-semibold text-slate-700">已上传文件（{totalFiles}）</h2>
          <p className="text-xs text-slate-400 mt-0.5">支持 DXF、PDF 平面图，以及现场照片</p>
        </div>

        {totalFiles === 0 && !hasInputText ? (
          <div className="p-10 text-center text-slate-400 text-sm">
            尚无文件，请上传设计图、现场照片或填写补充说明
          </div>
        ) : totalFiles === 0 ? (
          <div className="p-10 text-center text-slate-400 text-sm">
            尚无文件，使用文本说明开始分析
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {files.map((f) => (
              <div key={f.id} className="px-5 py-3 flex items-center gap-3 hover:bg-slate-50">
                <FileText className="w-5 h-5 text-blue-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700 truncate">{f.original_name}</p>
                  <p className="text-xs text-slate-400">{formatSize(f.file_size)}{f.file_type ? ` · ${f.file_type.toUpperCase()}` : ''}</p>
                </div>
                {f.parsed_content && <CheckCircle2 className="w-4 h-4 text-green-500" />}
              </div>
            ))}
            {images.map((img) => (
              <div key={img.id} className="px-5 py-3 flex items-center gap-3 hover:bg-slate-50">
                <Image className="w-5 h-5 text-purple-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700 truncate">{img.original_name}</p>
                  <p className="text-xs text-slate-400">{formatSize(img.file_size)}{img.width && img.height ? ` · ${img.width}x${img.height}` : ''}</p>
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