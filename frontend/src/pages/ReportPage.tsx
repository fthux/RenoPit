import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Loader2, Download, AlertTriangle, FileDown } from 'lucide-react'
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
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <Link
          to={`/project/${projectId}`}
          className="text-slate-400 hover:text-slate-600 no-underline flex items-center gap-2 mb-6"
        >
          <ArrowLeft className="w-4 h-4" /> 返回项目
        </Link>
        <div className="bg-white rounded-xl border border-slate-200 p-10 text-center text-slate-400">
          <AlertTriangle className="w-10 h-10 mx-auto mb-3 text-yellow-500" />
          <p>{error || '尚无报告，请先完成分析'}</p>
        </div>
      </div>
    )
  }

  const { summary } = report

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-3 mb-6">
        <Link to={`/project/${projectId}/analysis`} className="text-slate-400 hover:text-slate-600 no-underline">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-slate-800">分析报告</h1>
          <p className="text-slate-500 text-sm mt-0.5">可下载 PDF 版本供设计师或工班参考</p>
        </div>
        <div className="ml-auto">
          <button
            onClick={downloadPdf}
            disabled={downloading}
            className="flex items-center gap-2 px-5 py-2.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
            下载 PDF 报告
          </button>
        </div>
      </div>

      {/* Report Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-400 mb-1">总陷阱数</p>
          <p className="text-2xl font-bold text-slate-800">{summary.total_pitfalls}</p>
        </div>
        <div className="bg-white rounded-xl border border-red-200 p-4 bg-red-50">
          <p className="text-xs text-red-600 mb-1">严重</p>
          <p className="text-2xl font-bold text-red-700">{summary.critical_count}</p>
        </div>
        <div className="bg-white rounded-xl border border-orange-200 p-4 bg-orange-50">
          <p className="text-xs text-orange-600 mb-1">高</p>
          <p className="text-2xl font-bold text-orange-700">{summary.high_count}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-400 mb-1">中 / 低</p>
          <p className="text-2xl font-bold text-slate-800">{summary.medium_count + summary.low_count}</p>
        </div>
      </div>

      {/* Score Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 mb-8">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-700">综合评分</h2>
          <span
            className={`text-3xl font-bold ${summary.score >= 80 ? 'text-green-600' : summary.score >= 60 ? 'text-yellow-600' : 'text-red-600'
              }`}
          >
            {summary.score}
            <span className="text-base font-normal text-slate-400"> / 100</span>
          </span>
        </div>
        <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${summary.score >= 80 ? 'bg-green-500' : summary.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
            style={{ width: `${Math.max(summary.score, 2)}%` }}
          />
        </div>
      </div>

      {/* PDF Section */}
      {report.pdf_path ? (
        <div className="bg-white rounded-xl border border-slate-200 p-6 text-center">
          <Download className="w-10 h-10 text-green-500 mx-auto mb-3" />
          <p className="text-slate-700 font-medium mb-1">PDF 报告已生成</p>
          <p className="text-slate-400 text-sm mb-4">
            生成时间：{new Date(report.generated_at).toLocaleString('zh-CN')}
          </p>
          <button
            onClick={downloadPdf}
            disabled={downloading}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
            下载 PDF 报告
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 p-6 text-center">
          <AlertTriangle className="w-10 h-10 text-yellow-500 mx-auto mb-3" />
          <p className="text-slate-700 font-medium mb-1">PDF 尚未生成</p>
          <p className="text-slate-400 text-sm mb-4">请点击上方按钮下载 PDF 报告</p>
          <button
            onClick={downloadPdf}
            disabled={downloading}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
            生成并下载 PDF
          </button>
        </div>
      )}
    </div>
  )
}