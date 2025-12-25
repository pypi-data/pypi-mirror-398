from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserProfile:
    user_id: str
    username: str
    created_at: datetime
