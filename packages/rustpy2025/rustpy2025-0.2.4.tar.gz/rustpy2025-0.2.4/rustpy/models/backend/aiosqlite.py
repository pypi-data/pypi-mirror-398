import aiosqlite

class AsyncSQLiteBackend:
    def __init__(self, path):
        self.path = path
        self._conn = None

    async def _get_conn(self):
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.path)
            self._conn.row_factory = aiosqlite.Row
            
            await self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    async def execute(self, sql, params=None):
        conn = await self._get_conn()
        await conn.execute(sql, params or [])
        await conn.commit()

    async def fetch_all(self, sql, params=None):
        conn = await self._get_conn()
        cur = await conn.execute(sql, params or [])
        return await cur.fetchall()

    async def abegin(self):
        conn = await self._get_conn()
        await conn.execute("BEGIN")

    async def acommit(self):
        conn = await self._get_conn()
        await conn.commit()

    async def arollback(self):
        conn = await self._get_conn()
        await conn.rollback()

    async def close(self):
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
