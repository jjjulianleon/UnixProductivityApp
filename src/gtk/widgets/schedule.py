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

# Fixed schedule
FIXED_SCHEDULE = {
    0: [  # Lunes
        {"start": "13:00", "end": "14:20", "title": "Data Mining", "color": "#4285f4"},
        {"start": "14:30", "end": "15:50", "title": "Redes Lab", "color": "#34a853"},
    ],
    1: [  # Martes
        {"start": "10:00", "end": "11:20", "title": "Bases de Datos", "color": "#fbbc05"},
        {"start": "13:00", "end": "14:20", "title": "Redes", "color": "#34a853"},
        {"start": "14:30", "end": "15:50", "title": "Mercados Int.", "color": "#ea4335"},
        {"start": "16:00", "end": "18:00", "title": "PASEC", "color": "#9c27b0"},
    ],
    2: [  # Miércoles
        {"start": "13:00", "end": "14:20", "title": "Data Mining", "color": "#4285f4"},
        {"start": "14:30", "end": "15:50", "title": "PASEC Teoría", "color": "#9c27b0"},
    ],
    3: [  # Jueves
        {"start": "10:00", "end": "11:20", "title": "Bases de Datos", "color": "#fbbc05"},
        {"start": "13:00", "end": "14:20", "title": "Redes", "color": "#34a853"},
        {"start": "14:30", "end": "15:50", "title": "Mercados Int.", "color": "#ea4335"},
    ],
    4: [  # Viernes
        {"start": "08:30", "end": "13:30", "title": "PASANTÍAS", "color": "#ff5722", "internship": True},
        {"start": "14:00", "end": "18:00", "title": "PASEC", "color": "#9c27b0"},
    ],
    5: [],
    6: [],
}


class AddEventDialog(Adw.Window):
    """Dialog to add a schedule event"""
    
    __gsignals__ = {
        'event-added': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, parent=None, default_day=0, default_hour=9):
        super().__init__()
        self.set_title("Nuevo Evento")
        self.set_default_size(400, 400)
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
        group1 = Adw.PreferencesGroup()
        group1.add(self.title_entry)
        content.append(group1)
        
        # Day
        self.day_row = Adw.ComboRow()
        self.day_row.set_title("Día")
        self.day_row.set_model(Gtk.StringList.new(["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]))
        self.day_row.set_selected(default_day)
        group2 = Adw.PreferencesGroup()
        group2.add(self.day_row)
        content.append(group2)
        
        # Time
        self.start_entry = Adw.EntryRow()
        self.start_entry.set_title("Inicio (HH:MM)")
        self.start_entry.set_text(f"{default_hour:02d}:00")
        
        self.end_entry = Adw.EntryRow()
        self.end_entry.set_title("Fin (HH:MM)")
        self.end_entry.set_text(f"{default_hour+1:02d}:00")
        
        group3 = Adw.PreferencesGroup()
        group3.add(self.start_entry)
        group3.add(self.end_entry)
        content.append(group3)
        
        # Recurring
        self.recurring = Adw.SwitchRow()
        self.recurring.set_title("Repetir cada semana")
        group4 = Adw.PreferencesGroup()
        group4.add(self.recurring)
        content.append(group4)
        
        main_box.append(content)
        
    def _on_save(self, btn):
        title = self.title_entry.get_text()
        if not title:
            return
        try:
            task_manager.add_schedule_event({
                'title': title,
                'day': self.day_row.get_selected(),
                'start_time': self.start_entry.get_text(),
                'end_time': self.end_entry.get_text(),
                'recurring': self.recurring.get_active(),
                'color': '#4285f4'
            })
        except:
            pass
        self.emit("event-added")
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
            
            # Day cells
            for col in range(1, 8):
                cell = Gtk.Button()
                cell.add_css_class("flat")
                cell.set_size_request(100, self.HOUR_HEIGHT)
                cell.connect("clicked", lambda b, d=col-1, h=hour: self._show_add_dialog(d, h))
                self.grid.attach(cell, col, row, 1, 1)
                
        # Add events
        for day in range(7):
            day_date = self.current_week_start + timedelta(days=day)
            self._add_day_events(day, day_date)
            
    def _add_day_events(self, day_index, day_date):
        if not (SEMESTER_START <= day_date <= SEMESTER_END):
            return
            
        events = FIXED_SCHEDULE.get(day_index, [])
        
        for event in events:
            if event.get('internship') and day_date > INTERNSHIP_END:
                continue
            self._add_event_widget(day_index, event)
            
    def _add_event_widget(self, day_index, event):
        start_hour = int(event['start'].split(':')[0])
        start_min = int(event['start'].split(':')[1])
        end_hour = int(event['end'].split(':')[0])
        end_min = int(event['end'].split(':')[1])
        
        row = start_hour - 7 + 1
        duration_mins = (end_hour * 60 + end_min) - (start_hour * 60 + start_min)
        span = max(1, round(duration_mins / 60))
        
        if row < 1 or row > 13:
            return
            
        col = day_index + 1
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_valign(Gtk.Align.FILL)
        box.set_halign(Gtk.Align.FILL)
        
        color = event.get('color', '#4285f4')
        css = Gtk.CssProvider()
        css.load_from_data(f"""
            box {{
                background: {color};
                border-radius: 6px;
                padding: 4px 6px;
                margin: 2px;
            }}
            label {{
                color: white;
            }}
        """.encode())
        box.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        title = Gtk.Label(label=event['title'])
        title.set_halign(Gtk.Align.START)
        title.set_ellipsize(3)
        title.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        box.append(title)
        
        time_str = f"{event['start']}-{event['end']}"
        time_lbl = Gtk.Label(label=time_str)
        time_lbl.add_css_class("caption")
        time_lbl.set_halign(Gtk.Align.START)
        time_lbl.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        box.append(time_lbl)
        
        self.grid.attach(box, col, row, 1, span)
