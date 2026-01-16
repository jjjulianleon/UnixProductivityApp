#!/bin/bash
# Installation script for Calendar Widget

echo "🚀 Instalando Calendar Widget..."

# Create directories
mkdir -p ~/.local/share/applications
mkdir -p ~/.local/bin

# Copy main script
cp calendar_widget.py ~/.local/bin/calendar_widget.py
chmod +x ~/.local/bin/calendar_widget.py

# Create desktop entry
cat > ~/.local/share/applications/calendar-widget.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Calendar Widget
Comment=Glassmorphism Calendar Widget
Exec=python3 ~/.local/bin/calendar_widget.py
Icon=calendar
Terminal=false
Categories=Utility;Office;
Keywords=calendar;widget;schedule;obsidian;
StartupWMClass=calendar_widget
EOF

echo "✅ Instalación completada!"
echo ""
echo "Puedes ejecutar el widget de las siguientes formas:"
echo "  1. Buscar 'Calendar Widget' en el menú de aplicaciones"
echo "  2. Ejecutar: python3 ~/.local/bin/calendar_widget.py"
echo ""
echo "Para añadirlo al inicio automático:"
echo "  - Ve a Configuración del Sistema > Arranque y Apagado > Inicio Automático"
echo "  - Añade 'Calendar Widget'"
