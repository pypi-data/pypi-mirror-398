# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  redis-helper
# FileName:     list_helper.py
# Description:  列表帮助模块
# Author:       ASUS
# CreateDate:   2025/12/21
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Optional
import redis.asyncio as redis


class AsyncReliableQueue:
    """
    循环可靠队列（适合 Cron/定时任务）
    """

    def __init__(self, redis: redis.Redis, key: str):
        self.redis = redis
        self.pending = f"queue:pending:list:{key}:"
        self.processing = f"queue:processing:list:{key}"

        # 使用 Lua 做 pop（原子操作）
        self.pop_script = redis.register_script("""
        -- 从队尾取出
        local task = redis.call('RPOP', KEYS[1])
        if not task then
            return nil
        end
        -- 放入 processing
        redis.call('LPUSH', KEYS[2], task)
        return task
        """)

    async def lpush_if_not_exists(self, task: str):
        CHECK_AND_PUSH = """
        local exist = redis.call('LPOS', KEYS[1], ARGV[1])
        if not exist then
            return redis.call('LPUSH', KEYS[1], ARGV[1])
        else
            return 0
        end
        """
        return await self.redis.eval(CHECK_AND_PUSH, 1, self.pending, task)

    async def add(self, task: str) -> None:
        """生产者：插入队首（FIFO 原生支持）"""
        await self.redis.lpush(self.pending, task)

    async def pop(self) -> Optional[str]:
        """消费者：FIFO 从队尾取出任务，并放入 processing（原子操作）"""
        return await self.pop_script(keys=[self.pending, self.processing], args=[])

    async def finish(self, task: str):
        """任务完成：从 processing 中删除"""
        await self.redis.lrem(self.processing, 1, task)

    async def requeue(self, task: str):
        """任务回队首：从 processing 删除 → 回 pending 队首"""
        pipe = self.redis.pipeline()
        await pipe.lrem(self.processing, 1, task)
        await pipe.lpush(self.pending, task)
        await pipe.execute()

    async def recover(self):
        """恢复崩溃中的任务：processing → pending 队首"""
        tasks = await self.redis.lrange(self.processing, 0, -1)
        if not tasks:
            return 0

        pipe = self.redis.pipeline()
        for t in tasks:
            await pipe.lrem(self.processing, 1, t)
            await pipe.lpush(self.pending, t)
        await pipe.execute()

        return len(tasks)
