from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Config:
    params_path: Path

    @classmethod
    def default(cls) -> "Config":
        repo_root = Path(__file__).resolve().parents[2]
        return cls(params_path=repo_root / "params.yml")

    def as_dict(self) -> dict[str, Any]:
        return {"params_path": str(self.params_path)}

