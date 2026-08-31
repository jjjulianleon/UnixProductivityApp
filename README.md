# UniDex

Aplicacion de productividad para Linux y macOS con integracion a Obsidian, calendario estilo Microsoft Teams, gestion de tareas con Kanban y temporizador Pomodoro.

Desarrollada con Python 3.13 y GTK4 + Libadwaita, con aspecto nativo en cada plataforma.

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
- GTK4 + Libadwaita + PyGObject
- SQLite (incluido con Python)
- Sistema operativo: Linux (GNOME/KDE Plasma) o macOS 12+

### Dependencias de Integraciones

- **caldav >= 1.2.0**: Para sincronizacion con iCloud Calendar (CalDAV)
- **icalendar >= 5.0.0**: Para importar calendarios ICS (Brightspace, Teams)
- **requests >= 2.28.0**: Para obtener feeds ICS remotos

---

## Instalacion

### Instalar todas las dependencias

```bash
# Linux
pip install -r requirements_gtk.txt

# macOS (GTK4 viene de Homebrew, ver install_macos.sh)
pip install -r requirements_macos.txt
```

### O instalar manualmente

```bash
pip install PyGObject>=3.42.0 pycairo>=1.20.0 caldav>=1.2.0 icalendar>=5.0.0 requests>=2.28.0
```

### Clonar o descargar el proyecto

```bash
cd ~/Desktop
git clone <repositorio> CalendarWidget
cd CalendarWidget
```

### Instalacion en macOS

La app es GTK4 + Libadwaita en ambas plataformas; en macOS el stack GTK viene de Homebrew.

```bash
./install_macos.sh
```

El instalador:

1. Instala con Homebrew `gtk4`, `libadwaita`, `pygobject3`, `adwaita-icon-theme` y `librsvg`
2. Construye `/Applications/UniDex.app` y `/Applications/UniDex Widget.app` (con icono `.icns` generado desde `assets/app_icon.svg`)
3. Crea un venv `--system-site-packages` dentro de cada bundle con `requirements_macos.txt`
4. El widget **no** arranca solo; abrelo cuando quieras desde `UniDex Widget.app`. Para que inicie con la sesion: `./install_macos.sh --autostart`

Para desinstalar (conserva tus datos):

```bash
./uninstall_macos.sh
```

**Diferencias en macOS**

| Aspecto | Linux | macOS |
|---------|-------|-------|
| Datos y config | `~/.local/share/UniDex`, `~/.config/…` | `~/Library/Application Support/…` |
| Notificaciones | `notify-send` | `osascript` (Centro de Notificaciones) |
| Abrir archivos | `xdg-open` | `open` |
| Inicio automatico del widget | `~/.config/autostart` (activo) | LaunchAgent opcional (`--autostart`) |
| Widget de escritorio | Plasmoide nativo de KDE | Ventana flotante (`UniDex Widget.app`) |
| Modificador de atajos | Ctrl | ⌘ (Command) |
| Ventana | Translucida | Opaca (macOS no da vibrancy a GTK) |
| Barra de titulo | Una por panel (Adwaita) | Igual; los semaforos caen en la del sidebar |
| Seleccion del sidebar | Relleno tenue de Adwaita | Relleno solido del color de acento, como Finder |
| Hoja de estilos | `src/gtk/styles/style.css` | + `src/gtk/styles/macos.css` encima |

El vault de Obsidian se detecta automaticamente (iCloud Drive o `~/Documents/Obsidian`). Para forzar otra ruta:

```bash
export UNIDEX_OBSIDIAN_VAULT="/ruta/a/tu/vault"
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
python main_gtk.py
```

### Ejecutar el widget de escritorio

```bash
python widget_gtk.py
```

### Ejecutar ambos

```bash
python main_gtk.py &
python widget_gtk.py &
```

---

## Estructura del Proyecto

```
CalendarWidget/
|-- main_gtk.py                 # Punto de entrada de la aplicacion (GTK4/Libadwaita)
|-- widget_gtk.py               # Widget de escritorio
|-- icloud_integration.py       # Sincronizacion con iCloud Calendar (CalDAV)
|-- ics_integration.py          # Integracion unificada ICS (Brightspace/Teams)
|-- teams_integration.py        # Integracion con Microsoft Teams Graph API
|-- brightspace_integration.py  # Integracion con Brightspace D2L (API)
|-- requirements_gtk.txt        # Dependencias en Linux
|-- requirements_macos.txt      # Dependencias en macOS
|-- README.md                   # Este archivo
|-- Manual_Tecnico.md           # Documentacion tecnica
|-- Manual_Usuario.md           # Manual de usuario
|-- install.sh                  # Instalacion en Linux
|-- install_macos.sh            # Construye UniDex.app y UniDex Widget.app
|
|-- src/
|   |-- core/
|   |   |-- database.py         # Persistencia SQLite con backup/export
|   |   |-- task_manager.py     # Operaciones CRUD de tareas
|   |   |-- obsidian_sync.py    # Sincronizacion bidireccional con Obsidian
|   |   |-- notifications.py    # Recordatorios de fechas limite
|   |   |-- auto_sync.py        # Sincronizacion periodica en segundo plano
|   |   |-- signals.py          # Hub central de senales
|   |
|   |-- gtk/
|   |   |-- __init__.py         # init_theme(): CSS, iconos y fuente
|   |   |-- window.py           # Ventana principal (NavigationSplitView)
|   |   |-- styles/
|   |   |   |-- style.css       # Tema unico (app y widget)
|   |   |   |-- macos.css       # Ajustes para que se vea nativa en macOS
|   |   |-- views/              # Dashboard, tareas, calendario, estadisticas
|   |   |-- widgets/            # Kanban, Pomodoro, notas, horario, comunes
|   |   |-- dialogs/            # Nueva tarea, configuracion
|   |
|   |-- utils/
|       |-- system.py           # Capa de plataforma (rutas, notificaciones)
|       |-- constants.py        # Configuracion y constantes
|
|-- assets/
|   |-- app_icon.svg            # Icono principal de la aplicacion
|   |-- icons/                  # Iconos simbolicos propios de UniDex
|
|-- tests/
|   |-- test_app_actions.py     # Acciones, atajos y navegacion
|   |-- test_icons.py           # Todos los iconos existen en el tema
|   |-- test_database.py
|   |-- test_obsidian_sync.py
|   |-- test_ics_integration_flow.py
|
|-- plasmoid/                   # Plasmoid de KDE (opcional)
```

---

## Almacenamiento de Datos

### Base de Datos

Ubicacion: `~/.local/share/UniDex/data.db` (Linux) o `~/Library/Application Support/UniDex/data.db` (macOS)

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

Ubicacion: subcarpeta `backups/` junto a la base de datos

Formatos de exportacion:
- JSON
- CSV
- SQLite (copia de la base de datos)

---

## Atajos de Teclado

En macOS se usa ⌘ (Command); en Linux, Ctrl.

| macOS | Linux    | Accion                                    |
|-------|----------|-------------------------------------------|
| ⌘1-⌘8 | Ctrl+1-8 | Dashboard, Tareas, Kanban, Calendario, Horario, Pomodoro, Notas, Estadisticas |
| ⌘N    | Ctrl+N   | Nueva tarea                               |
| ⌘,    | Ctrl+,   | Configuracion                             |
| ⌘W    | Ctrl+W   | Cerrar ventana                            |
| ⌘Q    | Ctrl+Q   | Salir                                     |

---

## Configuracion del Widget

1. Ejecutar el widget: `python widget_gtk.py`
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

Relativas al vault detectado (`$UNIDEX_OBSIDIAN_VAULT`, iCloud Drive en macOS, o `~/Documents/Obsidian`):

- Personal: `Personal/Pendientes Personal.md`
- Universidad: `Universidad/8vo Semestre/Pendientes Universidad.md`
- Fedora: `Pendientes Fedora.md`
- Pasantias: `Pasantías/Pendientes Pasantía.md`

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
