"""Sistema de temas y pares de curses.

Patrón de Clock: define roles semánticos (header, accent, text, etc.),
presets nombrados y un modo custom. Los pares se inicializan en la app
(requieren curses ya iniciado); este módulo solo define constantes y
estructuras de temas.
"""

from __future__ import annotations

import curses
from typing import Any

# ── Índices de pares (fijos, inicializados por init_pairs) ──
PAIR_HEADER = 1
PAIR_CONTROLS = 2
PAIR_FOOTER = 3
PAIR_ACCENT = 4
PAIR_TEXT = 5
PAIR_TEXT_DIM = 6
PAIR_WEATHER = 7
PAIR_DIVIDER = 8
PAIR_TOAST = 9
PAIR_ERROR = 10
PAIR_BORDER = 11
PAIR_SELECTED = 12
PAIR_SEV_HIGH = 13
PAIR_SEV_MED = 14
PAIR_SEV_LOW = 15
PAIR_FILTER_ACTIVE = 16

# ── Palette de curses (nombre en español → COLOR_*) ──
COLORS_PACK: dict[str, int] = {
    "Negro": curses.COLOR_BLACK,
    "Rojo": curses.COLOR_RED,
    "Verde": curses.COLOR_GREEN,
    "Amarillo": curses.COLOR_YELLOW,
    "Azul": curses.COLOR_BLUE,
    "Magenta": curses.COLOR_MAGENTA,
    "Cian": curses.COLOR_CYAN,
    "Blanco": curses.COLOR_WHITE,
}
COLOR_NAMES = list(COLORS_PACK.keys())


# ── Helpers para tema custom ──
def _resolve_custom(props: dict[str, Any] | None = None) -> dict[str, tuple[int, int]]:
    """Devuelve el tema custom (colores configurados o defaults)."""
    props = props or {}
    if props.get("make") is True:
        return THEMES["clasico"]
    c = props or {}

    def _c(key: str, default_fg: str, default_bg: str = "-1") -> tuple[int, int]:
        fg_name = c.get(f"custom_color_{key}_fg", default_fg)
        bg_name = c.get(f"custom_color_{key}_bg", default_bg)
        fg = COLORS_PACK.get(fg_name, COLORS_PACK[default_fg])
        bg = -1 if bg_name == "-1" else COLORS_PACK.get(bg_name, -1)
        return (fg, bg)

    return {
        "header": _c("header", "Azul", "Negro"),
        "controls": _c("controls", "Blanco", "Negro"),
        "footer": _c("footer", "Blanco", "Negro"),
        "accent": _c("accent", "Cian"),
        "text": _c("text", "Blanco"),
        "text_dim": _c("text_dim", "Blanco"),
        "weather": _c("weather", "Verde"),
        "divider": _c("divider", "Blanco"),
        "toast": _c("toast", "Negro", "Amarillo"),
        "error": _c("error", "Rojo"),
        "border": _c("border", "Blanco"),
        "selected": _c("selected", "Negro", "Cian"),
        "sev_high": _c("sev_high", "Rojo"),
        "sev_med": _c("sev_med", "Amarillo"),
        "sev_low": _c("sev_low", "Blanco"),
        "filter_active": _c("filter_active", "Negro", "Cian"),
    }


# ── Presets ──
# Cada valor es (fg, bg) — bg=-1 = fondo por defecto del terminal.
THEMES: dict[str, dict[str, tuple[int, int]]] = {
    "clasico": {
        "header": (7, 4),       # blanco sobre azul
        "controls": (0, 8),     # negro sobre gris
        "footer": (7, 8),       # blanco sobre gris
        "accent": (6, -1),      # cian
        "text": (7, -1),        # blanco
        "text_dim": (8, -1),    # gris (metadatos)
        "weather": (2, -1),     # verde
        "divider": (8, -1),     # gris
        "toast": (0, 3),        # negro sobre amarillo
        "error": (1, -1),       # rojo
        "border": (8, -1),      # gris
        "selected": (0, 6),     # negro sobre cian
        "sev_high": (1, -1),    # rojo
        "sev_med": (3, -1),     # amarillo
        "sev_low": (2, -1),     # verde
        "filter_active": (0, 6),  # negro sobre cian
    },
    "mono": {
        "header": (7, 8),       # blanco sobre gris
        "controls": (7, 8),     # blanco sobre gris
        "footer": (7, 8),       # blanco sobre gris
        "accent": (7, -1),      # blanco bold
        "text": (7, -1),
        "text_dim": (8, -1),
        "weather": (7, -1),
        "divider": (8, -1),
        "toast": (0, 7),        # negro sobre blanco
        "error": (7, -1),
        "border": (8, -1),
        "selected": (0, 7),     # negro sobre blanco
        "sev_high": (7, -1),
        "sev_med": (7, -1),
        "sev_low": (8, -1),
        "filter_active": (0, 7),
    },
    "calido": {
        "header": (0, 3),       # negro sobre amarillo
        "controls": (0, 8),
        "footer": (0, 8),
        "accent": (1, -1),      # rojo
        "text": (7, -1),
        "text_dim": (3, -1),    # amarillo
        "weather": (1, -1),     # rojo
        "divider": (3, -1),     # amarillo
        "toast": (0, 1),        # negro sobre rojo
        "error": (1, -1),
        "border": (3, -1),
        "selected": (0, 1),     # negro sobre rojo
        "sev_high": (1, -1),
        "sev_med": (3, -1),
        "sev_low": (7, -1),
        "filter_active": (0, 1),
    },
    "alto_contraste": {
        "header": (0, 5),       # negro sobre magenta
        "controls": (0, 8),
        "footer": (0, 8),
        "accent": (2, -1),      # verde
        "text": (7, -1),
        "text_dim": (5, -1),    # magenta
        "weather": (2, -1),     # verde
        "divider": (5, -1),     # magenta
        "toast": (0, 5),        # negro sobre magenta
        "error": (1, -1),
        "border": (5, -1),
        "selected": (0, 2),     # negro sobre verde
        "sev_high": (1, -1),
        "sev_med": (3, -1),
        "sev_low": (2, -1),
        "filter_active": (0, 2),
    },
    "flatline": {
        "header": (6, -1),      # cian (sin bg, solo fg bold)
        "controls": (0, 8),
        "footer": (0, 8),
        "accent": (1, -1),      # rojo
        "text": (7, -1),
        "text_dim": (6, -1),    # cian
        "weather": (1, -1),     # rojo
        "divider": (6, -1),     # cian
        "toast": (0, 1),        # negro sobre rojo
        "error": (1, -1),
        "border": (6, -1),
        "selected": (0, 1),     # negro sobre rojo
        "sev_high": (1, -1),
        "sev_med": (3, -1),
        "sev_low": (6, -1),
        "filter_active": (0, 1),
    },
    "custom": {},  # se resuelve dinámicamente
}
THEME_NAMES = list(THEMES.keys())


# ── API pública ──

def resolve_palette(config: dict[str, Any]) -> dict[str, tuple[int, int]]:
    """Lee config['tema'] y devuelve la paleta de colores resuelta."""
    nombre = config.get("tema", "clasico")
    if nombre == "custom":
        return _resolve_custom(config)
    return THEMES.get(nombre, THEMES["clasico"])


def init_pairs(palette: dict[str, tuple[int, int]]) -> dict[str, int]:
    """Inicializa los pares de curses y devuelve dict de attrs.

    Llamar después de curses.start_color() + curses.use_default_colors().
    Devuelve un dict usable como ``pairs["accent"]`` en las vistas.
    """
    pairs_map = {
        "header": PAIR_HEADER,
        "controls": PAIR_CONTROLS,
        "footer": PAIR_FOOTER,
        "accent": PAIR_ACCENT,
        "text": PAIR_TEXT,
        "text_dim": PAIR_TEXT_DIM,
        "weather": PAIR_WEATHER,
        "divider": PAIR_DIVIDER,
        "toast": PAIR_TOAST,
        "error": PAIR_ERROR,
        "border": PAIR_BORDER,
        "selected": PAIR_SELECTED,
        "sev_high": PAIR_SEV_HIGH,
        "sev_med": PAIR_SEV_MED,
        "sev_low": PAIR_SEV_LOW,
        "filter_active": PAIR_FILTER_ACTIVE,
    }
    attrs: dict[str, int] = {}
    for role, pair_idx in pairs_map.items():
        fg, bg = palette.get(role, (7, -1))
        try:
            curses.init_pair(pair_idx, fg, bg)
        except curses.error:
            pass
        attrs[role] = curses.color_pair(pair_idx)
    # accent y selected con BOLD para que resalten
    attrs["accent"] |= curses.A_BOLD
    attrs["sev_high"] |= curses.A_BOLD
    return attrs
