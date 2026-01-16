"""
Task Manager - Central task management with database and Obsidian sync
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from .database import db
from .obsidian_sync import ObsidianSync


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
        obsidian_tasks = self.obsidian.read_all_tasks()
        
        for task in obsidian_tasks:
            # Check if task already exists in DB
            existing = db.search_tasks(task['title'])
            matching = [t for t in existing if t['category'] == task['category']]
            
            if not matching:
                # Add to database
                db.add_task(
                    title=task['title'],
                    category=task['category'],
                    description=task.get('description', ''),
                    status=task.get('status', 'pendiente'),
                    priority=task.get('priority', 'media'),
                    deadline=task.get('deadline')
                )
    
    def add_task(self, title: str, category: str, description: str = "",
                 status: str = "pendiente", priority: str = "media",
                 deadline: Optional[str] = None) -> int:
        """Add a new task"""
        task_id = db.add_task(title, category, description, status, priority, deadline)
        self.obsidian.add_task(title, category, status, deadline, priority)
        return task_id
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        """Update an existing task"""
        task = db.get_task(task_id)
        if not task:
            return False
        
        success = db.update_task(task_id, **kwargs)
        if success:
            self.obsidian.update_task(task['title'], task['category'], **kwargs)
            if kwargs.get('status') == 'completado':
                db.increment_tasks_completed()
        return success
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        task = db.get_task(task_id)
        if not task:
            return False
        
        success = db.delete_task(task_id)
        if success:
            self.obsidian.delete_task(task['title'], task['category'])
        return success
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        """Get a single task"""
        return db.get_task(task_id)
    
    def get_all_tasks(self, category: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
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
    
    def add_quick_note(self, title: str, content: str = "") -> int:
        """Add a quick note"""
        file_path = self.obsidian.save_quick_note(title, content)
        return db.add_quick_note(title, content, file_path)
    
    def get_all_quick_notes(self) -> List[Dict]:
        """Get all quick notes"""
        return db.get_all_quick_notes()
    
    def start_pomodoro(self, task_id: Optional[int] = None, duration: int = 25) -> int:
        """Start a pomodoro session"""
        return db.start_pomodoro(task_id, duration)
    
    def complete_pomodoro(self, session_id: int) -> bool:
        """Complete a pomodoro session"""
        return db.complete_pomodoro(session_id)
    
    def get_today_pomodoros(self) -> List[Dict]:
        """Get today's pomodoro sessions"""
        return db.get_today_pomodoros()
    
    def get_weekly_stats(self) -> Dict:
        """Get weekly statistics"""
        return db.get_weekly_stats()
    
    def get_monthly_stats(self) -> Dict:
        """Get monthly statistics"""
        return db.get_monthly_stats()
    
    def add_schedule_event(self, title: str, day_of_week: int, start_time: str, 
                          end_time: str, color: str = "66, 133, 244") -> int:
        """Add a schedule event"""
        return db.add_schedule_event(title, day_of_week, start_time, end_time, color)
    
    def get_schedule_events(self, day_of_week: Optional[int] = None) -> List[Dict]:
        """Get schedule events"""
        return db.get_schedule_events(day_of_week)
    
    def delete_schedule_event(self, event_id: int) -> bool:
        """Delete a schedule event"""
        return db.delete_schedule_event(event_id)


# Lazy singleton
task_manager = TaskManager.get_instance()
