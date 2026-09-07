"""Estado global del TUI (en memoria)."""

from __future__ import annotations

from typing import Any


class State:
    """Estado mínimo del esqueleto: solo la config en memoria…"""

    def __init__(self, cfg: dict[str, Any] | None = None) -> None:
        self.cfg = dict(cfg or {})

    @property
    def base_url(self) -> str:
        return str(self.cfg.get("base_url", "")).rstrip("/")