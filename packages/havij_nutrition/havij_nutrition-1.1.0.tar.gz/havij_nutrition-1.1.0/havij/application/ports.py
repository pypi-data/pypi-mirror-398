from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional, Protocol

from havij.domain.model.product import Product
from havij.domain.model.meal import DayLog
from havij.domain.model.user import UserProfile

class ProductCatalog(Protocol):
    def get_by_barcode(self, barcode: str) -> Product: ...

class DayLogRepository(Protocol):
    def load_day(self, day: date, user_id: str) -> DayLog: ...
    def save_day(self, log: DayLog, user_id: str) -> None: ...
    def assign_unowned_entries(self, user_id: str) -> int: ...

@dataclass(frozen=True, slots=True)
class UserAuthRecord:
    user_id: str
    username: str
    password_hash: str
    salt: str
    created_at: datetime

class UserRepository(Protocol):
    def create_user(
        self,
        user_id: str,
        username: str,
        password_hash: str,
        salt: str,
        created_at: datetime,
    ) -> UserProfile: ...
    def get_auth_by_username(self, username: str) -> Optional[UserAuthRecord]: ...
    def get_profile(self, user_id: str) -> Optional[UserProfile]: ...
    def count_users(self) -> int: ...
