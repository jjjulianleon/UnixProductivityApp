"""
Notification Manager - Desktop notifications using notify-send
"""
import subprocess
from datetime import datetime, timedelta
from typing import Optional


class NotificationManager:
    """Handles desktop notifications"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.app_name = "UnixProductivityApp"
    
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
        except subprocess.CalledProcessError:
            pass  # Silently fail if notify-send is not available
        except FileNotFoundError:
            pass  # notify-send not installed
    
    def notify_task_deadline(self, task_title: str, deadline: str, days_until: int):
        """Send notification for upcoming task deadline"""
        if days_until == 0:
            urgency = "critical"
            message = f"¡La tarea '{task_title}' vence HOY!"
        elif days_until == 1:
            urgency = "critical"
            message = f"La tarea '{task_title}' vence MAÑANA"
        elif days_until <= 3:
            urgency = "normal"
            message = f"La tarea '{task_title}' vence en {days_until} días ({deadline})"
        else:
            urgency = "low"
            message = f"La tarea '{task_title}' vence el {deadline}"
        
        self.send_notification("📅 Recordatorio de tarea", message, urgency)
    
    def notify_pomodoro_complete(self, session_type: str = "work"):
        """Send notification when pomodoro is complete"""
        if session_type == "work":
            title = "🍅 ¡Pomodoro completado!"
            message = "Buen trabajo. Toma un descanso de 5 minutos."
        elif session_type == "short_break":
            title = "☕ Descanso terminado"
            message = "Hora de volver al trabajo."
        else:
            title = "🎉 ¡Descanso largo terminado!"
            message = "Hora de empezar un nuevo ciclo de pomodoros."
        
        self.send_notification(title, message, "normal")
    
    def notify_task_completed(self, task_title: str):
        """Send notification when task is completed"""
        self.send_notification(
            "✅ Tarea completada",
            f"¡Felicidades! Has completado '{task_title}'",
            "normal"
        )
    
    def check_upcoming_deadlines(self, tasks: list):
        """Check for tasks with upcoming deadlines and send notifications"""
        today = datetime.now().date()
        
        for task in tasks:
            if task.get('deadline') and task.get('status') != 'completado':
                try:
                    deadline = datetime.strptime(task['deadline'], "%Y-%m-%d").date()
                    days_until = (deadline - today).days
                    
                    # Notify for tasks due within 3 days
                    if 0 <= days_until <= 3:
                        self.notify_task_deadline(task['title'], task['deadline'], days_until)
                except ValueError:
                    pass  # Invalid date format


# Create singleton instance
notification_manager = NotificationManager.get_instance()
