"""
数据库连接配置 — SQLAlchemy 引擎、Session、Base
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

engine = create_engine(settings.DB_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI 依赖注入：每次请求获取独立数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()