"""
Weekly Schedule Widget - GTK4
Clean implementation with translucent today header
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
SEMESTER_START = datetime(2026, 1, 12)
SEMESTER_END = datetime(2026, 5, 16)
INTERNSHIP_END = datetime(2026, 2, 14)


class AddEventDialog(Adw.Window):
    """Dialog to add or edit a schedule event"""

    __gsignals__ = {
        'event-added': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'event-deleted': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, parent=None, default_day=0, default_hour=9, event=None):
        super().__init__()
        self.event = event
        self.is_edit = event is not None
        self.set_title("Editar Evento" if self.is_edit else "Nuevo Evento")
        self.set_default_size(400, 450)
        self.set_modal(True)
        if parent:
            self.set_transient_for(parent)
        self._setup_ui(default_day, default_hour)
        
    def _setup_ui(self, default_day, default_hour):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)

        header = Adw.HeaderBar()
        header.add_css_class("flat")

        cancel_btn = Gtk.Button(label="Cancelar")
        cancel_btn.connect("clicked", lambda _: self.close())
        header.pack_start(cancel_btn)

        # Delete button (only for editing)
        if self.is_edit:
            delete_btn = Gtk.Button(label="Eliminar")
            delete_btn.add_css_class("destructive-action")
            delete_btn.connect("clicked", self._on_delete)
            header.pack_start(delete_btn)

        save_btn = Gtk.Button(label="Guardar")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save)
        header.pack_end(save_btn)

        main_box.append(header)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)

        # Title
        self.title_entry = Adw.EntryRow()
        self.title_entry.set_title("Nombre")
        if self.event:
            self.title_entry.set_text(self.event.get('title', ''))
        group1 = Adw.PreferencesGroup()
        group1.add(self.title_entry)
        content.append(group1)

        # Day
        self.day_row = Adw.ComboRow()
        self.day_row.set_title("Día")
        self.day_row.set_model(Gtk.StringList.new(["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]))
        if self.event:
            self.day_row.set_selected(self.event.get('day_of_week', default_day))
        else:
            self.day_row.set_selected(default_day)
        group2 = Adw.PreferencesGroup()
        group2.add(self.day_row)
        content.append(group2)

        # Time
        self.start_entry = Adw.EntryRow()
        self.start_entry.set_title("Inicio (HH:MM)")
        if self.event:
            self.start_entry.set_text(self.event.get('start', f"{default_hour:02d}:00"))
        else:
            self.start_entry.set_text(f"{default_hour:02d}:00")

        self.end_entry = Adw.EntryRow()
        self.end_entry.set_title("Fin (HH:MM)")
        if self.event:
            self.end_entry.set_text(self.event.get('end', f"{default_hour+1:02d}:00"))
        else:
            self.end_entry.set_text(f"{default_hour+1:02d}:00")

        group3 = Adw.PreferencesGroup()
        group3.add(self.start_entry)
        group3.add(self.end_entry)
        content.append(group3)

        # Recurring
        self.recurring = Adw.SwitchRow()
        self.recurring.set_title("Repetir cada semana")
        if self.event:
            self.recurring.set_active(self.event.get('recurring', 1) == 1)
        group4 = Adw.PreferencesGroup()
        group4.add(self.recurring)
        content.append(group4)
        
        # Color picker
        self.color_row = Adw.ComboRow()
        self.color_row.set_title("Color")
        colors_list = Gtk.StringList.new([
            "🔵 Azul",
            "🟢 Verde",
            "🟡 Amarillo",
            "🔴 Rojo",
            "🟣 Morado",
            "🟠 Naranja"
        ])
        self.color_row.set_model(colors_list)
        # Set current color if editing
        if self.event:
            colors = ['#4285f4', '#34a853', '#fbbc05', '#ea4335', '#9c27b0', '#ff5722']
            event_color = self.event.get('color', '#4285f4')
            if event_color in colors:
                self.color_row.set_selected(colors.index(event_color))
        group5 = Adw.PreferencesGroup()
        group5.add(self.color_row)
        content.append(group5)

        main_box.append(content)

    def _on_save(self, btn):
        title = self.title_entry.get_text()
        if not title:
            return

        # Color mapping
        colors = ['#4285f4', '#34a853', '#fbbc05', '#ea4335', '#9c27b0', '#ff5722']
        selected_color = colors[self.color_row.get_selected()]

        try:
            if self.is_edit and self.event.get('id'):
                # Update existing event
                task_manager.update_schedule_event(
                    self.event['id'],
                    title=title,
                    day_of_week=self.day_row.get_selected(),
                    start_time=self.start_entry.get_text(),
                    end_time=self.end_entry.get_text(),
                    color=selected_color
                )
            else:
                # Add new event
                recurring = 1 if self.recurring.get_active() else 0
                task_manager.add_schedule_event(
                    title=title,
                    day_of_week=self.day_row.get_selected(),
                    start_time=self.start_entry.get_text(),
                    end_time=self.end_entry.get_text(),
                    color=selected_color,
                    recurring=recurring
                )
        except Exception as e:
            print(f"Error saving event: {e}")

        self.emit("event-added")
        self.close()

    def _on_delete(self, btn):
        if self.event and self.event.get('id'):
            try:
                from src.core.database import db
                db.delete_schedule_event(self.event['id'])
            except Exception as e:
                print(f"Error deleting event: {e}")
            self.emit("event-deleted")
        self.close()


class WeeklySchedule(Gtk.Box):
    """Weekly schedule grid"""
    
    HOUR_HEIGHT = 50
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)
        
        self.current_week_start = self._get_week_start(datetime.now())
        self._setup_ui()
        self.refresh()
        
    def _get_week_start(self, date):
        return date - timedelta(days=date.weekday())
        
    def _setup_ui(self):
        # Nav bar - NO extra + button here, only in nav row
        nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        prev_btn = Gtk.Button()
        prev_btn.set_icon_name("go-previous-symbolic")
        prev_btn.add_css_class("circular")
        prev_btn.add_css_class("flat")
        prev_btn.connect("clicked", lambda _: self._change_week(-7))
        nav.append(prev_btn)
        
        today_btn = Gtk.Button(label="Hoy")
        today_btn.add_css_class("flat")
        today_btn.connect("clicked", lambda _: self._go_today())
        nav.append(today_btn)
        
        add_btn = Gtk.Button()
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.add_css_class("suggested-action")
        add_btn.add_css_class("circular")
        add_btn.connect("clicked", lambda _: self._show_add_dialog(0, 9))
        nav.append(add_btn)
        
        self.week_label = Gtk.Label()
        self.week_label.add_css_class("title-4")
        self.week_label.set_hexpand(True)
        nav.append(self.week_label)
        
        next_btn = Gtk.Button()
        next_btn.set_icon_name("go-next-symbolic")
        next_btn.add_css_class("circular")
        next_btn.add_css_class("flat")
        next_btn.connect("clicked", lambda _: self._change_week(7))
        nav.append(next_btn)
        
        self.append(nav)
        
        # Schedule grid
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(False)
        self.grid.set_row_spacing(1)
        self.grid.set_column_spacing(1)
        scroll.set_child(self.grid)
        
        self.append(scroll)
        
    def _change_week(self, days):
        self.current_week_start += timedelta(days=days)
        self.refresh()
        
    def _go_today(self):
        self.current_week_start = self._get_week_start(datetime.now())
        self.refresh()
        
    def _show_add_dialog(self, day, hour):
        dialog = AddEventDialog(parent=self.get_root(), default_day=day, default_hour=hour)
        dialog.connect("event-added", lambda d: self.refresh())
        dialog.present()
        
    def refresh(self):
        # Update label
        week_end = self.current_week_start + timedelta(days=6)
        months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        self.week_label.set_text(
            f"{self.current_week_start.day} {months[self.current_week_start.month-1]} - "
            f"{week_end.day} {months[week_end.month-1]} {week_end.year}"
        )
        
        # Clear grid
        while child := self.grid.get_first_child():
            self.grid.remove(child)
            
        today = datetime.now().date()
        
        # Time column header (empty)
        self.grid.attach(Gtk.Label(label=""), 0, 0, 1, 1)
        
        # Day headers
        day_names = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for col, name in enumerate(day_names, start=1):
            day_date = self.current_week_start + timedelta(days=col-1)
            is_today = day_date.date() == today
            
            header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            header.set_size_request(100, 40)
            header.set_halign(Gtk.Align.FILL)
            header.set_valign(Gtk.Align.FILL)
            
            if is_today:
                # Translucent highlight for today - entire header
                css = Gtk.CssProvider()
                css.load_from_data(b"""
                    box {
                        background: alpha(@accent_color, 0.25);
                        border-radius: 8px;
                        padding: 4px;
                    }
                """)
                header.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
                
            name_lbl = Gtk.Label(label=name)
            name_lbl.add_css_class("caption")
            header.append(name_lbl)
            
            date_lbl = Gtk.Label(label=str(day_date.day))
            date_lbl.add_css_class("title-4" if is_today else "dim-label")
            header.append(date_lbl)
            
            self.grid.attach(header, col, 0, 1, 1)
            
        # Time rows
        for row, hour in enumerate(range(7, 20), start=1):
            # Time label
            time_lbl = Gtk.Label(label=f"{hour:02d}:00")
            time_lbl.add_css_class("dim-label")
            time_lbl.set_size_request(50, self.HOUR_HEIGHT)
            self.grid.attach(time_lbl, 0, row, 1, 1)
            
            # Day cells with hour separator line
            for col in range(1, 8):
                cell = Gtk.Button()
                cell.add_css_class("flat")
                cell.set_size_request(100, self.HOUR_HEIGHT)
                cell.connect("clicked", lambda b, d=col-1, h=hour: self._show_add_dialog(d, h))
                
                # Add bottom border for hour separation
                css = Gtk.CssProvider()
                css.load_from_data(b"button { border-bottom: 1px solid alpha(white, 0.1); border-radius: 0; }")
                cell.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
                
                self.grid.attach(cell, col, row, 1, 1)
                
        # Add events
        for day in range(7):
            day_date = self.current_week_start + timedelta(days=day)
            self._add_day_events(day, day_date)
            
    def _add_day_events(self, day_index, day_date):
        """Load and display events for a specific day with overlap handling"""
        events_to_show = []

        # Load from Database only (FIXED_SCHEDULE removed)
        db_events = task_manager.get_schedule_events(day_index)
        for event in db_events:
            # Check if event is recurring or one-time
            is_recurring = event.get('recurring', 1) == 1
            event_date_str = event.get('event_date')

            if not is_recurring and event_date_str:
                # Non-recurring event: only show on the specific date
                try:
                    event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
                    if day_date.date() != event_date:
                        continue  # Skip if not the right date
                except ValueError:
                    continue  # Skip if date is invalid

            # Filter internship events after deadline
            title_lower = event.get('title', '').lower()
            is_internship = any(kw in title_lower for kw in ['pasant', 'trabajo', 'intern', 'work'])
            if is_internship and day_date > INTERNSHIP_END:
                continue

            # Match the format expected by _add_event_widget
            formatted_event = {
                'id': event.get('id'),
                'title': event['title'],
                'start': event['start_time'],
                'end': event['end_time'],
                'color': event['color'],
                'day_of_week': event.get('day_of_week', day_index),
                'recurring': event.get('recurring', 1),
                'is_db_event': True
            }
            events_to_show.append(formatted_event)

        # Group overlapping events and add them with proper layout
        if events_to_show:
            self._add_events_with_overlap_handling(day_index, events_to_show)

    def _events_overlap(self, e1, e2):
        """Check if two events overlap in time"""
        def to_mins(t):
            h, m = map(int, t.split(':'))
            return h * 60 + m

        start1, end1 = to_mins(e1['start']), to_mins(e1['end'])
        start2, end2 = to_mins(e2['start']), to_mins(e2['end'])
        return start1 < end2 and start2 < end1

    def _group_overlapping_events(self, events):
        """Group events that overlap into clusters"""
        if not events:
            return []

        def to_mins(t):
            h, m = map(int, t.split(':'))
            return h * 60 + m

        # Sort by start time
        sorted_events = sorted(events, key=lambda e: to_mins(e['start']))

        groups = []
        current_group = [sorted_events[0]]
        group_end = to_mins(sorted_events[0]['end'])

        for evt in sorted_events[1:]:
            evt_start = to_mins(evt['start'])
            evt_end = to_mins(evt['end'])

            if evt_start < group_end:
                # Overlaps with current group
                current_group.append(evt)
                group_end = max(group_end, evt_end)
            else:
                # New group
                groups.append(current_group)
                current_group = [evt]
                group_end = evt_end

        groups.append(current_group)
        return groups

    def _add_events_with_overlap_handling(self, day_index, events):
        """Add events with horizontal splitting for overlaps"""
        groups = self._group_overlapping_events(events)

        for group in groups:
            num_cols = len(group)
            for col_idx, event in enumerate(group):
                self._add_event_widget(day_index, event, col_idx, num_cols)

    def _add_event_widget(self, day_index, event, col_idx=0, num_cols=1):
        start_hour = int(event['start'].split(':')[0])
        start_min = int(event['start'].split(':')[1])
        end_hour = int(event['end'].split(':')[0])
        end_min = int(event['end'].split(':')[1])

        row = start_hour - 7 + 1
        duration_mins = (end_hour * 60 + end_min) - (start_hour * 60 + start_min)

        # Calculate span based on which hour rows the event covers
        # An event from 08:30-09:50 covers rows for 08:00 and 09:00 (span=2)
        start_total_mins = start_hour * 60 + start_min
        end_total_mins = end_hour * 60 + end_min

        # Calculate how many hour rows this event spans
        first_row_hour = start_hour
        last_row_hour = end_hour if end_min > 0 else end_hour - 1
        span = max(1, last_row_hour - first_row_hour + 1)

        # Calculate pixel-based positioning for precise placement
        # margin_top: offset within the starting hour cell (based on start_min)
        # height: actual duration in pixels
        pixels_per_min = self.HOUR_HEIGHT / 60.0
        margin_top_offset = int(start_min * pixels_per_min)
        event_height = int(duration_mins * pixels_per_min)

        if row < 1 or row > 13:
            return

        col = day_index + 1
        color = event.get('color', '#4285f4')

        # Calculate width based on number of overlapping events
        base_width = 100
        event_width = base_width // num_cols
        margin_left = col_idx * event_width

        # Helper to parse color safely (supports #RRGGBB and "R, G, B")
        def parse_color(c):
            if c.startswith('#'):
                try:
                    r = int(c[1:3], 16)
                    g = int(c[3:5], 16)
                    b = int(c[5:7], 16)
                    return r, g, b
                except:
                    return 66, 133, 244
            elif ',' in c:
                try:
                    parts = [int(p.strip()) for p in c.split(',')]
                    return parts[0], parts[1], parts[2]
                except:
                    return 66, 133, 244
            return 66, 133, 244

        r, g, b = parse_color(color)

        # Create the event widget (button for DB events, box otherwise)
        widget = Gtk.Button()
        widget.set_valign(Gtk.Align.START)
        widget.set_halign(Gtk.Align.START if num_cols > 1 else Gtk.Align.FILL)
        widget.set_size_request(event_width - 2, event_height)

        if event.get('is_db_event'):
            widget.connect("clicked", lambda btn, e=event: self._on_event_clicked(e))

        css = Gtk.CssProvider()
        css.load_from_data(f"""
            button {{
                background: rgba({r}, {g}, {b}, 0.8);
                border-radius: 4px;
                padding: 2px 4px;
                margin-left: {margin_left}px;
                margin-right: 1px;
                margin-top: {margin_top_offset}px;
                margin-bottom: 1px;
                border-left: 3px solid rgb({r}, {g}, {b});
                border-top: none;
                border-right: none;
                border-bottom: none;
                min-width: {event_width - 6}px;
                max-width: {event_width - 2}px;
                min-height: {event_height - 2}px;
            }}
            button:hover {{
                background: rgba({r}, {g}, {b}, 0.95);
            }}
            label {{
                color: white;
                font-size: 9px;
            }}
        """.encode())
        widget.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_lbl = Gtk.Label(label=event['title'])
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.set_ellipsize(3)
        title_lbl.set_max_width_chars(10 if num_cols > 1 else 15)
        title_lbl.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        box.append(title_lbl)

        # Show time for events with enough height
        if event_height >= 40:
            time_str = f"{event['start']}-{event['end']}"
            time_lbl = Gtk.Label(label=time_str)
            time_lbl.add_css_class("caption")
            time_lbl.set_halign(Gtk.Align.START)
            time_lbl.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            box.append(time_lbl)

        widget.set_child(box)
        self.grid.attach(widget, col, row, 1, span)

    def _on_event_clicked(self, event):
        """Open edit dialog for DB event"""
        dialog = AddEventDialog(
            parent=self.get_root(),
            default_day=event.get('day_of_week', 0),
            default_hour=int(event.get('start', '09:00').split(':')[0]),
            event=event
        )
        dialog.connect("event-added", lambda d: self.refresh())
        dialog.connect("event-deleted", lambda d: self.refresh())
        dialog.present()
