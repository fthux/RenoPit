import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Loader2, AlertTriangle, Zap, AlertCircle, Info, Download, ChevronRight, Shield, ShieldCheck, FileText, DollarSign, FileSignature, PlusCircle, ScrollText, BarChart3, Award, ClipboardList, TrendingUp } from 'lucide-react'
import type { AnalysisResult, PitfallItem, PitfallSeverity } from '../types'
import ExtraPredictionPanel from '../components/ExtraPredictionPanel'

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
  const [activeSection, setActiveSection] = useState('')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const observerRef = useRef<IntersectionObserver | null>(null)

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

  // IntersectionObserver for active section highlighting
  useEffect(() => {
    // Compute section IDs based on available data
    if (!result) return
    const docs = result.document_analyses
    const hasDocs = docs && Object.keys(docs).length > 0
    const hasExtra = hasDocs && Object.values(docs).some((doc: any) => doc.extra_item_prediction)
    const sectionIds = [
      'section-summary',
      'section-pitfalls',
      'section-score',
      'section-details',
      ...(hasDocs ? ['section-contract'] : []),
      ...(hasExtra ? ['section-extra'] : []),
    ]
    const entriesMap = new Map<string, number>()

    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          entriesMap.set(entry.target.id, entry.intersectionRatio)
        })

        // Find the section with the highest visible ratio
        let maxRatio = 0
        let maxId = ''
        for (const id of sectionIds) {
          const ratio = entriesMap.get(id) || 0
          if (ratio > maxRatio) {
            maxRatio = ratio
            maxId = id
          }
        }
        if (maxId) {
          setActiveSection((prev) => prev !== maxId ? maxId : prev)
        }
      },
      { threshold: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], rootMargin: '-80px 0px -40% 0px' }
    )

    // Observe only existing section elements
    sectionIds.forEach((id) => {
      const el = document.getElementById(id)
      if (el && observerRef.current) {
        observerRef.current.observe(el)
      }
    })

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect()
      }
    }
  }, [result])

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

  const { id: analysisId, summary, pitfalls, document_analyses, created_at: analysisCreatedAt, completed_at: analysisCompletedAt } = result

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

  const hasDocumentAnalyses = document_analyses && Object.keys(document_analyses).length > 0
  const hasExtraPrediction = hasDocumentAnalyses && Object.values(document_analyses).some((doc: any) => doc.extra_item_prediction)

  const navItems = [
    { id: 'section-summary', Icon: ScrollText, label: '总体评价', color: 'text-teal-500' },
    { id: 'section-pitfalls', Icon: BarChart3, label: '陷阱数', color: 'text-blue-500' },
    { id: 'section-score', Icon: Award, label: '综合评分', color: 'text-amber-500' },
    { id: 'section-details', Icon: ClipboardList, label: '问题详情', color: 'text-slate-500' },
    ...(hasDocumentAnalyses ? [{ id: 'section-contract', Icon: FileText, label: '合同/报价单', color: 'text-violet-500' }] : []),
    ...(hasExtraPrediction ? [{ id: 'section-extra', Icon: TrendingUp, label: '增项预测', color: 'text-purple-500' }] : []),
  ]

  const HEADER_OFFSET = 100 // offset in px to account for fixed header (breadcrumb + title + metadata + mobile nav)

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id)
    if (el) {
      const top = el.getBoundingClientRect().top + window.scrollY - HEADER_OFFSET
      window.scrollTo({ behavior: 'smooth', top })
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 mb-6">
        <Link to={`/project/${projectId}`} className="text-slate-400 hover:text-slate-600 no-underline flex items-center gap-1 text-sm transition-colors">
          <ArrowLeft className="w-4 h-4" />
          项目详情
        </Link>
        <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
        <span className="text-sm text-slate-600 font-medium">分析结果</span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
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
      {(analysisId || projectId || analysisCreatedAt || analysisCompletedAt) && (
        <div className="flex items-center gap-4 md:gap-6 flex-wrap mb-6 px-1">
          {analysisId && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-400">分析报告编号</span>
              <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">{analysisId}</span>
            </div>
          )}
          {projectId && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-400">所属项目编号</span>
              <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">{projectId}</span>
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

      {/* Mobile: Horizontal scrollable nav */}
      <nav className="lg:hidden -mx-4 px-4 mb-6 overflow-x-auto scrollbar-hide sticky top-0 z-10 bg-white/95 backdrop-blur-sm border-b border-slate-100 py-2.5">
        <div className="flex items-center gap-1 min-w-max">
          {navItems.map((item) => {
            const isActive = activeSection === item.id
            const Icon = item.Icon
            return (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all duration-200 cursor-pointer ${isActive ? 'bg-slate-100 text-slate-800 shadow-sm' : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'
                  }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? item.color : 'text-slate-400'}`} />
                {item.label}
              </button>
            )
          })}
        </div>
      </nav>

      {/* Desktop: Flex layout with sticky sidebar */}
      <div className={`flex ${sidebarCollapsed ? 'gap-4' : 'gap-8'}`}>
        {/* Desktop sidebar nav */}
        <nav className={`hidden lg:block flex-shrink-0 transition-all duration-300 ${sidebarCollapsed ? 'w-14' : 'w-36'}`}>
          <div className={`sticky top-24 max-h-[calc(100vh-8rem)] overflow-y-auto ${sidebarCollapsed ? 'space-y-1' : 'space-y-0.5'}`}>
            {/* Toggle button */}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className={`w-full flex items-center justify-center px-2 py-2 rounded-xl text-xs font-medium transition-all duration-200 cursor-pointer text-slate-400 hover:text-slate-600 hover:bg-slate-50 mb-1 ${sidebarCollapsed ? '' : 'gap-2'}`}
              title={sidebarCollapsed ? '展开侧栏' : '收起侧栏'}
            >
              <ChevronRight className={`w-4 h-4 transition-transform duration-300 ${sidebarCollapsed ? '' : 'rotate-180'}`} />
              {!sidebarCollapsed && <span className="text-xs">收起</span>}
            </button>
            {navItems.map((item) => {
              const isActive = activeSection === item.id
              const Icon = item.Icon
              return (
                <button
                  key={item.id}
                  onClick={() => scrollToSection(item.id)}
                  className={`w-full flex items-center ${sidebarCollapsed ? 'justify-center' : 'gap-2.5 px-3'} py-2 rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer text-left ${isActive
                    ? 'bg-slate-100 text-slate-800 shadow-sm'
                    : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'
                    }`}
                  title={sidebarCollapsed ? item.label : undefined}
                >
                  <Icon className={`w-4 h-4 flex-shrink-0 transition-colors duration-200 ${isActive ? item.color : 'text-slate-400'
                    }`} />
                  {!sidebarCollapsed && <span className="truncate">{item.label}</span>}
                  {/* Active indicator dot - only show when expanded */}
                  {!sidebarCollapsed && isActive && <span className={`ml-auto w-1.5 h-1.5 rounded-full ${item.color.replace('text-', 'bg-')}`} />}
                </button>
              )
            })}
          </div>
        </nav>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          {/* Section: 总体评价 */}
          <div id="section-summary">
            {/* Title: 总体评价 */}
            <div className="flex items-center gap-2 mb-4">
              <ScrollText className="w-5 h-5 text-teal-500" />
              <h2 className="text-lg font-semibold text-slate-800">总体评价</h2>
            </div>
            {/* Summary text */}
            {summary.summary_text && (
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50/50 rounded-2xl border border-blue-100/80 px-5 py-4 mb-8 shadow-sm">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <ShieldCheck className="w-4 h-4 text-blue-600" />
                  </div>
                  <p className="text-sm text-slate-700 leading-relaxed">{summary.summary_text}</p>
                </div>
              </div>
            )}
          </div>

          {/* Section: 陷阱数 */}
          <div id="section-pitfalls">
            {/* Title: 陷阱数 */}
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 className="w-5 h-5 text-blue-500" />
              <h2 className="text-lg font-semibold text-slate-800">陷阱数</h2>
            </div>
            {/* Stats Bar */}
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
              {summary.total_pitfalls > 0 && (
                <div className="mt-3 flex h-2 rounded-full overflow-hidden bg-slate-100">
                  {(['critical', 'high', 'medium', 'low'] as PitfallSeverity[]).map((s) => {
                    const count = summary[`${s}_count` as keyof typeof summary] as number
                    const pct = (count / summary.total_pitfalls) * 100
                    if (pct === 0) return null
                    const barColor = {
                      critical: 'bg-red-500', high: 'bg-orange-400', medium: 'bg-yellow-400', low: 'bg-blue-400',
                    }[s]
                    return <div key={s} className={`${barColor} h-full transition-all duration-700`} style={{ width: `${pct}%` }} />
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Section: 综合评分 */}
          <div id="section-score">
            {/* Title: 综合评分 */}
            <div className="flex items-center gap-2 mb-4">
              <Award className="w-5 h-5 text-amber-500" />
              <h2 className="text-lg font-semibold text-slate-800">综合评分</h2>
            </div>
            {/* Score Card */}
            <div className={`bg-white rounded-2xl border p-6 mb-8 shadow-sm overflow-hidden relative ${scoreLevel.color === 'text-green-600' ? 'border-green-200' : scoreLevel.color === 'text-yellow-600' ? 'border-yellow-200' : 'border-red-200'}`}>
              {/* Decorative top accent bar */}
              <div className={`absolute top-0 left-0 right-0 h-1 ${scoreLevel.bg}`} />
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                {/* Left: Large Score */}
                <div className="flex items-center gap-4">
                  {/* Score ring */}
                  <div className={`relative w-20 h-20 rounded-full flex items-center justify-center flex-shrink-0 ${scoreLevel.bg === 'bg-green-500' ? 'bg-green-50' : scoreLevel.bg === 'bg-yellow-500' ? 'bg-yellow-50' : 'bg-red-50'}`}>
                    <span className={`text-3xl font-extrabold ${scoreLevel.color}`}>{summary.score}</span>
                    <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 80 80">
                      <circle cx="40" cy="40" r="34" fill="none" stroke="currentColor" strokeWidth="4" className="text-slate-100" />
                      <circle
                        cx="40" cy="40" r="34" fill="none" strokeWidth="4"
                        className={scoreLevel.bg}
                        strokeLinecap="round"
                        strokeDasharray={`${2 * Math.PI * 34}`}
                        strokeDashoffset={`${2 * Math.PI * 34 * (1 - summary.score / 100)}`}
                        style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
                      />
                    </svg>
                  </div>
                  <div>
                    <div className={`text-lg font-bold ${scoreLevel.color}`}>{scoreLevel.label}</div>
                    <div className="text-xs text-slate-400 mt-0.5">{scoreLevel.desc}</div>
                  </div>
                </div>
                {/* Right: Summary metrics */}
                <div className="flex items-center gap-4 md:gap-6 flex-shrink-0">
                  <div className="text-center px-4 py-2 rounded-xl bg-slate-50 border border-slate-100">
                    <div className="text-xs text-slate-400 mb-0.5">最高</div>
                    <div className="text-sm font-semibold text-slate-700">100</div>
                  </div>
                  <div className="text-center px-4 py-2 rounded-xl bg-slate-50 border border-slate-100">
                    <div className="text-xs text-slate-400 mb-0.5">及格线</div>
                    <div className="text-sm font-semibold text-slate-700">60</div>
                  </div>
                  <div className="text-center px-4 py-2 rounded-xl bg-slate-50 border border-slate-100">
                    <div className="text-xs text-slate-400 mb-0.5">当前</div>
                    <div className={`text-sm font-semibold ${scoreLevel.color}`}>{summary.score}</div>
                  </div>
                </div>
              </div>
              {/* Progress bar */}
              <div className="mt-5">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
                  <span>0</span>
                  <span>100</span>
                </div>
                <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden shadow-inner">
                  <div className={`h-full rounded-full transition-all duration-1000 ${scoreLevel.bg} shadow-lg`} style={{ width: `${Math.max(summary.score, 2)}%` }} />
                </div>
              </div>
            </div>
          </div>

          {/* Section: 问题详情 */}
          <div id="section-details">
            {/* Title: 问题详情 */}
            <div className="flex items-center gap-2 mb-4">
              <ClipboardList className="w-5 h-5 text-slate-500" />
              <h2 className="text-lg font-semibold text-slate-800">问题详情</h2>
              <span className="ml-2 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-500 text-xs font-medium">{pitfalls.length} 项</span>
            </div>
            {/* Pitfall List */}
            <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm mb-8">
              <div className="divide-y divide-slate-100">
                {pitfalls.map((item) => (
                  <PitfallCard key={item.id} item={item} />
                ))}
              </div>
            </div>
          </div>

          {/* Section: 合同/报价单风险分析 + 增项预测 */}
          {document_analyses && Object.keys(document_analyses).length > 0 && (
            <div>
              {/* Contract risk section */}
              <div id="section-contract">
                <div className="flex items-center gap-2 mb-4">
                  <FileText className="w-5 h-5 text-violet-500" />
                  <h2 className="text-lg font-semibold text-slate-800">合同 / 报价单风险分析</h2>
                </div>
                {Object.values(document_analyses).map((doc) => (
                  <div key={doc.id}>
                    <DocRiskSection doc={doc} />
                    {doc.extra_item_prediction && (
                      <div id="section-extra">
                        <div className="flex items-center gap-2 mb-4">
                          <TrendingUp className="w-5 h-5 text-purple-500" />
                          <h2 className="text-lg font-semibold text-slate-800">增项预测与总花费估算</h2>
                        </div>
                        <ExtraPredictionPanel prediction={doc.extra_item_prediction} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Fallback for extra prediction if no document_analyses */}
          {(!document_analyses || Object.keys(document_analyses).length === 0) && result && 'extra_item_prediction' in result && (
            <div id="section-extra">
              {/* Extra prediction fallback placeholder if needed */}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function DocRiskSection({ doc }: { doc: any }) {
  const risks = doc.risks || []
  const categoryConfig: Record<string, { icon: typeof FileText; label: string; color: string; bg: string; border: string }> = {
    billing_trap: { icon: DollarSign, label: '报价陷阱', color: 'text-rose-600', bg: 'bg-rose-50', border: 'border-rose-200' },
    contract_clause: { icon: FileSignature, label: '合同条款', color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200' },
    extra_item: { icon: PlusCircle, label: '增项风险', color: 'text-purple-600', bg: 'bg-purple-50', border: 'border-purple-200' },
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-4 shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-semibold text-slate-700">
              {doc.doc_type === 'quotation' ? '报价单分析' : doc.doc_type === 'contract' ? '合同分析' : '文档分析'}
            </span>
            <span className="text-xs text-slate-400">置信度 {Math.round(doc.confidence * 100)}%</span>
          </div>
          {doc.summary && <p className="text-sm text-slate-600 mt-2 leading-relaxed">{doc.summary}</p>}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {risks.length > 0 ? (
            <span className="px-3 py-1 rounded-full bg-red-50 text-red-700 text-xs font-semibold">{risks.length} 个风险</span>
          ) : (
            <span className="px-3 py-1 rounded-full bg-green-50 text-green-700 text-xs font-semibold">未发现风险</span>
          )}
        </div>
      </div>

      {/* Estimated total risk */}
      {doc.total_estimated_risk && (
        <div className="flex items-center gap-2 p-3 bg-rose-50 rounded-xl border border-rose-100 mb-4">
          <AlertTriangle className="w-4 h-4 text-rose-500 flex-shrink-0" />
          <span className="text-sm text-rose-700 font-medium">预估总风险：{doc.total_estimated_risk}</span>
        </div>
      )}

      {/* Risk items */}
      {risks.length > 0 ? (
        <div className="space-y-3">
          {risks.map((risk: any) => {
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
                  <p className="text-xs text-slate-500 italic mb-2"><span className="font-semibold text-slate-700">原文：</span>「{risk.original_text}」</p>
                )}
                {risk.critique && (
                  <p className="text-sm text-slate-700 leading-relaxed mb-2"><span className="font-semibold text-slate-700">风险分析：</span>{risk.critique}</p>
                )}
                {risk.financial_consequence && (
                  <div className="flex items-center gap-1.5 text-sm text-rose-600 font-medium mb-1">
                    <DollarSign className="w-3.5 h-3.5" />
                    财务影响：{risk.financial_consequence}
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
                <span className="font-semibold text-amber-700">⚠ 问题分析：</span>{item.critique}
              </p>
            </div>
          )}

          {item.trap_explanation && (
            <div className="mt-3 p-3 bg-red-50/80 rounded-xl border border-red-100/80">
              <p className="text-xs text-slate-600">
                <span className="font-semibold text-red-700">⛔ 陷阱说明：</span>{item.trap_explanation}
              </p>
            </div>
          )}

          <div className="mt-3 p-3 bg-green-50/50 rounded-xl border border-green-100/50">
            <p className="text-xs text-slate-600">
              <span className="font-semibold text-green-700">✓ 建议：</span>{item.suggestion}
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