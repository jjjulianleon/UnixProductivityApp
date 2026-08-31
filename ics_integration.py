"""
ICS Calendar Integration Module

Unified module for importing calendar events from ICS feeds:
- Brightspace D2L (university deadlines)
- Microsoft Teams/Outlook (work calendar)

Events are imported into the app's calendar and optionally as tasks in the Kanban.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import os

# Try to import icalendar for ICS parsing
try:
    from icalendar import Calendar, Event
    from icalendar.prop import vDDDTypes
    HAS_ICALENDAR = True
except ImportError:
    HAS_ICALENDAR = False
    print("Para soporte ICS: pip install icalendar")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from icloud_integration import ICloudSync
    HAS_ICLOUD = True
except ImportError:
    HAS_ICLOUD = False



# ============== CONFIGURATION ==============
import sys
sys.path.insert(0, str(Path(__file__).parent))
from src.utils.system import config_dir

CONFIG_DIR = config_dir("calendar_widget")
CONFIG_FILE = CONFIG_DIR / "ics_config.json"
CACHE_DIR = CONFIG_DIR / "cache"

# Default course mappings
COURSE_MAPPINGS = {
    "CMP 4005": {"name": "Redes", "tag": "Redes", "color": "66, 133, 244"},
    "CMP 5002": {"name": "Data Mining", "tag": "Data Mining", "color": "52, 168, 83"},
    "CMP 4002": {"name": "Base de Datos", "tag": "Bases", "color": "231, 76, 60"},
    "FIN 4007": {"name": "Mercados Int.", "tag": "Finanzas", "color": "241, 196, 15"},
    "ING 0001": {"name": "Coloquios", "tag": "Coloquios", "color": "149, 165, 166"},
    "PRC 2000": {"name": "PASEC", "tag": "PASEC", "color": "155, 89, 182"},
}

# Event types to detect
EVENT_TYPES = {
    "assignment": ["tarea", "assignment", "homework", "hw", "deberes", "pset"],
    "exam": ["quiz", "examen", "test", "exam", "prueba"],
    "project": ["proyecto", "project", "informe"],
    "lab": ["lab", "laboratorio"],
    "meeting": ["meeting", "reunión", "reunion", "resultados"],
}


class ICSConfig:
    """Configuration manager for ICS integrations"""
    
    def __init__(self):
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        """Load configuration from file"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self._default_config()
            
    def _default_config(self) -> dict:
        return {
            "brightspace": {
                "enabled": True,
                "source": "file",  # "file" or "url"
                "file_path": str(Path(__file__).parent / "brightspace" / "feed.ics"),
                "url": "",
                "import_as_tasks": True,
                "category": "Universidad"
            },
            "teams": {
                "enabled": True,
                "source": "file",  # "file" or "url"
                "file_path": str(Path(__file__).parent / "teams" / "calendar.ics"),
                "url": "https://outlook.office365.com/owa/calendar/91bdba2c9fd14d6fa042fb36a8f7043b@usfq.edu.ec/08d6df05166f4b71ba1deeb7141cee5c17574312868342675028/calendar.ics",
                "import_as_events": True,
                "filter_work_only": False
            },
            "course_mappings": COURSE_MAPPINGS,
            "cache_duration_minutes": 30,
            "last_sync": None
        }
        
    def save(self):
        """Save configuration to file"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
            
    def get(self, key: str, default=None):
        return self.config.get(key, default)
        
    def set(self, key: str, value):
        self.config[key] = value
        self.save()


class ICSParser:
    """Parse ICS calendar files and extract events"""
    
    def __init__(self):
        if not HAS_ICALENDAR:
            raise ImportError("icalendar library required: pip install icalendar")
            
    def parse_file(self, file_path: str) -> List[Dict]:
        """Parse events from a local ICS file"""
        try:
            with open(file_path, 'rb') as f:
                return self._parse_ics_content(f.read())
        except FileNotFoundError:
            print(f"ICS file not found: {file_path}")
            return []
        except Exception as e:
            print(f"Error parsing ICS file: {e}")
            return []
            
    def parse_url(self, url: str) -> List[Dict]:
        """Parse events from an ICS URL"""
        if not HAS_REQUESTS:
            print("requests library required: pip install requests")
            return []
            
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return self._parse_ics_content(response.content)
        except Exception as e:
            print(f"Error fetching ICS URL: {e}")
            return []
            
    def _parse_ics_content(self, content: bytes) -> List[Dict]:
        """Parse ICS content and return list of events"""
        events = []
        cal = Calendar.from_ical(content)
        
        for component in cal.walk():
            if component.name == "VEVENT":
                event = self._parse_event(component)
                if event:
                    events.append(event)
                    
        return events
        
    def _parse_event(self, component) -> Optional[Dict]:
        """Parse a single VEVENT component"""
        try:
            summary = str(component.get('SUMMARY', ''))
            if not summary:
                return None
                
            dtstart = component.get('DTSTART')
            # Parse date
            dt_start = component.get('dtstart').dt
            
            # Handle deadlines (using End Date often implies the due time)
            dt_end = component.get('dtend')
            target_dt = dt_end.dt if dt_end else dt_start
            
            # Convert to local timezone and extract the date for deadline display
            if isinstance(target_dt, datetime):
                # Convert to local timezone first
                if target_dt.tzinfo is not None:
                    local_dt = target_dt.astimezone()
                else:
                    local_dt = target_dt
                    
                # Handle midnight edge case: 00:00 of day X means deadline was day X-1 at 23:59
                # This is common in ICS where "due by Sunday" is encoded as Monday 00:00
                if local_dt.hour == 0 and local_dt.minute == 0:
                    # Subtract 1 minute to get the actual deadline day
                    local_dt = local_dt - timedelta(minutes=1)
                    
                deadline_str = local_dt.strftime('%Y-%m-%d')
            else:
                # It's a date object (all-day event)
                deadline_str = target_dt.strftime('%Y-%m-%d')
            start_dt = self._normalize_datetime(dtstart.dt)
            end_dt = self._normalize_datetime(dt_end.dt) if dt_end else start_dt
            
            # Extract other fields
            description = str(component.get('DESCRIPTION', '') or '')
            location = str(component.get('LOCATION', '') or '')
            uid = str(component.get('UID', ''))
            
            # Check for recurrence
            rrule = component.get('RRULE')
            is_recurring = rrule is not None
            
            return {
                'uid': uid,
                'title': summary.strip(),
                'start': start_dt.isoformat() if start_dt else None,
                'end': end_dt.isoformat() if end_dt else None,
                'deadline': local_dt.replace(tzinfo=None).isoformat() if isinstance(target_dt, datetime) else target_dt.strftime('%Y-%m-%dT%H:%M:%S') if target_dt else None,
                'description': description[:500],  # Limit description length
                'location': location,
                'url': str(component.get('URL', '') or ''),
                'is_recurring': is_recurring,
                'all_day': not hasattr(dtstart.dt, 'hour'),
                'raw_rrule': str(rrule) if rrule else None
            }
        except Exception as e:
            print(f"Error parsing event: {e}")
            return None
            
    def _normalize_datetime(self, dt) -> Optional[datetime]:
        """Normalize datetime to Python datetime object in local time"""
        if dt is None:
            return None
        if isinstance(dt, datetime):
            # Convert to local time if timezone aware
            if dt.tzinfo:
                dt = dt.astimezone()
            # Return naive datetime in local timzone
            return dt.replace(tzinfo=None)
        # Handle date-only (all-day events)
        if hasattr(dt, 'year'):
            return datetime(dt.year, dt.month, dt.day)
        return None


class BrightspaceIntegration:
    """Integration for Brightspace D2L calendar"""
    
    def __init__(self, config: ICSConfig):
        self.config = config
        self.parser = ICSParser()
        self.bs_config = config.get("brightspace", {})
        
    def get_deadlines(self) -> List[Dict]:
        """Get all upcoming deadlines from Brightspace"""
        events = self._fetch_events()
        return self._process_deadlines(events)
        
    def _fetch_events(self) -> List[Dict]:
        """Fetch events from configured source"""
        source = self.bs_config.get("source", "file")
        
        if source == "file":
            file_path = self.bs_config.get("file_path", "")
            return self.parser.parse_file(file_path)
        else:
            url = self.bs_config.get("url", "")
            return self.parser.parse_url(url)
            
    def _process_deadlines(self, events: List[Dict]) -> List[Dict]:
        """Process events into deadline format with course tags"""
        deadlines = []
        now = datetime.now()
        course_mappings = self.config.get("course_mappings", COURSE_MAPPINGS)
        
        for event in events:
            # Skip past events
            if event.get('start'):
                start_dt = datetime.fromisoformat(event['start'])
                if start_dt < now:
                    continue
                    
            # Extract course info from LOCATION field
            location = event.get('location', '')
            course_code, course_info = self._extract_course(location, course_mappings)
            
            # Skip if no valid course found (university general events)
            if not course_code:
                continue
                
            # Detect event type
            event_type = self._detect_event_type(event['title'])
            
            # Clean title (remove "- Vencimiento" suffix)
            title = event['title']
            title = re.sub(r'\s*-\s*(Vencimiento|Disponible|La disponibilidad finaliza)$', '', title)
            
            deadlines.append({
                'uid': event['uid'],
                'title': title,
                'due_date': event.get('deadline') or event['start'],
                'course_code': course_code,
                'course_name': course_info.get('name', ''),
                'tag': course_info.get('tag', course_code),
                'color': course_info.get('color', '66, 133, 244'),
                'type': event_type,
                'description': event.get('description', ''),
                'url': event.get('url', ''),
                'source': 'brightspace'
            })
            
        # Sort by due date
        deadlines.sort(key=lambda x: x['due_date'])
        return deadlines
        
    def _extract_course(self, location: str, mappings: dict) -> Tuple[str, dict]:
        """Extract course code and info from location string"""
        if not location:
            return None, {}
            
        # 1. Try exact match from mappings
        for code, info in mappings.items():
            if code in location:
                return code, info
                
        # 2. Dynamic extraction using Regex (e.g., "CMP 4005 Redes")
        # Pattern: 3 letters + space + 4 digits
        match = re.search(r'([A-Z]{3}\s\d{4})\s+(.+?)(?:\s-|$)', location)
        if match:
            code = match.group(1)
            raw_name = match.group(2).strip()
            # Clean up name (remove common suffixes)
            name = raw_name.split('-')[0].strip()
            
            return code, {
                "name": name,
                "tag": name,  # Use full name as tag if unknown
                "color": "127, 140, 141"  # Default gray
            }
            
        return None, {}
        
    def _detect_event_type(self, title: str) -> str:
        """Detect assignment type from title"""
        title_lower = title.lower()
        
        for event_type, keywords in EVENT_TYPES.items():
            if any(kw in title_lower for kw in keywords):
                return event_type
                
        return 'other'


class TeamsIntegration:
    """Integration for Microsoft Teams/Outlook calendar via ICS"""
    
    def __init__(self, config: ICSConfig):
        self.config = config
        self.parser = ICSParser()
        self.teams_config = config.get("teams", {})
        
    def get_events(self, days_ahead: int = 30) -> List[Dict]:
        """Get upcoming events from Teams calendar"""
        events = self._fetch_events()
        return self._process_events(events, days_ahead)
        
    def _fetch_events(self) -> List[Dict]:
        """Fetch events from configured source"""
        source = self.teams_config.get("source", "file")
        
        if source == "file":
            file_path = self.teams_config.get("file_path", "")
            return self.parser.parse_file(file_path)
        else:
            url = self.teams_config.get("url", "")
            return self.parser.parse_url(url)
            
    def _process_events(self, events: List[Dict], days_ahead: int) -> List[Dict]:
        """Process and filter events"""
        processed = []
        now = datetime.now()
        cutoff = now + timedelta(days=days_ahead)
        
        for event in events:
            if not event.get('start'):
                continue
                
            start_dt = datetime.fromisoformat(event['start'])
            
            # Filter by date range
            if start_dt < now or start_dt > cutoff:
                continue
                
            # Detect if it's a meeting
            is_meeting = 'Teams' in event.get('location', '') or \
                         'meeting' in event['title'].lower() or \
                         'reunión' in event['title'].lower()
                         
            processed.append({
                'uid': event['uid'],
                'title': event['title'],
                'start': event['start'],
                'end': event['end'],
                'location': event.get('location', ''),
                'is_meeting': is_meeting,
                'is_recurring': event.get('is_recurring', False),
                'all_day': event.get('all_day', False),
                'source': 'teams'
            })
            
        # Sort by start time
        processed.sort(key=lambda x: x['start'])
        return processed
        
    def get_today_events(self) -> List[Dict]:
        """Get events for today only"""
        return [e for e in self.get_events(days_ahead=1)]
        
    def get_week_events(self) -> List[Dict]:
        """Get events for the next 7 days"""
        return self.get_events(days_ahead=7)


class UnifiedCalendarSync:
    """Main class to synchronize all calendar sources"""
    
    def __init__(self):
        self.config = ICSConfig()
        self.brightspace = BrightspaceIntegration(self.config)
        self.teams = TeamsIntegration(self.config)
        
        if HAS_ICLOUD:
            self.icloud = ICloudSync()
        else:
            self.icloud = None
        
    def sync_all(self) -> Dict[str, List[Dict]]:
        """Synchronize all calendar sources"""
        result = {
            'brightspace_deadlines': [],
            'teams_events': [],
            'icloud_events': [],
            'errors': []
        }
        
        # Sync Brightspace
        if self.config.get("brightspace", {}).get("enabled", True):
            try:
                result['brightspace_deadlines'] = self.brightspace.get_deadlines()
            except Exception as e:
                result['errors'].append(f"Brightspace: {str(e)}")
                
        # Sync Teams
        if self.config.get("teams", {}).get("enabled", True):
            try:
                result['teams_events'] = self.teams.get_events()
            except Exception as e:
                result['errors'].append(f"Teams: {str(e)}")
                
        # Sync iCloud (read events)
        if self.icloud and self.icloud.config.get("enabled", False):
            try:
                # Sync next 30 days
                start = datetime.now()
                end = start + timedelta(days=30)
                result['icloud_events'] = self.icloud.get_events(start, end)
                
                # Upload D2L deadlines to iCloud (bidirectional sync)
                if result['brightspace_deadlines']:
                    sync_result = self.icloud.sync_deadlines_to_icloud(result['brightspace_deadlines'])
                    if sync_result.get('created', 0) > 0:
                        print(f"✅ Synced {sync_result['created']} deadlines to iCloud")
                        
            except Exception as e:
                result['errors'].append(f"iCloud: {str(e)}")
                
        # Update last sync time
        self.config.set("last_sync", datetime.now().isoformat())
        
        return result
        
    def get_upcoming_deadlines(self, days: int = 7) -> List[Dict]:
        """Get deadlines for the next N days"""
        deadlines = self.brightspace.get_deadlines()
        cutoff = datetime.now() + timedelta(days=days)
        
        return [
            d for d in deadlines
            if datetime.fromisoformat(d['due_date']) <= cutoff
        ]
        
    def get_upcoming_events(self, days: int = 7) -> List[Dict]:
        """Get combined events (Teams + iCloud) for the next N days"""
        # Teams events
        teams_events = self.teams.get_events(days_ahead=days)
        
        # iCloud events
        icloud_events = []
        if self.icloud and self.icloud.config.get("enabled", False):
            try:
                start = datetime.now()
                end = start + timedelta(days=days)
                raw_events = self.icloud.get_events(start, end)
                
                # Format to match Teams structure
                for ev in raw_events:
                    icloud_events.append({
                        'uid': ev['uid'],
                        'title': ev['title'],
                        'start': ev['start_time'].isoformat(),
                        'end': ev['end_time'].isoformat(),
                        'location': ev['location'],
                        'is_meeting': False, # Unless detected
                        'is_recurring': False, # Handled by CalDAV expansion
                        'source': 'icloud',
                        'color': '52, 168, 83' # Green for iCloud
                    })
            except Exception:
                pass
                
        # Combine and sort
        all_events = teams_events + icloud_events
        all_events.sort(key=lambda x: x['start'])
        
        return all_events
        
    def refresh_teams_ics(self) -> bool:
        """Download fresh ICS from Teams URL"""
        if not HAS_REQUESTS:
            return False
            
        url = self.config.get("teams", {}).get("url", "")
        file_path = self.config.get("teams", {}).get("file_path", "")
        
        if not url or not file_path:
            return False
            
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(response.content)
                
            return True
        except Exception as e:
            print(f"Error refreshing Teams ICS: {e}")
            return False


# ============== CLI TEST ==============
if __name__ == "__main__":
    print("=" * 60)
    print("ICS Calendar Integration Test")
    print("=" * 60)
    
    if not HAS_ICALENDAR:
        print("\n❌ Error: icalendar not installed")
        print("Run: pip install icalendar")
        exit(1)
        
    sync = UnifiedCalendarSync()
    
    print("\n📚 Brightspace Deadlines:")
    print("-" * 40)
    deadlines = sync.get_upcoming_deadlines(days=30)
    
    if deadlines:
        for dl in deadlines:
            due = datetime.fromisoformat(dl['due_date'])
            days_left = (due - datetime.now()).days
            emoji = "🔴" if days_left <= 2 else "🟡" if days_left <= 5 else "🟢"
            print(f"  {emoji} {dl['title']}")
            print(f"     📅 {due.strftime('%d/%m/%Y %H:%M')} ({days_left} días)")
            print(f"     🏷️  [{dl['tag']}] - {dl['type']}")
            print()
    else:
        print("  No hay deadlines próximos")
        
    print("\n📅 Teams/Outlook Events (próximos 7 días):")
    print("-" * 40)
    events = sync.get_upcoming_events(days=7)
    
    if events:
        for event in events[:10]:  # Limit to 10
            start = datetime.fromisoformat(event['start'])
            emoji = "📞" if event['is_meeting'] else "📌"
            print(f"  {emoji} {event['title']}")
            print(f"     📅 {start.strftime('%d/%m/%Y %H:%M')}")
            if event['location']:
                print(f"     📍 {event['location'][:50]}")
            print()
    else:
        print("  No hay eventos próximos")
        
    print("\n✅ Configuración guardada en:", CONFIG_FILE)
