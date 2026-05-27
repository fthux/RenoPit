import { useState } from 'react'
import {
  AlertTriangle,
  AlertCircle,
  Info,
  FileText,
  FileSignature,
  DollarSign,
  Wrench,
  ShoppingCart,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronRight,
  Target,
} from 'lucide-react'
import type { CrossDocumentChecks } from '../types'

interface CrossCheckPanelProps {
  crossChecks: CrossDocumentChecks
}

const discrepancyTypeConfig: Record<string, { icon: typeof AlertTriangle; label: string; color: string; bg: string; border: string }> = {
  scope_mismatch: { icon: ShoppingCart, label: '范围缺失', color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' },
  material_substitution: { icon: Wrench, label: '材料替换', color: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200' },
  payment_inconsistency: { icon: DollarSign, label: '付款矛盾', color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200' },
  process_downgrade: { icon: FileSignature, label: '工艺降级', color: 'text-purple-600', bg: 'bg-purple-50', border: 'border-purple-200' },
  price_discrepancy: { icon: DollarSign, label: '价格差异', color: 'text-rose-600', bg: 'bg-rose-50', border: 'border-rose-200' },
  supervision_tracking: { icon: Target, label: '问题追踪', color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' },
  other: { icon: AlertCircle, label: '其他', color: 'text-slate-600', bg: 'bg-slate-50', border: 'border-slate-200' },
}

const severityConfig = {
  high: { icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-50', label: '高', border: 'border-red-200' },
  medium: { icon: AlertCircle, color: 'text-yellow-600', bg: 'bg-yellow-50', label: '中', border: 'border-yellow-200' },
  low: { icon: Info, color: 'text-blue-600', bg: 'bg-blue-50', label: '低', border: 'border-blue-200' },
}

export default function CrossCheckPanel({ crossChecks }: CrossCheckPanelProps) {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set())
  const [showTracking, setShowTracking] = useState(false)

  const toggleItem = (id: string) => {
    setExpandedItems((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const { discrepancies, document_pairs, supervision_tracking } = crossChecks

  // Determine the check mode label
  const checkModeLabel = crossChecks.check_mode === 'BILL_vs_CONTRACT'
    ? '合同 vs 报价单'
    : crossChecks.check_mode === 'SUPERVISION_TRACKING'
      ? '监理报告追踪'
      : crossChecks.check_mode === 'DESIGN_vs_BILL'
        ? '设计说明 vs 报价单'
        : '跨文档核查'

  // Determine the pair type display
  const pairTypeDisplay = crossChecks.pair_type
    ? crossChecks.pair_type === 'BILL_vs_CONTRACT'
      ? '合同 vs 报价单'
      : crossChecks.pair_type === 'SUPERVISION_TRACKING'
        ? '监理报告追踪'
        : crossChecks.pair_type === 'DESIGN_vs_BILL'
          ? '设计说明 vs 报价单'
          : crossChecks.pair_type
    : ''

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <FileText className="w-5 h-5 text-indigo-500" />
              <h3 className="text-base font-semibold text-slate-800">跨文档交叉核查</h3>
            </div>
            <p className="text-sm text-slate-500 mt-1">
              比对模式：{checkModeLabel}
              {pairTypeDisplay && <span className="ml-2">（{pairTypeDisplay}）</span>}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {discrepancies.length > 0 ? (
              <span className="px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-semibold">
                {discrepancies.length} 项不一致
              </span>
            ) : (
              <span className="px-3 py-1 rounded-full bg-green-50 text-green-700 text-xs font-semibold">
                未发现不一致
              </span>
            )}
          </div>
        </div>

        {/* Document pairs info */}
        {document_pairs && document_pairs.length > 0 && (
          <div className="flex items-center gap-2 p-3 bg-slate-50 rounded-xl border border-slate-100 text-sm text-slate-600">
            <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
            <span>参与比对的文档：{document_pairs.join('、')}</span>
          </div>
        )}
      </div>

      {/* Discrepancies list */}
      {discrepancies.length > 0 ? (
        <div className="space-y-3">
          {discrepancies.map((item, index) => {
            const typeCfg = discrepancyTypeConfig[item.type] || discrepancyTypeConfig.other
            const sevCfg = severityConfig[item.severity] || severityConfig.medium
            const TypeIcon = typeCfg.icon
            const SevIcon = sevCfg.icon
            const itemKey = `discrepancy-${index}`
            const isExpanded = expandedItems.has(itemKey)

            return (
              <div
                key={itemKey}
                className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm hover:shadow-md transition-all duration-200"
              >
                {/* Summary row - always visible */}
                <button
                  onClick={() => toggleItem(itemKey)}
                  className="w-full flex items-start gap-3 p-4 text-left cursor-pointer hover:bg-slate-50/50 transition-colors"
                >
                  {/* Type icon */}
                  <div className={`p-2 rounded-xl ${typeCfg.bg} ${typeCfg.border} border flex-shrink-0`}>
                    <TypeIcon className={`w-4 h-4 ${typeCfg.color}`} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${typeCfg.bg} ${typeCfg.color} ${typeCfg.border} border`}>
                        {typeCfg.label}
                      </span>
                      <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${sevCfg.bg} ${sevCfg.color} ${sevCfg.border} border`}>
                        <SevIcon className="w-3 h-3" />
                        严重等级：{sevCfg.label}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-slate-800 leading-relaxed">
                      {item.description}
                    </p>
                  </div>

                  {/* Expand toggle */}
                  <div className="flex-shrink-0 mt-1">
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </button>

                {/* Expanded detail */}
                {isExpanded && (
                  <div className="px-4 pb-4 pt-0 border-t border-slate-100">
                    <div className="space-y-3 mt-3">
                      {/* Source A */}
                      <div className="p-3 bg-blue-50 rounded-xl border border-blue-100">
                        <div className="flex items-center gap-1.5 mb-1">
                          <FileText className="w-3.5 h-3.5 text-blue-600" />
                          <span className="text-xs font-semibold text-blue-700">来源文档 A</span>
                        </div>
                        <p className="text-sm text-slate-700">{item.source_a}</p>
                      </div>

                      {/* Source B */}
                      <div className="p-3 bg-amber-50 rounded-xl border border-amber-100">
                        <div className="flex items-center gap-1.5 mb-1">
                          <FileText className="w-3.5 h-3.5 text-amber-600" />
                          <span className="text-xs font-semibold text-amber-700">来源文档 B</span>
                        </div>
                        <p className="text-sm text-slate-700">{item.source_b}</p>
                      </div>

                      {/* Risk */}
                      {item.risk && (
                        <div className="flex items-start gap-2 p-3 bg-red-50 rounded-xl border border-red-100">
                          <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                          <div>
                            <span className="text-xs font-semibold text-red-700">风险：</span>
                            <span className="text-sm text-slate-700">{item.risk}</span>
                          </div>
                        </div>
                      )}

                      {/* Suggested action */}
                      {item.suggested_action && (
                        <div className="flex items-start gap-2 p-3 bg-green-50 rounded-xl border border-green-100">
                          <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                          <div>
                            <span className="text-xs font-semibold text-green-700">建议：</span>
                            <span className="text-sm text-slate-700">{item.suggested_action}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm text-center">
          <CheckCircle className="w-10 h-10 text-green-400 mx-auto mb-3" />
          <p className="text-sm text-slate-500 font-medium">未发现跨文档不一致</p>
          <p className="text-xs text-slate-400 mt-1">
            所有参与比对的文档内容一致，未发现矛盾或差异
          </p>
        </div>
      )}

      {/* Supervision tracking */}
      {supervision_tracking && (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
          <button
            onClick={() => setShowTracking(!showTracking)}
            className="w-full flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50/50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-blue-500" />
              <h3 className="text-base font-semibold text-slate-800">监理报告问题追踪</h3>
            </div>
            <div className="flex items-center gap-3">
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${supervision_tracking.unresolved > 0
                ? 'bg-red-50 text-red-700'
                : 'bg-green-50 text-green-700'
                }`}>
                {supervision_tracking.unresolved} 项未解决
              </span>
              {showTracking ? (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronRight className="w-4 h-4 text-slate-400" />
              )}
            </div>
          </button>

          {/* Summary stats */}
          <div className="px-4 pb-2 flex items-center gap-4 flex-wrap">
            <span className="text-sm text-slate-500">
              共发现 <strong className="text-slate-700">{supervision_tracking.total_issues_found}</strong> 个问题
            </span>
            <span className="text-sm text-green-600">
              已解决 <strong>{supervision_tracking.resolved}</strong>
            </span>
            {supervision_tracking.unresolved > 0 && (
              <span className="text-sm text-red-600">
                未解决 <strong>{supervision_tracking.unresolved}</strong>
              </span>
            )}
          </div>

          {/* Tracking details */}
          {showTracking && (
            <div className="px-4 pb-4 border-t border-slate-100">
              {/* Unresolved items */}
              {supervision_tracking.unresolved_items.length > 0 && (
                <div className="mt-3">
                  <h4 className="flex items-center gap-1.5 text-sm font-semibold text-red-700 mb-2">
                    <XCircle className="w-4 h-4" />
                    未解决的问题
                  </h4>
                  <div className="space-y-2">
                    {supervision_tracking.unresolved_items.map((item, i) => (
                      <div key={i} className="p-3 bg-red-50 rounded-xl border border-red-100">
                        <p className="text-sm font-medium text-slate-800 mb-1">{item.issue}</p>
                        <div className="flex items-center gap-2 flex-wrap text-xs text-slate-500">
                          <span>首次报告：{item.first_reported}</span>
                          <span>最近报告：{item.last_reported}</span>
                          <span className={`px-1.5 py-0.5 rounded font-semibold ${item.severity === 'high' ? 'text-red-600 bg-red-100' :
                            item.severity === 'medium' ? 'text-yellow-600 bg-yellow-100' :
                              'text-blue-600 bg-blue-100'
                            }`}>
                            {item.severity === 'high' ? '严重' : item.severity === 'medium' ? '中等' : '轻微'}
                          </span>
                        </div>
                        {item.risk && (
                          <p className="text-xs text-red-600 mt-1">
                            <span className="font-semibold">风险：</span>{item.risk}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Resolved items */}
              {supervision_tracking.resolved_items.length > 0 && (
                <div className="mt-4">
                  <h4 className="flex items-center gap-1.5 text-sm font-semibold text-green-700 mb-2">
                    <CheckCircle className="w-4 h-4" />
                    已解决的问题
                  </h4>
                  <div className="space-y-2">
                    {supervision_tracking.resolved_items.map((item, i) => (
                      <div key={i} className="p-3 bg-green-50 rounded-xl border border-green-100 flex items-start gap-3">
                        <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-sm font-medium text-slate-800">{item.issue}</p>
                          <p className="text-xs text-slate-500 mt-0.5">
                            首次报告：{item.first_reported} → 已在 {item.resolved_in} 中解决
                          </p>
                          {item.resolution && (
                            <p className="text-xs text-green-700 mt-0.5">{item.resolution}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}