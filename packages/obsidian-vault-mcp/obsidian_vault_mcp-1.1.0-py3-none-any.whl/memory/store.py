"""Memory 存储 - SQLite 实现"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Any


@dataclass
class Memory:
    """记忆条目"""
    key: str
    value: Any
    category: str = "general"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now


class MemoryStore:
    """SQLite 记忆存储"""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_path / "memory.db"
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_category
                ON memories(category)
            """)
            conn.commit()

    def set(self, key: str, value: Any, category: str = "general") -> Memory:
        """设置记忆"""
        now = datetime.now().isoformat()
        value_json = json.dumps(value, ensure_ascii=False)

        with self._get_conn() as conn:
            existing = conn.execute(
                "SELECT created_at FROM memories WHERE key = ?", (key,)
            ).fetchone()

            if existing:
                conn.execute("""
                    UPDATE memories SET value = ?, category = ?, updated_at = ?
                    WHERE key = ?
                """, (value_json, category, now, key))
                created_at = existing["created_at"]
            else:
                conn.execute("""
                    INSERT INTO memories (key, value, category, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (key, value_json, category, now, now))
                created_at = now

            conn.commit()

        return Memory(key=key, value=value, category=category,
                      created_at=created_at, updated_at=now)

    def get(self, key: str) -> Memory | None:
        """获取记忆"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM memories WHERE key = ?", (key,)
            ).fetchone()

            if row:
                return Memory(
                    key=row["key"],
                    value=json.loads(row["value"]),
                    category=row["category"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
            return None

    def delete(self, key: str) -> bool:
        """删除记忆"""
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM memories WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0

    def list_by_category(self, category: str = "general") -> list[Memory]:
        """按分类列出"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM memories WHERE category = ? ORDER BY updated_at DESC",
                (category,)
            ).fetchall()

            return [
                Memory(
                    key=row["key"],
                    value=json.loads(row["value"]),
                    category=row["category"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
                for row in rows
            ]

    def get_stats(self) -> dict:
        """统计信息"""
        with self._get_conn() as conn:
            count = conn.execute("SELECT COUNT(*) as c FROM memories").fetchone()["c"]
            categories = conn.execute("""
                SELECT category, COUNT(*) as c FROM memories GROUP BY category
            """).fetchall()

            return {
                "total": count,
                "categories": {r["category"]: r["c"] for r in categories},
            }
