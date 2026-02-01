"""
Notification Manager - Desktop notifications and scheduled reminders
Uses GLib for timers to remain compatible with GTK
"""
import subprocess
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pathlib import Path

from gi.repository import GLib

from .database import db
from .signals import signals


class NotificationManager:
    """Handles desktop notifications and scheduled reminders"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.app_name = "UniDex"
        self.check_interval_ms = 60000  # Check every minute
        self.backup_interval_ms = 6 * 60 * 60 * 1000  # 6 hours
        
        self.reminder_timer_id = None
        self.backup_timer_id = None
    
    def start(self):
        """Start the notification manager timers"""
        # Start GLib timers
        self.reminder_timer_id = GLib.timeout_add(self.check_interval_ms, self._check_reminders_timer)
        self.backup_timer_id = GLib.timeout_add(self.backup_interval_ms, self._auto_backup_timer)
        
        # Check reminders immediately on start
        self._check_reminders()
        
        # Check for deadline notifications
        self._check_deadlines()
    
    def stop(self):
        """Stop the notification manager timers"""
        if self.reminder_timer_id:
            GLib.source_remove(self.reminder_timer_id)
        if self.backup_timer_id:
            GLib.source_remove(self.backup_timer_id)

    def _check_reminders_timer(self):
        self._check_reminders()
        return True # Continue timer
        
    def _auto_backup_timer(self):
        self._auto_backup()
        return True # Continue timer
    
    def send_notification(self, title: str, message: str, urgency: str = "normal",
                          icon: Optional[str] = None):
        """Send a desktop notification using notify-send"""
        cmd = [
            "notify-send",
            "-u", urgency,
            "-a", self.app_name,
            title,
            message
        ]
        
        if icon:
            cmd.extend(["-i", icon])
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            signals.notification_triggered.emit(title, message, urgency)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    def _check_reminders(self):
        """Check for pending reminders and trigger notifications"""
        pending = db.get_pending_reminders()
        
        for reminder in pending:
            task_title = reminder.get('task_title', 'Tarea')
            message = reminder.get('message') or f"Recordatorio para: {task_title}"
            
            self.send_notification(
                "Recordatorio",
                message,
                "normal"
            )
            
            # Mark as triggered
            db.mark_reminder_triggered(reminder['id'])
            signals.reminder_due.emit(reminder)
    
    def _check_deadlines(self):
        """Check for tasks with upcoming deadlines"""
        tasks = db.get_tasks_with_deadlines()
        today = datetime.now().date()
        
        notified_today = db.get_setting('notified_deadlines_today', [])
        current_date = today.strftime("%Y-%m-%d")
        
        # Reset notifications if it's a new day
        if db.get_setting('last_notification_date') != current_date:
            notified_today = []
            db.set_setting('last_notification_date', current_date)
        
        for task in tasks:
            if task['id'] in notified_today:
                continue

            try:
                # Handle both YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS formats
                deadline_str = task['deadline'][:10]  # Extract just YYYY-MM-DD
                deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
                days_until = (deadline - today).days

                if days_until <= 3:
                    self._notify_task_deadline(task, days_until)
                    notified_today.append(task['id'])
            except ValueError:
                pass
        
        db.set_setting('notified_deadlines_today', notified_today)
    
    def _notify_task_deadline(self, task: Dict, days_until: int):
        """Send notification for upcoming task deadline"""
        task_title = task['title']
        
        if days_until < 0:
            urgency = "critical"
            message = f"La tarea '{task_title}' esta VENCIDA"
        elif days_until == 0:
            urgency = "critical"
            message = f"La tarea '{task_title}' vence HOY"
        elif days_until == 1:
            urgency = "critical"
            message = f"La tarea '{task_title}' vence MANANA"
        elif days_until <= 3:
            urgency = "normal"
            message = f"La tarea '{task_title}' vence en {days_until} dias"
        else:
            urgency = "low"
            message = f"La tarea '{task_title}' vence el {task['deadline']}"
        
        self.send_notification("Deadline de tarea", message, urgency)
    
    def notify_pomodoro_complete(self, session_type: str = "work"):
        """Send notification when pomodoro is complete"""
        if session_type == "work":
            title = "Pomodoro completado"
            message = "Buen trabajo. Toma un descanso de 5 minutos."
        elif session_type == "short_break":
            title = "Descanso terminado"
            message = "Hora de volver al trabajo."
        else:
            title = "Descanso largo terminado"
            message = "Hora de empezar un nuevo ciclo de pomodoros."
        
        self.send_notification(title, message, "normal")
    
    def notify_task_completed(self, task_title: str):
        """Send notification when task is completed"""
        self.send_notification(
            "Tarea completada",
            f"Has completado '{task_title}'",
            "normal"
        )
    
    def notify_backup_completed(self, backup_path: str):
        """Send notification when backup is completed"""
        self.send_notification(
            "Backup completado",
            f"Base de datos respaldada exitosamente",
            "low"
        )
    
    def _auto_backup(self):
        """Perform automatic backup"""
        try:
            backup_path = db.create_backup(backup_type="auto")
            signals.backup_completed.emit(backup_path)
        except Exception:
            pass
    
    def schedule_reminder(self, task_id: int, remind_at: datetime, message: str = "") -> int:
        """Schedule a reminder for a task"""
        remind_at_str = remind_at.isoformat()
        return db.add_reminder(task_id, remind_at_str, message)
    
    def schedule_deadline_reminders(self, task_id: int, deadline: str):
        """Automatically schedule reminders for a task deadline"""
        try:
            # Handle both YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS formats
            deadline_str = deadline[:10]  # Extract just YYYY-MM-DD
            deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d")
            
            # Clear existing reminders for this task
            db.delete_task_reminders(task_id)
            
            task = db.get_task(task_id)
            task_title = task['title'] if task else "Tarea"
            
            # 3 days before at 9:00 AM
            remind_3d = deadline_date - timedelta(days=3)
            remind_3d = remind_3d.replace(hour=9, minute=0, second=0)
            if remind_3d > datetime.now():
                db.add_reminder(task_id, remind_3d.isoformat(), 
                               f"'{task_title}' vence en 3 dias")
            
            # 1 day before at 9:00 AM
            remind_1d = deadline_date - timedelta(days=1)
            remind_1d = remind_1d.replace(hour=9, minute=0, second=0)
            if remind_1d > datetime.now():
                db.add_reminder(task_id, remind_1d.isoformat(), 
                               f"'{task_title}' vence manana")
            
            # Same day at 8:00 AM
            remind_same = deadline_date.replace(hour=8, minute=0, second=0)
            if remind_same > datetime.now():
                db.add_reminder(task_id, remind_same.isoformat(), 
                               f"'{task_title}' vence HOY")
        except ValueError:
            pass
    
    def get_scheduled_reminders(self, task_id: int) -> List[Dict]:
        """Get all scheduled reminders for a task"""
        return db.get_task_reminders(task_id)
    
    def cancel_reminder(self, reminder_id: int) -> bool:
        """Cancel a scheduled reminder"""
        return db.delete_reminder(reminder_id)


notification_manager = NotificationManager.get_instance()
