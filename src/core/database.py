"""
Database module for persistent storage using SQLite
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


class Database:
    """SQLite database manager for UnixProductivityApp"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.db_dir = Path.home() / ".local" / "share" / "UnixProductivityApp"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.db_dir / "data.db"
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Create all necessary tables"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                category TEXT NOT NULL,
                status TEXT DEFAULT 'pendiente',
                priority TEXT DEFAULT 'media',
                deadline TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                obsidian_synced INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quick_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                duration_minutes INTEGER DEFAULT 25,
                completed INTEGER DEFAULT 0,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                ended_at TEXT,
                session_type TEXT DEFAULT 'work',
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                tasks_completed INTEGER DEFAULT 0,
                pomodoros_completed INTEGER DEFAULT 0,
                total_focus_minutes INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                day_of_week INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                color TEXT DEFAULT '66, 133, 244',
                recurring INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    def add_task(self, title: str, category: str, description: str = "",
                 status: str = "pendiente", priority: str = "media",
                 deadline: Optional[str] = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (title, description, category, status, priority, deadline)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, description, category, status, priority, deadline))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        kwargs['updated_at'] = datetime.now().isoformat()
        if kwargs.get('status') == 'completado':
            kwargs['completed_at'] = datetime.now().isoformat()
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [task_id]
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_task(self, task_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_tasks(self, category: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY priority DESC, deadline ASC, created_at DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_tasks_by_deadline(self, deadline: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE deadline = ? AND status != 'completado'", (deadline,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_tasks_with_deadlines(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE deadline IS NOT NULL AND status != 'completado'")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_today_tasks(self) -> List[Dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.get_tasks_by_deadline(today)
    
    def get_tomorrow_tasks(self) -> List[Dict]:
        from datetime import timedelta
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        return self.get_tasks_by_deadline(tomorrow)
    
    def search_tasks(self, query: str) -> List[Dict]:
        cursor = self.conn.cursor()
        search_pattern = f"%{query}%"
        cursor.execute("""
            SELECT * FROM tasks WHERE title LIKE ? OR description LIKE ?
            ORDER BY created_at DESC
        """, (search_pattern, search_pattern))
        return [dict(row) for row in cursor.fetchall()]
    
    def add_quick_note(self, title: str, content: str = "", file_path: Optional[str] = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO quick_notes (title, content, file_path) VALUES (?, ?, ?)",
                      (title, content, file_path))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_quick_note(self, note_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        kwargs['updated_at'] = datetime.now().isoformat()
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [note_id]
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE quick_notes SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_quick_note(self, note_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM quick_notes WHERE id = ?", (note_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_all_quick_notes(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM quick_notes ORDER BY updated_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def start_pomodoro(self, task_id: Optional[int] = None, duration: int = 25, session_type: str = "work") -> int:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO pomodoro_sessions (task_id, duration_minutes, session_type) VALUES (?, ?, ?)",
                      (task_id, duration, session_type))
        self.conn.commit()
        return cursor.lastrowid
    
    def complete_pomodoro(self, session_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE pomodoro_sessions SET completed = 1, ended_at = ? WHERE id = ?",
                      (datetime.now().isoformat(), session_id))
        self.conn.commit()
        self._update_daily_stats_pomodoro()
        return cursor.rowcount > 0
    
    def get_today_pomodoros(self) -> List[Dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM pomodoro_sessions WHERE date(started_at) = ? AND completed = 1", (today,))
        return [dict(row) for row in cursor.fetchall()]
    
    def _update_daily_stats_pomodoro(self):
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO statistics (date, pomodoros_completed, total_focus_minutes) VALUES (?, 1, 25)
            ON CONFLICT(date) DO UPDATE SET pomodoros_completed = pomodoros_completed + 1, total_focus_minutes = total_focus_minutes + 25
        """, (today,))
        self.conn.commit()
    
    def increment_tasks_completed(self):
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO statistics (date, tasks_completed) VALUES (?, 1)
            ON CONFLICT(date) DO UPDATE SET tasks_completed = tasks_completed + 1
        """, (today,))
        self.conn.commit()
    
    def get_weekly_stats(self) -> Dict:
        from datetime import timedelta
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(tasks_completed), 0) as tasks,
                   COALESCE(SUM(pomodoros_completed), 0) as pomodoros,
                   COALESCE(SUM(total_focus_minutes), 0) as focus_minutes
            FROM statistics WHERE date >= ?
        """, (week_start.strftime("%Y-%m-%d"),))
        row = cursor.fetchone()
        return {'tasks_completed': row['tasks'], 'pomodoros_completed': row['pomodoros'], 'total_focus_minutes': row['focus_minutes']}
    
    def get_monthly_stats(self) -> Dict:
        today = datetime.now()
        month_start = today.replace(day=1)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(tasks_completed), 0) as tasks,
                   COALESCE(SUM(pomodoros_completed), 0) as pomodoros,
                   COALESCE(SUM(total_focus_minutes), 0) as focus_minutes
            FROM statistics WHERE date >= ?
        """, (month_start.strftime("%Y-%m-%d"),))
        row = cursor.fetchone()
        return {'tasks_completed': row['tasks'], 'pomodoros_completed': row['pomodoros'], 'total_focus_minutes': row['focus_minutes']}
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row['value'])
            except json.JSONDecodeError:
                return row['value']
        return default
    
    def set_setting(self, key: str, value: Any):
        cursor = self.conn.cursor()
        value_str = json.dumps(value) if not isinstance(value, str) else value
        cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?",
                      (key, value_str, value_str))
        self.conn.commit()
    
    def add_schedule_event(self, title: str, day_of_week: int, start_time: str, end_time: str, color: str = "66, 133, 244") -> int:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO schedule_events (title, day_of_week, start_time, end_time, color) VALUES (?, ?, ?, ?, ?)",
                      (title, day_of_week, start_time, end_time, color))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_schedule_events(self, day_of_week: Optional[int] = None) -> List[Dict]:
        cursor = self.conn.cursor()
        if day_of_week is not None:
            cursor.execute("SELECT * FROM schedule_events WHERE day_of_week = ?", (day_of_week,))
        else:
            cursor.execute("SELECT * FROM schedule_events")
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_schedule_event(self, event_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM schedule_events WHERE id = ?", (event_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def close(self):
        if self.conn:
            self.conn.close()


# Create singleton instance lazily
db = Database.get_instance()
