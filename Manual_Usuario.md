# Manual de Usuario - UniDex

## (Sistema de Productividad y Gestion de Tareas para Linux)

---

## Informacion general

- **Nombre del producto:** UniDex
- **Version:** 1.0.0
- **Fecha de emision:** 06/02/2026
- **Responsable del documento:** Julian Leon
- **Contacto de soporte:** [Pendiente de completar]
- **Autor:** Julian Leon

---

## Introduccion

UniDex es una aplicacion de productividad nativa para Linux disenada para estudiantes universitarios que utilizan Fedora con KDE Plasma o GNOME. Permite gestionar tareas mediante un tablero Kanban, planificar actividades con un calendario mensual y horario semanal, cronometrar sesiones de trabajo con Pomodoro, tomar notas rapidas y sincronizar toda la informacion con Obsidian, Brightspace D2L e iCloud Calendar.

Este manual esta dirigido a usuarios finales y tiene como objetivo proporcionar las instrucciones necesarias para instalar, configurar y utilizar eficazmente el sistema en su entorno de escritorio Linux.

---

## Objetivos

1. **Centralizar la gestion academica y personal** en una sola herramienta nativa de escritorio, eliminando la necesidad de alternar entre multiples aplicaciones web.
2. **Sincronizar automaticamente** fechas limite de Brightspace D2L, eventos de iCloud Calendar y tareas de Obsidian para mantener una vista unificada de pendientes.
3. **Mejorar la productividad** mediante el uso de un temporizador Pomodoro integrado con estadisticas de rendimiento diarias.
4. **Proporcionar acceso rapido** a la informacion mas relevante del dia a traves de un widget compacto que permanece visible en el escritorio.
5. **Facilitar la organizacion visual** de tareas mediante un tablero Kanban con arrastrar y soltar, prioridades y categorias.

---

## Requisitos del Sistema

### 3.1. Requisitos de Hardware

| Recurso | Minimo | Recomendado |
|---------|--------|-------------|
| Procesador | x86_64, 2 nucleos | Intel Core i3 o superior |
| Memoria RAM | 2 GB | 4 GB |
| Almacenamiento | 200 MB libres | 500 MB libres |
| Pantalla | 1366x768 | 1920x1080 o superior |

### 3.2. Requisitos de Software

| Componente | Requisito |
|------------|-----------|
| Sistema operativo | Fedora Linux 41+ (recomendado), Ubuntu 22.04+, o cualquier distribucion con GTK4 |
| Entorno de escritorio | KDE Plasma 6.x o GNOME 45+ |
| Display server | Wayland (recomendado) o X11 |
| Python | 3.10 o superior (desarrollado con 3.13) |
| GTK4 | 4.0+ con Libadwaita 1.x |
| Fuente tipografica | Source Code Pro (recomendada) |

### 3.3. Dependencias del Sistema

**Fedora:**
```bash
sudo dnf install gtk4-devel libadwaita-devel python3-gobject python3-pip
```

**Ubuntu/Debian:**
```bash
sudo apt install libgtk-4-dev libadwaita-1-dev python3-gi python3-pip
```

---

## Acceso a la Aplicacion

### 4.1. Instalacion

1. Clonar o descargar el proyecto:
   ```bash
   git clone <url-repositorio> CalendarWidget
   cd CalendarWidget
   ```

2. Ejecutar el script de instalacion:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. El instalador verificara las dependencias, copiara los archivos necesarios a `~/.local/share/unidex/`, creara un entorno virtual de Python, instalara las dependencias y configurara las entradas de menu.

4. Una vez completada la instalacion, la aplicacion aparecera en el menu de aplicaciones bajo el nombre **UniDex**.

### 4.2. Inicio de la Aplicacion

**Desde el menu de aplicaciones:**
- Buscar "UniDex" en GNOME Activities o en el lanzador de KDE.

**Desde la terminal:**
```bash
unidex          # Aplicacion principal
unidex-widget   # Widget de escritorio
```

**Inicio automatico del widget:**
El widget se configura automaticamente para iniciar con la sesion del escritorio. Puede deshabilitarse desde la configuracion de aplicaciones de inicio automatico del sistema.

### 4.3. Desinstalacion

```bash
./uninstall.sh
```

> **Nota:** La desinstalacion conserva los datos del usuario (base de datos y configuraciones) en `~/.config/calendar_widget/` y `~/.local/share/UniDex/`.

---

## Navegacion del Sistema

### 5.1. Estructura de la Interfaz

La aplicacion principal se compone de una **barra lateral de navegacion** a la izquierda y un **area de contenido** a la derecha que cambia segun la seccion seleccionada.

| Seccion | Descripcion | Icono/Etiqueta |
|---------|-------------|----------------|
| Dashboard | Vista general del dia actual con resumen de tareas pendientes y accesos rapidos | Dashboard |
| Kanban | Tablero de gestion de tareas con tres columnas: Pendiente, En Progreso, Completado | Kanban |
| Calendario | Vista mensual con indicadores de fechas limite y detalle por dia | Calendario |
| Pomodoro | Temporizador de trabajo con intervalos configurables y seguimiento de sesiones | Pomodoro |
| Notas Rapidas | Editor de notas sincronizado con Obsidian Rough Notes | Notas |
| Horario | Vista semanal tipo calendario de clases y eventos recurrentes | Horario |
| Estadisticas | Graficos de productividad: tareas completadas, sesiones Pomodoro y tiempo de enfoque | Estadisticas |

### 5.2. Atajos de Teclado

| Atajo | Accion |
|-------|--------|
| `Ctrl+1` | Ir a Dashboard |
| `Ctrl+2` | Ir a Tareas/Kanban |
| `Ctrl+3` | Ir a Calendario |
| `Ctrl+4` | Ir a Notas |
| `Ctrl+5` | Ir a Estadisticas |
| `Ctrl+N` | Crear nueva tarea |
| `Ctrl+F` | Enfocar campo de busqueda |
| `F5` | Refrescar datos |

---

## Funcionalidades Principales

### 6.1. Dashboard

La vista de Dashboard presenta un resumen del dia actual:

- **Contador de tareas:** Pendientes, para hoy, vencidas y completadas.
- **Proxima fecha limite:** Muestra la tarea urgente mas cercana con los dias restantes.
- **Proxima clase:** Si hay eventos en el horario semanal, indica cual es la siguiente clase y en cuantos minutos comienza.
- **Barra de progreso:** Porcentaje de tareas completadas del dia.

### 6.2. Tablero Kanban

El tablero Kanban organiza las tareas en tres columnas:

| Columna | Estado | Color del encabezado |
|---------|--------|----------------------|
| Pendiente | `pendiente` | Azul |
| En Progreso | `en progreso` | Amarillo |
| Completado | `completado` | Verde |

**Crear una tarea:**
1. Hacer clic en el boton "+" o usar `Ctrl+N`.
2. Completar el formulario: titulo, descripcion, categoria, prioridad y fecha limite.
3. Confirmar con "Guardar".

**Mover una tarea:**
- Arrastrar la tarjeta de una columna a otra para cambiar su estado.

**Filtrar tareas:**
- Usar el filtro de categoria en la parte superior del tablero (Todas, Personal, Universidad, Fedora).

**Indicadores visuales de las tarjetas:**
- **Borde izquierdo coloreado:** Indica la prioridad (rojo = alta, amarillo = media, verde = baja).
- **Etiqueta de categoria:** Color segun la categoria.
- **Fecha limite:** Con icono de calendario; se muestra en rojo si esta vencida.
- **Icono de sincronizacion Obsidian:** Aparece si la tarea esta sincronizada.

### 6.3. Calendario Mensual

- Muestra un grid del mes actual con navegacion entre meses.
- Los dias con tareas pendientes muestran **indicadores rojos** (puntos).
- **El dia actual** se resalta con un fondo circular azul.
- Al hacer clic en un dia, se muestra una lista lateral con las tareas asociadas a esa fecha.

### 6.4. Horario Semanal

Vista tipo calendario de clases que muestra eventos recurrentes por dia de la semana:

1. Hacer clic en un bloque horario vacio para **crear un evento**.
2. Completar: titulo, dia de la semana, hora de inicio, hora de fin y color.
3. Los eventos recurrentes aparecen automaticamente cada semana.
4. Hacer clic en un evento existente para editarlo o eliminarlo.

**Rango horario visible:** 6:00 AM a 10:00 PM.

### 6.5. Temporizador Pomodoro

El temporizador sigue la tecnica Pomodoro con los siguientes valores predeterminados:

| Parametro | Valor por defecto |
|-----------|-------------------|
| Trabajo | 25 minutos |
| Descanso corto | 5 minutos |
| Descanso largo | 15 minutos |
| Sesiones antes de descanso largo | 4 |

**Uso:**
1. Seleccionar una tarea asociada (opcional).
2. Presionar "Iniciar" para comenzar la sesion de trabajo.
3. Al finalizar el tiempo de trabajo, se inicia automaticamente un descanso corto.
4. Cada 4 sesiones, el descanso es largo.
5. Las sesiones completadas se registran en las estadisticas.

**Configurar duraciones:**
Abrir el dialogo de configuracion y ajustar los valores en la pestana "Pomodoro".

### 6.6. Notas Rapidas

- Permite crear notas cortas con titulo y contenido en formato texto.
- Las notas se guardan en la base de datos local y se sincronizan con la carpeta `~/Documents/Obsidian/Rough Notes/` en formato Markdown.
- Pueden crearse desde cualquier vista usando el acceso rapido en el Dashboard o Widget.

### 6.7. Estadisticas

Muestra graficos de productividad que incluyen:

- **Tareas completadas por dia:** Visualizacion semanal y mensual.
- **Sesiones Pomodoro completadas:** Conteo diario.
- **Tiempo de enfoque acumulado:** Minutos totales de sesiones de trabajo finalizadas.

---

## Widget de Escritorio

### 7.1. Descripcion

El widget es una ventana compacta de **520x380 pixeles** que permanece visible en el escritorio, proporcionando acceso rapido a la informacion mas importante sin necesidad de abrir la aplicacion principal.

### 7.2. Componentes del Widget

| Componente | Ubicacion | Descripcion |
|------------|-----------|-------------|
| Reloj | Superior izquierda | Hora actual, se actualiza cada 30 segundos |
| Botones de accion | Superior derecha | Nota rapida y abrir aplicacion principal |
| Cajas de estadisticas | Fila superior | Pendientes, Hoy, Vencidas, Completadas |
| Calendario compacto | Centro izquierda | Mini calendario mensual con indicadores |
| Fecha limite urgente | Centro derecha | Tarea mas proxima a vencer |
| Pomodoro compacto | Centro derecha | Temporizador del widget |
| Proxima clase | Inferior | Siguiente evento del horario |
| Barra de progreso | Inferior | Porcentaje de tareas del dia completadas |

### 7.3. Interaccion

- El widget es **arrastrable**: hacer clic y mantener en la barra superior para reposicionar.
- Los datos se **actualizan automaticamente** cada 30 segundos.
- El temporizador Pomodoro tiene su propio ciclo de actualizacion cada segundo.

---

## Integraciones

### 8.1. Obsidian

UniDex sincroniza bidireccionalmente las tareas con archivos Markdown de Obsidian:

| Categoria | Ruta del archivo en Obsidian |
|-----------|------------------------------|
| Personal | `~/Documents/Obsidian/Personal/Pendientes Personal.md` |
| Universidad | `~/Documents/Obsidian/Universidad/8vo Semestre/Pendientes Universidad.md` |
| Fedora | `~/Documents/Obsidian/Pendientes Fedora.md` |
| Notas Rapidas | `~/Documents/Obsidian/Rough Notes/` |

**Formato de tareas en Obsidian:**
```markdown
- [ ] Titulo de la tarea | Descripcion opcional [deadline: 2026-01-31] [priority: alta] (en progreso)
- [x] Tarea completada
```

**Metadatos soportados:**
- Estado: `- [ ]` (pendiente), `- [x]` (completado), `(en progreso)` al final
- Fecha limite: `[deadline: YYYY-MM-DD]` o `📅 YYYY-MM-DD`
- Prioridad: `[priority: alta|media|baja]`
- Descripcion: despues del separador `|`

### 8.2. Brightspace D2L

Importa automaticamente las fechas limite desde la plataforma academica Brightspace D2L a traves de su feed ICS/iCal.

**Configuracion:**
1. En Brightspace, acceder a Calendario > Suscribirse al calendario > Copiar enlace ICS.
2. En UniDex, abrir Configuracion > Integraciones > pegar la URL del feed ICS.
3. La sincronizacion automatica se ejecuta cada 15 minutos en segundo plano.

**Cursos detectados automaticamente:**

| Codigo | Nombre del curso | Etiqueta |
|--------|------------------|----------|
| CMP 4005 | Redes | Redes |
| CMP 5002 | Data Mining | Data Mining |
| CMP 4002 | Base de Datos | Bases |
| FIN 4007 | Mercados Internacionales | Finanzas |
| ING 0001 | Coloquios | Coloquios |
| PRC 2000 | PASEC | PASEC |

### 8.3. iCloud Calendar

Sincronizacion bidireccional con iCloud Calendar via protocolo CalDAV.

**Configuracion:**
1. Generar una contrasena especifica de aplicacion en [appleid.apple.com](https://appleid.apple.com).
2. Editar el archivo `~/.config/calendar_widget/icloud_config.json`:
   ```json
   {
     "enabled": true,
     "apple_id": "su_correo@icloud.com",
     "app_password": "xxxx-xxxx-xxxx-xxxx",
     "calendar_name": "Calendar"
   }
   ```
3. Los eventos del horario semanal y las fechas limite se sincronizan automaticamente hacia iCloud.

### 8.4. Microsoft Teams

La integracion con Microsoft Teams permite importar eventos del calendario via Microsoft Graph API.

**Estado actual:** Estructura implementada, requiere configuracion de credenciales OAuth2.

**Requisitos para activarla:**
1. Registrar una aplicacion en Azure Active Directory.
2. Configurar permisos: `Calendars.Read`, `User.Read`.
3. Obtener `CLIENT_ID`, `CLIENT_SECRET` y `TENANT_ID`.
4. Completar las variables en el archivo `teams_integration.py`.

---

## Codigo de ejemplo

### Crear una tarea desde la linea de comandos (via Python)

```python
from src.core.task_manager import TaskManager

tm = TaskManager()
tm.add_task(
    title="Entregar informe de Redes",
    description="Capitulo 5 del libro de Kurose",
    category="Universidad",
    priority="alta",
    deadline="2026-03-15"
)
```

### Formato de tarea en Obsidian

```markdown
- [ ] Entregar informe de Redes | Capitulo 5 del libro de Kurose [deadline: 2026-03-15] [priority: alta]
```

### Configuracion ICS (ics_config.json)

```json
{
  "brightspace": {
    "enabled": true,
    "url": "https://usfq.brightspace.com/d2l/le/calendar/feed/..."
  },
  "teams": {
    "enabled": false,
    "url": ""
  }
}
```

---

## Informacion de investigacion

UniDex fue desarrollado como respuesta a la fragmentacion de herramientas de productividad en el ecosistema Linux. La investigacion previa identifico las siguientes necesidades del usuario objetivo (estudiantes universitarios en Linux):

1. **Falta de integracion nativa:** Las herramientas web (Brightspace, Teams) no ofrecen widgets nativos de escritorio en Linux, obligando a abrir el navegador constantemente.
2. **Obsidian como hub central:** Muchos estudiantes ya usan Obsidian para notas; la sincronizacion bidireccional permite gestionar tareas sin abandonar su flujo de trabajo.
3. **Widget siempre visible:** Inspirado en los widgets de Windows y macOS, se identifico la necesidad de un panel compacto y permanente que muestre la informacion del dia.
4. **Diseno glassmorphism:** Se opto por un estilo visual moderno con fondos semi-transparentes, coherente con las tendencias de escritorios Linux modernos.

---

## Viabilidad tecnica

### Stack actual

El sistema es completamente funcional sobre Python 3.13 con GTK4/Libadwaita para la interfaz nativa GNOME y un widget QML para KDE Plasma. La base de datos SQLite se incluye con Python, eliminando dependencias de servidores externos.

### Requerimientos de infraestructura

- **Sin servidor:** La aplicacion es 100% local, no requiere infraestructura en la nube.
- **Base de datos embebida:** SQLite no requiere instalacion ni configuracion separada.
- **Integraciones opcionales:** Las conexiones a Brightspace, iCloud y Teams son opcionales y configurables; la aplicacion funciona completamente sin ellas.

### Limitaciones conocidas

- La interfaz esta optimizada para el idioma espanol.
- Las rutas de Obsidian estan configuradas para una estructura de vault especifica y deben ajustarse manualmente.
- La integracion con Microsoft Teams requiere acceso a Azure Active Directory para obtener credenciales OAuth2.

---

## Alternativas consideradas

| Solucion alternativa | Pros | Contras |
|----------------------|------|---------|
| Notion + Google Calendar | Multiplataforma, colaborativo, muchas integraciones | No es nativo de Linux, requiere navegador, sin modo offline robusto |
| Todoist + Pomodoro web | Interfaz limpia, multiplataforma | Sin integracion con Obsidian ni Brightspace, sin widget nativo |
| Obsidian Tasks plugin | Ya integrado en Obsidian, formato Markdown | Sin Kanban visual, sin widget de escritorio, sin Pomodoro |
| GNOME To Do + Pomodoro GNOME | Nativo de GNOME, ligero | Sin integracion con calendarios academicos, sin Kanban, funcionalidad limitada |
| Planner/Tasks (KDE) | Nativo de KDE | Sin integracion con Brightspace ni Obsidian, sin vista unificada |

---

## Preguntas Frecuentes

### Donde se almacenan mis datos?

- **Base de datos:** `~/.local/share/UniDex/data.db`
- **Backups:** `~/.local/share/UniDex/backups/`
- **Configuracion:** `~/.config/calendar_widget/`

### Como exporto mis datos?

Desde la aplicacion principal, acceder a Configuracion > Backup/Export. Se soportan los formatos JSON, CSV y copia directa de la base de datos SQLite.

### El widget no aparece al iniciar sesion?

Verificar que el archivo `~/.config/autostart/unidex-widget.desktop` exista. Si fue eliminado, ejecutar nuevamente `install.sh` o crear manualmente la entrada de autostart.

### Las tareas de Obsidian no se sincronizan?

1. Verificar que las rutas en `src/utils/constants.py` coincidan con la estructura de su vault de Obsidian.
2. Asegurarse de que los archivos Markdown (`Pendientes Personal.md`, etc.) existan en las rutas configuradas.
3. Verificar que el formato de las tareas sea correcto (ver seccion 8.1).

### Como cambio las duraciones del Pomodoro?

Abrir Configuracion (icono de engranaje) > pestana Pomodoro > ajustar los valores de duracion de trabajo, descanso corto y descanso largo.

---

## Vinculos relevantes

- **Repositorio del proyecto:** [Pendiente de completar]
- **Documentacion tecnica:** Ver archivo `Documentacion.md` incluido en el proyecto
- **Hoja de ruta de migracion a Flutter:** Ver archivo `migracion_futura.md`
- **Obsidian:** [https://obsidian.md](https://obsidian.md)
- **Brightspace D2L:** [Pendiente de completar - URL institucional]
- **GTK4 Documentation:** [https://docs.gtk.org/gtk4/](https://docs.gtk.org/gtk4/)
- **Libadwaita:** [https://gnome.pages.gitlab.gnome.org/libadwaita/](https://gnome.pages.gitlab.gnome.org/libadwaita/)

---

**Ultima actualizacion:** Febrero 2026
**Autor:** Julian Leon
**Licencia:** MIT
