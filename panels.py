"""Dibujo de paneles del TUI.

Funciones puras que reciben curses windows/state/theme y pintan. No manejan
entrada ni estado mutante: eso vive en App. Los colores vienen en un dict
``pairs`` (roles semánticos del tema — ver theme.py) en vez de constantes.
"""

from __future__ import annotations

import curses
import time
from typing import Any

from . import format as F
from .state import TOAST_TTL, State


def _put(win: Any, y: int, x: int, text: str, attr: int = 0) -> None:
    try:
        win.addstr(y, x, F.truncate(text, max(0, win.getmaxyx()[1] - x)), attr)
    except curses.error:
        pass


def _fill(win: Any, attr: int) -> None:
    h, w = win.getmaxyx()
    for y in range(h):
        try:
            win.addnstr(y, 0, " " * w, w, attr)
        except curses.error:
            pass


def draw_separator(win: Any, pairs: dict[str, int]) -> None:
    """Regla horizontal simple (divisor entre secciones)."""
    h, w = win.getmaxyx()
    if h <= 0:
        return
    win.erase()
    _put(win, 0, 0, "─" * w, pairs["divider"])


def draw_header(win: Any, st: State, pairs: dict[str, int]) -> None:
    h, w = win.getmaxyx()
    if h <= 0:
        return
    win.erase()
    _fill(win, pairs["header"])
    base = st.base_url.replace("http://", "").replace("https://", "")
    loc = st.active_location()
    loc_name = loc["name"] if loc else (st.config.get("zone", {}).get("name") or "Zona")
    title = " Natural Alerts "
    _put(win, 0, 0, title, pairs["header"] | curses.A_BOLD)
    mid = f" {loc_name} " if loc_name else ""
    _put(win, 0, len(title), mid, pairs["header"] | curses.A_BOLD)
    right = base
    _put(win, 0, max(0, w - len(right) - 1), right, pairs["header"] | curses.A_DIM)


def draw_controls(win: Any, st: State, pairs: dict[str, int], cursor: int, focus: bool) -> None:
    h, w = win.getmaxyx()
    if h <= 0:
        return
    win.erase()
    _fill(win, pairs["controls"])
    f = st.cfg
    provider = f["provider"]
    days = f["days"]
    sort = f["sort"]
    order = f["order"]
    scope = f["scope"]
    radius = f["radius"]

    segs = [
        f"[{F.PROVIDER_LABELS.get(provider, provider) or 'Todos'}▾]",
        f"[{F.DAY_LABELS.get(days, str(days))}▾]",
        f"[{F.SORT_LABELS.get(sort, sort)}▾]",
        f"[{'Asc ↑' if order == 'asc' else 'Desc ↓'}]",
        f"[Radio {radius} km ±5]",
        f"[{'Zona' if scope == 'zone' else F.SCOPE_LABELS.get(scope, scope) + '▾'}]",
    ]
    y = 0
    x = 0
    for i, seg in enumerate(segs):
        attr = pairs["controls"]
        if focus and cursor == i:
            attr = pairs["filter_active"]
        _put(win, y, x, " " + seg, attr)
        x += 1 + len(seg) + 1
        if x > w:
            break


def draw_alerts_list(win: Any, st: State, cursor: int, focus: bool, pairs: dict[str, int]) -> None:
    h, w = win.getmaxyx()
    if h <= 0:
        return
    win.erase()
    attr_title = pairs["accent"] if focus else pairs["text"]
    # Header del card + regla divisora bajo el título
    label = f" Alertas ({st.alert_count})"
    days_txt = f"últimos {st.days} d" if st.days else f"todo el período · {st.sort} {'↑' if st.order == 'asc' else '↓'}"
    prefix = "▌" if focus else " "
    _put(win, 0, 0, prefix + label + " " + days_txt, attr_title | curses.A_BOLD)
    _put(win, 1, 0, "─" * w, pairs["divider"])
    for y in range(2, h):
        try:
            win.addnstr(y, 0, " " * w, w, pairs["text"])
        except curses.error:
            pass

    if st.error_alerts:
        _put(win, 3, 1, f"Error: {st.error_alerts}", pairs["error"])
        return
    if not st.alerts:
        _put(win, 3, 1, "Sin alertas para este filtro", pairs["text"])
        return

    body_h = h - 2
    if cursor >= len(st.alerts):
        cursor = len(st.alerts) - 1
    top = max(0, cursor - body_h + 1)
    for i in range(top, min(len(st.alerts), top + body_h)):
        y = i - top + 2
        a = st.alerts[i]
        selected = i == cursor and focus
        row = _alert_line(a)
        attr = pairs["selected"] if selected else pairs["text"]
        if selected:
            _put(win, y, 0, "▶", pairs["accent"] | curses.A_BOLD)
        _put(win, y, 2, F.truncate(row, w - 3), attr)


def _alert_line(a: dict[str, Any]) -> str:
    typ = F.TYPE_LABELS.get(a.get("type"), a.get("type") or "?")
    mag = F.mag_label(a)
    mag_txt = f" {mag}" if mag else ""
    place = a.get("place") or a.get("title") or ""
    sev = int(max(0, min(100, a.get("severity") or 0)))
    dist = f" {int(a.get('distance_km'))} km" if a.get("distance_km") is not None else ""
    src = F.SOURCE_LABELS.get(a.get("source"), a.get("source") or "")
    rel = F.time_ago(a.get("time"))
    return f"{typ:<11} {mag_txt:<6} {place} · {rel} · {sev}/100{dist} · {src}"


def draw_alerts_detail(win: Any, st: State, a: dict[str, Any] | None, pairs: dict[str, int]) -> None:
    h, w = win.getmaxyx()
    win.erase()
    _fill(win, pairs["text"])
    if a is None:
        _put(win, 0, 0, " Alertas", pairs["accent"] | curses.A_BOLD)
        return
    _put(win, 0, 0, " ▌Detalle de alerta", pairs["accent"] | curses.A_BOLD)
    _put(win, 1, 0, "─" * w, pairs["divider"])
    y = 2
    d = a.get("details") or {}
    typ = F.TYPE_LABELS.get(a.get("type"), a.get("type") or "?")
    _put(win, y, 2, f"Tipo:     {typ}", pairs["text"]); y += 1
    _put(win, y, 2, f"Fuente:   {F.SOURCE_LABELS.get(a.get('source'), a.get('source') or '')}", pairs["text"]); y += 1
    mag = F.mag_label(a) or "—"
    _put(win, y, 2, f"Magnitud: {mag}", pairs["text"]); y += 1
    _put(win, y, 2, f"Lugar:    {a.get('place') or a.get('title') or '—'}", pairs["text"]); y += 1
    _put(win, y, 2, f"Hora:     {F.fmt_datetime(a.get('time'))} ({F.time_ago(a.get('time'))})", pairs["text"]); y += 1
    sev = int(max(0, min(100, a.get("severity") or 0)))
    sev_attr = pairs["sev_high"] if sev >= 66 else pairs["sev_med"] if sev >= 33 else pairs["sev_low"]
    _put(win, y, 2, f"Severidad:{sev}/100  {_severity_bar(sev, w - 16)}", sev_attr); y += 2
    dist = a.get("distance_km")
    _put(win, y, 2, f"Distancia:{f'{int(dist)} km' if dist is not None else '—'}", pairs["text"]); y += 1
    link = F.source_link(a)
    if link:
        _put(win, y, 2, f"Link:     {link}", pairs["text"]); y += 1
    title = a.get("title")
    if title and title != (a.get("place") or ""):
        _put(win, y, 2, f"Título:   {title}", pairs["text"]); y += 1
    y += 1
    _put(win, y, 2, " q/h/← volver", pairs["text_dim"])


def _severity_bar(sev: int, width: int) -> str:
    width = max(1, width)
    filled = int((sev / 100) * width)
    return "#" * filled + "." * (width - filled)


def draw_weather(win: Any, st: State, cursor: int, focus: bool, pairs: dict[str, int]) -> None:
    h, w = win.getmaxyx()
    if h <= 0:
        return
    win.erase()
    attr_title = pairs["accent"] if focus else pairs["text"]
    head = " ▌Clima" if focus else " Clima"
    _put(win, 0, 0, head, attr_title | curses.A_BOLD)
    _put(win, 1, 0, "─" * w, pairs["divider"])

    wd = st.weather
    if st.error_weather:
        _put(win, 3, 1, f"Error: {st.error_weather}", pairs["error"])
        return
    if not wd:
        _put(win, 3, 1, "Cargando clima...", pairs["text"])
        return

    loc = st.active_location()
    loc_name = loc["name"] if loc else (st.config.get("zone", {}).get("name") or "Zona")
    temp = wd.get("temperature_c")
    desc = wd.get("weather_description") or "—"
    wind = wd.get("windspeed_kmh")
    wind_txt = f"Viento {wind} km/h" if wind is not None else ""
    if wd.get("winddirection") is not None:
        wind_txt += f" · {wd['winddirection']}°"
    tz = (wd.get("timezone") or "Open-Meteo").split("/")[-1]
    updated = F.time_ago(wd.get("fetched_at"))
    icon = F.wmo_icon(wd.get("weathercode"))

    y = 2
    _put(win, y, 2, f"{loc_name}", pairs["accent"] | curses.A_BOLD); y += 1
    _put(win, y, 2, f"{icon} {temp}°C" if temp is not None else " —°C", pairs["text"] | curses.A_BOLD); y += 1
    _put(win, y, 2, f"{desc}  {wind_txt}", pairs["text"]); y += 1
    _put(win, y, 2, f"{tz} · actualizado {updated}", pairs["text_dim"]); y += 2

    # Toggle ubicación (+)
    row_loc = (pairs["selected"] if focus and cursor == 0
               else pairs["accent"] if focus
               else pairs["text"])
    _put(win, y, 2, " ▲/▼ ubicación  [+] añadir  [m] gestionar", row_loc); y += 2

    # Toggle horario/semanal
    view_txt = " [horario]" if st.weather_view == "hourly" else " [semanal]"
    row_view = (pairs["selected"] if focus and cursor == 1
                else pairs["accent"] if focus
                else pairs["text"])
    _put(win, y, 2, " Ver:" + view_txt, row_view); y += 1

    # Celda seleccionada en la grilla: cursor 2..4 (cell_idx = cursor - 2).
    cell_cursor = cursor - 2 if focus and cursor >= 2 else -1
    if st.weather_view == "hourly":
        y = _draw_hour_grid(win, st, cell_cursor, focus, pairs, y, w)
    else:
        y = _draw_daily_grid(win, st, cell_cursor, focus, pairs, y, w)


def _draw_hour_grid(win: Any, st: State, cursor: int, focus: bool, pairs: dict[str, int], y0: int, w: int) -> int:
    hourly = (st.weather or {}).get("hourly") or {}
    times = hourly.get("time") or []
    if not times:
        _put(win, y0, 2, "Sin proyección horaria", pairs["text"])
        return y0 + 1
    # construir celdas hora
    cells = []
    for i, t in enumerate(times):
        cells.append({
            "t": t,
            "temp": _arr(hourly, "temperature_2m", i),
            "code": _arr(hourly, "weathercode", i),
            "wind": _arr(hourly, "wind_speed_10m", i),
            "gust": _arr(hourly, "windgusts_10m", i),
            "precip": _arr(hourly, "precipitation", i),
            "pop": _arr(hourly, "precipitation_probability", i),
            "hum": _arr(hourly, "relativehumidity_2m", i),
            "feels": _arr(hourly, "apparent_temperature", i),
            "cloud": _arr(hourly, "cloudcover", i),
            "press": _arr(hourly, "pressure_msl", i),
        })
    _put(win, y0, 2, " Proyección: +1 +2 +3 horas  (◀ ▶ o h/l)", pairs["text"]); y0 += 1
    WINDOW = 3  # +1,+2,+3
    n = len(cells)
    start = max(0, min(st.hour_window, max(0, n - WINDOW)))
    slot = cells[start : start + WINDOW]
    col_w = max(12, (w - 6) // len(slot)) if slot else 12
    for i, cell in enumerate(slot):
        x = 2 + i * (col_w + 1)
        sel = focus and cursor == i
        attr = pairs["selected"] if sel else pairs["text"]
        if sel:
            _put(win, y0, x - 1, "▶", pairs["accent"] | curses.A_BOLD)
        hh = F.fmt_clock(cell["t"])
        tmp = f"{int(cell['temp'])}°" if cell["temp"] is not None else ""
        wnd = f"{int(cell['wind'])}k" if cell["wind"] is not None else ""
        ic = F.wmo_icon(cell["code"])
        lines = [hh, f"{ic} {tmp}", wnd]
        for li, txt in enumerate(lines):
            _put(win, y0 + li, x, F.truncate(txt, col_w), attr)
    return y0 + 3


def _draw_daily_grid(win: Any, st: State, cursor: int, focus: bool, pairs: dict[str, int], y0: int, w: int) -> int:
    daily = (st.weather or {}).get("daily") or {}
    times = daily.get("time") or []
    if not times:
        _put(win, y0, 2, "Sin proyección semanal", pairs["text"])
        return y0 + 1
    cells = []
    for i, t in enumerate(times):
        cells.append({
            "t": t,
            "code": _arr(daily, "weathercode", i),
            "tmax": _arr(daily, "temperature_2m_max", i),
            "tmin": _arr(daily, "temperature_2m_min", i),
            "precip": _arr(daily, "precipitation_sum", i),
            "sunrise": _arr(daily, "sunrise", i),
            "sunset": _arr(daily, "sunset", i),
            "uv": _arr(daily, "uv_index_max", i),
            "windMax": _arr(daily, "wind_speed_10m_max", i),
        })
    _put(win, y0, 2, f" Proyección: +1 +2 +3 días  (◀ ▶ o h/l, hasta 16d)", pairs["text"]); y0 += 1
    WINDOW = 3
    n = len(cells)
    start = max(0, min(st.daily_window, max(0, n - WINDOW)))
    slot = cells[start : start + WINDOW]
    col_w = max(14, (w - 6) // len(slot)) if slot else 14
    for i, cell in enumerate(slot):
        x = 2 + i * (col_w + 1)
        sel = focus and cursor == i
        attr = pairs["selected"] if sel else pairs["text"]
        if sel:
            _put(win, y0, x - 1, "▶", pairs["accent"] | curses.A_BOLD)
        name = "Hoy" if i == 0 and start == 0 else F.fmt_day(cell["t"])
        ic = F.wmo_icon(cell["code"])
        tmax = f"{int(cell['tmax'])}°" if cell["tmax"] is not None else ""
        tmin = f"{int(cell['tmin'])}°" if cell["tmin"] is not None else ""
        ppt = f" {cell['precip']}mm" if cell["precip"] else ""
        lines = [name, f"{ic}", f"max {tmax}  min {tmin}{ppt}"]
        for li, txt in enumerate(lines):
            _put(win, y0 + li, x, F.truncate(txt, col_w), attr)
    return y0 + 3


def _arr(data: dict[str, Any], key: str, i: int) -> Any:
    arr = data.get(key)
    if isinstance(arr, list) and i < len(arr):
        return arr[i]
    return None


def draw_footer(win: Any, st: State, cursor: int, focus: bool, pairs: dict[str, int]) -> None:
    h, w = win.getmaxyx()
    win.erase()
    _fill(win, pairs["footer"])
    cfg = st.config
    sources = cfg.get("sources", {})
    names = list(sources.keys())
    # Botones de fuentes en fila 0
    y = 0
    x = 0
    for i, name in enumerate(names):
        s = sources[name]
        label = F.SOURCE_LABELS.get(name, name)
        status = "ok" if s.get("ok") else ("err" if s.get("error") else "…" if s.get("running") else "off")
        last = F.fmt_clock(s.get("last_fetch_at"))
        item = f" [{label} {status}] {last}"
        if i == cursor and focus:
            _put(win, y, x, "▶" + item, pairs["selected"] | curses.A_BOLD)
            x += 1 + len(item)
            continue
        if status == "ok":
            attr = pairs["accent"]
        elif status == "err":
            attr = pairs["error"]
        else:
            attr = pairs["footer"]
        _put(win, y, x, item, attr)
        x += len(item)
        if x > w - 20:
            break

    # Fila 1: reloj + countdown + Sync All + Config
    y = min(1, h - 1)
    right = "[Config]  [Sync All]"
    _put(win, y, max(0, w - len(right) - 1), right, pairs["footer"])


def draw_toast(st: State, win: Any, pairs: dict[str, int]) -> None:
    if not st.toast:
        return
    # expiración del toast: se limpia solo tras TTL
    if st.toast_at is not None and time.monotonic() - st.toast_at > TOAST_TTL:
        st.toast = None
        st.toast_at = None
        return
    h, w = win.getmaxyx()
    msg = F.truncate(st.toast, w - 6)
    box_w = len(msg) + 4
    y = h - 3
    x = max(0, (w - box_w) // 2)
    attr = pairs["toast"] | curses.A_BOLD
    try:
        win.addstr(y, x, " " * box_w, attr)
        win.addstr(y, x, " " + msg + " ", attr)
    except curses.error:
        pass