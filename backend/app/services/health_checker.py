"""
健康检查服务 — 全方位系统健康体检
检查维度：数据库、Redis、Celery、LLM API、文件系统、应用数据、运行时、网络
"""

import asyncio
import json
import logging
import os
import sys
import time
import threading
import gc
import socket
import ssl
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from ..core.config import settings
from ..core.database import engine

logger = logging.getLogger(__name__)

# 应用启动时间
APP_START_TIME = time.time()

# ============================================================
# 工具函数
# ============================================================


def tcp_ping(host: str, port: int, timeout: float = 3.0) -> tuple[bool, float]:
    """TCP 连接探测，返回 (成功, 延迟_ms)"""
    start = time.perf_counter()
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        latency = (time.perf_counter() - start) * 1000
        return True, latency
    except Exception:
        return False, 0.0


def tls_connect(host: str, port: int, timeout: float = 5.0) -> tuple[bool, float]:
    """TLS 连接探测，返回 (成功, 延迟_ms)"""
    start = time.perf_counter()
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host):
                latency = (time.perf_counter() - start) * 1000
                return True, latency
    except Exception:
        return False, 0.0


def get_open_fd_count() -> int:
    """获取当前进程打开的文件描述符数量"""
    try:
        import psutil
        return len(psutil.Process().open_files())
    except ImportError:
        pass
    try:
        # macOS/Linux 通用方式
        return len(os.listdir(f"/proc/{os.getpid()}/fd"))
    except Exception:
        return -1


def get_process_memory_mb() -> float:
    """获取当前进程内存 RSS (MB)"""
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        pass
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except Exception:
        return -1.0


def get_cpu_percent() -> float:
    """获取当前进程 CPU 使用率"""
    try:
        import psutil
        return psutil.Process().cpu_percent(interval=0.1)
    except ImportError:
        return -1.0


def get_queue_depth() -> int:
    """获取 Celery 队列积压任务数"""
    try:
        from ..tasks.celery_app import celery_app
        inspect = celery_app.control.inspect(timeout=2.0)
        if inspect is None:
            return -1
        active = inspect.active()
        if active is None:
            return 0
        return sum(len(tasks) for tasks in active.values())
    except Exception:
        return -1


def get_celery_worker_count() -> int:
    """获取在线 Celery Worker 数量"""
    try:
        from ..tasks.celery_app import celery_app
        result = celery_app.control.ping(timeout=2.0)
        if result is None:
            return 0
        return len(result)
    except Exception:
        return -1


# ============================================================
# 检查项数据类
# ============================================================


@dataclass
class CheckResult:
    name: str
    status: str  # "ok" | "error" | "warning"
    detail: str = ""
    latency_ms: float = 0.0
    extra: dict = field(default_factory=dict)


# ============================================================
# 各维度检查函数
# ============================================================


async def check_database() -> CheckResult:
    """数据库连接检查"""
    result = CheckResult(name="数据库 PostgreSQL", status="ok")
    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(engine.dialect.do_ping(conn) if False else __import__("sqlalchemy").text("SELECT 1"))
            result.latency_ms = round((time.perf_counter() - start) * 1000, 1)

        # 连接池状态
        pool = engine.pool
        result.extra = {
            "pool_size": getattr(pool, "size", lambda: -1)(),
            "checked_in": getattr(pool, "checkedin", lambda: 0)(),
            "overflow": getattr(pool, "overflow", lambda: -1)(),
        }
        result.detail = f"延迟 {result.latency_ms}ms"
    except Exception as e:
        result.status = "error"
        result.detail = str(e)[:200]
    return result


async def check_redis() -> CheckResult:
    """Redis 连接检查"""
    result = CheckResult(name="Redis", status="ok")
    try:
        import redis.asyncio as aioredis
        r = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        start = time.perf_counter()
        pong = await r.ping()
        result.latency_ms = round((time.perf_counter() - start) * 1000, 1)

        # 内存信息
        info = await r.info("memory")
        result.extra = {
            "used_memory_mb": round(info.get("used_memory", 0) / (1024 * 1024), 1),
            "maxmemory_mb": round(info.get("maxmemory", 0) / (1024 * 1024), 1) if info.get("maxmemory", 0) > 0 else None,
        }
        result.detail = f"延迟 {result.latency_ms}ms, 内存 {result.extra['used_memory_mb']}MB"
        await r.aclose()
    except ImportError:
        result.status = "warning"
        result.detail = "redis-py 未安装"
    except Exception as e:
        result.status = "error"
        result.detail = str(e)[:200]
    return result


async def check_celery() -> CheckResult:
    """Celery Worker 检查"""
    result = CheckResult(name="Celery Worker", status="ok")
    try:
        worker_count = await asyncio.to_thread(get_celery_worker_count)
        queue_depth = await asyncio.to_thread(get_queue_depth)

        result.extra = {
            "workers_online": worker_count,
            "queue_depth": queue_depth,
        }

        if worker_count == 0:
            result.status = "error"
            result.detail = "无在线 Worker"
        elif queue_depth > 50:
            result.status = "warning"
            result.detail = f"{worker_count} worker(s) 在线, 队列积压 {queue_depth}"
        else:
            result.detail = f"{worker_count} worker(s) 在线, 队列 {queue_depth} 个任务"
    except ImportError:
        result.status = "warning"
        result.detail = "Celery 未配置"
    except Exception as e:
        result.status = "error"
        result.detail = str(e)[:200]
    return result


async def check_llm_api() -> CheckResult:
    """LLM API 可用性检查"""
    result = CheckResult(name="LLM API", status="ok")
    if not settings.LLM_API_KEY:
        result.status = "warning"
        result.detail = "LLM_API_KEY 未配置"
        return result

    try:
        from urllib.parse import urlparse
        parsed = urlparse(settings.LLM_BASE_URL)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        # 网络连通性
        tcp_ok, tcp_latency = tcp_ping(host, port)
        if not tcp_ok:
            result.status = "error"
            result.detail = f"无法连接到 {host}:{port}"
            return result

        # API 可用性
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            timeout=10,
        )
        start = time.perf_counter()
        models = await client.models.list()
        result.latency_ms = round((time.perf_counter() - start) * 1000, 1)

        model_ids = [m.id for m in models.data]
        model_available = settings.LLM_MODEL_NAME in model_ids

        result.extra = {
            "model": settings.LLM_MODEL_NAME,
            "available": model_available,
            "tcp_latency_ms": round(tcp_latency, 1),
        }

        if model_available:
            result.detail = f"{settings.LLM_MODEL_NAME} 可用, 延迟 {result.latency_ms}ms"
        else:
            result.status = "warning"
            result.detail = f"{settings.LLM_MODEL_NAME} 不在模型列表中"
    except ImportError:
        result.status = "warning"
        result.detail = "openai 客户端未安装"
    except Exception as e:
        result.status = "error"
        result.detail = str(e)[:200]
    return result


async def check_filesystem() -> CheckResult:
    """文件系统检查"""
    result = CheckResult(name="文件系统", status="ok")
    try:
        import shutil

        upload_dir = os.path.abspath(settings.UPLOAD_DIR)
        report_dir = os.path.abspath(settings.REPORT_DIR)
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(report_dir, exist_ok=True)

        upload_writable = os.access(upload_dir, os.W_OK)
        report_writable = os.access(report_dir, os.W_OK)

        # 磁盘空间（检查根文件系统，避免 Docker 容器内子目录文件系统与实际磁盘不符）
        usage = shutil.disk_usage("/")

        # 临时文件读写测试
        temp_path = os.path.join(upload_dir, ".health_check_temp")
        try:
            with open(temp_path, "w") as f:
                f.write("ok")
            with open(temp_path, "r") as f:
                content = f.read()
            os.remove(temp_path)
            temp_ok = content == "ok"
        except Exception:
            temp_ok = False

        free_gb = usage.free / (1024 ** 3)
        free_mb = usage.free / (1024 * 1024)

        result.extra = {
            "disk_free_mb": round(free_mb, 1),
            "disk_total_mb": round(usage.total / (1024 * 1024), 1),
            "upload_dir_writable": upload_writable,
            "report_dir_writable": report_writable,
            "temp_file_rw": temp_ok,
        }

        issues = []
        if not upload_writable:
            issues.append("上传目录不可写")
        if not report_writable:
            issues.append("报告目录不可写")
        if not temp_ok:
            issues.append("临时文件读写失败")
        if free_gb < 1.0:
            issues.append(f"磁盘剩余仅 {free_mb:.0f}MB")
            if result.status == "ok":
                result.status = "warning"

        if issues:
            if any("不可写" in i or "失败" in i for i in issues):
                result.status = "error"
            result.detail = "; ".join(issues)
        else:
            result.detail = f"磁盘剩余 {free_gb:.1f}GB, 目录正常"
    except Exception as e:
        result.status = "error"
        result.detail = str(e)[:200]
    return result


async def check_application_data() -> CheckResult:
    """应用数据完整性检查"""
    result = CheckResult(name="应用数据", status="ok")
    try:
        issues = []

        # pitfalls.json
        pitfalls_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "data", "pitfalls.json")
        )
        if os.path.exists(pitfalls_path):
            try:
                with open(pitfalls_path, "r") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    result.extra["pitfalls_count"] = len(data)
                else:
                    result.extra["pitfalls_count"] = 1
            except Exception as e:
                issues.append(f"pitfalls.json 解析失败: {e}")
        else:
            issues.append("pitfalls.json 不存在")

        # 字体文件
        font_path = settings.FONT_PATH
        if os.path.exists(font_path):
            size_mb = os.path.getsize(font_path) / (1024 * 1024)
            result.extra["font_size_mb"] = round(size_mb, 1)
            result.extra["font_path"] = font_path
        else:
            issues.append(f"字体文件不存在: {font_path}")

        # 环境变量
        missing_env = []
        if not settings.LLM_API_KEY:
            missing_env.append("LLM_API_KEY")
        result.extra["env_configured"] = len(missing_env) == 0

        if issues:
            result.status = "error" if any("不存在" in i for i in issues) else "warning"
            result.detail = "; ".join(issues)
        else:
            result.detail = f"pitfalls ({result.extra.get('pitfalls_count', '?')} 项), 字体 OK"
    except Exception as e:
        result.status = "error"
        result.detail = str(e)[:200]
    return result


async def check_runtime() -> CheckResult:
    """应用运行时状态"""
    result = CheckResult(name="应用运行时", status="ok")
    try:
        uptime = time.time() - APP_START_TIME
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)

        gc_stats = gc.get_stats()

        result.extra = {
            "python_version": sys.version,
            "uptime_seconds": int(uptime),
            "uptime_display": f"{hours}h {minutes}m {seconds}s",
            "memory_rss_mb": round(get_process_memory_mb(), 1),
            "cpu_percent": round(get_cpu_percent(), 1),
            "thread_count": threading.active_count(),
            "open_fds": get_open_fd_count(),
            "gc_generation_0_collections": gc_stats[0].get("collections", 0) if gc_stats else 0,
        }

        result.detail = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}, 运行 {result.extra['uptime_display']}"
    except Exception as e:
        result.status = "error"
        result.detail = str(e)[:200]
    return result


async def check_network() -> CheckResult:
    """外部网络连通性"""
    result = CheckResult(name="网络连通性", status="ok")
    try:
        from urllib.parse import urlparse
        parsed = urlparse(settings.LLM_BASE_URL)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        # DNS 解析
        dns_ok = False
        try:
            socket.getaddrinfo(host, port)
            dns_ok = True
        except Exception:
            pass

        # TLS 连接
        tls_ok, tls_latency = False, 0.0
        if dns_ok:
            tls_ok, tls_latency = tls_connect(host, port)

        result.extra = {
            "dns_resolution": "ok" if dns_ok else "error",
            "tls_connectivity": "ok" if tls_ok else "error",
            "target": f"{host}:{port}",
        }

        if not dns_ok:
            result.status = "error"
            result.detail = f"DNS 解析失败: {host}"
        elif not tls_ok:
            result.status = "error"
            result.detail = f"TLS 连接失败: {host}:{port}"
        else:
            result.detail = f"DNS + TLS 正常, 延迟 {tls_latency:.0f}ms"
    except Exception as e:
        result.status = "error"
        result.detail = str(e)[:200]
    return result


# ============================================================
# 主入口
# ============================================================


async def run_all_checks() -> dict:
    """运行所有健康检查，返回完整结果"""
    checks = {}
    total_status = "healthy"

    # 核心依赖（故障则 unhealthy）
    core_checks = {
        "database": check_database,
        "redis": check_redis,
        "filesystem": check_filesystem,
    }
    # 业务依赖（故障则 degraded）
    business_checks = {
        "llm_api": check_llm_api,
        "celery": check_celery,
        "application_data": check_application_data,
    }
    # 信息类（不影响状态）
    info_checks = {
        "runtime": check_runtime,
        "network": check_network,
    }

    ordered = list(core_checks.items()) + list(business_checks.items()) + list(info_checks.items())

    for key, check_fn in ordered:
        try:
            result = await check_fn()
        except Exception as e:
            result = CheckResult(name=key, status="error", detail=f"检查异常: {str(e)[:200]}")
        checks[key] = {
            "name": result.name,
            "status": result.status,
            "detail": result.detail,
            "latency_ms": result.latency_ms,
            "extra": result.extra,
        }

    # 确定整体状态
    # core 中任何 error → unhealthy
    for key in core_checks:
        if checks[key]["status"] == "error":
            total_status = "unhealthy"
            break

    if total_status == "healthy":
        # business 中任何 error 且 core 全部 ok → degraded
        for key in business_checks:
            if checks[key]["status"] == "error":
                total_status = "degraded"
                break
        # 否则检查 warning
        if total_status == "healthy":
            for key in list(core_checks) + list(business_checks):
                if checks[key]["status"] == "warning":
                    total_status = "degraded"
                    break

    return {
        "status": total_status,
        "service": "RenoPit",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(time.time() - APP_START_TIME),
        "checks": checks,
    }