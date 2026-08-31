"""
Tests for database operations
"""
import unittest
import tempfile
import shutil
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import Database
from src.utils.constants import SEMESTER_END


class TestDatabase(unittest.TestCase):
    """Test cases for Database class"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a fresh database instance for testing
        Database._instance = None
        self.db = Database.__new__(Database)
        self.db.db_dir = Path(self.temp_dir)
        self.db.db_path = self.db.db_dir / "test.db"
        self.db.backup_dir = self.db.db_dir / "backups"
        self.db.backup_dir.mkdir(parents=True, exist_ok=True)
        
        import sqlite3
        self.db.conn = sqlite3.connect(str(self.db.db_path), check_same_thread=False)
        self.db.conn.row_factory = sqlite3.Row
        self.db._create_tables()
    
    def tearDown(self):
        """Clean up test database"""
        self.db.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        Database._instance = None
    
    # ==================== TASK TESTS ====================
    
    def test_add_task(self):
        """Test adding a task"""
        task_id = self.db.add_task(
            title="Test Task",
            category="personal",
            description="Test description",
            priority="alta"
        )
        
        self.assertIsNotNone(task_id)
        self.assertGreater(task_id, 0)
        
        task = self.db.get_task(task_id)
        self.assertEqual(task['title'], "Test Task")
        self.assertEqual(task['category'], "personal")
        self.assertEqual(task['priority'], "alta")
        self.assertEqual(task['status'], "pendiente")
    
    def test_update_task(self):
        """Test updating a task"""
        task_id = self.db.add_task(title="Original", category="trabajo")
        
        success = self.db.update_task(task_id, title="Updated", priority="alta")
        self.assertTrue(success)
        
        task = self.db.get_task(task_id)
        self.assertEqual(task['title'], "Updated")
        self.assertEqual(task['priority'], "alta")
    
    def test_update_task_status_to_completed(self):
        """Test updating task status to completed sets completed_at"""
        task_id = self.db.add_task(title="Task", category="personal")
        
        self.db.update_task(task_id, status="completado")
        
        task = self.db.get_task(task_id)
        self.assertEqual(task['status'], "completado")
        self.assertIsNotNone(task['completed_at'])
    
    def test_delete_task(self):
        """Test deleting a task"""
        task_id = self.db.add_task(title="To Delete", category="personal")
        
        success = self.db.delete_task(task_id)
        self.assertTrue(success)
        
        task = self.db.get_task(task_id)
        self.assertIsNone(task)
    
    def test_get_all_tasks(self):
        """Test getting all tasks"""
        self.db.add_task(title="Task 1", category="personal")
        self.db.add_task(title="Task 2", category="trabajo")
        self.db.add_task(title="Task 3", category="personal")
        
        all_tasks = self.db.get_all_tasks()
        self.assertEqual(len(all_tasks), 3)
        
        personal_tasks = self.db.get_all_tasks(category="personal")
        self.assertEqual(len(personal_tasks), 2)
    
    def test_get_tasks_by_status(self):
        """Test filtering tasks by status"""
        self.db.add_task(title="Pending", category="personal", status="pendiente")
        self.db.add_task(title="In Progress", category="personal", status="en_progreso")
        self.db.add_task(title="Done", category="personal", status="completado")
        
        pending = self.db.get_all_tasks(status="pendiente")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]['title'], "Pending")
    
    def test_task_with_deadline(self):
        """Test tasks with deadlines"""
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        self.db.add_task(title="Today Task", category="personal", deadline=today)
        self.db.add_task(title="Tomorrow Task", category="personal", deadline=tomorrow)
        
        today_tasks = self.db.get_today_tasks()
        self.assertEqual(len(today_tasks), 1)
        self.assertEqual(today_tasks[0]['title'], "Today Task")
        
        tomorrow_tasks = self.db.get_tomorrow_tasks()
        self.assertEqual(len(tomorrow_tasks), 1)
    
    def test_search_tasks(self):
        """Test searching tasks"""
        self.db.add_task(title="Python project", category="trabajo")
        self.db.add_task(title="JavaScript project", category="trabajo")
        self.db.add_task(title="Meeting", category="personal")
        
        results = self.db.search_tasks("project")
        self.assertEqual(len(results), 2)
        
        results = self.db.search_tasks("Python")
        self.assertEqual(len(results), 1)
    
    def test_task_position(self):
        """Test task position for ordering"""
        id1 = self.db.add_task(title="Task 1", category="personal", position=2)
        id2 = self.db.add_task(title="Task 2", category="personal", position=1)
        id3 = self.db.add_task(title="Task 3", category="personal", position=0)
        
        tasks = self.db.get_all_tasks(category="personal")
        self.assertEqual(tasks[0]['title'], "Task 3")
        self.assertEqual(tasks[1]['title'], "Task 2")
        self.assertEqual(tasks[2]['title'], "Task 1")
    
    def test_reorder_tasks(self):
        """Test reordering tasks"""
        id1 = self.db.add_task(title="Task 1", category="personal", status="pendiente")
        id2 = self.db.add_task(title="Task 2", category="personal", status="pendiente")
        id3 = self.db.add_task(title="Task 3", category="personal", status="pendiente")
        
        self.db.reorder_tasks_in_status("pendiente", [id3, id1, id2])
        
        tasks = self.db.get_all_tasks(status="pendiente")
        self.assertEqual(tasks[0]['id'], id3)
        self.assertEqual(tasks[1]['id'], id1)
        self.assertEqual(tasks[2]['id'], id2)
    
    def test_task_tags(self):
        """Test task tags"""
        task_id = self.db.add_task(
            title="Tagged Task",
            category="personal",
            tags=["urgent", "review"]
        )
        
        task = self.db.get_task(task_id)
        self.assertIn("urgent", task['tags'])
        self.assertIn("review", task['tags'])
    
    # ==================== QUICK NOTES TESTS ====================
    
    def test_add_quick_note(self):
        """Test adding a quick note"""
        note_id = self.db.add_quick_note(
            title="Test Note",
            content="Note content"
        )
        
        self.assertIsNotNone(note_id)
        
        notes = self.db.get_all_quick_notes()
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]['title'], "Test Note")
    
    def test_update_quick_note(self):
        """Test updating a quick note"""
        note_id = self.db.add_quick_note(title="Original", content="Content")
        
        success = self.db.update_quick_note(note_id, title="Updated")
        self.assertTrue(success)
        
        note = self.db.get_quick_note(note_id)
        self.assertEqual(note['title'], "Updated")
    
    def test_delete_quick_note(self):
        """Test deleting a quick note"""
        note_id = self.db.add_quick_note(title="To Delete")
        
        success = self.db.delete_quick_note(note_id)
        self.assertTrue(success)
        
        notes = self.db.get_all_quick_notes()
        self.assertEqual(len(notes), 0)
    
    # ==================== POMODORO TESTS ====================
    
    def test_pomodoro_session(self):
        """Test pomodoro session lifecycle"""
        session_id = self.db.start_pomodoro(duration=25)
        self.assertIsNotNone(session_id)
        
        success = self.db.complete_pomodoro(session_id)
        self.assertTrue(success)
        
        today_pomodoros = self.db.get_today_pomodoros()
        self.assertEqual(len(today_pomodoros), 1)
    
    def test_pomodoro_with_task(self):
        """Test pomodoro linked to task"""
        task_id = self.db.add_task(title="Task", category="personal")
        session_id = self.db.start_pomodoro(task_id=task_id)
        
        self.db.complete_pomodoro(session_id)
        
        pomodoros = self.db.get_today_pomodoros()
        self.assertEqual(pomodoros[0]['task_id'], task_id)
    
    # ==================== STATISTICS TESTS ====================
    
    def test_statistics_update(self):
        """Test statistics are updated correctly"""
        self.db.start_pomodoro()
        session = self.db.start_pomodoro()
        self.db.complete_pomodoro(session)
        
        stats = self.db.get_weekly_stats()
        self.assertEqual(stats['pomodoros_completed'], 1)
        self.assertEqual(stats['total_focus_minutes'], 25)
    
    def test_increment_tasks_completed(self):
        """Test incrementing completed tasks counter"""
        self.db.increment_tasks_completed()
        self.db.increment_tasks_completed()
        
        stats = self.db.get_weekly_stats()
        self.assertEqual(stats['tasks_completed'], 2)
    
    # ==================== SETTINGS TESTS ====================
    
    def test_settings(self):
        """Test settings storage"""
        self.db.set_setting("theme", "dark")
        self.db.set_setting("pomodoro_duration", 30)
        self.db.set_setting("categories", ["work", "personal"])
        
        self.assertEqual(self.db.get_setting("theme"), "dark")
        self.assertEqual(self.db.get_setting("pomodoro_duration"), 30)
        self.assertEqual(self.db.get_setting("categories"), ["work", "personal"])
        self.assertIsNone(self.db.get_setting("nonexistent"))
        self.assertEqual(self.db.get_setting("nonexistent", "default"), "default")
    
    # ==================== SCHEDULE TESTS ====================
    
    def test_schedule_events(self):
        """Test schedule events"""
        event_id = self.db.add_schedule_event(
            title="Meeting",
            day_of_week=1,
            start_time="09:00",
            end_time="10:00",
            color="255, 0, 0"
        )
        
        self.assertIsNotNone(event_id)
        
        events = self.db.get_schedule_events(day_of_week=1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['title'], "Meeting")
        
        all_events = self.db.get_schedule_events()
        self.assertEqual(len(all_events), 1)
    
    def test_delete_schedule_event(self):
        """Test deleting schedule event"""
        event_id = self.db.add_schedule_event(
            title="Event",
            day_of_week=0,
            start_time="10:00",
            end_time="11:00"
        )
        
        success = self.db.delete_schedule_event(event_id)
        self.assertTrue(success)
        
        events = self.db.get_schedule_events()
        self.assertEqual(len(events), 0)
    
    # ==================== REMINDERS TESTS ====================
    
    def test_add_reminder(self):
        """Test adding a reminder"""
        task_id = self.db.add_task(title="Task", category="personal")
        remind_at = (datetime.now() + timedelta(hours=1)).isoformat()
        
        reminder_id = self.db.add_reminder(task_id, remind_at, "Test reminder")
        self.assertIsNotNone(reminder_id)
        
        reminders = self.db.get_task_reminders(task_id)
        self.assertEqual(len(reminders), 1)
    
    def test_pending_reminders(self):
        """Test getting pending reminders"""
        task_id = self.db.add_task(title="Task", category="personal")
        
        # Past reminder (should be pending)
        past_time = (datetime.now() - timedelta(hours=1)).isoformat()
        self.db.add_reminder(task_id, past_time, "Past reminder")
        
        # Future reminder (should not be pending)
        future_time = (datetime.now() + timedelta(hours=1)).isoformat()
        self.db.add_reminder(task_id, future_time, "Future reminder")
        
        pending = self.db.get_pending_reminders()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]['message'], "Past reminder")
    
    def test_mark_reminder_triggered(self):
        """Test marking reminder as triggered"""
        task_id = self.db.add_task(title="Task", category="personal")
        past_time = (datetime.now() - timedelta(hours=1)).isoformat()
        reminder_id = self.db.add_reminder(task_id, past_time)
        
        self.db.mark_reminder_triggered(reminder_id)
        
        pending = self.db.get_pending_reminders()
        self.assertEqual(len(pending), 0)
    
    # ==================== EXPORT/IMPORT TESTS ====================
    
    def test_export_to_json(self):
        """Test exporting data to JSON"""
        self.db.add_task(title="Task 1", category="personal")
        self.db.add_task(title="Task 2", category="trabajo")
        self.db.add_quick_note(title="Note 1")
        
        filepath = self.db.export_to_json()
        
        self.assertTrue(os.path.exists(filepath))
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(len(data['tasks']), 2)
        self.assertEqual(len(data['quick_notes']), 1)
    
    def test_export_tasks_to_csv(self):
        """Test exporting tasks to CSV"""
        self.db.add_task(title="Task 1", category="personal")
        self.db.add_task(title="Task 2", category="trabajo")
        
        filepath = self.db.export_tasks_to_csv()
        
        self.assertTrue(os.path.exists(filepath))
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 3)  # Header + 2 tasks
    
    def test_import_from_json(self):
        """Test importing data from JSON"""
        # Create export file
        self.db.add_task(title="Original Task", category="personal")
        filepath = self.db.export_to_json()
        
        # Clear database
        self.db.delete_task(1)
        
        # Import
        counts = self.db.import_from_json(filepath)
        
        self.assertEqual(counts['tasks'], 1)
        
        tasks = self.db.get_all_tasks()
        self.assertEqual(len(tasks), 1)
    
    # ==================== BACKUP TESTS ====================
    
    def test_create_backup(self):
        """Test creating a backup"""
        self.db.add_task(title="Task", category="personal")
        
        backup_path = self.db.create_backup()
        
        self.assertTrue(os.path.exists(backup_path))
        
        backups = self.db.get_backup_list()
        self.assertEqual(len(backups), 1)
    
    def test_restore_from_backup(self):
        """Test restoring from backup"""
        # Create data and backup
        self.db.add_task(title="Original", category="personal")
        backup_path = self.db.create_backup()
        
        # Modify data
        self.db.add_task(title="New Task", category="trabajo")
        self.assertEqual(len(self.db.get_all_tasks()), 2)
        
        # Restore
        success = self.db.restore_from_backup(backup_path)
        self.assertTrue(success)
        
        # Should only have original task
        tasks = self.db.get_all_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['title'], "Original")


class TestHorarioPorFecha(unittest.TestCase):
    """get_schedule_events(for_date=...) filtra por fin de semestre y fecha"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        Database._instance = None
        self.db = Database(str(Path(self.temp_dir) / "test.db"))

    def tearDown(self):
        self.db.conn.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_recurrente_se_corta_tras_fin_de_semestre(self):
        """El horario semanal no se repite pasada la semana del 16 de diciembre"""
        self.db.add_schedule_event(title="Algoritmos", day_of_week=0,
                                   start_time="13:00", end_time="14:20")
        dentro = SEMESTER_END.date() - timedelta(days=7)
        fuera = SEMESTER_END.date() + timedelta(days=1)

        self.assertEqual(len(self.db.get_schedule_events(0, for_date=dentro)), 1)
        self.assertEqual(self.db.get_schedule_events(0, for_date=fuera), [])
        # Sin fecha se sigue viendo todo (editar / exportar)
        self.assertEqual(len(self.db.get_schedule_events(0)), 1)

    def test_evento_puntual_solo_en_su_fecha(self):
        dia = SEMESTER_END.date() - timedelta(days=14)
        self.db.add_schedule_event(title="Examen", day_of_week=dia.weekday(),
                                   start_time="09:00", end_time="10:00",
                                   recurring=0, event_date=dia.isoformat())

        self.assertEqual(len(self.db.get_schedule_events(dia.weekday(), for_date=dia)), 1)
        otra_semana = dia - timedelta(days=7)
        self.assertEqual(self.db.get_schedule_events(dia.weekday(), for_date=otra_semana), [])


if __name__ == '__main__':
    unittest.main()
