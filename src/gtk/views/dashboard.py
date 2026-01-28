"""
Dashboard View - GTK4
Shows overview with urgent tasks, today's schedule, and quick stats
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager


class DashboardView(Gtk.Box):
    """Dashboard with overview cards"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_spacing(20)
        
        self._setup_ui()
        self.refresh()
        
    def _setup_ui(self):
        """Setup dashboard UI"""
        # Welcome section
        welcome_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        greeting = self._get_greeting()
        greeting_label = Gtk.Label(label=greeting)
        greeting_label.add_css_class("title-1")
        greeting_label.set_halign(Gtk.Align.START)
        welcome_box.append(greeting_label)
        
        date_label = Gtk.Label(label=datetime.now().strftime("%A, %d de %B %Y"))
        date_label.add_css_class("dim-label")
        date_label.set_halign(Gtk.Align.START)
        welcome_box.append(date_label)
        
        self.append(welcome_box)
        
        # Stats row
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        stats_box.set_homogeneous(True)
        
        self.pending_stat = self._create_stat_card("Pendientes", "0", "dialog-information-symbolic")
        stats_box.append(self.pending_stat)
        
        self.today_stat = self._create_stat_card("Hoy", "0", "alarm-symbolic")
        stats_box.append(self.today_stat)
        
        self.overdue_stat = self._create_stat_card("Atrasadas", "0", "dialog-warning-symbolic")
        stats_box.append(self.overdue_stat)
        
        self.completed_stat = self._create_stat_card("Completadas", "0", "emblem-ok-symbolic")
        stats_box.append(self.completed_stat)
        
        self.append(stats_box)
        
        # Main content row
        content_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        content_row.set_vexpand(True)
        
        # Urgent tasks column
        urgent_column = self._create_urgent_tasks_card()
        urgent_column.set_hexpand(True)
        content_row.append(urgent_column)
        
        # Today's schedule column
        schedule_column = self._create_schedule_card()
        schedule_column.set_hexpand(True)
        content_row.append(schedule_column)
        
        self.append(content_row)
        
    def _get_greeting(self) -> str:
        """Get time-appropriate greeting"""
        hour = datetime.now().hour
        if hour < 12:
            return "Buenos días, Julian"
        elif hour < 18:
            return "Buenas tardes, Julian"
        else:
            return "Buenas noches, Julian"
            
    def _create_stat_card(self, label: str, value: str, icon: str) -> Gtk.Box:
        """Create a statistics card"""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.add_css_class("glass-card")
        card.set_valign(Gtk.Align.START)
        
        # Icon
        icon_widget = Gtk.Image.new_from_icon_name(icon)
        icon_widget.set_pixel_size(24)
        icon_widget.add_css_class("dim-label")
        card.append(icon_widget)
        
        # Value
        value_label = Gtk.Label(label=value)
        value_label.add_css_class("stat-value")
        value_label.set_name(f"stat-{label.lower()}")
        card.append(value_label)
        
        # Label
        text_label = Gtk.Label(label=label)
        text_label.add_css_class("stat-label")
        card.append(text_label)
        
        return card
        
    def _create_urgent_tasks_card(self) -> Gtk.Box:
        """Create urgent tasks card"""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.add_css_class("glass-card")
        
        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title = Gtk.Label(label="Tareas Urgentes")
        title.add_css_class("title-4")
        title.set_halign(Gtk.Align.START)
        header.append(title)
        card.append(header)
        
        # Task list in scrolled window
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.urgent_tasks_list = Gtk.ListBox()
        self.urgent_tasks_list.add_css_class("boxed-list")
        self.urgent_tasks_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.set_child(self.urgent_tasks_list)
        
        card.append(scroll)
        return card
        
    def _create_schedule_card(self) -> Gtk.Box:
        """Create today's schedule card"""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.add_css_class("glass-card")
        
        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title = Gtk.Label(label="Horario de Hoy")
        title.add_css_class("title-4")
        title.set_halign(Gtk.Align.START)
        header.append(title)
        card.append(header)
        
        # Schedule list
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.schedule_list = Gtk.ListBox()
        self.schedule_list.add_css_class("boxed-list")
        self.schedule_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.set_child(self.schedule_list)
        
        card.append(scroll)
        return card
        
    def refresh(self):
        """Refresh dashboard data"""
        try:
            # Get task counts
            pending = len(task_manager.get_pending_tasks()) + len(task_manager.get_in_progress_tasks())
            today = len(task_manager.get_today_tasks())
            overdue = len(task_manager.get_overdue_tasks())
            completed = len(task_manager.get_completed_tasks())
            
            # Update stat cards
            self._update_stat_value(self.pending_stat, str(pending))
            self._update_stat_value(self.today_stat, str(today))
            self._update_stat_value(self.overdue_stat, str(overdue))
            self._update_stat_value(self.completed_stat, str(completed))
            
            # Update urgent tasks list
            self._update_urgent_tasks()
            
            # Update schedule
            self._update_schedule()
            
        except Exception as e:
            print(f"Dashboard refresh error: {e}")
            
    def _update_stat_value(self, card: Gtk.Box, value: str):
        """Update value in a stat card"""
        # Find the value label (second child)
        child = card.get_first_child()
        if child:
            child = child.get_next_sibling()  # Skip icon
            if child and isinstance(child, Gtk.Label):
                child.set_text(value)
                
    def _update_urgent_tasks(self):
        """Update urgent tasks list"""
        # Clear existing
        while True:
            child = self.urgent_tasks_list.get_first_child()
            if child:
                self.urgent_tasks_list.remove(child)
            else:
                break
                
        # Get upcoming tasks
        upcoming = task_manager.get_upcoming_tasks(7)
        
        if not upcoming:
            empty = Adw.StatusPage()
            empty.set_icon_name("checkbox-checked-symbolic")
            empty.set_title("¡Sin tareas urgentes!")
            empty.set_description("Disfruta tu día")
            self.urgent_tasks_list.append(empty)
            return
            
        for task in upcoming[:5]:  # Show max 5
            row = self._create_task_row(task)
            self.urgent_tasks_list.append(row)
            
    def _create_task_row(self, task: dict) -> Adw.ActionRow:
        """Create a task row"""
        row = Adw.ActionRow()
        row.set_title(task.get('title', 'Sin título'))
        
        # Deadline subtitle
        deadline = task.get('deadline', '')
        if deadline:
            days = self._days_until(deadline)
            if days == 0:
                row.set_subtitle("Hoy")
            elif days == 1:
                row.set_subtitle("Mañana")
            elif days < 0:
                row.set_subtitle(f"Atrasada ({abs(days)} días)")
            else:
                row.set_subtitle(f"En {days} días")
                
        # Priority indicator
        priority = task.get('priority', 'media')
        priority_colors = {'alta': 'red', 'media': 'orange', 'baja': 'green'}
        
        indicator = Gtk.Box()
        indicator.set_size_request(4, 32)
        indicator.add_css_class(f"priority-{priority}")
        row.add_prefix(indicator)
        
        return row
        
    def _days_until(self, deadline: str) -> int:
        """Calculate days until deadline"""
        try:
            # Handle both YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS formats
            date_part = deadline[:10]  # Extract just YYYY-MM-DD
            deadline_date = datetime.strptime(date_part, "%Y-%m-%d").date()
            today = datetime.now().date()
            return (deadline_date - today).days
        except:
            return 999
            
    def _update_schedule(self):
        """Update today's schedule"""
        # Clear existing
        while True:
            child = self.schedule_list.get_first_child()
            if child:
                self.schedule_list.remove(child)
            else:
                break
                
        # Get today's events
        today_weekday = datetime.now().weekday()
        events = task_manager.get_schedule_events(today_weekday)
        
        if not events:
            empty = Adw.StatusPage()
            empty.set_icon_name("weather-clear-symbolic")
            empty.set_title("Sin eventos hoy")
            empty.set_description("Tu día está libre")
            self.schedule_list.append(empty)
            return
            
        for event in events:
            row = Adw.ActionRow()
            row.set_title(event.get('title', ''))
            row.set_subtitle(f"{event.get('start_time', '')} - {event.get('end_time', '')}")
            self.schedule_list.append(row)
