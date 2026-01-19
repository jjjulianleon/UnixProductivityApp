"""
Kanban Board Widget - GTK4 with Category Filters
Categories: Todas, Universidad, Pasantías, Personal, Fedora
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gdk, GObject
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager

# Obsidian Pasantías path
PASANTIAS_MD_PATH = Path("/home/jjulianleon/Documents/Obsidian/Pasantías/Pendientes Pasantía.md")


class DraggableTaskCard(Gtk.Box):
    """A draggable task card"""
    
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
        
        priority = task.get('priority', 'media')
        self.add_css_class(f"priority-{priority}")
        
        # Only enable drag for DB tasks
        if self.task_id:
            drag_source = Gtk.DragSource()
            drag_source.set_actions(Gdk.DragAction.MOVE)
            drag_source.connect("prepare", self._on_drag_prepare)
            drag_source.connect("drag-begin", self._on_drag_begin)
            drag_source.connect("drag-end", self._on_drag_end)
            self.add_controller(drag_source)
        
        click = Gtk.GestureClick()
        click.connect("released", self._on_click_released)
        self.add_controller(click)
        
        self._setup_ui()
        
    def _setup_ui(self):
        title = Gtk.Label(label=self.task.get('title', ''))
        title.set_halign(Gtk.Align.START)
        title.set_wrap(True)
        title.set_max_width_chars(25)
        title.add_css_class("heading")
        self.append(title)
        
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
            
        if self.task.get('source') == 'obsidian':
            obs_label = Gtk.Label(label="📝")
            obs_label.set_tooltip_text("Desde Obsidian")
            subtitle_box.append(obs_label)
            
        self.append(subtitle_box)
        
    def _on_drag_prepare(self, source, x, y):
        self._drag_started = True
        return Gdk.ContentProvider.new_for_value(f"{self.task_id}:{self.current_status}")
        
    def _on_drag_begin(self, source, drag):
        self.set_opacity(0.5)
        
    def _on_drag_end(self, source, drag, delete_data):
        self.set_opacity(1.0)
        GLib.timeout_add(100, lambda: setattr(self, '_drag_started', False))
        
    def _on_click_released(self, gesture, n_press, x, y):
        if self._drag_started:
            return
        if n_press == 1:
            if self.task.get('source') == 'obsidian':
                import subprocess
                subprocess.Popen(['xdg-open', str(PASANTIAS_MD_PATH)])
                return
            from .task_detail import TaskDetailDialog
            dialog = TaskDetailDialog(self.task, parent=self.get_root())
            dialog.connect("task-updated", lambda d: self.board.refresh())
            dialog.present()


class KanbanColumn(Gtk.Box):
    """A kanban column"""
    
    def __init__(self, status: str, title: str, color: str, board):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.status = status
        self.board = board
        self.add_css_class("kanban-column")
        
        drop_target = Gtk.DropTarget.new(GObject.TYPE_STRING, Gdk.DragAction.MOVE)
        drop_target.connect("drop", self._on_drop)
        drop_target.connect("enter", self._on_drag_enter)
        drop_target.connect("leave", self._on_drag_leave)
        self.add_controller(drop_target)
        
        self._setup_ui(title, color)
        
    def _setup_ui(self, title: str, color: str):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.add_css_class("kanban-column-header")
        
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
        
        self.count_label = Gtk.Label(label="0")
        self.count_label.add_css_class("dim-label")
        header.append(self.count_label)
        
        self.append(header)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.EXTERNAL)
        
        self.task_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        scroll.set_child(self.task_list)
        
        self.append(scroll)
        
    def _on_drop(self, target, value, x, y):
        try:
            task_id, from_status = value.split(":")
            if from_status != self.status:
                task_manager.update_task(int(task_id), status=self.status)
                self.board.refresh()
            return True
        except:
            return False
            
    def _on_drag_enter(self, target, x, y):
        self.add_css_class("drag-hover")
        return Gdk.DragAction.MOVE
        
    def _on_drag_leave(self, target):
        self.remove_css_class("drag-hover")
        
    def add_task(self, task: dict):
        card = DraggableTaskCard(task, self.status, self.board)
        self.task_list.append(card)
        
    def clear_tasks(self):
        while child := self.task_list.get_first_child():
            self.task_list.remove(child)
                
    def update_count(self, count: int):
        self.count_label.set_text(str(count))


class KanbanBoard(Gtk.Box):
    """Kanban board with category filters"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)
        
        self.current_filter = "Todas"
        self._setup_ui()
        self.refresh()
        
    def _setup_ui(self):
        # Header with filter and search
        header_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        
        # Filter bar
        filter_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        filter_label = Gtk.Label(label="Filtrar:")
        filter_bar.append(filter_label)
        
        # Category filter buttons
        categories = ["Todas", "Universidad", "Pasantías", "Personal", "Fedora"]
        self.filter_buttons = {}
        
        for cat in categories:
            btn = Gtk.ToggleButton(label=cat)
            btn.add_css_class("flat")
            if cat == "Todas":
                btn.set_active(True)
            btn.connect("toggled", self._on_filter_changed, cat)
            filter_bar.append(btn)
            self.filter_buttons[cat] = btn
            
        header_bar.append(filter_bar)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header_bar.append(spacer)
        
        # Search box
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        search_icon = Gtk.Image.new_from_icon_name("system-search-symbolic")
        search_box.append(search_icon)
        
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Buscar tareas...")
        self.search_entry.set_width_chars(20)
        self.search_entry.connect("changed", self._on_search_changed)
        search_box.append(self.search_entry)
        
        header_bar.append(search_box)
        
        self.append(header_bar)
        
        # Columns container
        self.columns_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.columns_box.set_vexpand(True)
        
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
            self.columns_box.append(column)
            
        self.append(self.columns_box)
        
    def _on_search_changed(self, entry):
        """Handle search text change"""
        self.refresh()
        
    def _on_filter_changed(self, btn, category):
        if btn.get_active():
            self.current_filter = category
            for cat, b in self.filter_buttons.items():
                if cat != category:
                    b.set_active(False)
            self.refresh()
        elif self.current_filter == category:
            btn.set_active(True)
            
    def _load_pasantias_from_obsidian(self) -> list:
        """Load pending tasks from Obsidian pasantías file"""
        tasks = []
        if not PASANTIAS_MD_PATH.exists():
            return tasks
            
        try:
            content = PASANTIAS_MD_PATH.read_text()
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('- [ ]'):
                    task_text = line[5:].strip()
                    tasks.append({
                        'id': None,
                        'title': task_text,
                        'category': 'Pasantías',
                        'priority': 'media',
                        'status': 'pendiente',
                        'source': 'obsidian'
                    })
                elif line.startswith('- [x]'):
                    task_text = line[5:].strip()
                    tasks.append({
                        'id': None,
                        'title': task_text,
                        'category': 'Pasantías',
                        'priority': 'media',
                        'status': 'completado',
                        'source': 'obsidian'
                    })
        except:
            pass
            
        return tasks
            
    def refresh(self):
        search_text = self.search_entry.get_text().lower().strip() if hasattr(self, 'search_entry') else ""
        
        for status, column in self.columns.items():
            column.clear_tasks()
            
            try:
                tasks = task_manager.get_all_tasks(status=status)
                
                # Apply category filter (map Trabajo -> Pasantías)
                if self.current_filter != "Todas":
                    if self.current_filter == "Pasantías":
                        # Include both Pasantías and Trabajo
                        tasks = [t for t in tasks if t.get('category') in ['Pasantías', 'Trabajo']]
                    else:
                        tasks = [t for t in tasks if t.get('category') == self.current_filter]
                        
                # Apply search filter
                if search_text:
                    tasks = [t for t in tasks if search_text in t.get('title', '').lower()]
            except:
                tasks = []
            
            # Get existing task titles to avoid duplicates
            existing_titles = {t.get('title', '').lower().strip() for t in tasks}
                
            # Add Obsidian pasantías tasks (only if not already in DB)
            if self.current_filter in ["Todas", "Pasantías"]:
                obsidian_tasks = self._load_pasantias_from_obsidian()
                for t in obsidian_tasks:
                    if t.get('status') == status:
                        task_title = t.get('title', '').lower().strip()
                        # Skip if task already exists from DB
                        if task_title in existing_titles:
                            continue
                        # Apply search to obsidian tasks too
                        if not search_text or search_text in task_title:
                            tasks.append(t)
                
            column.update_count(len(tasks))
            
            for task in tasks:
                column.add_task(task)
