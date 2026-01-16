"""
Task Manager - Central task management with database, Obsidian sync and signals
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from .database import db
from .obsidian_sync import ObsidianSync
from .signals import signals


class TaskManager:
    """Central task manager that syncs between database and Obsidian"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.obsidian = ObsidianSync()
        self._initial_sync()
    
    def _initial_sync(self):
        """Sync tasks from Obsidian to database on startup"""
        try:
            obsidian_tasks = self.obsidian.read_all_tasks()
            
            for task in obsidian_tasks:
                existing = db.search_tasks(task['title'])
                matching = [t for t in existing if t['category'] == task['category']]
                
                if not matching:
                    db.add_task(
                        title=task['title'],
                        category=task['category'],
                        description=task.get('description', ''),
                        status=task.get('status', 'pendiente'),
                        priority=task.get('priority', 'media'),
                        deadline=task.get('deadline')
                    )
        except Exception:
            pass  # Silently fail if Obsidian sync fails
    
    def add_task(self, title: str, category: str, description: str = "",
                 status: str = "pendiente", priority: str = "media",
                 deadline: Optional[str] = None, tags: List[str] = None) -> int:
        """Add a new task"""
        task_id = db.add_task(title, category, description, status, priority, deadline, tags=tags)
        
        try:
            self.obsidian.add_task(title, category, status, deadline, priority)
        except Exception:
            pass
        
        task = db.get_task(task_id)
        if task:
            signals.task_added.emit(task)
            signals.stats_updated.emit()
        
        return task_id
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        """Update an existing task"""
        task = db.get_task(task_id)
        if not task:
            return False
        
        old_status = task.get('status')
        success = db.update_task(task_id, **kwargs)
        
        if success:
            try:
                self.obsidian.update_task(task['title'], task['category'], **kwargs)
            except Exception:
                pass
            
            new_status = kwargs.get('status')
            if new_status == 'completado' and old_status != 'completado':
                db.increment_tasks_completed()
            
            updated_task = db.get_task(task_id)
            signals.task_updated.emit(task_id, updated_task or {})
            signals.stats_updated.emit()
        
        return success
    
    def update_task_position(self, task_id: int, new_position: int, 
                            new_status: Optional[str] = None) -> bool:
        """Update task position for drag and drop"""
        task = db.get_task(task_id)
        if not task:
            return False
        
        old_status = task.get('status')
        success = db.update_task_position(task_id, new_position, new_status)
        
        if success:
            if new_status and new_status == 'completado' and old_status != 'completado':
                db.increment_tasks_completed()
            
            updated_task = db.get_task(task_id)
            signals.task_updated.emit(task_id, updated_task or {})
            signals.stats_updated.emit()
        
        return success
    
    def reorder_tasks(self, status: str, task_ids: List[int]) -> bool:
        """Reorder tasks within a status column"""
        success = db.reorder_tasks_in_status(status, task_ids)
        if success:
            signals.tasks_reloaded.emit()
        return success
    
    def move_task_to_date(self, task_id: int, new_deadline: str) -> bool:
        """Move task to a different date"""
        success = db.move_task_to_date(task_id, new_deadline)
        if success:
            task = db.get_task(task_id)
            signals.task_updated.emit(task_id, task or {})
        return success
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        task = db.get_task(task_id)
        if not task:
            return False
        
        db.delete_task_reminders(task_id)
        success = db.delete_task(task_id)
        
        if success:
            try:
                self.obsidian.delete_task(task['title'], task['category'])
            except Exception:
                pass
            
            signals.task_deleted.emit(task_id)
            signals.stats_updated.emit()
        
        return success
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        """Get a single task"""
        return db.get_task(task_id)
    
    def get_all_tasks(self, category: Optional[str] = None, 
                      status: Optional[str] = None) -> List[Dict]:
        """Get all tasks with optional filters"""
        return db.get_all_tasks(category, status)
    
    def get_tasks_by_deadline(self, deadline: str) -> List[Dict]:
        """Get tasks for a specific deadline"""
        return db.get_tasks_by_deadline(deadline)
    
    def get_tasks_with_deadlines(self) -> List[Dict]:
        """Get all tasks with deadlines"""
        return db.get_tasks_with_deadlines()
    
    def get_today_tasks(self) -> List[Dict]:
        """Get today's tasks"""
        return db.get_today_tasks()
    
    def get_tomorrow_tasks(self) -> List[Dict]:
        """Get tomorrow's tasks"""
        return db.get_tomorrow_tasks()
    
    def get_overdue_tasks(self) -> List[Dict]:
        """Get overdue tasks"""
        today = datetime.now().strftime("%Y-%m-%d")
        all_deadline_tasks = db.get_tasks_with_deadlines()
        return [t for t in all_deadline_tasks if t['deadline'] < today]
    
    def get_in_progress_tasks(self) -> List[Dict]:
        """Get tasks that are in progress"""
        return db.get_all_tasks(status='en_progreso')
    
    def get_pending_tasks(self) -> List[Dict]:
        """Get pending tasks"""
        return db.get_all_tasks(status='pendiente')
    
    def get_completed_tasks(self) -> List[Dict]:
        """Get completed tasks"""
        return db.get_all_tasks(status='completado')
    
    def get_upcoming_deadlines(self, days: int = 7) -> List[Dict]:
        """Get tasks with deadlines in the next N days"""
        return self.get_upcoming_tasks(days)
    
    def get_upcoming_tasks(self, days: int = 7) -> List[Dict]:
        """Get tasks due in the next N days"""
        today = datetime.now()
        future = today + timedelta(days=days)
        today_str = today.strftime("%Y-%m-%d")
        future_str = future.strftime("%Y-%m-%d")
        
        all_deadline_tasks = db.get_tasks_with_deadlines()
        return [t for t in all_deadline_tasks if today_str <= t['deadline'] <= future_str]
    
    def search_tasks(self, query: str) -> List[Dict]:
        """Search tasks by title or description"""
        return db.search_tasks(query)
    
    # Quick Notes
    def add_quick_note(self, title: str, content: str = "") -> int:
        """Add a quick note"""
        try:
            file_path = self.obsidian.save_quick_note(title, content)
        except Exception:
            file_path = None
        
        note_id = db.add_quick_note(title, content, file_path)
        note = db.get_quick_note(note_id)
        if note:
            signals.note_added.emit(note)
        return note_id
    
    def update_quick_note(self, note_id: int, **kwargs) -> bool:
        """Update a quick note"""
        success = db.update_quick_note(note_id, **kwargs)
        if success:
            signals.note_updated.emit(note_id)
        return success
    
    def delete_quick_note(self, note_id: int) -> bool:
        """Delete a quick note"""
        success = db.delete_quick_note(note_id)
        if success:
            signals.note_deleted.emit(note_id)
        return success
    
    def get_all_quick_notes(self) -> List[Dict]:
        """Get all quick notes"""
        return db.get_all_quick_notes()
    
    # Pomodoro
    def start_pomodoro(self, task_id: Optional[int] = None, duration: int = 25) -> int:
        """Start a pomodoro session"""
        session_id = db.start_pomodoro(task_id, duration)
        signals.pomodoro_started.emit(session_id)
        return session_id
    
    def complete_pomodoro(self, session_id: int) -> bool:
        """Complete a pomodoro session"""
        success = db.complete_pomodoro(session_id)
        if success:
            signals.pomodoro_completed.emit(session_id)
            signals.stats_updated.emit()
        return success
    
    def get_today_pomodoros(self) -> List[Dict]:
        """Get today's pomodoro sessions"""
        return db.get_today_pomodoros()
    
    # Statistics
    def get_weekly_stats(self) -> Dict:
        """Get weekly statistics"""
        return db.get_weekly_stats()
    
    def get_monthly_stats(self) -> Dict:
        """Get monthly statistics"""
        return db.get_monthly_stats()
    
    def get_daily_stats(self, date: str) -> Dict:
        """Get daily statistics"""
        return db.get_daily_stats(date)
    
    # Schedule
    def add_schedule_event(self, title: str, day_of_week: int, start_time: str, 
                          end_time: str, color: str = "66, 133, 244") -> int:
        """Add a schedule event"""
        event_id = db.add_schedule_event(title, day_of_week, start_time, end_time, color)
        signals.schedule_updated.emit()
        return event_id
    
    def update_schedule_event(self, event_id: int, **kwargs) -> bool:
        """Update a schedule event"""
        success = db.update_schedule_event(event_id, **kwargs)
        if success:
            signals.schedule_updated.emit()
        return success
    
    def get_schedule_events(self, day_of_week: Optional[int] = None) -> List[Dict]:
        """Get schedule events"""
        return db.get_schedule_events(day_of_week)
    
    def delete_schedule_event(self, event_id: int) -> bool:
        """Delete a schedule event"""
        success = db.delete_schedule_event(event_id)
        if success:
            signals.schedule_updated.emit()
        return success
    
    # Reminders
    def add_reminder(self, task_id: int, remind_at: str, message: str = "") -> int:
        """Add a reminder for a task"""
        return db.add_reminder(task_id, remind_at, message)
    
    def get_task_reminders(self, task_id: int) -> List[Dict]:
        """Get reminders for a task"""
        return db.get_task_reminders(task_id)
    
    def delete_reminder(self, reminder_id: int) -> bool:
        """Delete a reminder"""
        return db.delete_reminder(reminder_id)
    
    # Export/Import
    def export_to_json(self, filepath: Optional[str] = None) -> str:
        """Export all data to JSON"""
        return db.export_to_json(filepath)
    
    def export_tasks_to_csv(self, filepath: Optional[str] = None) -> str:
        """Export tasks to CSV"""
        return db.export_tasks_to_csv(filepath)
    
    def import_from_json(self, filepath: str) -> Dict[str, int]:
        """Import data from JSON"""
        counts = db.import_from_json(filepath)
        signals.tasks_reloaded.emit()
        signals.notes_reloaded.emit()
        signals.schedule_updated.emit()
        return counts
    
    # Backup
    def create_backup(self, backup_type: str = "manual") -> str:
        """Create a database backup"""
        backup_path = db.create_backup(backup_type)
        signals.backup_completed.emit(backup_path)
        return backup_path
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """Restore from a backup"""
        success = db.restore_from_backup(backup_path)
        if success:
            signals.tasks_reloaded.emit()
            signals.notes_reloaded.emit()
            signals.schedule_updated.emit()
            signals.stats_updated.emit()
        return success
    
    def get_backup_list(self) -> List[Dict]:
        """Get list of available backups"""
        return db.get_backup_list()
    
    # Settings
    def get_setting(self, key: str, default=None):
        """Get a setting value"""
        return db.get_setting(key, default)
    
    def set_setting(self, key: str, value):
        """Set a setting value"""
        db.set_setting(key, value)
        signals.settings_changed.emit(key, value)
    
    def get_all_settings(self) -> Dict:
        """Get all settings"""
        return db.get_all_settings()


task_manager = TaskManager.get_instance()
