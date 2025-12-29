# rustpy/models/backend/sqlite.py
import sqlite3
from pathlib import Path


class SQLiteBackend:
    def __init__(self, path):
        self.path = Path(path)

        # 🔥 MUHIM: papkani yarat
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)

        # 🔥 connect
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row

        # 🔥 majburiy write → db faylni yaratadi
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.commit()

    def execute(self, sql, params=None):
        cur = self.conn.cursor()
        cur.execute(sql, params or [])
        self.conn.commit()

    def fetch_all(self, sql, params=None):
        cur = self.conn.cursor()
        cur.execute(sql, params or [])
        return cur.fetchall()

    def begin(self):
        self.conn.execute("BEGIN")

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()
