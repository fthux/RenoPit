"""
SSE (Server-Sent Events) 管理器
维护每个项目的订阅者队列，支持推送状态变更事件
"""

import asyncio
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SSEManager:
    """全局 SSE 管理器，维护 project_id → 订阅者队列 映射"""

    def __init__(self):
        # Dict[project_id, List[asyncio.Queue]]
        self._subscriptions: dict[str, list[asyncio.Queue]] = {}

    def subscribe(self, project_id: str) -> asyncio.Queue:
        """注册订阅者，返回一个 asyncio.Queue 供生成器消费"""
        queue: asyncio.Queue = asyncio.Queue()
        if project_id not in self._subscriptions:
            self._subscriptions[project_id] = []
        self._subscriptions[project_id].append(queue)
        logger.info(f"SSE subscribe: project={project_id}, total_subscribers={len(self._subscriptions[project_id])}")
        return queue

    def unsubscribe(self, project_id: str, queue: asyncio.Queue):
        """移除订阅者"""
        if project_id not in self._subscriptions:
            return
        try:
            self._subscriptions[project_id].remove(queue)
            logger.info(f"SSE unsubscribe: project={project_id}, remaining={len(self._subscriptions[project_id])}")
            if not self._subscriptions[project_id]:
                del self._subscriptions[project_id]
        except ValueError:
            pass

    def publish(self, project_id: str, event: str, data: dict, retry: Optional[int] = None, event_id: Optional[str] = None):
        """推送事件到所有订阅者（同步方法，供 Celery worker 使用）"""
        if project_id not in self._subscriptions:
            return

        # 构建 SSE 格式消息
        sse_lines = []
        if event_id:
            sse_lines.append(f"id: {event_id}")
        sse_lines.append(f"event: {event}")
        sse_lines.append(f"data: {json.dumps(data, ensure_ascii=False)}")
        if retry is not None:
            sse_lines.append(f"retry: {retry}")
        sse_lines.append("")  # 空行结束
        sse_message = "\n".join(sse_lines)

        dead_queues = []
        for queue in self._subscriptions[project_id]:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 事件循环运行中，用 call_soon_threadsafe
                    loop.call_soon_threadsafe(queue.put_nowait, sse_message)
                else:
                    queue.put_nowait(sse_message)
            except Exception:
                dead_queues.append(queue)

        for q in dead_queues:
            self.unsubscribe(project_id, q)

    async def publish_async(self, project_id: str, event: str, data: dict, retry: Optional[int] = None, event_id: Optional[str] = None):
        """推送事件到所有订阅者（异步方法，供 FastAPI 端点使用）"""
        if project_id not in self._subscriptions:
            return

        sse_lines = []
        if event_id:
            sse_lines.append(f"id: {event_id}")
        sse_lines.append(f"event: {event}")
        sse_lines.append(f"data: {json.dumps(data, ensure_ascii=False)}")
        if retry is not None:
            sse_lines.append(f"retry: {retry}")
        sse_lines.append("")
        sse_message = "\n".join(sse_lines)

        dead_queues = []
        for queue in self._subscriptions[project_id]:
            try:
                queue.put_nowait(sse_message)
            except Exception:
                dead_queues.append(queue)

        for q in dead_queues:
            self.unsubscribe(project_id, q)


# 全局单例
sse_manager = SSEManager()