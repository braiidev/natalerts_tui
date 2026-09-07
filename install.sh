#!/usr/bin/env bash
# install.sh — Instala/actualiza natalerts-tui (TUI curses de Natural Alerts)
# Uso: curl -fsSL https://raw.githubusercontent.com/braiidev/natalerts_tui/main/install.sh | bash
# Instala en ~/.local/natalerts/tui y deja el comando /usr/local/bin/natalerts-tui.
# Config local (config.json, generado por el TUI al primer uso): NO se toca
# (vive dentro del directorio instalado y está excluido del repo).
#
# Variables de entorno opcionales (para testing/servidores):
#   NATALERTS_TUI_REPO   URL del repo (default: github.com/braiidev/natalerts_tui.git)
#   NATALERTS_TUI_DIR    directorio de instalación (default: ~/.local/natalerts/tui)
#   NATALERTS_TUI_BIN    ruta del comando (default: /usr/local/bin/natalerts-tui)

set -euo pipefail

REPO_URL="${NATALERTS_TUI_REPO:-https://github.com/braiidev/natalerts_tui.git}"
TARGET="${NATALERTS_TUI_DIR:-$HOME/.local/natalerts/tui}"
BIN="${NATALERTS_TUI_BIN:-/usr/local/bin/natalerts-tui}"

# ── Prerrequisitos ──
for cmd in git python3; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Error: $cmd no está instalado" >&2
        exit 1
    fi
done

# ── Obtener/actualizar el código ──
echo "▶ natalerts-tui — instalando en $TARGET"
if [ -d "$TARGET/.git" ]; then
    echo "  ↳ ya existe, actualizando..."
    git -C "$TARGET" pull --ff-only
elif [ -d "$TARGET" ]; then
    echo "  ↳ existe pero no es un repo, respaldando como tui.bak..."
    mv "$TARGET" "$TARGET.bak"
    git clone "$REPO_URL" "$TARGET"
else
    mkdir -p "$(dirname "$TARGET")"
    git clone "$REPO_URL" "$TARGET"
fi

# ── Launcher (re-ejecuta con python3 para permitir el auto-relanzado del TUI) ──
TMP_BIN="$(mktemp)"
cat > "$TMP_BIN" <<EOF
#!/usr/bin/env bash
# natalerts-tui — launcher del TUI (instalado por install.sh).
exec python3 "$TARGET/main.py" "\$@"
EOF
chmod +x "$TMP_BIN"

BIN_DIR="$(dirname "$BIN")"
FALLBACK="$HOME/.local/bin/natalerts-tui"
if [ -d "$BIN_DIR" ] && [ -w "$BIN_DIR" ]; then
    install -m 0755 "$TMP_BIN" "$BIN"
elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
    # sudo sin password disponible (no-interactivo): instalar directo
    sudo -n install -m 0755 "$TMP_BIN" "$BIN"
else
    # sin permisos y sin sudo no-interactivo: fallback a ~/.local/bin
    mkdir -p "$(dirname "$FALLBACK")"
    install -m 0755 "$TMP_BIN" "$FALLBACK"
    echo "  ⚠ Sin permisos para $BIN (sudo pide password / no disponible). Comando en: $FALLBACK"
    echo "    Agregá ~/.local/bin a tu PATH:"
    echo '      echo '\''export PATH="$HOME/.local/bin:$PATH"'\'' >> ~/.bashrc'
    BIN="$FALLBACK"
fi
rm -f "$TMP_BIN"

echo ""
echo "✅ natalerts-tui instalado. Ejecutá:  natalerts-tui"
echo "   Código:   $TARGET"
echo "   Comando:  $BIN"
echo "   Comandos: natalerts-tui (TUI) · --update · --check-update · --version · --uninstall"
echo "   En el TUI: [Config] → Comprobar actualización (relanza la TUI si actualiza)"