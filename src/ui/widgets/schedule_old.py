"""
Weekly Schedule Widget
"""
from datetime import datetime, timedelta
from typing import List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.utils.styles import COLORS, FONT_FAMILY, get_button_style, get_scroll_area_style, get_nav_button_style
from src.utils.constants import DAYS_ES_SHORT, SCHEDULE_START_HOUR, SCHEDULE_END_HOUR
from src.core.database import db


class TimeSlot(QWidget):
    """Single time slot in schedule"""
    
    clicked = pyqtSignal(int, int)  # day_index, hour
    
    def __init__(self, day_index: int, hour: int, parent=None):
        super().__init__(parent)
        self.day_index = day_index
        self.hour = hour
        self.events: List[Dict] = []
        
        self.setup_ui()
    
    def setup_ui(self):
        self.setMinimumHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        self.events_container = QWidget()
        self.events_layout = QVBoxLayout(self.events_container)
        self.events_layout.setContentsMargins(0, 0, 0, 0)
        self.events_layout.setSpacing(1)
        
        layout.addWidget(self.events_container)
        
        self._update_style()
    
    def _update_style(self):
        if self.events:
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: rgba({COLORS['primary']}, 0.1);
                    border-radius: 4px;
                }}
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                }
                QWidget:hover {
                    background-color: rgba(255, 255, 255, 0.03);
                }
            """)
    
    def set_events(self, events: List[Dict]):
        """Set events for this time slot"""
        # Clear existing
        while self.events_layout.count():
            item = self.events_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.events = events
        
        for event in events:
            color = event.get('color', COLORS['primary'])
            lbl = QLabel(event.get('title', ''))
            lbl.setFont(QFont(FONT_FAMILY, 8))
            lbl.setStyleSheet(f"""
                QLabel {{
                    background-color: rgba({color}, 0.3);
                    color: rgb({color});
                    border-left: 2px solid rgb({color});
                    border-radius: 3px;
                    padding: 2px 4px;
                }}
            """)
            lbl.setWordWrap(True)
            self.events_layout.addWidget(lbl)
        
        self._update_style()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.day_index, self.hour)


class WeeklySchedule(QWidget):
    """Teams-style weekly schedule view"""
    
    slot_clicked = pyqtSignal(int, int)  # day_index, hour
    
    def __init__(self, compact: bool = False, parent=None):
        super().__init__(parent)
        self.compact = compact
        self.current_date = datetime.now()
        self.week_start = self._get_week_start()
        self.slots: Dict[tuple, TimeSlot] = {}
        
        self.setup_ui()
        self._load_events()  # Load events on init
    
    def _get_week_start(self) -> datetime:
        """Get Monday of current week"""
        today = self.current_date.date()
        return datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        margin = 8 if self.compact else 16
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(8)
        
        # Navigation
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("<")
        self.prev_btn.setFixedSize(28, 28)
        self.prev_btn.setStyleSheet(get_nav_button_style())
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.clicked.connect(self._prev_week)
        nav_layout.addWidget(self.prev_btn)
        
        self.week_label = QLabel()
        self.week_label.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
        self.week_label.setStyleSheet(f"color: rgb({COLORS['primary']}); background: transparent;")
        self.week_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.week_label, 1)
        
        self.next_btn = QPushButton(">")
        self.next_btn.setFixedSize(28, 28)
        self.next_btn.setStyleSheet(get_nav_button_style())
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.clicked.connect(self._next_week)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        # Schedule grid in scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(get_scroll_area_style())
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        grid_container = QWidget()
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(1)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(grid_container)
        layout.addWidget(scroll, 1)
        
        self._build_grid()
        self._update_labels()
    
    def _build_grid(self):
        """Build the schedule grid"""
        # Day headers
        self.day_labels = []
        for col in range(7):
            day_widget = QWidget()
            day_layout = QVBoxLayout(day_widget)
            day_layout.setContentsMargins(2, 4, 2, 4)
            day_layout.setSpacing(2)
            
            day_name = QLabel(DAYS_ES_SHORT[col])
            day_name.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Bold))
            day_name.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
            day_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            day_layout.addWidget(day_name)
            
            day_date = QLabel()
            day_date.setFont(QFont(FONT_FAMILY, 8))
            day_date.setStyleSheet(f"color: rgb({COLORS['text_muted']}); background: transparent;")
            day_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
            day_layout.addWidget(day_date)
            
            self.day_labels.append(day_date)
            self.grid_layout.addWidget(day_widget, 0, col + 1)
        
        # Time labels and slots
        start_hour = SCHEDULE_START_HOUR
        end_hour = SCHEDULE_END_HOUR if not self.compact else min(SCHEDULE_END_HOUR, start_hour + 10)
        
        for row, hour in enumerate(range(start_hour, end_hour)):
            # Time label
            time_lbl = QLabel(f"{hour:02d}:00")
            time_lbl.setFont(QFont(FONT_FAMILY, 8))
            time_lbl.setStyleSheet(f"color: rgb({COLORS['text_muted']}); background: transparent;")
            time_lbl.setFixedWidth(40)
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            self.grid_layout.addWidget(time_lbl, row + 1, 0)
            
            # Time slots for each day
            for col in range(7):
                slot = TimeSlot(col, hour)
                slot.clicked.connect(self._on_slot_clicked)
                self.slots[(col, hour)] = slot
                self.grid_layout.addWidget(slot, row + 1, col + 1)
    
    def _update_labels(self):
        """Update day date labels"""
        week_start = self.week_start
        week_end = week_start + timedelta(days=6)
        
        self.week_label.setText(
            f"{week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m/%Y')}"
        )
        
        today = datetime.now().date()
        
        for i, lbl in enumerate(self.day_labels):
            date = (week_start + timedelta(days=i)).date()
            lbl.setText(str(date.day))
            
            if date == today:
                lbl.setStyleSheet(f"color: rgb({COLORS['primary']}); background: transparent; font-weight: bold;")
            else:
                lbl.setStyleSheet(f"color: rgb({COLORS['text_muted']}); background: transparent;")
    
    def _prev_week(self):
        """Go to previous week"""
        self.week_start -= timedelta(weeks=1)
        self._update_labels()
        self._load_events()
    
    def _next_week(self):
        """Go to next week"""
        self.week_start += timedelta(weeks=1)
        self._update_labels()
        self._load_events()
    
    def _on_slot_clicked(self, day_index: int, hour: int):
        """Handle slot click"""
        self.slot_clicked.emit(day_index, hour)
    
    def _load_events(self):
        """Load events from database"""
        # Clear all slots
        for slot in self.slots.values():
            slot.set_events([])
        
        # Get events for this week
        events = db.get_schedule_events()
        
        for event in events:
            day = event.get('day_of_week', 0)
            start_time = event.get('start_time', '00:00')
            
            try:
                hour = int(start_time.split(':')[0])
                if (day, hour) in self.slots:
                    slot = self.slots[(day, hour)]
                    current_events = slot.events.copy()
                    current_events.append(event)
                    slot.set_events(current_events)
            except (ValueError, IndexError):
                continue
    
    def set_events(self, events: List[Dict]):
        """Set events from external source"""
        # Clear all slots
        for slot in self.slots.values():
            slot.set_events([])
        
        for event in events:
            day = event.get('day_of_week', 0)
            start_time = event.get('start_time', '00:00')
            
            try:
                hour = int(start_time.split(':')[0])
                if (day, hour) in self.slots:
                    slot = self.slots[(day, hour)]
                    current_events = slot.events.copy()
                    current_events.append(event)
                    slot.set_events(current_events)
            except (ValueError, IndexError):
                continue
    
    def go_to_today(self):
        """Navigate to current week"""
        self.current_date = datetime.now()
        self.week_start = self._get_week_start()
        self._update_labels()
        self._load_events()
