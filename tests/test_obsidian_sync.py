"""
Tests for Obsidian sync operations
"""
import unittest
import tempfile
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.obsidian_sync import ObsidianSync


class TestObsidianSync(unittest.TestCase):
    """Test cases for ObsidianSync class"""
    
    def setUp(self):
        """Set up test vault"""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir) / "TestVault"
        self.vault_path.mkdir(parents=True)
        
        self.sync = ObsidianSync(str(self.vault_path))
    
    def tearDown(self):
        """Clean up test vault"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_creates_folders(self):
        """Test that initialization creates necessary folders"""
        self.assertTrue(self.sync.tasks_folder.exists())
        self.assertTrue(self.sync.rough_notes_folder.exists())
    
    def test_init_creates_category_files(self):
        """Test that initialization creates category files"""
        for filename in self.sync.categories.values():
            file_path = self.sync.tasks_folder / filename
            self.assertTrue(file_path.exists())
    
    def test_add_task(self):
        """Test adding a task"""
        self.sync.add_task(
            title="Test Task",
            category="personal",
            status="pendiente",
            deadline="2024-12-31",
            priority="alta"
        )
        
        file_path = self.sync.tasks_folder / "Personal.md"
        content = file_path.read_text()
        
        self.assertIn("Test Task", content)
        self.assertIn("[deadline: 2024-12-31]", content)
        self.assertIn("[priority: alta]", content)
    
    def test_add_task_completed(self):
        """Test adding a completed task"""
        self.sync.add_task(
            title="Done Task",
            category="trabajo",
            status="completado"
        )
        
        file_path = self.sync.tasks_folder / "Trabajo.md"
        content = file_path.read_text()
        
        self.assertIn("- [x] Done Task", content)
    
    def test_read_all_tasks(self):
        """Test reading all tasks"""
        self.sync.add_task(title="Task 1", category="personal")
        self.sync.add_task(title="Task 2", category="trabajo")
        self.sync.add_task(title="Task 3", category="personal")
        
        tasks = self.sync.read_all_tasks()
        
        self.assertEqual(len(tasks), 3)
        titles = [t['title'] for t in tasks]
        self.assertIn("Task 1", titles)
        self.assertIn("Task 2", titles)
        self.assertIn("Task 3", titles)
    
    def test_read_task_with_metadata(self):
        """Test reading tasks preserves metadata"""
        self.sync.add_task(
            title="Meta Task",
            category="personal",
            deadline="2024-06-15",
            priority="alta"
        )
        
        tasks = self.sync.read_all_tasks()
        task = [t for t in tasks if t['title'] == "Meta Task"][0]
        
        self.assertEqual(task['deadline'], "2024-06-15")
        self.assertEqual(task['priority'], "alta")
        self.assertEqual(task['category'], "personal")
    
    def test_update_task(self):
        """Test updating a task"""
        self.sync.add_task(title="Original Title", category="personal")
        
        self.sync.update_task(
            old_title="Original Title",
            category="personal",
            title="Updated Title"
        )
        
        tasks = self.sync.read_all_tasks()
        titles = [t['title'] for t in tasks]
        
        self.assertNotIn("Original Title", titles)
        self.assertIn("Updated Title", titles)
    
    def test_update_task_status(self):
        """Test updating task status"""
        self.sync.add_task(title="Task", category="personal", status="pendiente")
        
        self.sync.update_task(
            old_title="Task",
            category="personal",
            status="completado"
        )
        
        file_path = self.sync.tasks_folder / "Personal.md"
        content = file_path.read_text()
        
        self.assertIn("- [x] Task", content)
    
    def test_delete_task(self):
        """Test deleting a task"""
        self.sync.add_task(title="To Delete", category="personal")
        self.sync.add_task(title="Keep This", category="personal")
        
        self.sync.delete_task("To Delete", "personal")
        
        tasks = self.sync.read_all_tasks()
        titles = [t['title'] for t in tasks]
        
        self.assertNotIn("To Delete", titles)
        self.assertIn("Keep This", titles)
    
    def test_save_quick_note(self):
        """Test saving a quick note"""
        filepath = self.sync.save_quick_note(
            title="Test Note",
            content="This is a test note."
        )
        
        self.assertTrue(Path(filepath).exists())
        
        content = Path(filepath).read_text()
        self.assertIn("# Test Note", content)
        self.assertIn("This is a test note.", content)
    
    def test_get_quick_notes(self):
        """Test getting quick notes"""
        self.sync.save_quick_note("Note 1", "Content 1")
        self.sync.save_quick_note("Note 2", "Content 2")
        
        notes = self.sync.get_quick_notes()
        
        self.assertEqual(len(notes), 2)
        titles = [n['title'] for n in notes]
        self.assertIn("Note 1", titles)
        self.assertIn("Note 2", titles)
    
    def test_category_sections(self):
        """Test that tasks are added to correct sections"""
        self.sync.add_task(title="Pending", category="personal", status="pendiente")
        self.sync.add_task(title="Progress", category="personal", status="en_progreso")
        self.sync.add_task(title="Done", category="personal", status="completado")
        
        file_path = self.sync.tasks_folder / "Personal.md"
        content = file_path.read_text()
        
        # Check order of sections
        pendiente_pos = content.find("## Pendiente")
        progreso_pos = content.find("## En Progreso")
        completado_pos = content.find("## Completado")
        
        pending_task_pos = content.find("Pending")
        progress_task_pos = content.find("Progress")
        done_task_pos = content.find("Done")
        
        self.assertLess(pendiente_pos, pending_task_pos)
        self.assertLess(progreso_pos, progress_task_pos)
        self.assertLess(completado_pos, done_task_pos)
    
    def test_unknown_category_uses_personal(self):
        """Test that unknown categories default to Personal.md"""
        self.sync.add_task(title="Unknown Category", category="unknown")
        
        file_path = self.sync.tasks_folder / "Personal.md"
        content = file_path.read_text()
        
        self.assertIn("Unknown Category", content)
    
    def test_special_characters_in_note_title(self):
        """Test handling special characters in note titles"""
        filepath = self.sync.save_quick_note(
            title="Test: Note! @2024",
            content="Content"
        )
        
        self.assertTrue(Path(filepath).exists())
        # File should be created with sanitized name
        self.assertIn("Test_Note_2024", Path(filepath).stem)


if __name__ == '__main__':
    unittest.main()
