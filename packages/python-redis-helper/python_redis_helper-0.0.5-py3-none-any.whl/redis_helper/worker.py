# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  redis-helper
# FileName:     worker.py
# Description:  多消费者异步 Worker 模板
# Author:       ASUS
# CreateDate:   2025/12/21
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import asyncio
from typing import Callable, Coroutine, Any
from redis_helper.set_helper import AsyncReliableQueue

class AsyncWorker:
    """
    多消费者异步 Worker 模板
    """

    def __init__(
        self,
        queue: AsyncReliableQueue,
        worker_id: str,
        handler: Callable[[str], Coroutine[Any, Any, None]],
        poll_interval: float = 0.1,
    ):
        """
        :param queue: AsyncReliableQueue 实例
        :param worker_id: 当前 Worker 唯一 ID（日志/调试用）
        :param handler: 异步任务处理函数，接受 task 字符串
        :param poll_interval: 空队列轮询间隔（秒）
        """
        self.queue = queue
        self.worker_id = worker_id
        self.handler = handler
        self.poll_interval = poll_interval
        self._stop = False

    async def start(self):
        """
        启动 Worker 循环
        """
        while not self._stop:
            task = await self.queue.pop()
            if not task:
                await asyncio.sleep(self.poll_interval)
                continue

            try:
                await self.handler(task)
                await self.queue.finish(task)
            except Exception as e:
                # 失败回队列
                await self.queue.requeue(task)
                print(f"[Worker {self.worker_id}] Task failed, requeued: {task}, error: {e}")

    def stop(self):
        """
        停止 Worker
        """
        self._stop = True
