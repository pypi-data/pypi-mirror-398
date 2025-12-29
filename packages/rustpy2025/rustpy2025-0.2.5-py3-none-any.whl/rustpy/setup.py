
from rustpy.db import set_backend
from rustpy.db_async import set_async_backend
try:
    from rustpy.models.backend.aiosqlite import AsyncSQLiteBackend
except ImportError:
    AsyncSQLiteBackend = None

from rustpy.models.backend.sqlite import SQLiteBackend

def setup_from_config(config):
    db = SQLiteBackend(config.DATABASE["NAME"])  # 🔥 .DATABASE
    set_backend(db)
    if AsyncSQLiteBackend:
        db = AsyncSQLiteBackend(config.DATABASE["NAME"])
        set_async_backend(db)
    return db


