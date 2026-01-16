"""
Kanban Board Widget with improved drag & drop
"""
import json
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent

from src.utils.styles import COLORS, FONT_FAMILY, get_button_style, get_scroll_area_style
from src.utils.constants import TASK_STATUSES
from src.core.task_manager import task_manager
from .common import DraggableTaskCard, EmptyState


class KanbanColumn(QFrame):
    """Single column in Kanban board with reordering support"""
    
    task_dropped = pyqtSignal(dict, str, int)  # task, new_status, position
    task_clicked = pyqtSignal(dict)
    add_task_requested = pyqtSignal(str)  # status
    
    def __init__(self, status: str, title: str, color: str, parent=None):
        super().__init__(parent)
        self.status = status
        self.title = title
        self.color = color
        self.tasks: List[Dict] = []
        
        self.setAcceptDrops(True)
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(40, 40, 45, 150);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 10px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Status indicator (circle instead of emoji)
        title_label = QLabel(f"[{self.title}]")
        title_label.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: rgb({self.color}); background: transparent;")
        header_layout.addWidget(title_label)
        
        self.count_label = QLabel("0")
        self.count_label.setFont(QFont(FONT_FAMILY, 9))
        self.count_label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba({self.color}, 0.2);
                color: rgb({self.color});
                border-radius: 10px;
                padding: 2px 8px;
            }}
        """)
        header_layout.addWidget(self.count_label)
        
        header_layout.addStretch()
        
        add_btn = QPushButton("+")
        add_btn.setFont(QFont(FONT_FAMILY, 12))
        add_btn.setFixedSize(24, 24)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba({self.color}, 0.2);
                color: rgb({self.color});
                border: none;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background-color: rgba({self.color}, 0.4);
            }}
        """)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(lambda: self.add_task_requested.emit(self.status))
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Tasks scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(get_scroll_area_style())
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.tasks_widget = QWidget()
        self.tasks_widget.setAcceptDrops(True)
        self.tasks_layout = QVBoxLayout(self.tasks_widget)
        self.tasks_layout.setContentsMargins(0, 0, 4, 0)
        self.tasks_layout.setSpacing(6)
        self.tasks_layout.addStretch()
        
        scroll.setWidget(self.tasks_widget)
        layout.addWidget(scroll, 1)
    
    def set_tasks(self, tasks: List[Dict]):
        """Set tasks for this column"""
        self.tasks = tasks
        
        # Clear existing cards
        while self.tasks_layout.count() > 1:
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add new cards with position tracking
        for idx, task in enumerate(tasks):
            task['_position'] = idx
            card = DraggableTaskCard(task, compact=True)
            card.clicked.connect(self.task_clicked.emit)
            self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, card)
        
        # Update count
        self.count_label.setText(str(len(tasks)))
        
        # Show empty state if no tasks
        if not tasks:
            empty = EmptyState("Sin tareas")
            self.tasks_layout.insertWidget(0, empty)
    
    def _get_drop_position(self, y_pos: int) -> int:
        """Calculate drop position based on Y coordinate"""
        for i in range(self.tasks_layout.count() - 1):  # -1 to skip stretch
            widget = self.tasks_layout.itemAt(i).widget()
            if widget and isinstance(widget, DraggableTaskCard):
                widget_center = widget.y() + widget.height() // 2
                if y_pos < widget_center:
                    return i
        return len(self.tasks)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText() or event.mimeData().hasFormat("application/x-task"):
            event.acceptProposedAction()
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(40, 40, 45, 150);
                    border: 2px solid rgba({self.color}, 0.5);
                    border-radius: 10px;
                }}
            """)
    
    def dragMoveEvent(self, event):
        """Track drag position for reordering"""
        event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(40, 40, 45, 150);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 10px;
            }}
        """)
    
    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(40, 40, 45, 150);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 10px;
            }}
        """)
        
        try:
            # Get task data
            if event.mimeData().hasFormat("application/x-task"):
                task_json = event.mimeData().data("application/x-task").data().decode()
            else:
                task_json = event.mimeData().text()
            
            task = json.loads(task_json)
            
            # Calculate drop position
            drop_pos = self._get_drop_position(event.position().toPoint().y())
            
            self.task_dropped.emit(task, self.status, drop_pos)
            event.acceptProposedAction()
        except (json.JSONDecodeError, Exception) as e:
            event.ignore()


class KanbanBoard(QWidget):
    """Full Kanban board with three columns and reordering"""
    
    task_status_changed = pyqtSignal(dict, str)
    task_position_changed = pyqtSignal(dict, str, int)
    task_clicked = pyqtSignal(dict)
    add_task_requested = pyqtSignal(str)
    
    def __init__(self, compact: bool = False, parent=None):
        super().__init__(parent)
        self.compact = compact
        self.columns: Dict[str, KanbanColumn] = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        margin = 8 if self.compact else 16
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(12)
        
        column_configs = [
            ("pendiente", "Pendiente", COLORS['warning']),
            ("en progreso", "En Progreso", COLORS['primary']),
            ("completado", "Completado", COLORS['success']),
        ]
        
        for status, title, color in column_configs:
            column = KanbanColumn(status, title, color)
            column.task_dropped.connect(self._on_task_dropped)
            column.task_clicked.connect(self.task_clicked.emit)
            column.add_task_requested.connect(self.add_task_requested.emit)
            
            self.columns[status] = column
            layout.addWidget(column, 1)
    
    def _on_task_dropped(self, task: Dict, new_status: str, position: int):
        """Handle task drop with position"""
        old_status = task.get('status', 'pendiente')
        task_id = task.get('id')
        
        if old_status != new_status:
            # Status changed - emit status change
            self.task_status_changed.emit(task, new_status)
        
        # Update position
        if task_id:
            task_manager.update_task_position(task_id, new_status, position)
    
    def set_tasks(self, tasks: List[Dict]):
        """Distribute tasks to columns, sorted by position"""
        by_status = {
            "pendiente": [],
            "en progreso": [],
            "completado": []
        }
        
        for task in tasks:
            status = task.get('status', 'pendiente')
            if status in by_status:
                by_status[status].append(task)
        
        # Sort each status by position
        for status in by_status:
            by_status[status].sort(key=lambda t: t.get('position', 999))
        
        for status, column in self.columns.items():
            column.set_tasks(by_status.get(status, []))
    
    def set_tasks_by_category(self, tasks: List[Dict], category: Optional[str] = None):
        """Set tasks filtered by category"""
        if category:
            filtered = [t for t in tasks if t.get('category') == category]
        else:
            filtered = tasks
        self.set_tasks(filtered)
