# Documentacion Tecnica - UniDex

Este documento contiene la documentacion tecnica completa de UniDex, incluyendo arquitectura, estado actual de implementacion, integraciones pendientes y roadmap de desarrollo.

---

## Tabla de Contenidos

1. [Vision General del Proyecto](#vision-general-del-proyecto)
2. [Stack Tecnologico](#stack-tecnologico)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Estado Actual de Implementacion](#estado-actual-de-implementacion)
5. [Integraciones Externas](#integraciones-externas)
6. [Esquema de Base de Datos](#esquema-de-base-de-datos)
7. [Sistema de Senales](#sistema-de-senales)
8. [Sistema de Estilos](#sistema-de-estilos)
9. [Problemas Conocidos](#problemas-conocidos)
10. [Roadmap de Desarrollo](#roadmap-de-desarrollo)
11. [Guia para Contribuir](#guia-para-contribuir)

---

## Vision General del Proyecto

### Objetivo

Crear una aplicacion de productividad nativa para Fedora Linux con KDE Plasma que integre:

1. Gestion de tareas con sincronizacion a Obsidian
2. Calendario con conexion a Microsoft Teams
3. Importacion de fechas limite desde Brightspace D2L (plataforma universitaria)
4. Widget de escritorio siempre visible
5. Temporizador Pomodoro con estadisticas

### Publico Objetivo

Estudiantes universitarios que usan:
- Fedora Linux con KDE Plasma (Wayland)
- Obsidian para notas
- Microsoft Teams para clases y reuniones
- Brightspace D2L como plataforma academica

### Filosofia de Diseno

- Glassmorphism: Fondos semi-transparentes con blur
- Fuente monoespaciada: Source Code Pro
- Colores oscuros con acentos en azul
- UI en espanol
- Interfaz limpia sin distracciones

---

## Stack Tecnologico

### Lenguaje y Framework

| Componente | Tecnologia | Version |
|------------|------------|---------|
| Lenguaje | Python | 3.13 |
| Framework GUI | PyQt6 | 6.x |
| Base de datos | SQLite | 3.x |
| Sistema operativo | Fedora Linux | 41 |
| Entorno de escritorio | KDE Plasma | 6.x |
| Display server | Wayland | - |

### Dependencias Python

**Archivo:** requirements.txt

```
PyQt6>=6.4.0        # Framework GUI principal
caldav>=1.2.0       # Sincronizacion iCloud Calendar (CalDAV)
icalendar>=5.0.0    # Parseo de calendarios ICS
requests>=2.28.0    # Obtener feeds ICS remotos
```

### Rutas del Sistema

| Recurso | Ruta |
|---------|------|
| Base de datos | ~/.local/share/UniDex/data.db |
| Backups | ~/.local/share/UniDex/backups/ |
| Configuracion | ~/.config/UniDex/ |
| Config ICS | ~/.config/calendar_widget/ics_config.json |
| Config iCloud | ~/.config/calendar_widget/icloud_config.json |
| Cache ICS | ~/.config/calendar_widget/cache/ |
| Token MS Teams | ~/.config/calendar_widget/ms_token.json |

---

## Arquitectura del Sistema

### Patron de Arquitectura

La aplicacion sigue un patron MVC modificado con un sistema de senales centralizado para comunicacion entre componentes:

```
+------------------+     +------------------+     +------------------+
|      Views       |     |      Core        |     |     Database     |
|  (UI Components) |<--->|  (Business Logic)|<--->|    (SQLite)      |
+------------------+     +------------------+     +------------------+
         ^                       ^
         |                       |
         v                       v
+--------------------------------------------------+
|              SignalHub (Evento central)          |
+--------------------------------------------------+
```

### Modulos Principales

**src/core/** - Logica de negocio
- database.py: Singleton que maneja todas las operaciones SQLite
- task_manager.py: CRUD de tareas con validacion
- obsidian_sync.py: Sincronizacion bidireccional con archivos markdown
- notifications.py: Integracion con sistema de notificaciones Linux
- signals.py: Hub central de senales PyQt para comunicacion reactiva

**src/ui/widgets/** - Componentes visuales reutilizables
- calendar.py: Widget de calendario mensual con grid
- schedule.py: Vista semanal con canvas personalizado (QPainter)
- kanban.py: Tablero con columnas y drag-and-drop
- pomodoro.py: Temporizador con barra de progreso
- quick_notes.py: Editor de notas con sincronizacion
- common.py: Componentes compartidos (DraggableTaskCard, etc)

**src/ui/views/** - Vistas principales de la aplicacion
- dashboard.py: Pagina de inicio con resumen
- tasks_view.py: Vista completa del Kanban con filtros
- calendar_view.py: Calendario mensual + horario semanal
- statistics_view.py: Graficos de productividad

**src/ui/dialogs/** - Ventanas modales
- task_dialogs.py: Crear/editar tareas, crear/editar eventos
- settings_dialog.py: Configuracion de la aplicacion

**src/utils/** - Utilidades
- styles.py: Tema glassmorphism, funciones de estilo CSS
- constants.py: Configuracion global, rutas, valores por defecto

### Flujo de Datos

```
Usuario interactua con UI
         |
         v
View emite senal (ej: task_added)
         |
         v
SignalHub propaga la senal
         |
         v
Core procesa la logica (TaskManager)
         |
         v
Database persiste los datos
         |
         v
SignalHub emite senal de confirmacion
         |
         v
Todas las Views se actualizan
```

---

## Estado Actual de Implementacion

### Funcionalidades Completadas

**Core:**
- [x] Base de datos SQLite con todas las tablas
- [x] CRUD completo de tareas
- [x] CRUD de eventos del horario
- [x] CRUD de notas rapidas
- [x] Sistema de estadisticas
- [x] Sistema de backups (JSON, CSV, SQLite)
- [x] Sincronizacion con Obsidian (lectura y escritura)
- [x] Sistema de senales centralizado

**UI - Aplicacion Principal:**
- [x] Sidebar de navegacion
- [x] Dashboard con resumen del dia
- [x] Tablero Kanban con drag-and-drop
- [x] Vista de calendario mensual
- [x] Vista de horario semanal (estilo Teams)
- [x] Notas rapidas con lista
- [x] Temporizador Pomodoro
- [x] Vista de estadisticas con graficos
- [x] Dialogo de configuracion
- [x] Dialogo de backup/export
- [x] Atajos de teclado

**UI - Widget de Escritorio:**
- [x] Calendario compacto
- [x] Mini Kanban
- [x] Lista de deadlines
- [x] Pomodoro compacto
- [x] Ventana arrastrable
- [x] Siempre en escritorio

**Diseno:**
- [x] Tema glassmorphism
- [x] Fuente Source Code Pro
- [x] Colores consistentes
- [x] Tarjetas con bordes de categoria
- [x] Iconos y badges

### Funcionalidades Parciales

**Integraciones externas:**
- [x] iCloud Calendar via CalDAV (sincronizacion bidireccional)
- [x] Importacion ICS unificada (Brightspace y Teams)
- [ ] Microsoft Teams Calendar via Graph API (estructura lista, sin credenciales)
- [ ] Brightspace D2L via API (estructura lista, sin credenciales)

**UI:**
- [x] Temporizador Pomodoro con duraciones configurables
- [x] Dialogo de configuracion con tabs (General, Pomodoro, Integraciones)
- [ ] Animaciones de transicion (basicas)
- [ ] Combobox dropdowns con fondo oscuro (problema de Qt en Wayland)

### Funcionalidades Pendientes

- [ ] Configuracion de rutas de Obsidian desde UI
- [ ] Temas claros/oscuros
- [ ] Exportar a Google Calendar
- [ ] Sincronizacion en la nube
- [ ] Aplicacion movil complementaria

---

## Integraciones Externas

### Microsoft Teams Calendar

**Archivo:** teams_integration.py

**Estado:** Estructura implementada, requiere configuracion

**Metodo de autenticacion:** OAuth2 via Microsoft Graph API

**Configuracion requerida:**
1. Registrar aplicacion en Azure Portal
2. Obtener CLIENT_ID, CLIENT_SECRET, TENANT_ID
3. Configurar permisos: Calendars.Read, User.Read
4. Completar variables en teams_integration.py

**Clases principales:**
- MSGraphAuth: Manejo de tokens OAuth2
- TeamsCalendar: Fetch de eventos del calendario

**Funcionalidades:**
- Obtener eventos del dia/semana
- Cache de eventos en memoria
- Autenticacion con refresh token

### Brightspace D2L

**Archivo:** brightspace_integration.py

**Estado:** Estructura implementada, multiples opciones

**Opciones de integracion:**

1. **API Oficial** (requiere acceso institucional)
   - La universidad debe habilitar acceso a la API
   - Requiere App ID y App Key del administrador

2. **Web Scraping** (alternativa)
   - Usa credenciales de estudiante
   - Menos estable, puede romperse con actualizaciones

3. **ICS/iCal** (recomendado)
   - Brightspace exporta calendarios en formato iCal
   - No requiere API access
   - Metodo mas simple y estable

**Clase principal:**
- BrightspaceCalendar: Obtener deadlines de tareas

**Funcionalidades:**
- Parse de calendario ICS
- Cache de deadlines (30 minutos)
- Conversion a formato interno

### iCloud Calendar (CalDAV)

**Archivo:** icloud_integration.py

**Estado:** Funcional con configuracion

**Clase principal:** ICloudSync

**Configuracion:** ~/.config/calendar_widget/icloud_config.json

**Funcionalidades:**
- Conexion a iCloud via CalDAV
- Obtener eventos del calendario
- Sincronizar deadlines locales a iCloud
- Sincronizar eventos del horario semanal a iCloud
- Deteccion de eventos duplicados

**Requisitos:**
- Libreria caldav: `pip install caldav`
- App-specific password de Apple

---

### Integracion ICS Unificada

**Archivo:** ics_integration.py

**Estado:** Funcional

**Clases principales:**
- ICSConfig: Gestor de configuracion
- ICSParser: Parser de archivos/URLs ICS
- BrightspaceIntegration: Deadlines de D2L
- TeamsIntegration: Eventos de Teams/Outlook
- ICSCalendarManager: Orquestador principal

**Configuracion:** ~/.config/calendar_widget/ics_config.json

**Funcionalidades:**
- Parsear archivos ICS locales
- Parsear URLs de feeds ICS
- Deteccion automatica de cursos (CMP 4005, CMP 5002, etc.)
- Categorizacion automatica de tipos de eventos (tarea, examen, proyecto)
- Cache de eventos en disco

---

### Obsidian

**Archivo:** src/core/obsidian_sync.py

**Estado:** Completamente funcional

**Rutas configuradas:**
```python
OBSIDIAN_VAULT_PATHS = {
    "Personal": "~/Documents/Obsidian/Personal/Pendientes Personal.md",
    "Universidad": "~/Documents/Obsidian/Universidad/8vo Semestre/Pendientes Universidad.md",
    "Fedora": "~/Documents/Obsidian/Pendientes Fedora.md"
}
OBSIDIAN_ROUGH_NOTES = "~/Documents/Obsidian/Rough Notes/"
```

**Formato de tareas:**
```markdown
- [ ] Titulo | Descripcion [deadline: YYYY-MM-DD] [priority: alta/media/baja] (en progreso)
- [x] Tarea completada
```

**Funcionalidades:**
- Lectura de tareas desde archivos .md
- Escritura de tareas a archivos .md
- Sincronizacion bidireccional
- Guardado de notas rapidas

---

## Esquema de Base de Datos

### Tabla: tasks

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    category TEXT NOT NULL,           -- 'Personal', 'Universidad', 'Fedora'
    status TEXT DEFAULT 'pendiente',  -- 'pendiente', 'en progreso', 'completado'
    priority TEXT DEFAULT 'media',    -- 'alta', 'media', 'baja'
    deadline TEXT,                    -- ISO format: 'YYYY-MM-DD'
    position INTEGER DEFAULT 0,       -- Para ordenamiento en Kanban
    tags TEXT DEFAULT '[]',           -- JSON array
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    obsidian_synced INTEGER DEFAULT 0
);
```

### Tabla: quick_notes

```sql
CREATE TABLE quick_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    file_path TEXT                    -- Ruta al archivo en Obsidian
);
```

### Tabla: pomodoro_sessions

```sql
CREATE TABLE pomodoro_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,                  -- Tarea asociada (opcional)
    duration_minutes INTEGER DEFAULT 25,
    completed INTEGER DEFAULT 0,
    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
    ended_at TEXT,
    session_type TEXT DEFAULT 'work', -- 'work', 'short_break', 'long_break'
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

### Tabla: schedule_events

```sql
CREATE TABLE schedule_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    day_of_week INTEGER NOT NULL,     -- 0=Lunes, 6=Domingo
    start_time TEXT NOT NULL,         -- 'HH:MM'
    end_time TEXT NOT NULL,           -- 'HH:MM'
    color TEXT DEFAULT '66, 133, 244', -- RGB sin parentesis
    recurring INTEGER DEFAULT 1,       -- 1=semanal, 0=unico
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Tabla: statistics

```sql
CREATE TABLE statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,        -- 'YYYY-MM-DD'
    tasks_completed INTEGER DEFAULT 0,
    pomodoros_completed INTEGER DEFAULT 0,
    total_focus_minutes INTEGER DEFAULT 0
);
```

### Tabla: settings

```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT                        -- JSON o string simple
);
```

**Claves de configuracion:**
- pomodoro_work: Duracion del trabajo (minutos)
- pomodoro_short_break: Descanso corto (minutos)
- pomodoro_long_break: Descanso largo (minutos)
- pomodoro_sessions: Sesiones antes de descanso largo
- theme: Tema de la aplicacion
- language: Idioma de la interfaz

### Tabla: reminders

```sql
CREATE TABLE reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    remind_at TEXT NOT NULL,          -- ISO datetime
    message TEXT,
    triggered INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);
```

### Tabla: backup_history

```sql
CREATE TABLE backup_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_path TEXT NOT NULL,
    backup_type TEXT DEFAULT 'manual', -- 'manual', 'auto'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## Sistema de Senales

### SignalHub (src/core/signals.py)

Patron Singleton que centraliza todas las senales de la aplicacion para comunicacion reactiva entre componentes.

```python
class SignalHub(QObject):
    # Tareas
    task_added = pyqtSignal(dict)
    task_updated = pyqtSignal(int, dict)
    task_deleted = pyqtSignal(int)
    tasks_reloaded = pyqtSignal()
    
    # Notas
    note_added = pyqtSignal(dict)
    note_updated = pyqtSignal(int)
    note_deleted = pyqtSignal(int)
    notes_reloaded = pyqtSignal()
    
    # Pomodoro
    pomodoro_started = pyqtSignal(int)
    pomodoro_completed = pyqtSignal(int)
    pomodoro_tick = pyqtSignal(int)
    
    # Horario
    schedule_updated = pyqtSignal()
    
    # Estadisticas
    stats_updated = pyqtSignal()
    
    # Notificaciones
    notification_triggered = pyqtSignal(str, str, str)
    reminder_due = pyqtSignal(dict)
    
    # Configuracion
    settings_changed = pyqtSignal(str, object)
    theme_changed = pyqtSignal(str)
    
    # Sincronizacion
    obsidian_sync_started = pyqtSignal()
    obsidian_sync_completed = pyqtSignal()
    backup_completed = pyqtSignal(str)
```

### Uso Tipico

```python
# Obtener instancia
signals = SignalHub.get_instance()

# Emitir senal
signals.task_added.emit({'id': 1, 'title': 'Nueva tarea'})

# Conectar a senal
signals.task_added.connect(self._on_task_added)
```

---

## Sistema de Estilos

### Archivo: src/utils/styles.py

### Paleta de Colores

```python
COLORS = {
    'primary': '66, 133, 244',      # Azul principal
    'secondary': '81, 162, 218',    # Azul secundario
    'success': '52, 168, 83',       # Verde
    'warning': '251, 188, 4',       # Amarillo
    'danger': '234, 67, 53',        # Rojo
    'text_primary': '230, 230, 240',
    'text_secondary': '180, 180, 190',
    'text_muted': '140, 140, 150',
    'bg_dark': '25, 25, 30',
    'bg_medium': '35, 35, 40',
    'bg_light': '50, 50, 55',
    
    # Categorias
    'personal': '66, 133, 244',     # Azul
    'universidad': '52, 168, 83',   # Verde
    'fedora': '81, 162, 218',       # Azul claro
    
    # Prioridades
    'priority_high': '234, 67, 53',   # Rojo
    'priority_medium': '251, 188, 4', # Amarillo
    'priority_low': '52, 168, 83',    # Verde
}
```

### Fuente

```python
FONT_FAMILY = "Source Code Pro"
```

### Estilos CSS Principales

**Glassmorphism base:**
```css
background-color: rgba(30, 30, 35, 230);
```

**Tarjetas:**
```css
background-color: rgba(50, 50, 55, 180);
border: 1px solid rgba(255, 255, 255, 0.05);
border-radius: 8px;
```

**Botones:**
```css
background-color: rgba(255, 255, 255, 0.08);
border: 1px solid rgba(COLOR, 0.3);
border-radius: 6px;
```

### Funciones de Estilo

- get_main_window_style()
- get_widget_style()
- get_button_style(variant)
- get_nav_button_style()
- get_input_style()
- get_combobox_style()
- get_scrollbar_style()
- get_scroll_area_style()
- get_card_style()
- get_category_color(category)
- get_priority_color(priority)
- get_deadline_color(deadline_str)

---

## Problemas Conocidos

### QComboBox dropdown con fondo blanco

**Problema:** En KDE Plasma con Wayland, los dropdown de QComboBox muestran un fondo blanco del sistema detras del contenido estilizado.

**Causa:** Qt usa el popup nativo del sistema en Wayland, ignorando los estilos CSS del QAbstractItemView.

**Estado:** Sin solucion satisfactoria. Intentos de usar QListView personalizado rompen el renderizado del texto.

**Workaround:** Aceptar el fondo parcialmente visible o usar widgets alternativos.

### D-Bus Tray Icon Warning

**Problema:** Al iniciar la app aparece:
```
QDBusTrayIcon encountered a D-Bus error: QDBusError("org.freedesktop.DBus.Error.ServiceUnknown")
```

**Causa:** El sistema no tiene un servicio de bandeja compatible activo.

**Impacto:** Solo warning, no afecta funcionalidad.

**Estado:** Ignorable, es comportamiento normal en algunos entornos.

### Drag and Drop visual glitches

**Problema:** Durante el drag and drop en el Kanban, ocasionalmente hay parpadeos visuales.

**Causa:** Repintado rapido durante animaciones.

**Estado:** Mejorado significativamente, queda pulido pendiente.

---

## Roadmap de Desarrollo

### Fase 1 - Core (COMPLETADA)

- [x] Estructura del proyecto
- [x] Base de datos SQLite
- [x] CRUD de tareas
- [x] Sistema de senales
- [x] Tema glassmorphism

### Fase 2 - UI Principal (COMPLETADA)

- [x] Sidebar y navegacion
- [x] Dashboard
- [x] Kanban con drag-and-drop
- [x] Calendario mensual
- [x] Horario semanal
- [x] Pomodoro con duraciones configurables
- [x] Estadisticas
- [x] Notas rapidas
- [x] Dialogo de configuracion con tabs

### Fase 3 - Widget (COMPLETADA)

- [x] Ventana widget
- [x] Componentes compactos
- [x] Arrastrable
- [x] Siempre en escritorio

### Fase 4 - Integraciones (AVANZADO)

- [x] Obsidian sync (bidireccional)
- [x] iCloud Calendar via CalDAV
- [x] Importacion ICS (Brightspace D2L, Teams)
- [x] Sincronizacion de deadlines a iCloud
- [x] Sincronizacion de eventos locales a iCloud
- [ ] Microsoft Teams via Graph API (pendiente credenciales)
- [ ] Google Calendar export

### Fase 5 - Pulido (EN PROGRESO)

- [x] Tests automatizados (43 tests passing)
- [x] DevContainer para desarrollo
- [ ] Animaciones suaves
- [ ] Temas adicionales
- [ ] Configuracion avanzada
- [ ] Documentacion de usuario
- [ ] Packaging (Flatpak/RPM)

### Fase 6 - Expansion (FUTURO)

- [ ] Sincronizacion en la nube
- [ ] App movil complementaria
- [ ] Plugins/extensiones
- [ ] Colaboracion multiusuario

---

## Guia para Contribuir

### Estructura de Commits

```
tipo(modulo): descripcion corta

Descripcion detallada si es necesario.
```

Tipos:
- feat: Nueva funcionalidad
- fix: Correccion de bug
- refactor: Refactorizacion de codigo
- style: Cambios de estilo/formato
- docs: Documentacion
- test: Tests

### Convenciones de Codigo

**Python:**
- PEP 8 para formato
- Type hints cuando sea posible
- Docstrings en funciones publicas
- Clases con mayuscula inicial
- Variables y funciones en snake_case

**PyQt6:**
- Prefijo _ para metodos privados
- Sufijo _layout, _widget para variables de layout
- Conectar senales en metodo _connect_signals()
- UI setup en metodo setup_ui()

### Estructura de Nuevos Widgets

```python
class NuevoWidget(QWidget):
    # Senales primero
    some_signal = pyqtSignal(type)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = SignalHub.get_instance()
        self.setup_ui()
        self._connect_signals()
    
    def setup_ui(self):
        """Construir la interfaz"""
        pass
    
    def _connect_signals(self):
        """Conectar senales del SignalHub"""
        pass
    
    def _on_some_event(self):
        """Handlers de eventos"""
        pass
```

---

## Contacto

Desarrollador: Julian Leon
Proyecto: UniDex
Plataforma: Fedora Linux / KDE Plasma

---

Ultima actualizacion: Enero 2026
