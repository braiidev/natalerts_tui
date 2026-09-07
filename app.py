"""App curses: loop principal, layout, render y dispatch de teclas."""

from __future__ import annotations

import curses
import time
from typing import Any

from . import format as F
from . import modals
from . import panels as P
from .api import ApiError, Client
from .state import State

# Secciones navegables con <tab>
SECTIONS = ["controls", "alerts"]


class App:
    def __init__(self, scr: Any, state: State) -> None:
        self.scr = scr
        self.st = state
        self.st.client = Client(state.base_url)
        self.section = "alerts"
        self.cursor = 0  # cursor genérico por sección (lista/item)
        self.detail_open = False
        self.detail_alert: dict[str, Any] | None = None
        self.busy = False
        self._init_colors()
        self._init_windows()
        # primer refresh inmediato
        self.refresh_config()
        self.refresh_locations()
        self.refresh_alerts()

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
        # Layout: header 1, controls 1, body (resto)
        self.header = curses.newwin(1, w, 0, 0)
        self.controls = curses.newwin(1, w, 1, 0)
        body_top = 2
        body_h = h - body_top
        if body_h < 1:
            body_h = 1
        self.body = curses.newwin(body_h, w, body_top, 0)
        # Split del body: 50 / 50
        mid = w // 2
        self.left = self.body.derwin(body_h, mid, 0, 0)
        right_w = w - mid
        self.right = self.body.derwin(body_h, right_w, 0, mid)

    # ---------- refrescos de datos ----------
    def _client(self) -> Client:
        return self.st.client  # type: ignore[return-value]

    def refresh_alerts(self) -> None:
        st = self.st
        try:
            loc = st.active_location()
            lat = lon = radius = None
            scope = st.scope
            if scope == "zone":
                if loc:
                    lat, lon = loc["lat"], loc["lon"]
                    radius = loc.get("radius_km") or st.radius
                else:
                    radius = st.radius
            d = self._client().alerts(
                source=st.provider,
                days=st.days,
                sort=st.sort,
                order=st.order,
                scope=scope,
                lat=lat,
                lon=lon,
                radius=radius,
            )
            st.alerts = d.get("alerts", [])
            st.alert_count = d.get("count", len(st.alerts))
            st.error_alerts = None
            if self.detail_open:
                # revalidar la alerta en detalle (puede haber desaparecido)
                if self.detail_alert and not any(
                    a.get("id") == self.detail_alert["id"] for a in st.alerts
                ):
                    self.detail_open = False
                    self.detail_alert = None
        except ApiError as e:
            st.error_alerts = str(e)

    def refresh_config(self, *_a: Any) -> None:
        st = self.st
        try:
            st.config = self._client().config()
            st.error_config = None
            st.connected = True
        except ApiError as e:
            st.error_config = str(e)
            st.connected = False

    def refresh_locations(self, *_a: Any) -> None:
        st = self.st
        try:
            st.locations = self._client().locations()
        except ApiError:
            pass

    # ---------- dispatch de teclas ----------
    def handle_key(self, key: int) -> bool:
        """Devuelve True si se salió (q/esc en raíz)."""
        # Teclas globales
        if key == 9:  # tab
            idx = SECTIONS.index(self.section)
            self.section = SECTIONS[(idx + 1) % len(SECTIONS)]
            self.cursor = 0
            return False
        # En la sección de alertas con detalle abierto, q/h/←/esc cierran el
        # detalle (no salen del TUI).
        if self.section == "alerts" and self.detail_open:
            return self._key_alerts(key)

        # Raíz: q/esc salen, el resto se despacha por sección.
        if key in (ord("q"), 27):
            return True
        if self.section == "controls":
            return self._key_controls(key)
        if self.section == "alerts":
            return self._key_alerts(key)
        return False

    # ---------- controles ----------
    def _key_controls(self, key: int) -> bool:
        st = self.st
        if key in (curses.KEY_LEFT, ord("h")) or key in (curses.KEY_RIGHT, ord("l")):
            # mover el "cursor de filtro" entre índices de filtros
            self.cursor = (self.cursor + (1 if key in (curses.KEY_RIGHT, ord("l")) else -1)) % 6
            return False
        if key in (curses.KEY_ENTER, 10, 13, ord(" ")):
            self._activate_filter(self.cursor)
            return False
        return False

    def _activate_filter(self, idx: int) -> None:
        st = self.st
        if idx == 0:  # proveedor
            opts = ["all", "usgs", "eonet", "gdacs"]
            i = opts.index(st.provider) if st.provider in opts else 0
            st.cfg["provider"] = opts[(i + 1) % len(opts)]
        elif idx == 1:  # días
            opts = [1, 7, 30, 90, 0]
            i = opts.index(st.days) if st.days in opts else 1
            st.cfg["days"] = opts[(i + 1) % len(opts)]
        elif idx == 2:  # sort
            opts = ["severity", "time", "distance"]
            i = opts.index(st.sort) if st.sort in opts else 0
            st.cfg["sort"] = opts[(i + 1) % len(opts)]
        elif idx == 3:  # orden
            st.cfg["order"] = "asc" if st.order == "desc" else "desc"
        elif idx == 4:  # radio ±5
            self.clamp_radius(delta=5)
        elif idx == 5:  # scope
            opts = ["world", "country", "zone"]
            i = opts.index(st.scope) if st.scope in opts else 0
            st.cfg["scope"] = opts[(i + 1) % len(opts)]
        self.refresh_alerts()
        self._persist()

    def clamp_radius(self, delta: int) -> None:
        new = self.st.radius + delta
        new = max(0, min(1000, new))
        self.st.cfg["radius"] = new
        if not self.st.active_location():
            self.refresh_alerts()

    # ---------- alertas ----------
    def _key_alerts(self, key: int) -> bool:
        st = self.st
        if self.detail_open:
            if key in (ord("q"), ord("h"), curses.KEY_LEFT, 27):
                self.detail_open = False
                self.detail_alert = None
            return False
        if key in (curses.KEY_DOWN, ord("j")):
            if self.cursor < len(st.alerts) - 1:
                self.cursor += 1
        elif key in (curses.KEY_UP, ord("k")):
            if self.cursor > 0:
                self.cursor -= 1
        elif key in (curses.KEY_ENTER, 10, 13, ord(" ")):
            if st.alerts:
                self.detail_alert = st.alerts[self.cursor]
                self.detail_open = True
        return False

    def _persist(self) -> None:
        from . import config as C
        st = self.st
        C.save_config(
            {
                "base_url": st.cfg["base_url"],
                "provider": st.provider,
                "days": st.days,
                "sort": st.sort,
                "order": st.order,
                "scope": st.scope,
                "radius": st.radius,
                "active_location_id": st.active_location_id,
            }
        )

    # ---------- loop ----------
    def run(self) -> None:
        while True:
            self._tick()
            self.render()
            curses.napms(100)
            key = self.scr.getch()
            if key != -1:
                if self.handle_key(key):
                    break

    def _tick(self) -> None:
        pass

    def render(self) -> None:
        st = self.st
        focus = lambda s: self.section == s
        P.draw_header(self.header, st)
        P.draw_controls(self.controls, st)
        if focus("alerts") and self.detail_open:
            P.draw_alerts_detail(self.left, st, self.detail_alert)
        else:
            P.draw_alerts_list(self.left, st, self.cursor, focus("alerts"))
        self.header.refresh()
        self.controls.refresh()
        self.body.refresh()
        self.left.refresh()
        self.scr.refresh()