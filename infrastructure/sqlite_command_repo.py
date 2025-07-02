"""
Repositorio SQLite que almacena comandos personalizados.
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List
from domain.ports import CommandRepository


class SQLiteCommands(CommandRepository):
    def __init__(self, db_path: str | Path = "commands.db") -> None:
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._ensure_schema()

    # ---------- API pública --------------------------------------

    def list_commands(self) -> List[str]:
        cur = self.conn.execute("SELECT command FROM commands")
        return [row[0] for row in cur.fetchall()]

    def add(self, name: str, url: str) -> None:
        self.conn.execute(
            "INSERT INTO commands(command, url) VALUES (?, ?)", (name, url)
        )
        self.conn.commit()

    def get_url(self, name: str) -> str | None:
        cur = self.conn.execute(
            "SELECT url FROM commands WHERE command = ?", (name,)
        )
        row = cur.fetchone()
        return row[0] if row else None

    # ---------- helpers internos ---------------------------------

    def _ensure_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS commands(
                id      INTEGER PRIMARY KEY,
                command TEXT UNIQUE,
                url     TEXT NOT NULL
            )
            """
        )
        self.conn.commit()