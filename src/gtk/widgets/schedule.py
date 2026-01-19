"""
Weekly Schedule Widget - GTK4
Teams-style weekly schedule with correct times and event handling
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gdk, GObject
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager


# Semester configuration
SEMESTER_START = datetime(2026, 1, 12)  # 12 de enero
SEMESTER_END = datetime(2026, 5, 16)    # 16 de mayo
INTERNSHIP_END = datetime(2026, 2, 14)  # Pasantías hasta 14 de febrero

# Fixed schedule - CORRECT TIMES
# Format: {"start": "HH:MM", "end": "HH:MM", "title": "...", "color": "R, G, B"}
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
        {"start": "08:30", "end": "13:30", "title": "PASANTÍAS", "color": "255, 87, 34", "internship": True},
        {"start": "14:00", "end": "18:00", "title": "PASEC", "color": "156, 39, 176"},
    ],
    5: [],  # Sábado
    6: [],  # Domingo
}


class AddEventDialog(Adw.Window):
    """Dialog to add a new schedule event"""
    
    __gsignals__ = {
        'event-added': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, parent=None, default_day=0, default_hour=9):
        super().__init__()
        self.set_title("Nuevo Evento")
        self.set_default_size(400, 450)
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
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
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
        
        # Description (optional)
        desc_group = Adw.PreferencesGroup()
        self.desc_entry = Adw.EntryRow()
        self.desc_entry.set_title("Descripción (opcional)")
        desc_group.add(self.desc_entry)
        content.append(desc_group)
        
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
        self.start_row.set_title("Inicio (HH:MM)")
        self.start_row.set_text(f"{self.default_hour:02d}:00")
        time_group.add(self.start_row)
        
        self.end_row = Adw.EntryRow()
        self.end_row.set_title("Fin (HH:MM)")
        self.end_row.set_text(f"{self.default_hour + 1:02d}:00")
        time_group.add(self.end_row)
        
        content.append(time_group)
        
        # Recurring options
        recur_group = Adw.PreferencesGroup()
        recur_group.set_title("Repetir")
        
        self.recurring_switch = Adw.SwitchRow()
        self.recurring_switch.set_title("Evento recurrente")
        self.recurring_switch.set_subtitle("Se repite cada semana")
        recur_group.add(self.recurring_switch)
        
        content.append(recur_group)
        
        # Color picker
        color_group = Adw.PreferencesGroup()
        color_group.set_title("Color")
        
        color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        color_box.set_margin_top(8)
        
        colors = [
            ("66, 133, 244", "#4285f4"),   # Blue
            ("52, 168, 83", "#34a853"),     # Green
            ("251, 188, 5", "#fbbc05"),     # Yellow
            ("234, 67, 53", "#ea4335"),     # Red
            ("156, 39, 176", "#9c27b0"),    # Purple
        ]
        
        self.selected_color = colors[0][0]
        self.color_buttons = []
        
        for rgb, hex_color in colors:
            btn = Gtk.ToggleButton()
            btn.set_size_request(32, 32)
            css = Gtk.CssProvider()
            css.load_from_data(f"button {{ background: {hex_color}; border-radius: 50%; }}".encode())
            btn.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            btn.connect("toggled", self._on_color_selected, rgb)
            color_box.append(btn)
            self.color_buttons.append(btn)
            
        self.color_buttons[0].set_active(True)
        color_group.add(color_box)
        content.append(color_group)
        
        main_box.append(content)
        
    def _on_color_selected(self, btn, color):
        """Handle color selection"""
        if btn.get_active():
            self.selected_color = color
            for b in self.color_buttons:
                if b != btn:
                    b.set_active(False)
                    
    def _on_save(self, btn):
        """Save the event"""
        title = self.title_entry.get_text()
        if not title:
            self.title_entry.add_css_class("error")
            return
            
        event = {
            'title': title,
            'description': self.desc_entry.get_text(),
            'day': self.day_row.get_selected(),
            'start_time': self.start_row.get_text(),
            'end_time': self.end_row.get_text(),
            'recurring': self.recurring_switch.get_active(),
            'color': self.selected_color
        }
        
        try:
            task_manager.add_schedule_event(event)
        except Exception as e:
            print(f"Error saving event: {e}")
            
        self.emit("event-added")
        self.close()


class WeeklySchedule(Gtk.Box):
    """Weekly schedule grid with proper event layout"""
    
    HOUR_HEIGHT = 50  # Pixels per hour
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)
        
        self.current_week_start = self._get_week_start(datetime.now())
        self.custom_events = []
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
        add_btn.connect("clicked", lambda _: self._show_add_dialog(0, 9))
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
        
        # Schedule container
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Use overlay for event positioning
        self.schedule_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        scroll.set_child(self.schedule_box)
        
        self.append(scroll)
        
    def _show_add_dialog(self, day, hour):
        """Show add event dialog"""
        dialog = AddEventDialog(parent=self.get_root(), default_day=day, default_hour=hour)
        dialog.connect("event-added", lambda d: self.refresh())
        dialog.present()
        
    def _prev_week(self, btn):
        self.current_week_start -= timedelta(days=7)
        self.refresh()
        
    def _next_week(self, btn):
        self.current_week_start += timedelta(days=7)
        self.refresh()
        
    def _go_today(self, btn):
        self.current_week_start = self._get_week_start(datetime.now())
        self.refresh()
        
    def _is_in_semester(self, date: datetime) -> bool:
        return SEMESTER_START <= date <= SEMESTER_END
        
    def _is_internship_active(self, date: datetime) -> bool:
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
        
        # Clear schedule
        while True:
            child = self.schedule_box.get_first_child()
            if child:
                self.schedule_box.remove(child)
            else:
                break
                
        # Time column
        time_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        time_col.set_size_request(60, -1)
        
        # Empty header
        header_spacer = Gtk.Label(label="")
        header_spacer.set_size_request(60, 40)
        time_col.append(header_spacer)
        
        # Time labels
        for hour in range(7, 20):
            time_label = Gtk.Label(label=f"{hour:02d}:00")
            time_label.add_css_class("dim-label")
            time_label.add_css_class("caption")
            time_label.set_size_request(60, self.HOUR_HEIGHT)
            time_label.set_valign(Gtk.Align.START)
            time_col.append(time_label)
            
        self.schedule_box.append(time_col)
        
        # Day columns
        today = datetime.now().date()
        day_names = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        
        for day in range(7):
            day_date = self.current_week_start + timedelta(days=day)
            is_today = day_date.date() == today
            
            day_col = self._create_day_column(day, day_names[day], day_date, is_today)
            self.schedule_box.append(day_col)
            
    def _create_day_column(self, day_index: int, day_name: str, day_date: datetime, is_today: bool) -> Gtk.Box:
        """Create a day column with events"""
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        col.set_hexpand(True)
        col.set_size_request(100, -1)
        
        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        header.set_size_request(-1, 40)
        if is_today:
            header.add_css_class("accent-button")
        
        name_label = Gtk.Label(label=day_name)
        name_label.add_css_class("caption")
        header.append(name_label)
        
        date_label = Gtk.Label(label=str(day_date.day))
        date_label.add_css_class("title-4" if is_today else "dim-label")
        header.append(date_label)
        
        col.append(header)
        
        # Time grid with events overlay
        overlay = Gtk.Overlay()
        overlay.set_vexpand(True)
        
        # Background grid (clickable cells)
        grid_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        for hour in range(7, 20):
            cell = Gtk.Button()
            cell.add_css_class("flat")
            cell.set_size_request(-1, self.HOUR_HEIGHT)
            css = Gtk.CssProvider()
            css.load_from_data(b"button { border-bottom: 1px solid alpha(white, 0.05); border-radius: 0; }")
            cell.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            cell.connect("clicked", lambda b, d=day_index, h=hour: self._show_add_dialog(d, h))
            grid_box.append(cell)
            
        overlay.set_child(grid_box)
        
        # Events layer
        events_box = Gtk.Fixed()
        events_box.set_size_request(-1, self.HOUR_HEIGHT * 13)
        
        # Get events for this day
        events = self._get_events_for_day(day_index, day_date)
        
        # Group overlapping events
        event_groups = self._group_overlapping_events(events)
        
        for group in event_groups:
            num_in_group = len(group)
            for i, event in enumerate(group):
                widget = self._create_event_widget(event, num_in_group, i)
                y_pos = self._time_to_y(event['start'])
                events_box.put(widget, 0, y_pos)
                
        overlay.add_overlay(events_box)
        col.append(overlay)
        
        return col
        
    def _get_events_for_day(self, day_index: int, day_date: datetime) -> list:
        """Get all events for a specific day"""
        events = []
        
        # Skip if outside semester
        if not self._is_in_semester(day_date):
            return events
            
        # Fixed schedule
        for ev in FIXED_SCHEDULE.get(day_index, []):
            # Skip internship if past its end date
            if ev.get('internship') and not self._is_internship_active(day_date):
                continue
            events.append(ev.copy())
            
        # Custom events from database
        try:
            custom = task_manager.get_schedule_events(day_index)
            for ev in custom:
                events.append({
                    'start': ev.get('start_time', '09:00'),
                    'end': ev.get('end_time', '10:00'),
                    'title': ev.get('title', ''),
                    'color': ev.get('color', '66, 133, 244')
                })
        except:
            pass
            
        return events
        
    def _group_overlapping_events(self, events: list) -> list:
        """Group events that overlap in time"""
        if not events:
            return []
            
        # Sort by start time
        sorted_events = sorted(events, key=lambda e: self._time_to_minutes(e['start']))
        
        groups = []
        current_group = [sorted_events[0]]
        current_end = self._time_to_minutes(sorted_events[0]['end'])
        
        for event in sorted_events[1:]:
            start = self._time_to_minutes(event['start'])
            end = self._time_to_minutes(event['end'])
            
            if start < current_end:  # Overlaps
                current_group.append(event)
                current_end = max(current_end, end)
            else:
                groups.append(current_group)
                current_group = [event]
                current_end = end
                
        groups.append(current_group)
        return groups
        
    def _time_to_minutes(self, time_str: str) -> int:
        """Convert HH:MM to minutes from midnight"""
        parts = time_str.split(':')
        return int(parts[0]) * 60 + int(parts[1])
        
    def _time_to_y(self, time_str: str) -> int:
        """Convert time to Y position"""
        minutes = self._time_to_minutes(time_str)
        hours_from_7 = (minutes - 7 * 60) / 60
        return int(hours_from_7 * self.HOUR_HEIGHT)
        
    def _create_event_widget(self, event: dict, num_in_slot: int, slot_index: int) -> Gtk.Box:
        """Create an event widget with proper sizing"""
        start = self._time_to_minutes(event['start'])
        end = self._time_to_minutes(event['end'])
        duration_hours = (end - start) / 60
        height = int(duration_hours * self.HOUR_HEIGHT) - 4
        
        # Width calculation for overlapping events
        base_width = 90
        width = base_width // num_in_slot
        x_offset = width * slot_index
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_size_request(width, height)
        box.set_margin_start(x_offset + 2)
        box.set_margin_end(2)
        box.set_margin_top(2)
        
        color = event.get('color', '66, 133, 244')
        css = Gtk.CssProvider()
        css.load_from_data(f"""
            box {{
                background: rgba({color}, 0.9);
                border-radius: 6px;
                padding: 4px 6px;
            }}
        """.encode())
        box.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        title = Gtk.Label(label=event['title'])
        title.set_halign(Gtk.Align.START)
        title.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        title.add_css_class("heading")
        box.append(title)
        
        if height > 30:
            time_label = Gtk.Label(label=f"{event['start']}-{event['end']}")
            time_label.add_css_class("caption")
            time_label.set_halign(Gtk.Align.START)
            box.append(time_label)
        
        return box
