import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Upload, FileText, Image, Play, Download, Loader2, CheckCircle2 } from 'lucide-react'
import type { Project, ProjectFile, ProjectImage, SSEMessage } from '../types'

const API = '/api'

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const projectId = id ?? ''

  const [project, setProject] = useState<Project | null>(null)
  const [files, setFiles] = useState<ProjectFile[]>([])
  const [images, setImages] = useState<ProjectImage[]>([])
  const [loading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [sseProgress, setSseProgress] = useState(0)
  const [sseMessage, setSseMessage] = useState('')
  const eventSourceRef = useRef<EventSource | null>(null)

  const fetchProject = useCallback(async () => {
    const res = await fetch(`${API}/projects/${projectId}`)
    if (res.ok) setProject(await res.json())
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
    fetchProject()
    fetchFiles()
    fetchImages()
    return () => { eventSourceRef.current?.close() }
  }, [fetchProject, fetchFiles, fetchImages])

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const fileList = e.target.files
    if (!fileList || fileList.length === 0) return
    setUploading(true)
    try {
      const formData = new FormData()
      Array.from(fileList).forEach((f) => formData.append('files', f))
      const res = await fetch(`${API}/projects/${projectId}/upload`, { method: 'POST', body: formData })
      if (res.ok) {
        await Promise.all([fetchFiles(), fetchImages(), fetchProject()])
      }
    } catch (e) { console.error(e) }
    finally { setUploading(false) }
  }

  const startAnalysis = useCallback(() => {
    setAnalyzing(true)
    setSseProgress(0)
    setSseMessage('正在啟動分析...')

    // Close any existing SSE connection
    eventSourceRef.current?.close()

    const es = new EventSource(`${API}/projects/${projectId}/analyze/stream`)
    eventSourceRef.current = es

    es.addEventListener('progress', (e) => {
      const msg: SSEMessage = JSON.parse(e.data)
      setSseProgress(msg.data.progress)
      setSseMessage(msg.data.message)
    })

    es.addEventListener('completed', (e) => {
      JSON.parse(e.data)
      setSseProgress(100)
      setSseMessage('分析完成！')
      setAnalyzing(false)
      es.close()
      fetchProject()
      navigate(`/project/${projectId}/analysis`)
    })

    es.addEventListener('failed', (e) => {
      const msg: SSEMessage = JSON.parse(e.data)
      setSseMessage(msg.data.error || '分析失敗')
      setAnalyzing(false)
      es.close()
      fetchProject()
    })

    es.onerror = () => {
      setSseMessage('連線中斷，正在重試...')
    }
  }, [projectId, navigate])

  if (loading && !project) {
    return <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-slate-400" /></div>
  }
  if (!project) {
    return <div className="max-w-6xl mx-auto px-4 py-8 text-center text-slate-400">找不到此專案</div>
  }

  const totalFiles = files.length + images.length
  const canAnalyze = totalFiles > 0 && !analyzing

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
        <label className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium cursor-pointer transition-colors ${uploading ? 'bg-slate-100 text-slate-400' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}>
          <Upload className="w-4 h-4" />
          {uploading ? '上傳中...' : '上傳檔案'}
          <input type="file" multiple accept=".dxf,.dwg,.pdf,.png,.jpg,.jpeg,.webp" onChange={handleFileUpload} disabled={uploading} className="hidden" />
        </label>

        <button onClick={startAnalysis} disabled={!canAnalyze}
          className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40 transition-colors">
          <Play className="w-4 h-4" /> 開始分析
        </button>

        {project.status === 'completed' && (
          <Link to={`/project/${projectId}/report`} className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 no-underline">
            <Download className="w-4 h-4" /> 檢視報告
          </Link>
        )}
      </div>

      {/* SSE Progress */}
      {analyzing && (
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

      {/* File List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
          <h2 className="text-sm font-semibold text-slate-700">已上傳檔案（{totalFiles}）</h2>
          <p className="text-xs text-slate-400 mt-0.5">支援 DXF、PDF 平面圖，以及現場照片</p>
        </div>

        {totalFiles === 0 ? (
          <div className="p-10 text-center text-slate-400 text-sm">
            尚無檔案，請上傳設計圖或現場照片
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {files.map((f) => (
              <div key={f.id} className="px-5 py-3 flex items-center gap-3 hover:bg-slate-50">
                <FileText className="w-5 h-5 text-blue-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700 truncate">{f.original_name}</p>
                  <p className="text-xs text-slate-400">{formatSize(f.file_size)} · {f.file_type.toUpperCase()}</p>
                </div>
                {f.parsed_content && <CheckCircle2 className="w-4 h-4 text-green-500" />}
              </div>
            ))}
            {images.map((img) => (
              <div key={img.id} className="px-5 py-3 flex items-center gap-3 hover:bg-slate-50">
                <Image className="w-5 h-5 text-purple-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700 truncate">{img.original_name}</p>
                  <p className="text-xs text-slate-400">{formatSize(img.file_size)} · {img.width}x{img.height}</p>
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