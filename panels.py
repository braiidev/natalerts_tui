"""Dibujo de paneles del TUI.

Funciones puras que reciben curses windows/state y pintan con color. No
manejan entrada ni estado mutante: eso vive en App.
"""

from __future__ import annotations

import curses
from typing import Any

from . import format as F
from .state import State

# IDs de color registrados en App.init_colors
C_HEADER = 1
C_CONTROLS = 2
C_ACTIVE = 3
C_NORMAL = 4
C_TITLE = 5
C_CARD = 6
C_SELECTED = 7
C_FOOTER = 8
C_TOAST = 9
C_BAR = 10


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


def draw_header(win: Any, st: State) -> None:
    h, w = win.getmaxyx()
    if h <= 0:
        return
    _fill(win, curses.color_pair(C_HEADER))
    base = st.base_url.replace("http://", "").replace("https://", "")
    loc = st.active_location()
    loc_name = loc["name"] if loc else (st.config.get("zone", {}).get("name") or "Zona")
    title = " Natural Alerts "
    _put(win, 0, 0, title, curses.color_pair(C_TITLE) | curses.A_BOLD)
    mid = f" {loc_name} " if loc_name else ""
    _put(win, 0, len(title), mid, curses.color_pair(C_HEADER) | curses.A_BOLD)
    right = base
    _put(win, 0, max(0, w - len(right) - 1), right, curses.color_pair(C_HEADER))


def draw_controls(win: Any, st: State) -> None:
    h, w = win.getmaxyx()
    if h <= 0:
        return
    _fill(win, curses.color_pair(C_CONTROLS))
    f = st.cfg
    provider = f["provider"]
    days = f["days"]
    sort = f["sort"]
    order = f["order"]
    scope = f["scope"]
    radius = f["radius"]

    y = 0
    seg_provider = f"[{F.PROVIDER_LABELS.get(provider, provider) or 'Todos'}▾]"
    seg_days = f"[{F.DAY_LABELS.get(days, str(days))}▾]"
    seg_sort = f"[{F.SORT_LABELS.get(sort, sort)}▾]"
    seg_order = f"[{'Asc ↑' if order == 'asc' else 'Desc ↓'}]"
    seg_scope = f"[{'Zona' if scope == 'zone' else F.SCOPE_LABELS.get(scope, scope) + '▾'}]"

    _put(win, y, 0, " " + seg_provider)
    _put(win, y, len(seg_provider) + 2, seg_days)
    _put(win, y, len(seg_provider) + len(seg_days) + 4, seg_sort)
    _put(win, y, len(seg_provider) + len(seg_days) + len(seg_sort) + 6, seg_order)

    # Fila 2 (si cabe) o continuar fila 1 según ancho
    seg_radius = f"[Radio {radius} km ±5]"
    start = len(seg_provider) + len(seg_days) + len(seg_sort) + len(seg_order) + 8
    _put(win, y, start, seg_radius)
    start2 = len(seg_provider) + len(seg_days) + len(seg_sort) + len(seg_order) + len(seg_radius) + 10
    _put(win, y, start2, seg_scope)
    _put(win, y + 1, 0, " [Config]", curses.color_pair(C_ACTIVE) | curses.A_BOLD)


def draw_alerts_list(win: Any, st: State, cursor: int, focus: bool) -> None:
    h, w = win.getmaxyx()
    if h <= 0:
        return
    attr_normal = curses.color_pair(C_ACTIVE if focus else C_NORMAL)
    attr_sel = curses.color_pair(C_SELECTED)
    # Header del card
    label = f" Alertas ({st.alert_count})"
    days_txt = f"últimos {st.days} d" if st.days else f"todo el período · {st.sort} {'↑' if st.order == 'asc' else '↓'}"
    if focus:
        _put(win, 0, 0, "▌" + label + " " + days_txt, attr_normal | curses.A_BOLD)
    else:
        _put(win, 0, 0, " " + label + " " + days_txt, attr_normal | curses.A_BOLD)
    for y in range(1, h):
        try:
            win.addnstr(y, 0, " " * w, w, curses.color_pair(C_NORMAL))
        except curses.error:
            pass

    if st.error_alerts:
        _put(win, 1, 1, f"Error: {st.error_alerts}", curses.color_pair(C_TOAST))
        return
    if not st.alerts:
        _put(win, 1, 1, "Sin alertas para este filtro", curses.color_pair(C_NORMAL))
        return

    body_h = h - 1
    if cursor >= len(st.alerts):
        cursor = len(st.alerts) - 1
    top = max(0, cursor - body_h + 1)
    for i in range(top, min(len(st.alerts), top + body_h)):
        y = i - top + 1
        a = st.alerts[i]
        selected = i == cursor and focus
        row = _alert_line(a)
        attr = curses.color_pair(C_SELECTED if selected else C_NORMAL)
        if selected:
            _put(win, y, 0, "▶", attr | curses.A_BOLD)
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


def draw_alerts_detail(win: Any, st: State, a: dict[str, Any] | None) -> None:
    h, w = win.getmaxyx()
    _fill(win, curses.color_pair(C_CARD))
    if a is None:
        _put(win, 0, 0, " Alertas", curses.color_pair(C_ACTIVE) | curses.A_BOLD)
        return
    _put(win, 0, 0, " ▌Detalle de alerta", curses.color_pair(C_ACTIVE) | curses.A_BOLD)
    y = 1
    d = a.get("details") or {}
    typ = F.TYPE_LABELS.get(a.get("type"), a.get("type") or "?")
    _put(win, y, 2, f"Tipo:     {typ}", curses.color_pair(C_NORMAL)); y += 1
    _put(win, y, 2, f"Fuente:   {F.SOURCE_LABELS.get(a.get('source'), a.get('source') or '')}"); y += 1
    mag = F.mag_label(a) or "—"
    _put(win, y, 2, f"Magnitud: {mag}", curses.color_pair(C_NORMAL)); y += 1
    _put(win, y, 2, f"Lugar:    {a.get('place') or a.get('title') or '—'}"); y += 1
    _put(win, y, 2, f"Hora:     {F.fmt_datetime(a.get('time'))} ({F.time_ago(a.get('time'))})"); y += 1
    sev = int(max(0, min(100, a.get("severity") or 0)))
    _put(win, y, 2, f"Severidad:{sev}/100  {_severity_bar(sev, w - 16)}", curses.color_pair(C_NORMAL)); y += 2
    dist = a.get("distance_km")
    _put(win, y, 2, f"Distancia:{f'{int(dist)} km' if dist is not None else '—'}"); y += 1
    link = F.source_link(a)
    if link:
        _put(win, y, 2, f"Link:     {link}", curses.color_pair(C_NORMAL)); y += 1
    title = a.get("title")
    if title and title != (a.get("place") or ""):
        _put(win, y, 2, f"Título:   {title}", curses.color_pair(C_NORMAL)); y += 1
    y += 1
    _put(win, y, 2, " q/h/← volver", curses.color_pair(C_FOOTER))


def _severity_bar(sev: int, width: int) -> str:
    width = max(1, width)
    filled = int((sev / 100) * width)
    return "#" * filled + "." * (width - filled)


def draw_weather(win: Any, st: State, cursor: int, focus: bool) -> None:
    h, w = win.getmaxyx()
    if h <= 0:
        return
    attr_focus = curses.color_pair(C_ACTIVE if focus else C_NORMAL)
    attr_sel = curses.color_pair(C_SELECTED)
    head = " ▌Clima" if focus else " Clima"
    _put(win, 0, 0, head, attr_focus | curses.A_BOLD)
    _fill_line = lambda y: _put(win, y, 0, " " * w, curses.color_pair(C_NORMAL))

    wd = st.weather
    if st.error_weather:
        _put(win, 1, 1, f"Error: {st.error_weather}", curses.color_pair(C_TOAST))
        return
    if not wd:
        _put(win, 1, 1, "Cargando clima...", curses.color_pair(C_NORMAL))
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

    y = 1
    _put(win, y, 2, f"{loc_name}", curses.color_pair(C_ACTIVE) | curses.A_BOLD); y += 1
    _put(win, y, 2, f"{icon} {temp}°C" if temp is not None else " —°C", curses.color_pair(C_NORMAL) | curses.A_BOLD); y += 1
    _put(win, y, 2, f"{desc}  {wind_txt}", curses.color_pair(C_NORMAL)); y += 1
    _put(win, y, 2, f"{tz} · actualizado {updated}", curses.color_pair(C_NORMAL)); y += 2

    # Toggle ubicación (+)
    _put(win, y, 2, " ▲/▼ ubicación  [+] añadir", curses.color_pair(C_ACTIVE if focus else C_NORMAL)); y += 2

    # Toggle horario/semanal
    view_txt = " [horario]" if st.weather_view == "hourly" else " [semanal]"
    _put(win, y, 2, " Ver:" + view_txt, curses.color_pair(C_ACTIVE if focus else C_NORMAL)); y += 1

    if st.weather_view == "hourly":
        y = _draw_hour_grid(win, st, cursor, focus, y, w)
    else:
        y = _draw_daily_grid(win, st, cursor, focus, y, w)


def _draw_hour_grid(win: Any, st: State, cursor: int, focus: bool, y0: int, w: int) -> int:
    hourly = (st.weather or {}).get("hourly") or {}
    times = hourly.get("time") or []
    if not times:
        _put(win, y0, 2, "Sin proyección horaria", curses.color_pair(C_NORMAL))
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
    _put(win, y0, 2, " Proyección: +1 +2 +3 horas  (◀ ▶ o h/l)", curses.color_pair(C_NORMAL)); y0 += 1
    WINDOW = 3  # +1,+2,+3
    n = len(cells)
    start = max(0, min(st.hour_window, max(0, n - WINDOW)))
    slot = cells[start : start + WINDOW]
    col_w = max(12, (w - 6) // len(slot)) if slot else 12
    for i, cell in enumerate(slot):
        x = 2 + i * (col_w + 1)
        sel = focus and cursor == i
        attr = curses.color_pair(C_SELECTED if sel else C_NORMAL)
        if sel:
            _put(win, y0, x - 1, "▶", attr | curses.A_BOLD)
        hh = F.fmt_clock(cell["t"])
        tmp = f"{int(cell['temp'])}°" if cell["temp"] is not None else ""
        wnd = f"{int(cell['wind'])}k" if cell["wind"] is not None else ""
        ic = F.wmo_icon(cell["code"])
        lines = [hh, f"{ic} {tmp}", wnd]
        for li, txt in enumerate(lines):
            _put(win, y0 + li, x, F.truncate(txt, col_w), attr)
    return y0 + 3


def _draw_daily_grid(win: Any, st: State, cursor: int, focus: bool, y0: int, w: int) -> int:
    daily = (st.weather or {}).get("daily") or {}
    times = daily.get("time") or []
    if not times:
        _put(win, y0, 2, "Sin proyección semanal", curses.color_pair(C_NORMAL))
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
    _put(win, y0, 2, f" Proyección: +1 +2 +3 días  (◀ ▶ o h/l, hasta 16d)", curses.color_pair(C_NORMAL)); y0 += 1
    WINDOW = 3
    n = len(cells)
    start = max(0, min(st.daily_window, max(0, n - WINDOW)))
    slot = cells[start : start + WINDOW]
    col_w = max(14, (w - 6) // len(slot)) if slot else 14
    for i, cell in enumerate(slot):
        x = 2 + i * (col_w + 1)
        sel = focus and cursor == i
        attr = curses.color_pair(C_SELECTED if sel else C_NORMAL)
        if sel:
            _put(win, y0, x - 1, "▶", attr | curses.A_BOLD)
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


def draw_footer(win: Any, st: State, cursor: int, focus: bool) -> None:
    h, w = win.getmaxyx()
    _fill(win, curses.color_pair(C_FOOTER))
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
            _put(win, y, x, "▶" + item, curses.color_pair(C_SELECTED) | curses.A_BOLD)
            x += 1 + len(item)
            continue
        _put(win, y, x, item, curses.color_pair(C_FOOTER))
        x += len(item)
        if x > w - 20:
            break

    # Fila 1: reloj + countdown + Sync All + Config
    y = min(1, h - 1)
    right = "[Config]  [Sync All]"
    _put(win, y, max(0, w - len(right) - 1), right, curses.color_pair(C_FOOTER))


def draw_toast(st: State, win: Any) -> None:
    if not st.toast:
        return
    h, w = win.getmaxyx()
    msg = F.truncate(st.toast, w - 6)
    box_w = len(msg) + 4
    y = h - 3
    x = max(0, (w - box_w) // 2)
    attr = curses.color_pair(C_TOAST) | curses.A_BOLD
    try:
        win.addstr(y, x, " " * box_w, attr)
        win.addstr(y, x, " " + msg + " ", attr)
    except curses.error:
        pass
