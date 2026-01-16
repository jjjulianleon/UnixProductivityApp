"""
Calendar View - Monthly calendar with weekly schedule
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.utils.styles import COLORS, FONT_FAMILY, get_button_style, get_tab_style
from src.core.task_manager import task_manager
from src.ui.widgets.calendar import MonthlyCalendar
from src.ui.widgets.schedule import WeeklySchedule
from src.ui.dialogs.task_dialogs import TaskDetailDialog, DeadlineTasksDialog


class CalendarView(QWidget):
    """Full calendar view with monthly and weekly tabs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self._sync_deadlines()
        
        # Connect to updates
        # task_manager.tasks_updated.connect(self._sync_deadlines)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📅 Calendario")
        title.setFont(QFont(FONT_FAMILY, 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Today button
        today_btn = QPushButton("Hoy")
        today_btn.setFont(QFont(FONT_FAMILY, 10))
        today_btn.setStyleSheet(get_button_style('primary'))
        today_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        today_btn.clicked.connect(self._go_to_today)
        header_layout.addWidget(today_btn)
        
        layout.addLayout(header_layout)
        
        # Tab widget for month/week views
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(get_tab_style())
        
        # Monthly calendar
        self.monthly = MonthlyCalendar()
        self.monthly.deadline_clicked.connect(self._on_deadline_clicked)
        self.tabs.addTab(self.monthly, "📆 Mes")
        
        # Weekly schedule
        self.weekly = WeeklySchedule()
        self.tabs.addTab(self.weekly, "📋 Semana")
        
        layout.addWidget(self.tabs, 1)
    
    def _sync_deadlines(self):
        """Sync deadlines from tasks to calendar"""
        tasks = task_manager.get_tasks_with_deadlines()
        self.monthly.set_deadlines(tasks)
    
    def _on_deadline_clicked(self, tasks: list):
        """Handle click on deadline in calendar"""
        if len(tasks) == 1:
            dialog = TaskDetailDialog(tasks[0], self)
            dialog.task_updated.connect(self._on_task_updated)
            dialog.exec()
        else:
            dialog = DeadlineTasksDialog(tasks, self)
            dialog.exec()
    
    def _on_task_updated(self, task: dict):
        """Handle task update"""
        task_id = task.get('id')
        if task_id:
            task_manager.update_task(
                task_id,
                status=task.get('status')
            )
    
    def _go_to_today(self):
        """Navigate to today in both views"""
        self.monthly.go_to_today()
        self.weekly.go_to_today()
    
    def refresh(self):
        """Refresh view"""
        self._sync_deadlines()
