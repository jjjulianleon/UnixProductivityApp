"""
Monthly Calendar Widget
"""
from datetime import datetime, timedelta
import calendar
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor

from src.utils.styles import COLORS, FONT_FAMILY, get_button_style, get_nav_button_style
from src.utils.constants import DAYS_ES_SHORT, MONTHS_ES


class DayCell(QWidget):
    """Single day cell in calendar"""
    
    clicked = pyqtSignal(int, int, int)  # year, month, day
    
    def __init__(self, day: int, month: int, year: int, 
                 is_current_month: bool = True, 
                 is_today: bool = False,
                 has_deadline: bool = False,
                 parent=None):
        super().__init__(parent)
        self.day = day
        self.month = month
        self.year = year
        self.is_current_month = is_current_month
        self.is_today = is_today
        self.has_deadline = has_deadline
        
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background for today
        if self.is_today:
            painter.setBrush(QColor(66, 133, 244, 80))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(2, 2, 28, 28, 6, 6)
        
        # Day number
        if self.is_current_month:
            color = QColor(230, 230, 240) if not self.is_today else QColor(66, 133, 244)
        else:
            color = QColor(100, 100, 110)
        
        painter.setPen(color)
        painter.setFont(QFont(FONT_FAMILY, 10))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, str(self.day))
        
        # Deadline indicator (red dot)
        if self.has_deadline:
            painter.setBrush(QColor(234, 67, 53))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(22, 4, 6, 6)
        
        painter.end()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.year, self.month, self.day)


class MonthlyCalendar(QWidget):
    """Monthly calendar view"""
    
    date_clicked = pyqtSignal(str)  # YYYY-MM-DD format
    deadline_clicked = pyqtSignal(list)  # list of tasks
    
    def __init__(self, compact: bool = False, parent=None):
        super().__init__(parent)
        self.compact = compact
        self.current_date = datetime.now()
        self.display_date = datetime.now()
        self.deadlines: Dict[str, List[Dict]] = {}  # date -> [tasks]
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        margin = 8 if self.compact else 16
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(8)
        
        # Navigation header
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("<")
        self.prev_btn.setFixedSize(28, 28)
        self.prev_btn.setStyleSheet(get_nav_button_style())
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.clicked.connect(self._prev_month)
        nav_layout.addWidget(self.prev_btn)
        
        self.month_label = QLabel()
        self.month_label.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
        self.month_label.setStyleSheet(f"color: rgb({COLORS['primary']}); background: transparent;")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.month_label, 1)
        
        self.next_btn = QPushButton(">")
        self.next_btn.setFixedSize(28, 28)
        self.next_btn.setStyleSheet(get_nav_button_style())
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.clicked.connect(self._next_month)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        # Day headers
        headers_layout = QHBoxLayout()
        headers_layout.setSpacing(0)
        for day in DAYS_ES_SHORT:
            lbl = QLabel(day)
            lbl.setFont(QFont(FONT_FAMILY, 8))
            lbl.setStyleSheet(f"color: rgb({COLORS['text_muted']}); background: transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedWidth(32)
            headers_layout.addWidget(lbl)
        layout.addLayout(headers_layout)
        
        # Calendar grid
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(2)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.grid_widget)
        
        self._update_calendar()
    
    def _update_calendar(self):
        """Update the calendar grid"""
        # Clear existing cells
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Update month label
        month_name = MONTHS_ES[self.display_date.month - 1]
        self.month_label.setText(f"{month_name} {self.display_date.year}")
        
        # Get calendar data
        cal = calendar.Calendar(firstweekday=0)  # Monday first
        month_days = cal.monthdayscalendar(self.display_date.year, self.display_date.month)
        
        today = self.current_date.date()
        
        for row, week in enumerate(month_days):
            for col, day in enumerate(week):
                if day == 0:
                    # Day from adjacent month
                    if row == 0:
                        # Previous month
                        prev_month = self.display_date.replace(day=1) - timedelta(days=1)
                        adj_day = prev_month.day - (6 - col)
                        cell = DayCell(adj_day, prev_month.month, prev_month.year, 
                                      is_current_month=False)
                    else:
                        # Next month
                        next_day = col + 1
                        next_month = self.display_date.month + 1
                        next_year = self.display_date.year
                        if next_month > 12:
                            next_month = 1
                            next_year += 1
                        cell = DayCell(next_day, next_month, next_year,
                                      is_current_month=False)
                else:
                    # Current month day
                    date_key = f"{self.display_date.year}-{self.display_date.month:02d}-{day:02d}"
                    has_deadline = date_key in self.deadlines and len(self.deadlines[date_key]) > 0
                    is_today = (day == today.day and 
                               self.display_date.month == today.month and 
                               self.display_date.year == today.year)
                    
                    cell = DayCell(day, self.display_date.month, self.display_date.year,
                                  is_current_month=True, is_today=is_today, 
                                  has_deadline=has_deadline)
                
                cell.clicked.connect(self._on_day_clicked)
                self.grid_layout.addWidget(cell, row, col)
    
    def _prev_month(self):
        """Go to previous month"""
        if self.display_date.month == 1:
            self.display_date = self.display_date.replace(year=self.display_date.year - 1, month=12)
        else:
            self.display_date = self.display_date.replace(month=self.display_date.month - 1)
        self._update_calendar()
    
    def _next_month(self):
        """Go to next month"""
        if self.display_date.month == 12:
            self.display_date = self.display_date.replace(year=self.display_date.year + 1, month=1)
        else:
            self.display_date = self.display_date.replace(month=self.display_date.month + 1)
        self._update_calendar()
    
    def _on_day_clicked(self, year: int, month: int, day: int):
        """Handle day click"""
        date_str = f"{year}-{month:02d}-{day:02d}"
        self.date_clicked.emit(date_str)
        
        # Check if there are deadlines for this date
        if date_str in self.deadlines and self.deadlines[date_str]:
            self.deadline_clicked.emit(self.deadlines[date_str])
    
    def set_deadlines(self, tasks: List[Dict]):
        """Set deadlines from task list"""
        self.deadlines.clear()
        for task in tasks:
            deadline = task.get('deadline')
            if deadline and task.get('status') != 'completado':
                if deadline not in self.deadlines:
                    self.deadlines[deadline] = []
                self.deadlines[deadline].append(task)
        self._update_calendar()
    
    def go_to_today(self):
        """Navigate to current month"""
        self.display_date = datetime.now()
        self._update_calendar()
