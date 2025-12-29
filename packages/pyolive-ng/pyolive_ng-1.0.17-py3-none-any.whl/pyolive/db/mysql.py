import aiomysql
from .base import Database


class MySQLDatabase(Database):
    def __init__(self, **kwargs):
        self.config = kwargs
        self.pool = None

    async def connect(self):
        self.pool = await aiomysql.create_pool(**self.config)

    async def disconnect(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def execute_query(self, query: str, params: tuple = ()):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                await conn.commit()

    async def fetch_query(self, query: str, params: tuple = ()) -> list:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, params)
                return await cur.fetchall()