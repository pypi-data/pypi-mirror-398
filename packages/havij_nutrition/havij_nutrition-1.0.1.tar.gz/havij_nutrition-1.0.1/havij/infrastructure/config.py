from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True, slots=True)
class AppConfig:
    db_path: Path

def load_config() -> AppConfig:
    db_path = Path(os.getenv("DB_PATH", "data/app.sqlite"))
    return AppConfig(db_path=db_path)
