import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronRight, Shield, Sparkles, Zap, ArrowRight, Layers, BarChart3, FileText } from 'lucide-react'

export default function LandingPage() {
  const navigate = useNavigate()
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const features = [
    {
      icon: Zap,
      title: 'AI 智能检测',
      desc: '上传设计图纸或现场照片，AI 自动识别装修陷阱与施工隐患',
    },
    {
      icon: Shield,
      title: '全面覆盖',
      desc: '涵盖结构安全、水电隐蔽工程、防水防潮、消防规范等 40+ 大类',
    },
    {
      icon: BarChart3,
      title: '量化评分',
      desc: '基于权威标准对设计方案进行综合评分，一目了然风险等级',
    },
    {
      icon: Layers,
      title: '多格式支持',
      desc: '支持 DXF / DWG / PDF 图纸、现场照片、文本描述等多种输入',
    },
    {
      icon: FileText,
      title: '专业报告',
      desc: '自动生成包含全文批注的 PDF 报告，方便与设计师、施工方沟通',
    },
    {
      icon: Sparkles,
      title: '持续优化',
      desc: '持续更新行业标准与法规库，确保检测结果与时俱进',
    },
  ]

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white overflow-hidden">
      {/* Animated background orbs */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] rounded-full bg-gradient-to-br from-blue-500/10 via-purple-500/8 to-transparent blur-[100px] animate-pulse-slow" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full bg-gradient-to-tl from-cyan-500/10 via-blue-500/8 to-transparent blur-[100px] animate-pulse-slow animation-delay-2000" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full bg-gradient-to-r from-indigo-500/8 via-purple-500/5 to-transparent blur-[120px]" />
      </div>

      {/* Navbar */}
      <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${scrolled ? 'bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-white/5' : 'bg-transparent'
        }`}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold shadow-lg shadow-blue-500/20">
              装
            </div>
            <span className="text-lg font-bold tracking-tight">
              <span className="text-white">装</span>
              <span className="text-blue-400">闭</span>
            </span>
          </div>
          <nav className="flex items-center gap-4">
            <button
              onClick={() => navigate('/projects')}
              className="text-sm text-gray-400 hover:text-white transition-colors px-4 py-2"
            >
              项目列表
            </button>
            <button
              onClick={() => navigate('/projects')}
              className="text-sm font-medium px-5 py-2 rounded-xl bg-white text-[#0a0a0f] hover:bg-gray-200 transition-all duration-300 shadow-lg shadow-white/10 hover:shadow-white/20 hover:scale-[1.02] active:scale-[0.98]"
            >
              开始使用
            </button>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm text-gray-400 mb-8 backdrop-blur-sm">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>AI 驱动的装修陷阱检测引擎</span>
          </div>

          {/* Title */}
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-6 leading-[1.1]">
            <span className="text-white">装修</span>
            <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">闭坑</span>
            <br />
            <span className="text-3xl md:text-4xl lg:text-5xl text-gray-400 font-normal">
              用 <span className="text-white font-bold">"装闭"</span> 就够了
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            上传你的装修设计图纸，AI 将在数分钟内完成全面检测，
            <br className="hidden md:block" />
            识别安全隐患、施工陷阱与不合规设计，并生成专业报告。
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => navigate('/projects')}
              className="group relative px-8 py-4 rounded-2xl bg-white text-[#0a0a0f] font-semibold text-lg transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] shadow-2xl shadow-white/20 hover:shadow-white/30"
            >
              <span className="flex items-center gap-2">
                开始检测
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </span>
            </button>
            <button
              onClick={() => navigate('/projects')}
              className="px-8 py-4 rounded-2xl border border-white/10 text-gray-300 font-medium text-lg transition-all duration-300 hover:bg-white/5 hover:border-white/20 hover:text-white backdrop-blur-sm"
            >
              查看项目列表
            </button>
          </div>

          {/* Stats */}
          <div className="mt-16 grid grid-cols-3 gap-8 max-w-lg mx-auto">
            {[
              { value: '40+', label: '检测类别' },
              { value: '500+', label: '法规标准' },
              { value: '99%', label: '准确率' },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-2xl md:text-3xl font-bold text-white mb-1">{stat.value}</div>
                <div className="text-xs md:text-sm text-gray-500">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative z-10 py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                全方位装修检测
              </span>
            </h2>
            <p className="text-gray-500 text-lg max-w-2xl mx-auto">
              从结构安全到施工细节，AI 帮你把好每一道关
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map((feat, i) => {
              const Icon = feat.icon
              return (
                <div
                  key={i}
                  className="group relative p-6 rounded-2xl border border-white/5 bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/10 transition-all duration-500"
                >
                  {/* Hover glow effect */}
                  <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br from-blue-500/5 via-transparent to-purple-500/5 pointer-events-none" />

                  <div className="relative z-10">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/5 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-500">
                      <Icon className="w-5 h-5 text-blue-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">{feat.title}</h3>
                    <p className="text-sm text-gray-400 leading-relaxed">{feat.desc}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="relative z-10 py-24 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-4 text-white">
              三步完成检测
            </h2>
            <p className="text-gray-500 text-lg">简单三步，即可获得专业的装修陷阱分析报告</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '01', title: '上传文件', desc: '上传设计图纸（DXF/PDF）、现场照片或直接输入文字描述', color: 'from-blue-500/20 to-blue-600/10' },
              { step: '02', title: 'AI 分析', desc: 'AI 自动解析图纸和照片，逐项检测潜在陷阱与安全隐患', color: 'from-purple-500/20 to-purple-600/10' },
              { step: '03', title: '获取报告', desc: '获得详细的检测报告与综合评分，支持下载 PDF 版本', color: 'from-pink-500/20 to-pink-600/10' },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className={`w-16 h-16 rounded-full bg-gradient-to-br ${item.color} border border-white/5 flex items-center justify-center mx-auto mb-5`}>
                  <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">{item.step}</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-sm text-gray-400 max-w-xs mx-auto">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 py-24 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl md:text-5xl font-bold mb-6 text-white">
            准备好开始了吗？
          </h2>
          <p className="text-gray-400 text-lg mb-8">
            上传你的装修设计，让 AI 帮你规避风险，安心装修
          </p>
          <button
            onClick={() => navigate('/projects')}
            className="group inline-flex items-center gap-2 px-8 py-4 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold text-lg transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] shadow-xl shadow-blue-500/20 hover:shadow-blue-500/30"
          >
            立即开始
            <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 py-8 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">装</div>
            装闭 — 装修闭坑利器
          </div>
          <p className="text-sm text-gray-600">
            Powered by AI · 仅供参考，最终以专业设计师意见为准
          </p>
        </div>
      </footer>
    </div>
  )
}