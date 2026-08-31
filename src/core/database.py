"""
Database module for persistent storage using SQLite
With export/import and backup functionality
"""
import sqlite3
import json
import csv
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..utils.system import data_dir


class Database:
    """SQLite database manager for UniDex"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self, db_path=None):
        """db_path solo se usa en tests (":memory:"); en la app va la de siempre."""
        self.db_dir = data_dir("UniDex")
        self.db_path = db_path or self.db_dir / "data.db"
        self.backup_dir = self.db_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._run_migrations()
    
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
                position INTEGER DEFAULT 0,
                tags TEXT DEFAULT '[]',
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
                event_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                remind_at TEXT NOT NULL,
                message TEXT,
                triggered INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backup_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_path TEXT NOT NULL,
                backup_type TEXT DEFAULT 'manual',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    def _run_migrations(self):
        """Run any necessary database migrations"""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'position' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN position INTEGER DEFAULT 0")
        if 'tags' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN tags TEXT DEFAULT '[]'")

        # Migration for schedule_events table
        cursor.execute("PRAGMA table_info(schedule_events)")
        schedule_columns = [col[1] for col in cursor.fetchall()]

        if 'event_date' not in schedule_columns:
            cursor.execute("ALTER TABLE schedule_events ADD COLUMN event_date TEXT")

        self.conn.commit()
    
    def add_task(self, title: str, category: str, description: str = "",
                 status: str = "pendiente", priority: str = "media",
                 deadline: Optional[str] = None, position: int = 0,
                 tags: List[str] = None) -> int:
        cursor = self.conn.cursor()
        tags_json = json.dumps(tags or [])
        cursor.execute("""
            INSERT INTO tasks (title, description, category, status, priority, deadline, position, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, description, category, status, priority, deadline, position, tags_json))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        kwargs['updated_at'] = datetime.now().isoformat()
        if kwargs.get('status') == 'completado':
            kwargs['completed_at'] = datetime.now().isoformat()
        if 'tags' in kwargs and isinstance(kwargs['tags'], list):
            kwargs['tags'] = json.dumps(kwargs['tags'])
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [task_id]
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def update_task_position(self, task_id: int, new_position: int, new_status: Optional[str] = None) -> bool:
        cursor = self.conn.cursor()
        if new_status:
            cursor.execute(
                "UPDATE tasks SET position = ?, status = ?, updated_at = ? WHERE id = ?",
                (new_position, new_status, datetime.now().isoformat(), task_id)
            )
        else:
            cursor.execute(
                "UPDATE tasks SET position = ?, updated_at = ? WHERE id = ?",
                (new_position, datetime.now().isoformat(), task_id)
            )
        self.conn.commit()
        return cursor.rowcount > 0
    
    def reorder_tasks_in_status(self, status: str, task_ids: List[int]) -> bool:
        cursor = self.conn.cursor()
        for position, task_id in enumerate(task_ids):
            cursor.execute(
                "UPDATE tasks SET position = ? WHERE id = ? AND status = ?",
                (position, task_id, status)
            )
        self.conn.commit()
        return True
    
    def delete_task(self, task_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if row:
            task = dict(row)
            task['tags'] = json.loads(task.get('tags', '[]'))
            return task
        return None
    
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
        query += " ORDER BY position ASC, priority DESC, deadline ASC, created_at DESC"
        cursor.execute(query, params)
        tasks = []
        for row in cursor.fetchall():
            task = dict(row)
            task['tags'] = json.loads(task.get('tags', '[]'))
            tasks.append(task)
        return tasks
    
    def get_tasks_by_deadline(self, deadline: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM tasks WHERE deadline = ? AND status != 'completado' ORDER BY position ASC",
            (deadline,)
        )
        tasks = []
        for row in cursor.fetchall():
            task = dict(row)
            task['tags'] = json.loads(task.get('tags', '[]'))
            tasks.append(task)
        return tasks
    
    def get_tasks_with_deadlines(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM tasks WHERE deadline IS NOT NULL AND status != 'completado' ORDER BY deadline ASC"
        )
        tasks = []
        for row in cursor.fetchall():
            task = dict(row)
            task['tags'] = json.loads(task.get('tags', '[]'))
            tasks.append(task)
        return tasks
    
    def get_today_tasks(self) -> List[Dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.get_tasks_by_deadline(today)
    
    def get_tomorrow_tasks(self) -> List[Dict]:
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        return self.get_tasks_by_deadline(tomorrow)
    
    def search_tasks(self, query: str) -> List[Dict]:
        cursor = self.conn.cursor()
        search_pattern = f"%{query}%"
        cursor.execute("""
            SELECT * FROM tasks WHERE title LIKE ? OR description LIKE ?
            ORDER BY created_at DESC
        """, (search_pattern, search_pattern))
        tasks = []
        for row in cursor.fetchall():
            task = dict(row)
            task['tags'] = json.loads(task.get('tags', '[]'))
            tasks.append(task)
        return tasks
    
    def move_task_to_date(self, task_id: int, new_deadline: str) -> bool:
        return self.update_task(task_id, deadline=new_deadline)
    
    def add_quick_note(self, title: str, content: str = "", file_path: Optional[str] = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO quick_notes (title, content, file_path) VALUES (?, ?, ?)",
            (title, content, file_path)
        )
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
    
    def get_quick_note(self, note_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM quick_notes WHERE id = ?", (note_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_quick_notes(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM quick_notes ORDER BY updated_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def start_pomodoro(self, task_id: Optional[int] = None, duration: int = 25, 
                       session_type: str = "work") -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO pomodoro_sessions (task_id, duration_minutes, session_type) VALUES (?, ?, ?)",
            (task_id, duration, session_type)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def complete_pomodoro(self, session_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE pomodoro_sessions SET completed = 1, ended_at = ? WHERE id = ?",
            (datetime.now().isoformat(), session_id)
        )
        self.conn.commit()
        self._update_daily_stats_pomodoro()
        return cursor.rowcount > 0
    
    def get_today_pomodoros(self) -> List[Dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        # started_at lo pone CURRENT_TIMESTAMP, que SQLite guarda en UTC, y today
        # es local: sin 'localtime' los pomodoros de la tarde/noche (UTC-5 en
        # adelante) contaban como del dia siguiente y desaparecian de "hoy".
        cursor.execute(
            "SELECT * FROM pomodoro_sessions "
            "WHERE date(started_at, 'localtime') = ? AND completed = 1",
            (today,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def _update_daily_stats_pomodoro(self):
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO statistics (date, pomodoros_completed, total_focus_minutes) VALUES (?, 1, 25)
            ON CONFLICT(date) DO UPDATE SET 
                pomodoros_completed = pomodoros_completed + 1, 
                total_focus_minutes = total_focus_minutes + 25
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
    
    def get_daily_stats(self, date: str) -> Dict:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM statistics WHERE date = ?", (date,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {'tasks_completed': 0, 'pomodoros_completed': 0, 'total_focus_minutes': 0}
    
    def _stats_since(self, since: str) -> Dict:
        """Suma de la tabla statistics desde una fecha (inclusive)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(tasks_completed), 0) as tasks,
                   COALESCE(SUM(pomodoros_completed), 0) as pomodoros,
                   COALESCE(SUM(total_focus_minutes), 0) as focus_minutes
            FROM statistics WHERE date >= ?
        """, (since,))
        row = cursor.fetchone()
        return {
            'tasks_completed': row['tasks'],
            'pomodoros_completed': row['pomodoros'],
            'total_focus_minutes': row['focus_minutes']
        }

    def get_weekly_stats(self) -> Dict:
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        return self._stats_since(week_start.strftime("%Y-%m-%d"))

    def get_monthly_stats(self) -> Dict:
        return self._stats_since(datetime.now().replace(day=1).strftime("%Y-%m-%d"))

    def get_alltime_stats(self) -> Dict:
        return self._stats_since("0001-01-01")

    def get_stats_range(self, start_date: str, end_date: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM statistics WHERE date >= ? AND date <= ? ORDER BY date ASC
        """, (start_date, end_date))
        return [dict(row) for row in cursor.fetchall()]
    
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
        cursor.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?",
            (key, value_str, value_str)
        )
        self.conn.commit()
    
    def get_all_settings(self) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        settings = {}
        for row in cursor.fetchall():
            try:
                settings[row['key']] = json.loads(row['value'])
            except json.JSONDecodeError:
                settings[row['key']] = row['value']
        return settings
    
    def add_schedule_event(self, title: str, day_of_week: int, start_time: str,
                          end_time: str, color: str = "66, 133, 244",
                          recurring: int = 1, event_date: Optional[str] = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO schedule_events (title, day_of_week, start_time, end_time, color, recurring, event_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, day_of_week, start_time, end_time, color, recurring, event_date)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def update_schedule_event(self, event_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [event_id]
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE schedule_events SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return cursor.rowcount > 0
    
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
    
    def add_reminder(self, task_id: int, remind_at: str, message: str = "") -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (task_id, remind_at, message) VALUES (?, ?, ?)",
            (task_id, remind_at, message)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_pending_reminders(self) -> List[Dict]:
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT r.*, t.title as task_title, t.deadline as task_deadline
            FROM reminders r
            LEFT JOIN tasks t ON r.task_id = t.id
            WHERE r.remind_at <= ? AND r.triggered = 0
            ORDER BY r.remind_at ASC
        """, (now,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_task_reminders(self, task_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM reminders WHERE task_id = ? ORDER BY remind_at ASC",
            (task_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def mark_reminder_triggered(self, reminder_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE reminders SET triggered = 1 WHERE id = ?", (reminder_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_reminder(self, reminder_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_task_reminders(self, task_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE task_id = ?", (task_id,))
        self.conn.commit()
        return True
    
    def export_to_json(self, filepath: Optional[str] = None) -> str:
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = str(self.db_dir / f"export_{timestamp}.json")
        
        data = {
            'exported_at': datetime.now().isoformat(),
            'version': '1.0',
            'tasks': self.get_all_tasks(),
            'quick_notes': self.get_all_quick_notes(),
            'schedule_events': self.get_schedule_events(),
            'settings': self.get_all_settings(),
            'statistics': self._get_all_statistics()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def export_tasks_to_csv(self, filepath: Optional[str] = None) -> str:
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = str(self.db_dir / f"tasks_{timestamp}.csv")
        
        tasks = self.get_all_tasks()
        if not tasks:
            return filepath
        
        fieldnames = ['id', 'title', 'description', 'category', 'status', 
                      'priority', 'deadline', 'tags', 'created_at', 'completed_at']
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for task in tasks:
                task['tags'] = ','.join(task.get('tags', []))
                writer.writerow(task)
        
        return filepath
    
    def import_from_json(self, filepath: str) -> Dict[str, int]:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        counts = {'tasks': 0, 'notes': 0, 'events': 0}
        
        for task in data.get('tasks', []):
            self.add_task(
                title=task['title'],
                category=task['category'],
                description=task.get('description', ''),
                status=task.get('status', 'pendiente'),
                priority=task.get('priority', 'media'),
                deadline=task.get('deadline'),
                tags=task.get('tags', [])
            )
            counts['tasks'] += 1
        
        for note in data.get('quick_notes', []):
            self.add_quick_note(
                title=note['title'],
                content=note.get('content', ''),
                file_path=note.get('file_path')
            )
            counts['notes'] += 1
        
        for event in data.get('schedule_events', []):
            self.add_schedule_event(
                title=event['title'],
                day_of_week=event['day_of_week'],
                start_time=event['start_time'],
                end_time=event['end_time'],
                color=event.get('color', '66, 133, 244')
            )
            counts['events'] += 1
        
        return counts
    
    def _get_all_statistics(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM statistics ORDER BY date DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def create_backup(self, backup_type: str = "manual") -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{backup_type}_{timestamp}.db"
        backup_path = self.backup_dir / backup_filename
        
        self.conn.close()
        shutil.copy2(self.db_path, backup_path)
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO backup_history (backup_path, backup_type) VALUES (?, ?)",
            (str(backup_path), backup_type)
        )
        self.conn.commit()
        
        self._cleanup_old_backups()
        
        return str(backup_path)
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT backup_path FROM backup_history 
            ORDER BY created_at DESC 
            LIMIT -1 OFFSET ?
        """, (keep_count,))
        
        old_backups = cursor.fetchall()
        for row in old_backups:
            backup_path = Path(row['backup_path'])
            if backup_path.exists():
                backup_path.unlink()
        
        cursor.execute("""
            DELETE FROM backup_history 
            WHERE id NOT IN (
                SELECT id FROM backup_history ORDER BY created_at DESC LIMIT ?
            )
        """, (keep_count,))
        self.conn.commit()
    
    def restore_from_backup(self, backup_path: str) -> bool:
        backup_file = Path(backup_path)
        if not backup_file.exists():
            return False
        
        self.create_backup(backup_type="pre_restore")
        self.conn.close()
        shutil.copy2(backup_file, self.db_path)
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        return True
    
    def get_backup_list(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM backup_history ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        if self.conn:
            self.conn.close()


db = Database.get_instance()
