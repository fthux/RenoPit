import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, FolderOpen, Loader2, Trash2, Copy, Clock, CheckCircle2, AlertCircle, FileText, Image, FileWarning, ChevronLeft, ChevronRight, Ellipsis } from 'lucide-react'
import type { Project } from '../types'
import ConfirmDialog from '../components/ConfirmDialog'

const API = '/api'
const PAGE_SIZE = 8

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const navigate = useNavigate()
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchProjects = useCallback(async (p: number) => {
    try {
      const res = await fetch(`${API}/projects?page=${p}&page_size=${PAGE_SIZE}`)
      if (res.ok) {
        const data = await res.json()
        setProjects(data.projects || [])
        setTotal(data.total || 0)
        setTotalPages(data.total_pages || 1)
      }
    } catch (err) { console.error(err) }
  }, [])

  useEffect(() => {
    const cancelled = { current: false }
    fetchProjects(page).finally(() => {
      if (!cancelled.current) setLoading(false)
    })
    return () => { cancelled.current = true }
  }, [page])

  // Poll for status updates for analyzing projects
  useEffect(() => {
    const hasAnalyzing = projects.some((p) => p.status === 'analyzing')
    if (!hasAnalyzing) return
    pollRef.current = setInterval(() => fetchProjects(page), 3000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [projects, fetchProjects, page])

  function goToPage(p: number) {
    if (p < 1 || p > totalPages || p === page) return
    setPage(p)
    setLoading(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  /** 生成带截断符的页码数组：首尾 + 当前页前后各1页，其余用 "..." 表示 */
  function getPageNumbers(): (number | string)[] {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1)
    }

    const pages: (number | string)[] = [1]

    if (page > 3) {
      pages.push('...')
    }

    // 当前页前后各1页
    const start = Math.max(2, page - 1)
    const end = Math.min(totalPages - 1, page + 1)
    for (let i = start; i <= end; i++) {
      pages.push(i)
    }

    if (page < totalPages - 2) {
      pages.push('...')
    }

    pages.push(totalPages)

    return pages
  }

  async function duplicateProject(id: string) {
    try {
      const res = await fetch(`${API}/projects/${id}/duplicate`, { method: 'POST' })
      if (res.ok) {
        await fetchProjects(page)
      }
    } catch (err) { console.error(err) }
  }

  async function deleteProject(id: string) {
    try {
      await fetch(`${API}/projects/${id}`, { method: 'DELETE' })
      setDeleteConfirm(null)
      // 删除后重新请求 API 获取当前页数据，保证分页一致性
      await fetchProjects(page)
    } catch (err) { console.error(err) }
  }

  const statusConfig: Record<string, { label: string; icon: typeof Clock; className: string }> = {
    pending: { label: '待处理', icon: Clock, className: 'text-slate-400 border-slate-200 bg-slate-50' },
    parsing: { label: '解析中', icon: Loader2, className: 'text-yellow-600 border-yellow-200 bg-yellow-50' },
    analyzing: { label: '分析中', icon: Loader2, className: 'text-blue-600 border-blue-200 bg-blue-50' },
    completed: { label: '已完成', icon: CheckCircle2, className: 'text-emerald-600 border-emerald-200 bg-emerald-50' },
    failed: { label: '失败', icon: AlertCircle, className: 'text-red-600 border-red-200 bg-red-50' },
  }

  function formatDate(ts: string | undefined) {
    if (!ts) return ''
    const d = new Date(ts)
    return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
  }

  const empty = !loading && projects.length === 0

  const projectCards = !loading && projects.length > 0

  return (
    <div className="min-h-screen bg-[#fcfcfd]">
      <div className="max-w-5xl mx-auto px-6 py-14">

        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-slate-800 tracking-tight">
            我的项目
          </h1>
          <div className="mt-3 h-1 w-16 rounded-full bg-gradient-to-r from-blue-500 to-purple-600" />
          <p className="text-slate-500 text-lg mt-4 max-w-2xl leading-relaxed">
            上传设计图纸或现场照片，AI 逐项审查装修陷阱，帮你守护每一分钱。
          </p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-32">
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
              <span className="text-sm text-slate-400">加载中...</span>
            </div>
          </div>
        )}

        {/* Empty State */}
        {empty && (
          <div className="flex flex-col items-center py-32">
            <div className="relative mb-8">
              <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-blue-50 to-purple-50 border border-slate-100 flex items-center justify-center shadow-2xl shadow-slate-200/30">
                <FileWarning className="w-10 h-10 text-slate-300" />
              </div>
              <div className="absolute -top-2 -right-2 w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold shadow-lg shadow-blue-500/30">
                ?
              </div>
            </div>
            <h2 className="text-xl font-semibold text-slate-700 mb-2">还没有项目</h2>
            <p className="text-slate-400 text-base mb-8 max-w-md text-center leading-relaxed">
              上传你的设计文档或现场照片，AI 将在几分钟内帮你揪出藏在设计里的坑。
            </p>
            <button
              onClick={() => navigate('/projects/new')}
              className="flex items-center gap-2 px-7 py-3.5 bg-white border-2 border-slate-200 rounded-2xl text-slate-700 font-semibold hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50/50 transition-all duration-300 shadow-lg shadow-slate-200/50 hover:shadow-xl hover:shadow-blue-200/30 active:scale-[0.98]"
            >
              <Plus className="w-5 h-5" />
              创建第一个项目
            </button>
          </div>
        )}

        {/* Project Grid */}
        {projectCards && (
          <div>
            {/* Stats Row */}
            <div className="flex items-center justify-between mb-6">
              <span className="text-sm text-slate-400">
                共 {total} 个项目 · 第 {page}/{totalPages} 页
              </span>
              <button
                onClick={() => navigate('/projects/new')}
                className="flex items-center gap-2 px-5 py-2.5 bg-white border-2 border-slate-200 rounded-xl text-slate-600 font-medium text-sm hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50/30 transition-all duration-300 active:scale-[0.97]"
              >
                <Plus className="w-4 h-4" />
                新建项目
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {projects.map((p) => {
                const st = statusConfig[p.status] || statusConfig.pending
                const StatusIcon = st.icon
                const isSpinning = p.status === 'parsing' || p.status === 'analyzing'

                return (
                  <div key={p.id}>
                    <div
                      className="group relative bg-white rounded-3xl border border-slate-100 p-6 hover:shadow-2xl hover:shadow-slate-200/40 hover:border-blue-100 hover:-translate-y-0.5 transition-all duration-500 cursor-pointer overflow-hidden"
                      onClick={() => navigate(`/project/${p.id}`)}
                    >
                      {/* Hover glow */}
                      <div className="absolute inset-0 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 bg-gradient-to-br from-blue-50/40 via-transparent to-purple-50/40 pointer-events-none" />

                      <div className="relative z-10">
                        {/* Top: icon + name + status */}
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-start gap-4">
                            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-50 to-purple-50 border border-slate-100 flex items-center justify-center shadow-sm group-hover:shadow-md group-hover:scale-105 transition-all duration-500">
                              <FolderOpen className="w-7 h-7 text-blue-500 group-hover:text-blue-600 transition-colors" />
                            </div>
                            <div className="pt-1">
                              <h3 className="text-lg font-bold text-slate-800 group-hover:text-blue-600 transition-colors leading-snug">
                                {p.name}
                              </h3>
                              {p.description && (
                                <p className="text-sm text-slate-400 mt-0.5 line-clamp-2 max-w-[240px] leading-relaxed">
                                  {p.description}
                                </p>
                              )}
                            </div>
                          </div>
                          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium whitespace-nowrap ${st.className}`}>
                            <StatusIcon className={`w-3.5 h-3.5 ${isSpinning ? 'animate-spin' : ''}`} />
                            {st.label}
                          </div>
                        </div>

                        {/* Bottom: meta + actions */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4 text-xs text-slate-400">
                            {p.file_count !== undefined && (
                              <span className="flex items-center gap-1">
                                <FileText className="w-3.5 h-3.5" />
                                {p.file_count} 个文件
                              </span>
                            )}
                            {p.image_count !== undefined && p.image_count > 0 && (
                              <span className="flex items-center gap-1">
                                <Image className="w-3.5 h-3.5" />
                                {p.image_count} 张图片
                              </span>
                            )}
                            {p.created_at && (
                              <span className="flex items-center gap-1">
                                <Clock className="w-3.5 h-3.5" />
                                {formatDate(p.created_at)}
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-2">
                            <button
                              onClick={async (e) => { e.stopPropagation(); await duplicateProject(p.id); }}
                              className="p-2 text-slate-300 hover:text-blue-400 hover:bg-blue-50 rounded-xl transition-all opacity-0 group-hover:opacity-100"
                              title="复制项目"
                            >
                              <Copy className="w-4 h-4" />
                            </button>
                            <button
                              onClick={(e) => { e.stopPropagation(); setDeleteConfirm(p.id) }}
                              className="p-2 text-slate-300 hover:text-red-400 hover:bg-red-50 rounded-xl transition-all opacity-0 group-hover:opacity-100"
                              title="删除"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                            <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center group-hover:bg-blue-100 group-hover:text-blue-600 transition-all text-slate-300">
                              <svg className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                            </div>
                          </div>
                        </div>
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
                )
              })}
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-10">
                <button
                  onClick={() => goToPage(page - 1)}
                  disabled={page <= 1}
                  className="flex items-center gap-1 px-4 py-2 rounded-xl border border-slate-200 text-sm font-medium text-slate-600 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50/30 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronLeft className="w-4 h-4" />
                  上一页
                </button>

                {getPageNumbers().map((p, idx) =>
                  p === '...' ? (
                    <span
                      key={`ellipsis-${idx}`}
                      className="w-10 h-10 flex items-center justify-center text-slate-400 text-sm select-none"
                    >
                      <Ellipsis className="w-4 h-4" />
                    </span>
                  ) : (
                    <button
                      key={p}
                      onClick={() => goToPage(p as number)}
                      className={`w-10 h-10 rounded-xl text-sm font-medium transition-all ${p === page
                        ? 'bg-blue-600 text-white shadow-lg shadow-blue-200'
                        : 'border border-slate-200 text-slate-600 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50/30'
                        }`}
                    >
                      {p}
                    </button>
                  )
                )}

                <button
                  onClick={() => goToPage(page + 1)}
                  disabled={page >= totalPages}
                  className="flex items-center gap-1 px-4 py-2 rounded-xl border border-slate-200 text-sm font-medium text-slate-600 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50/30 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                >
                  下一页
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
