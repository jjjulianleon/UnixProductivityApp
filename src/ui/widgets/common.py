"""
Shared UI components - Reusable widgets
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QFont, QDrag, QCursor

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
        
        # Priority dot
        priority_dot = QLabel("●")
        priority_dot.setFont(QFont(FONT_FAMILY, 6))
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
                    deadline_text = f"⚠️ Vencido"
                elif days_until == 0:
                    deadline_text = "📅 Hoy"
                elif days_until == 1:
                    deadline_text = "📅 Mañana"
                else:
                    deadline_text = f"📅 {deadline_date.strftime('%d/%m')}"
                
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
    
    def __init__(self, task: Dict, compact: bool = False, parent=None):
        super().__init__(task, compact, parent)
        self._drag_start_pos = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if not self._drag_start_pos:
            return
        
        if (event.pos() - self._drag_start_pos).manhattanLength() < 20:
            return
        
        try:
            drag = QDrag(self)
            mime_data = QMimeData()
            
            # Serialize task data
            import json
            task_json = json.dumps(self.task)
            mime_data.setText(task_json)
            
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.MoveAction)
        except RuntimeError:
            pass
        finally:
            self._drag_start_pos = None
    
    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        try:
            super().mouseReleaseEvent(event)
        except RuntimeError:
            pass


class StatCard(QFrame):
    """Statistics display card"""
    
    def __init__(self, title: str, value: str, icon: str = "", 
                 color: str = None, parent=None):
        super().__init__(parent)
        self.setup_ui(title, value, icon, color or COLORS['primary'])
    
    def setup_ui(self, title: str, value: str, icon: str, color: str):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(50, 50, 55, 150);
                border: 1px solid rgba({color}, 0.3);
                border-radius: 10px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        # Icon + Title
        header = QLabel(f"{icon} {title}" if icon else title)
        header.setFont(QFont(FONT_FAMILY, 9))
        header.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
        layout.addWidget(header)
        
        # Value
        value_label = QLabel(value)
        value_label.setFont(QFont(FONT_FAMILY, 18, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: rgb({color}); background: transparent;")
        layout.addWidget(value_label)
    
    def update_value(self, value: str):
        """Update the displayed value"""
        # Find and update the value label
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QLabel):
                font = widget.font()
                if font.pointSize() >= 18:
                    widget.setText(value)
                    break


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
        
        # Title
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
    
    def __init__(self, message: str, icon: str = "📭", parent=None):
        super().__init__(parent)
        self.setup_ui(message, icon)
    
    def setup_ui(self, message: str, icon: str):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont(FONT_FAMILY, 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)
        
        msg_label = QLabel(message)
        msg_label.setFont(QFont(FONT_FAMILY, 10))
        msg_label.setStyleSheet(f"color: rgb({COLORS['text_muted']}); background: transparent;")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg_label)
