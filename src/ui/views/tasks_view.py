"""
Tasks View - Full Kanban with search and filters
"""
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from src.utils.styles import (
    COLORS, FONT_FAMILY, get_button_style, get_input_style,
    get_combobox_style
)
from src.utils.constants import TASK_CATEGORIES
from src.core.task_manager import task_manager
from src.core.signals import SignalHub
from src.ui.widgets.kanban import KanbanBoard
from src.ui.dialogs.task_dialogs import AddTaskDialog, TaskDetailDialog


class TasksView(QWidget):
    """Full tasks view with Kanban board"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = SignalHub.get_instance()
        self.current_category = None
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        self.setup_ui()
        self._load_tasks()
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect to signal hub"""
        self.signals.task_added.connect(self._load_tasks)
        self.signals.task_updated.connect(self._load_tasks)
        self.signals.task_deleted.connect(self._load_tasks)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Tareas")
        title.setFont(QFont(FONT_FAMILY, 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar tareas...")
        self.search_input.setFont(QFont(FONT_FAMILY, 10))
        self.search_input.setStyleSheet(get_input_style())
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self._on_search_changed)
        header_layout.addWidget(self.search_input)
        
        # Category filter
        self.category_filter = QComboBox()
        self.category_filter.addItem("Todas las categorias")
        self.category_filter.addItems(TASK_CATEGORIES)
        self.category_filter.setFont(QFont(FONT_FAMILY, 10))
        self.category_filter.setStyleSheet(get_combobox_style())
        self.category_filter.currentTextChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.category_filter)
        
        # Add task button
        add_btn = QPushButton("+ Nueva Tarea")
        add_btn.setFont(QFont(FONT_FAMILY, 10))
        add_btn.setStyleSheet(get_button_style('primary'))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_task)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Kanban board
        self.kanban = KanbanBoard()
        self.kanban.task_status_changed.connect(self._on_status_changed)
        self.kanban.task_clicked.connect(self._on_task_clicked)
        self.kanban.add_task_requested.connect(self._add_task_with_status)
        layout.addWidget(self.kanban, 1)
    
    def _load_tasks(self, *args):
        """Load and display tasks"""
        if self.current_category:
            tasks = task_manager.get_tasks_by_category(self.current_category)
        else:
            tasks = task_manager.get_all_tasks()
        
        self.kanban.set_tasks(tasks)
    
    def _on_search_changed(self, text: str):
        """Handle search input change with debounce"""
        self.search_timer.stop()
        self.search_timer.start(300)
    
    def _perform_search(self):
        """Execute search"""
        query = self.search_input.text().strip()
        if query:
            tasks = task_manager.search_tasks(query)
            if self.current_category:
                tasks = [t for t in tasks if t.get('category') == self.current_category]
            self.kanban.set_tasks(tasks)
        else:
            self._load_tasks()
    
    def _on_filter_changed(self, text: str):
        """Handle category filter change"""
        if text == "Todas las categorias":
            self.current_category = None
        else:
            self.current_category = text
        self._load_tasks()
    
    def _on_status_changed(self, task: dict, new_status: str):
        """Handle task status change from drag & drop"""
        task_id = task.get('id')
        if task_id:
            task_manager.update_task(task_id, status=new_status)
    
    def _on_task_clicked(self, task: dict):
        """Handle task click"""
        dialog = TaskDetailDialog(task, self)
        dialog.task_updated.connect(self._on_task_updated)
        dialog.task_deleted.connect(self._on_task_deleted)
        dialog.exec()
    
    def _on_task_updated(self, task: dict):
        """Handle task update from dialog"""
        task_id = task.get('id')
        if task_id:
            task_manager.update_task(
                task_id,
                status=task.get('status'),
                priority=task.get('priority'),
                deadline=task.get('deadline')
            )
    
    def _on_task_deleted(self, task_id: int):
        """Handle task deletion"""
        task_manager.delete_task(task_id)
    
    def _add_task(self):
        """Show add task dialog"""
        dialog = AddTaskDialog(
            default_category=self.current_category,
            parent=self
        )
        dialog.task_created.connect(self._create_task)
        dialog.exec()
    
    def _add_task_with_status(self, status: str):
        """Show add task dialog with preset status"""
        dialog = AddTaskDialog(
            default_status=status,
            default_category=self.current_category,
            parent=self
        )
        dialog.task_created.connect(self._create_task)
        dialog.exec()
    
    def _create_task(self, task: dict):
        """Create a new task"""
        task_manager.add_task(
            title=task['title'],
            category=task['category'],
            description=task.get('description', ''),
            status=task.get('status', 'pendiente'),
            priority=task.get('priority', 'media'),
            deadline=task.get('deadline'),
            tags=task.get('tags', [])
        )
    
    def refresh(self):
        """Refresh view"""
        self._load_tasks()
