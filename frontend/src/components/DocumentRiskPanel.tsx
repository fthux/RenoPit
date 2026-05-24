import { useState, useEffect } from 'react'
import { FileText, AlertTriangle, DollarSign, FileSignature, PlusCircle, Loader2, ChevronDown, ChevronUp, Shield, ShieldAlert, Eye } from 'lucide-react'
import type { DocumentRiskItem, DocumentAnalysisResult, DocRiskCategory } from '../types'

const API = '/api'

const categoryConfig: Record<DocRiskCategory, { icon: typeof AlertTriangle; label: string; color: string; bg: string; border: string }> = {
  billing_trap: { icon: DollarSign, label: '报价陷阱', color: 'text-rose-600', bg: 'bg-rose-50', border: 'border-rose-200' },
  contract_clause: { icon: FileSignature, label: '合同条款', color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200' },
  extra_item: { icon: PlusCircle, label: '增项风险', color: 'text-purple-600', bg: 'bg-purple-50', border: 'border-purple-200' },
}

interface Props {
  projectId: string
}

export default function DocumentRiskPanel({ projectId }: Props) {
  const [analyses, setAnalyses] = useState<DocumentAnalysisResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedRisk, setExpandedRisk] = useState<string | null>(null)

  useEffect(() => {
    if (!projectId) return
    fetch(`${API}/projects/${projectId}/document-analysis`)
      .then(r => {
        if (!r.ok) throw new Error('获取文档分析失败')
        return r.json()
      })
      .then(data => {
        setAnalyses(data.items || [])
        setError('')
      })
      .catch(e => {
        console.error('Document analysis fetch failed:', e)
        setError('暂无文档分析结果')
      })
      .finally(() => setLoading(false))
  }, [projectId])

  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center">
            <FileText className="w-5 h-5 text-violet-600" />
          </div>
          <h2 className="text-lg font-semibold text-slate-800">合同 / 报价单风险分析</h2>
        </div>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-slate-300" />
        </div>
      </div>
    )
  }

  if (error || analyses.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center">
            <FileText className="w-5 h-5 text-violet-600" />
          </div>
          <h2 className="text-lg font-semibold text-slate-800">合同 / 报价单风险分析</h2>
        </div>
        <div className="text-center py-8 text-slate-400">
          <Eye className="w-10 h-10 mx-auto mb-3 text-slate-300" />
          <p className="text-sm">上传合同或报价单文件后，点击分析按钮即可检测隐藏风险</p>
        </div>
      </div>
    )
  }

  // 取最新一次分析
  const latest = analyses[0]
  const allRisks: DocumentRiskItem[] = latest.risks || []

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center">
            <FileText className="w-5 h-5 text-violet-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-800">合同 / 报价单风险分析</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              文档类型：{latest.doc_type === 'quotation' ? '报价单' : latest.doc_type === 'contract' ? '合同' : '文档'}
              {' · '}置信度 {Math.round(latest.confidence * 100)}%
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {allRisks.length > 0 ? (
            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-red-50 text-red-700 text-xs font-semibold">
              <ShieldAlert className="w-3.5 h-3.5" />
              {allRisks.length} 个风险
            </span>
          ) : (
            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-green-50 text-green-700 text-xs font-semibold">
              <Shield className="w-3.5 h-3.5" />
              未发现风险
            </span>
          )}
        </div>
      </div>

      {/* Summary */}
      {latest.summary && (
        <div className="mb-6 p-4 bg-slate-50 rounded-xl border border-slate-100">
          <p className="text-sm text-slate-600 leading-relaxed">{latest.summary}</p>
        </div>
      )}

      {/* Estimated total risk */}
      {latest.total_estimated_risk && (
        <div className="mb-6 flex items-center gap-2 p-3 bg-rose-50 rounded-lg border border-rose-100">
          <AlertTriangle className="w-4 h-4 text-rose-500 flex-shrink-0" />
          <span className="text-sm text-rose-700 font-medium">
            预估总风险：{latest.total_estimated_risk}
          </span>
        </div>
      )}

      {/* Risk list */}
      {allRisks.length === 0 ? (
        <div className="text-center py-6 text-slate-400 text-sm">
          <Shield className="w-8 h-8 mx-auto mb-2 text-green-300" />
          未发现明显的合同或报价风险
        </div>
      ) : (
        <div className="space-y-3">
          {allRisks.map(risk => {
            const cfg = categoryConfig[risk.category] || categoryConfig.contract_clause
            const Icon = cfg.icon
            const isExpanded = expandedRisk === risk.id

            return (
              <div
                key={risk.id}
                className={`rounded-xl border transition-all duration-200 ${isExpanded ? cfg.border + ' shadow-sm' : 'border-slate-100 hover:border-slate-200'
                  }`}
              >
                {/* Risk header — click to expand */}
                <button
                  onClick={() => setExpandedRisk(isExpanded ? null : risk.id)}
                  className="w-full text-left p-4 flex items-start gap-3"
                >
                  <div className={`w-8 h-8 rounded-lg ${cfg.bg} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                    <Icon className={`w-4 h-4 ${cfg.color}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">{cfg.label}</span>
                    </div>
                    <h4 className="text-sm font-semibold text-slate-800 leading-snug">{risk.title}</h4>
                    {risk.original_text && (
                      <p className="text-xs text-slate-500 mt-1 line-clamp-2 italic">
                        「{risk.original_text}」
                      </p>
                    )}
                  </div>
                  <div className="flex-shrink-0 text-slate-300 mt-1">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </button>

                {/* Expanded detail */}
                {isExpanded && (
                  <div className="px-4 pb-4 pt-0 border-t border-slate-100 ml-0">
                    <div className="pl-11 space-y-3 mt-3">
                      {risk.critique && (
                        <div>
                          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">风险分析</span>
                          <p className="text-sm text-slate-600 mt-1 leading-relaxed">{risk.critique}</p>
                        </div>
                      )}
                      {risk.financial_consequence && (
                        <div>
                          <span className="text-xs font-semibold text-rose-400 uppercase tracking-wide">财务影响</span>
                          <p className="text-sm text-rose-600 mt-1 leading-relaxed font-medium">{risk.financial_consequence}</p>
                        </div>
                      )}
                      {risk.suggested_fix && (
                        <div>
                          <span className="text-xs font-semibold text-emerald-500 uppercase tracking-wide">建议对策</span>
                          <p className="text-sm text-slate-700 mt-1 leading-relaxed">{risk.suggested_fix}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* History list (previous analyses) */}
      {analyses.length > 1 && (
        <div className="mt-8 pt-6 border-t border-slate-200">
          <h3 className="text-sm font-semibold text-slate-500 mb-3">历史分析记录</h3>
          <div className="space-y-2">
            {analyses.slice(1).map(a => (
              <div key={a.id} className="flex items-center justify-between px-4 py-3 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-600">
                    {a.doc_type === 'quotation' ? '报价单分析' : a.doc_type === 'contract' ? '合同分析' : '文档分析'}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-400">
                    {a.risks_count} 个风险 · {new Date(a.created_at).toLocaleDateString('zh-CN')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}