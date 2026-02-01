#!/bin/bash
# Direct install script for KDE Plasma Widget
# Bypasses kpackagetool6 validation issues by manual installation

APP_ID="com.jjjulianleon.unidex"
INSTALL_DIR="$HOME/.local/share/plasma/plasmoids/$APP_ID"
BACKEND_DIR="$HOME/.local/share/unidex"

echo "📦 Instalando widget nativo..."

# 1. Install Backend & App (Python scripts + src + assets)
echo "   -> Instalando backend y aplicación en $BACKEND_DIR"
rm -rf "$BACKEND_DIR"
mkdir -p "$BACKEND_DIR"
# Copy all necessary files for the app to run
cp -r src "$BACKEND_DIR/"
cp -r assets "$BACKEND_DIR/" 2>/dev/null || true
cp -r resources "$BACKEND_DIR/" 2>/dev/null || true
cp main_app.py "$BACKEND_DIR/"
cp main_gtk.py "$BACKEND_DIR/"
cp plasmoid_backend.py "$BACKEND_DIR/"

# 2. Fix Wrapper Script
echo "   -> Configurando ejecutable en ~/.local/bin/unidex"
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/unidex" << EOF
#!/bin/bash
cd "$BACKEND_DIR"
# Usamos main_gtk.py (Versión GTK migrada)
exec python3 main_gtk.py "\$@"
EOF
chmod +x "$HOME/.local/bin/unidex"

# 3. Install Plasmoid
echo "   -> Instalando plasmoid en $INSTALL_DIR"
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Copy package contents
cp -r plasmoid/package/* "$INSTALL_DIR/"

# NOTE: We do NOT create metadata.desktop anymore. 
# Plasma 6 prefers metadata.json which is already in plasmoid/package/metadata.json.
# Creating a legacy metadata.desktop with 'declarativeappletscript' causes "Unsupported Widget" error.

echo "✅ Widget instalado correctamente."
echo ""
echo "🔄 Reiniciando plasmashell para detectar cambios..."
# Try to restart plasma quietly
if command -v kquitapp6 >/dev/null; then
    kquitapp6 plasmashell || true
    kstart6 plasmashell >/dev/null 2>&1 &
elif command -v kquitapp5 >/dev/null; then
    kquitapp5 plasmashell || true
    kstart5 plasmashell >/dev/null 2>&1 &
else
    # Brute force
    killall plasmashell || true
    nohup plasmashell >/dev/null 2>&1 &
fi

echo "🚀 Listo! Busca 'UniDex Widget' en tu lista de widgets."
