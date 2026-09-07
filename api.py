"""Cliente HTTP de la API de Natural Alerts (solo stdlib, urllib).

Cada función devuelve el JSON parseado o lanza ApiError con mensaje legible.
Registra `last_request_at` (epoch) para el countdown del footer.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

_TIMEOUT = 10

last_request_at: float | None = None


class ApiError(Exception):
    """Error de red o de la API, con mensaje legible para mostrar en TUI."""


def _get(base: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """GET a `base+path` con query params opcionales."""
    global last_request_at
    url = base + path
    if params:
        url += "?" + urllib.parse.urlencode(
            {k: v for k, v in params.items() if v is not None}
        )
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            last_request_at = time.time()
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        last_request_at = time.time()
        body = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body).get("error", body)
        except json.JSONDecodeError:
            detail = body
        raise ApiError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ApiError(f"No se pudo conectar a {base}: {exc.reason}") from exc
    except OSError as exc:
        raise ApiError(f"Error de red: {exc}") from exc


def _send(
    base: str, method: str, path: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    global last_request_at
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        base + path, data=data, method=method, headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            last_request_at = time.time()
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        last_request_at = time.time()
        body = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body).get("error", body)
        except json.JSONDecodeError:
            detail = body
        raise ApiError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ApiError(f"No se pudo conectar a {base}: {exc.reason}") from exc
    except OSError as exc:
        raise ApiError(f"Error de red: {exc}") from exc


class Client:
    """Cliente de la API configurable por base URL."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    # ---- Refresco ----
    def health(self) -> bool:
        try:
            self._get("/health")
            return True
        except ApiError:
            return False

    def alerts(
        self,
        *,
        source: str | None = None,
        days: int | None = None,
        sort: str = "severity",
        order: str = "desc",
        scope: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius: int | None = None,
        types: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "sort": sort,
            "order": order,
            "limit": limit,
        }
        if source and source != "all":
            params["source"] = source
        if types and types != "all":
            params["type"] = types
        if days:
            params["days"] = days
        if scope:
            params["scope"] = scope
        if lat is not None and lon is not None:
            params["lat"] = lat
            params["lon"] = lon
            params["radius"] = radius
        return self._get("/api/alerts", params)

    def alert(self, alert_id: str) -> dict[str, Any]:
        return self._get(f"/api/alerts/{urllib.parse.quote(alert_id)}")

    # ---- Clima ----
    def weather(self, lat: float | None = None, lon: float | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if lat is not None and lon is not None:
            params["lat"] = lat
            params["lon"] = lon
        return self._get("/api/weather", params)

    # ---- Ubicaciones ----
    def locations(self) -> list[dict[str, Any]]:
        return self._get("/api/locations").get("locations", [])

    def create_location(
        self, name: str, lat: float, lon: float, radius_km: float = 250
    ) -> dict[str, Any]:
        return self._send(
            "POST",
            "/api/locations",
            {"name": name, "lat": lat, "lon": lon, "radius_km": radius_km},
        )

    def update_location(
        self, loc_id: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        return self._send("PUT", f"/api/locations/{loc_id}", data)

    def delete_location(self, loc_id: int) -> dict[str, Any]:
        return self._send("DELETE", f"/api/locations/{loc_id}")

    def set_default_location(self, loc_id: int) -> dict[str, Any]:
        return self.update_location(loc_id, {"is_default": True})

    # ---- Geocoding ----
    def geocode(self, query: str, count: int = 6) -> list[dict[str, Any]]:
        data = self._get("/api/geocode", {"q": query, "count": count})
        return data.get("results", [])

    # ---- Recolector / fuentes ----
    def config(self) -> dict[str, Any]:
        return self._get("/api/config")

    def source_sync(self, name: str) -> dict[str, Any]:
        return self._send("POST", f"/api/sources/{name}/sync")

    def source_refresh(self, name: str) -> dict[str, Any]:
        return self._send("POST", f"/api/sources/{name}/refresh")

    def source_interval(self, name: str, minutes: int) -> dict[str, Any]:
        return self._send(
            "PUT", f"/api/sources/{name}/interval", {"minutes": minutes}
        )

    def sync_all(self) -> dict[str, Any]:
        return self._send("POST", "/api/sources/sync_all")

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return _get(self.base_url, path, params)

    def _send(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return _send(self.base_url, method, path, payload)
