"""
Weekly Schedule Widget - Teams-style with custom painting
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QMenu, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPen, QMouseEvent

from src.utils.styles import COLORS, FONT_FAMILY, get_nav_button_style
from src.utils.constants import DAYS_ES_SHORT, SCHEDULE_START_HOUR, SCHEDULE_END_HOUR
from src.core.database import db


class ScheduleCanvas(QWidget):
    """Custom painted schedule widget for Teams-like appearance"""
    
    cell_clicked = pyqtSignal(int, int)  # day, hour
    event_clicked = pyqtSignal(dict)  # event data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.week_start = datetime.now()
        self.events: Dict[int, List] = {}  # day_index -> list of events
        self.event_rects: List[tuple] = []  # (QRectF, event_data)
        
        # Make background transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        # Hours to display
        self.hour_start = SCHEDULE_START_HOUR
        self.hour_end = SCHEDULE_END_HOUR
        self.hours = list(range(self.hour_start, self.hour_end + 1))
        
        # Fixed dimensions for scrollable content
        self.hour_label_width = 50
        self.header_height = 40
        self.day_width = 85
        self.hour_height = 45
        
        # Calculate total size
        total_width = self.hour_label_width + (self.day_width * 7)
        total_height = self.header_height + (self.hour_height * len(self.hours))
        self.setMinimumSize(total_width, total_height)
        self.setFixedSize(total_width, total_height)
    
    def set_data(self, week_start: datetime, events: Dict[int, List]):
        """Set schedule data"""
        self.week_start = week_start
        self.events = events
        self.event_rects = []
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Clear event rects
        self.event_rects = []
        
        # Dimensions
        hour_label_width = self.hour_label_width
        header_height = self.header_height
        day_width = self.day_width
        hour_height = self.hour_height
        width = self.width()
        height = self.height()
        
        # Colors
        text_color = QColor(200, 200, 210)
        text_muted = QColor(130, 130, 140)
        line_color = QColor(255, 255, 255, 25)
        today_bg = QColor(66, 133, 244, 25)
        
        today = datetime.now().date()
        
        # Draw day headers
        painter.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Bold))
        for i, day_name in enumerate(DAYS_ES_SHORT):
            current_day = self.week_start + timedelta(days=i)
            is_today = current_day.date() == today
            
            x = hour_label_width + i * day_width
            
            # Highlight today column
            if is_today:
                painter.fillRect(int(x), 0, int(day_width), height, today_bg)
            
            # Day header
            header_text = f"{day_name}\n{current_day.day}"
            
            if is_today:
                painter.setPen(QColor(66, 133, 244))
            else:
                painter.setPen(text_color)
            
            painter.drawText(int(x), 5, int(day_width), header_height - 5,
                           Qt.AlignmentFlag.AlignCenter, header_text)
        
        # Draw hour lines and labels
        painter.setFont(QFont(FONT_FAMILY, 8))
        for i, hour in enumerate(self.hours):
            y = header_height + i * hour_height
            
            # Hour label
            painter.setPen(text_muted)
            painter.drawText(2, int(y), hour_label_width - 8, int(hour_height),
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
                           f"{hour:02d}:00")
            
            # Horizontal line
            painter.setPen(QPen(line_color, 1))
            painter.drawLine(int(hour_label_width), int(y), width, int(y))
        
        # Draw vertical lines between days
        for i in range(8):
            x = hour_label_width + i * day_width
            painter.drawLine(int(x), header_height, int(x), height)
        
        # Draw events
        for day_idx, day_events in self.events.items():
            grouped = self._group_overlapping_events(day_events)
            
            for group in grouped:
                num_cols = len(group)
                for col_idx, evt in enumerate(group):
                    self._draw_event(painter, day_idx, evt, 
                                   hour_label_width, header_height, 
                                   day_width, hour_height,
                                   col_idx, num_cols)
    
    def _group_overlapping_events(self, events: List) -> List[List]:
        """Group events that overlap in time"""
        if not events:
            return []
        
        def time_to_mins(t):
            h, m = map(int, t.split(':'))
            return h * 60 + m
        
        sorted_events = sorted(events, key=lambda e: time_to_mins(e.get('start_time', '00:00')))
        
        groups = []
        current_group = [sorted_events[0]]
        group_end = time_to_mins(sorted_events[0].get('end_time', '00:00'))
        
        for evt in sorted_events[1:]:
            evt_start = time_to_mins(evt.get('start_time', '00:00'))
            evt_end = time_to_mins(evt.get('end_time', '00:00'))
            
            if evt_start < group_end:
                current_group.append(evt)
                group_end = max(group_end, evt_end)
            else:
                groups.append(current_group)
                current_group = [evt]
                group_end = evt_end
        
        groups.append(current_group)
        return groups
    
    def _draw_event(self, painter: QPainter, day_idx: int, event: Dict,
                   hour_label_width: int, header_height: int,
                   day_width: int, hour_height: int,
                   col_idx: int = 0, num_cols: int = 1):
        """Draw a single event"""
        start_time = event.get('start_time', '09:00')
        end_time = event.get('end_time', '10:00')
        title = event.get('title', '')
        color_str = event.get('color', COLORS['primary'])
        
        start_h, start_m = map(int, start_time.split(':'))
        end_h, end_m = map(int, end_time.split(':'))
        
        # Calculate position
        start_offset = (start_h - self.hour_start) + start_m / 60
        end_offset = (end_h - self.hour_start) + end_m / 60
        
        if start_offset < 0:
            start_offset = 0
        if end_offset > len(self.hours):
            end_offset = len(self.hours)
        
        # Calculate dimensions with column support
        col_width = day_width / num_cols
        x = hour_label_width + day_idx * day_width + col_idx * col_width + 2
        y = header_height + start_offset * hour_height + 1
        w = col_width - 4
        h = (end_offset - start_offset) * hour_height - 2
        
        if h < 12:
            h = 12
        
        # Store rect for click detection
        rect = QRectF(x, y, w, h)
        self.event_rects.append((rect, event))
        
        # Parse color
        if isinstance(color_str, str) and ',' in color_str:
            parts = [int(p.strip()) for p in color_str.split(',')]
            color = QColor(*parts)
        else:
            color = QColor(66, 133, 244)
        
        # Draw event background
        bg_color = QColor(color)
        bg_color.setAlpha(160)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(int(x), int(y), int(w), int(h), 4, 4)
        
        # Draw left border accent
        accent_color = QColor(color)
        accent_color.setAlpha(255)
        painter.setBrush(QBrush(accent_color))
        painter.drawRoundedRect(int(x), int(y), 3, int(h), 2, 2)
        
        # Draw text
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont(FONT_FAMILY, 7))
        
        text_x = int(x) + 6
        text_y = int(y) + 2
        text_w = int(w) - 10
        text_h = int(h) - 4
        
        if h > 30:
            display = f"{title}\n{start_time}-{end_time}"
        else:
            display = title
        
        painter.drawText(text_x, text_y, text_w, text_h,
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop |
                        Qt.TextFlag.TextWordWrap, display)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle clicks"""
        pos = event.position()
        
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicked on an event
            for rect, evt_data in self.event_rects:
                if rect.contains(pos):
                    self.event_clicked.emit(evt_data)
                    return
            
            # Check if click is in schedule area
            if pos.x() > self.hour_label_width and pos.y() > self.header_height:
                day = int((pos.x() - self.hour_label_width) / self.day_width)
                hour_offset = (pos.y() - self.header_height) / self.hour_height
                hour = self.hour_start + int(hour_offset)
                
                if 0 <= day < 7 and self.hour_start <= hour <= self.hour_end:
                    self.cell_clicked.emit(day, hour)


class WeeklySchedule(QWidget):
    """Teams-style weekly schedule view"""
    
    slot_clicked = pyqtSignal(int, int)  # day_index, hour
    event_clicked = pyqtSignal(dict)  # event data
    add_event_requested = pyqtSignal()  # request to add new event with date picker
    
    def __init__(self, compact: bool = False, parent=None):
        super().__init__(parent)
        self.compact = compact
        self.current_date = datetime.now()
        self.week_start = self._get_week_start()
        self.external_events = []  # List of external events (Teams/ICS)
        
        self.setup_ui()
        self._load_events()
    
    def set_external_events(self, events: List[Dict]):
        """Set external events (e.g. from Teams)"""
        self.external_events = events
        self._load_events()
    
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
        
        today_btn = QPushButton("Hoy")
        today_btn.setFixedSize(45, 28)
        today_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.08);
                color: rgb({COLORS['text_secondary']});
                border: 1px solid rgba({COLORS['text_secondary']}, 0.3);
                border-radius: 6px;
                padding: 0px;
                font-family: "{FONT_FAMILY}";
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: rgba({COLORS['text_secondary']}, 0.15);
                border: 1px solid rgba({COLORS['text_secondary']}, 0.5);
            }}
            QPushButton:pressed {{
                background-color: rgba({COLORS['text_secondary']}, 0.25);
            }}
        """)
        today_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        today_btn.clicked.connect(self._go_today)
        nav_layout.addWidget(today_btn)
        
        # Add event button
        add_btn = QPushButton("+")
        add_btn.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        add_btn.setFixedSize(28, 28)
        add_btn.setStyleSheet(get_nav_button_style())
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_event)
        nav_layout.addWidget(add_btn)
        
        nav_layout.addStretch()
        
        self.week_label = QLabel()
        self.week_label.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
        self.week_label.setStyleSheet(f"color: rgb({COLORS['primary']}); background: transparent;")
        self.week_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.week_label)
        
        nav_layout.addStretch()
        
        self.next_btn = QPushButton(">")
        self.next_btn.setFixedSize(28, 28)
        self.next_btn.setStyleSheet(get_nav_button_style())
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.clicked.connect(self._next_week)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        # Scroll area for schedule
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.25);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 6px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 3px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(255, 255, 255, 0.25);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: transparent;
            }
        """)
        scroll.viewport().setStyleSheet("background: transparent;")
        
        # Container to center the canvas
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addStretch()
        
        # Schedule canvas
        self.canvas = ScheduleCanvas()
        self.canvas.cell_clicked.connect(self._on_cell_clicked)
        self.canvas.event_clicked.connect(self.event_clicked.emit)
        container_layout.addWidget(self.canvas)
        
        container_layout.addStretch()
        scroll.setWidget(container)
        
        layout.addWidget(scroll, 1)
        
        self._update_labels()
    
    def _update_labels(self):
        """Update week label"""
        week_end = self.week_start + timedelta(days=6)
        self.week_label.setText(
            f"{self.week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m/%Y')}"
        )
    
    def _load_events(self):
        """Load schedule events from database and external sources"""
        # 1. Load DB events (recurring weekly)
        events = db.get_schedule_events()
        
        # Group by day
        by_day: Dict[int, List] = {i: [] for i in range(7)}
        for evt in events:
            day = evt.get('day_of_week', 0)
            if 0 <= day < 7:
                evt['is_internal'] = True
                by_day[day].append(evt)
        
        # 2. Process external events (specific dates)
        week_end = self.week_start + timedelta(days=7)
        
        for ext_evt in self.external_events:
            if not ext_evt.get('start'):
                continue
                
            try:
                start_dt = datetime.fromisoformat(ext_evt['start'].replace('Z', ''))
                
                # Check if event falls in current week
                if self.week_start <= start_dt < week_end:
                    day_idx = (start_dt.weekday()) 
                    
                    # Calculate end time
                    if ext_evt.get('end'):
                        end_dt = datetime.fromisoformat(ext_evt['end'].replace('Z', ''))
                    else:
                        end_dt = start_dt + timedelta(hours=1)
                    
                    # Format for canvas
                    canvas_evt = {
                        'id': ext_evt.get('uid', 0),
                        'title': ext_evt.get('title', 'Evento'),
                        'day_of_week': day_idx,
                        'start_time': start_dt.strftime('%H:%M'),
                        'end_time': end_dt.strftime('%H:%M'),
                        'color': '142, 68, 173' if ext_evt.get('is_meeting') else '39, 174, 96', # Purple/Green
                        'location': ext_evt.get('location', ''),
                        'is_external': True,
                        'source': ext_evt.get('source', 'external')
                    }
                    by_day[day_idx].append(canvas_evt)
            except Exception as e:
                print(f"Error processing external event: {e}")
        
        self.canvas.set_data(self.week_start, by_day)
    
    def _on_cell_clicked(self, day: int, hour: int):
        """Handle cell click - emit signal for dialog"""
        self.slot_clicked.emit(day, hour)
    
    def _prev_week(self):
        """Go to previous week"""
        self.week_start -= timedelta(days=7)
        self._update_labels()
        self._load_events()
    
    def _next_week(self):
        """Go to next week"""
        self.week_start += timedelta(days=7)
        self._update_labels()
        self._load_events()
    
    def _go_today(self):
        """Go to current week"""
        self.current_date = datetime.now()
        self.week_start = self._get_week_start()
        self._update_labels()
        self._load_events()
    
    def _add_event(self):
        """Request to add a new event with date picker"""
        self.add_event_requested.emit()
    
    def refresh(self):
        """Refresh schedule"""
        self._load_events()
