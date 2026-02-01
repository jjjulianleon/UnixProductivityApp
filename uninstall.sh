#!/bin/bash
# =============================================================================
# UniDex - Uninstall Script
# =============================================================================

APP_NAME="unidex"
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
AUTOSTART_DIR="$HOME/.config/autostart"

echo "🗑️ Desinstalando UniDex..."

# Remove files
rm -rf "$INSTALL_DIR"
rm -f "$BIN_DIR/$APP_NAME"
rm -f "$BIN_DIR/${APP_NAME}-widget"
rm -f "$DESKTOP_DIR/$APP_NAME.desktop"
rm -f "$DESKTOP_DIR/${APP_NAME}-widget.desktop"
rm -f "$ICONS_DIR/$APP_NAME.svg"
rm -f "$AUTOSTART_DIR/${APP_NAME}-widget.desktop"

# Update databases
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo "✅ Desinstalación completada"
echo ""
echo "Nota: Los datos de usuario se mantienen en:"
echo "  - ~/.config/calendar_widget/"
echo "  - Base de datos SQLite"
echo ""
echo "Para eliminar también los datos de usuario, ejecuta:"
echo "  rm -rf ~/.config/calendar_widget"
