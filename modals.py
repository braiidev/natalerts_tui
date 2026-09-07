"""Modales del TUI: detalle de alerta, detalle de clima, ubicaciones, fuente, config.

Cada modal es una ventana centrada/absoluta que captura todas las teclas.
Devuelven un "resultado" (acción de vuelta) para que App la procese, o None
si solo hay que cerrar.
"""

from __future__ import annotations

import curses
from typing import Any, Callable

from . import format as F
from .state import State

# Retornos de acciones de modales
BACK = "back"          # solo cerrar y volver
SYNCED = "synced"      # se ejecutó una sync/refresh (recargar config)
DELETED = "deleted"    # se eliminó una ubicación


def _box(scr: Any, y: int, x: int, h: int, w: int, title: str) -> Any:
    win = curses.newwin(h, w, y, x)
    win.box()
    try:
        win.addstr(0, 1, F.truncate(title, w - 2), curses.A_BOLD)
    except curses.error:
        pass
    return win


def alert_detail(scr: Any, a: dict[str, Any]) -> None:
    """Modal de detalle ampliado de una alerta."""
    h, w = scr.getmaxyx()
    d = a.get("details") or {}
    lines: list[tuple[str, str]] = [
        ("Tipo", F.TYPE_LABELS.get(a.get("type"), a.get("type") or "-")),
        ("Fuente", F.SOURCE_LABELS.get(a.get("source"), a.get("source") or "-")),
        ("Magnitud", F.mag_label(a) or "—"),
        ("Lugar", a.get("place") or a.get("title") or "—"),
        ("Hora", f"{F.fmt_datetime(a.get('time'))} ({F.time_ago(a.get('time'))})"),
        ("Distancia", f"{int(a.get('distance_km'))} km" if a.get("distance_km") is not None else "—"),
        ("Severidad", f"{int(max(0, min(100, a.get('severity') or 0)))}/100"),
    ]
    link = F.source_link(a)
    if link:
        lines.append(("Link", link))
    if a.get("title") and a.get("title") != (a.get("place") or ""):
        lines.append(("Título", a["title"]))
    for k, v in sorted(d.items()):
        if k in ("mag", "magnitude_value", "magnitude_unit", "url", "link", "country_scope"):
            continue
        if v is not None and str(v):
            lines.append((k.replace("_", " ").title(), str(v)))

    box_h = min(h - 2, len(lines) + 4)
    box_w = min(w - 4, max(40, max(len(l[0] + l[1]) + 6 for l in lines)))
    by = max(0, (h - box_h) // 2)
    bx = max(0, (w - box_w) // 2)
    win = _box(scr, by, bx, box_h, box_w, " Detalle de alerta ")

    def draw(_: Any) -> None:
        for i, (label, val) in enumerate(lines[: box_h - 4]):
            try:
                win.addstr(i + 1, 2, F.truncate(f"{label}: {val}", box_w - 4))
            except curses.error:
                pass
        try:
            win.addstr(box_h - 2, 2, " q / h / ← volver", curses.A_DIM)
        except curses.error:
            pass
        win.touchwin()
        win.refresh()

    try:
        while True:
            scr.refresh()
            draw(scr)
            key = scr.getch()
            if key in (ord("q"), ord("h"), curses.KEY_LEFT, 27):
                return None
    finally:
        win.erase()
        win.touchwin()
        win.refresh()


def weather_detail(scr: Any, title: str, lines: list[tuple[str, str]]) -> None:
    """Modal de detalle de una celda de clima (horaria o diaria)."""
    h, w = scr.getmaxyx()
    box_h = min(h - 2, len(lines) + 4)
    box_w = min(w - 4, max(36, max((len(l[0] + l[1]) + 6) for l in lines) + 4))
    by = max(0, (h - box_h) // 2)
    bx = max(0, (w - box_w) // 2)
    win = _box(scr, by, bx, box_h, box_w, f" {title} ")

    def draw(_: Any) -> None:
        for i, (label, val) in enumerate(lines[: box_h - 4]):
            try:
                win.addstr(i + 1, 2, F.truncate(f"{label}: {val}", box_w - 4))
            except curses.error:
                pass
        try:
            win.addstr(box_h - 2, 2, " q / h / ← volver", curses.A_DIM)
        except curses.error:
            pass
        win.touchwin()
        win.refresh()

    try:
        while True:
            scr.refresh()
            draw(scr)
            key = scr.getch()
            if key in (ord("q"), ord("h"), curses.KEY_LEFT, 27):
                return None
    finally:
        win.erase()
        win.touchwin()
        win.refresh()


def _prompt(scr: Any, title: str, initial: str = "") -> str | None:
    """Prompt de una línea con el texto que se tipea."""
    h, w = scr.getmaxyx()
    box_w = min(w - 6, 60)
    box_h = 5
    by = max(0, (h - box_h) // 2)
    bx = max(0, (w - box_w) // 2)
    win = _box(scr, by, bx, box_h, box_w, f" {title} ")
    prefilled = bool(initial)
    buf = list(initial)
    cleared = False

    def draw() -> None:
        cur = "".join(buf)
        try:
            win.addstr(1, 2, " " * (box_w - 4), curses.A_NORMAL)
            win.addstr(1, 2, F.truncate(cur, box_w - 4), curses.A_NORMAL)
            win.move(1, 2 + min(len(cur), box_w - 5))
            win.addstr(2, 2, " Enter=confirmar  Esc=cancelar", curses.A_DIM)
        except curses.error:
            pass
        win.touchwin()
        win.refresh()

    while True:
        scr.refresh()
        draw()
        key = scr.getch()
        if key == curses.KEY_ENTER or key == 10 or key == 13:
            win.erase()
            return "".join(buf)
        if key == 27:  # esc
            win.erase()
            return None
        if key == curses.KEY_BACKSPACE or key == 127:
            if buf:
                buf.pop()
        elif key == curses.KEY_LEFT:
            pass
        elif 32 <= key <= 126:
            # El primer carácter de una edición prellenada reemplaza el valor
            # (para no escribir encima; como una barra de URL).
            if prefilled and not cleared:
                buf = []
                cleared = True
            buf.append(chr(key))


def _confirm(scr: Any, title: str, message: str) -> bool:
    h, w = scr.getmaxyx()
    box_w = min(w - 6, 60)
    box_h = 6
    by = max(0, (h - box_h) // 2)
    bx = max(0, (w - box_w) // 2)
    win = _box(scr, by, bx, box_h, box_w, f" {title} ")
    sel = 0
    options = ["  Sí  ", "  No  "]

    def draw() -> None:
        try:
            win.addstr(1, 2, " " * (box_w - 4))
            win.addstr(1, 2, F.truncate(message, box_w - 4))
        except curses.error:
            pass
        x = 4
        for i, opt in enumerate(options):
            attr = curses.A_REVERSE if i == sel else curses.A_NORMAL
            try:
                win.addstr(4, x, opt, attr)
            except curses.error:
                pass
            x += len(opt) + 6
        win.touchwin()
        win.refresh()

    while True:
        scr.refresh()
        draw()
        key = scr.getch()
        if key in (curses.KEY_LEFT,):
            sel = 0
        elif key in (curses.KEY_RIGHT,):
            sel = 1
        elif key in (curses.KEY_ENTER, 10, 13):
            win.erase()
            return sel == 0
        elif key in (ord("q"), 27):
            win.erase()
            return False


def manage_locations(scr: Any, st: State, api: Any) -> Any:
    """Modal para administrar ubicaciones: listar, añadir, usar, borrar, buscar."""
    h, w = scr.getmaxyx()
    box_w = min(w - 6, 64)
    box_h = min(h - 4, max(14, len(st.locations) + 8))
    by = max(0, (h - box_h) // 2)
    bx = max(0, (w - box_w) // 2)
    win = _box(scr, by, bx, box_h, box_w, " Ubicaciones ")
    cursor = 0
    mode = "list"  # list | add | search
    buf = ""
    results: list[dict[str, Any]] = []
    hints = []

    def refresh_list() -> None:
        nonlocal cursor
        cursor = 0

    def draw() -> None:
        for yy in range(1, box_h - 1):
            try:
                win.addstr(yy, 2, " " * (box_w - 4), curses.A_NORMAL)
            except curses.error:
                pass
        if mode == "list":
            lis = st.locations
            if not lis:
                try:
                    win.addstr(2, 2, "Sin ubicaciones. (+) para añadir.", curses.A_DIM)
                except curses.error:
                    pass
            else:
                for i, loc in enumerate(lis[: box_h - 7]):
                    sel = i == cursor
                    active = st.active_location_id == loc.get("id")
                    mark = "*" if loc.get("is_default") else " "
                    flag = "▸" if active else " "
                    name = loc["name"]
                    line = f" {flag} {mark} {name}  ({loc.get('lat')}, {loc.get('lon')}) {loc.get('radius_km')}km"
                    attr = curses.A_REVERSE if sel else curses.A_NORMAL
                    try:
                        win.addstr(i + 2, 2, F.truncate(line, box_w - 4), attr)
                    except curses.error:
                        pass
            hints = ["↑↓ navegar", "Enter usar", "a añadir", "s buscar", "P principal", "d borrar", "q cerrar"]
        elif mode == "add":
            try:
                win.addstr(2, 2, "Nombre: " + F.truncate(buf, box_w - 14) + "_")
            except curses.error:
                pass
        elif mode == "search":
            try:
                win.addstr(2, 2, "Buscar:  " + F.truncate(buf, box_w - 14) + "_")
            except curses.error:
                pass
            for i, r in enumerate(results[: box_h - 7]):
                line = f" {i+1}. {r.get('label')}"
                try:
                    win.addstr(i + 3, 2, F.truncate(line, box_w - 4))
                except curses.error:
                    pass
        hx = 0
        for it in hints:
            try:
                win.addstr(box_h - 2, hx, it, curses.A_DIM)
            except curses.error:
                pass
            hx += len(it) + 2
        win.touchwin()
        win.refresh()

    while True:
        scr.refresh()
        draw()
        key = scr.getch()
        if mode == "list":
            if key in (curses.KEY_UP, ord("k")) and cursor > 0:
                cursor -= 1
            elif key in (curses.KEY_DOWN, ord("j")) and cursor < len(st.locations) - 1:
                cursor += 1
            elif key in (curses.KEY_ENTER, 10, 13) and st.locations:
                loc = st.locations[cursor]
                st.active_location_id = loc.get("id")
                st.cfg["active_location_id"] = loc.get("id")
                return loc.get("id")
            elif key in (ord("a"), ord("+")):
                mode = "add"
                buf = ""
                hints = ["escribir nombre, Enter confirmar, Esc cancelar"]
            elif key in (ord("s"), ord("/")):
                mode = "search"
                buf = ""
                results = []
                hints = ["escribir búsqueda, Enter listar, Esc cancelar"]
            elif key in (ord("p"), ord("P")) and st.locations:
                loc = st.locations[cursor]
                try:
                    api.set_default_location(loc["id"])
                    st.locations = api.locations()
                except Exception as e:
                    st.set_toast(str(e))
                refresh_list()
            elif key in (ord("d"), ord("D")) and st.locations:
                loc = st.locations[cursor]
                if len(st.locations) > 1 and not loc.get("is_default"):
                    if _confirm(scr, "Eliminar", f"¿Eliminar {loc['name']}?"):
                        try:
                            api.delete_location(loc["id"])
                            st.locations = api.locations()
                        except Exception as e:
                            st.set_toast(str(e))
                        refresh_list()
            elif key in (ord("q"), 27, curses.KEY_LEFT):
                return None
        elif mode == "add":
            if key in (curses.KEY_ENTER, 10, 13):
                name = buf.strip()
                if name:
                    # añade con la ubicación activa o zona actual como lat/lon (luego se busca)
                    st.set_toast("Buscando coordenadas... usa 's' para geocodificar")
                    mode = "list"
                    # mantener simple: los guardamos tras búsqueda
                    st._pending_name = name
                buf = ""
                mode = "list"
                hints = []
            elif key == 27:
                mode = "list"
                buf = ""
            elif key in (curses.KEY_BACKSPACE, 127):
                buf = buf[:-1]
            elif 32 <= key <= 126:
                buf += chr(key)
        elif mode == "search":
            if key in (curses.KEY_ENTER, 10, 13):
                if buf.strip():
                    try:
                        results = api.geocode(buf.strip(), 6)
                    except Exception as e:
                        st.set_toast(str(e))
                        results = []
                else:
                    results = []
            elif key == 27:
                mode = "list"
                buf = ""
            elif key in (ord("1"), ord("2"), ord("3"), ord("4"), ord("5"), ord("6")) and results:
                idx = key - ord("1")
                if idx < len(results):
                    r = results[idx]
                    name = getattr(st, "_pending_name", None) or (r.get("label") or r.get("name"))
                    try:
                        api.create_location(name, r["lat"], r["lon"], st.radius)
                        st.locations = api.locations()
                        st.set_toast(f"Ubicación añadida: {name}")
                    except Exception as e:
                        st.set_toast(str(e))
                    mode = "list"
                    buf = ""
                    results = []
            elif key in (curses.KEY_BACKSPACE, 127):
                buf = buf[:-1]
            elif 32 <= key <= 126:
                buf += chr(key)


def source_config(scr: Any, st: State, api: Any, name: str) -> Any:
    """Modal de config de una fuente: intervalo fijo, sincronizar ahora, recargar."""
    h, w = scr.getmaxyx()
    cfg = st.config.get("sources", {}).get(name, {})
    box_w = min(w - 6, 56)
    box_h = 12
    by = max(0, (h - box_h) // 2)
    bx = max(0, (w - box_w) // 2)
    win = _box(scr, by, bx, box_h, box_w, f" Configurar {F.SOURCE_LABELS.get(name, name)} ")

    INTERVALS = {
        "usgs": [1, 2, 3, 4, 5, 10, 15, 30, 60],
        "eonet": [1, 2, 3, 4, 5, 10, 15, 30, 60],
        "gdacs": [5, 10, 15, 30, 60],
        "open_meteo": [10, 15, 30, 60],
    }
    intervals = INTERVALS.get(name, [10, 15, 30, 60])
    sel = 0  # menu row
    iv_sel = 0
    cur_iv = cfg.get("interval_minutes")
    if cur_iv in intervals:
        iv_sel = intervals.index(cur_iv)

    def draw() -> None:
        try:
            last = F.fmt_clock(cfg.get("last_fetch_at"))
            nxt = F.fmt_clock(cfg.get("next_run"))
            win.addstr(1, 2, f"Última: {last}   Próxima: {nxt}")
            win.addstr(2, 2, f"Intervalo (min):", curses.A_BOLD)
            x = 18
            for i, iv in enumerate(intervals[:8]):
                attr = curses.A_REVERSE if sel == 0 and i == iv_sel else curses.A_NORMAL
                try:
                    win.addstr(2, x, f"{iv:>3}", attr)
                except curses.error:
                    pass
                x += 4
            rows = [
                ("Sincronizar ahora", "POST /sync"),
                ("Recargar", "POST /refresh"),
                ("Cerrar", ""),
            ]
            for i, (label, sub) in enumerate(rows):
                attr = curses.A_REVERSE if sel == i + 1 else curses.A_NORMAL
                try:
                    win.addstr(4 + i, 2, f" {label:<18}", attr)
                except curses.error:
                    pass
        except curses.error:
            pass
        win.touchwin()
        win.refresh()

    while True:
        scr.refresh()
        draw()
        key = scr.getch()
        if sel == 0:
            if key in (curses.KEY_LEFT, ord("h")):
                iv_sel = max(0, iv_sel - 1)
            elif key in (curses.KEY_RIGHT, ord("l")):
                iv_sel = min(len(intervals) - 1, iv_sel + 1)
            elif key in (curses.KEY_DOWN, ord("j")):
                sel = 1
            elif key in (curses.KEY_ENTER, 10, 13):
                mins = intervals[iv_sel]
                try:
                    api.source_interval(name, mins)
                    st.set_toast(f"Intervalo {name} → {mins} min")
                except Exception as e:
                    st.set_toast(str(e))
                return SYNCED
        else:
            if key in (curses.KEY_UP, ord("k")):
                sel -= 1
            elif key in (curses.KEY_ENTER, 10, 13):
                if sel == 1:
                    try:
                        api.source_sync(name)
                        st.set_toast(f"{F.SOURCE_LABELS.get(name, name)} sincronizada")
                    except Exception as e:
                        st.set_toast(str(e))
                    return SYNCED
                elif sel == 2:
                    try:
                        api.source_refresh(name)
                        st.set_toast(f"{F.SOURCE_LABELS.get(name, name)} recargada")
                    except Exception as e:
                        st.set_toast(str(e))
                    return SYNCED
                else:  # cerrar
                    return None
        if key in (ord("q"), 27) or (curses.KEY_LEFT == key and sel != 0):
            return None


def global_config(scr: Any, st: State) -> str | None:
    """Modal dev-friendly de configuración global: URL base, radio y vista de clima."""
    h, w = scr.getmaxyx()
    box_w = min(w - 6, 56)
    box_h = 10
    by = max(0, (h - box_h) // 2)
    bx = max(0, (w - box_w) // 2)
    win = _box(scr, by, bx, box_h, box_w, " Configuración ")
    cursor = 0
    fields = ["base_url", "radius", "weather_view"]
    changed = False
    rows = [
        ("URL base", st.base_url),
        ("Radio (km)", str(st.radius)),
        ("Vista clima", st.weather_view),
        ("Guardar y salir", ""),
    ]

    def draw() -> None:
        for i, (label, val) in enumerate(rows):
            if i == 0:
                val = st.base_url
            elif i == 1:
                val = str(st.radius)
            elif i == 2:
                val = st.weather_view
            attr = curses.A_REVERSE if i == cursor else curses.A_NORMAL
            try:
                line = f" {label:<16} {val}"
                win.addstr(i + 1, 2, F.truncate(line, box_w - 4), attr)
            except curses.error:
                pass
        try:
            win.addstr(box_h - 2, 2, " ↑↓ mover  Enter editar  q/← salir", curses.A_DIM)
        except curses.error:
            pass
        win.touchwin()
        win.refresh()

    base_url = st.cfg["base_url"]
    while True:
        scr.refresh()
        draw()
        key = scr.getch()
        if key in (curses.KEY_UP, ord("k")) and cursor > 0:
            cursor -= 1
        elif key in (curses.KEY_DOWN, ord("j")) and cursor < len(rows) - 1:
            cursor += 1
        elif key in (curses.KEY_ENTER, 10, 13):
            if cursor == 0:
                new_url = _prompt(scr, "URL base (ej: http://192.168.1.42:8000)", base_url)
                if new_url is not None and new_url.strip():
                    st.cfg["base_url"] = new_url.strip().rstrip("/")
                    base_url = st.cfg["base_url"]
                    st.client = None  # se reconstruye en App
                    changed = True
            elif cursor == 1:
                new_r = _prompt(scr, "Radio (km)", str(st.radius))
                if new_r is not None and new_r.strip().isdigit():
                    st.cfg["radius"] = int(new_r.strip())
                    changed = True
            elif cursor == 2:
                st.cfg["weather_view"] = "daily" if st.weather_view == "hourly" else "hourly"
                st.weather_view = st.cfg["weather_view"]
                changed = True
            elif cursor == 3:
                if changed:
                    return "save"
                return None
        elif key in (ord("q"), 27, curses.KEY_LEFT):
            if changed:
                return "save"
            return None
        elif key == ord("s"):
            return "save"
