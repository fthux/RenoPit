"""
应用配置 — 从环境变量读取所有配置项
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "renovate"
    DB_PASSWORD: str = "renovate123"
    DB_NAME: str = "renovate_db"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @property
    def CELERY_BROKER_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    # AI 模型
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    AI_MODEL_PROVIDER: str = "openai"

    # 文件上传限制
    MAX_UPLOAD_SIZE: int = 20_971_520  # 20 MB
    MAX_TEXT_FILE_SIZE: int = 5_242_880  # 5 MB
    MAX_INPUT_TEXT_LENGTH: int = 2_000  # 字符

    # 中文字体
    FONT_PATH: str = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

    # 联网搜索
    ENABLE_WEB_SEARCH: bool = True

    # 上传/报告目录（相对于 backend/）
    UPLOAD_DIR: str = "uploads"
    REPORT_DIR: str = "reports"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()