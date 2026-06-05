"""
RenoPit — FastAPI Application
装修避坑分析器 后端入口
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
import os

from .core.database import engine, Base
from .api import projects_router
from .api.health import router as health_router

app = FastAPI(
    title="RenoPit",
    description="装修设计图避坑分析器 API",
    version="0.1.0",
    redoc_url=None,  # 禁用默认 Redoc（CDN @next tag 已失效），用自定义路由替代
    docs_url=None,  # 禁用默认 /docs，用自定义路由替代
)

# CORS — 开发阶段允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(projects_router)
app.include_router(health_router)


@app.on_event("startup")
async def startup():
    """启动时自动创建所有数据库表（开发阶段使用，生产环境用 Alembic 迁移）"""
    # 确保所有模型已导入才能被 Base.metadata 发现
    from .models import Project, ProjectImage, ProjectFile, Analysis, DocumentAnalysis, Report  # noqa: F401
    Base.metadata.create_all(bind=engine)


SWAGGER_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <title>RenoPit — Swagger UI</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
  <style>
    html { box-sizing: border-box; overflow-y: scroll; }
    *, *:before, *:after { box-sizing: inherit; }
    body { margin: 0; background: #fafafa; }

    /* Desktop: normal Swagger UI layout */

    /* Mobile: make swagger sidebar and content stack vertically */
    @media (max-width: 768px) {
      .swagger-ui .wrapper { padding: 0 10px; }
      .swagger-ui .scheme-container { padding: 10px; }
      .swagger-ui .opblock-tag { font-size: 18px; }
      .swagger-ui .opblock .opblock-summary { padding: 8px; }
      .swagger-ui .opblock .opblock-summary-description { font-size: 13px; }
      .swagger-ui .opblock .opblock-summary-path { font-size: 12px; word-break: break-all; }
      .swagger-ui .opblock .opblock-summary-method { min-width: 60px; font-size: 12px; padding: 4px 8px; }
      .swagger-ui .opblock-body pre.microlight { font-size: 11px; max-height: 200px; }
      .swagger-ui table thead tr td, .swagger-ui table thead tr th { font-size: 11px; padding: 6px 4px; }
      .swagger-ui table tbody tr td { font-size: 11px; padding: 6px 4px; }
      .swagger-ui .parameter__name { font-size: 12px; }
      .swagger-ui .parameter__type { font-size: 11px; }
      .swagger-ui .response-col_status { font-size: 12px; }
      .swagger-ui .response-col_description { font-size: 12px; }
      .swagger-ui .responses-inner h4 { font-size: 13px; }
      .swagger-ui .info .title { font-size: 24px; }
      .swagger-ui .info { margin: 20px 0; }
      .swagger-ui .btn { padding: 4px 12px; font-size: 12px; }
      .swagger-ui select { font-size: 12px; }
      .swagger-ui .model-box { font-size: 12px; }
      .swagger-ui section.models h4 { font-size: 14px; }
    }

    @media (max-width: 480px) {
      .swagger-ui .wrapper { padding: 0 6px; }
      .swagger-ui .opblock-tag { font-size: 16px; }
      .swagger-ui .opblock .opblock-summary-description { font-size: 12px; }
      .swagger-ui .opblock .opblock-summary-path { font-size: 11px; }
      .swagger-ui .opblock .opblock-summary-method { min-width: 50px; font-size: 11px; padding: 3px 6px; }
      .swagger-ui .info .title { font-size: 20px; }
      .swagger-ui .info .description { font-size: 12px; }
      .swagger-ui .tab li { font-size: 12px; }
    }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
  <script>
    SwaggerUIBundle({
      url: "/openapi.json",
      dom_id: "#swagger-ui",
      deepLinking: true,
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
      layout: "StandaloneLayout",
      defaultModelsExpandDepth: -1,
      docExpansion: "list",
      filter: true,
    });
  </script>
</body>
</html>
"""

REDOC_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>RenoPit — ReDoc</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <style>
    body { margin: 0; padding: 0; }
  </style>
</head>
<body>
  <div id="redoc-container"></div>
  <script src="https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js"></script>
  <script>
    Redoc.init("/openapi.json", {
      scrollYOffset: 0,
      hideDownloadButton: false,
      expandResponses: "200",
    }, document.getElementById("redoc-container"));
  </script>
</body>
</html>
"""


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Swagger UI 文档页面（带移动端自适应样式）"""
    return HTMLResponse(SWAGGER_HTML)


@app.get("/favicon.svg", include_in_schema=False)
async def favicon():
    """返回 favicon 图标"""
    favicon_path = os.path.join(os.path.dirname(__file__), "favicon.svg")
    return FileResponse(favicon_path)


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """自定义 Redoc 文档页面（使用指定版本的 CDN，避免 @next tag 失效）"""
    return HTMLResponse(REDOC_HTML)
