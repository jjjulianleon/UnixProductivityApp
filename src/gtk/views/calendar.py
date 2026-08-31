"""
Calendar View - GTK4
Monthly calendar with centered circles and dots
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Pango
from datetime import datetime, timedelta
import calendar
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager


DAY_NAMES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
MONTHS_SHORT = ["ene", "feb", "mar", "abr", "may", "jun",
                "jul", "ago", "sep", "oct", "nov", "dic"]


class CalendarView(Gtk.Box):
    """Monthly calendar view"""

    # Lo que cabe en una celda sin que la rejilla crezca de mas
    MAX_EVENTS_PER_CELL = 3
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_spacing(16)
        
        self.current_date = datetime.now()
        self.deadlines = {}
        self.selected_day = self.current_date.day
        
        self._setup_ui()
        self.refresh()
        
    def _setup_ui(self):
        # Barra de navegacion, comun a las dos vistas
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        prev_btn = Gtk.Button()
        prev_btn.set_icon_name("go-previous-symbolic")
        prev_btn.add_css_class("circular")
        prev_btn.connect("clicked", self._shift_month, -1)
        nav_box.append(prev_btn)
        
        self.month_label = Gtk.Label()
        self.month_label.add_css_class("title-3")
        self.month_label.set_hexpand(True)
        self.month_label.set_halign(Gtk.Align.START)
        nav_box.append(self.month_label)
        
        today_btn = Gtk.Button(label="Hoy")
        today_btn.add_css_class("pill")
        today_btn.connect("clicked", self._go_today)
        nav_box.append(today_btn)
        
        # Selector de vista: puntos (compacta) o mes completo
        switcher = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        switcher.add_css_class("linked")
        self.dots_toggle = Gtk.ToggleButton(label="Puntos", active=True)
        self.month_toggle = Gtk.ToggleButton(label="Mes", group=self.dots_toggle)
        self.dots_toggle.connect("toggled", self._on_view_toggled)
        switcher.append(self.dots_toggle)
        switcher.append(self.month_toggle)
        nav_box.append(switcher)
        
        next_btn = Gtk.Button()
        next_btn.set_icon_name("go-next-symbolic")
        next_btn.add_css_class("circular")
        next_btn.connect("clicked", self._shift_month, 1)
        nav_box.append(next_btn)
        
        self.append(nav_box)
        
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(120)
        self.stack.set_vexpand(True)
        self.append(self.stack)
        
        self.stack.add_named(self._build_dots_view(), "dots")
        self.stack.add_named(self._build_month_view(), "month")
        
    def _build_dots_view(self) -> Gtk.Box:
        """Vista compacta: rejilla con puntos + tareas del dia a la derecha"""
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        
        calendar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        calendar_box.add_css_class("glass-card")
        calendar_box.set_hexpand(True)
        
        # Day headers
        headers_grid = Gtk.Grid()
        headers_grid.set_column_homogeneous(True)
        for i, day in enumerate(DAY_NAMES):
            label = Gtk.Label(label=day)
            label.add_css_class("dim-label")
            label.add_css_class("caption")
            headers_grid.attach(label, i, 0, 1, 1)
        calendar_box.append(headers_grid)
        
        # Calendar grid
        self.calendar_grid = Gtk.Grid()
        self.calendar_grid.set_column_homogeneous(True)
        self.calendar_grid.set_row_homogeneous(True)
        self.calendar_grid.set_row_spacing(8)
        self.calendar_grid.set_column_spacing(4)
        calendar_box.append(self.calendar_grid)
        
        root.append(calendar_box)
        
        # Right: Selected day tasks
        tasks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        tasks_box.add_css_class("glass-card")
        tasks_box.set_size_request(300, -1)
        
        self.selected_date_label = Gtk.Label(label="Tareas del día")
        self.selected_date_label.add_css_class("title-4")
        self.selected_date_label.set_halign(Gtk.Align.START)
        tasks_box.append(self.selected_date_label)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.day_tasks_list = Gtk.ListBox()
        self.day_tasks_list.add_css_class("boxed-list")
        self.day_tasks_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.set_child(self.day_tasks_list)
        
        tasks_box.append(scroll)
        root.append(tasks_box)
        return root
        
    def _build_month_view(self) -> Gtk.Widget:
        """Vista de mes completa: cada dia lista sus clases y sus entregas"""
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        
        self.month_grid = Gtk.Grid()
        self.month_grid.add_css_class("glass-card")
        self.month_grid.set_column_homogeneous(True)
        self.month_grid.set_row_homogeneous(True)
        scroll.set_child(self.month_grid)
        return scroll
        
    def _on_view_toggled(self, btn):
        self.stack.set_visible_child_name("dots" if btn.get_active() else "month")
        
    def _go_today(self, btn):
        self.current_date = datetime.now()
        self.selected_day = self.current_date.day
        self._update_calendar()
        self._show_day_tasks(self.selected_day)
        
    def _shift_month(self, btn, delta: int):
        """Mueve el calendario delta meses.

        Con day=1 siempre: hacer replace(month=...) conservando el dia lanzaba
        ValueError los dias 29-31 (un 31 de agosto no existe en septiembre) y
        los botones de navegacion se quedaban muertos.
        """
        month = self.current_date.month - 1 + delta
        year = self.current_date.year + month // 12
        self.current_date = self.current_date.replace(year=year, month=month % 12 + 1, day=1)
        self.selected_day = 1
        self._update_calendar()
        self._show_day_tasks(1)
        
    def refresh(self):
        self.deadlines = {}
        try:
            tasks = task_manager.get_tasks_with_deadlines()
            for task in tasks:
                if task.get('deadline') and task.get('status') != 'completado':
                    # Extract date-only for grouping (YYYY-MM-DD)
                    date_str = task['deadline'][:10]
                    if date_str not in self.deadlines:
                        self.deadlines[date_str] = []
                    self.deadlines[date_str].append(task)
        except Exception as e:
            print(f"Calendar refresh error: {e}")
        self._update_calendar()
        
        # Auto-show today's tasks
        today = datetime.now()
        self._show_day_tasks(today.day)
        
    def _update_calendar(self):
        months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.month_label.set_text(f"{months[self.current_date.month - 1]} {self.current_date.year}")
        
        # Clear grid
        while child := self.calendar_grid.get_first_child():
            self.calendar_grid.remove(child)
                
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(self.current_date.year, self.current_date.month)
        today = datetime.now()
        
        for row_idx, week in enumerate(month_days):
            for col_idx, day in enumerate(week):
                if day == 0:
                    self.calendar_grid.attach(Gtk.Label(label=""), col_idx, row_idx, 1, 1)
                else:
                    cell = self._create_day_cell(day, today)
                    self.calendar_grid.attach(cell, col_idx, row_idx, 1, 1)

        self._update_month_grid(today.date())

    def _update_month_grid(self, today):
        """Rejilla de mes al estilo Calendar: cada celda lista lo del dia"""
        while child := self.month_grid.get_first_child():
            self.month_grid.remove(child)

        for col, name in enumerate(DAY_NAMES):
            header = Gtk.Label(label=name)
            header.add_css_class("dim-label")
            header.add_css_class("caption")
            header.add_css_class("month-header")
            self.month_grid.attach(header, col, 0, 1, 1)

        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdatescalendar(self.current_date.year, self.current_date.month)
        for row, week in enumerate(weeks, start=1):
            for col, day in enumerate(week):
                self.month_grid.attach(self._create_month_cell(day, today), col, row, 1, 1)

    def _create_month_cell(self, day, today) -> Gtk.Widget:
        cell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        cell.add_css_class("month-cell")
        if day.month != self.current_date.month:
            cell.add_css_class("month-cell-outside")

        # El dia 1 lleva el mes, para no perderse en las semanas de empalme
        label = str(day.day) if day.day != 1 else f"1 {MONTHS_SHORT[day.month - 1]}"
        number = Gtk.Label(label=label)
        number.set_halign(Gtk.Align.END)
        number.add_css_class("caption")
        if day == today:
            number.add_css_class("calendar-today")
        cell.append(number)

        events = self._events_for(day)
        for event in events[:self.MAX_EVENTS_PER_CELL]:
            cell.append(self._create_event_row(event))

        hidden = len(events) - self.MAX_EVENTS_PER_CELL
        if hidden > 0:
            more = Gtk.Label(label=f"+{hidden} más")
            more.add_css_class("caption")
            more.add_css_class("dim-label")
            more.set_halign(Gtk.Align.START)
            cell.append(more)

        return cell

    def _events_for(self, day) -> list:
        """Clases del horario y entregas de ese dia, ordenadas por hora"""
        # ponytail: una consulta por celda (42 al mes). Cachear por semana si
        # el mes tarda en pintarse.
        events = [
            {'time': e.get('start_time', ''), 'title': e.get('title', ''), 'task': None}
            for e in task_manager.get_schedule_events(day.weekday(), for_date=day)
        ]
        for task in self.deadlines.get(day.isoformat(), []):
            deadline = task.get('deadline', '')
            events.append({
                'time': deadline[11:16] if 'T' in deadline else '23:59',
                'title': task.get('title', ''),
                'task': task,
            })
        events.sort(key=lambda e: e['time'])
        return events

    def _create_event_row(self, event) -> Gtk.Widget:
        is_task = event['task'] is not None

        marker = Gtk.Box()
        marker.add_css_class("color-dot" if is_task else "color-bar")
        marker.add_css_class("error" if is_task else "accent")
        marker.set_size_request(6, 6) if is_task else marker.set_size_request(3, 14)
        marker.set_valign(Gtk.Align.CENTER)

        label = Gtk.Label(label=event['title'])
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_xalign(0)
        label.set_hexpand(True)
        label.add_css_class("caption")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        row.append(marker)
        row.append(label)

        if not is_task:
            row.set_tooltip_text(f"{event['time']} {event['title']}")
            return row

        btn = Gtk.Button(child=row)
        btn.add_css_class("flat")
        btn.add_css_class("month-event")
        btn.set_tooltip_text(f"{event['time']} {event['title']}")
        btn.connect("clicked", lambda b, t=event['task']: self._on_task_clicked(None, t))
        return btn
                    
    def _create_day_cell(self, day: int, today: datetime) -> Gtk.Button:
        is_today = (day == today.day and 
                    self.current_date.month == today.month and 
                    self.current_date.year == today.year)
        
        date_str = f"{self.current_date.year}-{self.current_date.month:02d}-{day:02d}"
        has_deadline = date_str in self.deadlines
        deadline_count = len(self.deadlines.get(date_str, []))
        
        # Container for day + dot
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        container.set_halign(Gtk.Align.CENTER)
        container.set_valign(Gtk.Align.CENTER)
        
        # Day number with circle if today
        day_label = Gtk.Label(label=str(day))
        day_label.set_halign(Gtk.Align.CENTER)
        day_label.set_valign(Gtk.Align.CENTER)
        
        if is_today:
            day_label.set_size_request(32, 32)
            day_label.add_css_class("calendar-today")
        
        container.append(day_label)
        
        # Red dot for deadlines (centered)
        if has_deadline:
            dot = Gtk.Label(label="●")
            dot.set_halign(Gtk.Align.CENTER)
            dot.add_css_class("deadline-dot")
            container.append(dot)
        else:
            spacer = Gtk.Label(label=" ")
            spacer.set_size_request(-1, 8)
            container.append(spacer)
        
        # Wrap in button
        btn = Gtk.Button()
        btn.add_css_class("flat")
        btn.set_child(container)
        btn.connect("clicked", self._on_day_clicked, day)
        
        if has_deadline:
            btn.set_tooltip_text(f"{deadline_count} tarea(s)")
        
        return btn
        
    def _on_day_clicked(self, btn, day):
        """Handle day button click"""
        self.selected_day = day
        self._show_day_tasks(day)
        
    def _show_day_tasks(self, day: int):
        """Display tasks for a specific day in the sidebar"""
        date_str = f"{self.current_date.year}-{self.current_date.month:02d}-{day:02d}"
        self.selected_date_label.set_text(f"Tareas - {day}/{self.current_date.month}")
        
        while child := self.day_tasks_list.get_first_child():
            self.day_tasks_list.remove(child)
                
        tasks = self.deadlines.get(date_str, [])
        
        if not tasks:
            empty = Gtk.Label(label="Sin tareas para este día")
            empty.add_css_class("dim-label")
            empty.set_margin_top(20)
            self.day_tasks_list.append(empty)
            return
            
        for task in tasks:
            row = Adw.ActionRow()
            
            # Format time if available
            title = task.get('title', '')
            deadline_str = task.get('deadline', '')
            
            if 'T' in deadline_str:
                try:
                    dt = datetime.fromisoformat(deadline_str)
                    # format: 11:59 PM
                    time_str = dt.strftime("%I:%M %p").lower()
                    title = f"[{time_str}] {title}"
                except ValueError:
                    pass
            
            row.set_title(title)
            row.set_subtitle(task.get('category', ''))
            row.set_activatable(True)
            row.connect("activated", self._on_task_clicked, task)
            self.day_tasks_list.append(row)
            
    def _on_task_clicked(self, row, task):
        from ..widgets.task_detail import TaskDetailDialog
        dialog = TaskDetailDialog(task, parent=self.get_root())
        dialog.connect("task-updated", lambda d: self.refresh())
        dialog.present()
