"""
Central signal hub for application-wide communication
"""
"""
Central signal hub for application-wide communication
Generic implementation to support both GTK and Qt (or standalone)
"""

class GenericSignal:
    """Simple signal implementation with connect/emit"""
    def __init__(self):
        self._slots = []
        
    def connect(self, slot):
        if slot not in self._slots:
            self._slots.append(slot)
            
    def disconnect(self, slot):
        if slot in self._slots:
            self._slots.remove(slot)
            
    def emit(self, *args, **kwargs):
        for slot in self._slots:
            try:
                slot(*args, **kwargs)
            except Exception as e:
                print(f"Error emitting signal: {e}")

class SignalHub:
    """Central hub for all application signals"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if SignalHub._instance is not None:
            raise RuntimeError("Use get_instance() instead")
        
        # Task signals
        self.task_added = GenericSignal()
        self.task_updated = GenericSignal()
        self.task_deleted = GenericSignal()
        self.tasks_reloaded = GenericSignal()
        
        # Note signals
        self.note_added = GenericSignal()
        self.note_updated = GenericSignal()
        self.note_deleted = GenericSignal()
        self.notes_reloaded = GenericSignal()
        
        # Pomodoro signals
        self.pomodoro_started = GenericSignal()
        self.pomodoro_completed = GenericSignal()
        self.pomodoro_tick = GenericSignal()  # remaining seconds
        
        # Schedule signals
        self.schedule_updated = GenericSignal()
        
        # Statistics signals
        self.stats_updated = GenericSignal()
        
        # Notification signals
        self.notification_triggered = GenericSignal()  # title, message, urgency
        self.reminder_due = GenericSignal()  # task data
        
        # Settings signals
        self.settings_changed = GenericSignal()  # key, value
        self.theme_changed = GenericSignal()  # theme name
        
        # Sync signals
        self.obsidian_sync_started = GenericSignal()
        self.obsidian_sync_completed = GenericSignal()
        self.backup_completed = GenericSignal()  # backup path
        
        # External integrations
        self.teams_events_updated = GenericSignal()
        self.brightspace_deadlines_updated = GenericSignal()
        self.ics_sync_completed = GenericSignal()
        self.ics_error = GenericSignal()

# Global signal hub instance
signals = SignalHub.get_instance()


# Global signal hub instance
signals = SignalHub.get_instance()
