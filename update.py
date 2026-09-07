"""Self-update vía git (patrón Clock).

El TUI se instala clonando `braiidev/natalerts_tui` (rama `main`) y se
actualiza **por commits** (`git rev-list --count HEAD..origin/main`), no por
comparación semántica de versiones: inmune al desfase entre las tags v0.N
(utilizadas para versionar) y cualquier contador interno.

El repo raíz ES el directorio donde vive este módulo (código == clone), así
que `repo_root()` no necesita caminar hacia arriba: `update.py` se copia a la
raíz del repo por install.sh.
"""

from __future__ import annotations

import os
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path

GIT_TIMEOUT = 8
PULL_TIMEOUT = 30

# Directorio donde install.sh deja el código (validado por --uninstall).
INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".local", "natalerts", "tui")

_lock = threading.Lock()


def repo_root() -> str:
    """Raíz del repo git que contiene esta instalación (== directorio del módulo)."""
    return str(Path(__file__).resolve().parent)


def _git(
    repo: str, args: list[str], timeout: int = GIT_TIMEOUT
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, timeout=timeout
    )


def _describe(repo: str, rev: str) -> str:
    """Última tag alcanzable desde `rev`; sin tags, el sha corto."""
    try:
        r = _git(repo, ["describe", "--tags", rev, "--abbrev=0"])
        if r.returncode == 0:
            return r.stdout.strip()
        s = _git(repo, ["rev-parse", "--short", rev])
        if s.returncode == 0:
            return s.stdout.strip()
    except Exception:
        pass
    return rev[:7]


def current_version() -> str:
    """Versión visible de la instalación local (para --version y el modal)."""
    try:
        return _describe(repo_root(), "HEAD")
    except Exception:
        return "?"


@dataclass
class UpdateInfo:
    ok: bool
    error: str | None = None
    behind: int = 0
    current: str = ""
    available: str = ""


def check_update(repo: str | None = None) -> UpdateInfo:
    """Cuántos commits está detrás la instalación respecto de origin/main."""
    with _lock:
        return _check_update_unlocked(repo or repo_root())


def _check_update_unlocked(repo: str) -> UpdateInfo:
    if not os.path.isdir(os.path.join(repo, ".git")):
        return UpdateInfo(False, "no es un repositorio git")
    try:
        f = _git(repo, ["fetch", "origin"], timeout=GIT_TIMEOUT)
        if f.returncode != 0:
            return UpdateInfo(False, (f.stderr.strip() or "fetch falló"))
        r = _git(repo, ["rev-list", "--count", "HEAD..origin/main"])
        if r.returncode != 0:
            return UpdateInfo(False, (r.stderr.strip() or "rev-list falló"))
        behind = int((r.stdout or "0").strip() or 0)
        return UpdateInfo(
            ok=True,
            behind=behind,
            current=_describe(repo, "HEAD"),
            available=_describe(repo, "origin/main"),
        )
    except FileNotFoundError:
        return UpdateInfo(False, "git no está instalado")
    except Exception as e:  # noqa: BLE001
        return UpdateInfo(False, str(e))


@dataclass
class UpdateResult:
    ok: bool
    message: str
    updated: bool = False
    available: str = ""


def do_update(repo: str | None = None) -> UpdateResult:
    """Aplica la actualización si hay commits detrás. Si falla el pull, resetea."""
    with _lock:
        repo = repo or repo_root()
        info = _check_update_unlocked(repo)
        if not info.ok:
            return UpdateResult(False, f"No se pudo verificar: {info.error}")
        if info.behind == 0:
            return UpdateResult(True, f"Estás al día ({info.current})")
        pull = _git(repo, ["pull", "--ff-only"], timeout=PULL_TIMEOUT)
        if pull.returncode == 0:
            return UpdateResult(
                True,
                f"Actualizado a {info.available} — reiniciá",
                updated=True,
                available=info.available,
            )
        reset = _git(repo, ["reset", "--hard", "origin/main"], timeout=15)
        if reset.returncode == 0:
            return UpdateResult(
                True,
                f"Actualizado a {info.available} (historial corregido) — reiniciá",
                updated=True,
                available=info.available,
            )
        return UpdateResult(False, f"Falló el pull: {pull.stderr.strip()}")


__all__ = [
    "INSTALL_DIR",
    "UpdateInfo",
    "UpdateResult",
    "check_update",
    "current_version",
    "do_update",
    "repo_root",
]