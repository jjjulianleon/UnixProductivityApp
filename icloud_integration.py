"""
iCloud Calendar Integration
"""
import json
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from pathlib import Path

# Try to import caldav and icalendar
try:
    import caldav
    from caldav.elements import dav, cdav
    import icalendar
    HAS_CALDAV = True
except ImportError:
    HAS_CALDAV = False
    print("caldav and icalendar libraries required: pip install caldav icalendar")

CONFIG_DIR = Path.home() / ".config" / "calendar_widget"
ICLOUD_CONFIG_FILE = CONFIG_DIR / "icloud_config.json"
SYNC_CACHE_FILE = CONFIG_DIR / "icloud_sync_cache.json"


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
                "apple_id": "",
                "app_password": "",
                "calendar_name": "Calendar",
                "last_sync": None
            }
            
    def save_config(self, username, password, enabled=True, calendar_name="Calendar"):
        """Save credentials"""
        self.config["apple_id"] = username
        self.config["app_password"] = password
        self.config["enabled"] = enabled
        self.config["calendar_name"] = calendar_name
        
        with open(ICLOUD_CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
            
    def _load_sync_cache(self) -> set:
        """Load set of already-synced event identifiers"""
        try:
            with open(SYNC_CACHE_FILE, 'r') as f:
                return set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return set()
            
    def _save_sync_cache(self, cache: set):
        """Save sync cache to disk"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(SYNC_CACHE_FILE, 'w') as f:
            json.dump(list(cache), f)
            
    def _make_event_key(self, title: str, due_date: str) -> str:
        """Create unique key for event deduplication"""
        # Use title + date (not time) for key
        date_only = due_date[:10] if due_date else ""
        return f"{title.lower().strip()}|{date_only}"
            
    def connect(self) -> bool:
        """Connect to iCloud CalDAV server"""
        if not HAS_CALDAV or not self.config.get("enabled"):
            return False
        
        username = self.config.get("apple_id")
        password = self.config.get("app_password")
        
        if not username or not password:
            print(f"iCloud: Missing credentials.")
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
            # print(f"Connected to iCloud, using calendar: {self.calendar}")
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
                try:
                    # Parse with icalendar
                    cal = icalendar.Calendar.from_ical(event.data)
                    vevent = None
                    for component in cal.walk():
                        if component.name == "VEVENT":
                            vevent = component
                            break
                    if not vevent:
                        continue # Skip if no VEVENT found
                    
                    uid = str(vevent.get('UID'))
                    summary = str(vevent.get('SUMMARY'))
                    dtstart_ical = vevent.get('DTSTART')
                    dtend_ical = vevent.get('DTEND')
                    
                    dtstart = dtstart_ical.dt if dtstart_ical else None
                    dtend = dtend_ical.dt if dtend_ical else dtstart
                    
                    location = str(vevent.get('LOCATION')) if vevent.get('LOCATION') else ""
                    
                    # Normalize timezones and convert date objects to datetime
                    if isinstance(dtstart, date) and not isinstance(dtstart, datetime):
                        dtstart = datetime.combine(dtstart, datetime.min.time())
                    elif isinstance(dtstart, datetime) and dtstart.tzinfo:
                        dtstart = dtstart.astimezone().replace(tzinfo=None) # Local time
                    
                    if isinstance(dtend, date) and not isinstance(dtend, datetime):
                        dtend = datetime.combine(dtend, datetime.min.time())
                    elif isinstance(dtend, datetime) and dtend.tzinfo:
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
                except Exception as parse_e:
                    print(f"Error parsing iCloud event: {parse_e}")
                    continue
                
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
        """Check if an event with title and date already exists"""
        if not self.connected and not self.connect():
            return False
            
        try:
            # Search for events on that day
            end = start + timedelta(days=1)
            # Use caldav's date_search
            events = self.calendar.date_search(start=start, end=end, expand=True)
            
            target_title = title.lower().strip()
            target_date = start.date()
            
            for event in events:
                try:
                    # Parse with icalendar
                    cal = icalendar.Calendar.from_ical(event.data)
                    for component in cal.walk():
                        if component.name == "VEVENT":
                            summary = str(component.get('SUMMARY'))
                            dtstart_ical = component.get('DTSTART')
                            dtstart = dtstart_ical.dt if dtstart_ical else None
                            
                            # Handle timezone awareness for comparison
                            if isinstance(dtstart, datetime):
                                event_date = dtstart.date()
                            elif isinstance(dtstart, date):
                                event_date = dtstart
                            else:
                                continue # Skip if dtstart is not a date or datetime
                                
                            if event_date != target_date:
                                continue
                                
                            existing_title = summary.lower().strip()
                            
                            # Check for specific match
                            if target_title == existing_title or target_title in existing_title:
                                return True
                except Exception as parse_e:
                    # print(f"Error checking event: {parse_e}")
                    continue
                    
            return False
        except Exception as e:
            print(f"Error checking existence: {e}")
            return False
    
    def sync_deadlines_to_icloud(self, deadlines: list) -> dict:
        """
        Sync deadlines to iCloud Calendar.
        Returns count of created/skipped events.
        """
        if not self.connected and not self.connect():
            return {'created': 0, 'skipped': 0, 'error': 'Not connected'}
            
        created = 0
        skipped = 0
        
        # Load local sync cache to prevent duplicates across restarts
        sync_cache = self._load_sync_cache()
        
        for dl in deadlines:
            try:
                base_title = dl.get('title', 'Tarea')
                course = dl.get('tag', dl.get('course_name', ''))
                
                full_title = f"📚 {base_title}"
                if course:
                    full_title = f"📚 [{course}] {base_title}"
                
                due_date_str = dl.get('due_date', '')
                if not due_date_str:
                    skipped += 1
                    continue
                
                # Check local cache FIRST (fast, no network)
                event_key = self._make_event_key(base_title, due_date_str)
                if event_key in sync_cache:
                    skipped += 1
                    continue
                    
                due_dt = datetime.fromisoformat(due_date_str)
                
                # Then check iCloud (slower, for safety)
                if self.event_exists(full_title, due_dt):
                    # Add to cache since it exists
                    sync_cache.add(event_key)
                    skipped += 1
                    continue
                
                # Use same start/end time for deadlines (point-in-time, not a span)
                end_dt = due_dt  # No +1 hour, deadline is a moment not a duration
                location = f"D2L - {course}" if course else "D2L Brightspace"
                
                if self.add_event(full_title, due_dt, end_dt, location):
                    created += 1
                    # Track in local cache
                    sync_cache.add(event_key)
                else:
                    skipped += 1
                    
            except Exception as e:
                print(f"Error syncing deadline: {e}")
                skipped += 1
        
        # Save updated cache
        self._save_sync_cache(sync_cache)
                
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

