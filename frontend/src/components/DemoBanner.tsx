import { Info } from 'lucide-react'

function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
    </svg>
  )
}

export default function DemoBanner() {
  const isDemo =
    import.meta.env.VITE_DEMO_MODE === 'true' ||
    import.meta.env.VITE_DEMO_MODE === '1'

  if (!isDemo) return null

  return (
    <div className="sticky top-0 z-[60] bg-gradient-to-r from-blue-600/95 via-indigo-600/95 to-blue-600/95 backdrop-blur-md text-white shadow-lg shadow-blue-900/20 min-h-[42px]">
      <div className="max-w-7xl mx-auto px-4 h-[42px] flex items-center justify-center gap-2 md:gap-3 text-xs md:text-sm flex-nowrap whitespace-nowrap overflow-hidden">
        <Info className="w-4 h-4 flex-shrink-0 opacity-80" />
        <span className="truncate">
          🧪 当前为<strong className="font-semibold">演示模式</strong>
          <span className="hidden sm:inline">，分析报告数据源自真实装修案例，仅供体验参考</span>
        </span>
        <a
          href="https://github.com/fthux/RenoPit"
          target="_blank"
          rel="noopener noreferrer"
          className="flex-shrink-0 inline-flex items-center gap-1.5 px-2 md:px-3 py-1 rounded-lg bg-white/15 hover:bg-white/25 text-white text-xs font-medium transition-all hover:scale-[1.02] no-underline"
        >
          <GitHubIcon className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">体验完整功能</span>
          <span className="sm:hidden">体验</span>
        </a>
      </div>
    </div>
  )
}
