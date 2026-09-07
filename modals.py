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
