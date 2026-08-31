#!/bin/bash
# =============================================================================
# UniDex - macOS Installation Script
# Builds /Applications/UniDex.app and /Applications/UniDex Widget.app
# =============================================================================

set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'

SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
APPS_DIR="/Applications"
MAIN_APP="$APPS_DIR/UniDex.app"
WIDGET_APP="$APPS_DIR/UniDex Widget.app"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
WIDGET_AGENT="$LAUNCH_AGENTS/com.jjjulianleon.unidex.widget.plist"

echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   UniDex - macOS Installer${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"

# ---------------------------------------------------------------- dependencies
echo -e "${YELLOW}[1/5]${NC} Verificando dependencias..."

if ! command -v brew &> /dev/null; then
    echo -e "${RED}❌ Homebrew no encontrado. Instalalo desde https://brew.sh${NC}"
    exit 1
fi

BREW_PREFIX="$(brew --prefix)"
BREW_PYTHON="$BREW_PREFIX/bin/python3"

for pkg in gtk4 libadwaita pygobject3 adwaita-icon-theme librsvg; do
    brew list --versions "$pkg" &> /dev/null || brew install "$pkg"
done

"$BREW_PYTHON" -c "import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1')" || {
    echo -e "${RED}❌ GTK4/Libadwaita no disponibles para $BREW_PYTHON${NC}"
    exit 1
}
echo -e "${GREEN}✓ GTK4 + Libadwaita listos${NC}"

# --------------------------------------------------------------- bundle helper
# make_bundle <ruta.app> <bundle-id> <script-python> <LSUIElement>
make_bundle() {
    local bundle="$1" bundle_id="$2" entry="$3" agent="$4"
    local res="$bundle/Contents/Resources"
    local bin="$bundle/Contents/MacOS"
    local exec_name="$(basename "$bundle" .app | tr -d ' ')"

    rm -rf "$bundle"
    mkdir -p "$res" "$bin"

    cp -R "$SOURCE_DIR/src" "$SOURCE_DIR/assets" "$res/"
    mkdir -p "$res/brightspace" "$res/teams"
    cp -R "$SOURCE_DIR/brightspace/." "$res/brightspace/" 2>/dev/null || true
    cp -R "$SOURCE_DIR/teams/." "$res/teams/" 2>/dev/null || true
    cp "$SOURCE_DIR"/{main_gtk.py,widget_gtk.py,ics_integration.py,icloud_integration.py,teams_integration.py,brightspace_integration.py,requirements_macos.txt} "$res/"

    cat > "$bin/$exec_name" << EOF
#!/bin/bash
RES="\$(cd "\$(dirname "\$0")/../Resources" && pwd)"
export XDG_DATA_DIRS="$BREW_PREFIX/share:\${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
export GSETTINGS_SCHEMA_DIR="$BREW_PREFIX/share/glib-2.0/schemas"
cd "\$RES"
exec "\$RES/.venv/bin/python3" "$entry" "\$@"
EOF
    chmod +x "$bin/$exec_name"

    cat > "$bundle/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>$(basename "$bundle" .app)</string>
    <key>CFBundleDisplayName</key><string>$(basename "$bundle" .app)</string>
    <key>CFBundleIdentifier</key><string>$bundle_id</string>
    <key>CFBundleExecutable</key><string>$exec_name</string>
    <key>CFBundleIconFile</key><string>AppIcon</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleShortVersionString</key><string>1.0.0</string>
    <key>LSMinimumSystemVersion</key><string>12.0</string>
    <key>NSHighResolutionCapable</key><true/>
    <key>LSUIElement</key><$agent/>
</dict>
</plist>
EOF

    # Icono: SVG -> PNG -> icns (rsvg-convert e iconutil son parte del stack ya instalado)
    local iconset="$res/AppIcon.iconset"
    mkdir -p "$iconset"
    for size in 16 32 64 128 256 512; do
        rsvg-convert -w $size -h $size "$SOURCE_DIR/assets/app_icon.svg" -o "$iconset/icon_${size}x${size}.png"
        rsvg-convert -w $((size*2)) -h $((size*2)) "$SOURCE_DIR/assets/app_icon.svg" -o "$iconset/icon_${size}x${size}@2x.png"
    done
    iconutil -c icns "$iconset" -o "$res/AppIcon.icns"
    rm -rf "$iconset"
}

echo -e "${YELLOW}[2/5]${NC} Construyendo UniDex.app..."
make_bundle "$MAIN_APP" "com.github.jjjulianleon.unidex" "main_gtk.py" "false"
echo -e "${GREEN}✓ $MAIN_APP${NC}"

echo -e "${YELLOW}[3/5]${NC} Construyendo UniDex Widget.app..."
make_bundle "$WIDGET_APP" "com.jjjulianleon.productivitywidget" "widget_gtk.py" "true"
echo -e "${GREEN}✓ $WIDGET_APP${NC}"

# ------------------------------------------------------------------- entorno
echo -e "${YELLOW}[4/5]${NC} Configurando entorno virtual..."
for app in "$MAIN_APP" "$WIDGET_APP"; do
    res="$app/Contents/Resources"
    "$BREW_PYTHON" -m venv --system-site-packages "$res/.venv"
    "$res/.venv/bin/pip" install -q -r "$res/requirements_macos.txt"
done
echo -e "${GREEN}✓ Dependencias Python instaladas${NC}"

# --------------------------------------------------------------- inicio auto
# El widget NO arranca solo salvo que se pida: ./install_macos.sh --autostart
if [[ "$1" != "--autostart" ]]; then
    launchctl unload "$WIDGET_AGENT" 2>/dev/null || true
    rm -f "$WIDGET_AGENT"
    echo -e "${YELLOW}[5/5]${NC} Inicio automatico del widget: ${BLUE}desactivado${NC} (usa --autostart para activarlo)"
else
echo -e "${YELLOW}[5/5]${NC} Configurando inicio automatico del widget..."
mkdir -p "$LAUNCH_AGENTS"
cat > "$WIDGET_AGENT" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.jjjulianleon.unidex.widget</string>
    <key>ProgramArguments</key>
    <array>
        <string>$WIDGET_APP/Contents/MacOS/UniDexWidget</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><false/>
</dict>
</plist>
EOF
launchctl unload "$WIDGET_AGENT" 2>/dev/null || true
launchctl load "$WIDGET_AGENT"
echo -e "${GREEN}✓ Widget arranca con la sesion${NC}"
fi

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   ✅ Instalacion completada${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BLUE}•${NC} Abre ${YELLOW}UniDex${NC} desde Spotlight (⌘+Espacio)"
echo -e "  ${BLUE}•${NC} Widget (solo cuando lo abras): ${YELLOW}open \"$WIDGET_APP\"${NC}"
echo -e "  ${BLUE}•${NC} Vault de Obsidian: exporta ${YELLOW}UNIDEX_OBSIDIAN_VAULT${NC} si no esta en la ruta por defecto"
echo -e "  ${BLUE}•${NC} Desinstalar: ${YELLOW}$SOURCE_DIR/uninstall_macos.sh${NC}"
echo ""
