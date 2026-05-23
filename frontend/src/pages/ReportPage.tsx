import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Loader2, AlertTriangle, FileDown, ChevronRight, FileText, CheckCircle2 } from 'lucide-react'
import type { Report } from '../types'

const API = '/api'

export default function ReportPage() {
  const { id: projectId } = useParams<{ id: string }>()
  const [report, setReport] = useState<Report | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState('')

  const fetchReport = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/projects/${projectId}/report`)
      if (res.ok) setReport(await res.json())
      else setError('尚无报告，请先完成分析')
    } catch {
      setError('加载失败')
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => { fetchReport() }, [fetchReport])

  async function downloadPdf() {
    setDownloading(true)
    try {
      const res = await fetch(`${API}/projects/${projectId}/report/pdf`)
      if (res.ok) {
        const blob = await res.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `report_${projectId}.pdf`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch {
      // ignore
    } finally {
      setDownloading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <Loader2 className="w-8 h-8 animate-spin text-slate-300" />
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <Link
          to={`/project/${projectId}`}
          className="text-slate-400 hover:text-slate-600 no-underline flex items-center gap-1 text-sm mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> 返回项目
        </Link>
        <div className="flex flex-col items-center justify-center min-h-[50vh] text-slate-400">
          <AlertTriangle className="w-12 h-12 text-slate-300 mb-3" />
          <p className="text-lg font-medium text-slate-500">{error || '尚无报告，请先完成分析'}</p>
        </div>
      </div>
    )
  }

  const { summary } = report

  const getScoreLevel = (score: number) => {
    if (score >= 80) return { color: 'text-green-600', bg: 'bg-green-500', label: '优秀' }
    if (score >= 60) return { color: 'text-yellow-600', bg: 'bg-yellow-500', label: '待改进' }
    return { color: 'text-red-600', bg: 'bg-red-500', label: '需重视' }
  }

  const scoreLevel = getScoreLevel(summary.score)

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 mb-8">
        <Link to={`/project/${projectId}/analysis`} className="text-slate-400 hover:text-slate-600 no-underline flex items-center gap-1 text-sm transition-colors">
          <ArrowLeft className="w-4 h-4" />
          分析结果
        </Link>
        <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
        <span className="text-sm text-slate-600 font-medium">分析报告</span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">分析报告</h1>
          <p className="text-slate-500 text-sm mt-1.5">可下载 PDF 版本供设计师或工班参考</p>
        </div>
        <button
          onClick={downloadPdf}
          disabled={downloading}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-green-600 to-emerald-500 text-white rounded-xl text-sm font-medium hover:from-green-700 hover:to-emerald-600 disabled:opacity-50 transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-green-500/20"
        >
          {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
          下载 PDF 报告
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <FileText className="w-4 h-4 text-blue-500" />
            <p className="text-xs text-slate-500 font-medium">总陷阱数</p>
          </div>
          <p className="text-3xl font-bold text-slate-800">{summary.total_pitfalls}</p>
        </div>
        <div className="bg-white rounded-2xl border border-red-200 p-5 shadow-sm bg-gradient-to-br from-red-50 to-white">
          <p className="text-xs text-red-600 font-medium mb-1">严重</p>
          <p className="text-3xl font-bold text-red-700">{summary.critical_count}</p>
        </div>
        <div className="bg-white rounded-2xl border border-orange-200 p-5 shadow-sm bg-gradient-to-br from-orange-50 to-white">
          <p className="text-xs text-orange-600 font-medium mb-1">高</p>
          <p className="text-3xl font-bold text-orange-700">{summary.high_count}</p>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <p className="text-xs text-slate-500 font-medium mb-1">中 / 低</p>
          <p className="text-3xl font-bold text-slate-800">{summary.medium_count + summary.low_count}</p>
        </div>
      </div>

      {/* Score Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-8 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <CheckCircle2 className={`w-5 h-5 ${scoreLevel.color}`} />
            <h2 className="text-sm font-semibold text-slate-700">综合评分</h2>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-sm font-medium ${scoreLevel.color}`}>{scoreLevel.label}</span>
            <span className={`text-4xl font-bold ${scoreLevel.color}`}>
              {summary.score}
              <span className="text-base font-normal text-slate-400"> / 100</span>
            </span>
          </div>
        </div>
        <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden mt-3 shadow-inner">
          <div
            className={`h-full rounded-full transition-all duration-1000 ${scoreLevel.bg} shadow-lg`}
            style={{ width: `${Math.max(summary.score, 2)}%` }}
          />
        </div>
      </div>

      {/* PDF Section */}
      <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center shadow-sm">
        {report.pdf_path ? (
          <>
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-green-100 to-emerald-50 flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-8 h-8 text-green-500" />
            </div>
            <p className="text-slate-700 font-semibold text-lg mb-1">PDF 报告已生成</p>
            <p className="text-slate-400 text-sm mb-5">
              生成时间：{new Date(report.generated_at).toLocaleString('zh-CN')}
            </p>
          </>
        ) : (
          <>
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-yellow-100 to-amber-50 flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-8 h-8 text-yellow-500" />
            </div>
            <p className="text-slate-700 font-semibold text-lg mb-1">PDF 尚未生成</p>
            <p className="text-slate-400 text-sm mb-5">请点击下方按钮生成 PDF 报告</p>
          </>
        )}
        <button
          onClick={downloadPdf}
          disabled={downloading}
          className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-500 text-white rounded-xl text-sm font-medium hover:from-green-700 hover:to-emerald-600 disabled:opacity-50 transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-green-500/20"
        >
          {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
          {report.pdf_path ? '重新下载 PDF' : '生成并下载 PDF'}
        </button>
      </div>
    </div>
  )
}