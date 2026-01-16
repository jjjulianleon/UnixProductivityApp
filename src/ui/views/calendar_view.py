"""
Calendar View - Monthly calendar with weekly schedule
"""
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.utils.styles import COLORS, FONT_FAMILY, get_button_style, get_tab_style
from src.core.task_manager import task_manager
from src.core.database import db
from src.core.signals import SignalHub
from src.ui.widgets.calendar import MonthlyCalendar
from src.ui.widgets.schedule import WeeklySchedule
from src.ui.dialogs.task_dialogs import TaskDetailDialog, DeadlineTasksDialog, ScheduleEventDialog


class CalendarView(QWidget):
    """Full calendar view with monthly and weekly tabs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = SignalHub.get_instance()
        self.setup_ui()
        self._sync_deadlines()
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect to signal hub"""
        self.signals.task_added.connect(self._sync_deadlines)
        self.signals.task_updated.connect(self._sync_deadlines)
        self.signals.task_deleted.connect(self._sync_deadlines)
        self.signals.task_deleted.connect(self._sync_deadlines)
        self.signals.schedule_updated.connect(self._refresh_schedule)
        self.signals.teams_events_updated.connect(self._update_external_events)
    
    def _update_external_events(self, events: list):
        """Update external events in weekly view"""
        self.weekly.set_external_events(events)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Calendario")
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
        self.tabs.addTab(self.monthly, "Mes")
        
        # Weekly schedule
        self.weekly = WeeklySchedule()
        self.weekly.slot_clicked.connect(self._on_slot_clicked)
        self.weekly.event_clicked.connect(self._on_event_clicked)
        self.weekly.add_event_requested.connect(self._on_add_event)
        self.tabs.addTab(self.weekly, "Semana")
        
        layout.addWidget(self.tabs, 1)
    
    def _sync_deadlines(self, *args):
        """Sync deadlines from tasks to calendar"""
        tasks = task_manager.get_tasks_with_deadlines()
        self.monthly.set_deadlines(tasks)
    
    def _refresh_schedule(self):
        """Refresh the weekly schedule"""
        self.weekly._load_events()
    
    def _on_deadline_clicked(self, tasks: list):
        """Handle click on deadline in calendar"""
        if len(tasks) == 1:
            dialog = TaskDetailDialog(tasks[0], self)
            dialog.task_updated.connect(self._on_task_updated)
            dialog.exec()
        else:
            dialog = DeadlineTasksDialog(tasks, self)
            dialog.exec()
    
    def _on_slot_clicked(self, day_index: int, hour: int):
        """Handle click on schedule slot - open dialog to add event"""
        dialog = ScheduleEventDialog(day_index, hour, parent=self)
        dialog.event_saved.connect(self._on_event_saved)
        dialog.exec()
    
    def _on_add_event(self):
        """Handle + button click - open dialog with today's settings"""
        today = datetime.now()
        day_index = today.weekday()  # 0 = Monday
        hour = today.hour if 6 <= today.hour <= 22 else 9
        dialog = ScheduleEventDialog(day_index, hour, parent=self)
        dialog.event_saved.connect(self._on_event_saved)
        dialog.exec()
    
    def _on_event_saved(self, event_data: dict):
        """Handle event save"""
        target = event_data.get('target', 'local')
        
        if target == 'icloud':
            # Create iCloud event
            date_str = event_data.get('date')
            start_str = event_data.get('start_time')
            end_str = event_data.get('end_time')
            
            try:
                # Combine date and time
                start_dt = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
                end_dt = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M")
                
                if task_manager.icloud_sync:
                    success = task_manager.icloud_sync.add_event(
                        title=event_data['title'],
                        start=start_dt,
                        end=end_dt
                    )
                    if success:
                        # Trigger refresh to fetch new event
                        task_manager.sync_external_calendars()
            except Exception as e:
                print(f"Error creating iCloud event: {e}")
                
        else:
            # Local event logic
            event_id = event_data.get('id')
            if event_id:
                task_manager.update_schedule_event(
                    event_id,
                    title=event_data['title'],
                    day_of_week=event_data['day_of_week'],
                    start_time=event_data['start_time'],
                    end_time=event_data['end_time']
                )
            else:
                task_manager.add_schedule_event(
                    title=event_data['title'],
                    day_of_week=event_data['day_of_week'],
                    start_time=event_data['start_time'],
                    end_time=event_data['end_time'],
                    color=event_data.get('color', '66, 133, 244')
                )
        self._refresh_schedule()
    
    def _on_event_clicked(self, event: dict):
        """Handle click on existing schedule event - open edit dialog"""
        dialog = ScheduleEventDialog(
            day_index=event.get('day_of_week', 0),
            hour=int(event.get('start_time', '09:00').split(':')[0]),
            event=event,
            parent=self
        )
        dialog.event_saved.connect(self._on_event_saved)
        dialog.event_deleted.connect(self._on_event_deleted)
        dialog.exec()
    
    def _on_event_deleted(self, event_id: int):
        """Handle event deletion"""
        db.delete_schedule_event(event_id)
        self._refresh_schedule()
    
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
        self.weekly._go_today()
    
    def refresh(self):
        """Refresh view"""
        self._sync_deadlines()
        self._refresh_schedule()
