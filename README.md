# Natural Alerts TUI

Consumidor **TUI (curses)** de la API de Natural Alerts, separado como
subproyecto independiente del server + web.

- **Lenguaje**: Python 3.9+ (solo stdlib: `curses`, `urllib`, `json`, `sqlite3`).
- **Frontend**: curses — TUI en una sola vista dashboard (sin mapa).
- **Persistencia propia**: `config.json` (settings locales). No toca la DB del server.
- **Repo**: git propio e independiente (subproyecto dentro de `tui/`).
- **Stack de referencia**: dashboard web (Bootswatch darkly) de Natural Alerts, cuyo
  layout y lógica de datos se replica adaptada a TUI.

## Requisitos

- Python 3.9+ (curses viene en la stdlib de Linux; en Windows usar WSL).
- Acceso de red al mini-server `192.168.1.42` (API en :8000).

## Instalación / ejecución

```bash
# Instalación (repo braiidev/natalerts_tui → ~/.local/natalerts/tui,
# comando /usr/local/bin/natalerts-tui):
curl -fsSL https://raw.githubusercontent.com/braiidev/natalerts_tui/main/install.sh | bash

natalerts-tui                            # arranca la TUI
natalerts-tui --url http://192.168.1.42:8000   # override de URL base
```

Corre en cualquier TUI (terminal interactiva). `<Esc>` o `q` en estado raíz sale.

### Actualización

```bash
natalerts-tui --check-update    # ¿hay versión nueva?
natalerts-tui --update          # aplica la actualización y sale
```

O desde dentro de la TUI: `[Config]` (`u`/`U`) → `Comprobar actualización`; si
hay versión nueva la aplica y **relanza la TUI automáticamente** con el código
nuevo.

## Interfaz (una vista, layout similar a la web)

```
[Header (h=1)  Titulo · Ubicación activa · Hora de ubicación]
[Controls (h=1) Filtros toggle circular]
  [Todos>] [Dias>] [Urgencia>] [Asc-Desc>] [Radio(±5)] Zona[Pais>] [Tipo>]
[Contenido (todo el H disponible)]
  [Card Alertas 50%w]           [Card Clima 50%w]
    lista truncada + scroll        ubicación actual (toggle) (+)
    enter → modal detalle          toggle [horario/semanal] + grid
                                   celda → modal con detalle
  (Card Mapa omitida)
[Footer (h=2)  x4[Evento <estado>] · [Config] [Sync All]  /  hh:mm · countdown]
```

### Navegación

- `<Tab>`: cicla secciones activas (Controls → Alertas → Clima → Footer → vuelta).
  La sección activa se resalta (título en `accent` + `▌`, filtro/fuente bajo el
  cursor con realce).
- Dentro de una sección: `<hjkl>` / flechas desplazan el cursor según el contexto
  (índice de filtro, item de lista, celda de grid, botón del footer).
- `<space>` / `<enter>`: acción (togglar filtro / abrir modal / sincronizar).
- En modales: `<q>` / `<h>` / `arrow_left` vuelven atrás.
- Modo prompt (escribir texto): solo `<esc>` (cancela) y `<enter>` (confirma)
  accionan; el resto de teclas imprimibles escriben.

### Atajos de teclado

| Sección | Tecla | Acción |
|---------|-------|--------|
| Raíz | `q` / `Esc` | Salir (en modal/detalle: volver atrás) |
| Raíz | `Tab` | Ciclar sección activa (Controls → Alertas → Clima → Footer) |
| Raíz | `u` / `U` | Configuración global (URL, radio, clima, tema, actualizar) |
| Controls | `h`/`l`, `←`/`→` | Mover el cursor de filtro |
| Controls | `Enter` / `Space` | Activar filtro (cicla opciones: proveedor, días, orden, radio, alcance, tipo de evento) |
| Alertas | `j`/`k`, `↓`/`↑` | Desplazarse por la lista |
| Alertas | `Enter` / `Space` | Abrir detalle inline; `q`/`h`/`←`/`Esc` cierra |
| Clima | `j`/`k` | Filas interactivas: ubicación / vista / grilla |
| Clima | `h`/`l`, `←`/`→` | Mover la celda dentro de la grilla (la ventana la sigue sola) |
| Clima | `Enter` / `Space` | Según fila: toggle de ubicación, vista `[horario/semanal]` o modal de la celda |
| Clima | `+` | Añadir ubicación |
| Footer | `h`/`l`/`k`/`j` | Fuentes y botones (`[Config]`, `[Sync All]`, resaltados bajo el cursor) |
| Footer | `Enter` / `Space` | Modal de la fuente / Configuración / Sincronizar todo |
| Ubicaciones | `a`/`+` añadir, `s`/`/` buscar, `p` principal, `d` borrar | Modal de gestión |

### Temas

El TUI usa roles semánticos de color (tema) en vez de colores fijos. Hay 5
presets (`clasico`, `mono`, `calido`, `alto_contraste`, `flatline`) y uno
`custom`:

- Cambiar: `[Config]` (`u`/`U`) → fila `Tema` → `<enter>` cicla con **preview en
  vivo** detrás del modal; `<enter>` en `Guardar y salir` lo persiste.
- Clave `tema` en `config.json` (se hereda al archivo de la máquina instalada).
- `custom`: se configura desde `config.json` con `custom_color_<rol>_fg` /
  `custom_color_<rol>_bg` usando nombres de color del pack (Negro/Rojo/Verde/
  Amarillo/Azul/Magenta/Cian/Blanco, `-1` = fondo por defecto). Sin esas claves
  cae a `clasico`.

Roles usados: `header`, `controls`, `footer`, `accent`, `text`, `text_dim`,
`weather`, `divider`, `toast`, `error`, `border`, `selected`, `sev_high`,
`sev_med`, `sev_low`, `filter_active`.

### Severidad y clima

- La severidad de cada alerta se colorea por umbrales: `<33` (sev_low), `<66`
  (sev_med), `>=66` (sev_high) — tanto en la lista (`47/100`) como en el detalle
  (barra `#`).
- En la grilla de clima: hora/nombre en bold, icono WMO en `accent`, temperatura
  en bold y viento/precipitación en `text_dim`.

## Configuración (`tui/config.json`)

Persistencia propia del TUI (no choca con la web ni con la DB del server):

```json
{
  "base_url": "http://192.168.1.42:8000",
  "provider": "all",
  "days": 7,
  "sort": "severity",
  "order": "desc",
  "scope": "world",
  "radius": 250,
  "active_location_id": null,
  "weather_view": "hourly",
  "tema": "clasico"
}
```

- `base_url` se puede cambiar por CLI (`--url`) o editando el archivo, por si
  cambia el mini-server o el puerto de la API.
- `tema` se cambia desde el modal Configuración (ver arriba) o editando el archivo.

## Consumo de API

Endpoints usados por el TUI (API Flask del server en :8000):

| Endpoint | Uso |
|----------|-----|
| `GET /api/alerts` | Lista de alertas (filtros: source, days, sort, order, scope, lat/lon/radius) |
| `GET /api/alerts/<id>` | Detalle de una alerta |
| `GET /api/weather` | Clima de la zona / `?lat=&lon=` de una ubicación |
| `GET /api/locations` | Ubicaciones guardadas (favoritos/pin) |
| `POST/PUT/DELETE /api/locations[/<id>]` | CRUD de ubicaciones |
| `GET /api/geocode?q=` | Buscar lugar → lat/lon (modal de ubicaciones) |
| `GET /api/config` | Estado del recolector y fuentes (footer) |
| `POST /api/sources/<name>/sync` | Sincronizar una fuente ahora |
| `POST /api/sources/<name>/refresh` | Recarga en vivo una fuente |
| `PUT /api/sources/<name>/interval` | Cambiar intervalo (min) de una fuente |
| `POST /api/sources/sync_all` | Sincronizar todas las fuentes |

## Convenciones

Mismas que el proyecto mayor (AGENTS.md global): `snake_case` en Python, type hints,
pytest si aplica, formato de commit `v0.N <tipo>: <descripción>` en español.

## Estado del milestone

Ver `TODO.md` de este subproyecto.
