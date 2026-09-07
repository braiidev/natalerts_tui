# TODO — Natural Alerts TUI

Subproyecto consumidor (curses) de la API de Natural Alerts. Repo git propio en `tui/`.

## Proyecto
- Python 3.9+ solo stdlib (curses, urllib, json). TUI dashboard en una sola vista.
- Persistencia propia: `tui/config.json` (settings locales) — no toca la DB del server.
- API a consumir: `http://192.168.1.42:8000` (configurable).
- Formato de commit: `v0.N <tipo>: <descripción>` en español.

## Doing
- [ ] v0.8 chore: limpieza final, docs de uso y atajos, verificación manual E2E
      contra el server real.

## Next
- Fixes pendientes detectados en la verificación manual (v0.8):
  - Clima: `<enter>` en celda de la grilla no abre el detalle de celda
    (`_open_weather_cell` inalcanzable: el cursor en clima queda clampeado a 0..2 y
    Enter colisiona con los toggles de ubicación/vista).
  - Artefactos de redibujo tras abrir/cerrar algunos modales (chars residuales en
    filas compartidas) — reproducible al abrir/cerrar `source_config` tras resizes.
  - Toast persistente: no expira y puede tapar el estado del footer.

## Done
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

## Done
- [x] v0.0 docs: subproyecto TUI creado con git init propio en `tui/` (ignorado por
      el repo padre como subproyecto independiente); documentación del milestone
      (README + TODO del TUI) con la especificación completa de la interfaz,
      navegación, persistencia, consumo de API y convenciones.

## Referencia
- Detalle por versión: `git log --oneline --decorate` (repo tui propio).
- URL base de la API configurable en `tui/config.json` (`base_url`) o vía `--url`.
