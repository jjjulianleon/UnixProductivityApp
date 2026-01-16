"""
Desktop Widget - Compact 520x320 widget for KDE Plasma
"""
import sys
import subprocess
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from src.utils.styles import (
    COLORS, FONT_FAMILY, get_button_style, get_widget_style,
    get_tab_style, get_scroll_area_style
)
from src.utils.constants import WIDGET_WIDTH, WIDGET_HEIGHT, DAYS_ES
from src.core.task_manager import task_manager
from src.core.database import db
from src.ui.widgets.calendar import MonthlyCalendar
from src.ui.widgets.schedule import WeeklySchedule
from src.ui.widgets.pomodoro import MiniPomodoro
from src.ui.widgets.common import TaskCard, EmptyState
from src.ui.widgets.quick_notes import QuickNoteDialog
from src.ui.dialogs.task_dialogs import TaskDetailDialog, DeadlineTasksDialog


class CompactKanban(QWidget):
    """Compact Kanban view for widget"""
    
    task_clicked = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self._load_tasks()
        
        # task_manager.tasks_updated.connect(self._load_tasks)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Tabs for statuses
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(get_tab_style())
        
        # Pendiente tab
        self.pending_scroll = self._create_scroll_area()
        self.pending_layout = self.pending_scroll.widget().layout()
        self.tabs.addTab(self.pending_scroll, "📋 Pendiente")
        
        # En progreso tab
        self.progress_scroll = self._create_scroll_area()
        self.progress_layout = self.progress_scroll.widget().layout()
        self.tabs.addTab(self.progress_scroll, "🔄 Progreso")
        
        layout.addWidget(self.tabs)
    
    def _create_scroll_area(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(get_scroll_area_style())
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(6)
        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def _load_tasks(self):
        """Load tasks into tabs"""
        # Clear existing
        for layout in [self.pending_layout, self.progress_layout]:
            while layout.count() > 1:
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        all_tasks = task_manager.get_all_tasks()
        
        pending = [t for t in all_tasks if t.get('status') == 'pendiente'][:8]
        in_progress = [t for t in all_tasks if t.get('status') == 'en progreso'][:8]
        
        self._populate_list(self.pending_layout, pending, "Sin tareas pendientes")
        self._populate_list(self.progress_layout, in_progress, "Sin tareas en progreso")
        
        # Update tab titles with counts
        self.tabs.setTabText(0, f"📋 Pendiente ({len(pending)})")
        self.tabs.setTabText(1, f"🔄 Progreso ({len(in_progress)})")
    
    def _populate_list(self, layout: QVBoxLayout, tasks: list, empty_msg: str):
        if not tasks:
            empty = EmptyState(empty_msg, "✅")
            layout.insertWidget(0, empty)
            return
        
        for task in tasks:
            card = TaskCard(task, compact=True)
            card.clicked.connect(self.task_clicked.emit)
            layout.insertWidget(layout.count() - 1, card)


class DeadlinesList(QWidget):
    """Today/Tomorrow deadlines list"""
    
    task_clicked = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self._load_tasks()
        
        # task_manager.tasks_updated.connect(self._load_tasks)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header
        header = QLabel("⏰ Próximos Deadlines")
        header.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        header.setStyleSheet(f"color: rgb({COLORS['danger']}); background: transparent;")
        layout.addWidget(header)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(get_scroll_area_style())
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.tasks_widget = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_widget)
        self.tasks_layout.setContentsMargins(0, 0, 4, 0)
        self.tasks_layout.setSpacing(6)
        self.tasks_layout.addStretch()
        
        scroll.setWidget(self.tasks_widget)
        layout.addWidget(scroll, 1)
    
    def _load_tasks(self):
        # Clear existing
        while self.tasks_layout.count() > 1:
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get today and tomorrow tasks
        today_tasks = task_manager.get_today_tasks()
        tomorrow_tasks = task_manager.get_tomorrow_tasks()
        
        all_deadline_tasks = []
        
        # Add today's tasks with marker
        for task in today_tasks:
            task['_deadline_label'] = '🔴 HOY'
            all_deadline_tasks.append(task)
        
        # Add tomorrow's tasks with marker
        for task in tomorrow_tasks:
            task['_deadline_label'] = '🟠 Mañana'
            all_deadline_tasks.append(task)
        
        if not all_deadline_tasks:
            empty = EmptyState("Sin deadlines próximos 🎉", "📅")
            self.tasks_layout.insertWidget(0, empty)
            return
        
        for task in all_deadline_tasks[:10]:
            card = self._create_task_card(task)
            self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, card)
    
    def _create_task_card(self, task: dict) -> QFrame:
        from src.utils.styles import get_category_color
        
        category = task.get('category', '')
        color = get_category_color(category)
        
        card = QFrame()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(50, 50, 55, 150);
                border-left: 3px solid rgba({color}, 200);
                border-radius: 6px;
            }}
            QFrame:hover {{
                background-color: rgba(60, 60, 65, 180);
            }}
        """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        # Deadline label
        deadline_label = QLabel(task.get('_deadline_label', ''))
        deadline_label.setFont(QFont(FONT_FAMILY, 8))
        deadline_label.setStyleSheet(f"color: rgb({COLORS['danger']}); background: transparent;")
        deadline_label.setFixedWidth(60)
        layout.addWidget(deadline_label)
        
        # Title
        title = QLabel(task.get('title', '')[:30])
        title.setFont(QFont(FONT_FAMILY, 9))
        title.setStyleSheet(f"color: rgb({color}); background: transparent;")
        layout.addWidget(title, 1)
        
        card.mousePressEvent = lambda e, t=task: self.task_clicked.emit(t)
        
        return card


class DesktopWidget(QWidget):
    """Compact desktop widget (520x320)"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UnixProductivityApp Widget")
        self.setFixedSize(WIDGET_WIDTH, WIDGET_HEIGHT)
        
        # Widget flags for desktop widget behavior
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnBottomHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
        self._start_clock()
    
    def setup_ui(self):
        # Main container with glassmorphism
        container = QFrame(self)
        container.setGeometry(0, 0, WIDGET_WIDTH, WIDGET_HEIGHT)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(25, 25, 30, 220);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        # Header with time and buttons
        header = QHBoxLayout()
        
        self.time_label = QLabel()
        self.time_label.setFont(QFont(FONT_FAMILY, 10))
        self.time_label.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
        header.addWidget(self.time_label)
        
        header.addStretch()
        
        # Quick note button
        note_btn = QPushButton("📝")
        note_btn.setFont(QFont(FONT_FAMILY, 12))
        note_btn.setFixedSize(28, 28)
        note_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba({COLORS['warning']}, 0.2);
                color: rgb({COLORS['warning']});
                border: none;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba({COLORS['warning']}, 0.4);
            }}
        """)
        note_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        note_btn.setToolTip("Nueva nota rápida")
        note_btn.clicked.connect(self._add_quick_note)
        header.addWidget(note_btn)
        
        # Open main app button
        app_btn = QPushButton("🚀")
        app_btn.setFont(QFont(FONT_FAMILY, 12))
        app_btn.setFixedSize(28, 28)
        app_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba({COLORS['primary']}, 0.2);
                color: rgb({COLORS['primary']});
                border: none;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba({COLORS['primary']}, 0.4);
            }}
        """)
        app_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        app_btn.setToolTip("Abrir aplicación")
        app_btn.clicked.connect(self._open_main_app)
        header.addWidget(app_btn)
        
        layout.addLayout(header)
        
        # Main content tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(get_tab_style() + """
            QTabBar::tab {
                padding: 4px 10px;
                font-size: 9px;
            }
        """)
        
        # Calendar tab
        self.calendar = MonthlyCalendar(compact=True)
        self.calendar.deadline_clicked.connect(self._on_deadline_clicked)
        self.tabs.addTab(self.calendar, "📆")
        
        # Schedule tab
        self.schedule = WeeklySchedule(compact=True)
        self.tabs.addTab(self.schedule, "📋")
        
        # Kanban tab
        self.kanban = CompactKanban()
        self.kanban.task_clicked.connect(self._on_task_clicked)
        self.tabs.addTab(self.kanban, "📌")
        
        # Deadlines tab
        self.deadlines = DeadlinesList()
        self.deadlines.task_clicked.connect(self._on_task_clicked)
        self.tabs.addTab(self.deadlines, "⏰")
        
        # Pomodoro tab
        self.pomodoro = MiniPomodoro()
        self.tabs.addTab(self.pomodoro, "🍅")
        
        layout.addWidget(self.tabs, 1)
        
        # Sync deadlines to calendar
        self._sync_deadlines()
        # task_manager.tasks_updated.connect(self._sync_deadlines)
    
    def _start_clock(self):
        """Start the clock timer"""
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_time)
        self.clock_timer.start(1000)
        self._update_time()
    
    def _update_time(self):
        """Update time display"""
        now = datetime.now()
        day_name = DAYS_ES[now.weekday()]
        self.time_label.setText(
            f"{day_name}, {now.strftime('%d/%m/%Y')} • {now.strftime('%H:%M:%S')}"
        )
    
    def _sync_deadlines(self):
        """Sync deadlines to calendar"""
        tasks = task_manager.get_tasks_with_deadlines()
        self.calendar.set_deadlines(tasks)
    
    def _on_deadline_clicked(self, tasks: list):
        """Handle deadline click in calendar"""
        if len(tasks) == 1:
            self._on_task_clicked(tasks[0])
        else:
            dialog = DeadlineTasksDialog(tasks, self)
            dialog.exec()
    
    def _on_task_clicked(self, task: dict):
        """Handle task click"""
        dialog = TaskDetailDialog(task, self)
        dialog.task_updated.connect(self._on_task_updated)
        dialog.exec()
    
    def _on_task_updated(self, task: dict):
        """Handle task update"""
        task_id = task.get('id')
        if task_id:
            task_manager.update_task(task_id, status=task.get('status'))
    
    def _add_quick_note(self):
        """Show quick note dialog"""
        dialog = QuickNoteDialog(self)
        dialog.note_created.connect(self._create_quick_note)
        dialog.exec()
    
    def _create_quick_note(self, title: str, content: str):
        """Create quick note"""
        from src.core.obsidian_sync import ObsidianSync
        obsidian = ObsidianSync()
        obsidian.create_quick_note(title, content)
        db.add_quick_note(title, content)
    
    def _open_main_app(self):
        """Open the main application"""
        try:
            subprocess.Popen([sys.executable, "main_app.py"], 
                           cwd="/home/jjulianleon/Desktop/CalendarWidget")
        except Exception as e:
            print(f"Error opening main app: {e}")
    
    def mousePressEvent(self, event):
        """Allow dragging the widget"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        """Handle widget dragging"""
        if hasattr(self, '_drag_pos') and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)


def main():
    """Widget entry point"""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    widget = DesktopWidget()
    widget.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
