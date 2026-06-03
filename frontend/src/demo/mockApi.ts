// ═══════════════════════════════════════════════════════════════════════
// Mock API — intercepts fetch calls and returns hardcoded demo data
// ═══════════════════════════════════════════════════════════════════════

import {
  DEMO_PROJECT,
  DEMO_PROJECTS_LIST,
  DEMO_ANALYSIS_RESULT,
  DEMO_FILES,
  DEMO_IMAGES,
} from './demoData'

/// Prefix patterns to match — handles both the Vite dev proxy paths (/api/...)
/// and the proxied backend paths (http://localhost:8000/api/v1/...).
const PREFIXES = ['/api', 'http://localhost:8000/api/v1']

type MockHandler = (url: string, options?: RequestInit) => Response | null

/**
 * Normalize a URL to an API path by stripping protocol, host, port, and /api/v1 prefix.
 * e.g.
 *   /api/projects             → /projects
 *   /api/projects/123/files   → /projects/123/files
 *   http://localhost:8000/api/v1/projects → /projects
 */
function normalizePath(url: string): string | null {
  // Remove query string
  const path = url.split('?')[0]

  for (const prefix of PREFIXES) {
    if (path.startsWith(prefix)) {
      return path.slice(prefix.length) || '/'
    }
  }

  // Also try matching the full URL form http://.../api/v1/...
  const match = path.match(/https?:\/\/[^/]+\/api\/v1/)
  if (match) {
    return path.slice(match[0].length) || '/'
  }

  return null
}

/**
 * Try to match a normalized API path against a pattern, return the params if matched.
 * e.g. matchPath('/projects/123', '/projects/:id') => { id: '123' }
 */
function matchPath(normalized: string, pattern: string): Record<string, string> | null {
  const actualParts = normalized.split('/')
  const patternParts = pattern.split('/')
  if (actualParts.length !== patternParts.length) return null
  const params: Record<string, string> = {}
  for (let i = 0; i < patternParts.length; i++) {
    if (patternParts[i].startsWith(':')) {
      params[patternParts[i].slice(1)] = actualParts[i]
    } else if (patternParts[i] !== actualParts[i]) {
      return null
    }
  }
  return params
}

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const mockHandlers: MockHandler[] = [
  // -----------------------------------------------------------------------
  // GET /api/projects — list projects (must match GET method)
  // -----------------------------------------------------------------------
  (url, options) => {
    const path = normalizePath(url)
    if (path && matchPath(path, '/projects') && (!options || options.method === undefined || options.method === 'GET')) {
      return jsonResponse({
        projects: DEMO_PROJECTS_LIST,
        total: 1,
        page: 1,
        total_pages: 1,
      })
    }
    return null
  },

  // -----------------------------------------------------------------------
  // GET /api/projects/:id — get project detail
  // -----------------------------------------------------------------------
  (url, options) => {
    const path = normalizePath(url)
    const params = path && matchPath(path, '/projects/:id')
    if (params && (!options || options.method === undefined || options.method === 'GET')) {
      return jsonResponse(DEMO_PROJECT)
    }
    return null
  },

  // -----------------------------------------------------------------------
  // GET /api/projects/:id/files — list files
  // -----------------------------------------------------------------------
  (url) => {
    const path = normalizePath(url)
    const params = path && matchPath(path, '/projects/:id/files')
    if (params) {
      return jsonResponse(DEMO_FILES)
    }
    return null
  },

  // -----------------------------------------------------------------------
  // GET /api/projects/:id/images — list images
  // -----------------------------------------------------------------------
  (url) => {
    const path = normalizePath(url)
    const params = path && matchPath(path, '/projects/:id/images')
    if (params) {
      return jsonResponse(DEMO_IMAGES)
    }
    return null
  },

  // -----------------------------------------------------------------------
  // GET /api/projects/:id/result — get analysis result
  //   (AnalysisPage fetches /api/projects/:id/result)
  // -----------------------------------------------------------------------
  (url) => {
    const path = normalizePath(url)
    const params = path && matchPath(path, '/projects/:id/result')
    if (params) {
      return jsonResponse(DEMO_ANALYSIS_RESULT)
    }
    return null
  },

  // -----------------------------------------------------------------------
  // GET /api/projects/:id/analysis — get analysis result (alt pattern)
  // -----------------------------------------------------------------------
  (url) => {
    const path = normalizePath(url)
    const params = path && matchPath(path, '/projects/:id/analysis')
    if (params) {
      return jsonResponse(DEMO_ANALYSIS_RESULT)
    }
    return null
  },

  // -----------------------------------------------------------------------
  // GET /api/projects/:id/analysis/status — analysis status
  // -----------------------------------------------------------------------
  (url) => {
    const path = normalizePath(url)
    const params = path && matchPath(path, '/projects/:id/analysis/status')
    if (params) {
      return jsonResponse({ status: 'completed', progress: 100 })
    }
    return null
  },

  // -----------------------------------------------------------------------
  // POST /api/projects — create project (rejected in demo mode)
  // -----------------------------------------------------------------------
  (url, options) => {
    const path = normalizePath(url)
    if (path && matchPath(path, '/projects') && options?.method === 'POST') {
      return jsonResponse({ detail: 'Demo 模式下不支持创建项目，请去GitHub仓库下载源代码，启动后端服务后重试。' }, 400)
    }
    return null
  },

  // -----------------------------------------------------------------------
  // DELETE /api/projects/:id — delete project (returns success)
  // -----------------------------------------------------------------------
  (url, options) => {
    const path = normalizePath(url)
    const params = path && matchPath(path, '/projects/:id');
    if (params && options?.method === 'DELETE') {
      return jsonResponse({ detail: 'Demo 模式下不支持删除项目，请去GitHub仓库下载源代码，启动后端服务后重试。' }, 400)
    }
    return null
  },

  // -----------------------------------------------------------------------
  // POST /api/projects/:id/duplicate — duplicate project
  // -----------------------------------------------------------------------
  (url, options) => {
    const path = normalizePath(url)
    const params = path && matchPath(path, '/projects/:id/duplicate')
    if (params && options?.method === 'POST') {
      return jsonResponse({ detail: 'Demo 模式下不支持复制项目，请去GitHub仓库下载源代码，启动后端服务后重试。' }, 400)
    }
    return null
  },

  // -----------------------------------------------------------------------
  // POST /api/projects/:id/upload — upload files (returns success)
  // -----------------------------------------------------------------------
  (url, options) => {
    const path = normalizePath(url)
    const params = path && matchPath(path, '/projects/:id/upload')
    if (params && options?.method === 'POST') {
      return jsonResponse({ success: true })
    }
    return null
  },

  // -----------------------------------------------------------------------
  // POST /api/projects/:id/analyze — start analysis (rejected in demo mode)
  // -----------------------------------------------------------------------
  (url, options) => {
    const path = normalizePath(url)
    const params = path && matchPath(path, '/projects/:id/analyze')
    if (params && options?.method === 'POST') {
      return jsonResponse({ detail: 'Demo 模式下不支持启动分析，请去GitHub仓库下载源代码，启动后端服务后重试。' }, 400)
    }
    return null
  },

  // -----------------------------------------------------------------------
  // GET /api/projects/:id/report/pdf — download PDF report (unavailable in demo mode)
  // -----------------------------------------------------------------------
  (url) => {
    const path = normalizePath(url)
    const params = path && matchPath(path, '/projects/:id/report/pdf')
    if (params) {
      return jsonResponse({ detail: 'Demo 模式下不支持下载 PDF 报告，请去GitHub仓库下载源代码，启动后端服务后重试。' }, 400)
    }
    return null
  },

  // -----------------------------------------------------------------------
  // GET /api/projects/:id — also match /api/projects/:id (no trailing)
  // Already covered by the :id handler above
  // -----------------------------------------------------------------------
]

export function enableMockApi() {
  const originalFetch = window.fetch.bind(window)

  window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url

    // Try mock handlers first
    for (const handler of mockHandlers) {
      const mockResponse = handler(url, init)
      if (mockResponse) {
        // Simulate network delay for realism
        await new Promise((r) => setTimeout(r, 200))
        return mockResponse
      }
    }

    // Fall through to real fetch for non-mocked URLs
    return originalFetch(input, init)
  }

  console.log('[Demo Mode] Mock API enabled. All requests return hardcoded demo data.')
}

export function disableMockApi() {
  // Reload to restore original fetch
  window.location.reload()
}