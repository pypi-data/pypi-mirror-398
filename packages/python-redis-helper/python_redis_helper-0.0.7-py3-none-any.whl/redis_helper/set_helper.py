# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  redis-helper
# FileName:     set_helper.py
# Description:  集合脚手架
# Author:       ASUS
# CreateDate:   2025/12/21
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Optional
import redis.asyncio as redis

"""
无重复
    *   pending 和 processing 都是 Set，天然保证唯一性
并发安全
    *   pop() 原子 Lua 脚本，多消费者同时取任务不会冲突
    *   requeue / recover 用 pipeline 原子操作
顺序无关
    *   Set 是无序的，谁先取到谁执行
调用方式几乎不变
    *   pop(), finish(), requeue(), recover() 使用方式和list的一致
    *   add() 被你弃用，lpush_if_not_exists() 保留去重逻辑
"""


class AsyncReliableQueue:
    """
    并发安全、无序、去重的可靠队列（适合多消费者场景）
    """

    def __init__(self, redis: redis.Redis, key: str):
        self.redis = redis
        self.pending = f"queue:pending:set:{key}"  # 待执行任务（唯一）
        self.processing = f"queue:processing:set:{key}"  # 正在执行任务（唯一）

        # 原子 pop: 从 pending SPOP 取出任务，加入 processing
        self.pop_script = self.redis.register_script("""
        local task = redis.call('SPOP', KEYS[1])
        if not task then
            return nil
        end
        redis.call('SADD', KEYS[2], task)
        return task
        """)

    # ================= API =================

    async def lpush_if_not_exists(self, task: str) -> bool:
        """
        去重加入队列（Set 已经保证唯一性）
        返回 True 表示入队成功，False 表示任务已存在
        """
        return bool(await self.redis.sadd(self.pending, task))

    async def pop(self) -> Optional[str]:
        """
        消费者原子取任务
        """
        return await self.pop_script(keys=[self.pending, self.processing], args=[])

    async def finish(self, task: str):
        """
        标记任务完成（幂等）
        """
        await self.redis.srem(self.processing, task)

    async def requeue(self, task: str):
        """
        任务失败回队
        """
        pipe = self.redis.pipeline()
        await pipe.srem(self.processing, task)
        await pipe.sadd(self.pending, task)
        await pipe.execute()

    async def recover(self) -> int:
        """
        程序启动或人工触发恢复未完成任务
        """
        tasks = await self.redis.smembers(self.processing)
        if not tasks:
            return 0

        pipe = self.redis.pipeline()
        for t in tasks:
            await pipe.srem(self.processing, t)
            await pipe.sadd(self.pending, t)
        await pipe.execute()
        return len(tasks)

    # ================= 存在性判断 =================
    async def in_pending(self, task: str) -> bool:
        """是否在待执行队列"""
        return bool(await self.redis.sismember(self.pending, task))

    async def in_processing(self, task: str) -> bool:
        """是否正在执行"""
        return bool(await self.redis.sismember(self.processing, task))

    async def exists(self, task: str) -> bool:
        """
        是否已在系统中（pending 或 processing）
        """
        pipe = self.redis.pipeline()
        await pipe.sismember(self.pending, task)
        await pipe.sismember(self.processing, task)
        in_pending, in_processing = await pipe.execute()
        return bool(in_pending or in_processing)
