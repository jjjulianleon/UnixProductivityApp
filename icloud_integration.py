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
            
        username = self.config.get("username")
        password = self.config.get("password")
        
        if not username or not password:
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
            
            for cal in calendars:
                # Provide a loose match or check display name
                props = cal.get_properties([dav.DisplayName(), ])
                name = props.get(f"{{{dav.ns('dav')}}}displayname", "")
                if name == target_name:
                    self.calendar = cal
                    break
            
            if not self.calendar and calendars:
                self.calendar = calendars[0]  # Fallback to first
                
            self.connected = True
            return True
            
        except Exception as e:
            print(f"iCloud connection error: {e}")
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
