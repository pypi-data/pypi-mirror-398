from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime

from havij.application.ports import UserRepository
from havij.domain.model.user import UserProfile

_PBKDF2_ITERATIONS = 120_000


class UserService:
    def __init__(self, repo: UserRepository):
        self._repo = repo

    def signup(self, username: str, password: str) -> UserProfile:
        username = username.strip()
        if not username:
            raise ValueError("Username is required")
        if not password:
            raise ValueError("Password is required")
        if self._repo.get_auth_by_username(username):
            raise ValueError("Username already exists")

        salt = secrets.token_bytes(16)
        password_hash = _hash_password(password, salt)
        user_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        return self._repo.create_user(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            salt=salt.hex(),
            created_at=created_at,
        )

    def authenticate(self, username: str, password: str) -> UserProfile | None:
        username = username.strip()
        if not username or not password:
            return None
        record = self._repo.get_auth_by_username(username)
        if not record:
            return None
        salt = bytes.fromhex(record.salt)
        expected = record.password_hash
        candidate = _hash_password(password, salt)
        if not hmac.compare_digest(expected, candidate):
            return None
        return UserProfile(
            user_id=record.user_id,
            username=record.username,
            created_at=record.created_at,
        )

    def get_profile(self, user_id: str) -> UserProfile | None:
        return self._repo.get_profile(user_id)

    def count_users(self) -> int:
        return self._repo.count_users()


def _hash_password(password: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return digest.hex()
