"""Dibujo de paneles del TUI.

Funciones puras que reciben curses windows/state y pintan con color. No
manejan entrada ni estado mutante: eso vive en App.
"""

from __future__ import annotations

import curses
from typing import Any

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
        limit = max(0, win.getmaxyx()[1] - x)
        win.addstr(y, x, text[:limit], attr)
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
    _put(win, 0, 0, " Natural Alerts", curses.color_pair(C_HEADER) | curses.A_BOLD)
    _put(win, 0, w - 12, " v0.1 esqueleto", curses.color_pair(C_HEADER))