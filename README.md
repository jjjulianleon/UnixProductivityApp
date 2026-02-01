# UniDex

Aplicacion de productividad para Linux diseñada para KDE Plasma con integracion a Obsidian, calendario estilo Microsoft Teams, gestion de tareas con Kanban y temporizador Pomodoro.

Desarrollada con Python 3.13 y PyQt6 con un diseno glassmorphism moderno.

---

## Tabla de Contenidos

1. [Caracteristicas](#caracteristicas)
2. [Requisitos](#requisitos)
3. [Instalacion](#instalacion)
4. [Uso](#uso)
5. [Estructura del Proyecto](#estructura-del-proyecto)
6. [Almacenamiento de Datos](#almacenamiento-de-datos)
7. [Atajos de Teclado](#atajos-de-teclado)
8. [Configuracion del Widget](#configuracion-del-widget)
9. [Integracion con Obsidian](#integracion-con-obsidian)
10. [Licencia](#licencia)

---

## Caracteristicas

### Aplicacion Principal

**Dashboard**
- Vista general del dia actual
- Tareas pendientes con fechas limite proximas
- Acceso rapido a todas las secciones

**Tablero Kanban**
- Gestion de tareas con drag and drop
- Tres columnas: Pendiente, En Progreso, Completado
- Tarjetas con informacion de categoria, prioridad y fecha limite
- Filtrado por categoria y busqueda

**Calendario**
- Vista mensual con indicadores de fechas limite
- Vista semanal estilo Microsoft Teams
- Canvas personalizado con QPainter para visualizacion fluida
- Eventos con soporte para horarios superpuestos
- Creacion, edicion y eliminacion de eventos

**Notas Rapidas**
- Notas sincronizadas con Obsidian Rough Notes
- Creacion rapida desde cualquier parte de la app
- Guardado automatico en formato markdown

**Temporizador Pomodoro**
- Intervalos configurables de trabajo y descanso
- Valores por defecto: 25/5/15 minutos
- Seguimiento de sesiones completadas
- Estadisticas de productividad

**Estadisticas**
- Graficos de productividad semanal y mensual
- Tareas completadas por dia
- Tiempo de enfoque acumulado
- Sesiones Pomodoro completadas

**Sistema de Notificaciones**
- Alertas de escritorio para fechas limite
- Recordatorios configurables
- Integracion con el sistema de notificaciones de Linux

### Widget de Escritorio

Dimensiones: 520x320 pixeles

Componentes:
- Calendario compacto con puntos indicadores de fechas limite
- Vista semanal del horario
- Mini Kanban con tareas pendientes y en progreso
- Lista de fechas limite para hoy y manana
- Temporizador Pomodoro compacto
- Boton de nota rapida
- Arrastrable y permanece en el escritorio

---

## Requisitos

- Python 3.10 o superior (desarrollado con 3.13)
- PyQt6 >= 6.4.0
- SQLite (incluido con Python)
- Sistema operativo: Linux (optimizado para KDE Plasma/Wayland)
- Fuente: Source Code Pro (recomendada)

### Dependencias de Integraciones

- **caldav >= 1.2.0**: Para sincronizacion con iCloud Calendar (CalDAV)
- **icalendar >= 5.0.0**: Para importar calendarios ICS (Brightspace, Teams)
- **requests >= 2.28.0**: Para obtener feeds ICS remotos

---

## Instalacion

### Instalar todas las dependencias

```bash
pip install -r requirements.txt
```

### O instalar manualmente

```bash
pip install PyQt6>=6.4.0 caldav>=1.2.0 icalendar>=5.0.0 requests>=2.28.0
```

### Clonar o descargar el proyecto

```bash
cd ~/Desktop
git clone <repositorio> CalendarWidget
cd CalendarWidget
```

### Desarrollo con Dev Container (opcional)

El proyecto incluye configuracion de devcontainer para desarrollo en VS Code:

1. Abrir el proyecto en VS Code
2. Instalar la extension "Dev Containers"
3. Ejecutar "Reopen in Container"

---

## Uso

### Ejecutar la aplicacion principal

```bash
python main_app.py
```

### Ejecutar el widget de escritorio

```bash
python widget.py
```

### Ejecutar ambos

```bash
python main_app.py &
python widget.py &
```

---

## Estructura del Proyecto

```
CalendarWidget/
|-- main_app.py                 # Punto de entrada de la aplicacion principal (PyQt6)
|-- main_gtk.py                 # Punto de entrada GTK4/Libadwaita
|-- widget.py                   # Punto de entrada del widget de escritorio
|-- widget_gtk.py               # Widget de escritorio GTK4
|-- icloud_integration.py       # Sincronizacion con iCloud Calendar (CalDAV)
|-- ics_integration.py          # Integracion unificada ICS (Brightspace/Teams)
|-- teams_integration.py        # Integracion con Microsoft Teams Graph API
|-- brightspace_integration.py  # Integracion con Brightspace D2L (API)
|-- requirements.txt            # Dependencias del proyecto
|-- README.md                   # Este archivo
|-- Documentacion.md            # Documentacion tecnica completa
|-- install.sh                  # Script de instalacion
|
|-- .devcontainer/              # Configuracion para desarrollo en contenedor
|   |-- devcontainer.json
|   |-- Dockerfile
|
|-- src/
|   |-- __init__.py
|   |
|   |-- core/
|   |   |-- __init__.py
|   |   |-- database.py         # Persistencia SQLite con backup/export
|   |   |-- task_manager.py     # Operaciones CRUD de tareas
|   |   |-- obsidian_sync.py    # Sincronizacion bidireccional con Obsidian
|   |   |-- notifications.py    # Notificaciones de escritorio Linux
|   |   |-- signals.py          # Hub central de senales PyQt
|   |
|   |-- ui/
|   |   |-- __init__.py
|   |   |
|   |   |-- widgets/
|   |   |   |-- __init__.py
|   |   |   |-- calendar.py     # Widget de calendario mensual
|   |   |   |-- schedule.py     # Vista semanal estilo Teams (QPainter)
|   |   |   |-- kanban.py       # Tablero Kanban con drag and drop
|   |   |   |-- pomodoro.py     # Temporizador Pomodoro configurable
|   |   |   |-- quick_notes.py  # Widget de notas rapidas
|   |   |   |-- common.py       # Componentes compartidos (tarjetas, etc)
|   |   |
|   |   |-- dialogs/
|   |   |   |-- __init__.py
|   |   |   |-- task_dialogs.py     # Dialogos de tareas y eventos
|   |   |   |-- settings_dialog.py  # Dialogo de configuracion con tabs
|   |   |
|   |   |-- views/
|   |   |   |-- __init__.py
|   |   |   |-- dashboard.py        # Vista del dashboard
|   |   |   |-- tasks_view.py       # Vista de tareas (Kanban completo)
|   |   |   |-- calendar_view.py    # Vista de calendario
|   |   |   |-- statistics_view.py  # Vista de estadisticas
|   |
|   |-- utils/
|       |-- __init__.py
|       |-- styles.py           # Tema glassmorphism y estilos
|       |-- constants.py        # Configuracion y constantes
|
|-- assets/
|   |-- icons/                  # Iconos de la aplicacion
|   |-- app_icon.svg            # Icono principal de la aplicacion
|
|-- tests/                      # Tests unitarios (43 tests)
|   |-- test_database.py
|   |-- test_obsidian_sync.py
|
|-- resources/                  # Recursos adicionales (archivos ICS)
```

---

## Almacenamiento de Datos

### Base de Datos

Ubicacion: `~/.local/share/UniDex/data.db`

Tablas:
- tasks: Tareas con titulo, descripcion, categoria, estado, prioridad, fecha limite
- quick_notes: Notas rapidas con titulo y contenido
- pomodoro_sessions: Sesiones de Pomodoro completadas
- schedule_events: Eventos del horario semanal
- statistics: Estadisticas diarias de productividad
- settings: Configuracion de la aplicacion
- reminders: Recordatorios programados
- backup_history: Historial de backups

### Backups

Ubicacion: `~/.local/share/UniDex/backups/`

Formatos de exportacion:
- JSON
- CSV
- SQLite (copia de la base de datos)

---

## Atajos de Teclado

| Atajo   | Accion            |
|---------|-------------------|
| Ctrl+1  | Ir a Dashboard    |
| Ctrl+2  | Ir a Tareas       |
| Ctrl+3  | Ir a Calendario   |
| Ctrl+4  | Ir a Notas        |
| Ctrl+5  | Ir a Estadisticas |
| Ctrl+N  | Nueva Tarea       |
| Ctrl+F  | Enfocar Busqueda  |
| F5      | Refrescar         |

---

## Configuracion del Widget

1. Ejecutar el widget: `python widget.py`
2. Posicionar el widget arrastrando
3. Para autostart, crear archivo en `~/.config/autostart/`:

```desktop
[Desktop Entry]
Type=Application
Name=UniDex Widget
Exec=python /ruta/a/CalendarWidget/widget.py
Hidden=false
X-KDE-autostart-after=panel
```

4. Configurar reglas de ventana en KDE System Settings para comportamiento "Dodge Windows"

---

## Integracion con Obsidian

### Rutas de sincronizacion configuradas

- Personal: `~/Documents/Obsidian/Personal/Pendientes Personal.md`
- Universidad: `~/Documents/Obsidian/Universidad/8vo Semestre/Pendientes Universidad.md`
- Fedora: `~/Documents/Obsidian/Pendientes Fedora.md`

### Notas rapidas

Se guardan en: `~/Documents/Obsidian/Rough Notes/`

### Formato de tareas en Obsidian

```markdown
- [ ] Titulo de la tarea | Descripcion opcional [deadline: 2026-01-31] [priority: alta] (en progreso)
```

Estados soportados:
- `- [ ]`: Pendiente
- `- [ ] ... (en progreso)`: En progreso
- `- [x]`: Completado

---

## Licencia

MIT License

---

## Autor

Julian Leon
