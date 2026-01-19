#!/usr/bin/env python3
"""
Desktop Widget - GTK4 Version
Compact widget for desktop showing calendar, tasks, and quick actions
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gdk
from datetime import datetime, timedelta
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.core.task_manager import task_manager


class WidgetApp(Adw.Application):
    """Compact desktop widget application"""
    
    def __init__(self):
        super().__init__(application_id="com.jjjulianleon.productivitywidget")
        
    def do_activate(self):
        self.window = WidgetWindow(application=self)
        self._load_css()
        self.window.present()
        
    def _load_css(self):
        css = Gtk.CssProvider()
        css.load_from_data(b"""
            window.widget-window {
                background-color: alpha(@window_bg_color, 0.75);
            }
            
            .widget-card {
                background-color: alpha(@card_bg_color, 0.5);
                border-radius: 12px;
                padding: 12px;
            }
            
            .widget-header {
                font-size: 10px;
            }
            
            .today-highlight {
                background-color: alpha(@accent_color, 0.25);
                border-radius: 50%;
                font-weight: bold;
            }
            
            .deadline-dot {
                color: #ea4335;
                font-size: 6px;
            }
            
            .task-row {
                padding: 6px 8px;
                border-radius: 6px;
            }
            
            .task-row:hover {
                background-color: alpha(white, 0.08);
            }
            
            .priority-alta { border-left: 3px solid #ea4335; }
            .priority-media { border-left: 3px solid #fbbc05; }
            .priority-baja { border-left: 3px solid #34a853; }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


class WidgetWindow(Adw.ApplicationWindow):
    """Compact widget window"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Productivity Widget")
        self.set_default_size(480, 320)
        self.add_css_class("widget-window")
        
        # Enable dragging
        self._setup_drag()
        self._setup_ui()
        self._start_clock()
        
    def _setup_drag(self):
        """Allow dragging the widget"""
        gesture = Gtk.GestureDrag()
        gesture.connect("drag-begin", self._on_drag_begin)
        gesture.connect("drag-update", self._on_drag_update)
        self.add_controller(gesture)
        
    def _on_drag_begin(self, gesture, x, y):
        surface = self.get_surface()
        if surface:
            self._start_x, self._start_y = surface.get_position()
            
    def _on_drag_update(self, gesture, offset_x, offset_y):
        surface = self.get_surface()
        if surface and hasattr(self, '_start_x'):
            # Note: Moving windows is limited in Wayland
            pass
        
    def _setup_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        
        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        self.time_label = Gtk.Label()
        self.time_label.add_css_class("widget-header")
        self.time_label.add_css_class("dim-label")
        header.append(self.time_label)
        
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header.append(spacer)
        
        # Open main app button
        app_btn = Gtk.Button()
        app_btn.set_icon_name("go-next-symbolic")
        app_btn.add_css_class("circular")
        app_btn.add_css_class("flat")
        app_btn.set_tooltip_text("Abrir App")
        app_btn.connect("clicked", self._open_main_app)
        header.append(app_btn)
        
        main_box.append(header)
        
        # Content with tabs
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        # Calendar tab
        self.stack.add_titled(self._create_calendar_view(), "calendar", "Calendario")
        
        # Tasks tab
        self.stack.add_titled(self._create_tasks_view(), "tasks", "Tareas")
        
        # Schedule tab
        self.stack.add_titled(self._create_schedule_view(), "schedule", "Horario")
        
        # Tab switcher
        switcher = Gtk.StackSwitcher()
        switcher.set_stack(self.stack)
        switcher.set_halign(Gtk.Align.CENTER)
        main_box.append(switcher)
        
        main_box.append(self.stack)
        
        self.set_content(main_box)
        
    def _create_calendar_view(self) -> Gtk.Box:
        """Create compact calendar view"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_vexpand(True)
        
        # Month header
        self.current_month = datetime.now()
        
        nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        prev_btn = Gtk.Button()
        prev_btn.set_icon_name("go-previous-symbolic")
        prev_btn.add_css_class("flat")
        prev_btn.add_css_class("circular")
        prev_btn.connect("clicked", lambda _: self._change_month(-1))
        nav.append(prev_btn)
        
        self.month_label = Gtk.Label()
        self.month_label.add_css_class("title-4")
        self.month_label.set_hexpand(True)
        nav.append(self.month_label)
        
        next_btn = Gtk.Button()
        next_btn.set_icon_name("go-next-symbolic")
        next_btn.add_css_class("flat")
        next_btn.add_css_class("circular")
        next_btn.connect("clicked", lambda _: self._change_month(1))
        nav.append(next_btn)
        
        box.append(nav)
        
        # Calendar grid
        self.calendar_grid = Gtk.Grid()
        self.calendar_grid.set_column_homogeneous(True)
        self.calendar_grid.set_row_homogeneous(True)
        self.calendar_grid.set_column_spacing(2)
        self.calendar_grid.set_row_spacing(2)
        box.append(self.calendar_grid)
        
        self._update_calendar()
        
        return box
        
    def _change_month(self, delta):
        month = self.current_month.month + delta
        year = self.current_month.year
        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1
        self.current_month = self.current_month.replace(year=year, month=month)
        self._update_calendar()
        
    def _update_calendar(self):
        # Clear grid
        while child := self.calendar_grid.get_first_child():
            self.calendar_grid.remove(child)
            
        months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                  "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        self.month_label.set_text(f"{months[self.current_month.month - 1]} {self.current_month.year}")
        
        # Day headers
        days = ["L", "M", "X", "J", "V", "S", "D"]
        for col, day in enumerate(days):
            lbl = Gtk.Label(label=day)
            lbl.add_css_class("dim-label")
            lbl.add_css_class("caption")
            self.calendar_grid.attach(lbl, col, 0, 1, 1)
            
        # Get deadlines - store tasks by date
        self.deadlines = {}
        try:
            tasks = task_manager.get_tasks_with_deadlines()
            for t in tasks:
                if t.get('deadline') and t.get('status') != 'completado':
                    date_str = t['deadline']
                    if date_str not in self.deadlines:
                        self.deadlines[date_str] = []
                    self.deadlines[date_str].append(t)
        except:
            pass
            
        # Calendar days
        import calendar
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(self.current_month.year, self.current_month.month)
        today = datetime.now()
        
        for row_idx, week in enumerate(month_days):
            for col_idx, day in enumerate(week):
                if day == 0:
                    self.calendar_grid.attach(Gtk.Label(label=""), col_idx, row_idx + 1, 1, 1)
                else:
                    is_today = (day == today.day and 
                                self.current_month.month == today.month and 
                                self.current_month.year == today.year)
                    
                    date_str = f"{self.current_month.year}-{self.current_month.month:02d}-{day:02d}"
                    has_deadline = date_str in self.deadlines
                    
                    # Use button for clickable days
                    day_btn = Gtk.Button()
                    day_btn.add_css_class("flat")
                    
                    day_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    day_box.set_halign(Gtk.Align.CENTER)
                    
                    day_lbl = Gtk.Label(label=str(day))
                    if is_today:
                        day_lbl.add_css_class("today-highlight")
                        day_lbl.set_size_request(24, 24)
                    
                    day_box.append(day_lbl)
                    
                    if has_deadline:
                        dot = Gtk.Label(label="●")
                        dot.add_css_class("deadline-dot")
                        day_box.append(dot)
                        day_btn.connect("clicked", self._on_date_clicked, date_str)
                        day_btn.set_tooltip_text(f"{len(self.deadlines[date_str])} tarea(s)")
                    
                    day_btn.set_child(day_box)
                    self.calendar_grid.attach(day_btn, col_idx, row_idx + 1, 1, 1)
    
    def _on_date_clicked(self, btn, date_str):
        """Show tasks for clicked date"""
        tasks = self.deadlines.get(date_str, [])
        if not tasks:
            return
            
        # Create popover with tasks
        popover = Gtk.Popover()
        popover.set_parent(btn)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(8)
        box.set_margin_end(8)
        
        header = Gtk.Label(label=f"Tareas para {date_str}")
        header.add_css_class("heading")
        box.append(header)
        
        for task in tasks:
            task_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            
            priority = task.get('priority', 'media')
            colors = {'alta': '#ea4335', 'media': '#fbbc05', 'baja': '#34a853'}
            color = colors.get(priority, '#fbbc05')
            
            dot = Gtk.Label(label="●")
            css = Gtk.CssProvider()
            css.load_from_data(f"label {{ color: {color}; }}".encode())
            dot.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            task_row.append(dot)
            
            title = Gtk.Label(label=task.get('title', '')[:35])
            title.set_halign(Gtk.Align.START)
            task_row.append(title)
            
            box.append(task_row)
            
        popover.set_child(box)
        popover.popup()
        
    def _create_tasks_view(self) -> Gtk.Box:
        """Create compact tasks view"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_vexpand(True)
        
        # Header
        header = Gtk.Label(label="Tareas Pendientes")
        header.add_css_class("title-4")
        header.set_halign(Gtk.Align.START)
        box.append(header)
        
        # Task list
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.tasks_list = Gtk.ListBox()
        self.tasks_list.add_css_class("boxed-list")
        self.tasks_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.set_child(self.tasks_list)
        
        box.append(scroll)
        
        self._load_tasks()
        
        return box
        
    def _load_tasks(self):
        while child := self.tasks_list.get_first_child():
            self.tasks_list.remove(child)
                
        try:
            tasks = task_manager.get_pending_tasks()[:8]
        except:
            tasks = []
            
        if not tasks:
            empty = Gtk.Label(label="Sin tareas pendientes")
            empty.add_css_class("dim-label")
            empty.set_margin_top(20)
            self.tasks_list.append(empty)
            return
            
        for task in tasks:
            row = Adw.ActionRow()
            row.set_title(task.get('title', '')[:40])
            row.add_css_class("task-row")
            
            priority = task.get('priority', 'media')
            row.add_css_class(f"priority-{priority}")
            
            if task.get('deadline'):
                row.set_subtitle(f"📅 {task['deadline']}")
                
            self.tasks_list.append(row)
            
    def _create_schedule_view(self) -> Gtk.Box:
        """Create today's schedule view"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_vexpand(True)
        
        today = datetime.now()
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        
        header = Gtk.Label(label=f"Hoy: {days[today.weekday()]}")
        header.add_css_class("title-4")
        header.set_halign(Gtk.Align.START)
        box.append(header)
        
        # Today's events from fixed schedule
        FIXED_SCHEDULE = {
            0: [("13:00-14:20", "Data Mining"), ("14:30-15:50", "Redes Lab")],
            1: [("10:00-11:20", "Bases de Datos"), ("13:00-14:20", "Redes"), 
                ("14:30-15:50", "Mercados Int."), ("16:00-18:00", "PASEC")],
            2: [("13:00-14:20", "Data Mining"), ("14:30-15:50", "PASEC Teoría")],
            3: [("10:00-11:20", "Bases de Datos"), ("13:00-14:20", "Redes"), 
                ("14:30-15:50", "Mercados Int.")],
            4: [("14:00-18:00", "PASEC")],
        }
        
        events = FIXED_SCHEDULE.get(today.weekday(), [])
        
        if not events:
            empty = Gtk.Label(label="Sin clases hoy")
            empty.add_css_class("dim-label")
            empty.set_margin_top(20)
            box.append(empty)
        else:
            list_box = Gtk.ListBox()
            list_box.add_css_class("boxed-list")
            list_box.set_selection_mode(Gtk.SelectionMode.NONE)
            
            for time, title in events:
                row = Adw.ActionRow()
                row.set_title(title)
                row.set_subtitle(time)
                list_box.append(row)
                
            box.append(list_box)
        
        return box
        
    def _start_clock(self):
        self._update_time()
        GLib.timeout_add_seconds(1, self._update_time)
        
    def _update_time(self) -> bool:
        now = datetime.now()
        days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        self.time_label.set_text(f"{days[now.weekday()]} {now.strftime('%d/%m %H:%M')}")
        return True
        
    def _open_main_app(self, btn):
        """Open the main GTK4 app"""
        app_dir = Path(__file__).parent
        subprocess.Popen([sys.executable, "main_gtk.py"], cwd=str(app_dir))


def main():
    app = WidgetApp()
    app.run(None)


if __name__ == "__main__":
    main()
