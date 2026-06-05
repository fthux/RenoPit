"""
RenoPit — FastAPI Application
装修避坑分析器 后端入口
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .core.database import engine, Base
from .api import projects_router
from .api.health import router as health_router

app = FastAPI(
    title="RenoPit",
    description="装修设计图避坑分析器 API",
    version="0.1.0",
    redoc_url=None,  # 禁用默认 Redoc（CDN @next tag 已失效），用自定义路由替代
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


REDOC_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>RenoPit — ReDoc</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
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


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """自定义 Redoc 文档页面（使用指定版本的 CDN，避免 @next tag 失效）"""
    return HTMLResponse(REDOC_HTML)
