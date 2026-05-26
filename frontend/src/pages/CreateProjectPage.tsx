import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, Loader2, Trash2, FileText, Image as ImageIcon } from 'lucide-react'

const API = '/api'

export default function CreateProjectPage() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [inputText, setInputText] = useState('')
  const [creating, setCreating] = useState(false)

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

      navigate(`/project/${projectId}`)
    } catch (err) { console.error(err) }
    finally { setCreating(false) }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
      <div className="max-w-5xl mx-auto px-6 py-12">
        {/* Header - Clean and editorial */}
        <div className="mb-10">
          <h1 className="text-4xl md:text-5xl font-bold text-slate-800 tracking-tight">
            新建项目
          </h1>
          <div className="mt-3 h-1 w-16 rounded-full bg-gradient-to-r from-blue-500 to-purple-600" />
          <p className="text-slate-500 text-lg mt-4 leading-relaxed">
            上传你的设计图纸、现场照片，或直接描述你的装修需求。AI 会逐项审查，揪出那些不合理的设计和隐藏的陷阱。
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl shadow-slate-200/50 p-8 md:p-10 space-y-7">
          {/* Project Name + Description in one row */}
          <div className="grid md:grid-cols-2 gap-5">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                项目名称 <span className="text-red-400">*</span>
              </label>
              <input
                className="w-full px-5 py-3.5 border border-slate-200 rounded-2xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 bg-slate-50/30 transition-all"
                placeholder="例如：主卧装修方案"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">项目描述</label>
              <input
                className="w-full px-5 py-3.5 border border-slate-200 rounded-2xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 bg-slate-50/30 transition-all"
                placeholder="项目描述"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </div>

          {/* File Upload - Full width */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5">
              上传设计文件
              <span className="text-slate-400 font-normal ml-1">支持图片和文档格式</span>
            </label>
            <label className={`flex flex-col items-center gap-3 px-6 py-8 border-2 border-dashed rounded-2xl cursor-pointer transition-all
              ${selectedFiles.length > 0 ? 'border-blue-300 bg-blue-50/50 text-blue-600' : 'border-slate-200 bg-slate-50/30 text-slate-400 hover:border-slate-300 hover:text-slate-500 hover:bg-slate-50/50'}`}>
              <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center">
                <Upload className="w-6 h-6" />
              </div>
              <div className="text-center">
                <p className="text-sm font-medium">
                  {selectedFiles.length > 0 ? `已选择 ${selectedFiles.length} 个文件` : '点击选择文件或拖拽到此处'}
                </p>
                <p className="text-xs mt-1 text-slate-400">JPG / PNG / WEBP 图片 · PDF / DOCX 文档 · TXT / MD 文本</p>
              </div>
              <input
                type="file"
                multiple
                accept=".pdf,.png,.jpg,.jpeg,.webp,.txt,.docx,.md"
                onChange={handleFileSelect}
                className="hidden"
              />
            </label>

            {selectedFiles.length > 0 && (
              <div className="mt-3 grid gap-1.5 max-h-48 overflow-y-auto">
                {selectedFiles.map((f, i) => (
                  <div key={i} className="flex items-center gap-3 px-4 py-2.5 bg-slate-50 rounded-xl text-sm group">
                    {f.type.startsWith('image/') ? (
                      <ImageIcon className="w-4 h-4 text-purple-500 flex-shrink-0" />
                    ) : (
                      <FileText className="w-4 h-4 text-blue-500 flex-shrink-0" />
                    )}
                    <span className="text-slate-600 truncate flex-1">{f.name}</span>
                    <span className="text-slate-400 text-xs flex-shrink-0">{formatSize(f.size)}</span>
                    <button onClick={() => removeFile(i)} className="text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Input Text */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5">
              补充说明
              <span className="text-slate-400 font-normal ml-1">直接输入你的装修需求或注意事项</span>
            </label>
            <textarea
              className="w-full px-5 py-3.5 border border-slate-200 rounded-2xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 bg-slate-50/30 transition-all resize-none"
              rows={4}
              placeholder="例如：主卧需要独立衣帽间，卫生间要做干湿分离，厨房需要岛台..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              maxLength={2000}
            />
          </div>

          {/* Actions */}
          <div className="flex items-center gap-4 pt-2">
            <button
              onClick={createProject}
              disabled={!canCreate}
              className="px-8 py-3.5 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-2xl text-base font-semibold hover:from-blue-700 hover:to-blue-600 disabled:opacity-40 flex items-center gap-2 transition-all shadow-xl shadow-blue-500/20 hover:shadow-blue-500/30 hover:scale-[1.02] active:scale-[0.98]"
            >
              {creating && <Loader2 className="w-5 h-5 animate-spin" />}
              {creating ? '创建中...' : '创建'}
            </button>
            <button
              onClick={() => navigate('/projects')}
              className="px-6 py-3.5 bg-slate-100 text-slate-600 rounded-2xl text-sm font-medium hover:bg-slate-200 transition-all"
            >
              取消
            </button>
          </div>
        </div>

        {/* Tip */}
        <div className="mt-6 text-center">
          <p className="text-xs text-slate-400">
            上传后 AI 将自动分析设计图纸，检测周期通常为 1-3 分钟
          </p>
        </div>
      </div>
    </div>
  )
}