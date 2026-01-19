"""
Kanban Board Widget - GTK4 with proper Drag and Drop
Click opens details, long press + drag moves cards
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gdk, GObject
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager


class DraggableTaskCard(Gtk.Box):
    """A draggable task card for the Kanban board"""
    
    def __init__(self, task: dict, current_status: str, board):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.task = task
        self.current_status = current_status
        self.task_id = task.get('id')
        self.board = board
        self._drag_started = False
        
        self.add_css_class("task-card")
        self.set_margin_start(4)
        self.set_margin_end(4)
        self.set_margin_top(4)
        self.set_margin_bottom(4)
        
        # Priority class
        priority = task.get('priority', 'media')
        self.add_css_class(f"priority-{priority}")
        
        # Make draggable - this handles long press automatically
        drag_source = Gtk.DragSource()
        drag_source.set_actions(Gdk.DragAction.MOVE)
        drag_source.connect("prepare", self._on_drag_prepare)
        drag_source.connect("drag-begin", self._on_drag_begin)
        drag_source.connect("drag-end", self._on_drag_end)
        self.add_controller(drag_source)
        
        # Click gesture - only fires if drag didn't start
        click = Gtk.GestureClick()
        click.connect("released", self._on_click_released)
        self.add_controller(click)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup card UI"""
        # Title
        title = Gtk.Label(label=self.task.get('title', ''))
        title.set_halign(Gtk.Align.START)
        title.set_wrap(True)
        title.set_max_width_chars(25)
        title.add_css_class("heading")
        self.append(title)
        
        # Subtitle row
        subtitle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        if self.task.get('category'):
            cat_label = Gtk.Label(label=self.task['category'])
            cat_label.add_css_class("dim-label")
            cat_label.add_css_class("caption")
            subtitle_box.append(cat_label)
            
        if self.task.get('deadline'):
            deadline_label = Gtk.Label(label=f"📅 {self.task['deadline']}")
            deadline_label.add_css_class("dim-label")
            deadline_label.add_css_class("caption")
            subtitle_box.append(deadline_label)
            
        self.append(subtitle_box)
        
    def _on_drag_prepare(self, source, x, y):
        """Prepare drag data"""
        self._drag_started = True
        content = Gdk.ContentProvider.new_for_value(f"{self.task_id}:{self.current_status}")
        return content
        
    def _on_drag_begin(self, source, drag):
        """Visual feedback when drag starts"""
        self.set_opacity(0.5)
        
    def _on_drag_end(self, source, drag, delete_data):
        """Reset visual after drag"""
        self.set_opacity(1.0)
        # Reset flag after a short delay
        GLib.timeout_add(100, self._reset_drag_flag)
        
    def _reset_drag_flag(self):
        self._drag_started = False
        return False
        
    def _on_click_released(self, gesture, n_press, x, y):
        """Open task detail only if drag didn't happen"""
        if self._drag_started:
            return
        if n_press == 1:
            from .task_detail import TaskDetailDialog
            dialog = TaskDetailDialog(self.task, parent=self.get_root())
            dialog.connect("task-updated", self._on_task_updated)
            dialog.present()
            
    def _on_task_updated(self, dialog):
        """Refresh when task is updated"""
        self.board.refresh()


class KanbanColumn(Gtk.Box):
    """A column in the Kanban board that accepts drops"""
    
    def __init__(self, status: str, title: str, color: str, board):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.status = status
        self.board = board
        self.add_css_class("kanban-column")
        
        # Drop target
        drop_target = Gtk.DropTarget.new(GObject.TYPE_STRING, Gdk.DragAction.MOVE)
        drop_target.connect("drop", self._on_drop)
        drop_target.connect("enter", self._on_drag_enter)
        drop_target.connect("leave", self._on_drag_leave)
        self.add_controller(drop_target)
        
        self._setup_ui(title, color)
        
    def _setup_ui(self, title: str, color: str):
        """Setup column UI"""
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
        self.count_label = Gtk.Label(label="0")
        self.count_label.add_css_class("dim-label")
        header.append(self.count_label)
        
        self.append(header)
        
        # Task list with hidden scrollbar
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.EXTERNAL)  # Hidden scrollbar
        
        self.task_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        scroll.set_child(self.task_list)
        
        self.append(scroll)
        
    def _on_drop(self, target, value, x, y):
        """Handle task drop"""
        try:
            task_id, from_status = value.split(":")
            if from_status != self.status:
                task_manager.update_task(int(task_id), status=self.status)
                self.board.refresh()
            return True
        except Exception as e:
            print(f"Drop error: {e}")
            return False
            
    def _on_drag_enter(self, target, x, y):
        """Visual feedback on drag enter"""
        self.add_css_class("drag-hover")
        return Gdk.DragAction.MOVE
        
    def _on_drag_leave(self, target):
        """Remove visual feedback"""
        self.remove_css_class("drag-hover")
        
    def add_task(self, task: dict):
        """Add a task card to this column"""
        card = DraggableTaskCard(task, self.status, self.board)
        self.task_list.append(card)
        
    def clear_tasks(self):
        """Clear all tasks"""
        while True:
            child = self.task_list.get_first_child()
            if child:
                self.task_list.remove(child)
            else:
                break
                
    def update_count(self, count: int):
        """Update task count"""
        self.count_label.set_text(str(count))


class KanbanBoard(Gtk.Box):
    """Kanban board with drag and drop columns"""
    
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
        columns_config = [
            ("pendiente", "Pendiente", "#4285f4"),
            ("en progreso", "En Progreso", "#fbbc05"),
            ("completado", "Completado", "#34a853"),
        ]
        
        self.columns = {}
        
        for status, title, color in columns_config:
            column = KanbanColumn(status, title, color, self)
            column.set_hexpand(True)
            self.columns[status] = column
            self.append(column)
            
    def refresh(self):
        """Refresh all columns"""
        for status, column in self.columns.items():
            column.clear_tasks()
            
            try:
                tasks = task_manager.get_all_tasks(status=status)
            except Exception as e:
                print(f"Error loading tasks: {e}")
                tasks = []
                
            column.update_count(len(tasks))
            
            for task in tasks:
                column.add_task(task)
