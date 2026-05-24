import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Loader2, AlertTriangle, Zap, AlertCircle, Info, Download, ChevronRight, Shield, ShieldAlert, ShieldCheck } from 'lucide-react'
import type { AnalysisResult, PitfallItem, PitfallSeverity } from '../types'

const API = '/api'

const severityConfig: Record<PitfallSeverity, { icon: typeof AlertTriangle; color: string; bg: string; label: string; border: string }> = {
  critical: { icon: Zap, color: 'text-red-600', bg: 'bg-red-50', label: '严重', border: 'border-red-200' },
  high: { icon: AlertTriangle, color: 'text-orange-600', bg: 'bg-orange-50', label: '高', border: 'border-orange-200' },
  medium: { icon: AlertCircle, color: 'text-yellow-600', bg: 'bg-yellow-50', label: '中', border: 'border-yellow-200' },
  low: { icon: Info, color: 'text-blue-600', bg: 'bg-blue-50', label: '低', border: 'border-blue-200' },
}

export default function AnalysisPage() {
  const { id: projectId } = useParams<{ id: string }>()
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState(false)

  const handleDownloadPdf = useCallback(async () => {
    if (!projectId) return
    setDownloading(true)
    try {
      const res = await fetch(`/api/projects/${projectId}/report/pdf`)
      if (!res.ok) throw new Error('下载失败')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `renovation-report-${projectId.slice(0, 8)}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error('PDF download failed:', e)
      alert('PDF 下载失败，请稍后重试')
    } finally {
      setDownloading(false)
    }
  }, [projectId])

  const fetchAnalysis = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/projects/${projectId}/result`)
      if (res.ok) setResult(await res.json())
      else setError('无法加载分析结果')
    } catch { setError('加载失败') }
    finally { setLoading(false) }
  }, [projectId])

  useEffect(() => { fetchAnalysis() }, [fetchAnalysis])

  if (loading) {
    return <div className="flex items-center justify-center min-h-[70vh]"><Loader2 className="w-8 h-8 animate-spin text-slate-300" /></div>
  }

  if (error || !result) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <Link to={`/project/${projectId}`} className="text-slate-400 hover:text-slate-600 no-underline flex items-center gap-1 text-sm mb-6 transition-colors"><ArrowLeft className="w-4 h-4" /> 返回项目</Link>
        <div className="flex flex-col items-center justify-center min-h-[50vh] text-slate-400">
          <AlertTriangle className="w-12 h-12 text-slate-300 mb-3" />
          <p className="text-lg font-medium text-slate-500">{error || '尚无分析结果，请先上传文件并开始分析'}</p>
        </div>
      </div>
    )
  }

  if (result.status === 'failed') {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <Link to={`/project/${projectId}`} className="text-slate-400 hover:text-slate-600 no-underline flex items-center gap-1 text-sm mb-6 transition-colors"><ArrowLeft className="w-4 h-4" /> 返回项目</Link>
        <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-2xl border border-red-200 p-8 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-red-100 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-500" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-red-800">分析失败</h2>
              <p className="text-sm text-red-600">详细错误信息如下：</p>
            </div>
          </div>
          <div className="bg-white/80 rounded-xl border border-red-100 p-4 mt-2">
            <pre className="text-sm text-red-700 whitespace-pre-wrap font-mono">{result.error_message || '未知错误'}</pre>
          </div>
          <div className="mt-4">
            <Link to={`/project/${projectId}`} className="inline-flex items-center gap-2 px-5 py-2.5 bg-red-600 text-white rounded-xl text-sm font-medium hover:bg-red-700 no-underline transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-red-500/20">
              返回项目详情
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const { id: analysisId, summary, pitfalls, created_at: analysisCreatedAt, completed_at: analysisCompletedAt } = result

  const formatDateTime = (iso: string | undefined) => {
    if (!iso) return '—'
    const d = new Date(iso)
    return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  }

  const getScoreLevel = (score: number) => {
    if (score >= 80) return { color: 'text-green-600', bg: 'bg-green-500', label: '优秀', desc: '整体设计良好，仅有少量改进空间' }
    if (score >= 60) return { color: 'text-yellow-600', bg: 'bg-yellow-500', label: '待改进', desc: '存在部分问题，建议优化后再施工' }
    return { color: 'text-red-600', bg: 'bg-red-500', label: '需重视', desc: '存在较多隐患，建议重新审视设计' }
  }

  const scoreLevel = getScoreLevel(summary.score)

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 mb-8">
        <Link to={`/project/${projectId}`} className="text-slate-400 hover:text-slate-600 no-underline flex items-center gap-1 text-sm transition-colors">
          <ArrowLeft className="w-4 h-4" />
          项目详情
        </Link>
        <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
        <span className="text-sm text-slate-600 font-medium">分析结果</span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">分析结果</h1>
          <p className="text-slate-500 text-sm mt-1.5">AI 检测到的装修陷阱总览</p>
        </div>
        <button onClick={handleDownloadPdf} disabled={downloading} className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-green-600 to-emerald-500 text-white rounded-xl text-sm font-medium hover:from-green-700 hover:to-emerald-600 no-underline transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-green-500/20 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100">
          {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
          {downloading ? '下载中...' : '下载报告'}
        </button>
      </div>

      {/* Analysis Metadata */}
      {(analysisId || analysisCreatedAt || analysisCompletedAt) && (
        <div className="flex items-center gap-4 md:gap-6 flex-wrap mb-4 px-1">
          {analysisId && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-400">分析编号</span>
              <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">{analysisId.slice(0, 8)}</span>
            </div>
          )}
          {analysisCreatedAt && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-400">开始时间</span>
              <span className="text-xs text-slate-600 font-medium">{formatDateTime(analysisCreatedAt)}</span>
            </div>
          )}
          {analysisCompletedAt && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-400">完成时间</span>
              <span className="text-xs text-slate-600 font-medium">{formatDateTime(analysisCompletedAt)}</span>
            </div>
          )}
        </div>
      )}

      {/* Summary text */}
      {summary.summary_text && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50/50 rounded-2xl border border-blue-100/80 px-5 py-4 mb-6 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
              <ShieldCheck className="w-4 h-4 text-blue-600" />
            </div>
            <p className="text-sm text-slate-700 leading-relaxed">{summary.summary_text}</p>
          </div>
        </div>
      )}

      {/* Stats Bar: compact severity distribution */}
      <div className="bg-white rounded-2xl border border-slate-200 px-5 py-4 mb-8 shadow-sm">
        <div className="flex items-center gap-4 md:gap-6 flex-wrap">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-500">陷阱总数</span>
            <span className="text-xl font-bold text-slate-800">{summary.total_pitfalls}</span>
          </div>
          <div className="hidden md:block w-px h-6 bg-slate-200" />
          {(['critical', 'high', 'medium', 'low'] as PitfallSeverity[]).map((s, idx) => {
            const cfg = severityConfig[s]
            const Icon = cfg.icon
            const count = summary[`${s}_count` as keyof typeof summary] as number
            return (
              <div key={s} className="flex items-center gap-1.5">
                <Icon className={`w-3.5 h-3.5 ${cfg.color}`} />
                <span className="text-xs text-slate-500">{cfg.label}</span>
                <span className={`text-lg font-bold ${cfg.color}`}>{count}</span>
                {idx < 3 && <span className="hidden md:inline text-slate-200 mx-0.5">/</span>}
              </div>
            )
          })}
        </div>
        {/* Distribution bar */}
        {summary.total_pitfalls > 0 && (
          <div className="mt-3 flex h-2 rounded-full overflow-hidden bg-slate-100">
            {(['critical', 'high', 'medium', 'low'] as PitfallSeverity[]).map((s) => {
              const count = summary[`${s}_count` as keyof typeof summary] as number
              const pct = (count / summary.total_pitfalls) * 100
              if (pct === 0) return null
              const barColor = {
                critical: 'bg-red-500',
                high: 'bg-orange-400',
                medium: 'bg-yellow-400',
                low: 'bg-blue-400',
              }[s]
              return <div key={s} className={`${barColor} h-full transition-all duration-700`} style={{ width: `${pct}%` }} />
            })}
          </div>
        )}
      </div>

      {/* Score Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-8 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-slate-500" />
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
        <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden mt-3 mb-3 shadow-inner">
          <div
            className={`h-full rounded-full transition-all duration-1000 ${scoreLevel.bg} shadow-lg`}
            style={{ width: `${Math.max(summary.score, 2)}%` }}
          />
        </div>
        <p className="text-xs text-slate-400 mt-1">{scoreLevel.desc}</p>
      </div>

      {/* Pitfall List */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-slate-500" />
            <h2 className="text-sm font-semibold text-slate-700">问题详情（{pitfalls.length}）</h2>
          </div>
        </div>
        <div className="divide-y divide-slate-100">
          {pitfalls.map((item) => (
            <PitfallCard key={item.id} item={item} />
          ))}
        </div>
      </div>
    </div>
  )
}

function PitfallCard({ item }: { item: PitfallItem }) {
  const cfg = severityConfig[item.severity]
  const Icon = cfg.icon

  return (
    <div className="px-6 py-5 hover:bg-slate-50/50 transition-colors">
      <div className="flex items-start gap-4">
        <div className={`p-2 rounded-xl flex-shrink-0 ${cfg.bg} ${cfg.border} border`}>
          <Icon className={`w-4 h-4 ${cfg.color}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${cfg.bg} ${cfg.color} ${cfg.border} border`}>{cfg.label}</span>
            <span className="text-xs text-slate-400">{item.category}</span>
            {item.location && (
              <span className="text-xs text-slate-400 inline-flex items-center gap-1">
                <span>📍</span> {item.location}
              </span>
            )}
          </div>
          <p className="text-sm text-slate-700 font-medium leading-relaxed">{item.description}</p>

          {item.critique && (
            <div className="mt-3 p-3 bg-amber-50/80 rounded-xl border border-amber-100/80">
              <p className="text-xs text-slate-600">
                <span className="font-semibold text-amber-700">⚠ 问题分析：</span>
                {item.critique}
              </p>
            </div>
          )}

          {item.trap_explanation && (
            <div className="mt-3 p-3 bg-red-50/80 rounded-xl border border-red-100/80">
              <p className="text-xs text-slate-600">
                <span className="font-semibold text-red-700">⛔ 陷阱说明：</span>
                {item.trap_explanation}
              </p>
            </div>
          )}

          <div className="mt-3 p-3 bg-green-50/50 rounded-xl border border-green-100/50">
            <p className="text-xs text-slate-600">
              <span className="font-semibold text-green-700">✓ 建议：</span>
              {item.suggestion}
            </p>
          </div>
          {item.regulation_ref && (
            <p className="text-xs text-slate-400 mt-2 flex items-center gap-1">
              <span>📋</span> 法规参考：{item.regulation_ref}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}