# TODO — Natural Alerts TUI

Subproyecto consumidor (curses) de la API de Natural Alerts. Repo git propio en `tui/`.

## Proyecto
- Python 3.9+ solo stdlib (curses, urllib, json). TUI dashboard en una sola vista.
- Persistencia propia: `tui/config.json` (settings locales) — no toca la DB del server.
- API a consumir: `http://192.168.1.42:8000` (configurable).
- Formato de commit: `v0.N <tipo>: <descripción>` en español.

## Doing
- (vacío)

## Next

### Alta prioridad
- [ ] ~~tests format.py~~ (omitido: E2E manual OK)
- [ ] ~~tests config.py~~ (omitido: E2E manual OK)
- [ ] ~~tests theme.py~~ (omitido: E2E manual OK)
- [ ] ~~tests update.py~~ (omitido: E2E manual OK)
- [ ] ~~tests state.py~~ (omitido: E2E manual OK)
- [ ] ~~tests app.py~~ (omitido: E2E manual OK)
- [ ] ~~flujo "agregar ubicación" reescrito~~ (hecho en v0.18)
- [ ] ~~filtro por tipo de evento~~ (hecho en v0.19)

### Media prioridad
- [ ] indicador de conexión — renderizar State.connected en el header o footer
      como banner sutil (ej. "[sin server]" o icono) cuando connected=False.
- [ ] awareness de collector pausado — consumir un endpoint de estado del
      collector y mostrar aviso en el footer si está en pausa.
- [ ] README: corregir dependencias (quitar sqlite3), documentar
      NATALERTS_TUI_URL, documentar flujo de agregar ubicación.

### Baja prioridad
- [ ] box_h=12 dinámico en global_config — calcular alto del modal según
      número de filas para que no corte en terminales chicas.
- [ ] eliminar _tick() (no-op) si no se usa como hook futuro.
- [ ] ~~tests de integración E2E~~ (omitido: E2E manual OK)

## Done
- [x] v0.20 refactor: limpieza de código muerto — se eliminan TYPE_COLOR y
      wmo_desc() (format.py), Client.health() y Client.alert() (api.py),
      el global last_request_at y su import time (api.py, se seteaba sin
      lectores), SOURCE_INTERVALS (app.py, duplicado con modals.py), _arr()
      local (app.py usa P._arr de panels.py único), toast_color (state.py),
      SCOPE/PROVIDER/SORT/DAYS_OPTIONS (config.py) y el import locale inline
      (format.py). Verificado: compila y render E2E en tmux OK.
- [x] v0.19 feat: filtro por tipo de evento — nuevo séptimo toggle circular en
      `#controls` ([Todo▾] → [Sismos▾] → [Marejada▾] → [Tornados▾] → …) que
      consulta `?type=<tipo>` en `/api/alerts`, alineado con la web. Tipos
      principales (all, earthquake, tsunami, tornado, cyclone, storm, flood,
      fire, volcano, drought, other) con etiquetas en `EVENT_TYPE_LABELS`.
      Persistido en `config.json` (`event_type`, default "all"). Actualiza
      `format.py` (EVENT_TYPE_TYPES/LABELS), `config.py` (DEFAULTS),
      `state.py` (propiedad event_type), `api.py` (param types),
      `app.py` (refresh_alerts + _activate_filter idx 6 + _persist + _key_controls %7),
      `panels.py` (draw_controls segmento). Verificado en tmux: ciclo el toggle,
      filtra a 3 (fire) vs 6 (todos) con tipos únicos correctos, persiste.
- [x] v0.18 feat: flujo "agregar ubicación" reescrito — al presionar `a`/`+`
      y escribir un nombre, al confirmar con Enter se geocodifica automáticamente
      esa misma palabra y se pasa a la lista de resultados (antes dejaba el
      usuario colgado teniendo que saber presionar `s` para buscar). El nombre
      queda guardado en `st._pending_name` y al elegir un resultado (1-6) se
      crea la ubicación con sus coordenadas. Fix de bug: `hints` no asignado en
      `draw()` cuando se entraba a modo add (NameError que crasheaba el modal).
      `_pending_name` ahora se declara en `State.__init__` (antes era un
      atributo dinámico frágil). Verificado en tmux contra el server real:
      Cordoba → geocodifica → elegir → aparece en la lista. Prueba limpiada.
- [x] v0.17 feat: UX/UX — toast de "Espere por favor ~10 s" **antes** del
      `sync_all()` bloqueante (render explícito para que se pinte en pantalla);
      toast de resultado al terminar; botones `[Config]`/`[Sync All]` en la
      tira de footer destacados con `▶` + `selected|BOLD` cuando el cursor los
      alcanza (antes solo resaltaban las fuentes); ventana propia del toast
      (`toast_win`), refrescada al final de cada frame → cero parpadeo con los
      paneles; navegación de clima reescrita: cursor de filas (0=ubicación,
      1=vista, 2=grilla) + `h`/`l` mueve la celda absoluta (la ventana la
      sigue sola, centrando la celda); se eliminó `[m] gestionar` (redundante
      con `+`); copy: dirección del viento ahora en punto cardinal (`N`/`NE`…)
      en vez de grados crípticos; celdas de viento muestran `km/h` (antes
      `3k`); timezone con `_` reemplazado por espacio; magnitud vacía muestra
      `—` en la lista (antes quedaba la columna vacía).
- [x] v0.16 chore: limpieza (código muerto: `severity_class` en format.py,
      `fields` en modals.py, `d` sin uso en panels.draw_alerts_detail) + docs
      de atajos de teclado en README (tabla por sección) + E2E manual contra
      el server real en tmux: filtros (provider→NASA EONET recarga alertas),
      detalle inline, grilla de clima + modal de celda, footer y Sync All,
      tema con preview + persistencia, resize sin artefactos. Sin errores en
      el log.
- [x] v0.15 feat (FASE 2): severidad degradada — umbrales <33/…/>=66 con los
      roles sev_low/sev_med/sev_high en el fragmento `47/100` de la lista y en
      la barra `#` del detalle; grilla de clima coloreada (hora/nombre bold,
      `Hoy` en accent, icono WMO en accent, temp bold, viento/precip/min en
      text_dim); docs en README (secciones "Temas" y "Severidad y clima").
- [x] v0.14 feat (FASE 1): normalización visual — roles semánticos en
      `theme.py` (PAIR_*, COLORS_PACK en español, presets clasico/mono/calido/
      alto_contraste/flatline/custom, resolve_palette + init_pairs); temas
      conmutables y persistidos (`tema` en DEFAULTS/config.json) con selector
      en `[Config]` y **preview en vivo** tras el modal; reglas divisorias `─`
      bajo controles y títulos de sección; foco de sección más claro (accent +
      `▌` en títulos); feedback de cursor en `#controls` (filtro activo en cyan)
      y `#footer` (fuente bajo el cursor en `▶` + selected); limpieza de
      interior del modal (sin texto fantasma).
- [x] v0.13 fix: launcher con shebang /bin/sh — el comando solo funcionaba con
      bash presente (Alpine sin bash rompía el launcher); el cuerpo es POSIX.
- [x] v0.12 fix: install.sh no aborta si sudo pide password — instala el
      launcher en ~/.local/bin con aviso de PATH (antes set -e cortaba el
      script y dejaba el código instalado sin comando).
- [x] v0.11 feat: instalador + self-update — `install.sh` (curl|sh, repo
      `braiidev/natalerts_tui` en main) que instala en `~/.local/natalerts/tui`
      con launcher `/usr/local/bin/natalerts-tui`; CLI `--update`,
      `--check-update`, `--uninstall`, `--version`; dentro del TUI, en
      `[Config]`, acción `Comprobar actualización` que aplica el update en
      background (patrón Clock, decide por commits `HEAD..origin/main`) y
      **relanza la TUI** (`os.execv`) si la actualización fue exitosa.
- [x] v0.8 fix: clima — cursor separado en filas interactivas (ubicación/ver) +
      celdas de grilla; `<enter>` abre el detalle de la celda (antes la tecla
      colisionaba con los toggles de ubicación/vista).
- [x] v0.9 fix: toast con expiración — `State.set_toast()` guarda timestamp
      (TTL 4s) y `draw_toast` lo autolimpia; todos los emisores usan `set_toast`.
- [x] v0.10 fix: artefactos de redibujo — `erase()` al inicio de cada draw de
      panel + recrear ventanas en `KEY_RESIZE`; elimina restos tipo "Climaa"
      tras resizes y cierre de modales.
- [x] v0.1 feat: esqueleto completo del TUI de una sola sesión — layout
      Header/Controls/Alertas/Clima/Footer con `<tab>` entre secciones, dispatch de
      teclas por contexto, resalte de sección activa y layout con resize.
- [x] v0.2 feat: cliente API (urllib, `api.py`) + `config.json` (`config.py`) con
      URL base por `--url`/archivo/modal `[Config]` (tecla `u`/`U`), filtros,
      alcance, radio, ubicación activa y vista de clima persitidos.
- [x] v0.3 feat: Controls — toggles circulares [USGS▾][7 d▾][Urgencia▾][Asc ↑]
      [Radio ±5][Mundo▾] que re-cargan `/api/alerts`.
- [x] v0.4 feat: Card Alertas — lista truncada con scroll, contador/días; `<enter>`
      abre modal de detalle ampliado y `q/h/←` vuelve.
- [x] v0.5 feat: Card Clima — ubicación actual, toggle de ubicaciones (▲/▼ y `+`),
      modal de administrar ubicaciones, vista [horario/semanal], grilla de
      proyección +1/+2/+3 navegable con ◀▶/hl y paleta de colors por código WMO.
- [x] v0.6 feat: Footer — 4 mini-cards de fuentes con última carga hh:mm y estado;
      modal de configuración de fuente (intervalo fijo, sincronizar ahora,
      recargar, cerrar); botón [Config] y [Sync All] persistidos.
- [x] v0.7 feat: recarga automática — alertas 60s, clima 300s, config 300s con
      countdown de próxima recarga en el footer.
- [x] v0.0 docs: subproyecto TUI creado con git init propio en `tui/` (ignorado por
      el repo padre como subproyecto independiente); documentación del milestone
      (README + TODO del TUI) con la especificación completa de la interfaz,
      navegación, persistencia, consumo de API y convenciones.

## Referencia
- Detalle por versión: `git log --oneline --decorate` (repo tui propio).
- URL base de la API configurable en `tui/config.json` (`base_url`) o vía `--url`.
