"""
Calendar View - GTK4
Monthly calendar with deadline indicators
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from datetime import datetime, timedelta
import calendar
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager


class CalendarView(Gtk.Box):
    """Monthly calendar view"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_spacing(24)
        
        self.current_date = datetime.now()
        self.deadlines = {}  # {date_str: [tasks]}
        
        self._setup_ui()
        self.refresh()
        
    def _setup_ui(self):
        """Setup calendar UI"""
        # Left: Calendar grid
        calendar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        calendar_box.add_css_class("glass-card")
        calendar_box.set_hexpand(True)
        
        # Navigation
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        prev_btn = Gtk.Button()
        prev_btn.set_icon_name("go-previous-symbolic")
        prev_btn.add_css_class("circular")
        prev_btn.connect("clicked", self._prev_month)
        nav_box.append(prev_btn)
        
        self.month_label = Gtk.Label()
        self.month_label.add_css_class("title-3")
        self.month_label.set_hexpand(True)
        nav_box.append(self.month_label)
        
        next_btn = Gtk.Button()
        next_btn.set_icon_name("go-next-symbolic")
        next_btn.add_css_class("circular")
        next_btn.connect("clicked", self._next_month)
        nav_box.append(next_btn)
        
        calendar_box.append(nav_box)
        
        # Day headers
        headers_grid = Gtk.Grid()
        headers_grid.set_column_homogeneous(True)
        days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for i, day in enumerate(days):
            label = Gtk.Label(label=day)
            label.add_css_class("dim-label")
            label.add_css_class("caption")
            headers_grid.attach(label, i, 0, 1, 1)
        calendar_box.append(headers_grid)
        
        # Calendar grid
        self.calendar_grid = Gtk.Grid()
        self.calendar_grid.set_column_homogeneous(True)
        self.calendar_grid.set_row_homogeneous(True)
        self.calendar_grid.set_row_spacing(4)
        self.calendar_grid.set_column_spacing(4)
        calendar_box.append(self.calendar_grid)
        
        self.append(calendar_box)
        
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
        self.append(tasks_box)
        
    def _prev_month(self, btn):
        """Go to previous month"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self._update_calendar()
        
    def _next_month(self, btn):
        """Go to next month"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self._update_calendar()
        
    def refresh(self):
        """Refresh calendar data"""
        # Load deadlines
        self.deadlines = {}
        try:
            tasks = task_manager.get_tasks_with_deadlines()
            for task in tasks:
                if task.get('deadline') and task.get('status') != 'completado':
                    date_str = task['deadline']
                    if date_str not in self.deadlines:
                        self.deadlines[date_str] = []
                    self.deadlines[date_str].append(task)
        except Exception as e:
            print(f"Calendar refresh error: {e}")
            
        self._update_calendar()
        
    def _update_calendar(self):
        """Update calendar grid"""
        # Update month label
        months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.month_label.set_text(f"{months[self.current_date.month - 1]} {self.current_date.year}")
        
        # Clear grid
        while True:
            child = self.calendar_grid.get_first_child()
            if child:
                self.calendar_grid.remove(child)
            else:
                break
                
        # Get calendar data
        cal = calendar.Calendar(firstweekday=0)  # Monday first
        month_days = cal.monthdayscalendar(self.current_date.year, self.current_date.month)
        
        today = datetime.now()
        
        for row_idx, week in enumerate(month_days):
            for col_idx, day in enumerate(week):
                if day == 0:
                    # Empty cell
                    label = Gtk.Label(label="")
                    self.calendar_grid.attach(label, col_idx, row_idx, 1, 1)
                else:
                    btn = self._create_day_button(day, today)
                    self.calendar_grid.attach(btn, col_idx, row_idx, 1, 1)
                    
    def _create_day_button(self, day: int, today: datetime) -> Gtk.Button:
        """Create a day button"""
        btn = Gtk.Button(label=str(day))
        btn.add_css_class("flat")
        btn.add_css_class("calendar-day")
        
        # Check if today
        is_today = (day == today.day and 
                    self.current_date.month == today.month and 
                    self.current_date.year == today.year)
        if is_today:
            btn.add_css_class("today")
            btn.add_css_class("suggested-action")
            
        # Check for deadlines
        date_str = f"{self.current_date.year}-{self.current_date.month:02d}-{day:02d}"
        if date_str in self.deadlines:
            btn.add_css_class("has-deadline")
            # Add red dot indicator
            btn.set_tooltip_text(f"{len(self.deadlines[date_str])} tarea(s)")
            
        btn.connect("clicked", self._on_day_clicked, day)
        return btn
        
    def _on_day_clicked(self, btn, day):
        """Handle day click"""
        date_str = f"{self.current_date.year}-{self.current_date.month:02d}-{day:02d}"
        
        # Update header
        self.selected_date_label.set_text(f"Tareas - {day}/{self.current_date.month}")
        
        # Clear task list
        while True:
            child = self.day_tasks_list.get_first_child()
            if child:
                self.day_tasks_list.remove(child)
            else:
                break
                
        # Show tasks for this day
        tasks = self.deadlines.get(date_str, [])
        
        if not tasks:
            empty = Gtk.Label(label="Sin tareas para este día")
            empty.add_css_class("dim-label")
            empty.set_margin_top(20)
            self.day_tasks_list.append(empty)
            return
            
        for task in tasks:
            row = Adw.ActionRow()
            row.set_title(task.get('title', ''))
            row.set_subtitle(task.get('category', ''))
            self.day_tasks_list.append(row)
