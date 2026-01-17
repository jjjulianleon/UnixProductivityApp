"""
Weekly Schedule Widget - GTK4
Teams-style weekly schedule view
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gdk
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager


class WeeklySchedule(Gtk.Box):
    """Weekly schedule grid"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)
        
        self.current_week_start = self._get_week_start(datetime.now())
        self._setup_ui()
        self.refresh()
        
    def _get_week_start(self, date: datetime) -> datetime:
        """Get Monday of the week"""
        return date - timedelta(days=date.weekday())
        
    def _setup_ui(self):
        """Setup schedule UI"""
        # Navigation
        nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        prev_btn = Gtk.Button()
        prev_btn.set_icon_name("go-previous-symbolic")
        prev_btn.add_css_class("circular")
        prev_btn.connect("clicked", self._prev_week)
        nav.append(prev_btn)
        
        today_btn = Gtk.Button(label="Hoy")
        today_btn.add_css_class("flat")
        today_btn.connect("clicked", self._go_today)
        nav.append(today_btn)
        
        self.week_label = Gtk.Label()
        self.week_label.add_css_class("title-4")
        self.week_label.set_hexpand(True)
        nav.append(self.week_label)
        
        next_btn = Gtk.Button()
        next_btn.set_icon_name("go-next-symbolic")
        next_btn.add_css_class("circular")
        next_btn.connect("clicked", self._next_week)
        nav.append(next_btn)
        
        self.append(nav)
        
        # Schedule grid
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_spacing(2)
        self.grid.set_column_spacing(2)
        scroll.set_child(self.grid)
        
        self.append(scroll)
        
    def _prev_week(self, btn):
        """Go to previous week"""
        self.current_week_start -= timedelta(days=7)
        self.refresh()
        
    def _next_week(self, btn):
        """Go to next week"""
        self.current_week_start += timedelta(days=7)
        self.refresh()
        
    def _go_today(self, btn):
        """Go to current week"""
        self.current_week_start = self._get_week_start(datetime.now())
        self.refresh()
        
    def refresh(self):
        """Refresh schedule"""
        # Update week label
        week_end = self.current_week_start + timedelta(days=6)
        months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                  "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        self.week_label.set_text(
            f"{self.current_week_start.day} {months[self.current_week_start.month-1]} - "
            f"{week_end.day} {months[week_end.month-1]} {week_end.year}"
        )
        
        # Clear grid
        while True:
            child = self.grid.get_first_child()
            if child:
                self.grid.remove(child)
            else:
                break
                
        # Header row with days
        days = ["", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        today = datetime.now().date()
        
        for col, day in enumerate(days):
            if col == 0:
                continue  # Skip time column header
            
            day_date = self.current_week_start + timedelta(days=col-1)
            is_today = day_date.date() == today
            
            header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            header.add_css_class("schedule-header")
            if is_today:
                header.add_css_class("accent-button")
                
            day_label = Gtk.Label(label=day)
            day_label.add_css_class("caption")
            header.append(day_label)
            
            date_label = Gtk.Label(label=str(day_date.day))
            date_label.add_css_class("title-4" if is_today else "dim-label")
            header.append(date_label)
            
            self.grid.attach(header, col, 0, 1, 1)
            
        # Time rows
        hours = list(range(7, 20))  # 7 AM to 7 PM
        
        for row, hour in enumerate(hours, start=1):
            # Time label
            time_label = Gtk.Label(label=f"{hour:02d}:00")
            time_label.add_css_class("dim-label")
            time_label.add_css_class("caption")
            time_label.set_size_request(50, 40)
            self.grid.attach(time_label, 0, row, 1, 1)
            
            # Day cells
            for col in range(1, 8):
                cell = Gtk.Box()
                cell.set_size_request(-1, 40)
                cell.add_css_class("dim-label")
                # Light border effect
                css = Gtk.CssProvider()
                css.load_from_data(b"box { border: 1px solid alpha(white, 0.05); }")
                cell.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
                self.grid.attach(cell, col, row, 1, 1)
                
        # Add events
        self._add_events()
        
    def _add_events(self):
        """Add events to the grid"""
        for day in range(7):
            try:
                events = task_manager.get_schedule_events(day)
            except:
                events = []
                
            for event in events:
                self._add_event_to_grid(event, day)
                
    def _add_event_to_grid(self, event: dict, day: int):
        """Add a single event to the grid"""
        start_time = event.get('start_time', '09:00')
        end_time = event.get('end_time', '10:00')
        title = event.get('title', '')
        color = event.get('color', '66, 133, 244')
        
        # Parse times
        start_hour = int(start_time.split(':')[0])
        end_hour = int(end_time.split(':')[0])
        
        # Calculate grid position
        col = day + 1
        row = start_hour - 7 + 1  # Offset for header and 7 AM start
        span = max(1, end_hour - start_hour)
        
        if row < 1 or row > 13:
            return
            
        # Create event widget
        event_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        event_box.add_css_class("schedule-event")
        
        css = Gtk.CssProvider()
        css.load_from_data(f"box {{ background: rgba({color}, 0.8); }}".encode())
        event_box.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        title_label = Gtk.Label(label=title)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        event_box.append(title_label)
        
        time_label = Gtk.Label(label=f"{start_time}-{end_time}")
        time_label.add_css_class("caption")
        time_label.set_halign(Gtk.Align.START)
        event_box.append(time_label)
        
        self.grid.attach(event_box, col, row, 1, span)
