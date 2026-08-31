"""
Test ICS Integration Flow
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.task_manager import TaskManager
from src.core.database import db, Database
from src.core.signals import signals

class TestICSIntegration(unittest.TestCase):
    def setUp(self):
        # Use in-memory DB
        # Base en memoria: Database ya conecta y crea las tablas en __init__.
        fresh = Database(":memory:")
        db.conn = fresh.conn
        db.db_path = fresh.db_path
        
        # Reset TaskManager singleton
        TaskManager._instance = None
        self.tm = TaskManager.get_instance()
        
        # Mock ICS sync to avoid real network/file calls
        self.mock_results = {
            'brightspace_deadlines': [
                {
                    'uid': '123',
                    'title': 'Tarea 1',
                    'due_date': '2025-01-20T23:59:00',
                    'course_code': 'CMP 4005',
                    'course_name': 'Redes',
                    'tag': 'Redes',
                    'type': 'assignment',
                    'description': 'Desc',
                    'source': 'brightspace'
                }
            ],
            'teams_events': [
                {
                    'uid': '456',
                    'title': 'Reunion',
                    'start': '2025-01-20T10:00:00',
                    'end': '2025-01-20T11:00:00',
                    'is_meeting': True,
                    'source': 'teams'
                }
            ]
        }
        
    def test_sync_process(self):
        """Test full sync process"""
        # Mock the ICS module
        with patch('src.core.task_manager.UnifiedCalendarSync') as MockSync:
            instance = MockSync.return_value
            instance.sync_all.return_value = self.mock_results
            self.tm.ics_sync = instance
            
            # Setup signal listener
            mock_signal = MagicMock()
            signals.teams_events_updated.connect(mock_signal)
            
            # Run sync
            self.tm.sync_external_calendars()
            
            # Verify Tasks Created
            tasks = db.get_all_tasks()
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0]['title'], 'Tarea 1')
            self.assertEqual(tasks[0]['category'], 'Universidad')
            self.assertIn('Redes', tasks[0]['tags'])
            
            # Verify Signals Emitted
            mock_signal.assert_called_once()
            args = mock_signal.call_args[0][0]
            self.assertEqual(len(args), 1)
            self.assertEqual(args[0]['title'], 'Reunion')
            
            print("✅ Brightspace deadlines converted to Tasks")
            print("✅ Teams events emitted via Signal")
            
    def test_icloud_merge(self):
        """Test merging iCloud events"""
        with patch('src.core.task_manager.UnifiedCalendarSync') as MockICS, \
             patch('src.core.task_manager.ICloudSync') as MockCloud:
            
            # Setup ICS mock
            ics_instance = MockICS.return_value
            ics_instance.sync_all.return_value = {'teams_events': [{'title': 'Teams Event'}]}
            self.tm.ics_sync = ics_instance
            
            # Setup iCloud mock
            cloud_instance = MockCloud.return_value
            from datetime import datetime
            cloud_instance.get_events.return_value = [{
                'uid': 'cloud1',
                'title': 'iCloud Event',
                'start_time': datetime(2025, 1, 20, 15, 0),
                'end_time': datetime(2025, 1, 20, 16, 0),
                'location': 'Home',
                'source': 'icloud'
            }]
            self.tm.icloud_sync = cloud_instance
            
            # Listen to signal
            mock_signal = MagicMock()
            signals.teams_events_updated.connect(mock_signal)
            
            # Sync
            self.tm.sync_external_calendars()
            
            # Check signal received merged list
            args = mock_signal.call_args[0][0]
            titles = [e['title'] for e in args]
            
            self.assertIn('Teams Event', titles)
            self.assertIn('iCloud Event', titles)
            print("✅ iCloud and Teams events merged successfully")

if __name__ == '__main__':
    unittest.main()
