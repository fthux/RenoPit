import { DollarSign, Shield, TrendingUp, BarChart3 } from 'lucide-react'
import type { ExtraItemPrediction, PredictedItem } from '../types'

interface ExtraPredictionPanelProps {
  prediction: ExtraItemPrediction
}

const riskConfig: Record<string, { color: string; bg: string; label: string }> = {
  high: { color: 'text-red-600', bg: 'bg-red-50', label: '高风险' },
  medium: { color: 'text-yellow-600', bg: 'bg-yellow-50', label: '中风险' },
  low: { color: 'text-blue-600', bg: 'bg-blue-50', label: '低风险' },
}

const probabilityColors: Record<string, { color: string; bg: string }> = {
  '极高': { color: 'text-red-600', bg: 'bg-red-50' },
  '高': { color: 'text-orange-600', bg: 'bg-orange-50' },
  '中': { color: 'text-yellow-600', bg: 'bg-yellow-50' },
  '低': { color: 'text-blue-600', bg: 'bg-blue-50' },
}

function getProbabilityConfig(probability: string) {
  for (const [key, cfg] of Object.entries(probabilityColors)) {
    if (probability.includes(key)) return cfg
  }
  return { color: 'text-slate-600', bg: 'bg-slate-50' }
}

export default function ExtraPredictionPanel({ prediction }: ExtraPredictionPanelProps) {
  const { quoted_total, predicted_actual_total, confidence_range, risk_level, predicted_items } = prediction
  const riskCfg = riskConfig[risk_level] || riskConfig.medium
  const increase = predicted_actual_total - quoted_total
  const increasePct = quoted_total > 0 ? ((increase / quoted_total) * 100).toFixed(0) : '0'

  const formatMoney = (val: number) => {
    return new Intl.NumberFormat('zh-CN', { style: 'decimal', maximumFractionDigits: 0 }).format(val)
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-4 shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-5 h-5 text-purple-500" />
        <h2 className="text-lg font-semibold text-slate-800">增项预测与总花费估算</h2>
      </div>

      {/* Price Comparison Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
        {/* Quoted Total */}
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-1.5 mb-1">
            <DollarSign className="w-4 h-4 text-slate-400" />
            <span className="text-xs text-slate-500 font-medium">报价单表面总价</span>
          </div>
          <p className="text-2xl font-bold text-slate-800">¥{formatMoney(quoted_total)}</p>
        </div>

        {/* Predicted Actual Total */}
        <div className={`rounded-xl border p-4 ${riskCfg.bg} ${riskCfg.color.replace('text-', 'border-').replace('-600', '-200')}`}>
          <div className="flex items-center gap-1.5 mb-1">
            <BarChart3 className={`w-4 h-4 ${riskCfg.color}`} />
            <span className={`text-xs font-medium ${riskCfg.color}`}>预测实际总花费</span>
          </div>
          <p className={`text-2xl font-bold ${riskCfg.color}`}>¥{formatMoney(predicted_actual_total)}</p>
          <p className={`text-xs mt-1 ${riskCfg.color}`}>
            预估增加：+¥{formatMoney(increase)}（+{increasePct}%）
          </p>
        </div>

        {/* Confidence Range */}
        <div className="bg-indigo-50 rounded-xl border border-indigo-100 p-4">
          <div className="flex items-center gap-1.5 mb-1">
            <Shield className="w-4 h-4 text-indigo-500" />
            <span className="text-xs text-indigo-500 font-medium">置信区间</span>
          </div>
          <p className="text-lg font-bold text-indigo-700">
            ¥{formatMoney(confidence_range[0])} ~ ¥{formatMoney(confidence_range[1])}
          </p>
        </div>
      </div>

      {/* Risk Level */}
      <div className={`flex items-center gap-2 px-4 py-3 rounded-xl border mb-5 ${riskCfg.bg} ${riskCfg.color.replace('text-', 'border-').replace('-600', '-200')}`}>
        <span className={`text-sm font-semibold ${riskCfg.color}`}>总体风险等级：{riskCfg.label}</span>
        <span className="text-xs text-slate-400">|</span>
        <span className="text-xs text-slate-500">
          共预测 {predicted_items.length} 项增项
        </span>
      </div>

      {/* Predicted Items */}
      {predicted_items.length > 0 ? (
        <div className="space-y-3">
          <p className="text-xs text-slate-500 font-medium">预测增项列表（按概率从高到低排列）</p>
          {predicted_items.map((item, idx) => (
            <PredictedItemCard key={idx} item={item} />
          ))}
        </div>
      ) : (
        <div className="text-center py-6 text-slate-400 text-sm">
          未检测到明显的增项风险项
        </div>
      )}
    </div>
  )
}

function PredictedItemCard({ item }: { item: PredictedItem }) {
  const probCfg = getProbabilityConfig(item.probability)
  const formatMoney = (val: number) => {
    return new Intl.NumberFormat('zh-CN', { style: 'decimal', maximumFractionDigits: 0 }).format(val)
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      {/* Title */}
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-semibold text-slate-800">{item.name}</h4>
        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-semibold ${probCfg.bg} ${probCfg.color}`}>
          {item.probability}
        </span>
      </div>

      {/* Meta info */}
      <div className="flex items-center gap-3 flex-wrap mb-2 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <DollarSign className="w-3 h-3" />
          预估金额：¥{formatMoney(item.estimated_amount[0])} ~ ¥{formatMoney(item.estimated_amount[1])}
        </span>
        {item.trigger_phase && (
          <span className="flex items-center gap-1">
            <span>🔧</span>
            触发阶段：{item.trigger_phase}
          </span>
        )}
      </div>

      {/* Reason */}
      {item.reason && (
        <div className="mb-2 p-2 bg-amber-50 rounded-lg border border-amber-100">
          <p className="text-xs text-slate-600">
            <span className="font-semibold text-amber-700">预测理由：</span>
            {item.reason}
          </p>
        </div>
      )}

      {/* Prevention */}
      {item.prevention && (
        <div className="p-2 bg-green-50 rounded-lg border border-green-100">
          <p className="text-xs text-slate-600">
            <span className="font-semibold text-green-700">✓ 预防建议：</span>
            {item.prevention}
          </p>
        </div>
      )}
    </div>
  )
}