"""App curses: loop principal, layout y render del esqueleto."""

from __future__ import annotations

import curses
from typing import Any

from . import panels as P
from .state import State

# Secciones navegables con <tab>
SECTIONS = ["alerts"]


class App:
    def __init__(self, scr: Any, state: State) -> None:
        self.scr = scr
        self.st = state
        self.section = "alerts"
        self.cursor = 0  # cursor genérico por sección (lista/item)
        self.busy = False
        self._init_colors()
        self._init_windows()

    # ---------- setup ----------
    def _init_colors(self) -> None:
        curses.use_default_colors()
        for idx in (P.C_HEADER, P.C_CONTROLS, P.C_ACTIVE, P.C_NORMAL, P.C_TITLE,
                    P.C_CARD, P.C_SELECTED, P.C_FOOTER, P.C_TOAST, P.C_BAR):
            try:
                curses.init_pair(idx, -1, -1)
            except curses.error:
                pass
        # pares con fondo/foreground
        pairs = {
            P.C_HEADER: (7, 4),      # text blanco sobre azul
            P.C_CONTROLS: (0, 8),    # negro sobre gris
            P.C_ACTIVE: (2, -1),     # cyan
            P.C_NORMAL: (7, -1),     # blanco
            P.C_TITLE: (11, -1),     # amarillo brillante
            P.C_CARD: (7, -1),
            P.C_SELECTED: (0, 6),    # negro sobre cyan
            P.C_FOOTER: (7, 8),      # blanco sobre gris
            P.C_TOAST: (0, 3),       # negro sobre amarillo
            P.C_BAR: (3, -1),
        }
        for idx, (fg, bg) in pairs.items():
            try:
                curses.init_pair(idx, fg, bg)
            except curses.error:
                pass

    def _init_windows(self) -> None:
        h, w = self.scr.getmaxyx()
        self.h_h, self.h_w = h, w
        # Layout: header 1, body (resto)
        self.header = curses.newwin(1, w, 0, 0)
        body_top = 1
        body_h = h - body_top
        if body_h < 1:
            body_h = 1
        self.body = curses.newwin(body_h, w, body_top, 0)

    # ---------- dispatch de teclas ----------
    def handle_key(self, key: int) -> bool:
        """Devuelve True si se salió (q/esc en raíz)."""
        if key == 9:  # tab
            idx = SECTIONS.index(self.section)
            self.section = SECTIONS[(idx + 1) % len(SECTIONS)]
            self.cursor = 0
            return False
        if key in (ord("q"), 27):
            return True
        return False

    # ---------- loop ----------
    def run(self) -> None:
        while True:
            self.render()
            curses.napms(100)
            key = self.scr.getch()
            if key != -1:
                if self.handle_key(key):
                    break

    def render(self) -> None:
        P.draw_header(self.header, self.st)
        try:
            self.body.addstr(
                2, 3,
                "Esqueleto TUI — API y paneles llegan en las versiones siguientes.",
                curses.A_NORMAL,
            )
        except curses.error:
            pass
        self.header.refresh()
        self.body.refresh()
        self.scr.refresh()