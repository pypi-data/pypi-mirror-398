#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : freq
# @Time         : 2025/10/10 23:52
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : todo 「分组」很多，但 只关心每组最高分（或总和、计数）→ 用 HASH 做「分组聚合表」

from meutils.pipe import *
from meutils.db.redis_db import redis_client, redis_aclient
import asyncio, time, datetime
import redis.asyncio as redis  # 注意导入路径

import datetime as dt


class AsyncFreq:
    def __init__(self, name: str = "doubao"):
        self.name = name
        self.r = redis_aclient

    async def incr_count(self, key: Union[str, int], amount: int = 1):
        await self.r.hincrby(self.name, key, amount)

    async def get_count(self, start_ts: int, end_ts: int) -> int:
        pipe = self.r.pipeline()
        for m in range(start_ts // 60, end_ts // 60 + 1):
            pipe.hget(KEY, m)
        # 异步执行
        vals = await pipe.execute()
        return sum(int(x or 0) for x in vals)

    async def dump_all(self):
        """返回 dict{minute: count}"""
        return await self.r.hgetall(self.name)

    async def close(self):
        await self.r.close()

    async def add_score(self, group: str, mapping: dict):
        # await self.r.zadd(f"rank:{group}", {user: score})
        await self.r.zadd(f"rank:{group}", mapping)

    # 读取：拿到某组 TopN
    async def get_top_n(self, group: str, n: int = 10):
        if n < 0:
            return await self.r.zrange(f"rank:{group}", 0, -n - 1, withscores=True)

        # 倒排
        return await self.r.zrevrange(f"rank:{group}", 0, n - 1, withscores=True)

    async def trim_tail(self, group: str, keep: int = 100):
        """只留分数最高的 keep 个，其余删掉"""
        await self.r.zremrangebyrank(f"rank:{group}", 0, -(keep + 1))


class TokenPool:
    def __init__(self, redis_url: str = "redis://localhost"):
        self.r = redis.from_url(redis_url, decode_responses=True)

        self.r = redis_aclient

    # ---------- 内部工具 ----------
    def _hash_key(self, model: str, day: str = None) -> str:
        day = day or dt.date.today().strftime("%Y%m%d")
        return f"tk:{day}:{model}"

    def _zset_key(self, model: str, day: str = None) -> str:
        day = day or dt.date.today().strftime("%Y%m%d")
        return f"rk:{day}:{model}"

    async def set_tokens(self, model: str, api_key: str, tokens: int):  # 手动加入 没钱的key
        """强制把某个 api_key 的 tokens 设成指定值"""
        pipe = self.r.pipeline(transaction=True)
        pipe.hset(self._hash_key(model), api_key, tokens)  # 覆盖 HASH
        pipe.zadd(self._zset_key(model), {api_key: tokens})  # 覆盖 ZSET
        await pipe.execute()

    # ---------- 1. 记录/回写 tokens ----------
    async def incr_tokens(self, model: str, api_key: str, tokens: int, day: str = None):
        h_key = self._hash_key(model, day)
        z_key = self._zset_key(model, day)

        pipe = self.r.pipeline(transaction=True)
        pipe.hincrby(h_key, api_key, tokens)  # HASH 自增
        pipe.zincrby(z_key, tokens, api_key)  # ZSET 同步 排序
        # 给两个 key 都设 7 天后过期（秒数 7*24*3600=604800）
        pipe.expire(h_key, 7 * 24 * 3600)
        pipe.expire(z_key, 7 * 24 * 3600)
        await pipe.execute()

    # ---------- 2. 取当前最小 tokens 的 api_key ----------

    async def pick_min_key(self, model: str, day: str = None):
        z_key = self._zset_key(model, day)
        lst = await self.r.zrange(z_key, 0, 0, withscores=True)
        return lst

    # ---------- 3. 一站式「取 + 写」 ----------
    async def consume(self, model: str, tokens: int) -> Optional[str]:
        """tokens or freq 都可以用这个方法
        1. 选出该 model 下 tokens 最小的 api_key
        2. 立即把本次 tokens 写回
        3. 返回被消耗的 api_key；无可用返回 None
        """
        if api_key := await self.pick_min_key(model):
            pass  # todo: 完善具体的业务逻辑

            await self.incr_tokens(model, api_key, tokens)

        return "业务逻辑"

    # ---------- 辅助：查任意 key 当前 tokens ----------
    async def get_tokens(self, model: str, api_key: str) -> int:
        val = await self.r.hget(self._hash_key(model), api_key)
        return int(val) if val else 0

    async def close(self):
        await self.r.close()


if __name__ == "__main__":
    # async def main():
    #     freq = AsyncFreq()
    #     now = int(time.time())
    #     # 写
    #     await freq.incr_count(now, 3)
    #     # # 读
    #     # cnt = await freq.get_count(now - 300, now)  # 近 5 分钟
    #     cnt = await freq.dump_all()
    #     print("total:", cnt)
    #     await freq.close()
    async def main():
        add_score = AsyncFreq().add_score
        await add_score("model", {"key1": 98.5, "key2": 100, "key3": 100})
        await add_score("g1", {"u2": 97})
        await add_score("g1", {"u3": 60})

        print(await AsyncFreq().get_top_n("model"))
        await add_score("model", {"key1": 9811.5, "key2": 100, "key3": 100})
        print(await AsyncFreq().get_top_n("model"))


    # arun(main())

    async def main():
        pool = TokenPool()
        model = "gpt-4"
        model = "gpt-4o"

        # 初始导入一些 api_key（可批量）
        await pool.incr_tokens(model, "ak-1", 0)  # 0 表示初始没消耗
        await pool.incr_tokens(model, "ak-2", 0)
        await pool.incr_tokens(model, "ak-3", 0)
        await pool.incr_tokens(model, "ak-4", 0)

        # 模拟 5 次调用，每次 100 tokens
        for i in range(5):
            key = await pool.consume(model, i * 50)
            print("consume ->", key)

        # 查看各 key 累计
        for ak in ["ak-1", "ak-2", "ak-3", "ak-4"]:
            print(ak, await pool.get_tokens(model, ak))

        await pool.close()


    # asyncio.run(main())
    model = "gpt-4"
    #
    arun(TokenPool().pick_min_key(model))  # 取出最小的key

    # arun(TokenPool().incr_tokens(model, "no_money", 888))
