"""
RenoPit — FastAPI Application
装修避坑分析器 后端入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.database import engine, Base
from .api import projects_router

app = FastAPI(
    title="RenoPit",
    description="装修设计图避坑分析器 API",
    version="0.1.0",
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


@app.on_event("startup")
async def startup():
    """启动时自动创建所有数据库表（开发阶段使用，生产环境用 Alembic 迁移）"""
    # 确保所有模型已导入才能被 Base.metadata 发现
    from .models import Project, ProjectImage, ProjectFile, Analysis, DocumentAnalysis, Report  # noqa: F401
    Base.metadata.create_all(bind=engine)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "RenoPit"}
