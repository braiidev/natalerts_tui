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
    right = f" {base} "
    if st.connected is False:
        right = " [SIN SERVER] " + right
        _put(win, 0, max(0, w - len(right) - 1), right, pairs["header"] | pairs["error"] | curses.A_BOLD)
    else:
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
        f"[{F.EVENT_TYPE_LABELS.get(st.event_type, st.event_type)}▾]",
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


def _alert_parts(a: dict[str, Any]) -> tuple[str, str, str]:
    """Partes de la línea de alerta: (pre, sev_txt, suf) para colorear la severidad."""
    typ = F.TYPE_LABELS.get(a.get("type"), a.get("type") or "?")
    mag = F.mag_label(a) or "—"
    mag_txt = f" {mag}"
    place = a.get("place") or a.get("title") or ""
    sev = int(max(0, min(100, a.get("severity") or 0)))
    dist = f" {int(a.get('distance_km'))} km" if a.get("distance_km") is not None else ""
    src = F.SOURCE_LABELS.get(a.get("source"), a.get("source") or "")
    rel = F.time_ago(a.get("time"))
    pre = f"{typ:<11} {mag_txt:<6} {place} · {rel} · "
    sev_txt = f"{sev}/100"
    suf = f"{dist} · {src}"
    return pre, sev_txt, suf


def _severity_attr(pairs: dict[str, int], sev: int) -> int:
    """Color de severidad por umbral: <33 baja, <66 media, >=66 alta."""
    if sev >= 66:
        return pairs["sev_high"]
    if sev >= 33:
        return pairs["sev_med"]
    return pairs["sev_low"]


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
        pre, sev_txt, suf = _alert_parts(a)
        attr = pairs["selected"] if selected else pairs["text"]
        sev_attr = _severity_attr(pairs, int(a.get("severity") or 0))
        if selected:
            attr = pairs["selected"]
            sev_attr = pairs["selected"]
            _put(win, y, 0, "▶", pairs["accent"] | curses.A_BOLD)
        _put(win, y, 2, F.truncate(pre, max(0, w - 3)), attr)
        x_sev = 2 + len(pre)
        if x_sev < w - 3:
            _put(win, y, x_sev, F.truncate(sev_txt, max(0, w - 3 - x_sev)), sev_attr)
        x_suf = x_sev + len(sev_txt)
        if x_suf < w - 3:
            _put(win, y, x_suf, F.truncate(suf, max(0, w - 3 - x_suf)), attr)


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
    typ = F.TYPE_LABELS.get(a.get("type"), a.get("type") or "?")
    _put(win, y, 2, f"Tipo:     {typ}", pairs["text"]); y += 1
    _put(win, y, 2, f"Fuente:   {F.SOURCE_LABELS.get(a.get('source'), a.get('source') or '')}", pairs["text"]); y += 1
    mag = F.mag_label(a) or "—"
    _put(win, y, 2, f"Magnitud: {mag}", pairs["text"]); y += 1
    _put(win, y, 2, f"Lugar:    {a.get('place') or a.get('title') or '—'}", pairs["text"]); y += 1
    _put(win, y, 2, f"Hora:     {F.fmt_datetime(a.get('time'))} ({F.time_ago(a.get('time'))})", pairs["text"]); y += 1
    sev = int(max(0, min(100, a.get("severity") or 0)))
    sev_attr = _severity_attr(pairs, sev)
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
        wind_txt += f" {F.compass(wd['winddirection'])}"
    tz = (wd.get("timezone") or "Open-Meteo").split("/")[-1].replace("_", " ")
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
    _put(win, y, 2, " ▲/▼ ubicación  [+] añadir", row_loc); y += 2

    # Toggle horario/semanal
    view_txt = " [horario]" if st.weather_view == "hourly" else " [semanal]"
    row_view = (pairs["selected"] if focus and cursor == 1
                else pairs["accent"] if focus
                else pairs["text"])
    _put(win, y, 2, " Ver:" + view_txt, row_view); y += 1

    # Celda seleccionada en la grilla (solo con focus en la fila de celdas).
    cell_cursor = st.weather_cell if focus and cursor == 2 else -1
    if st.weather_view == "hourly":
        y = _draw_hour_grid(win, st, cell_cursor, focus, pairs, y, w)
    else:
        y = _draw_daily_grid(win, st, cell_cursor, focus, pairs, y, w)


def _draw_hour_grid(win: Any, st: State, cell: int, focus: bool, pairs: dict[str, int], y0: int, w: int) -> int:
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
        })
    WINDOW = 3
    n = len(cells)
    start = _window_start(cell, n, WINDOW)
    slot = cells[start : start + WINDOW]
    col_w = max(12, (w - 6) // len(slot)) if slot else 12
    for k, c in enumerate(slot):
        i = start + k
        x = 2 + k * (col_w + 1)
        sel = focus and cell == i
        base = pairs["selected"] if sel else pairs["text"]
        if sel:
            _put(win, y0, x - 1, "▶", pairs["accent"] | curses.A_BOLD)
        # hora bold; icono accent + temp bold; viento dim
        _put(win, y0, x, F.truncate(F.fmt_clock(c["t"]), col_w),
             base if sel else pairs["text"] | curses.A_BOLD)
        ic = F.wmo_icon(c["code"])
        tmp = f"{int(c['temp'])}°" if c["temp"] is not None else ""
        if sel:
            _put(win, y0 + 1, x, F.truncate(f"{ic} {tmp}", col_w), base)
        else:
            _put(win, y0 + 1, x, F.truncate(ic, col_w), pairs["accent"])
            x_tmp = x + len(ic) + 1
            if x_tmp < w - 1:
                _put(win, y0 + 1, x_tmp, F.truncate(tmp, max(0, w - 1 - x_tmp)),
                     pairs["text"] | curses.A_BOLD)
        wnd = f"{int(c['wind'])} km/h" if c["wind"] is not None else ""
        _put(win, y0 + 2, x, F.truncate(wnd, col_w), base if sel else pairs["text_dim"])
    return y0 + 3


def _draw_daily_grid(win: Any, st: State, cell: int, focus: bool, pairs: dict[str, int], y0: int, w: int) -> int:
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
        })
    WINDOW = 3
    n = len(cells)
    start = _window_start(cell, n, WINDOW)
    slot = cells[start : start + WINDOW]
    col_w = max(14, (w - 6) // len(slot)) if slot else 14
    for k, c in enumerate(slot):
        i = start + k
        x = 2 + k * (col_w + 1)
        sel = focus and cell == i
        base = pairs["selected"] if sel else pairs["text"]
        if sel:
            _put(win, y0, x - 1, "▶", pairs["accent"] | curses.A_BOLD)
        name = "Hoy" if i == 0 else F.fmt_day(c["t"])
        name_attr = base if sel else (pairs["accent"] if name == "Hoy" else pairs["text"] | curses.A_BOLD)
        _put(win, y0, x, F.truncate(name, col_w), name_attr)
        # icono en accent
        ic = F.wmo_icon(c["code"])
        _put(win, y0 + 1, x, F.truncate(ic, col_w), base if sel else pairs["accent"])
        # temps: max bold, min + precipitación dim
        tmax = f"{int(c['tmax'])}°" if c["tmax"] is not None else ""
        tmin = f"{int(c['tmin'])}°" if c["tmin"] is not None else ""
        ppt = f" {c['precip']}mm" if c["precip"] else ""
        _put(win, y0 + 2, x, F.truncate("max " + tmax, col_w),
             base if sel else pairs["text"] | curses.A_BOLD)
        if not sel:
            x_min = x + len("max " + tmax)
            if x_min < w - 1:
                _put(win, y0 + 2, x_min, F.truncate(" min " + tmin + ppt, max(0, w - 1 - x_min)),
                     pairs["text_dim"])
    return y0 + 3


def _window_start(cell: int, n: int, window: int) -> int:
    """Desplazamiento de la ventana para que la celda seleccionada quede visible.

    Con focus en la grilla (cell >= 0) centra la celda; sin lo usa el último
    valor (la ventana conserva su posición al volver a la sección).
    """
    if n <= window:
        return 0
    if cell < 0:
        cell = 1
    return max(0, min(cell - (window // 2), n - window))


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
    # Fila 0: tira interactiva — fuentes + [Config] + [Sync All], con el
    # elemento bajo el cursor destacado igual que en el resto de la app.
    y = 0
    x = 0
    for i, name in enumerate(names):
        s = sources[name]
        label = F.SOURCE_LABELS.get(name, name)
        status = "ok" if s.get("ok") else ("err" if s.get("error") else "…" if s.get("running") else "off")
        last = F.fmt_clock(s.get("last_fetch_at"))
        item = f" [{label} {status}] {last}"
        if focus and cursor == i:
            _put(win, y, x, "▶" + item, pairs["selected"] | curses.A_BOLD)
            x += 1 + len(item)
        else:
            if status == "ok":
                attr = pairs["accent"]
            elif status == "err":
                attr = pairs["error"]
            else:
                attr = pairs["footer"]
            _put(win, y, x, item, attr)
            x += len(item)
        if x >= w - 1:
            break
    # Botones a continuación, mismos índices de cursor que _key_footer.
    for j, label in enumerate(("[Config]", "[Sync All]")):
        idx = len(names) + j
        if x >= w - 1:
            break
        item = f" {label}"
        if focus and cursor == idx:
            _put(win, y, x, "▶" + item, pairs["selected"] | curses.A_BOLD)
        else:
            _put(win, y, x, item, pairs["footer"])
        x += 1 + len(item)


def draw_toast(st: State, win: Any, pairs: dict[str, int]) -> None:
    h, w = win.getmaxyx()
    win.erase()
    if not st.toast:
        return
    # expiración del toast: se limpia solo tras TTL
    if st.toast_at is not None and time.monotonic() - st.toast_at > TOAST_TTL:
        st.toast = None
        st.toast_at = None
        return
    msg = F.truncate(st.toast, w - 6)
    box_w = len(msg) + 4
    x = max(0, (w - box_w) // 2)
    attr = pairs["toast"] | curses.A_BOLD
    try:
        win.addstr(0, x, " " * box_w, attr)
        win.addstr(0, x, " " + msg + " ", attr)
    except curses.error:
        pass