#!/bin/bash
# =============================================================================
# Unix Productivity App - Fedora Installation Script
# Installs the main app and widget as native Fedora applications
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_NAME="unix-productivity"
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
AUTOSTART_DIR="$HOME/.config/autostart"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Unix Productivity App - Fedora Installer${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check dependencies
echo -e "${YELLOW}[1/6]${NC} Verificando dependencias..."

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 no encontrado. Por favor instala python3${NC}"
    exit 1
fi

# Check GTK4 and Adwaita
python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1')" 2>/dev/null || {
    echo -e "${RED}❌ GTK4 y Libadwaita no encontrados${NC}"
    echo -e "Instala con: sudo dnf install gtk4-devel libadwaita-devel python3-gobject"
    exit 1
}

echo -e "${GREEN}✓ Dependencias verificadas${NC}"

# Create directories
echo -e "${YELLOW}[2/6]${NC} Creando directorios..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICONS_DIR"
mkdir -p "$AUTOSTART_DIR"
echo -e "${GREEN}✓ Directorios creados${NC}"

# Copy application files
echo -e "${YELLOW}[3/6]${NC} Copiando archivos de la aplicación..."
cp -r "$SOURCE_DIR/src" "$INSTALL_DIR/"
cp -r "$SOURCE_DIR/assets" "$INSTALL_DIR/"
cp "$SOURCE_DIR/main_gtk.py" "$INSTALL_DIR/"
cp "$SOURCE_DIR/widget_gtk.py" "$INSTALL_DIR/"
cp "$SOURCE_DIR/ics_integration.py" "$INSTALL_DIR/"
cp "$SOURCE_DIR/icloud_integration.py" "$INSTALL_DIR/"
cp "$SOURCE_DIR/requirements_gtk.txt" "$INSTALL_DIR/"
cp "$SOURCE_DIR/plasmoid_backend.py" "$INSTALL_DIR/"
echo -e "${GREEN}✓ Archivos copiados a $INSTALL_DIR${NC}"

# Copy icon
cp "$SOURCE_DIR/assets/app_icon.svg" "$ICONS_DIR/$APP_NAME.svg"
echo -e "${GREEN}✓ Icono instalado${NC}"

# Create launcher scripts
echo -e "${YELLOW}[4/6]${NC} Creando scripts de lanzamiento..."

# Main app launcher
cat > "$BIN_DIR/$APP_NAME" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
exec python3 main_gtk.py "\$@"
EOF
chmod +x "$BIN_DIR/$APP_NAME"

# Widget launcher
cat > "$BIN_DIR/${APP_NAME}-widget" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
exec python3 widget_gtk.py "\$@"
EOF
chmod +x "$BIN_DIR/${APP_NAME}-widget"

echo -e "${GREEN}✓ Scripts creados en $BIN_DIR${NC}"

# Create desktop entries
echo -e "${YELLOW}[5/6]${NC} Creando entradas de menú..."

# Main app .desktop
cat > "$DESKTOP_DIR/$APP_NAME.desktop" << EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Unix Productivity
GenericName=Task Manager
Comment=Productivity application with calendar, kanban, pomodoro and more
Exec=$BIN_DIR/$APP_NAME
Icon=$APP_NAME
Terminal=false
Categories=Office;ProjectManagement;Calendar;
Keywords=tasks;calendar;kanban;pomodoro;productivity;
StartupNotify=true
StartupWMClass=com.github.jjjulianleon.unixproductivity
EOF

# Widget .desktop
cat > "$DESKTOP_DIR/${APP_NAME}-widget.desktop" << EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Productivity Widget
GenericName=Desktop Widget
Comment=Compact productivity widget for desktop
Exec=$BIN_DIR/${APP_NAME}-widget
Icon=$APP_NAME
Terminal=false
Categories=Office;Utility;
Keywords=widget;tasks;calendar;
StartupNotify=false
NoDisplay=true
EOF

echo -e "${GREEN}✓ Entradas de menú creadas${NC}"

# Auto-start configuration
echo -e "${YELLOW}[6/6]${NC} Configurando inicio automático del widget..."

cat > "$AUTOSTART_DIR/${APP_NAME}-widget.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Productivity Widget
Exec=$BIN_DIR/${APP_NAME}-widget
Icon=$APP_NAME
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=3
Hidden=false
NoDisplay=false
Comment=Desktop productivity widget
EOF

echo -e "${GREEN}✓ Widget configurado para inicio automático${NC}"

# Update desktop database
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   ✅ Instalación completada exitosamente!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Ahora puedes:"
echo -e "  ${BLUE}•${NC} Buscar '${YELLOW}Unix Productivity${NC}' en GNOME Activities"
echo -e "  ${BLUE}•${NC} Ejecutar desde terminal: ${YELLOW}$APP_NAME${NC}"
echo -e "  ${BLUE}•${NC} El widget iniciará automáticamente con tu sesión"
echo ""
echo -e "Para ejecutar el widget manualmente:"
echo -e "  ${YELLOW}${APP_NAME}-widget${NC}"
echo ""
echo -e "Para desinstalar:"
echo -e "  ${YELLOW}$SOURCE_DIR/uninstall.sh${NC}"
echo ""
