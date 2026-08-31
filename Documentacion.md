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

Aplicacion de productividad multiplataforma (Linux y macOS) que integra:

1. Gestion de tareas con sincronizacion bidireccional a Obsidian
2. Calendario y horario semanal
3. Importacion de fechas limite desde Brightspace D2L e iCloud (CalDAV)
4. Widget de escritorio compacto
5. Temporizador Pomodoro con estadisticas

### Publico Objetivo

Estudiantes universitarios que usan:
- Linux (GNOME o KDE Plasma) o macOS 12+
- Obsidian para notas
- Brightspace D2L como plataforma academica
- Microsoft Teams / iCloud para su calendario

### Filosofia de Diseno

- **Aspecto nativo en cada plataforma.** Se usan los patrones de Libadwaita
  (NavigationSplitView, ToolbarView, HeaderBar) en vez de una UI propia. En
  macOS una segunda hoja de estilos la vuelve opaca y ajusta barras y sidebar,
  porque el sistema no da vibrancy a GTK y la translucidez de Linux se ve sucia.
- **Sin colores fijos.** Todo sale de los colores nombrados de Adwaita
  (`@window_bg_color`, `@card_bg_color`) o de `alpha(currentColor, x)`, para que
  el tema claro y el oscuro funcionen sin dos hojas separadas.
- **Fuente del sistema** por defecto, configurable desde Ajustes.
- UI en espanol, sin distracciones.

---

---

## Stack Tecnologico

### Lenguaje y Framework

| Componente | Tecnologia | Version |
|------------|------------|---------|
| Lenguaje | Python | 3.13 |
| Framework GUI | GTK4 + Libadwaita | 4.22 / 1.9 |
| Binding | PyGObject | 3.42+ |
| Base de datos | SQLite | 3.x |
| Sistemas operativos | Linux (GNOME/KDE), macOS | 12+ |

### Dependencias Python

**Archivos:** `requirements_gtk.txt` (Linux), `requirements_macos.txt` (macOS)

```
PyGObject>=3.42.0   # Binding de GTK4 (solo Linux; en macOS viene de Homebrew)
pycairo>=1.20.0     # Requerido por PyGObject
caldav>=1.2.0       # Sincronizacion iCloud Calendar (CalDAV)
icalendar>=5.0.0    # Parseo de calendarios ICS
requests>=2.28.0    # Obtener feeds ICS remotos
```

En macOS, GTK4 y Libadwaita se instalan con Homebrew y el entorno virtual se
crea con `--system-site-packages` para verlos:

```bash
brew install gtk4 libadwaita pygobject3 adwaita-icon-theme librsvg
```

`caldav` e `icalendar` son opcionales: si faltan, la app arranca igual y solo
se desactiva la sincronizacion de calendarios.

### Rutas del Sistema

| Recurso | Linux | macOS |
|---------|-------|-------|
| Base de datos | `~/.local/share/UniDex/data.db` | `~/Library/Application Support/UniDex/data.db` |
| Backups | `~/.local/share/UniDex/backups/` | `~/Library/Application Support/UniDex/backups/` |
| Configuracion | `~/.config/UniDex/` | `~/Library/Application Support/UniDex/` |
| Vault de Obsidian | `~/Documents/Obsidian` | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents` |

Las rutas las resuelve `src/utils/system.py`, el unico modulo que sabe en que
sistema se esta ejecutando. `$UNIDEX_OBSIDIAN_VAULT` sobreescribe la del vault.

---

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

**src/core/** - Logica de negocio (sin nada de UI)
- `database.py`: Singleton SQLite. Acepta una ruta opcional (`Database(":memory:")`) para los tests.
- `task_manager.py`: CRUD de tareas y fachada sobre Obsidian, ICS e iCloud.
- `obsidian_sync.py`: Lectura y escritura de los .md del vault. Las rutas son inyectables.
- `auto_sync.py`: Sincronizacion periodica en segundo plano.
- `notifications.py`: Recordatorios de fechas limite (3 dias, 1 dia, mismo dia).
- `signals.py`: Hub de senales propio (`connect` / `emit`), sin dependencias de GUI.

**src/gtk/** - Interfaz GTK4
- `__init__.py`: `init_theme()`, que carga CSS, iconos propios y la fuente elegida.
- `window.py`: Ventana principal. `NAV_ITEMS` define las 8 vistas, su titulo y su icono.
- `styles/style.css`: Hoja unica, compartida con el widget.
- `styles/macos.css`: Se carga encima en macOS para el aspecto nativo del sistema.
- `views/`: `dashboard.py`, `tasks.py`, `calendar.py`, `stats.py`
- `widgets/`: `kanban.py`, `pomodoro.py`, `notes.py`, `schedule.py`, `task_detail.py`, `common.py`
- `dialogs/`: `add_task.py`, `settings.py`

**src/utils/** - Utilidades
- `system.py`: Capa de plataforma. Rutas, notificaciones, abrir archivos, `IS_MAC`.
- `constants.py`: Constantes, categorias, prioridades y la lista de fuentes por plataforma.

**assets/icons/** - Iconos simbolicos propios, para lo que el tema Adwaita no trae.

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
- [x] Layout nativo de Libadwaita (NavigationSplitView + ToolbarView)
- [x] Hoja de estilos unica para la app y el widget
- [x] Compatible con tema claro y oscuro
- [x] Hoja de ajustes especifica para macOS
- [x] Iconos simbolicos propios donde Adwaita no llega
- [x] Estados vacios compactos dentro de tarjetas

### Funcionalidades Parciales

**Integraciones externas:**
- [x] iCloud Calendar via CalDAV (sincronizacion bidireccional)
- [x] Importacion ICS unificada (Brightspace y Teams)
- [ ] Microsoft Teams Calendar via Graph API (estructura lista, sin credenciales)
- [ ] Brightspace D2L via API (estructura lista, sin credenciales)

**UI:**
- [x] Temporizador Pomodoro con duraciones configurables
- [x] Dialogo de configuracion (General, Pomodoro, Integraciones)
- [x] Selector de fuente por plataforma
- [ ] Punto de corte responsive para colapsar el sidebar en ventanas estrechas

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

### SignalHub (`src/core/signals.py`)

Singleton que centraliza la comunicacion entre componentes. La implementacion es
propia (`connect` / `disconnect` / `emit`), sin depender de ningun toolkit, para
que el nucleo pueda usarse desde la app, desde el widget o desde un test.

```python
class GenericSignal:
    def connect(self, slot): ...
    def disconnect(self, slot): ...
    def emit(self, *args, **kwargs): ...   # los errores de un slot no cortan el resto


class SignalHub:
    # Tareas
    task_added / task_updated / task_deleted / tasks_reloaded
    # Notas
    note_added / note_updated / note_deleted / notes_reloaded
    # Pomodoro
    pomodoro_started / pomodoro_completed / pomodoro_tick
    # Horario, estadisticas, notificaciones, configuracion, sincronizacion
    schedule_updated, stats_updated, notification_triggered, reminder_due,
    settings_changed, theme_changed,
    obsidian_sync_started, obsidian_sync_completed, backup_completed,
    ics_sync_completed, teams_events_updated
```

### Uso Tipico

```python
from src.core.signals import signals

signals.task_added.emit({'id': 1, 'title': 'Nueva tarea'})
signals.task_added.connect(self._on_task_added)
```

### Quien escucha que

`TasksView` y `KanbanBoard` se suscriben por su cuenta a las senales de tarea.
El resto de vistas (dashboard, calendario, horario, estadisticas) no lo hacen:
`MainWindow._connect_signals()` conecta las cuatro senales de tarea a
`refresh_views()`, que refresca todas las vistas que tengan `refresh()`.

> Al anadir una vista nueva basta con darle un metodo `refresh()`. Si se
> suscribe ademas por su cuenta, se refrescara dos veces por cambio.

Desde un hilo que no sea el principal hay que envolver la actualizacion de UI en
`GLib.idle_add()`, como hace `auto_sync`.

---

## Sistema de Estilos

### Archivos: `src/gtk/styles/style.css` y `src/gtk/styles/macos.css`

Una sola hoja para la aplicacion y para el widget. Antes cada uno definia sus
propios `.glass-card` y `.task-card` con valores distintos, y parecian dos
programas diferentes. Las carga `init_theme()`; en macOS se anade `macos.css`
encima para sobreescribir lo especifico de Linux.

### Paleta

Los colores se declaran como colores nombrados de Adwaita, respetando su
contrato: `_bg_color` es el relleno solido, `_fg_color` el texto encima, y
`accent_color` el acento usado como texto sobre el fondo de ventana (por eso es
un azul mas oscuro: tiene que contrastar tambien en tema claro).

```css
@define-color accent_bg_color #4285f4;
@define-color accent_fg_color #ffffff;
@define-color accent_color    #1a73e8;
@define-color success_color   #34a853;
@define-color warning_color   #f9ab00;
@define-color danger_color    #ea4335;
```

Todo lo demas se apoya en `@window_bg_color`, `@card_bg_color` y
`alpha(currentColor, x)`. **Regla: ningun color fijo para claro u oscuro.**
`alpha(white, 0.1)` era invisible en tema claro; `alpha(currentColor, 0.1)`
sigue al texto y funciona en los dos.

### Clases propias

| Clase | Uso |
|-------|-----|
| `.glass-card` | Tarjeta generica |
| `.task-card` + `.priority-alta/media/baja` | Tarjeta de tarea con borde de prioridad |
| `.color-dot` / `.color-bar` + `.accent/.warning/.error/.success` | Puntos e indicadores de color |
| `.kanban-column`, `.kanban-column-header`, `.drag-hover` | Tablero Kanban |
| `.schedule-cell`, `.schedule-day-header`, `.schedule-today` | Rejilla del horario |
| `.chart-bar` | Barras del grafico semanal |
| `.empty-list` | Quita el recuadro a una lista vacia |
| `.pomodoro-timer`, `.pomodoro-time` | Cronometros monoespaciados |

El resto (`.title-1`..`.title-4`, `.dim-label`, `.caption`, `.heading`,
`.boxed-list`, `.navigation-sidebar`, `.card`, `.flat`, `.circular`,
`.suggested-action`) lo aporta Libadwaita: no se redefine.

### Reglas al tocar la UI

1. **Colores por clase CSS, no por `Gtk.CssProvider` por widget.**
   `get_style_context().add_provider()` esta deprecado y ademas los providers se
   acumulan: el horario creaba 91 (uno por celda) en cada refresco.
   La unica excepcion viva son los eventos del horario, que llevan un color
   arbitrario guardado en la base de datos.
2. **Verificar que el icono existe.** GTK no avisa de un nombre inexistente:
   dibuja un cuadro gris. `tests/test_icons.py` escanea el codigo y falla si
   alguno no resuelve. Si Adwaita no lo tiene, se anade un SVG a
   `assets/icons/hicolor/scalable/actions/`.
3. **`Adw.StatusPage` solo a pagina completa.** Dentro de una tarjeta dibuja un
   icono de 128px; ahi va `empty_state()` de `src/gtk/widgets/common.py`.

---

## Problemas Conocidos

### macOS no expone vibrancy a GTK

**Problema:** Una ventana semi-transparente deja ver el escritorio y se lee mal.

**Solucion:** `macos.css` hace la ventana opaca y el widget casi opaco (0.97).
La translucidez real solo se usa en Linux.

### El tema Adwaita trae pocos iconos

**Problema:** Nombres razonables como `view-column-symbolic` o
`utilities-system-monitor-symbolic` no existen; GTK dibuja un cuadro gris sin
emitir ningun aviso.

**Solucion:** `tests/test_icons.py` los detecta antes de que lleguen a la UI.
Los que no existen se sustituyen por equivalentes reales o se anaden como SVG
propio en `assets/icons/`.

### `CURRENT_TIMESTAMP` de SQLite es UTC

**Problema:** Las columnas con `DEFAULT CURRENT_TIMESTAMP` se guardan en UTC,
pero las consultas comparaban contra `datetime.now()`, que es local. En UTC-5
los pomodoros de la tarde contaban como del dia siguiente y desaparecian de "hoy".

**Solucion:** `date(started_at, 'localtime')` en la consulta. Al escribir una
consulta nueva sobre una fecha, comprobar en que huso esta cada lado.

### Editar una tarea no puede arrastrar a sus vecinas

**Problema:** `update_task` y `delete_task` localizaban la tarea con
`title in line`, una comparacion por subcadena: borrar "Estudiar" se llevaba por
delante "Estudiar calculo" y "Estudiar fisica" del vault del usuario.

**Solucion:** un unico parser (`_parse_task_line`) que devuelve el titulo real, y
comparacion exacta contra el. Leer, actualizar y borrar pasan por el mismo sitio.

### La UI solo se toca desde el hilo principal

**Problema:** `sync_external_calendars()` corre en un hilo de fondo y emite
senales desde ahi. Con una vista suscrita, GTK4 (que no es thread-safe) acababa
en `Gtk-CRITICAL` y segfault intermitente.

**Solucion:** `bind_signals()` en `src/gtk/widgets/common.py` envuelve cada
callback en `GLib.idle_add`. **Toda** suscripcion al hub desde la UI debe pasar
por ahi; ademas desconecta sola cuando el widget se destruye, porque el hub es
un singleton de proceso y seguiria llamando a widgets ya liberados.

### Las dependencias de calendario son opcionales

**Problema:** `HAS_ICS` solo comprueba que el modulo se pueda importar, pero
`icalendar` se valida despues, al construir el parser. Una `ImportError` ahi
tumbaba la aplicacion entera al arrancar.

**Solucion:** `TaskManager.__init__` construye la sincronizacion dentro de un
`try`. Sin `icalendar` la app abre igual, solo sin calendarios.

---

## Roadmap de Desarrollo

### Fase 1 - Core (COMPLETADA)

- [x] Estructura del proyecto
- [x] Base de datos SQLite
- [x] CRUD de tareas
- [x] Sistema de senales
- [x] Sistema de estilos

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

- [x] Tests automatizados (46 tests en verde)
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

**GTK4:**
- Prefijo `_` para metodos privados
- Construccion de UI en `_setup_ui()`, conexiones en `_connect_signals()`
- Colores y tamanos por clase CSS, nunca con un `Gtk.CssProvider` por widget
- Comprobar que cada icono existe (`tests/test_icons.py` lo verifica)

### Estructura de una Vista Nueva

```python
class NuevaVista(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.set_margin_top(20)     # margenes iguales que las demas vistas
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)

        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        """Construir la interfaz. El titulo lo pone la barra: no repetirlo."""

    def refresh(self):
        """Releer datos. MainWindow.refresh_views() la llama en cada cambio."""
```

Para que aparezca en el sidebar basta con anadirla a `NAV_ITEMS` en
`src/gtk/window.py` (clave, etiqueta, titulo e icono) e instanciarla en
`_build_stack()`. El atajo Cmd/Ctrl+N sale del orden de la lista.

### Tests

```bash
python -m unittest discover -s tests    # 46 tests
```

Los tests **nunca** deben tocar el vault ni la base de datos reales:
`Database(":memory:")` y `ObsidianSync(vault_paths=..., rough_notes_folder=...)`
aceptan rutas inyectadas justamente para eso.

---

## Contacto

Desarrollador: Julian Leon
Proyecto: UniDex
Plataformas: Linux (GNOME / KDE Plasma) y macOS 12+

---

Ultima actualizacion: Agosto 2026
