"""
Auto Sync Module
Automatically synchronizes ICS calendars (Brightspace D2L, Teams) with the app.
Runs on startup and periodically in background.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.database import db
from src.core.task_manager import task_manager


class AutoSync:
    """Automatic calendar synchronization manager"""

    # Sync interval in seconds (15 minutes)
    SYNC_INTERVAL = 15 * 60

    def __init__(self):
        self.last_sync = None
        self.sync_thread = None
        self.running = False
        self._callbacks = []

    def add_callback(self, callback):
        """Add callback to be called after sync completes"""
        self._callbacks.append(callback)

    def start_background_sync(self):
        """Start background sync thread"""
        if self.running:
            return

        self.running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        print("AutoSync: Background sync started")

    def stop_background_sync(self):
        """Stop background sync thread"""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=2)

    def _sync_loop(self):
        """Background sync loop"""
        # Initial sync after 5 seconds (let app start up)
        time.sleep(5)
        self.sync_now()

        while self.running:
            time.sleep(self.SYNC_INTERVAL)
            if self.running:
                self.sync_now()

    def sync_now(self) -> Dict:
        """Perform immediate sync of all sources"""
        result = {
            'brightspace': {'imported': 0, 'skipped': 0, 'errors': []},
            'teams': {'imported': 0, 'skipped': 0, 'errors': []},
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Import ICS integration
            from ics_integration import UnifiedCalendarSync, HAS_ICALENDAR

            if not HAS_ICALENDAR:
                result['brightspace']['errors'].append("icalendar library not installed")
                return result

            sync = UnifiedCalendarSync()

            # Sync Brightspace deadlines
            bs_result = self._sync_brightspace(sync)
            result['brightspace'] = bs_result

            # Sync Teams events (optional - as schedule events)
            # teams_result = self._sync_teams(sync)
            # result['teams'] = teams_result

            self.last_sync = datetime.now()

            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(result)
                except Exception as e:
                    print(f"AutoSync callback error: {e}")

            print(f"AutoSync: Completed - {result['brightspace']['imported']} new deadlines")

        except ImportError as e:
            result['brightspace']['errors'].append(f"Import error: {e}")
            print(f"AutoSync: Import error - {e}")
        except Exception as e:
            result['brightspace']['errors'].append(str(e))
            print(f"AutoSync: Error - {e}")

        return result

    def _sync_brightspace(self, sync) -> Dict:
        """Sync Brightspace D2L deadlines as tasks"""
        result = {'imported': 0, 'skipped': 0, 'errors': []}

        try:
            deadlines = sync.get_upcoming_deadlines(days=60)

            if not deadlines:
                return result

            # Get existing tasks to avoid duplicates
            existing_tasks = task_manager.get_all_tasks()
            existing_titles = {t.get('title', '').lower().strip() for t in existing_tasks}
            existing_with_dates = {
                (t.get('title', '').lower().strip(), t.get('deadline', ''))
                for t in existing_tasks
            }

            for deadline in deadlines:
                try:
                    title = deadline.get('title', '').strip()
                    if not title:
                        continue

                    # Parse due date
                    due_date_str = deadline.get('due_date', '')
                    if not due_date_str:
                        continue

                    # Extract just the date part
                    if 'T' in due_date_str:
                        deadline_date = due_date_str.split('T')[0]
                    else:
                        deadline_date = due_date_str[:10]

                    # Check for duplicates (same title AND same deadline)
                    key = (title.lower().strip(), deadline_date)
                    if key in existing_with_dates:
                        result['skipped'] += 1
                        continue

                    # Also skip if title exists with different date (avoid duplicate entries)
                    # But only for very similar titles
                    if title.lower().strip() in existing_titles:
                        result['skipped'] += 1
                        continue

                    # Determine category based on course
                    course_name = deadline.get('course_name', '')
                    tag = deadline.get('tag', 'Universidad')

                    # Build description
                    desc_parts = []
                    if deadline.get('type'):
                        desc_parts.append(f"Tipo: {deadline['type']}")
                    if course_name:
                        desc_parts.append(f"Curso: {course_name}")
                    if deadline.get('url'):
                        desc_parts.append(f"Link: {deadline['url']}")
                    if deadline.get('description'):
                        desc_parts.append(deadline['description'][:200])

                    description = "\n".join(desc_parts)

                    # Determine priority based on days until deadline
                    days_until = (datetime.strptime(deadline_date, '%Y-%m-%d') - datetime.now()).days
                    if days_until <= 2:
                        priority = 'alta'
                    elif days_until <= 5:
                        priority = 'media'
                    else:
                        priority = 'baja'

                    # Add task
                    task_manager.add_task(
                        title=title,
                        description=description,
                        category='Universidad',
                        priority=priority,
                        deadline=deadline_date,
                        tags=[tag, 'D2L', 'auto-sync']
                    )

                    result['imported'] += 1

                    # Add to existing set to prevent duplicates within same sync
                    existing_titles.add(title.lower().strip())
                    existing_with_dates.add(key)

                except Exception as e:
                    result['errors'].append(f"Error importing {deadline.get('title', 'unknown')}: {e}")

        except Exception as e:
            result['errors'].append(str(e))

        return result

    def _sync_teams(self, sync) -> Dict:
        """Sync Teams events as schedule events"""
        result = {'imported': 0, 'skipped': 0, 'errors': []}

        try:
            events = sync.teams.get_events(days_ahead=14)

            for event in events:
                try:
                    title = event.get('title', '').strip()
                    if not title:
                        continue

                    # Parse start time
                    start_str = event.get('start', '')
                    if not start_str:
                        continue

                    start_dt = datetime.fromisoformat(start_str)
                    end_str = event.get('end', '')
                    end_dt = datetime.fromisoformat(end_str) if end_str else start_dt + timedelta(hours=1)

                    # Check if event already exists
                    day_of_week = start_dt.weekday()
                    existing = db.get_schedule_events(day_of_week)

                    # Simple duplicate check by title and time
                    start_time = start_dt.strftime('%H:%M')
                    is_duplicate = any(
                        e.get('title', '').lower() == title.lower() and
                        e.get('start_time', '') == start_time
                        for e in existing
                    )

                    if is_duplicate:
                        result['skipped'] += 1
                        continue

                    # Add as non-recurring event
                    db.add_schedule_event(
                        title=title,
                        day_of_week=day_of_week,
                        start_time=start_dt.strftime('%H:%M'),
                        end_time=end_dt.strftime('%H:%M'),
                        color='#ff5722' if event.get('is_meeting') else '#4285f4',
                        recurring=0,
                        event_date=start_dt.strftime('%Y-%m-%d')
                    )

                    result['imported'] += 1

                except Exception as e:
                    result['errors'].append(f"Error: {e}")

        except Exception as e:
            result['errors'].append(str(e))

        return result

    def get_status(self) -> Dict:
        """Get current sync status"""
        return {
            'running': self.running,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'next_sync': (self.last_sync + timedelta(seconds=self.SYNC_INTERVAL)).isoformat()
                        if self.last_sync else None
        }


# Singleton instance
auto_sync = AutoSync()
