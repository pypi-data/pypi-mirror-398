import asyncpg
from .base import Database


class PostgreSQLDatabase(Database):
    def __init__(self, **kwargs):
        self.config = kwargs
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(**self.config)

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def execute_query(self, query: str, params: tuple = ()):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(query, *params)

    async def fetch_query(self, query: str, params: tuple = ()) -> list:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]  # Convert to list of dicts