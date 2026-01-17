"""
Weekly Schedule Widget - GTK4
Teams-style weekly schedule view with semester date support
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


# Semester configuration
SEMESTER_START = datetime(2026, 1, 12)  # 12 de enero
SEMESTER_END = datetime(2026, 5, 16)    # 16 de mayo
INTERNSHIP_END = datetime(2026, 2, 14)  # Pasantías hasta 14 de febrero

# Fixed schedule (Lunes=0, Domingo=6)
FIXED_SCHEDULE = {
    0: [  # Lunes
        {"start": "13:00", "end": "14:20", "title": "Data Mining", "color": "66, 133, 244"},
        {"start": "14:30", "end": "15:50", "title": "Redes Lab", "color": "52, 168, 83"},
    ],
    1: [  # Martes
        {"start": "10:00", "end": "11:20", "title": "Bases de Datos", "color": "251, 188, 5"},
        {"start": "13:00", "end": "14:20", "title": "Redes", "color": "52, 168, 83"},
        {"start": "14:30", "end": "15:50", "title": "Mercados Int.", "color": "234, 67, 53"},
        {"start": "16:00", "end": "18:00", "title": "PASEC", "color": "156, 39, 176"},
    ],
    2: [  # Miércoles
        {"start": "13:00", "end": "14:20", "title": "Data Mining", "color": "66, 133, 244"},
        {"start": "14:30", "end": "15:50", "title": "PASEC Teoría", "color": "156, 39, 176"},
    ],
    3: [  # Jueves
        {"start": "10:00", "end": "11:20", "title": "Bases de Datos", "color": "251, 188, 5"},
        {"start": "13:00", "end": "14:20", "title": "Redes", "color": "52, 168, 83"},
        {"start": "14:30", "end": "15:50", "title": "Mercados Int.", "color": "234, 67, 53"},
    ],
    4: [  # Viernes
        {"start": "08:30", "end": "13:30", "title": "PASANTÍAS", "color": "255, 87, 34", "ends": INTERNSHIP_END},
        {"start": "14:00", "end": "18:00", "title": "PASEC", "color": "156, 39, 176"},
    ],
    5: [],  # Sábado
    6: [],  # Domingo
}


class AddEventDialog(Adw.Window):
    """Dialog to add a new event"""
    
    def __init__(self, parent=None, default_day=0, default_hour=9):
        super().__init__()
        self.set_title("Nuevo Evento")
        self.set_default_size(400, 400)
        self.set_modal(True)
        if parent:
            self.set_transient_for(parent)
            
        self.default_day = default_day
        self.default_hour = default_hour
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup dialog UI"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)
        
        # Header
        header = Adw.HeaderBar()
        header.add_css_class("flat")
        
        cancel_btn = Gtk.Button(label="Cancelar")
        cancel_btn.connect("clicked", lambda _: self.close())
        header.pack_start(cancel_btn)
        
        save_btn = Gtk.Button(label="Guardar")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save)
        header.pack_end(save_btn)
        
        main_box.append(header)
        
        # Content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        
        # Title
        title_group = Adw.PreferencesGroup()
        self.title_entry = Adw.EntryRow()
        self.title_entry.set_title("Nombre del evento")
        title_group.add(self.title_entry)
        content.append(title_group)
        
        # Day
        day_group = Adw.PreferencesGroup()
        self.day_row = Adw.ComboRow()
        self.day_row.set_title("Día")
        days = Gtk.StringList.new(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
        self.day_row.set_model(days)
        self.day_row.set_selected(self.default_day)
        day_group.add(self.day_row)
        content.append(day_group)
        
        # Time row
        time_group = Adw.PreferencesGroup()
        time_group.set_title("Horario")
        
        self.start_row = Adw.EntryRow()
        self.start_row.set_title("Inicio")
        self.start_row.set_text(f"{self.default_hour:02d}:00")
        time_group.add(self.start_row)
        
        self.end_row = Adw.EntryRow()
        self.end_row.set_title("Fin")
        self.end_row.set_text(f"{self.default_hour + 1:02d}:30")
        time_group.add(self.end_row)
        
        content.append(time_group)
        
        # Recurring
        recur_group = Adw.PreferencesGroup()
        self.recurring_switch = Adw.SwitchRow()
        self.recurring_switch.set_title("Evento recurrente")
        self.recurring_switch.set_subtitle("Se repite cada semana")
        recur_group.add(self.recurring_switch)
        content.append(recur_group)
        
        main_box.append(content)
        
    def _on_save(self, btn):
        """Save the event"""
        title = self.title_entry.get_text()
        if not title:
            self.title_entry.add_css_class("error")
            return
            
        # Save event (would save to database)
        try:
            event = {
                'title': title,
                'day': self.day_row.get_selected(),
                'start_time': self.start_row.get_text(),
                'end_time': self.end_row.get_text(),
                'recurring': self.recurring_switch.get_active(),
                'color': '66, 133, 244'
            }
            task_manager.add_schedule_event(event)
            self.close()
        except Exception as e:
            print(f"Error saving event: {e}")
            self.close()


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
        
        # Add event button
        add_btn = Gtk.Button()
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.add_css_class("suggested-action")
        add_btn.add_css_class("circular")
        add_btn.set_tooltip_text("Agregar evento")
        add_btn.connect("clicked", self._on_add_event)
        nav.append(add_btn)
        
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
        
    def _on_add_event(self, btn):
        """Show add event dialog"""
        dialog = AddEventDialog(parent=self.get_root())
        dialog.present()
        
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
        
    def _is_in_semester(self, date: datetime) -> bool:
        """Check if date is within semester"""
        return SEMESTER_START <= date <= SEMESTER_END
        
    def _is_internship_active(self, date: datetime) -> bool:
        """Check if internship is still active"""
        return date <= INTERNSHIP_END
        
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
            day_date = self.current_week_start + timedelta(days=day)
            
            # Skip if outside semester
            if not self._is_in_semester(day_date):
                continue
                
            # Get fixed schedule for this day
            events = FIXED_SCHEDULE.get(day, [])
            
            for event in events:
                # Check if event should be shown (e.g., internship ended)
                if 'ends' in event and day_date > event['ends']:
                    continue
                    
                self._add_event_to_grid(event, day)
                
            # Also get custom events from database
            try:
                custom_events = task_manager.get_schedule_events(day)
                for event in custom_events:
                    self._add_event_to_grid(event, day)
            except:
                pass
                
    def _add_event_to_grid(self, event: dict, day: int):
        """Add a single event to the grid"""
        start_time = event.get('start', event.get('start_time', '09:00'))
        end_time = event.get('end', event.get('end_time', '10:00'))
        title = event.get('title', '')
        color = event.get('color', '66, 133, 244')
        
        # Parse times
        try:
            start_hour = int(start_time.split(':')[0])
            start_min = int(start_time.split(':')[1])
            end_hour = int(end_time.split(':')[0])
            end_min = int(end_time.split(':')[1])
        except:
            return
        
        # Calculate grid position
        col = day + 1
        row = start_hour - 7 + 1  # Offset for header and 7 AM start
        
        # Calculate span (in hours, rounded up)
        start_total = start_hour * 60 + start_min
        end_total = end_hour * 60 + end_min
        span = max(1, (end_total - start_total + 30) // 60)
        
        if row < 1 or row > 13:
            return
            
        # Create event widget
        event_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        event_box.add_css_class("schedule-event")
        
        css = Gtk.CssProvider()
        css.load_from_data(f"box {{ background: rgba({color}, 0.85); border-radius: 6px; }}".encode())
        event_box.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        title_label = Gtk.Label(label=title)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        title_label.add_css_class("heading")
        event_box.append(title_label)
        
        time_label = Gtk.Label(label=f"{start_time}-{end_time}")
        time_label.add_css_class("caption")
        time_label.set_halign(Gtk.Align.START)
        event_box.append(time_label)
        
        self.grid.attach(event_box, col, row, 1, span)
