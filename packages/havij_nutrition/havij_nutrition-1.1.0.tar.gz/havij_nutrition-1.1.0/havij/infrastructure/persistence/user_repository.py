from __future__ import annotations

import sqlite3
from datetime import datetime

from havij.application.ports import UserAuthRecord
from havij.domain.model.user import UserProfile


class SqliteUserRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create_user(
        self,
        user_id: str,
        username: str,
        password_hash: str,
        salt: str,
        created_at: datetime,
    ) -> UserProfile:
        self._conn.execute(
            """
            INSERT INTO users(user_id, username, password_hash, salt, created_at)
            VALUES(?, ?, ?, ?, ?)
            """,
            (user_id, username, password_hash, salt, created_at.isoformat()),
        )
        self._conn.commit()
        return UserProfile(user_id=user_id, username=username, created_at=created_at)

    def get_auth_by_username(self, username: str) -> UserAuthRecord | None:
        row = self._conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not row:
            return None
        return UserAuthRecord(
            user_id=row["user_id"],
            username=row["username"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def get_profile(self, user_id: str) -> UserProfile | None:
        row = self._conn.execute(
            "SELECT user_id, username, created_at FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        return UserProfile(
            user_id=row["user_id"],
            username=row["username"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def count_users(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS c FROM users;").fetchone()
        return int(row["c"]) if row else 0
