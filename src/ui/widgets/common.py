"""
Shared UI components - Reusable widgets
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QPoint
from PyQt6.QtGui import QFont, QDrag, QCursor, QPixmap, QPainter, QColor

from src.utils.styles import (
    COLORS, FONT_FAMILY, get_button_style, get_card_style,
    get_category_color, get_priority_color, get_deadline_color
)


class TaskCard(QFrame):
    """Reusable task card widget"""
    
    clicked = pyqtSignal(dict)
    status_changed = pyqtSignal(dict, str)
    
    def __init__(self, task: Dict, compact: bool = False, parent=None):
        super().__init__(parent)
        self.task = task
        self.compact = compact
        self.setup_ui()
    
    def setup_ui(self):
        category = self.task.get('category', '')
        color = get_category_color(category)
        priority = self.task.get('priority', 'media')
        priority_color = get_priority_color(priority)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(50, 50, 55, 180);
                border-left: 3px solid rgba({color}, 200);
                border-radius: 8px;
            }}
            QFrame:hover {{
                background-color: rgba(60, 60, 65, 200);
            }}
        """)
        
        layout = QVBoxLayout(self)
        padding = 8 if self.compact else 12
        layout.setContentsMargins(padding, padding - 2, padding, padding - 2)
        layout.setSpacing(4 if self.compact else 6)
        
        # Title
        title = self.task.get('title', self.task.get('text', ''))
        title_label = QLabel(title)
        font_size = 9 if self.compact else 10
        title_label.setFont(QFont(FONT_FAMILY, font_size, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: rgb({color}); background: transparent; border: none;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Description (only if not compact and has description)
        if not self.compact:
            desc = self.task.get('description', '')
            if desc:
                desc_label = QLabel(desc[:100] + "..." if len(desc) > 100 else desc)
                desc_label.setFont(QFont(FONT_FAMILY, 9))
                desc_label.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent; border: none;")
                desc_label.setWordWrap(True)
                layout.addWidget(desc_label)
        
        # Bottom row: priority indicator + deadline
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)
        
        # Priority indicator (dot)
        priority_dot = QLabel("[" + priority[0].upper() + "]")
        priority_dot.setFont(QFont(FONT_FAMILY, 7))
        priority_dot.setStyleSheet(f"color: rgb({priority_color}); background: transparent; border: none;")
        priority_dot.setToolTip(f"Prioridad: {priority.capitalize()}")
        bottom_layout.addWidget(priority_dot)
        
        # Deadline
        deadline = self.task.get('deadline')
        if deadline:
            try:
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
                days_until = (deadline_date - datetime.now().date()).days
                deadline_color = get_deadline_color(days_until)
                
                if days_until < 0:
                    deadline_text = "VENCIDO"
                elif days_until == 0:
                    deadline_text = "Hoy"
                elif days_until == 1:
                    deadline_text = "Manana"
                else:
                    deadline_text = deadline_date.strftime('%d/%m')
                
                deadline_label = QLabel(deadline_text)
                deadline_label.setFont(QFont(FONT_FAMILY, 8))
                deadline_label.setStyleSheet(f"color: rgb({deadline_color}); background: transparent; border: none;")
                bottom_layout.addWidget(deadline_label)
            except ValueError:
                pass
        
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.task)
        super().mousePressEvent(event)


class DraggableTaskCard(TaskCard):
    """Task card with drag & drop support for Kanban"""
    
    dropped = pyqtSignal(dict, str, int)  # task, new_status, new_position
    
    def __init__(self, task: Dict, compact: bool = False, parent=None):
        super().__init__(task, compact, parent)
        self._drag_start_pos = None
        self._is_dragging = False
        self.setAcceptDrops(True)
    
    def _create_drag_pixmap(self) -> QPixmap:
        """Create a semi-transparent pixmap of the card for dragging"""
        # Render the widget to a pixmap
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(0.85)
        self.render(painter)
        painter.end()
        
        return pixmap
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self._is_dragging = False
        event.accept()
    
    def mouseMoveEvent(self, event):
        if not self._drag_start_pos:
            return
        
        if self._is_dragging:
            return
        
        distance = (event.pos() - self._drag_start_pos).manhattanLength()
        if distance < 10:
            return
        
        self._is_dragging = True
        
        try:
            import json
            drag = QDrag(self)
            mime_data = QMimeData()
            
            # Serialize task data
            task_copy = {}
            for k, v in self.task.items():
                if isinstance(v, (str, int, float, bool, list, dict, type(None))):
                    task_copy[k] = v
                else:
                    task_copy[k] = str(v)
            
            task_json = json.dumps(task_copy)
            mime_data.setText(task_json)
            mime_data.setData("application/x-task", task_json.encode())
            
            drag.setMimeData(mime_data)
            
            # Create drag pixmap
            pixmap = self._create_drag_pixmap()
            drag.setPixmap(pixmap)
            drag.setHotSpot(self._drag_start_pos)
            
            # Make original card semi-transparent while dragging
            self.setStyleSheet(self.styleSheet().replace("150)", "80)"))
            
            drag.exec(Qt.DropAction.MoveAction)
            
            # Restore opacity
            self.setStyleSheet(self.styleSheet().replace("80)", "150)"))
            
        except (RuntimeError, TypeError, json.JSONDecodeError):
            pass
        finally:
            self._drag_start_pos = None
            self._is_dragging = False
    
    def mouseReleaseEvent(self, event):
        was_click = not self._is_dragging and self._drag_start_pos is not None
        self._drag_start_pos = None
        self._is_dragging = False
        
        if was_click and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.task)
        event.accept()


class StatCard(QFrame):
    """Statistics display card"""
    
    def __init__(self, title: str, value: str, icon: str = "", 
                 color: str = None, parent=None):
        super().__init__(parent)
        self._value_label = None
        self.setup_ui(title, value, icon, color or COLORS['primary'])
    
    def setup_ui(self, title: str, value: str, icon: str, color: str):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(50, 50, 55, 150);
                border: none;
                border-radius: 10px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        # Title (no icon - icons removed)
        header = QLabel(title)
        header.setFont(QFont(FONT_FAMILY, 9))
        header.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
        layout.addWidget(header)
        
        # Value
        self._value_label = QLabel(value)
        self._value_label.setFont(QFont(FONT_FAMILY, 18, QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: rgb({color}); background: transparent;")
        layout.addWidget(self._value_label)
    
    def update_value(self, value: str):
        """Update the displayed value"""
        if self._value_label:
            self._value_label.setText(value)


class SectionHeader(QWidget):
    """Section header with title and optional action button"""
    
    action_clicked = pyqtSignal()
    
    def __init__(self, title: str, action_text: str = None, 
                 action_icon: str = None, parent=None):
        super().__init__(parent)
        self.setup_ui(title, action_text, action_icon)
    
    def setup_ui(self, title: str, action_text: str, action_icon: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        
        # Title (no emoji)
        title_label = QLabel(title)
        title_label.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Action button
        if action_text:
            btn_text = f"{action_icon} {action_text}" if action_icon else action_text
            action_btn = QPushButton(btn_text)
            action_btn.setFont(QFont(FONT_FAMILY, 9))
            action_btn.setStyleSheet(get_button_style('primary'))
            action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            action_btn.clicked.connect(self.action_clicked.emit)
            layout.addWidget(action_btn)


class EmptyState(QWidget):
    """Empty state placeholder"""
    
    def __init__(self, message: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.setup_ui(message)
    
    def setup_ui(self, message: str):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 40, 20, 40)
        
        # Simple dash indicator instead of emoji
        dash_label = QLabel("---")
        dash_label.setFont(QFont(FONT_FAMILY, 20))
        dash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash_label.setStyleSheet(f"color: rgb({COLORS['text_muted']}); background: transparent;")
        layout.addWidget(dash_label)
        
        msg_label = QLabel(message)
        msg_label.setFont(QFont(FONT_FAMILY, 10))
        msg_label.setStyleSheet(f"color: rgb({COLORS['text_muted']}); background: transparent;")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg_label)
