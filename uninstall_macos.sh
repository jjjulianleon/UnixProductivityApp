#!/bin/bash
# UniDex - macOS uninstaller (no borra tus datos)

set -e

WIDGET_AGENT="$HOME/Library/LaunchAgents/com.jjjulianleon.unidex.widget.plist"
DATA_DIR="$HOME/Library/Application Support/UniDex"

launchctl unload "$WIDGET_AGENT" 2>/dev/null || true
rm -f "$WIDGET_AGENT"

pkill -f "UniDex.app/Contents" 2>/dev/null || true

rm -rf "/Applications/UniDex.app" "/Applications/UniDex Widget.app"

echo "✅ UniDex desinstalado"
echo "Tus datos siguen en: $DATA_DIR"
echo "Para borrarlos tambien: rm -rf \"$DATA_DIR\""
