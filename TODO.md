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
- v0.14 chore: limpieza final, docs de uso y atajos, verificación manual E2E
      contra el server real.

## Done
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
