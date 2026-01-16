"""
Central signal hub for application-wide communication
"""
from PyQt6.QtCore import QObject, pyqtSignal


class SignalHub(QObject):
    """Central hub for all application signals"""
    
    _instance = None
    
    # Task signals
    task_added = pyqtSignal(dict)
    task_updated = pyqtSignal(int, dict)
    task_deleted = pyqtSignal(int)
    tasks_reloaded = pyqtSignal()
    
    # Note signals
    note_added = pyqtSignal(dict)
    note_updated = pyqtSignal(int)
    note_deleted = pyqtSignal(int)
    notes_reloaded = pyqtSignal()
    
    # Pomodoro signals
    pomodoro_started = pyqtSignal(int)
    pomodoro_completed = pyqtSignal(int)
    pomodoro_tick = pyqtSignal(int)  # remaining seconds
    
    # Schedule signals
    schedule_updated = pyqtSignal()
    
    # Statistics signals
    stats_updated = pyqtSignal()
    
    # Notification signals
    notification_triggered = pyqtSignal(str, str, str)  # title, message, urgency
    reminder_due = pyqtSignal(dict)  # task data
    
    # Settings signals
    settings_changed = pyqtSignal(str, object)  # key, value
    theme_changed = pyqtSignal(str)  # theme name
    
    # Sync signals
    obsidian_sync_started = pyqtSignal()
    obsidian_sync_completed = pyqtSignal()
    backup_completed = pyqtSignal(str)  # backup path
    
    # External integrations
    teams_events_updated = pyqtSignal(list)
    brightspace_deadlines_updated = pyqtSignal(list)
    ics_sync_completed = pyqtSignal(dict)
    ics_error = pyqtSignal(str)
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if SignalHub._instance is not None:
            raise RuntimeError("Use get_instance() instead")
        super().__init__()


# Global signal hub instance
signals = SignalHub.get_instance()
