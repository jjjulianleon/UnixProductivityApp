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
except ImportError:
    # Fallback if running from a different location
    sys.path.insert(0, "/home/jjulianleon/Coding/CalendarWidget")
    from src.core.database import db

def get_data():
    """Fetch all data needed for the widget"""
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
        today_str = datetime.now().strftime('%Y-%m-%d')
        now = datetime.now()
        
        # Process tasks
        pending_count = 0
        today_count = 0
        overdue_count = 0
        completed_count = 0
        
        task_list = []
        
        for t in tasks:
            status = t.get('status')
            deadline = t.get('deadline')
            
            # Stats
            if status == 'pendiente' or status == 'en progreso':
                pending_count += 1
                if deadline:
                    if deadline.startswith(today_str):
                        today_count += 1
                    elif deadline < today_str:
                        overdue_count += 1
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
            
        # Fixed schedule (Hardcoded for now as in widget_gtk.py)
        FIXED_SCHEDULE = {
            0: [("13:00", "Data Mining"), ("14:30", "Redes Lab")],
            1: [("10:00", "Bases de Datos"), ("13:00", "Redes"), ("14:30", "Mercados Int."), ("16:00", "PASEC")],
            2: [("13:00", "Data Mining"), ("14:30", "PASEC Teoría")],
            3: [("10:00", "Bases de Datos"), ("13:00", "Redes"), ("14:30", "Mercados Int.")],
            4: [("14:00", "PASEC")],
        }
        
        today_schedule = FIXED_SCHEDULE.get(now.weekday(), [])
        for time_str, name in today_schedule:
            h, m = map(int, time_str.split(':'))
            class_dt = now.replace(hour=h, minute=m, second=0)
            if class_dt > now:
                diff_min = int((class_dt - now).total_seconds() / 60)
                data["next_class"] = {
                    "name": name,
                    "minutes": diff_min
                }
                break
                
    except Exception as e:
        data["error"] = str(e)
        
    return data

if __name__ == "__main__":
    print(json.dumps(get_data()))
