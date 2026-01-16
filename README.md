# Glassmorphism Calendar Widget

Widget de escritorio flotante con efecto glassmorphism para KDE Plasma.

## ✨ Características

- **Vista Mensual**: Calendario del mes con el día actual resaltado
- **Vista Semanal**: Horario estilo Microsoft Teams con tus clases
- **Integración Obsidian**: Muestra pendientes de tus notas
- **Glassmorphism**: Fondo semitransparente con bordes redondeados
- **Arrastrable**: Mueve el widget a cualquier lugar de la pantalla

## 🚀 Instalación

```bash
# 1. Instalar dependencias
pip install PyQt6 requests

# 2. Ejecutar el instalador
chmod +x install.sh
./install.sh

# 3. Lanzar el widget
python3 calendar_widget.py
```

## ⚙️ Configuración

Edita la clase `Config` en `calendar_widget.py` para personalizar:

### Colores
```python
BG_COLOR = QColor(30, 30, 35, int(255 * 0.85))  # Fondo
ACCENT_COLOR = QColor(66, 133, 244)  # Color de acento
```

### Rutas de Obsidian
```python
PENDIENTES_FILES = [
    "/ruta/a/tu/archivo1.md",
    "/ruta/a/tu/archivo2.md",
]
```

### Horario
```python
SCHEDULE = {
    0: [  # Lunes (0=Lunes, 6=Domingo)
        ("13:00", "14:20", "Nombre Clase", "#color"),
    ],
    # ...
}
```

## 🔌 Integraciones Futuras

### Microsoft Teams (Graph API)
Para conectar con Teams necesitas:
1. Registrar una app en [Azure Portal](https://portal.azure.com)
2. Obtener Client ID y configurar permisos `Calendars.Read`
3. Ver `teams_integration.py` para más detalles

### Brightspace D2L
Para conectar con D2L necesitas:
1. Token de API institucional
2. URL de tu instancia de Brightspace
3. Ver `brightspace_integration.py` para más detalles

## 🎨 Uso en KDE Plasma

1. El widget ya funciona como ventana flotante independiente
2. Para modo "Dodge Windows": Click derecho en la barra de título > Más acciones > Mantener debajo
3. Para inicio automático: Configuración > Inicio automático > Añadir script

## 📝 Formato de Pendientes en Obsidian

El widget lee tareas en formato checkbox:

```markdown
# Mis Pendientes

- [ ] Tarea pendiente 1
- [ ] Tarea pendiente 2
- [x] Tarea completada (no se muestra)
```

## 🐛 Solución de Problemas

### El widget no aparece
```bash
# Verificar PyQt6
python3 -c "from PyQt6.QtWidgets import QApplication; print('OK')"
```

### Las tareas no se cargan
- Verifica que las rutas en `PENDIENTES_FILES` sean correctas
- Asegúrate de usar el formato `- [ ]` para las tareas

## 📄 Licencia

MIT License - Úsalo como quieras!
