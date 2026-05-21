import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Loader2, AlertTriangle, Zap, AlertCircle, Info, Download } from 'lucide-react'
import type { AnalysisResult, PitfallItem, PitfallSeverity } from '../types'

const API = '/api'

const severityConfig: Record<PitfallSeverity, { icon: typeof AlertTriangle; color: string; bg: string; label: string }> = {
  critical: { icon: Zap, color: 'text-red-600', bg: 'bg-red-50 border-red-200', label: '严重' },
  high: { icon: AlertTriangle, color: 'text-orange-600', bg: 'bg-orange-50 border-orange-200', label: '高' },
  medium: { icon: AlertCircle, color: 'text-yellow-600', bg: 'bg-yellow-50 border-yellow-200', label: '中' },
  low: { icon: Info, color: 'text-blue-600', bg: 'bg-blue-50 border-blue-200', label: '低' },
}

export default function AnalysisPage() {
  const { id: projectId } = useParams<{ id: string }>()
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchAnalysis = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/projects/${projectId}/analysis`)
      if (res.ok) setResult(await res.json())
      else setError('无法加载分析结果')
    } catch { setError('加载失败') }
    finally { setLoading(false) }
  }, [projectId])

  useEffect(() => { fetchAnalysis() }, [fetchAnalysis])

  if (loading) {
    return <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-slate-400" /></div>
  }

  if (error || !result) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <Link to={`/project/${projectId}`} className="text-slate-400 hover:text-slate-600 no-underline flex items-center gap-2 mb-6"><ArrowLeft className="w-4 h-4" /> 返回项目</Link>
        <div className="bg-white rounded-xl border border-slate-200 p-10 text-center text-slate-400">
          <AlertTriangle className="w-10 h-10 mx-auto mb-3 text-yellow-500" />
          <p>{error || '尚无分析结果，请先上传文件并开始分析'}</p>
        </div>
      </div>
    )
  }

  const { summary, pitfalls } = result

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-3 mb-6">
        <Link to={`/project/${projectId}`} className="text-slate-400 hover:text-slate-600 no-underline"><ArrowLeft className="w-5 h-5" /></Link>
        <div>
          <h1 className="text-2xl font-bold text-slate-800">分析结果</h1>
          <p className="text-slate-500 text-sm mt-0.5">AI 检测到的装修陷阱总览</p>
        </div>
        <div className="ml-auto">
          <Link to={`/project/${projectId}/report`} className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 no-underline">
            <Download className="w-4 h-4" /> 下载报告
          </Link>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-8">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-400 mb-1">总陷阱数</p>
          <p className="text-2xl font-bold text-slate-800">{summary.total_pitfalls}</p>
        </div>
        {(['critical', 'high', 'medium', 'low'] as PitfallSeverity[]).map((s) => {
          const cfg = severityConfig[s]
          const Icon = cfg.icon
          const count = summary[`${s}_count` as keyof typeof summary] as number
          return (
            <div key={s} className="bg-white rounded-xl border border-slate-200 p-4">
              <p className={`text-xs mb-1 flex items-center gap-1 ${cfg.color}`}><Icon className="w-3 h-3" />{cfg.label}</p>
              <p className="text-2xl font-bold text-slate-800">{count}</p>
            </div>
          )
        })}
      </div>

      {/* Score */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-8">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-semibold text-slate-700">综合评分</h2>
          <span className={`text-lg font-bold ${summary.score >= 80 ? 'text-green-600' : summary.score >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>{summary.score} 分</span>
        </div>
        <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${summary.score >= 80 ? 'bg-green-500' : summary.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
            style={{ width: `${Math.max(summary.score, 2)}%` }}
          />
        </div>
        <p className="text-xs text-slate-400 mt-2">
          {summary.score >= 80 ? '整体设计良好，仅有少量改进空间' : summary.score >= 60 ? '存在部分问题，建议优化后再施工' : '存在较多隐患，建议重新审视设计'}
        </p>
      </div>

      {/* Pitfall List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
          <h2 className="text-sm font-semibold text-slate-700">问题详情（{pitfalls.length}）</h2>
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
    <div className="px-5 py-4 hover:bg-slate-50">
      <div className="flex items-start gap-3">
        <div className={`p-1.5 rounded-lg flex-shrink-0 ${cfg.bg}`}>
          <Icon className={`w-4 h-4 ${cfg.color}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${cfg.bg} ${cfg.color}`}>{cfg.label}</span>
            <span className="text-xs text-slate-400">{item.category}</span>
            {item.location && <span className="text-xs text-slate-400">📍 {item.location}</span>}
          </div>
          <p className="text-sm text-slate-700 font-medium">{item.description}</p>
          <div className="mt-2 p-2.5 bg-slate-50 rounded-lg">
            <p className="text-xs text-slate-500"><span className="font-medium text-green-600">✓ 建议：</span>{item.suggestion}</p>
          </div>
          {item.regulation_ref && (
            <p className="text-xs text-slate-400 mt-1.5">📋 法规参考：{item.regulation_ref}</p>
          )}
        </div>
      </div>
    </div>
  )
}