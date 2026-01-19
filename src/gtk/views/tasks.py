"""
Tasks View - GTK4
List and manage tasks with status and category filters
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager

# Obsidian Pasantías path
PASANTIAS_MD_PATH = Path("/home/jjulianleon/Documents/Obsidian/Pasantías/Pendientes Pasantía.md")


class TasksView(Gtk.Box):
    """Tasks list view with status and category filters"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_spacing(16)
        
        self.current_status_filter = "all"
        self.current_category_filter = "Todas"
        self._setup_ui()
        self.refresh()
        
    def _setup_ui(self):
        """Setup tasks UI"""
        # Status filter row
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        status_label = Gtk.Label(label="Estado:")
        status_bar.append(status_label)
        
        self.status_dropdown = Gtk.DropDown.new_from_strings([
            "Todas", "Pendientes", "En Progreso", "Completadas", "Hoy", "Atrasadas"
        ])
        self.status_dropdown.connect("notify::selected", self._on_status_filter_changed)
        status_bar.append(self.status_dropdown)
        
        # Category filter
        cat_label = Gtk.Label(label="Área:")
        cat_label.set_margin_start(16)
        status_bar.append(cat_label)
        
        categories = ["Todas", "Universidad", "Pasantías", "Personal", "Fedora"]
        self.category_buttons = {}
        
        for cat in categories:
            btn = Gtk.ToggleButton(label=cat)
            btn.add_css_class("flat")
            if cat == "Todas":
                btn.set_active(True)
            btn.connect("toggled", self._on_category_filter_changed, cat)
            status_bar.append(btn)
            self.category_buttons[cat] = btn
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        status_bar.append(spacer)
        
        # Search
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Buscar tareas...")
        self.search_entry.connect("search-changed", self._on_search_changed)
        status_bar.append(self.search_entry)
        
        self.append(status_bar)
        
        # Tasks list
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.tasks_list = Gtk.ListBox()
        self.tasks_list.add_css_class("boxed-list")
        self.tasks_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.set_child(self.tasks_list)
        
        self.append(scroll)
        
    def _on_status_filter_changed(self, dropdown, param):
        """Handle status filter change"""
        filters = ["all", "pendiente", "en progreso", "completado", "today", "overdue"]
        self.current_status_filter = filters[dropdown.get_selected()]
        self.refresh()
        
    def _on_category_filter_changed(self, btn, category):
        """Handle category filter change"""
        if btn.get_active():
            self.current_category_filter = category
            # Deactivate other category buttons
            for cat, b in self.category_buttons.items():
                if cat != category:
                    b.set_active(False)
            self.refresh()
        elif self.current_category_filter == category:
            btn.set_active(True)  # Prevent deselecting current
        
    def _on_search_changed(self, entry):
        """Handle search text change"""
        self.refresh()
        
    def refresh(self):
        """Refresh tasks list"""
        # Clear existing
        while child := self.tasks_list.get_first_child():
            self.tasks_list.remove(child)
                
        # Get tasks based on filter
        try:
            if self.current_status_filter == "all":
                tasks = task_manager.get_all_tasks()
            elif self.current_status_filter == "today":
                tasks = task_manager.get_today_tasks()
            elif self.current_status_filter == "overdue":
                tasks = task_manager.get_overdue_tasks()
            else:
                tasks = task_manager.get_all_tasks(status=self.current_status_filter)
                
            # Apply category filter
            if self.current_category_filter != "Todas":
                tasks = [t for t in tasks if t.get('category') == self.current_category_filter]
                
            # Apply search filter
            search_text = self.search_entry.get_text().lower()
            if search_text:
                tasks = [t for t in tasks if search_text in t.get('title', '').lower()]
                
        except Exception as e:
            print(f"Error loading tasks: {e}")
            tasks = []
            
        # Also load pasantías from Obsidian if that filter is active
        if self.current_category_filter in ["Todas", "Pasantías"]:
            pasantia_tasks = self._load_pasantias_from_obsidian()
            tasks.extend(pasantia_tasks)
            
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
            
    def _load_pasantias_from_obsidian(self) -> list:
        """Load pending tasks from Obsidian pasantías file"""
        tasks = []
        if not PASANTIAS_MD_PATH.exists():
            return tasks
            
        try:
            content = PASANTIAS_MD_PATH.read_text()
            for line in content.split('\n'):
                line = line.strip()
                # Parse markdown checkboxes
                if line.startswith('- [ ]'):
                    task_text = line[5:].strip()
                    tasks.append({
                        'id': None,  # Obsidian tasks don't have DB id
                        'title': task_text,
                        'category': 'Pasantías',
                        'priority': 'media',
                        'status': 'pendiente',
                        'source': 'obsidian'
                    })
                elif line.startswith('- [x]'):
                    # Completed tasks - skip or include based on filter
                    if self.current_status_filter in ["all", "completado"]:
                        task_text = line[5:].strip()
                        tasks.append({
                            'id': None,
                            'title': task_text,
                            'category': 'Pasantías',
                            'priority': 'media',
                            'status': 'completado',
                            'source': 'obsidian'
                        })
        except Exception as e:
            print(f"Error loading pasantías: {e}")
            
        return tasks
            
    def _create_task_row(self, task: dict) -> Adw.ActionRow:
        """Create a task row"""
        row = Adw.ActionRow()
        row.set_title(task.get('title', 'Sin título'))
        row.set_activatable(True)
        
        # Subtitle with category and deadline
        parts = []
        if task.get('category'):
            parts.append(task['category'])
        if task.get('deadline'):
            parts.append(f"📅 {task['deadline']}")
        if task.get('source') == 'obsidian':
            parts.append("📝 Obsidian")
        row.set_subtitle(" • ".join(parts))
        
        # Priority indicator
        priority = task.get('priority', 'media')
        colors = {'alta': '#ea4335', 'media': '#fbbc05', 'baja': '#34a853'}
        
        priority_dot = Gtk.Box()
        priority_dot.set_size_request(8, 8)
        priority_dot.set_valign(Gtk.Align.CENTER)
        css = Gtk.CssProvider()
        css.load_from_data(f"box {{ background: {colors.get(priority, '#888')}; border-radius: 50%; }}".encode())
        priority_dot.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        row.add_prefix(priority_dot)
        
        # Checkbox (only for DB tasks)
        if task.get('id'):
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
            GLib.timeout_add(500, self.refresh)
            
    def _on_task_clicked(self, row, task):
        """Show task details dialog"""
        if task.get('source') == 'obsidian':
            # For Obsidian tasks, open file
            import subprocess
            subprocess.Popen(['xdg-open', str(PASANTIAS_MD_PATH)])
            return
            
        from ..widgets.task_detail import TaskDetailDialog
        dialog = TaskDetailDialog(task, parent=self.get_root())
        dialog.connect("task-updated", lambda d: self.refresh())
        dialog.present()
