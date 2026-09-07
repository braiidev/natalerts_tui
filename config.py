"""Persistencia de configuración del TUI.

Settings locales en `tui/config.json` (no choca con el server ni con la web).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(__file__).resolve().parent
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULTS: dict[str, Any] = {
    "base_url": "http://192.168.1.42:8000",
    "provider": "all",
    "days": 7,
    "sort": "severity",
    "order": "desc",
    "scope": "world",
    "radius": 250,
    "active_location_id": None,
    "weather_view": "hourly",
}

# Opciones válidas para edición desde el modal de config
SCOPE_OPTIONS = ["world", "country", "zone"]
PROVIDER_OPTIONS = ["all", "usgs", "eonet", "gdacs"]  # open_meteo no produce alertas
SORT_OPTIONS = ["severity", "time", "distance"]
DAYS_OPTIONS = [1, 7, 30, 90, 0]  # 0 = todos


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Carga config.json mergeando con defaults (campos faltantes/rotos)."""
    cfg_path = Path(path) if path else CONFIG_PATH
    data: dict[str, Any] = {}
    if cfg_path.exists():
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    merged = {**DEFAULTS, **data}
    if not isinstance(merged.get("base_url"), str) or not merged["base_url"]:
        merged["base_url"] = DEFAULTS["base_url"]
    return merged


def save_config(cfg: dict[str, Any], path: Path | str | None = None) -> None:
    """Persiste la config mergeada con defaults (mantiene esquema completo)."""
    cfg_path = Path(path) if path else CONFIG_PATH
    merged = {**DEFAULTS, **cfg}
    cfg_path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def base_url(cfg: dict[str, Any]) -> str:
    """Normaliza la base URL (sin barra final)."""
    return str(cfg.get("base_url", DEFAULTS["base_url"])).rstrip("/")


def apply_cli_defaults(cfg: dict[str, Any]) -> dict[str, Any]:
    """Aplica el override de URL por CLI (--url) sin persistirlo."""

    def _apply(url: str | None) -> None:
        if url:
            cfg["base_url"] = url.rstrip("/")

    _apply(os.environ.get("NATALERTS_TUI_URL"))
    return cfg
