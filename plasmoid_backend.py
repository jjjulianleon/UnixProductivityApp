#!/usr/bin/env python3
"""
Backend script for KDE Plasma Native Widget
Outputs JSON data for QML to consume
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path to reuse existing logic
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.core.database import db
    from src.core.task_manager import task_manager
except ImportError:
    # Fallback if running from a different location
    sys.path.insert(0, str(PROJECT_ROOT.resolve()))
    from src.core.database import db
    from src.core.task_manager import task_manager

def get_data(sync=False):
    """Fetch all data needed for the widget"""
    if sync:
        try:
            task_manager.sync_external_calendars()
        except:
            pass
            
    data = {
        "tasks": [],
        "stats": {
            "pending": 0,
            "today": 0,
            "overdue": 0,
            "completed": 0
        },
        "next_class": None,
        "urgent": None
    }
    
    try:
        tasks = db.get_all_tasks()
        
        # Get font setting
        fonts = [
            "",  # System default
            "Source Code Pro",
            "Inter",
            "Roboto",
            "Ubuntu",
            "Fira Code"
        ]
        font_idx = db.get_setting('app_font', 0)
        # Ensure index is valid and integer
        try:
            font_idx = int(font_idx)
            if font_idx < 0 or font_idx >= len(fonts):
                font_idx = 0
        except:
            font_idx = 0
            
        current_font = fonts[font_idx]
        
        today_str = datetime.now().strftime('%Y-%m-%d')
        now = datetime.now()
        
        # Process tasks
        pending_count = 0
        today_count = 0
        overdue_count = 0
        completed_count = 0
        
        task_list = []
        calendar_events = {}  # Map 'YYYY-MM-DD' -> List of titles
        
        for t in tasks:
            status = t.get('status')
            deadline = t.get('deadline')
            title = t.get('title')
            
            # Stats
            if status == 'pendiente' or status == 'en progreso':
                # Count both 'pendiente' and 'en progreso' as pending/active
                pending_count += 1
                
                if deadline:
                    dl_date = deadline.split('T')[0]
                    if dl_date == today_str:
                        today_count += 1
                    elif dl_date < today_str:
                        overdue_count += 1
                    
                    # Add to calendar events
                    if dl_date not in calendar_events:
                        calendar_events[dl_date] = []
                    calendar_events[dl_date].append(title)
                    
            elif status == 'completado':
                completed_count += 1
            
            # Add to list (simplify for JSON)
            task_list.append({
                "id": t['id'],
                "title": t['title'],
                "status": status,
                "category": t['category'],
                "priority": t.get('priority', 'media'),
                "deadline": deadline or ""
            })
            
        data["tasks"] = task_list
        data["calendar_events"] = calendar_events # Add to output
        data["font"] = current_font
        data["stats"] = {
            "pending": pending_count,
            "today": today_count,
            "overdue": overdue_count,
            "completed": completed_count
        }
        
        # Urgent task
        pending_deadlines = [t for t in tasks if (t.get('status') != 'completado') and t.get('deadline')]
        pending_deadlines.sort(key=lambda x: x['deadline'])
        
        if pending_deadlines:
            urgent = pending_deadlines[0]
            dl_obj = datetime.fromisoformat(urgent['deadline']) if 'T' in urgent['deadline'] else datetime.strptime(urgent['deadline'], '%Y-%m-%d')
            diff = (dl_obj.date() - now.date()).days
            
            data["urgent"] = {
                "title": urgent['title'],
                "days_left": diff,
                "date": urgent['deadline']
            }
            
        # Schedule from DB
        try:
            current_day = now.weekday()
            schedule_events = db.get_schedule_events(day_of_week=current_day)
            
            # Sort events by start time
            schedule_events.sort(key=lambda x: x['start_time'])
            
            for event in schedule_events:
                # Parse start time HH:MM
                h, m = map(int, event['start_time'].split(':'))
                class_dt = now.replace(hour=h, minute=m, second=0)
                
                # If class is in the future today
                if class_dt > now:
                    diff_min = int((class_dt - now).total_seconds() / 60)
                    data["next_class"] = {
                        "name": event['title'],
                        "minutes": diff_min
                    }
                    break
        except Exception as schedule_err:
            # Fallback or silent error for schedule
            pass
                
    except Exception as e:
        data["error"] = str(e)
        
    return data

if __name__ == "__main__":
    do_sync = "--sync" in sys.argv
    print(json.dumps(get_data(sync=do_sync)))
