"""
Main Window - GTK4 + Libadwaita with Translucency
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio
from pathlib import Path

# Import views
from .views.dashboard import DashboardView
from .views.tasks import TasksView
from .views.calendar import CalendarView
from .views.stats import StatsView

# Import widgets as views
from .widgets.kanban import KanbanBoard
from .widgets.pomodoro import PomodoroTimer
from .widgets.notes import QuickNotes
from .widgets.schedule import WeeklySchedule

# Import backend
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.core.task_manager import task_manager
from src.core.signals import signals


class MainWindow(Adw.ApplicationWindow):
    """Main application window with translucent sidebar"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.set_title("Unix Productivity")
        self.set_default_size(1100, 700)
        self.add_css_class("main-window")
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup the main UI layout"""
        # Main horizontal layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_content(main_box)
        
        # Content area with navigation view
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.content_box.set_hexpand(True)
        self.content_box.set_vexpand(True)
        
        # Stack for views - create FIRST so nav buttons can use it
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(200)
        self.stack.set_vexpand(True)
        self.stack.set_hexpand(True)
        
        # Add views
        self.dashboard_view = DashboardView()
        self.stack.add_titled(self.dashboard_view, "dashboard", "Dashboard")
        
        self.tasks_view = TasksView()
        self.stack.add_titled(self.tasks_view, "tasks", "Tareas")
        
        self.calendar_view = CalendarView()
        self.stack.add_titled(self.calendar_view, "calendar", "Calendario")
        
        self.stats_view = StatsView()
        self.stack.add_titled(self.stats_view, "stats", "Estadísticas")
        
        # Widget views
        self.kanban_view = KanbanBoard()
        self.stack.add_titled(self.kanban_view, "kanban", "Kanban")
        
        self.pomodoro_view = PomodoroTimer()
        self.stack.add_titled(self.pomodoro_view, "pomodoro", "Pomodoro")
        
        self.notes_view = QuickNotes()
        self.stack.add_titled(self.notes_view, "notes", "Rough Notes")
        
        self.schedule_view = WeeklySchedule()
        self.stack.add_titled(self.schedule_view, "schedule", "Horario")
        
        # Header bar - create BEFORE sidebar so header_title exists
        header = self._create_header()
        self.content_box.append(header)
        
        # NOW create sidebar (after stack AND header exist)
        sidebar = self._create_sidebar()
        main_box.append(sidebar)
        
        self.content_box.append(self.stack)
        main_box.append(self.content_box)
        
    def _create_sidebar(self) -> Gtk.Box:
        """Create the navigation sidebar"""
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar.set_size_request(200, -1)
        sidebar.add_css_class("sidebar")
        
        # App title
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title_box.set_margin_top(20)
        title_box.set_margin_bottom(20)
        title_box.set_margin_start(16)
        title_box.set_margin_end(16)
        
        app_icon = Gtk.Image.new_from_icon_name("appointment-soon-symbolic")
        app_icon.set_pixel_size(24)
        title_box.append(app_icon)
        
        title_label = Gtk.Label(label="Productivity")
        title_label.add_css_class("title-3")
        title_label.set_margin_start(8)
        title_box.append(title_label)
        
        sidebar.append(title_box)
        
        # Navigation buttons
        nav_items = [
            ("dashboard", "Dashboard", "view-grid-symbolic"),
            ("tasks", "Tareas", "checkbox-checked-symbolic"),
            ("kanban", "Kanban", "view-column-symbolic"),
            ("calendar", "Calendario", "x-office-calendar-symbolic"),
            ("schedule", "Horario", "go-today"),
            ("pomodoro", "Pomodoro", "alarm-symbolic"),
            ("notes", "Rough Notes", "accessories-text-editor-symbolic"),
            ("stats", "Estadísticas", "utilities-system-monitor-symbolic"),
        ]
        
        self.nav_buttons = {}
        self.current_nav_key = "dashboard"
        nav_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        nav_box.set_margin_start(8)
        nav_box.set_margin_end(8)
        
        for key, label, icon in nav_items:
            btn = Gtk.Button()
            btn.add_css_class("sidebar-button")
            btn.add_css_class("flat")
            
            btn_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            btn_icon = Gtk.Image.new_from_icon_name(icon)
            btn_label = Gtk.Label(label=label)
            btn_label.set_halign(Gtk.Align.START)
            btn_label.set_hexpand(True)
            
            btn_content.append(btn_icon)
            btn_content.append(btn_label)
            btn.set_child(btn_content)
            
            btn.connect("clicked", self._on_nav_button_clicked, key)
            self.nav_buttons[key] = btn
            nav_box.append(btn)
            
        # Set initial active state
        self.nav_buttons["dashboard"].add_css_class("suggested-action")
            
        sidebar.append(nav_box)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        sidebar.append(spacer)
        
        # Settings button at bottom
        settings_btn = Gtk.Button()
        settings_btn.add_css_class("sidebar-button")
        settings_btn.add_css_class("flat")
        settings_btn.set_margin_start(8)
        settings_btn.set_margin_end(8)
        settings_btn.set_margin_bottom(12)
        
        settings_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        settings_icon = Gtk.Image.new_from_icon_name("preferences-system-symbolic")
        settings_label = Gtk.Label(label="Configuración")
        settings_label.set_halign(Gtk.Align.START)
        settings_content.append(settings_icon)
        settings_content.append(settings_label)
        settings_btn.set_child(settings_content)
        settings_btn.connect("clicked", self._on_settings_clicked)
        sidebar.append(settings_btn)
        
        # Initial selection already set above with suggested-action class
        
        return sidebar
        
    def _create_header(self) -> Adw.HeaderBar:
        """Create the header bar"""
        header = Adw.HeaderBar()
        header.add_css_class("flat")
        
        # Title
        self.header_title = Gtk.Label(label="Dashboard")
        self.header_title.add_css_class("title-2")
        header.set_title_widget(self.header_title)
        
        # Add task button
        add_btn = Gtk.Button()
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.add_css_class("suggested-action")
        add_btn.add_css_class("circular")
        add_btn.set_tooltip_text("Nueva Tarea (Ctrl+N)")
        add_btn.connect("clicked", lambda _: self.show_add_task_dialog())
        header.pack_start(add_btn)
        
        # Search button
        search_btn = Gtk.Button()
        search_btn.set_icon_name("system-search-symbolic")
        search_btn.set_tooltip_text("Buscar (Ctrl+F)")
        header.pack_end(search_btn)
        
        # Menu button
        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("open-menu-symbolic")
        
        menu = Gio.Menu()
        menu.append("Crear Backup", "app.backup")
        menu.append("Exportar", "app.export")
        menu.append("Importar", "app.import")
        menu.append("Acerca de", "app.about")
        menu_btn.set_menu_model(menu)
        header.pack_end(menu_btn)
        
        return header
        
    def _on_nav_button_clicked(self, button, key):
        """Handle navigation button click - works on first click"""
        # Remove active state from previous button
        if self.current_nav_key in self.nav_buttons:
            self.nav_buttons[self.current_nav_key].remove_css_class("suggested-action")
        
        # Add active state to clicked button
        button.add_css_class("suggested-action")
        self.current_nav_key = key
        
        # Switch view
        self.stack.set_visible_child_name(key)
        
        # Update header title
        titles = {
            "dashboard": "Dashboard",
            "tasks": "Tareas",
            "kanban": "Kanban Board",
            "calendar": "Calendario", 
            "schedule": "Horario Semanal",
            "pomodoro": "Pomodoro Timer",
            "notes": "Rough Notes",
            "stats": "Estadísticas"
        }
        self.header_title.set_text(titles.get(key, key))
                
    def _on_settings_clicked(self, button):
        """Open settings dialog"""
        from .dialogs.settings import SettingsDialog
        dialog = SettingsDialog(parent=self)
        dialog.present()
        
    def _connect_signals(self):
        """Connect to backend signals"""
        # TODO: Connect GObject signals adapter
        pass
        
    def show_add_task_dialog(self):
        """Show add task dialog"""
        from .dialogs.add_task import AddTaskDialog
        dialog = AddTaskDialog(parent=self)
        dialog.present()
        
    def refresh_views(self):
        """Refresh all views with new data"""
        self.dashboard_view.refresh()
        self.tasks_view.refresh()
        self.calendar_view.refresh()
        self.stats_view.refresh()
