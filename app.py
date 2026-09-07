"""App curses: loop principal, layout, render y dispatch de teclas."""

from __future__ import annotations

import curses
import threading
import time
from typing import Any

from . import format as F
from . import modals
from . import panels as P
from . import theme as T
from .api import ApiError, Client
from .state import State

# Secciones navegables con <tab>
SECTIONS = ["controls", "alerts", "weather", "footer"]

# Intervalos de auto-refresco (s)
RELOAD_ALERTS = 60
RELOAD_WEATHER = 300
RELOAD_CONFIG = 300

# Intervalos de fuente válidos (para el modal de fuente)
SOURCE_INTERVALS = {
    "usgs": [1, 2, 3, 4, 5, 10, 15, 30, 60],
    "eonet": [1, 2, 3, 4, 5, 10, 15, 30, 60],
    "gdacs": [5, 10, 15, 30, 60],
    "open_meteo": [10, 15, 30, 60],
}


class App:
    def __init__(self, scr: Any, state: State) -> None:
        self.scr = scr
        self.st = state
        self.st.client = Client(state.base_url)
        self.section = "alerts"
        self.cursor = 0  # cursor genérico por sección (lista/item)
        self.detail_open = False
        self.detail_alert: dict[str, Any] | None = None
        self.start = time.monotonic()
        self._last_alerts = 0.0
        self._last_weather = 0.0
        self._last_config = 0.0
        self._relaunch_at: float | None = None
        self.busy = False
        self._install_theme()
        self._init_windows()
        # primer refresh inmediato
        self.refresh_config()
        self.refresh_locations()
        self.refresh_alerts()
        self.refresh_weather()

    # ---------- setup ----------
    def _install_theme(self) -> None:
        """Instala el tema de colores (roles → pares curses) desde la config."""
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
        self._pairs = T.init_pairs(T.resolve_palette(self.st.cfg))

    def _init_windows(self) -> None:
        h, w = self.scr.getmaxyx()
        self.h_h, self.h_w = h, w
        # Layout: header 1, controls 1, separador 1, body (resto - footer 2),
        # footer 2
        self.header = curses.newwin(1, w, 0, 0)
        self.controls = curses.newwin(1, w, 1, 0)
        self.separator = curses.newwin(1, w, 2, 0)
        body_top = 3
        self.footer_h = 2
        body_h = h - body_top - self.footer_h
        if body_h < 1:
            body_h = 1
        self.body = curses.newwin(body_h, w, body_top, 0)
        self.footer = curses.newwin(self.footer_h, w, body_top + body_h, 0)
        # Ventana del toast: 1 fila sobre la última del body, refrescada SIEMPRE
        # al final para que ningún panel le pise el contenido (fin del parpadeo).
        self.toast_win = curses.newwin(1, w, body_top + body_h - 1, 0)
        # Split del body: 50 / 50
        mid = w // 2
        self.left = self.body.derwin(body_h, mid, 0, 0)
        right_w = w - mid
        self.right = self.body.derwin(body_h, right_w, 0, mid)

    # ---------- refrescos de datos ----------
    def _client(self) -> Client:
        return self.st.client  # type: ignore[return-value]

    def _rebuild_client(self) -> None:
        self.st.client = Client(self.st.base_url)
        self._last_alerts = 0.0
        self._last_weather = 0.0
        self._last_config = 0.0
        self.refresh_config()
        self.refresh_locations()
        self.refresh_alerts()
        self.refresh_weather()

    def refresh_alerts(self) -> None:
        self._last_alerts = time.monotonic()
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

    def refresh_weather(self, *_a: Any) -> None:
        self._last_weather = time.monotonic()
        st = self.st
        try:
            loc = st.active_location()
            if loc:
                w = self._client().weather(loc["lat"], loc["lon"])
            else:
                w = self._client().weather()
            st.weather = w
            st.error_weather = None
        except ApiError as e:
            st.error_weather = str(e)

    def refresh_config(self, *_a: Any) -> None:
        self._last_config = time.monotonic()
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
            if self.section == "alerts" and self.detail_open:
                self.section = "footer"
            return False
        if key in (ord("u"), ord("U")):
            self._open_config()
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
        if self.section == "weather":
            return self._key_weather(key)
        if self.section == "footer":
            return self._key_footer(key)
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

    # ---------- clima ----------
    # El cursor de clima opera sobre filas interactivas:
    #   0 = toggle de ubicación, 1 = toggle horario/semanal, 2 = grilla.
    # La celda seleccionada dentro de la grilla vive en st.weather_cell y se
    # mueve con h/l (la ventana visible la sigue sola).
    WEATHER_ROWS = 3

    def _weather_cell_count(self) -> int:
        st = self.st
        w = st.weather or {}
        if st.weather_view == "hourly":
            return len((w.get("hourly") or {}).get("time") or [])
        return len((w.get("daily") or {}).get("time") or [])

    def _key_weather(self, key: int) -> bool:
        st = self.st
        if key in (curses.KEY_LEFT, ord("h")):
            n = self._weather_cell_count()
            if self.cursor == 2 and n:
                st.weather_cell = max(0, st.weather_cell - 1)
        elif key in (curses.KEY_RIGHT, ord("l")):
            n = self._weather_cell_count()
            if self.cursor == 2 and n:
                st.weather_cell = min(n - 1, st.weather_cell + 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            self.cursor = min(self.WEATHER_ROWS - 1, self.cursor + 1)
        elif key in (curses.KEY_UP, ord("k")):
            self.cursor = max(0, self.cursor - 1)
        elif key in (curses.KEY_ENTER, 10, 13, ord(" ")):
            if self.cursor == 0:
                # toggle entre ubicaciones
                if st.locations:
                    locs = st.locations
                    cur = st.active_location()
                    idx = 0
                    for i, l in enumerate(locs):
                        if cur and l.get("id") == cur.get("id"):
                            idx = i
                            break
                    nxt = locs[(idx + 1) % len(locs)]
                    st.active_location_id = nxt.get("id")
                    st.cfg["active_location_id"] = nxt.get("id")
                    self._persist()
                    self.refresh_weather()
            elif self.cursor == 1:
                # toggle horario/semanal
                st.cfg["weather_view"] = "daily" if st.weather_view == "hourly" else "hourly"
                st.weather_view = st.cfg["weather_view"]
                st.weather_cell = 0
                self._persist()
            else:
                # abrir modal de detalle de la celda seleccionada
                self._open_weather_cell(st.weather_cell)
        elif key == ord("+"):
            modals.manage_locations(self.scr, st, self._client())
            self._persist()
            self.refresh_locations()
            self.refresh_weather()
        return False

    def _open_weather_cell(self, cell_idx: int) -> None:
        st = self.st
        w = st.weather or {}
        if not w:
            return
        if st.weather_view == "hourly":
            hourly = w.get("hourly") or {}
            times = hourly.get("time") or []
            if not times:
                return
            i = max(0, min(cell_idx, len(times) - 1))
            cell = {
                "t": times[i] if i < len(times) else None,
                "temp": _arr(hourly, "temperature_2m", i),
                "code": _arr(hourly, "weathercode", i),
                "wind": _arr(hourly, "wind_speed_10m", i),
                "gust": _arr(hourly, "windgusts_10m", i),
                "precip": _arr(hourly, "precipitation", i),
                "pop": _arr(hourly, "precipitation_probability", i),
                "hum": _arr(hourly, "relativehumidity_2m", i),
                "feels": _arr(hourly, "apparent_temperature", i),
                "cloud": _arr(hourly, "cloudcover", i),
                "press": _arr(hourly, "pressure_msl", i),
            }
            lines = [
                ("Hora", F.fmt_clock(cell["t"])),
                ("Temp", f"{cell['temp']}°C" if cell["temp"] is not None else "—"),
                ("Sensación", f"{cell['feels']}°C" if cell["feels"] is not None else "—"),
                ("Viento", f"{cell['wind']} km/h" if cell["wind"] is not None else "—"),
                ("Ráfagas", f"{cell['gust']} km/h" if cell["gust"] is not None else "—"),
                ("Precip", f"{cell['precip']} mm" if cell["precip"] is not None else "—"),
                ("Prob. lluvia", f"{cell['pop']}%" if cell["pop"] is not None else "—"),
                ("Humedad", f"{cell['hum']}%" if cell["hum"] is not None else "—"),
                ("Nubosidad", f"{cell['cloud']}%" if cell["cloud"] is not None else "—"),
                ("Presión", f"{cell['press']} hPa" if cell["press"] is not None else "—"),
            ]
            modals.weather_detail(self.scr, f"Horas {F.fmt_clock(cell['t'])}", lines)
        else:
            daily = w.get("daily") or {}
            times = daily.get("time") or []
            if not times:
                return
            i = max(0, min(cell_idx, len(times) - 1))
            cell = {
                "t": times[i] if i < len(times) else None,
                "code": _arr(daily, "weathercode", i),
                "tmax": _arr(daily, "temperature_2m_max", i),
                "tmin": _arr(daily, "temperature_2m_min", i),
                "precip": _arr(daily, "precipitation_sum", i),
                "sunrise": _arr(daily, "sunrise", i),
                "sunset": _arr(daily, "sunset", i),
                "uv": _arr(daily, "uv_index_max", i),
                "windMax": _arr(daily, "wind_speed_10m_max", i),
            }
            name = "Hoy" if i == 0 else F.fmt_day(cell["t"])
            lines = [
                ("Día", name),
                ("Máx", f"{cell['tmax']}°C" if cell["tmax"] is not None else "—"),
                ("Mín", f"{cell['tmin']}°C" if cell["tmin"] is not None else "—"),
                ("Lluvia", f"{cell['precip']} mm" if cell["precip"] is not None else "—"),
                ("Amanecer", F.fmt_clock(cell["sunrise"] + "Z") if cell["sunrise"] else "—"),
                ("Atardecer", F.fmt_clock(cell["sunset"] + "Z") if cell["sunset"] else "—"),
                ("UV máx", f"{cell['uv']}" if cell["uv"] is not None else "—"),
                ("Viento máx", f"{cell['windMax']} km/h" if cell["windMax"] is not None else "—"),
            ]
            modals.weather_detail(self.scr, f"Día {name}", lines)

    # ---------- footer ----------
    def _key_footer(self, key: int) -> bool:
        st = self.st
        sources = list((st.config.get("sources") or {}).keys())
        # cursor en footer: 0..len(sources)-1, luego botones
        total_rows = len(sources) + 2  # +2 botones (config, sync all)
        nh = list(range(len(sources))) + [len(sources), len(sources) + 1]
        if key in (curses.KEY_LEFT, ord("h")):
            self.cursor = max(0, self.cursor - 1)
        elif key in (curses.KEY_RIGHT, ord("l")):
            self.cursor = min(total_rows - 1, self.cursor + 1)
        elif key in (curses.KEY_UP, ord("k")):
            self.cursor = max(0, self.cursor - 1)
        elif key in (curses.KEY_DOWN, ord("j")):
            self.cursor = min(total_rows - 1, self.cursor + 1)
        elif key in (curses.KEY_ENTER, 10, 13, ord(" ")):
            if self.cursor < len(sources):
                modals.source_config(self.scr, st, self._client(), sources[self.cursor])
                self.refresh_config()
            elif self.cursor == len(sources):
                self._open_config()
            elif self.cursor == len(sources) + 1:
                st.set_toast("Espere por favor ~10 s — sincronizando fuentes…")
                self.render()
                try:
                    self._client().sync_all()
                    st.set_toast("Sincronización completada")
                except ApiError as e:
                    st.set_toast(f"Error en Sync All: {e}")
                self.refresh_config()
        return False

    # ---------- config ----------
    def _preview_theme(self) -> None:
        """Repinta la dashboard con el tema actual de la config (preview)."""
        self._install_theme()
        self.render()

    def _open_config(self) -> None:
        st = self.st
        res = modals.global_config(self.scr, st, preview_theme=self._preview_theme)
        if res == "save":
            st.cfg["radius"] = st.radius
            self._persist()
            self._install_theme()  # puede haber cambiado el tema
            if not self.st.client or self.st.client.base_url != st.base_url:
                self._rebuild_client()
            else:
                self.refresh_alerts()
        elif res == "update":
            self._start_update()
        elif res == "changed":
            pass

    # ---------- self-update ----------
    def _start_update(self) -> None:
        """Arranca la actualización en un thread (git fetch/pull bloquean ~seg)."""
        st = self.st
        st.set_toast("Comprobando actualización…")
        threading.Thread(
            target=self._run_update, name="natalerts-tui-update", daemon=True
        ).start()

    def _run_update(self) -> None:
        from . import update as U

        try:
            res = U.do_update()
            if res.updated:
                # dar ~1.5s de visibilidad al toast y luego relanzar desde el loop
                self._relaunch_at = time.monotonic() + 1.5
                self.st.set_toast(f"Actualizado a {res.available} — reiniciando…")
                self.st.relaunch = True
            else:
                self.st.set_toast(res.message)
        except Exception as e:  # noqa: BLE001
            self.st.set_toast(f"Error: {e}")

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
                "weather_view": st.weather_view,
                "tema": st.tema,
            }
        )

    # ---------- loop ----------
    def run(self) -> None:
        while True:
            self._tick()
            self.render()
            curses.napms(100)
            key = self.scr.getch()
            if key == curses.KEY_RESIZE:
                self._resize()
                continue
            if key != -1:
                if self.handle_key(key):
                    break
            self._maybe_reload()
            if (
                self.st.relaunch
                and self._relaunch_at is not None
                and time.monotonic() >= self._relaunch_at
            ):
                # permite que el toast "Actualizado — reiniciando" se vea antes
                # de romper el loop; main.py relanza con os.execv
                break

    def _resize(self) -> None:
        """Rebuild windows tras un resize de terminal (evita artefactos)."""
        self._init_windows()
        for w in (self.header, self.controls, self.separator, self.body, self.left, self.right, self.footer, self.toast_win):
            w.touchwin()

    def _tick(self) -> None:
        pass

    def _maybe_reload(self) -> None:
        now = time.monotonic()
        if now - self._last_alerts >= RELOAD_ALERTS:
            self.refresh_alerts()
        if now - self._last_weather >= RELOAD_WEATHER:
            self.refresh_weather()
        if now - self._last_config >= RELOAD_CONFIG:
            self.refresh_config()
            self.refresh_locations()

    def render(self) -> None:
        st = self.st
        pairs = self._pairs
        focus = lambda s: self.section == s
        P.draw_header(self.header, st, pairs)
        P.draw_controls(self.controls, st, pairs, self.cursor, focus("controls"))
        P.draw_separator(self.separator, pairs)
        if focus("alerts") and self.detail_open:
            P.draw_alerts_detail(self.left, st, self.detail_alert, pairs)
        else:
            P.draw_alerts_list(self.left, st, self.cursor, focus("alerts"), pairs)
        P.draw_weather(self.right, st, self.cursor, focus("weather"), pairs)
        P.draw_footer(self.footer, st, self.cursor, focus("footer"), pairs)
        # countdown de próxima recarga en el footer
        self._draw_countdown()
        P.draw_toast(st, self.toast_win, pairs)
        self.header.refresh()
        self.controls.refresh()
        self.separator.refresh()
        self.body.refresh()
        self.left.refresh()
        self.right.refresh()
        self.footer.refresh()
        # el toast va por su propia ventana: se refresca al final para que
        # siempre termine pintado (sin alternancia con el body).
        self.toast_win.refresh()

    def _draw_countdown(self) -> None:
        h, w = self.footer.getmaxyx()
        # reloj hora local
        now = time.localtime()
        clock = time.strftime("%H:%M:%S", now)
        # countdown hasta la próxima recarga de alertas
        remaining = max(0, RELOAD_ALERTS - (time.monotonic() - self._last_alerts))
        cd = f"{int(remaining//60):02d}:{int(remaining%60):02d}"
        txt = f" {clock} · próxima recarga {cd}"
        try:
            self.footer.addstr(min(1, h - 1), 0, F.truncate(txt, w - 22), self._pairs["footer"])
        except curses.error:
            pass


def _arr(data: dict[str, Any], key: str, i: int) -> Any:
    arr = data.get(key)
    if isinstance(arr, list) and i < len(arr):
        return arr[i]
    return None
