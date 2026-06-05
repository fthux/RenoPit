"""
健康检查 API — 可视化的系统健康检查仪表盘
GET /health      → HTML 仪表盘页面
GET /health/data → JSON 检查结果
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from ..services.health_checker import run_all_checks

router = APIRouter(tags=["Health"])


@router.get("/health/data")
async def health_data():
    """返回健康检查的 JSON 数据"""
    return await run_all_checks()


HEALTH_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <title>RenoPit — 系统健康检查</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text: #e2e8f0;
      --text-secondary: #94a3b8;
      --ok: #22c55e;
      --error: #ef4444;
      --warning: #f59e0b;
      --accent: #3b82f6;
      --header-bg: #1a2332;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans SC", sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      line-height: 1.6;
    }
    .container { max-width: 1280px; margin: 0 auto; padding: 24px 32px; }
    .header {
      background: var(--header-bg);
      border-bottom: 1px solid var(--border);
      padding: 24px 32px;
      margin-bottom: 32px;
    }
    .header-inner { max-width: 1280px; margin: 0 auto; }
    .header h1 { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
    .header .subtitle { color: var(--text-secondary); font-size: 14px; }
    
    .status-badge {
      display: inline-flex; align-items: center; gap: 8px;
      padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 14px;
    }
    .status-badge.healthy { background: rgba(34,197,94,0.15); color: var(--ok); }
    .status-badge.degraded { background: rgba(245,158,11,0.15); color: var(--warning); }
    .status-badge.unhealthy { background: rgba(239,68,68,0.15); color: var(--error); }
    .status-dot {
      width: 8px; height: 8px; border-radius: 50%;
      display: inline-block;
    }
    .status-dot.ok { background: var(--ok); box-shadow: 0 0 6px var(--ok); }
    .status-dot.error { background: var(--error); box-shadow: 0 0 6px var(--error); }
    .status-dot.warning { background: var(--warning); box-shadow: 0 0 6px var(--warning); }

    .section { margin-bottom: 32px; }
    .section-title {
      font-size: 16px; font-weight: 600; color: var(--text-secondary);
      text-transform: uppercase; letter-spacing: 0.5px;
      padding-bottom: 10px; border-bottom: 1px solid var(--border);
      margin-bottom: 12px;
      display: flex; align-items: center; gap: 8px;
    }
    .section-title .icon { font-size: 18px; }
    
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }
    .card table { width: 100%; border-collapse: collapse; }
    .card th {
      text-align: left; padding: 10px 16px;
      font-size: 12px; font-weight: 600; color: var(--text-secondary);
      text-transform: uppercase; letter-spacing: 0.3px;
      background: rgba(0,0,0,0.2);
      border-bottom: 1px solid var(--border);
    }
    .card td {
      padding: 12px 16px; font-size: 14px;
      border-bottom: 1px solid rgba(51,65,85,0.4);
    }
    .card tr:last-child td { border-bottom: none; }
    .card tr:hover td { background: rgba(255,255,255,0.02); }

    .check-name { font-weight: 500; }
    .check-status {
      display: inline-flex; align-items: center; gap: 6px;
      font-weight: 600; font-size: 13px;
    }
    .check-status.ok { color: var(--ok); }
    .check-status.error { color: var(--error); }
    .check-status.warning { color: var(--warning); }
    .check-detail { color: var(--text-secondary); font-size: 13px; word-break: break-all; }

    .extra-tags { display: flex; flex-wrap: wrap; gap: 6px; }
    .extra-tag {
      padding: 2px 8px; border-radius: 4px;
      font-size: 11px; font-weight: 500;
      background: rgba(59,130,246,0.1); color: #93c5fd;
      border: 1px solid rgba(59,130,246,0.2);
    }
    .extra-tag.warn {
      background: rgba(245,158,11,0.1); color: #fcd34d;
      border: 1px solid rgba(245,158,11,0.2);
    }
    .extra-tag.err {
      background: rgba(239,68,68,0.1); color: #fca5a5;
      border: 1px solid rgba(239,68,68,0.2);
    }

    .footer {
      text-align: center; padding: 24px;
      color: var(--text-secondary); font-size: 12px;
    }
    .refresh-btn {
      background: var(--accent); color: white; border: none;
      padding: 8px 20px; border-radius: 6px; cursor: pointer;
      font-size: 14px; font-weight: 500;
      transition: opacity 0.2s;
    }
    .refresh-btn:hover { opacity: 0.85; }
    .header-row { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; }

    .spinner {
      display: inline-block; width: 14px; height: 14px;
      border: 2px solid var(--text-secondary);
      border-top-color: transparent; border-radius: 50%;
      animation: spin 0.6s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    .latency { font-variant-numeric: tabular-nums; color: var(--text-secondary); font-size: 12px; }

    /* ===== Mobile Card Layout ===== */
    .mobile-cards { display: none; }

    .check-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px 16px;
    }
    .check-card-header {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 10px; gap: 8px;
    }
    .check-card-name { font-weight: 600; font-size: 14px; }
    .check-card-body { display: flex; flex-direction: column; gap: 8px; }
    .check-card-row { display: flex; flex-direction: column; gap: 2px; }
    .check-card-label { font-size: 11px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.3px; }
    .check-card-value { font-size: 13px; word-break: break-all; }

    /* ===== Mobile Responsive ===== */
    @media (max-width: 768px) {
      .container { padding: 16px 12px; }
      .header { padding: 16px 12px; margin-bottom: 16px; }
      .header h1 { font-size: 20px; }
      .header .subtitle { font-size: 13px; }
      .header-row { flex-direction: column; gap: 10px; }
      .section { margin-bottom: 20px; }
      .section-title { font-size: 14px; }

      .card table { display: none; }
      .mobile-cards { display: flex; flex-direction: column; gap: 10px; }

      .refresh-btn { padding: 6px 14px; font-size: 13px; }
      .status-badge { font-size: 12px; padding: 4px 12px; }
      .footer { padding: 16px 12px; font-size: 11px; }
    }

    @media (max-width: 480px) {
      .header h1 { font-size: 18px; }
      .container { padding: 12px 8px; }
      .header { padding: 12px 8px; margin-bottom: 12px; }
      .section { margin-bottom: 16px; }
      .check-card { padding: 12px 14px; }
      .extra-tag { font-size: 10px; padding: 1px 6px; }
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="header-inner">
      <div class="header-row">
        <div>
          <h1>🔍 RenoPit 系统健康检查</h1>
          <div class="subtitle">实时监控所有系统依赖与组件状态</div>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
          <span id="overall-badge" class="status-badge">
            <span class="spinner"></span> 检查中...
          </span>
          <button class="refresh-btn" onclick="loadHealth()">刷新</button>
        </div>
      </div>
      <div style="margin-top:12px;font-size:13px;color:var(--text-secondary);">
        检查时间: <span id="timestamp">—</span>
        &nbsp;|&nbsp; 运行时间: <span id="uptime">—</span>
      </div>
    </div>
  </div>

  <div class="container" id="content">
    <div style="text-align:center;padding:60px;color:var(--text-secondary);">
      <span class="spinner"></span> 正在执行系统检查...
    </div>
  </div>

  <div class="footer">RenoPit v0.1.0 &mdash; Health Check Dashboard</div>

  <script>
    let uptimeTimer = null;
    let baseUptime = 0;
    let baseTimestamp = 0;

    const STATUS_ICON = { ok: '✅', error: '❌', warning: '⚠️' };
    const STATUS_LABEL = { ok: '正常', error: '异常', warning: '警告' };
    const SECTION_GROUPS = {
      core: { title: '📦 核心依赖', icon: '📦', keys: ['database', 'redis', 'filesystem'] },
      business: { title: '🔧 业务依赖', icon: '🔧', keys: ['llm_api', 'celery', 'application_data'] },
      info: { title: '📊 系统信息', icon: '📊', keys: ['runtime', 'network'] },
    };

    function renderExtra(key, extra) {
      if (!extra || Object.keys(extra).length === 0) return '';
      const tags = [];
      for (const [k, v] of Object.entries(extra)) {
        let val = v;
        if (typeof v === 'boolean') val = v ? '✓' : '✗';
        else if (typeof v === 'number' && v === -1) val = 'N/A';
        else if (typeof v === 'number') val = v.toLocaleString();
        else if (v === null || v === undefined) val = '—';
        tags.push(`<span class="extra-tag">${k}: ${val}</span>`);
      }
      return `<div class="extra-tags">${tags.join('')}</div>`;
    }

    function renderCheck(check) {
      const icon = STATUS_ICON[check.status] || '❓';
      const label = STATUS_LABEL[check.status] || check.status;
      const latencyHtml = check.latency_ms > 0 ? `<span class="latency">${check.latency_ms}ms</span>` : '';
      return `
        <tr>
          <td class="check-name">${icon} ${check.name}</td>
          <td><span class="check-status ${check.status}">${label}</span>${latencyHtml ? ' ' + latencyHtml : ''}</td>
          <td class="check-detail">${check.detail || '—'}</td>
          <td>${renderExtra(check.name, check.extra)}</td>
        </tr>
      `;
    }

    function renderCheckCard(check) {
      const icon = STATUS_ICON[check.status] || '❓';
      const label = STATUS_LABEL[check.status] || check.status;
      const latencyHtml = check.latency_ms > 0 ? `<span class="latency">${check.latency_ms}ms</span>` : '';
      const extraHtml = renderExtra(check.name, check.extra);
      return `
        <div class="check-card">
          <div class="check-card-header">
            <span class="check-card-name">${icon} ${check.name}</span>
            <span class="check-status ${check.status}">${label}${latencyHtml ? ' ' + latencyHtml : ''}</span>
          </div>
          <div class="check-card-body">
            <div class="check-card-row">
              <span class="check-card-label">详情</span>
              <span class="check-card-value">${check.detail || '—'}</span>
            </div>
            ${extraHtml ? '<div class="check-card-row"><span class="check-card-label">诊断数据</span><div class="check-card-value">' + extraHtml + '</div></div>' : ''}
          </div>
        </div>
      `;
    }

    function renderSection(title, checks) {
      return `
        <div class="section">
          <div class="section-title">${title}</div>
          <div class="card">
            <table>
              <thead><tr><th style="width:200px">检查项</th><th style="width:120px">状态</th><th>详情</th><th>诊断数据</th></tr></thead>
              <tbody>${checks.map(renderCheck).join('')}</tbody>
            </table>
            <div class="mobile-cards">${checks.map(renderCheckCard).join('')}</div>
          </div>
        </div>
      `;
    }

    function setBadge(status) {
      const badge = document.getElementById('overall-badge');
      badge.className = 'status-badge ' + status;
      const icons = { healthy: '✅', degraded: '⚠️', unhealthy: '❌' };
      const labels = { healthy: '系统健康', degraded: '部分降级', unhealthy: '系统异常' };
      badge.innerHTML = `<span class="status-dot ${status}"></span>${icons[status] || ''} ${labels[status] || status}`;
    }

    function renderDashboard(data) {
      document.getElementById('timestamp').textContent = data.timestamp
        ? new Date(data.timestamp).toLocaleString('zh-CN')
        : '—';
      baseUptime = data.uptime_seconds || 0;
      baseTimestamp = Date.now();
      updateUptimeDisplay();
      if (uptimeTimer) clearInterval(uptimeTimer);
      uptimeTimer = setInterval(updateUptimeDisplay, 1000);

      setBadge(data.status || 'unknown');

      const checks = data.checks || {};
      const html = [];

      for (const [groupKey, group] of Object.entries(SECTION_GROUPS)) {
        const groupChecks = group.keys
          .filter(k => checks[k])
          .map(k => checks[k]);
        if (groupChecks.length > 0) {
          html.push(renderSection(group.title, groupChecks));
        }
      }

      document.getElementById('content').innerHTML = html.join('') || '<p>无检查数据</p>';
    }

    function updateUptimeDisplay() {
      const elapsed = Math.floor((Date.now() - baseTimestamp) / 1000);
      const total = baseUptime + elapsed;
      const h = Math.floor(total / 3600);
      const m = Math.floor((total % 3600) / 60);
      const s = total % 60;
      document.getElementById('uptime').textContent = `${h}h ${m}m ${s}s`;
    }

    async function loadHealth() {
      document.getElementById('content').innerHTML =
        '<div style="text-align:center;padding:60px;color:var(--text-secondary);"><span class="spinner"></span> 正在执行系统检查...</div>';
      try {
        const resp = await fetch('/health/data');
        const data = await resp.json();
        renderDashboard(data);
      } catch (err) {
        document.getElementById('content').innerHTML =
          `<div style="text-align:center;padding:60px;color:var(--error);">❌ 检查失败: ${err.message}</div>`;
      }
    }

    loadHealth();
  </script>
</body>
</html>
"""


@router.get("/health", include_in_schema=False)
async def health_dashboard():
    """健康检查仪表盘 HTML 页面"""
    return HTMLResponse(HEALTH_DASHBOARD_HTML)