"""Formato y etiquetas (espejo puro de web/static/js/constants.js)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# Etiquetas por tipo de evento
TYPE_LABELS: dict[str, str] = {
    "earthquake": "Terremoto", "tsunami": "Maremoto", "tornado": "Tornado",
    "cyclone": "Ciclón", "storm": "Tormenta", "flood": "Inundación",
    "fire": "Incendio", "volcano": "Volcán", "drought": "Sequía",
    "landslide": "Deslizamiento", "dust_haze": "Polvo/humo", "manmade": "Humano",
    "sea_lake_ice": "Hielo", "snow": "Nieve", "temperature": "Temperatura",
    "other": "Otro",
}

# Color ANSI (16 colores básicos de curses) por tipo
TYPE_COLOR: dict[str, int] = {
    "earthquake": 1, "tsunami": 1, "tornado": 5, "cyclone": 4, "storm": 3,
    "flood": 4, "fire": 3, "volcano": 8, "drought": 3, "landslide": 8,
    "dust_haze": 6, "sea_lake_ice": 6, "snow": 7, "temperature": 3,
    "manmade": 7, "other": 7,
}

SOURCE_LABELS: dict[str, str] = {
    "usgs": "USGS", "eonet": "NASA EONET", "gdacs": "GDACS",
    "open_meteo": "Open-Meteo",
}

PROVIDER_LABELS: dict[str, str] = {
    "all": "Todos", "usgs": "USGS", "eonet": "NASA EONET",
    "gdacs": "GDACS", "open_meteo": "Open-Meteo",
}

DAY_LABELS: dict[int, str] = {1: "24 h", 7: "7 d", 30: "30 d", 90: "90 d", 0: "Todos"}

SORT_LABELS: dict[str, str] = {
    "severity": "Urgencia", "time": "Fecha", "distance": "Distancia",
}

SCOPE_LABELS: dict[str, str] = {
    "world": "Mundo", "country": "País", "zone": "Zona",
}

# Íconos ASCII (códigos WMO de Open-Meteo)
def wmo_icon(code: int | None) -> str:
    if code is None:
        return "~"
    if code <= 1:
        return "☀"
    if code <= 3:
        return "☁"
    if code in (45, 48):
        return "≡"
    if 71 <= code <= 77:
        return "❄"
    if code >= 95:
        return "⚡"
    if code >= 51:
        return "☂"
    return "☁"


def wmo_desc(code: int | None) -> str:
    descs = {
        0: "Despejado", 1: "Mayormente despejado", 2: "Parcialmente nublado",
        3: "Nublado", 45: "Niebla", 48: "Niebla con escarcha",
        51: "Llovizna ligera", 53: "Llovizna moderada", 55: "Llovizna densa",
        61: "Lluvia ligera", 63: "Lluvia moderada", 65: "Lluvia fuerte",
        71: "Nieve ligera", 73: "Nieve moderada", 75: "Nieve fuerte",
        80: "Chubascos ligeros", 81: "Chubascos moderados", 82: "Chubascos violentos",
        95: "Tormenta eléctrica", 96: "Tormenta con granizo ligero",
        99: "Tormenta con granizo fuerte",
    }
    return descs.get(code, "Desconocido")


def _parse_iso(iso: str | None) -> datetime | None:
    if not iso:
        return None
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return t
    except (ValueError, TypeError):
        return None


def time_ago(iso: str | None, now: datetime | None = None) -> str:
    t = _parse_iso(iso)
    now = now or datetime.now(timezone.utc)
    if t is None:
        return ""
    delta = now - t
    m = int(delta.total_seconds() // 60)
    if m < 1:
        return "ahora"
    if m < 60:
        return f"hace {m} min"
    h = m // 60
    if h < 24:
        return f"hace {h} h"
    d = h // 24
    return "ayer" if d == 1 else f"hace {d} d"


def fmt_clock(iso: str | None, tz: str | None = None) -> str:
    t = _parse_iso(iso)
    if t is None:
        return "—"
    if tz:
        try:
            from zoneinfo import ZoneInfo
            t = t.astimezone(ZoneInfo(tz))
        except Exception:
            pass
    return t.strftime("%H:%M")


def fmt_day(iso: str | None) -> str:
    if not iso:
        return ""
    if len(iso) == 10 and "-" in iso:  # yyyy-mm-dd (medianoche local)
        try:
            d = datetime.strptime(iso, "%Y-%m-%d")
        except ValueError:
            d = _parse_iso(iso)
    else:
        d = _parse_iso(iso)
    if d is None:
        return ""
    import locale
    try:
        return d.strftime("%a %d")
    finally:
        pass


def fmt_datetime(iso: str | None) -> str:
    t = _parse_iso(iso)
    if t is None:
        return "—"
    return t.strftime("%d %b · %H:%M")


def mag_label(a: dict[str, Any]) -> str:
    d = a.get("details") or {}
    if d.get("mag") is not None:
        try:
            return f"M {float(d['mag']):.1f}"
        except (TypeError, ValueError):
            return ""
    if d.get("magnitude_value") is not None:
        unit = f" {d.get('magnitude_unit', '')}".rstrip()
        try:
            return f"{float(d['magnitude_value']):.1f}{unit}"
        except (TypeError, ValueError):
            return ""
    return ""


def source_link(a: dict[str, Any]) -> str | None:
    d = a.get("details") or {}
    return a.get("source_url") or d.get("url") or d.get("link") or None


def compass(deg: int | None) -> str:
    """Dirección del viento a punto cardinal (0=N, 90=E, ...)."""
    if deg is None:
        return ""
    dirs = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
    ]
    return dirs[int((float(deg) % 360.0) / 22.5) % 16]


def truncate(s: str, width: int) -> str:
    """Recorta a `width` con elipsis, respetando ancho visible aprox."""
    if s is None:
        s = ""
    s = str(s)
    if len(s) <= width:
        return s
    if width <= 1:
        return "…"
    return s[: width - 1] + "…"
