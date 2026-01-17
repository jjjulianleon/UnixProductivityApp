"""
Tasks View - GTK4
List and manage all tasks with filters
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager


class TasksView(Gtk.Box):
    """Tasks list view with filters"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_spacing(16)
        
        self.current_filter = "all"
        self._setup_ui()
        self.refresh()
        
    def _setup_ui(self):
        """Setup tasks UI"""
        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        # Filter dropdown
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        filter_label = Gtk.Label(label="Filtrar:")
        filter_box.append(filter_label)
        
        self.filter_dropdown = Gtk.DropDown.new_from_strings([
            "Todas", "Pendientes", "En Progreso", "Completadas", "Hoy", "Atrasadas"
        ])
        self.filter_dropdown.connect("notify::selected", self._on_filter_changed)
        filter_box.append(self.filter_dropdown)
        toolbar.append(filter_box)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar.append(spacer)
        
        # Search
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Buscar tareas...")
        self.search_entry.connect("search-changed", self._on_search_changed)
        toolbar.append(self.search_entry)
        
        self.append(toolbar)
        
        # Tasks list
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.tasks_list = Gtk.ListBox()
        self.tasks_list.add_css_class("boxed-list")
        self.tasks_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.set_child(self.tasks_list)
        
        self.append(scroll)
        
    def _on_filter_changed(self, dropdown, param):
        """Handle filter change"""
        filters = ["all", "pendiente", "en progreso", "completado", "today", "overdue"]
        self.current_filter = filters[dropdown.get_selected()]
        self.refresh()
        
    def _on_search_changed(self, entry):
        """Handle search text change"""
        self.refresh()
        
    def refresh(self):
        """Refresh tasks list"""
        # Clear existing
        while True:
            child = self.tasks_list.get_first_child()
            if child:
                self.tasks_list.remove(child)
            else:
                break
                
        # Get tasks based on filter
        try:
            if self.current_filter == "all":
                tasks = task_manager.get_all_tasks()
            elif self.current_filter == "today":
                tasks = task_manager.get_today_tasks()
            elif self.current_filter == "overdue":
                tasks = task_manager.get_overdue_tasks()
            else:
                tasks = task_manager.get_all_tasks(status=self.current_filter)
                
            # Apply search filter
            search_text = self.search_entry.get_text().lower()
            if search_text:
                tasks = [t for t in tasks if search_text in t.get('title', '').lower()]
                
        except Exception as e:
            print(f"Error loading tasks: {e}")
            tasks = []
            
        if not tasks:
            empty = Adw.StatusPage()
            empty.set_icon_name("checkbox-checked-symbolic")
            empty.set_title("Sin tareas")
            empty.set_description("Crea una nueva tarea con el botón +")
            self.tasks_list.append(empty)
            return
            
        for task in tasks:
            row = self._create_task_row(task)
            self.tasks_list.append(row)
            
    def _create_task_row(self, task: dict) -> Adw.ActionRow:
        """Create an expandable task row"""
        row = Adw.ActionRow()
        row.set_title(task.get('title', 'Sin título'))
        row.set_activatable(True)
        
        # Subtitle with category and deadline
        parts = []
        if task.get('category'):
            parts.append(task['category'])
        if task.get('deadline'):
            parts.append(f"📅 {task['deadline']}")
        row.set_subtitle(" • ".join(parts))
        
        # Priority indicator prefix
        priority = task.get('priority', 'media')
        colors = {'alta': '#ea4335', 'media': '#fbbc05', 'baja': '#34a853'}
        
        priority_dot = Gtk.Box()
        priority_dot.set_size_request(8, 8)
        priority_dot.set_valign(Gtk.Align.CENTER)
        # Use inline CSS for color
        css = Gtk.CssProvider()
        css.load_from_data(f"box {{ background: {colors.get(priority, '#888')}; border-radius: 50%; }}".encode())
        priority_dot.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        row.add_prefix(priority_dot)
        
        # Checkbox suffix
        check = Gtk.CheckButton()
        check.set_active(task.get('status') == 'completado')
        check.set_valign(Gtk.Align.CENTER)
        check.connect("toggled", self._on_task_toggle, task.get('id'))
        row.add_suffix(check)
        
        # Click to show details
        row.connect("activated", self._on_task_clicked, task)
        
        return row
        
    def _on_task_toggle(self, check, task_id):
        """Handle task completion toggle"""
        if task_id:
            new_status = "completado" if check.get_active() else "pendiente"
            task_manager.update_task(task_id, status=new_status)
            GLib.timeout_add(500, self.refresh)  # Refresh after short delay
            
    def _on_task_clicked(self, row, task):
        """Show task details dialog"""
        from ..widgets.task_detail import TaskDetailDialog
        dialog = TaskDetailDialog(task, parent=self.get_root())
        dialog.connect("task-updated", lambda d: self.refresh())
        dialog.present()

