from __future__ import annotations

import asyncio
import time
from typing import Dict

from redis.asyncio import ConnectionPool, Redis


class RedisPoolManager:
    """
    单例，负责：
    1. 持有全局 ConnectionPool
    2. 记录 client_id -> Redis 实例
    3. 生命周期内统一创建/销毁
    """
    _inst: RedisPoolManager | None = None
    _lock = asyncio.Lock()

    def __new__(cls, *a, **kw):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
        return cls._inst

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        max_connections: int = 256,
    ):
        # 只允许初始化一次
        if hasattr(self, "_init"):
            return
        self.redis_url = redis_url
        self.max_connections = max_connections
        self._pool: ConnectionPool | None = None
        self._clients: Dict[str, Redis] = {}
        self._init = True

    async def ensure_pool(self):
        """延迟创建pool"""
        if self._pool is None:
            self._pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=True,  # 直接 str，免手动 decode
            )

    async def startup(self):
        """FastAPI startup 事件回调"""
        await self.ensure_pool()

    async def shutdown(self):
        """FastAPI shutdown 事件回调"""
        async with self._lock:
            # 1. 关闭所有客户端
            await asyncio.gather(*(c.aclose() for c in self._clients.values()))

            self._clients.clear()
            # 2. 关闭连接池
            if self._pool:
                await self._pool.aclose()
                self._pool = None

    async def get_client(self, client_id: str) -> Redis:
        """线程安全地获取（或创建）一个 Redis 实例，复用同一池"""
        async with self._lock:
            if client_id in self._clients:
                return self._clients[client_id]
            await self.ensure_pool()
            redis = Redis.from_pool(connection_pool=self._pool)
            self._clients[client_id] = redis
            return redis

    async def close_client(self, client_id: str) -> bool:
        """线程安全地关闭一个 Redis 实例"""
        async with self._lock:
            if client_id in self._clients:
                await self._clients[client_id].aclose()
                await self._clients.pop(client_id)
                return True
            return False

    async def list_clients(self) -> None:
        """线程安全地关闭一个 Redis 实例"""
        async with self._lock:
            clients = [c for c in self._clients.values()]
            print(f'共{len(clients)}个client')

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.startup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.shutdown()


if __name__ == '__main__':
    global_redis_pool_manager = RedisPoolManager()

    async def _main():
        client = await global_redis_pool_manager.get_client(client_id='test_1234')
        await global_redis_pool_manager.list_clients()

        await client.set('k1', 'hello', ex=3)  # 设值 + 30 秒过期
        val = await client.get('k1')
        print(f'get redis cache: {val}')

        time.sleep(3)

        val = await client.get('k1')
        print(f'get redis cache: {val}')

        await global_redis_pool_manager.close_client(client_id='test_1234')
        await global_redis_pool_manager.list_clients()

    asyncio.run(_main())
