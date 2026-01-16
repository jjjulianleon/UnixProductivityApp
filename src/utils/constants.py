"""
Shared constants and configuration
"""
from pathlib import Path

# Application info
APP_NAME = "UnixProductivityApp"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Julian Leon"

# Paths
DATA_DIR = Path.home() / ".local" / "share" / APP_NAME
CONFIG_DIR = Path.home() / ".config" / APP_NAME

# Obsidian paths
OBSIDIAN_VAULT_PATHS = {
    "Personal": Path.home() / "Documents/Obsidian/Personal/Pendientes Personal.md",
    "Universidad": Path.home() / "Documents/Obsidian/Universidad/8vo Semestre/Pendientes Universidad.md",
    "Fedora": Path.home() / "Documents/Obsidian/Pendientes Fedora.md"
}
OBSIDIAN_ROUGH_NOTES = Path.home() / "Documents/Obsidian/Rough Notes"

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
