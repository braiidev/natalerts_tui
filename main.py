"""Entrypoint del TUI de Natural Alerts (curses, solo stdlib).

Uso:
    natalerts-tui                       # arranca la TUI
    natalerts-tui --url http://192.168.1.42:8000
    natalerts-tui --update              # actualiza el paquete (git pull) y sale
    natalerts-tui --check-update        # verifica si hay versión nueva
    natalerts-tui --uninstall           # desinstala la instalación (vía install.sh)
    natalerts-tui --version             # imprime la versión instalada

Funciona tanto ejecutándolo como script directo (python3 tui/main.py) como
módulo del paquete (python3 -m tui.main). El instalador genera un launcher
`/usr/local/bin/natalerts-tui` que re-ejecuta este script con python3.
"""

from __future__ import annotations

import argparse
import curses
import os
import shutil
import sys
from typing import Any

# Permite ejecutarlo como script directo: agrega el padre del directorio tui/ a
# sys.path para poder importar el paquete `tui` (la carpeta instalada se llama
# `tui` y contiene el repo, así que el padre es la raíz de instalación).
if __package__ in (None, ""):
    _TUI_DIR = os.path.dirname(os.path.abspath(__file__))
    _ROOT = os.path.dirname(_TUI_DIR)
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)

from tui import config as C
from tui import update as U
from tui.app import App
from tui.state import State


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="natalerts-tui",
        description="TUI curses que consume la API de Natural Alerts.",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="URL base de la API (default: config.json / http://192.168.1.42:8000)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="actualiza el paquete (git pull) y sale",
    )
    parser.add_argument(
        "--check-update",
        action="store_true",
        help="verifica si hay versión nueva sin modificar nada",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="desinstala la instalación creada por install.sh",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="imprime la versión instalada",
    )
    return parser.parse_args(argv)


def _cli_update() -> int:
    res = U.do_update()
    print(res.message)
    return 0 if res.ok else 1


def _cli_check_update() -> int:
    info = U.check_update()
    if not info.ok:
        print(f"⚠ No se pudo verificar: {info.error}", file=sys.stderr)
        return 1
    if info.behind > 0:
        print(
            f"→ Hay una actualización disponible ({info.available}). "
            "Ejecutá: natalerts-tui --update"
        )
    else:
        print(f"✓ Estás al día ({info.current})")
    return 0


def _cli_version() -> int:
    print(f"natalerts-tui {U.current_version()}")
    return 0


def _confirm(prompt: str) -> bool:
    try:
        r = input(f"{prompt} [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return r in ("y", "yes")


def _cli_uninstall() -> int:
    source = U.repo_root()
    if os.path.realpath(source) != os.path.realpath(U.INSTALL_DIR):
        print(
            "Error: el código no vive en una instalación vía install.sh; no se borra.",
            file=sys.stderr,
        )
        print(f"  (repo detectado: {source})", file=sys.stderr)
        return 1

    bin_candidates = [
        "/usr/local/bin/natalerts-tui",
        os.path.join(os.path.expanduser("~"), ".local", "bin", "natalerts-tui"),
    ]
    print("▶ Desinstalando natalerts-tui...")
    print(f"  ↳ {source}")
    for p in bin_candidates:
        if os.path.exists(p):
            print(f"  ↳ {p}")
    if not _confirm("¿Eliminar la instalación? "):
        print("Cancelado.")
        return 1

    for p in bin_candidates:
        try:
            if os.path.islink(p) or os.path.exists(p):
                os.unlink(p)
        except OSError:
            pass

    config_src = os.path.join(source, "config.json")
    config_dst = os.path.join(
        os.path.expanduser("~"), ".config", "natalerts", "config.json"
    )
    if os.path.isfile(config_src):
        os.makedirs(os.path.dirname(config_dst), exist_ok=True)
        if not os.path.exists(config_dst):
            shutil.copy2(config_src, config_dst)
            print(f"  ↳ config.json respaldado en {config_dst}")
        else:
            print(f"  · config.json ya existía en {config_dst}; no se pisó")

    shutil.rmtree(source, ignore_errors=True)
    print("✓ natalerts-tui desinstalado")
    return 0


def _relaunch() -> None:
    """Re-ejecuta el TUI con el mismo intérprete y los mismos argumentos.

    Se usa tras una actualización exitosa desde dentro de la TUI: el proceso
    nuevo arranca ya con el código recién descargado (os.execv reemplaza el
    proceso actual por python3 <main.py> con los argv originales).
    """
    os.execv(
        sys.executable,
        [sys.executable, os.path.abspath(__file__), *sys.argv[1:]],
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.update:
        return _cli_update()
    if args.check_update:
        return _cli_check_update()
    if args.uninstall:
        return _cli_uninstall()
    if args.version:
        return _cli_version()

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
    if state.relaunch:
        _relaunch()
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
