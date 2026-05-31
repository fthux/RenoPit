import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Sparkles, Zap, ArrowRight, Layers, BarChart3, FileText, Target, Users, Quote, Eye, BookOpen, Star } from 'lucide-react'

function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
    </svg>
  )
}

function useScrollReveal() {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed')
          }
        })
      },
      { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
    )

    const elements = document.querySelectorAll('.scroll-reveal')
    elements.forEach((el) => observer.observe(el))

    return () => observer.disconnect()
  }, [])
}

export default function LandingPage() {
  const navigate = useNavigate()
  const [scrolled, setScrolled] = useState(false)

  useScrollReveal()

  useEffect(() => {
    document.title = '装闭 — 站在消费者一边的AI装修闭坑分析器'
  }, [])

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const scrollToSection = useCallback((id: string) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' })
    }
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
      desc: '支持设计图纸（PDF/图片）、现场照片、文档附件等多种输入',
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

      {/* Navbar */}
      <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${scrolled ? 'bg-[#0a0a0f]/80 backdrop-blur-xl shadow-[0_1px_0_0_rgba(255,255,255,0.05)] will-change-transform' : 'bg-transparent'
        }`}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <img src="/favicon.svg" alt="装闭" className="w-8 h-8" />
            <span className="text-lg font-bold tracking-tight">
              <span className="text-white">装闭</span>
            </span>
          </div>
          {/* Centered nav links - visible on md+ screens */}
          <nav className="hidden md:flex absolute left-1/2 -translate-x-1/2 items-center gap-6">
            <button
              onClick={() => scrollToSection('get-started')}
              className="text-sm text-gray-400 hover:text-white transition-colors px-4 py-2 cursor-pointer"
            >
              开始使用
            </button>
            <button
              onClick={() => scrollToSection('introduction')}
              className="text-sm text-gray-400 hover:text-white transition-colors px-4 py-2 cursor-pointer"
            >
              功能介绍
            </button>
            <button
              onClick={() => scrollToSection('about-us')}
              className="text-sm text-gray-400 hover:text-white transition-colors px-4 py-2 cursor-pointer"
            >
              关于我们
            </button>
          </nav>

          {/* Right side action buttons */}
          <div className="flex items-center gap-2 md:gap-3">
            <button
              onClick={() => window.open('https://deepwiki.com/fthux/RenovationPitfallAnalyzer', '_blank')}
              className="text-sm text-gray-400 hover:text-white transition-colors px-3 md:px-4 py-2 cursor-pointer inline-flex items-center gap-1.5"
            >
              <BookOpen className="w-4 h-4" />
              <span className="hidden sm:inline">文档</span>
            </button>
            <button
              onClick={() => window.open('https://github.com/fthux/RenovationPitfallAnalyzer', '_blank')}
              className="text-sm font-medium px-4 md:px-5 py-2 rounded-xl bg-white text-[#0a0a0f] hover:bg-gray-200 transition-all duration-300 shadow-lg shadow-white/10 hover:shadow-white/20 hover:scale-[1.02] active:scale-[0.98] cursor-pointer inline-flex items-center gap-1.5"
            >
              <GitHubIcon className="w-4 h-4" />
              <span className="hidden sm:inline">GitHub</span>
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section id="get-started" className="relative z-10 pt-24 md:pt-32 pb-16 md:pb-20 px-4 md:px-6">
        <div className="max-w-5xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm text-gray-400 mb-8 backdrop-blur-sm">
            <Sparkles className="w-3.5 h-3.5 text-white/60" />
            <span>站在消费者一边的AI装修闭坑分析器</span>
          </div>

          {/* Title */}
          <h1 className="text-4xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-6 leading-[1.1]">
            <span className="text-white">装修</span>
            <span className="text-white">闭坑</span>
            <br />
            <span className="text-xl md:text-4xl lg:text-5xl text-gray-400 font-normal">
              用 <span className="text-white">"</span><ruby className="text-white font-bold">装<rt className="text-[0.4em] font-normal tracking-wide">zhuāng</rt></ruby><ruby className="text-white font-bold">闭<rt className="text-[0.4em] font-normal tracking-wide">bì</rt></ruby><span className="text-white">"</span> 就够了
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-base md:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed px-2">
            上传你的设计图纸，AI 自动揪出那些只为增加预算的"垃圾设计"、
            <br className="hidden md:block" />
            过度装修、卫生死角、空间压迫感，揭露装修公司套路，给出更实用的方案。
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 md:gap-4">
            <button
              onClick={() => navigate('/projects/new')}
              className="group relative px-8 py-4 rounded-2xl bg-white text-[#0a0a0f] font-semibold text-lg transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] shadow-2xl shadow-white/20 hover:shadow-white/30 cursor-pointer"
            >
              <span className="flex items-center gap-2">
                免费检测
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </span>
            </button>
            <button
              onClick={() => window.open('https://github.com/fthux/RenovationPitfallAnalyzer', '_blank')}
              className="px-8 py-4 rounded-2xl border border-white/10 text-gray-300 font-medium text-lg transition-all duration-300 hover:bg-white/5 hover:border-white/20 hover:text-white backdrop-blur-sm cursor-pointer inline-flex items-center gap-2"
            >
              <Star className="w-5 h-5 text-yellow-400" />
              Star on GitHub
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="introduction" className="relative z-10 py-16 md:py-24 px-4 md:px-6">
        <div className="max-w-6xl mx-auto">
          <div className="scroll-reveal text-center mb-12 md:mb-16">
            <h2 className="text-2xl md:text-5xl font-bold mb-4">
              <span className="text-white">
                揭露套路，回归实用
              </span>
            </h2>
            <p className="text-gray-500 text-lg max-w-2xl mx-auto">
              装修公司和设计师的每一个增项、每一个"高级设计"，背后可能都是你的血汗钱
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-5">
            {features.map((feat, i) => {
              const Icon = feat.icon
              return (
                <div
                  key={i}
                  className="scroll-reveal group relative p-6 rounded-2xl border border-white/5 bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/10 transition-all duration-500"
                  style={{ transitionDelay: `${i * 100}ms` }}
                >
                  <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-white/[0.03] pointer-events-none" />

                  <div className="relative z-10">
                    <div className="w-10 h-10 rounded-xl bg-white/10 border border-white/5 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-500">
                      <Icon className="w-5 h-5 text-white/60" />
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
      <section className="relative z-10 py-16 md:py-24 px-4 md:px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <div className="scroll-reveal text-center mb-12 md:mb-16">
            <h2 className="text-2xl md:text-5xl font-bold mb-4 text-white">
              三步揪出垃圾设计
            </h2>
            <p className="text-gray-500 text-lg">上传图纸，AI 替你逐项审查，揭露每一个坑</p>
          </div>

          <div className="grid sm:grid-cols-3 gap-6 md:gap-8">
            {[
              { step: '01', title: '上传图纸', desc: '上传你的设计图纸（PDF/图片）、现场照片，或直接描述你的装修需求' },
              { step: '02', title: 'AI 逐项审查', desc: 'AI 对照本地知识库和行业标准，逐项筛查卫生死角、空间压迫、增项陷阱等' },
              { step: '03', title: '拿到避坑报告', desc: '获得详细的检测报告与综合评分，每个问题都附带替代方案，支持下载 PDF' },
            ].map((item, i) => (
              <div key={item.step} className="scroll-reveal text-center" style={{ transitionDelay: `${i * 200}ms` }}>
                <div className="w-16 h-16 rounded-full bg-white/10 border border-white/5 flex items-center justify-center mx-auto mb-5">
                  <span className="text-2xl font-bold text-white">{item.step}</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-sm text-gray-400 max-w-xs mx-auto">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* About Us Section */}
      <section id="about-us" className="relative z-10 py-16 md:py-24 px-4 md:px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <div className="scroll-reveal text-center mb-12 md:mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm text-gray-400 mb-6 backdrop-blur-sm">
              <Users className="w-3.5 h-3.5 text-white/60" />
              <span>关于我们</span>
            </div>
            <h2 className="text-2xl md:text-5xl font-bold mb-4 text-white">
              你的家，不该为别人的利润买单
            </h2>
            <p className="text-gray-400 text-lg max-w-3xl mx-auto leading-relaxed">
              装修行业充斥着为了增加预算而设计的"垃圾设计"——复杂的吊顶、积灰的开放格、
              只是为了好看的雕花隔断、用不了几次的嵌入式家电……设计师和装修公司赚得盆满钵满，
              而你却要为此多付几十万，还要在未来几十年里忍受家务负担。
            </p>
          </div>

          <div className="grid sm:grid-cols-3 gap-4 md:gap-6">
            <div className="scroll-reveal delay-100 group p-6 rounded-2xl border border-white/5 bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/10 transition-all duration-500">
              <div className="w-10 h-10 rounded-xl bg-white/10 border border-white/5 flex items-center justify-center mb-4">
                <Target className="w-5 h-5 text-white/60" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">只站消费者</h3>
              <p className="text-sm text-gray-400 leading-relaxed">
                我们完全站在业主一边。每一个分析都默认质疑那些"高端设计"和"常见增项"，
                将你的长期居住体验和实际需求放在首位，而不是设计师的审美和装修公司的利润。
              </p>
            </div>

            <div className="scroll-reveal delay-200 group p-6 rounded-2xl border border-white/5 bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/10 transition-all duration-500">
              <div className="w-10 h-10 rounded-xl bg-white/10 border border-white/5 flex items-center justify-center mb-4">
                <Eye className="w-5 h-5 text-white/60" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">揭露套路</h3>
              <p className="text-sm text-gray-400 leading-relaxed">
                每一项"复杂设计"背后都藏着装修公司的商业套路。我们帮你把这些套路一一拆穿——
                从材料以次充好到虚报面积，从过度设计到伪需求，让每一分钱都花在刀刃上。
              </p>
            </div>

            <div className="scroll-reveal delay-300 group p-6 rounded-2xl border border-white/5 bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/10 transition-all duration-500">
              <div className="w-10 h-10 rounded-xl bg-white/10 border border-white/5 flex items-center justify-center mb-4">
                <Quote className="w-5 h-5 text-white/60" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">实用至上</h3>
              <p className="text-sm text-gray-400 leading-relaxed">
                指出问题的同时，我们给出更实用、更经济的替代方案。不搞花架子，
                只做真正对业主有用的检测——把省下来的钱用在提升生活品质上，而不是喂饱装修公司。
              </p>
            </div>
          </div>

          <div className="scroll-reveal mt-12 text-center">
            <div className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-white/5 border border-white/10 text-gray-400 text-sm backdrop-blur-sm">
              <span>装修闭坑，用"装闭"就够了</span>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 py-6 md:py-8 px-4 md:px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3 md:gap-4 text-center md:text-left">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <img src="/favicon.svg" alt="装闭" className="w-6 h-6" />
            装闭 — 站在消费者一边的AI装修闭坑分析器
          </div>
          <p className="text-sm text-gray-600">
            Powered by AI · 不做中立审查，只做消费者代言人
          </p>
        </div>
      </footer>
    </div>
  )
}