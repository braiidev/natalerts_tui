# TODO — Natural Alerts TUI

Subproyecto consumidor (curses) de la API de Natural Alerts. Repo git propio en `tui/`.

## Proyecto
- Python 3.9+ solo stdlib (curses, urllib, json). TUI dashboard en una sola vista.
- Persistencia propia: `tui/config.json` (settings locales) — no toca la DB del server.
- API a consumir: `http://192.168.1.42:8000` (configurable).
- Formato de commit: `v0.N <tipo>: <descripción>` en español.

## Doing

## Next

- [ ] v0.1 feat: esqueleto del TUI — layout Header/Controls/Alertas/Clima/Footer,
      dispatch de teclas por contexto (modo normal / modal / prompt), navegación con
      `<tab>` entre secciones y `<hjkl>`/flechas dentro de cada una, resalte de la
      sección activa.
- [ ] v0.2 feat: cliente API (urllib) + carga y guardado de `config.json`
      (URL base configurable vía `--url` y archivo, filtros, alcance, radio,
      ubicación activa, vista de clima).
- [ ] v0.3 feat: Controls — filtros toggle circulares [Todos>][Dias>][Urgencia>]
      [Asc-Desc>][Radio(±5)] y alcance [Zona/Pais>], disparan re-carga de `/api/alerts`.
- [ ] v0.4 feat: Card Alertas — lista con truncado y scroll navegable, contador y
      días; `<enter>` en item abre modal de detalle ampliado; vuelta con q/h/arrow_left.
- [ ] v0.5 feat: Card Clima — ubicación actual (toggle circular entre ubicaciones +
      botón (+)), modal de administrar ubicaciones; toggle [horario/semanal] con
      proyecciones +1/+2/+3 navegables; `<enter>` en celda abre modal de detalle.
- [ ] v0.6 feat: Footer — 4 mini-cards de fuentes [Evento <estado>] con última carga
      hh:mm y countdown; modal para configurar fuente (intervalo fijo, sincronizar
      ahora, recargar); botón [Sync All].
- [ ] v0.7 feat: recarga automática — refresh de alertas (60s), clima (300s) y
      config (300s) con countdown visible de próxima recarga.
- [ ] v0.8 chore: limpieza final, docs de uso y atajos, verificación manual E2E
      contra el server real.

## Done
- [x] v0.0 docs: subproyecto TUI creado con git init propio en `tui/` (ignorado por
      el repo padre como subproyecto independiente); documentación del milestone
      (README + TODO del TUI) con la especificación completa de la interfaz,
      navegación, persistencia, consumo de API y convenciones.

## Referencia
- Detalle por versión: `git log --oneline --decorate` (repo tui propio).
- URL base de la API configurable en `tui/config.json` (`base_url`) o vía `--url`.
