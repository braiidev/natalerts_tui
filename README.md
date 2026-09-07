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
python3 tui/main.py                 # URL por defecto de config.json
python3 tui/main.py --url http://192.168.1.42:8000   # override de URL base
```

Corre en cualquier TUI (terminal interactiva). `<Esc>` o `q` en estado raíz sale.

## Interfaz (una vista, layout similar a la web)

```
[Header (h=1)  Titulo · Ubicación activa · Hora de ubicación]
[Controls (h=1) Filtros toggle circular]
  [Todos>] [Dias>] [Urgencia>] [Asc-Desc>] [Radio(±5)] Zona[Pais>]
[Contenido (todo el H disponible)]
  [Card Alertas 50%w]           [Card Clima 50%w]
    lista truncada + scroll        ubicación actual (toggle) (+)
    enter → modal detalle          toggle [horario/semanal] + grid
                                   celda → modal con detalle
  (Card Mapa omitida)
[Footer (h=2)  x4[Evento <estado>] · hh:mm · countdown · [Sync All]]
```

### Navegación

- `<Tab>`: cicla secciones activas (Controls → Alertas → Clima → Footer → vuelta).
  La sección activa se resalta.
- Dentro de una sección: `<hjkl>` / flechas desplazan el cursor según el contexto
  (índice de filtro, item de lista, celda de grid, botón del footer).
- `<space>` / `<enter>`: acción (togglar filtro / abrir modal / sincronizar).
- En modales: `<q>` / `<h>` / `arrow_left` vuelven atrás.
- Modo prompt (escribir texto): solo `<esc>` (cancela) y `<enter>` (confirma)
  accionan; el resto de teclas imprimibles escriben.

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
  "weather_view": "hourly"
}
```

- `base_url` se puede cambiar por CLI (`--url`) o editando el archivo, por si
  cambia el mini-server o el puerto de la API.

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
