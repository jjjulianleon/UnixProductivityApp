"""
Kanban Board Widget - GTK4
Drag and drop task management
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gdk
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager


class KanbanBoard(Gtk.Box):
    """Kanban board with columns for task status"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)
        
        self._setup_ui()
        self.refresh()
        
    def _setup_ui(self):
        """Setup kanban columns"""
        columns = [
            ("pendiente", "Pendiente", "#4285f4"),
            ("en progreso", "En Progreso", "#fbbc05"),
            ("completado", "Completado", "#34a853"),
        ]
        
        self.columns = {}
        
        for status, title, color in columns:
            column = self._create_column(status, title, color)
            column.set_hexpand(True)
            self.columns[status] = column
            self.append(column)
            
    def _create_column(self, status: str, title: str, color: str) -> Gtk.Box:
        """Create a kanban column"""
        column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        column.add_css_class("kanban-column")
        
        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.add_css_class("kanban-column-header")
        
        # Color indicator
        indicator = Gtk.Box()
        indicator.set_size_request(4, 20)
        css = Gtk.CssProvider()
        css.load_from_data(f"box {{ background: {color}; border-radius: 2px; }}".encode())
        indicator.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        header.append(indicator)
        
        title_label = Gtk.Label(label=title)
        title_label.add_css_class("title-4")
        title_label.set_margin_start(8)
        title_label.set_hexpand(True)
        title_label.set_halign(Gtk.Align.START)
        header.append(title_label)
        
        # Count badge
        count_label = Gtk.Label(label="0")
        count_label.add_css_class("dim-label")
        header.append(count_label)
        
        column.append(header)
        
        # Task list
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        task_list = Gtk.ListBox()
        task_list.add_css_class("boxed-list")
        task_list.set_selection_mode(Gtk.SelectionMode.NONE)
        task_list.set_name(status)
        scroll.set_child(task_list)
        
        column.append(scroll)
        
        # Store references
        column.task_list = task_list
        column.count_label = count_label
        
        return column
        
    def refresh(self):
        """Refresh all columns"""
        for status, column in self.columns.items():
            self._refresh_column(status, column)
            
    def _refresh_column(self, status: str, column: Gtk.Box):
        """Refresh a single column"""
        task_list = column.task_list
        
        # Clear existing
        while True:
            child = task_list.get_first_child()
            if child:
                task_list.remove(child)
            else:
                break
                
        # Get tasks for this status
        try:
            tasks = task_manager.get_all_tasks(status=status)
        except Exception as e:
            print(f"Error loading tasks: {e}")
            tasks = []
            
        # Update count
        column.count_label.set_text(str(len(tasks)))
        
        if not tasks:
            empty = Gtk.Label(label="Sin tareas")
            empty.add_css_class("dim-label")
            empty.set_margin_top(20)
            task_list.append(empty)
            return
            
        for task in tasks:
            row = self._create_task_card(task, status)
            task_list.append(row)
            
    def _create_task_card(self, task: dict, current_status: str) -> Gtk.Box:
        """Create a draggable task card"""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.add_css_class("task-card")
        card.set_margin_start(4)
        card.set_margin_end(4)
        card.set_margin_top(4)
        card.set_margin_bottom(4)
        
        # Priority class
        priority = task.get('priority', 'media')
        card.add_css_class(f"priority-{priority}")
        
        # Title
        title = Gtk.Label(label=task.get('title', ''))
        title.set_halign(Gtk.Align.START)
        title.set_wrap(True)
        title.set_max_width_chars(30)
        card.append(title)
        
        # Subtitle row
        subtitle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        if task.get('category'):
            cat_label = Gtk.Label(label=task['category'])
            cat_label.add_css_class("dim-label")
            cat_label.add_css_class("caption")
            subtitle_box.append(cat_label)
            
        if task.get('deadline'):
            deadline_label = Gtk.Label(label=f"📅 {task['deadline']}")
            deadline_label.add_css_class("dim-label")
            deadline_label.add_css_class("caption")
            subtitle_box.append(deadline_label)
            
        card.append(subtitle_box)
        
        # Action buttons
        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        actions.set_margin_top(8)
        
        # Move buttons based on current status
        if current_status != "pendiente":
            left_btn = Gtk.Button()
            left_btn.set_icon_name("go-previous-symbolic")
            left_btn.add_css_class("flat")
            left_btn.add_css_class("circular")
            left_btn.set_tooltip_text("Mover a la izquierda")
            left_btn.connect("clicked", self._on_move_left, task.get('id'), current_status)
            actions.append(left_btn)
            
        if current_status != "completado":
            right_btn = Gtk.Button()
            right_btn.set_icon_name("go-next-symbolic")
            right_btn.add_css_class("flat")
            right_btn.add_css_class("circular")
            right_btn.set_tooltip_text("Mover a la derecha")
            right_btn.connect("clicked", self._on_move_right, task.get('id'), current_status)
            actions.append(right_btn)
            
        card.append(actions)
        
        return card
        
    def _on_move_left(self, btn, task_id, current_status):
        """Move task to previous column"""
        status_order = ["pendiente", "en progreso", "completado"]
        idx = status_order.index(current_status)
        if idx > 0:
            new_status = status_order[idx - 1]
            task_manager.update_task(task_id, status=new_status)
            self.refresh()
            
    def _on_move_right(self, btn, task_id, current_status):
        """Move task to next column"""
        status_order = ["pendiente", "en progreso", "completado"]
        idx = status_order.index(current_status)
        if idx < len(status_order) - 1:
            new_status = status_order[idx + 1]
            task_manager.update_task(task_id, status=new_status)
            self.refresh()
