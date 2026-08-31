"""
Shared constants and configuration
"""
from pathlib import Path

from .system import IS_MAC, config_dir, data_dir, obsidian_vault

# Application info
APP_NAME = "UniDex"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Julian Leon"

# Semester Constraints (2026)
from datetime import datetime
# El horario va de la semana del 16 de agosto a la del 16 de diciembre.
# Fuera de esas fechas no se pinta nada del horario semanal.
SEMESTER_START = datetime(2026, 8, 16)
SEMESTER_END = datetime(2026, 12, 20)
INTERNSHIP_END = datetime(2026, 2, 14)

# Paths (platform-aware, see src/utils/system.py)
DATA_DIR = data_dir(APP_NAME)
CONFIG_DIR = config_dir(APP_NAME)

# Obsidian paths
OBSIDIAN_VAULT = obsidian_vault()
OBSIDIAN_VAULT_PATHS = {
    "Personal": OBSIDIAN_VAULT / "Personal/Pendientes Personal.md",
    "Universidad": OBSIDIAN_VAULT / "Universidad/8vo Semestre/Pendientes Universidad.md",
    "Fedora": OBSIDIAN_VAULT / "Pendientes Fedora.md"
}
OBSIDIAN_ROUGH_NOTES = OBSIDIAN_VAULT / "Rough Notes"
OBSIDIAN_PASANTIAS = OBSIDIAN_VAULT / "Pasantías/Pendientes Pasantía.md"

# Fuentes ofrecidas en Configuracion: (etiqueta, familia CSS).
# El indice es lo que se guarda en settings['app_font'], asi que el orden importa.
# Una sola lista para el dialogo, la app y el widget.
APP_FONTS = [
    ("Sistema (predeterminado)", ""),
    ("SF Mono", "'SF Mono'"),
    ("Helvetica Neue", "'Helvetica Neue'"),
    ("New York", "'New York'"),
    ("Menlo", "'Menlo'"),
    ("Fira Code", "'Fira Code'"),
] if IS_MAC else [
    ("Sistema (predeterminado)", ""),
    ("Source Code Pro", "'Source Code Pro'"),
    ("Inter", "'Inter'"),
    ("Roboto", "'Roboto'"),
    ("Ubuntu", "'Ubuntu'"),
    ("Fira Code", "'Fira Code'"),
]


def font_css(index: int) -> str:
    """Familia CSS para el indice guardado; cadena vacia = fuente del sistema"""
    if isinstance(index, int) and 0 <= index < len(APP_FONTS):
        return APP_FONTS[index][1]
    return ""


# Vistas del calendario ofrecidas en Configuracion > Apariencia.
# La clave es lo que se guarda en settings['calendar_view'].
CALENDAR_VIEWS = [
    ("Puntos", "dots"),
    ("Mes", "month"),
]

# Task statuses
TASK_STATUSES = ["pendiente", "en progreso", "completado"]

# Task priorities
TASK_PRIORITIES = ["alta", "media", "baja"]

# Categories
TASK_CATEGORIES = ["Personal", "Universidad", "Fedora"]

# Pomodoro defaults
POMODORO_WORK_DURATION = 25  # minutes
POMODORO_SHORT_BREAK = 5    # minutes
POMODORO_LONG_BREAK = 15    # minutes
POMODORO_SESSIONS_BEFORE_LONG_BREAK = 4

# Widget dimensions
WIDGET_WIDTH = 520
WIDGET_HEIGHT = 320

# Main app dimensions
MAIN_APP_MIN_WIDTH = 1200
MAIN_APP_MIN_HEIGHT = 700

# Days of week in Spanish
DAYS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
DAYS_ES_SHORT = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

# Months in Spanish
MONTHS_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# Schedule hours
SCHEDULE_START_HOUR = 6
SCHEDULE_END_HOUR = 22

# Notification thresholds (days before deadline)
NOTIFICATION_THRESHOLDS = [0, 1, 3]  # today, tomorrow, 3 days
