"""Estado global del TUI (en memoria)."""

from __future__ import annotations

import time
from typing import Any

# TTL del toast de feedback (s)
TOAST_TTL = 4.0


class State:
    """Mantiene la config activa, datos en caché y el resultado de la última
    operación (para feedback tipo toast)."""

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.cfg = cfg
        self.client = None  # type: ignore[assignment]
        self.connected: bool | None = None

        # Alertas
        self.alerts: list[dict[str, Any]] = []
        self.alert_count = 0
        self.error_alerts: str | None = None

        # Clima
        self.weather: dict[str, Any] | None = None
        self.error_weather: str | None = None
        self.locations: list[dict[str, Any]] = []
        self.active_location_id: int | None = cfg.get("active_location_id")
        self.weather_view = cfg.get("weather_view", "hourly")
        # Celda seleccionada en la grilla de clima (índice absoluto; la
        # ventana visible la sigue automáticamente).
        self.weather_cell = 0
        self.tema = cfg.get("tema", "clasico")

        # Fuentes / config
        self.config: dict[str, Any] = {}
        self.error_config: str | None = None

        # Feedback
        self.toast: str | None = None
        self.toast_at: float | None = None
        self.toast_color = 3  # amarillo
        # Relanzar tras actualización exitosa (lo consume main.py con os.execv)
        self.relaunch = False
        # Nombre en espera del flujo "añadir ubicación" (add -> search)
        self._pending_name: str | None = None

    def set_toast(self, msg: str) -> None:
        self.toast = msg
        self.toast_at = time.monotonic()

    # ---- Accesos de conveniencia ----
    @property
    def base_url(self) -> str:
        return str(self.cfg["base_url"]).rstrip("/")

    @property
    def provider(self) -> str:
        return self.cfg.get("provider", "all")

    @property
    def days(self) -> int:
        return self.cfg.get("days", 7)

    @property
    def sort(self) -> str:
        return self.cfg.get("sort", "severity")

    @property
    def order(self) -> str:
        return self.cfg.get("order", "desc")

    @property
    def scope(self) -> str:
        return self.cfg.get("scope", "world")

    @property
    def event_type(self) -> str:
        return self.cfg.get("event_type", "all")

    @property
    def radius(self) -> int:
        return int(self.cfg.get("radius", 250))

    def active_location(self) -> dict[str, Any] | None:
        if self.active_location_id is None:
            return None
        for loc in self.locations:
            if loc.get("id") == self.active_location_id:
                return loc
        # el id guardado ya no existe: limpiar
        self.active_location_id = None
        return None
