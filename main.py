"""Entrypoint del TUI de Natural Alerts (curses, solo stdlib).

Uso:
    python3 tui/main.py

Funciona tanto ejecutándolo como script directo (python3 tui/main.py) como
módulo del paquete (python3 -m tui.main).
"""

from __future__ import annotations

import curses
import sys
import os
from typing import Any

# Permite ejecutarlo como script directo: agrega el raíz del proyecto a sys.path
# (padre del directorio tui/) para poder importar el paquete `tui`.
if __package__ in (None, ""):
    _TUI_DIR = os.path.dirname(os.path.abspath(__file__))
    _ROOT = os.path.dirname(_TUI_DIR)
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)

from tui.app import App
from tui.state import State


def main(argv: list[str] | None = None) -> int:
    state = State({})
    try:
        curses.wrapper(_run, state)
    except Exception as exc:  # curses puede lanzar diversas excepciones al salir
        print(f"Error TUI: {exc}", file=sys.stderr)
        return 1
    return 0


def _run(scr: Any, state: State) -> None:
    try:
        curses.curs_set(0)
        scr.keypad(True)
        scr.nodelay(True)
        app = App(scr, state)
        app.run()
    except curses.error:
        pass
    finally:
        try:
            scr.nodelay(False)
            curses.curs_set(1)
        except curses.error:
            pass


if __name__ == "__main__":
    sys.exit(main())