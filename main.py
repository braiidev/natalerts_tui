"""Entrypoint del TUI de Natural Alerts (curses, solo stdlib).

Uso:
    python3 tui/main.py
    python3 tui/main.py --url http://192.168.1.42:8000

Funciona tanto ejecutándolo como script directo (python3 tui/main.py) como
módulo del paquete (python3 -m tui.main).
"""

from __future__ import annotations

import argparse
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

from tui import config as C
from tui.app import App
from tui.state import State


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="natural-alerts-tui",
        description="TUI curses que consume la API de Natural Alerts.",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="URL base de la API (default: config.json / http://192.168.1.42:8000)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg = C.load_config()
    if args.url:
        cfg["base_url"] = args.url.rstrip("/")
    state = State(cfg)
    if not state.base_url:
        print("Error: falta base_url en config.json", file=sys.stderr)
        return 1
    try:
        curses.wrapper(_run, state)
    except Exception as exc:  # curses puede lanzar diversas excepciones al salir
        print(f"Error TUI: {exc}", file=sys.stderr)
        return 1
    C.save_config(state.cfg)
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
