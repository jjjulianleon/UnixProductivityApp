"""
iCloud Calendar Integration
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

# Try to import caldav
try:
    import caldav
    from caldav.elements import dav, cdav
    HAS_CALDAV = True
except ImportError:
    HAS_CALDAV = False
    print("caldav library required: pip install caldav")

CONFIG_DIR = Path.home() / ".config" / "calendar_widget"
ICLOUD_CONFIG_FILE = CONFIG_DIR / "icloud_config.json"


class ICloudSync:
    """Manager for iCloud Calendar synchronization via CalDAV"""
    
    def __init__(self):
        self.client = None
        self.principal = None
        self.calendar = None
        self.connected = False
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        """Load configuration"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(ICLOUD_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "enabled": False,
                "username": "",
                "password": "",  # App-specific password
                "calendar_name": "Calendar",  # Default calendar name
                "last_sync": None
            }
            
    def save_config(self, username, password, enabled=True, calendar_name="Calendar"):
        """Save credentials"""
        self.config["username"] = username
        self.config["password"] = password
        self.config["enabled"] = enabled
        self.config["calendar_name"] = calendar_name
        
        with open(ICLOUD_CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
            
    def connect(self) -> bool:
        """Connect to iCloud CalDAV server"""
        if not HAS_CALDAV or not self.config.get("enabled"):
            return False
        
        # Support both key formats (apple_id or username)
        username = self.config.get("apple_id") or self.config.get("username")
        password = self.config.get("app_password") or self.config.get("password")
        
        if not username or not password:
            print(f"iCloud: Missing credentials. Have: {list(self.config.keys())}")
            return False
            
        try:
            url = "https://caldav.icloud.com/"
            self.client = caldav.DAVClient(
                url=url,
                username=username,
                password=password
            )
            self.principal = self.client.principal()
            
            # Find specific calendar or use default
            calendars = self.principal.calendars()
            target_name = self.config.get("calendar_name", "Calendar")
            
            # 1. Try exact match from config
            for cal in calendars:
                try:
                    cal_name = getattr(cal, 'name', '') or str(cal)
                    if target_name.lower() in cal_name.lower():
                        self.calendar = cal
                        break
                except:
                    pass
            
            # 2. If not found, try common names (Home, Work)
            if not self.calendar:
                for name in ["Home", "Work", "Untitled"]:
                    for cal in calendars:
                        if name.lower() in str(cal).lower():
                            self.calendar = cal
                            break
                    if self.calendar:
                        break
                        
            # 3. Fallback to first non-Reminders calendar
            if not self.calendar and calendars:
                for cal in calendars:
                    if "reminder" not in str(cal).lower():
                        self.calendar = cal
                        break
                
                # Absolute fallback
                if not self.calendar:
                    self.calendar = calendars[0]
                
            self.connected = True
            print(f"Connected to iCloud, using calendar: {self.calendar}")
            return True
            
        except Exception as e:
            print(f"iCloud connection error: {e}")
            import traceback
            traceback.print_exc()
            self.connected = False
            return False
            
    def get_events(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch events between dates"""
        if not self.connected and not self.connect():
            return []
            
        try:
            # CalDAV search
            events = self.calendar.date_search(start=start_date, end=end_date, expand=True)
            results = []
            
            for event in events:
                # Parse vObject
                vevent = event.instance.vevent
                
                uid = str(vevent.uid.value)
                summary = str(vevent.summary.value)
                dtstart = vevent.dtstart.value
                dtend = vevent.dtend.value if hasattr(vevent, 'dtend') else dtstart
                location = str(vevent.location.value) if hasattr(vevent, 'location') else ""
                
                # Normalize timezones
                if isinstance(dtstart, datetime):
                    if dtstart.tzinfo:
                        dtstart = dtstart.astimezone().replace(tzinfo=None) # Local time
                
                if isinstance(dtend, datetime):
                    if dtend.tzinfo:
                        dtend = dtend.astimezone().replace(tzinfo=None)
                
                results.append({
                    'uid': uid,
                    'title': summary,
                    'start_time': dtstart,  # datetime object
                    'end_time': dtend,      # datetime object
                    'location': location,
                    'source': 'icloud',
                    'dav_object': event     # Keep reference for updates
                })
                
            return results
        except Exception as e:
            print(f"Error fetching iCloud events: {e}")
            return []
            
    def add_event(self, title: str, start: datetime, end: datetime, location: str = "") -> bool:
        """Add new event to iCloud"""
        if not self.connected and not self.connect():
            return False
            
        try:
            self.calendar.save_event(
                dtstart=start,
                dtend=end,
                summary=title,
                location=location
            )
            return True
        except Exception as e:
            print(f"Error creating iCloud event: {e}")
            return False
            
    def update_event(self, uid: str, **kwargs) -> bool:
        """Update existing event"""
        # Note: robust update by UID requires searching first
        # For MVP, we might need the dav_object from a previous fetch
        return False  # To be implemented
    
    def event_exists(self, title: str, start: datetime) -> bool:
        """Check if an event with similar title and start time already exists"""
        if not self.connected and not self.connect():
            return False
            
        try:
            # Search for events on that day
            end = start + timedelta(days=1)
            events = self.calendar.date_search(start=start, end=end, expand=True)
            
            for event in events:
                vevent = event.instance.vevent
                existing_title = str(vevent.summary.value).lower()
                existing_start = vevent.dtstart.value
                
                # Fuzzy match on title and exact match on date
                if title.lower()[:20] in existing_title or existing_title in title.lower()[:20]:
                    return True
                    
            return False
        except Exception:
            return False
    
    def sync_deadlines_to_icloud(self, deadlines: list) -> dict:
        """
        Sync D2L/Brightspace deadlines to iCloud Calendar.
        Returns count of created/skipped events.
        """
        if not self.connected and not self.connect():
            return {'created': 0, 'skipped': 0, 'error': 'Not connected'}
            
        created = 0
        skipped = 0
        
        for dl in deadlines:
            try:
                title = f"📚 {dl.get('title', 'Tarea')}"
                course = dl.get('tag', dl.get('course_name', ''))
                if course:
                    title = f"📚 [{course}] {dl.get('title', 'Tarea')}"
                
                due_date_str = dl.get('due_date', '')
                if not due_date_str:
                    skipped += 1
                    continue
                    
                due_dt = datetime.fromisoformat(due_date_str)
                
                # Check if already exists
                if self.event_exists(dl.get('title', ''), due_dt):
                    skipped += 1
                    continue
                
                # Create as all-day event or with specific time
                # D2L deadlines usually have a specific time
                end_dt = due_dt + timedelta(hours=1)
                
                description = dl.get('description', '')
                url = dl.get('url', '')
                location = f"D2L - {course}" if course else "D2L Brightspace"
                
                if self.add_event(title, due_dt, end_dt, location):
                    created += 1
                else:
                    skipped += 1
                    
            except Exception as e:
                print(f"Error syncing deadline to iCloud: {e}")
                skipped += 1
                
        return {'created': created, 'skipped': skipped}
    
    def sync_local_events_to_icloud(self, events: list, week_start: datetime) -> dict:
        """
        Sync local schedule events to iCloud for a specific week.
        """
        if not self.connected and not self.connect():
            return {'created': 0, 'skipped': 0, 'error': 'Not connected'}
            
        created = 0
        skipped = 0
        
        for evt in events:
            try:
                title = evt.get('title', 'Evento')
                day_of_week = evt.get('day_of_week', 0)
                start_time = evt.get('start_time', '09:00')
                end_time = evt.get('end_time', '10:00')
                
                # Calculate actual date
                event_date = week_start + timedelta(days=day_of_week)
                
                # Parse times
                start_h, start_m = map(int, start_time.split(':'))
                end_h, end_m = map(int, end_time.split(':'))
                
                start_dt = event_date.replace(hour=start_h, minute=start_m)
                end_dt = event_date.replace(hour=end_h, minute=end_m)
                
                # Check if exists
                if self.event_exists(title, start_dt):
                    skipped += 1
                    continue
                
                if self.add_event(title, start_dt, end_dt):
                    created += 1
                else:
                    skipped += 1
                    
            except Exception as e:
                print(f"Error syncing local event to iCloud: {e}")
                skipped += 1
                
        return {'created': created, 'skipped': skipped}

