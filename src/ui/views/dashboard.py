"""
Dashboard View - Today's overview
"""
from datetime import datetime, timedelta
from typing import List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.utils.styles import (
    COLORS, FONT_FAMILY, get_button_style, get_scroll_area_style
)
from src.utils.constants import DAYS_ES
from src.core.task_manager import task_manager
from src.core.database import db
from src.ui.widgets.common import TaskCard, StatCard, SectionHeader, EmptyState
from src.ui.widgets.pomodoro import MiniPomodoro


class DashboardView(QWidget):
    """Main dashboard with today's overview"""
    
    task_clicked = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self._load_data()
        
        # Connect to task updates
        # task_manager.tasks_updated.connect(self._load_data)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header with date
        header_layout = QHBoxLayout()
        
        now = datetime.now()
        date_text = f"{DAYS_ES[now.weekday()]}, {now.strftime('%d de ')}"\
                   f"{['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'][now.month-1]}"
        
        self.date_label = QLabel(date_text)
        self.date_label.setFont(QFont(FONT_FAMILY, 20, QFont.Weight.Bold))
        self.date_label.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        header_layout.addWidget(self.date_label)
        
        header_layout.addStretch()
        
        # Today button
        today_btn = QPushButton("📅 Hoy")
        today_btn.setFont(QFont(FONT_FAMILY, 10))
        today_btn.setStyleSheet(get_button_style('primary'))
        header_layout.addWidget(today_btn)
        
        layout.addLayout(header_layout)
        
        # Main content area with scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(get_scroll_area_style())
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(20)
        
        # Stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        self.today_tasks_stat = StatCard("Tareas Hoy", "0", "📋", COLORS['danger'])
        stats_layout.addWidget(self.today_tasks_stat)
        
        self.in_progress_stat = StatCard("En Progreso", "0", "🔄", COLORS['primary'])
        stats_layout.addWidget(self.in_progress_stat)
        
        self.week_completed_stat = StatCard("Completadas (Semana)", "0", "✅", COLORS['success'])
        stats_layout.addWidget(self.week_completed_stat)
        
        self.pomodoros_stat = StatCard("Pomodoros Hoy", "0", "🍅", COLORS['danger'])
        stats_layout.addWidget(self.pomodoros_stat)
        
        content_layout.addLayout(stats_layout)
        
        # Two column layout
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)
        
        # Left column - Tasks
        left_column = QVBoxLayout()
        left_column.setSpacing(16)
        
        # Today's deadlines section
        today_header = SectionHeader("🔴 Deadlines de Hoy", "Ver todas", "→")
        left_column.addWidget(today_header)
        
        self.today_tasks_container = QWidget()
        self.today_tasks_layout = QVBoxLayout(self.today_tasks_container)
        self.today_tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.today_tasks_layout.setSpacing(8)
        left_column.addWidget(self.today_tasks_container)
        
        # In progress section
        progress_header = SectionHeader("🔄 En Progreso")
        left_column.addWidget(progress_header)
        
        self.progress_tasks_container = QWidget()
        self.progress_tasks_layout = QVBoxLayout(self.progress_tasks_container)
        self.progress_tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_tasks_layout.setSpacing(8)
        left_column.addWidget(self.progress_tasks_container)
        
        # Upcoming deadlines
        upcoming_header = SectionHeader("📅 Próximos Deadlines (7 días)")
        left_column.addWidget(upcoming_header)
        
        self.upcoming_container = QWidget()
        self.upcoming_layout = QVBoxLayout(self.upcoming_container)
        self.upcoming_layout.setContentsMargins(0, 0, 0, 0)
        self.upcoming_layout.setSpacing(8)
        left_column.addWidget(self.upcoming_container)
        
        left_column.addStretch()
        
        columns_layout.addLayout(left_column, 2)
        
        # Right column - Pomodoro & Overdue
        right_column = QVBoxLayout()
        right_column.setSpacing(16)
        
        # Mini Pomodoro
        pomodoro_frame = QFrame()
        pomodoro_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(40, 40, 45, 150);
                border: 1px solid rgba({COLORS['danger']}, 0.3);
                border-radius: 12px;
            }}
        """)
        pomodoro_layout = QVBoxLayout(pomodoro_frame)
        pomodoro_layout.setContentsMargins(16, 16, 16, 16)
        
        self.pomodoro = MiniPomodoro()
        self.pomodoro.session_completed.connect(self._on_pomodoro_completed)
        pomodoro_layout.addWidget(self.pomodoro)
        
        right_column.addWidget(pomodoro_frame)
        
        # Overdue tasks
        overdue_header = SectionHeader("⚠️ Tareas Vencidas")
        right_column.addWidget(overdue_header)
        
        self.overdue_container = QWidget()
        self.overdue_layout = QVBoxLayout(self.overdue_container)
        self.overdue_layout.setContentsMargins(0, 0, 0, 0)
        self.overdue_layout.setSpacing(8)
        right_column.addWidget(self.overdue_container)
        
        right_column.addStretch()
        
        columns_layout.addLayout(right_column, 1)
        
        content_layout.addLayout(columns_layout)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
    
    def _load_data(self):
        """Load all dashboard data"""
        # Today's tasks
        today_tasks = task_manager.get_today_tasks()
        self._populate_task_list(self.today_tasks_layout, today_tasks, "Sin deadlines para hoy 🎉")
        
        # In progress tasks
        in_progress = task_manager.get_in_progress_tasks()
        self._populate_task_list(self.progress_tasks_layout, in_progress[:5], "Sin tareas en progreso")
        
        # Upcoming deadlines
        upcoming = task_manager.get_upcoming_deadlines(7)
        # Exclude today's tasks
        today = datetime.now().strftime("%Y-%m-%d")
        upcoming = [t for t in upcoming if t.get('deadline') != today][:5]
        self._populate_task_list(self.upcoming_layout, upcoming, "Sin deadlines próximos")
        
        # Overdue tasks
        overdue = task_manager.get_overdue_tasks()
        self._populate_task_list(self.overdue_layout, overdue[:5], "Sin tareas vencidas ✅")
        
        # Update stats
        self.today_tasks_stat.update_value(str(len(today_tasks)))
        self.in_progress_stat.update_value(str(len(in_progress)))
        
        weekly_stats = db.get_weekly_stats()
        self.week_completed_stat.update_value(str(weekly_stats['tasks_completed']))
        self.pomodoros_stat.update_value(str(len(db.get_today_pomodoros())))
    
    def _populate_task_list(self, layout: QVBoxLayout, tasks: List[Dict], empty_msg: str):
        """Populate a task list container"""
        # Clear existing
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not tasks:
            empty = EmptyState(empty_msg, "📭")
            layout.addWidget(empty)
            return
        
        for task in tasks:
            card = TaskCard(task, compact=True)
            card.clicked.connect(self.task_clicked.emit)
            layout.addWidget(card)
    
    def _on_pomodoro_completed(self, session_type: str):
        """Handle pomodoro completion"""
        if session_type == 'work':
            self._load_data()
    
    def refresh(self):
        """Refresh dashboard data"""
        self._load_data()
