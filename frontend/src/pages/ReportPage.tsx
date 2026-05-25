import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft, Loader2, AlertTriangle, FileDown, ChevronRight, FileText,
  CheckCircle2, MapPin, Lightbulb, Tag, ShieldAlert, Info, Calendar, Hash,
  DollarSign, FileSignature, PlusCircle,
} from 'lucide-react'
import ExtraPredictionPanel from '../components/ExtraPredictionPanel'

const API = '/api'

interface Pitfall {
  id: string
  category: string
  description: string
  severity: string
  location: string | null
  suggestion: string
  critique: string | null
  trap_explanation: string | null
  bbox: number[] | null
}

interface Summary {
  total_pitfalls: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  score: number
  summary_text: string
}

interface DocumentRiskItem {
  id: string
  category: string
  title: string
  original_text: string
  critique: string | null
  financial_consequence: string | null
  suggested_fix: string | null
}

interface DocumentAnalysisResult {
  id: string
  project_id: string
  doc_type: string
  confidence: number
  summary: string
  total_estimated_risk: string
  risks_count: number
  risks: DocumentRiskItem[]
  extra_item_prediction?: any
  completed_at: string | null
  created_at: string | null
}

interface AnalysisResult {
  id: string
  project_id: string
  status: string
  summary: Summary
  pitfalls: Pitfall[]
  document_analyses?: Record<string, DocumentAnalysisResult>
  error_message: string | null
  completed_at: string | null
  created_at: string | null
}

export default function ReportPage() {
  const { id: projectId } = useParams<{ id: string }>()
  const [report, setReport] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState('')

  const fetchReport = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/projects/${projectId}/result`)
      if (!res.ok) throw new Error('加载失败')
      const data = await res.json()
      if (data.status === 'failed') {
        setError(data.summary?.summary_text || data.error_message || '分析失败')
      } else {
        setReport(data)
      }
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

  const { summary, pitfalls, document_analyses } = report

  const getScoreLevel = (score: number) => {
    if (score >= 80) return { color: 'text-green-600', bg: 'bg-green-500', label: '优秀' }
    if (score >= 60) return { color: 'text-yellow-600', bg: 'bg-yellow-500', label: '待改进' }
    return { color: 'text-red-600', bg: 'bg-red-500', label: '需重视' }
  }

  const scoreLevel = getScoreLevel(summary.score)

  const severityConfig: Record<string, { color: string; bg: string; border: string; label: string }> = {
    critical: { color: 'text-red-700', bg: 'bg-red-50', border: 'border-red-300', label: '严重' },
    high: { color: 'text-orange-700', bg: 'bg-orange-50', border: 'border-orange-300', label: '高' },
    medium: { color: 'text-yellow-700', bg: 'bg-yellow-50', border: 'border-yellow-300', label: '中' },
    low: { color: 'text-blue-700', bg: 'bg-blue-50', border: 'border-blue-300', label: '低' },
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '未知'
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    })
  }

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

      {/* Header + Download */}
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

      {/* Project Meta Info */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Hash className="w-3.5 h-3.5 text-slate-400" />
            <p className="text-xs text-slate-500 font-medium">项目 ID</p>
          </div>
          <p className="text-sm font-mono font-bold text-slate-700 truncate" title={report.project_id}>
            {report.project_id.slice(0, 16)}...
          </p>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <p className="text-xs text-slate-500 font-medium">创建时间</p>
          </div>
          <p className="text-xs text-slate-700">{formatDate(report.created_at)}</p>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
            <p className="text-xs text-slate-500 font-medium">完成分析</p>
          </div>
          <p className="text-xs text-slate-700">{formatDate(report.completed_at)}</p>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <FileText className="w-3.5 h-3.5 text-blue-500" />
            <p className="text-xs text-slate-500 font-medium">总陷阱数</p>
          </div>
          <p className="text-3xl font-bold text-slate-800">{summary.total_pitfalls}</p>
        </div>
      </div>

      {/* Score Card + Summary Text */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-8 shadow-sm">
        <div className="flex items-center justify-between mb-3">
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
        <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden mb-4 shadow-inner">
          <div
            className={`h-full rounded-full transition-all duration-1000 ${scoreLevel.bg} shadow-lg`}
            style={{ width: `${Math.max(summary.score, 2)}%` }}
          />
        </div>

        {/* Severity Counts */}
        <div className="grid grid-cols-4 gap-3 mb-4">
          {(['critical', 'high', 'medium', 'low'] as const).map((sev) => (
            <div key={sev} className={`rounded-xl border ${severityConfig[sev].border} ${severityConfig[sev].bg} p-3 text-center`}>
              <p className={`text-xs font-semibold ${severityConfig[sev].color} mb-1`}>{severityConfig[sev].label}</p>
              <p className={`text-2xl font-bold ${severityConfig[sev].color}`}>
                {summary[`${sev}_count` as keyof Summary] as number}
              </p>
            </div>
          ))}
        </div>

        {/* Summary Text */}
        {summary.summary_text && (
          <div className="bg-slate-50 rounded-xl border border-slate-200 p-4">
            <div className="flex items-center gap-2 mb-2">
              <Info className="w-4 h-4 text-slate-500" />
              <h3 className="text-sm font-semibold text-slate-600">总体评估</h3>
            </div>
            <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
              {summary.summary_text}
            </p>
          </div>
        )}
      </div>

      {/* Pitfalls Detail */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-5 h-5 text-amber-500" />
          <h2 className="text-lg font-semibold text-slate-800">问题详情</h2>
          <span className="text-sm text-slate-400">（共 {pitfalls.length} 个）</span>
        </div>

        {pitfalls.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center shadow-sm">
            <CheckCircle2 className="w-10 h-10 text-green-400 mx-auto mb-3" />
            <p className="text-slate-500">未发现装修陷阱，设计良好！</p>
          </div>
        ) : (
          <div className="space-y-4">
            {pitfalls.map((p) => {
              const cfg = severityConfig[p.severity] || severityConfig.medium
              return (
                <div
                  key={p.id}
                  className={`bg-white rounded-2xl border-l-4 ${cfg.border.replace('border-', 'border-l-')} border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow`}
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`inline-block px-2 py-0.5 rounded-md text-xs font-bold ${cfg.bg} ${cfg.color}`}>
                          {cfg.label}
                        </span>
                        {p.category && (
                          <span className="flex items-center gap-1 text-xs text-slate-500">
                            <Tag className="w-3 h-3" />
                            {p.category}
                          </span>
                        )}
                      </div>
                      <h3 className="text-base font-semibold text-slate-800">{p.description}</h3>
                    </div>
                    {p.location && (
                      <div className="flex items-center gap-1 text-xs text-slate-500 bg-slate-100 rounded-lg px-2 py-1 ml-3 shrink-0">
                        <MapPin className="w-3 h-3" />
                        {p.location}
                      </div>
                    )}
                  </div>

                  {/* Critique */}
                  {p.critique && (
                    <div className="mb-3">
                      <div className="flex items-center gap-1.5 mb-1">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                        <span className="text-xs font-medium text-slate-500">问题分析</span>
                      </div>
                      <p className="text-sm text-slate-700 leading-relaxed bg-amber-50 rounded-lg p-3">
                        {p.critique}
                      </p>
                    </div>
                  )}

                  {/* Trap Explanation */}
                  {p.trap_explanation && (
                    <div className="mb-3">
                      <div className="flex items-center gap-1.5 mb-1">
                        <ShieldAlert className="w-3.5 h-3.5 text-red-500" />
                        <span className="text-xs font-medium text-slate-500">陷阱说明</span>
                      </div>
                      <p className="text-sm text-slate-700 leading-relaxed bg-red-50 rounded-lg p-3">
                        {p.trap_explanation}
                      </p>
                    </div>
                  )}

                  {/* Suggestion */}
                  {p.suggestion && (
                    <div>
                      <div className="flex items-center gap-1.5 mb-1">
                        <Lightbulb className="w-3.5 h-3.5 text-green-500" />
                        <span className="text-xs font-medium text-slate-500">改进建议</span>
                      </div>
                      <p className="text-sm text-slate-700 leading-relaxed bg-green-50 rounded-lg p-3">
                        {p.suggestion}
                      </p>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Contract / Quotation Risk Analysis Section */}
      {document_analyses && Object.keys(document_analyses).length > 0 && (() => {
        const docList = Object.values(document_analyses)
        return (
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="w-5 h-5 text-violet-500" />
              <h2 className="text-lg font-semibold text-slate-800">合同 / 报价单风险分析</h2>
            </div>

            {docList.map((doc) => {
              const risks = doc.risks || []
              const categoryConfig: Record<string, { icon: typeof FileText; label: string; color: string; bg: string; border: string }> = {
                billing_trap: { icon: DollarSign, label: '报价陷阱', color: 'text-rose-600', bg: 'bg-rose-50', border: 'border-rose-300' },
                contract_clause: { icon: FileSignature, label: '合同条款', color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-300' },
                extra_item: { icon: PlusCircle, label: '增项风险', color: 'text-purple-600', bg: 'bg-purple-50', border: 'border-purple-300' },
              }

              return (
                <div key={doc.id} className="bg-white rounded-2xl border border-slate-200 p-6 mb-4 shadow-sm">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-semibold text-slate-700">
                          {doc.doc_type === 'quotation' ? '报价单分析' : doc.doc_type === 'contract' ? '合同分析' : '文档分析'}
                        </span>
                        <span className="text-xs text-slate-400">
                          置信度 {Math.round(doc.confidence * 100)}%
                        </span>
                      </div>
                      {doc.summary && (
                        <p className="text-sm text-slate-600 mt-2 leading-relaxed">{doc.summary}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {risks.length > 0 ? (
                        <span className="px-3 py-1 rounded-full bg-red-50 text-red-700 text-xs font-semibold">
                          {risks.length} 个风险
                        </span>
                      ) : (
                        <span className="px-3 py-1 rounded-full bg-green-50 text-green-700 text-xs font-semibold">
                          未发现风险
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Estimated total risk */}
                  {doc.total_estimated_risk && (
                    <div className="flex items-center gap-2 p-3 bg-rose-50 rounded-xl border border-rose-100 mb-4">
                      <AlertTriangle className="w-4 h-4 text-rose-500 flex-shrink-0" />
                      <span className="text-sm text-rose-700 font-medium">
                        预估总风险：{doc.total_estimated_risk}
                      </span>
                    </div>
                  )}

                  {/* Risk items */}
                  {risks.length > 0 ? (
                    <div className="space-y-3">
                      {risks.map((risk) => {
                        const cfg = categoryConfig[risk.category] || categoryConfig.contract_clause
                        const Icon = cfg.icon
                        return (
                          <div key={risk.id} className={`rounded-xl border ${cfg.border} ${cfg.bg} p-4`}>
                            <div className="flex items-center gap-2 mb-2">
                              <div className="w-7 h-7 rounded-lg bg-white flex items-center justify-center">
                                <Icon className={`w-3.5 h-3.5 ${cfg.color}`} />
                              </div>
                              <span className="text-xs font-semibold text-slate-400">{cfg.label}</span>
                            </div>
                            <h4 className="text-sm font-semibold text-slate-800 mb-1">{risk.title}</h4>
                            {risk.original_text && (
                              <p className="text-xs text-slate-500 italic mb-2">「{risk.original_text}」</p>
                            )}
                            {risk.critique && (
                              <p className="text-sm text-slate-700 leading-relaxed mb-2">{risk.critique}</p>
                            )}
                            {risk.financial_consequence && (
                              <div className="flex items-center gap-1.5 text-sm text-rose-600 font-medium mb-1">
                                <DollarSign className="w-3.5 h-3.5" />
                                {risk.financial_consequence}
                              </div>
                            )}
                            {risk.suggested_fix && (
                              <div className="mt-2 p-3 bg-green-50 rounded-lg border border-green-100">
                                <p className="text-sm text-slate-700">
                                  <span className="font-semibold text-green-700">✓ 建议：</span>
                                  {risk.suggested_fix}
                                </p>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-400 text-center py-4">未发现明显的合同或报价风险</p>
                  )}

                  {/* Extra Item Prediction */}
                  {doc.extra_item_prediction && (
                    <ExtraPredictionPanel prediction={doc.extra_item_prediction} />
                  )}
                </div>
              )
            })}
          </div>
        )
      })()}

      {/* PDF Download Section */}
      <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center shadow-sm">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-green-100 to-emerald-50 flex items-center justify-center mx-auto mb-4">
          <CheckCircle2 className="w-8 h-8 text-green-500" />
        </div>
        <p className="text-slate-700 font-semibold text-lg mb-1">报告已生成</p>
        <p className="text-slate-400 text-sm mb-5">可下载 PDF 版本保存或分享</p>
        <button
          onClick={downloadPdf}
          disabled={downloading}
          className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-500 text-white rounded-xl text-sm font-medium hover:from-green-700 hover:to-emerald-600 disabled:opacity-50 transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-green-500/20"
        >
          {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
          下载 PDF 报告
        </button>
      </div>
    </div>
  )
}