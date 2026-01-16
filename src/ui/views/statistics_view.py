"""
Statistics View - Productivity stats and charts
"""
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.utils.styles import COLORS, FONT_FAMILY, get_button_style
from src.core.database import db
from src.core.task_manager import task_manager
from src.core.signals import SignalHub
from src.ui.widgets.common import StatCard


class StatisticsView(QWidget):
    """Statistics and productivity view"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = SignalHub.get_instance()
        self.setup_ui()
        self._load_stats()
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect to signal hub"""
        self.signals.task_added.connect(self._load_stats)
        self.signals.task_updated.connect(self._load_stats)
        self.signals.task_deleted.connect(self._load_stats)
        self.signals.pomodoro_completed.connect(self._load_stats)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Header
        title = QLabel("Estadisticas")
        title.setFont(QFont(FONT_FAMILY, 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        layout.addWidget(title)
        
        # Time period tabs
        period_layout = QHBoxLayout()
        
        self.week_btn = QPushButton("Esta Semana")
        self.week_btn.setFont(QFont(FONT_FAMILY, 10))
        self.week_btn.setStyleSheet(get_button_style('primary'))
        self.week_btn.setCheckable(True)
        self.week_btn.setChecked(True)
        self.week_btn.clicked.connect(lambda: self._set_period('week'))
        period_layout.addWidget(self.week_btn)
        
        self.month_btn = QPushButton("Este Mes")
        self.month_btn.setFont(QFont(FONT_FAMILY, 10))
        self.month_btn.setStyleSheet(get_button_style())
        self.month_btn.setCheckable(True)
        self.month_btn.clicked.connect(lambda: self._set_period('month'))
        period_layout.addWidget(self.month_btn)
        
        period_layout.addStretch()
        layout.addLayout(period_layout)
        
        # Stats grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(16)
        
        # Row 1 - Main stats (no emojis)
        self.tasks_completed_card = StatCard("Tareas Completadas", "0", "", COLORS['success'])
        stats_grid.addWidget(self.tasks_completed_card, 0, 0)
        
        self.pomodoros_card = StatCard("Pomodoros", "0", "", COLORS['danger'])
        stats_grid.addWidget(self.pomodoros_card, 0, 1)
        
        self.focus_time_card = StatCard("Tiempo de Enfoque", "0h", "", COLORS['primary'])
        stats_grid.addWidget(self.focus_time_card, 0, 2)
        
        self.pending_card = StatCard("Pendientes", "0", "", COLORS['warning'])
        stats_grid.addWidget(self.pending_card, 0, 3)
        
        layout.addLayout(stats_grid)
        
        # Progress section
        progress_frame = QFrame()
        progress_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(40, 40, 45, 150);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
            }}
        """)
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(20, 20, 20, 20)
        progress_layout.setSpacing(16)
        
        progress_title = QLabel("Progreso por Categoria")
        progress_title.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        progress_title.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        progress_layout.addWidget(progress_title)
        
        # Category progress bars
        self.category_progress = {}
        categories = [
            ("Personal", COLORS['personal']),
            ("Universidad", COLORS['universidad']),
            ("Fedora", COLORS['fedora'])
        ]
        
        for cat_name, color in categories:
            cat_layout = QVBoxLayout()
            cat_layout.setSpacing(4)
            
            cat_header = QHBoxLayout()
            cat_label = QLabel(cat_name)
            cat_label.setFont(QFont(FONT_FAMILY, 10))
            cat_label.setStyleSheet(f"color: rgb({color}); background: transparent;")
            cat_header.addWidget(cat_label)
            
            cat_count = QLabel("0/0")
            cat_count.setFont(QFont(FONT_FAMILY, 9))
            cat_count.setStyleSheet(f"color: rgb({COLORS['text_muted']}); background: transparent;")
            cat_header.addStretch()
            cat_header.addWidget(cat_count)
            
            cat_layout.addLayout(cat_header)
            
            progress_bar = QProgressBar()
            progress_bar.setMaximum(100)
            progress_bar.setValue(0)
            progress_bar.setTextVisible(False)
            progress_bar.setFixedHeight(8)
            progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: rgba(255, 255, 255, 0.05);
                    border: none;
                    border-radius: 4px;
                }}
                QProgressBar::chunk {{
                    background-color: rgba({color}, 200);
                    border-radius: 4px;
                }}
            """)
            cat_layout.addWidget(progress_bar)
            
            self.category_progress[cat_name] = {
                'bar': progress_bar,
                'count': cat_count
            }
            
            progress_layout.addLayout(cat_layout)
        
        layout.addWidget(progress_frame)
        
        # Recent activity section
        activity_frame = QFrame()
        activity_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(40, 40, 45, 150);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
            }}
        """)
        activity_layout = QVBoxLayout(activity_frame)
        activity_layout.setContentsMargins(20, 20, 20, 20)
        activity_layout.setSpacing(12)
        
        activity_title = QLabel("Resumen")
        activity_title.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        activity_title.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        activity_layout.addWidget(activity_title)
        
        self.summary_label = QLabel()
        self.summary_label.setFont(QFont(FONT_FAMILY, 10))
        self.summary_label.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
        self.summary_label.setWordWrap(True)
        activity_layout.addWidget(self.summary_label)
        
        layout.addWidget(activity_frame)
        layout.addStretch()
    
    def _set_period(self, period: str):
        """Set the time period for stats"""
        self.week_btn.setChecked(period == 'week')
        self.month_btn.setChecked(period == 'month')
        
        self.week_btn.setStyleSheet(get_button_style('primary' if period == 'week' else 'default'))
        self.month_btn.setStyleSheet(get_button_style('primary' if period == 'month' else 'default'))
        
        self._load_stats(period)
    
    def _load_stats(self, *args):
        """Load statistics for the given period"""
        period = 'week' if self.week_btn.isChecked() else 'month'
        
        if period == 'week':
            stats = db.get_weekly_stats()
            period_name = "esta semana"
        else:
            stats = db.get_monthly_stats()
            period_name = "este mes"
        
        # Update cards
        self.tasks_completed_card.update_value(str(stats['tasks_completed']))
        self.pomodoros_card.update_value(str(stats['pomodoros_completed']))
        
        hours = stats['total_focus_minutes'] // 60
        mins = stats['total_focus_minutes'] % 60
        self.focus_time_card.update_value(f"{hours}h {mins}m" if hours else f"{mins}m")
        
        # Update category progress
        all_tasks = task_manager.get_all_tasks()
        
        # Update pending count
        pending = len([t for t in all_tasks if t.get('status') == 'pendiente'])
        self.pending_card.update_value(str(pending))
        
        for cat_name in self.category_progress:
            cat_tasks = [t for t in all_tasks if t.get('category') == cat_name]
            completed = len([t for t in cat_tasks if t.get('status') == 'completado'])
            total = len(cat_tasks)
            
            progress = int((completed / total * 100)) if total > 0 else 0
            
            self.category_progress[cat_name]['bar'].setValue(progress)
            self.category_progress[cat_name]['count'].setText(f"{completed}/{total}")
        
        # Update summary
        in_progress = len([t for t in all_tasks if t.get('status') == 'en progreso'])
        completed = len([t for t in all_tasks if t.get('status') == 'completado'])
        
        self.summary_label.setText(
            f"Tienes {pending} tareas pendientes, {in_progress} en progreso y "
            f"has completado {stats['tasks_completed']} tareas {period_name}. "
            f"Has completado {stats['pomodoros_completed']} sesiones Pomodoro "
            f"({stats['total_focus_minutes']} minutos de enfoque)."
        )
    
    def refresh(self):
        """Refresh statistics"""
        self._load_stats()
