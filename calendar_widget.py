#!/usr/bin/env python3
"""
Glassmorphism Calendar Widget for KDE Plasma
Author: GitHub Copilot
Features:
- Monthly calendar with today highlighted
- Weekly schedule view (Teams-style)
- Obsidian integration for tasks
- Microsoft Graph API ready for Teams meetings
- Brightspace D2L ready for university deadlines
"""

import sys
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QScrollArea, QFrame, QTabWidget, QPushButton,
    QSizePolicy, QGraphicsDropShadowEffect, QDialog, QLineEdit,
    QComboBox, QTimeEdit, QColorDialog, QSpinBox, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QTime, pyqtSignal, QMimeData, QRect
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QLinearGradient, QMouseEvent, QAction, QDrag


# ============== CONFIGURATION ==============
class Config:
    # Window settings
    WINDOW_WIDTH = 520
    WINDOW_HEIGHT = 420  # Increased for tabs
    BACKGROUND_OPACITY = 0.85
    BORDER_RADIUS = 20
    
    # Colors (Dark theme with blue accents)
    BG_COLOR = QColor(30, 30, 35, int(255 * BACKGROUND_OPACITY))
    ACCENT_COLOR = QColor(66, 133, 244)  # Google Blue
    TODAY_COLOR = QColor(66, 133, 244, 200)
    TEXT_COLOR = QColor(255, 255, 255)
    TEXT_SECONDARY = QColor(180, 180, 190)
    BORDER_COLOR = QColor(255, 255, 255, 30)
    CARD_BG = QColor(255, 255, 255, 15)
    
    # Obsidian paths
    OBSIDIAN_VAULT = "/home/jjulianleon/Documents/Obsidian/"
    PENDIENTES_FILES = [
        "/home/jjulianleon/Documents/Obsidian/Personal/Pendientes Personal.md",
        "/home/jjulianleon/Documents/Obsidian/Pendientes Fedora.md",
        "/home/jjulianleon/Documents/Obsidian/Universidad/8vo Semestre/Pendientes Universidad.md"
    ]
    
    # Schedule (Lunes=0, Domingo=6)
    SCHEDULE = {
        0: [  # Lunes
            ("13:00", "14:20", "Data Mining", "#4285F4"),
            ("14:30", "15:50", "Redes Lab", "#34A853"),
        ],
        1: [  # Martes
            ("10:00", "11:20", "Bases de Datos", "#FBBC05"),
            ("13:00", "14:20", "Redes", "#34A853"),
            ("14:30", "15:50", "Mercados Int.", "#EA4335"),
            ("16:00", "18:00", "PASEC", "#9C27B0"),
        ],
        2: [  # Miércoles
            ("13:00", "14:20", "Data Mining", "#4285F4"),
            ("14:30", "15:50", "PASEC Teoría", "#9C27B0"),
        ],
        3: [  # Jueves
            ("10:00", "11:20", "Bases de Datos", "#FBBC05"),
            ("13:00", "14:20", "Redes", "#34A853"),
            ("14:30", "15:50", "Mercados Int.", "#EA4335"),
        ],
        4: [  # Viernes
            ("08:30", "13:30", "PASANTÍAS", "#FF5722"),
            ("14:00", "18:00", "PASEC", "#9C27B0"),
        ],
        5: [],  # Sábado
        6: [],  # Domingo
    }
    
    HOUR_START = 7
    HOUR_END = 19
    
    # Time blocks of 1:30 hours (in minutes from start of day)
    TIME_BLOCKS = [
        ("07:00", "08:30"),
        ("08:30", "10:00"),
        ("10:00", "11:30"),
        ("11:30", "13:00"),
        ("13:00", "14:30"),
        ("14:30", "16:00"),
        ("16:00", "17:30"),
        ("17:30", "19:00"),
    ]


# ============== GLASSMORPHISM WIDGET BASE ==============
class GlassWidget(QWidget):
    """Base widget with glassmorphism effect"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._drag_pos = None
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw rounded rectangle background
        painter.setBrush(QBrush(Config.BG_COLOR))
        painter.setPen(QPen(Config.BORDER_COLOR, 1))
        painter.drawRoundedRect(
            self.rect().adjusted(1, 1, -1, -1),
            Config.BORDER_RADIUS,
            Config.BORDER_RADIUS
        )
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            
    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            
    def mouseReleaseEvent(self, event):
        self._drag_pos = None


# ============== DAY CELL FOR CALENDAR ==============
class DayCell(QWidget):
    """A clickable day cell with optional deadline indicator"""
    
    clicked = pyqtSignal(list)  # Emits list of tasks for this day
    
    def __init__(self, day, has_deadline, tasks, parent=None):
        super().__init__(parent)
        self.day = day
        self.has_deadline = has_deadline
        self.tasks = tasks
        self.is_today = False
        self.setFixedSize(32, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor if has_deadline else Qt.CursorShape.ArrowCursor)
        
    def set_today(self, is_today):
        self.is_today = is_today
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background circle for today
        if self.is_today:
            painter.setBrush(QColor(66, 133, 244, 77))  # 0.3 opacity
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, 32, 32)
            painter.setPen(QColor(255, 255, 255))
            font = QFont("Source Code Pro", 10, QFont.Weight.Bold)
        else:
            painter.setPen(QColor(Config.TEXT_COLOR))
            font = QFont("Source Code Pro", 10)
        
        painter.setFont(font)
        painter.drawText(QRect(0, 0, 32, 32), Qt.AlignmentFlag.AlignCenter, str(self.day))
        
        # Draw red dot if has deadline
        if self.has_deadline:
            painter.setBrush(QColor(255, 77, 79))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(13, 30, 6, 6)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.tasks:
            self.clicked.emit(self.tasks)


# ============== MONTHLY CALENDAR ==============
class MonthlyCalendar(QWidget):
    """Monthly calendar view with today highlighted and deadline indicators"""
    
    deadline_clicked = pyqtSignal(list)  # Emits list of tasks for that date
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_date = datetime.now()
        self.deadlines = {}  # {date_str: [tasks]}
        self.setup_ui()
        
    def set_deadlines(self, tasks):
        """Set deadlines from task list"""
        self.deadlines = {}
        for task in tasks:
            if task.get('deadline') and task.get('status') != 'done':
                date_str = task['deadline']
                if date_str not in self.deadlines:
                    self.deadlines[date_str] = []
                self.deadlines[date_str].append(task)
        self.update_calendar()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 15)
        layout.setSpacing(3)
        
        # Month navigation
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(30, 30)
        self.prev_btn.clicked.connect(self.prev_month)
        self.style_nav_button(self.prev_btn)
        
        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_label.setFont(QFont("Source Code Pro", 14, QFont.Weight.Bold))
        self.month_label.setStyleSheet(f"color: {Config.TEXT_COLOR.name()};")
        
        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(30, 30)
        self.next_btn.clicked.connect(self.next_month)
        self.style_nav_button(self.next_btn)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.month_label)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        layout.addSpacing(8)  # Space between month title and day headers
        
        # Add stretch before calendar to center it vertically
        layout.addStretch()
        
        # Calendar grid
        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(2)
        self.calendar_grid.setVerticalSpacing(1)
        layout.addLayout(self.calendar_grid)
        
        # Add stretch at the bottom for spacing before date
        layout.addStretch()
        
        self.update_calendar()
        
    def style_nav_button(self, btn):
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {Config.TEXT_COLOR.name()};
                border: none;
                border-radius: 15px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
        """)
        
    def update_calendar(self):
        # Clear grid
        while self.calendar_grid.count():
            item = self.calendar_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Month name
        months_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.month_label.setText(f"{months_es[self.current_date.month - 1]} {self.current_date.year}")
        
        # Day headers
        days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for i, day in enumerate(days):
            label = QLabel(day)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(QFont("Source Code Pro", 9, QFont.Weight.Bold))
            label.setStyleSheet(f"color: {Config.TEXT_SECONDARY.name()}; margin-bottom: 6px;")
            self.calendar_grid.addWidget(label, 0, i)
            
        # Calculate first day of month
        first_day = self.current_date.replace(day=1)
        start_weekday = first_day.weekday()
        
        # Get days in month
        if self.current_date.month == 12:
            next_month = self.current_date.replace(year=self.current_date.year + 1, month=1, day=1)
        else:
            next_month = self.current_date.replace(month=self.current_date.month + 1, day=1)
        days_in_month = (next_month - first_day).days
        
        # Fill calendar
        today = datetime.now()
        row = 1
        col = start_weekday
        
        for day in range(1, days_in_month + 1):
            # Check if this date has deadlines
            date_str = f"{self.current_date.year}-{self.current_date.month:02d}-{day:02d}"
            has_deadline = date_str in self.deadlines
            
            # Create day cell widget
            cell = DayCell(day, has_deadline, self.deadlines.get(date_str, []), self)
            cell.clicked.connect(self._on_day_clicked)
            
            is_today = (day == today.day and 
                       self.current_date.month == today.month and 
                       self.current_date.year == today.year)
            
            cell.set_today(is_today)
            self.calendar_grid.addWidget(cell, row, col)
            
            col += 1
            if col > 6:
                col = 0
                row += 1
                
    def _on_day_clicked(self, tasks):
        """Handle day cell click"""
        if tasks:
            self.deadline_clicked.emit(tasks)
                
    def prev_month(self):
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self.update_calendar()
        
    def next_month(self):
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self.update_calendar()


# ============== ADD EVENT DIALOG ==============
class AddEventDialog(QDialog):
    """Dialog to add or edit an event"""
    
    def __init__(self, parent=None, day=0, hour=8, edit_data=None):
        super().__init__(parent)
        self.edit_mode = edit_data is not None
        self.setWindowTitle("Editar Evento" if self.edit_mode else "Nuevo Evento")
        self.setFixedSize(300, 280)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: rgb(35, 35, 40);
                border-radius: 10px;
            }}
            QLabel {{
                color: white;
                font-family: "Source Code Pro";
            }}
            QLineEdit, QComboBox, QTimeEdit {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
                padding: 5px;
                color: white;
                font-family: "Source Code Pro";
            }}
            QPushButton {{
                background-color: rgba(66, 133, 244, 0.8);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-family: "Source Code Pro";
            }}
            QPushButton:hover {{
                background-color: rgba(66, 133, 244, 1);
            }}
            QPushButton#cancelBtn {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QPushButton#cancelBtn:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
        """)
        
        self.selected_color = edit_data['color'] if edit_data else "#4285F4"
        self.setup_ui(day, hour, edit_data)
        
    def setup_ui(self, day, hour, edit_data=None):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        layout.addWidget(QLabel("Nombre:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del evento")
        if edit_data:
            self.name_input.setText(edit_data['name'])
        layout.addWidget(self.name_input)
        
        # Day selector
        layout.addWidget(QLabel("Dia:"))
        self.day_combo = QComboBox()
        days = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
        self.day_combo.addItems(days)
        self.day_combo.setCurrentIndex(edit_data['day'] if edit_data else day)
        layout.addWidget(self.day_combo)
        
        # Time row
        time_layout = QHBoxLayout()
        
        time_layout.addWidget(QLabel("Inicio:"))
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm")
        if edit_data:
            h, m = map(int, edit_data['start'].split(':'))
            self.start_time.setTime(QTime(h, m))
        else:
            self.start_time.setTime(QTime(hour, 0))
        time_layout.addWidget(self.start_time)
        
        time_layout.addWidget(QLabel("Fin:"))
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("HH:mm")
        if edit_data:
            h, m = map(int, edit_data['end'].split(':'))
            self.end_time.setTime(QTime(h, m))
        else:
            self.end_time.setTime(QTime(hour + 1, 30))
        time_layout.addWidget(self.end_time)
        
        layout.addLayout(time_layout)
        
        # Color picker
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(40, 25)
        self.color_btn.setStyleSheet(f"background-color: {self.selected_color}; border-radius: 4px;")
        self.color_btn.clicked.connect(self.pick_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
    def pick_color(self):
        color = QColorDialog.getColor(QColor(self.selected_color), self)
        if color.isValid():
            self.selected_color = color.name()
            self.color_btn.setStyleSheet(f"background-color: {self.selected_color}; border-radius: 4px;")
            
    def get_event_data(self):
        return {
            'day': self.day_combo.currentIndex(),
            'start': self.start_time.time().toString("HH:mm"),
            'end': self.end_time.time().toString("HH:mm"),
            'name': self.name_input.text() or "Evento",
            'color': self.selected_color
        }


# ============== WEEKLY SCHEDULE VIEW ==============
class WeeklySchedule(QWidget):
    """Weekly schedule view like Microsoft Teams"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_week_start = self.get_week_start(datetime.now())
        self.custom_events = []  # User-added events
        self.setup_ui()
        
    def get_week_start(self, date):
        """Get Monday of the week"""
        return date - timedelta(days=date.weekday())
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Week navigation
        nav_layout = QHBoxLayout()
        
        prev_btn = QPushButton("<")
        prev_btn.setFixedSize(28, 28)
        prev_btn.clicked.connect(self.prev_week)
        self.style_nav_button(prev_btn)
        
        self.week_label = QLabel()
        self.week_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.week_label.setFont(QFont("Source Code Pro", 10, QFont.Weight.Bold))
        self.week_label.setStyleSheet(f"color: {Config.TEXT_COLOR.name()};")
        
        next_btn = QPushButton(">")
        next_btn.setFixedSize(28, 28)
        next_btn.clicked.connect(self.next_week)
        self.style_nav_button(next_btn)
        
        today_btn = QPushButton("Hoy")
        today_btn.setFixedSize(40, 28)
        today_btn.clicked.connect(self.go_today)
        self.style_nav_button(today_btn)
        
        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.clicked.connect(lambda: self.show_add_dialog(0, 8))
        self.style_nav_button(add_btn)
        
        nav_layout.addWidget(prev_btn)
        nav_layout.addWidget(today_btn)
        nav_layout.addWidget(add_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.week_label)
        nav_layout.addStretch()
        nav_layout.addWidget(next_btn)
        
        layout.addLayout(nav_layout)
        
        # Scroll area for schedule
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollArea > QWidget {
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
        
        # Make viewport transparent
        scroll.viewport().setStyleSheet("background: transparent;")
        
        # Schedule canvas (custom painted widget)
        self.schedule_canvas = ScheduleCanvas(self)
        self.schedule_canvas.cell_clicked.connect(self.on_cell_clicked)
        self.schedule_canvas.event_edit_requested.connect(self.on_edit_event)
        self.schedule_canvas.event_delete_requested.connect(self.on_delete_event)
        scroll.setWidget(self.schedule_canvas)
        
        layout.addWidget(scroll)
        
        self.update_schedule()
        
    def style_nav_button(self, btn):
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {Config.TEXT_COLOR.name()};
                border: none;
                border-radius: 14px;
                font-size: 11px;
                font-family: "Source Code Pro";
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
        """)
        
    def update_schedule(self):
        week_end = self.current_week_start + timedelta(days=6)
        months_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                     "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        self.week_label.setText(
            f"{self.current_week_start.day} {months_es[self.current_week_start.month-1]} - "
            f"{week_end.day} {months_es[week_end.month-1]} {week_end.year}"
        )
        
        # Combine fixed schedule with custom events
        all_events = {}
        for day, events in Config.SCHEDULE.items():
            all_events[day] = []
            for ev in events:
                # Fixed events: (start, end, title, color, is_custom=False, event_data=None)
                all_events[day].append((ev[0], ev[1], ev[2], ev[3], False, None))
        
        for idx, event in enumerate(self.custom_events):
            day = event['day']
            if day not in all_events:
                all_events[day] = []
            # Custom events: (start, end, title, color, is_custom=True, event_data with index)
            event_with_idx = dict(event)
            event_with_idx['index'] = idx
            all_events[day].append((event['start'], event['end'], event['name'], event['color'], True, event_with_idx))
        
        self.schedule_canvas.set_data(self.current_week_start, all_events)
        
    def on_cell_clicked(self, day, hour):
        self.show_add_dialog(day, hour)
        
    def show_add_dialog(self, day, hour):
        dialog = AddEventDialog(self, day, hour)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            event_data = dialog.get_event_data()
            self.custom_events.append(event_data)
            self.update_schedule()
    
    def on_edit_event(self, event_data):
        """Edit an existing custom event"""
        idx = event_data.get('index')
        if idx is not None and 0 <= idx < len(self.custom_events):
            dialog = AddEventDialog(self, event_data['day'], 
                                   int(event_data['start'].split(':')[0]),
                                   edit_data=event_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_data = dialog.get_event_data()
                self.custom_events[idx] = new_data
                self.update_schedule()
    
    def on_delete_event(self, event_data):
        """Delete a custom event with confirmation"""
        idx = event_data.get('index')
        if idx is not None and 0 <= idx < len(self.custom_events):
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setWindowTitle("Confirmar")
            msg.setText(f"Eliminar '{event_data['name']}'?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: rgba(30, 30, 35, 240);
                }
                QMessageBox QLabel {
                    color: rgb(200, 200, 210);
                    font-family: 'Source Code Pro';
                }
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.1);
                    color: rgb(200, 200, 210);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 4px;
                    padding: 6px 16px;
                    font-family: 'Source Code Pro';
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.2);
                }
            """)
            if msg.exec() == QMessageBox.StandardButton.Yes:
                del self.custom_events[idx]
                self.update_schedule()
        
    def prev_week(self):
        self.current_week_start -= timedelta(days=7)
        self.update_schedule()
        
    def next_week(self):
        self.current_week_start += timedelta(days=7)
        self.update_schedule()
        
    def go_today(self):
        self.current_week_start = self.get_week_start(datetime.now())
        self.update_schedule()


class ScheduleCanvas(QWidget):
    """Custom painted schedule widget for Teams-like appearance"""
    
    cell_clicked = pyqtSignal(int, int)  # day, hour
    event_edit_requested = pyqtSignal(dict)  # event_data
    event_delete_requested = pyqtSignal(dict)  # event_data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.week_start = datetime.now()
        self.events = {}
        self.event_rects = []  # Store event rectangles for click detection
        
        # Make background transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # Hours to display
        self.hour_start = 7
        self.hour_end = 19
        self.hours = list(range(self.hour_start, self.hour_end + 1))
        
        # Fixed dimensions for scrollable content
        self.hour_label_width = 45
        self.header_height = 35
        self.day_width = 70
        self.hour_height = 40
        
        # Calculate total size
        total_width = self.hour_label_width + (self.day_width * 7)
        total_height = self.header_height + (self.hour_height * len(self.hours))
        self.setMinimumSize(total_width, total_height)
        self.setFixedSize(total_width, total_height)
        
    def set_data(self, week_start, events):
        self.week_start = week_start
        self.events = events
        self.event_rects = []  # Clear event rectangles
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Clear event rects for this paint
        self.event_rects = []
        
        # Use fixed dimensions
        hour_label_width = self.hour_label_width
        header_height = self.header_height
        day_width = self.day_width
        hour_height = self.hour_height
        
        width = self.width()
        height = self.height()
        
        # Colors
        text_color = QColor(200, 200, 210)
        line_color = QColor(255, 255, 255, 20)
        today_bg = QColor(66, 133, 244, 30)
        
        days_es = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
        today = datetime.now().date()
        
        # Draw day headers
        painter.setFont(QFont("Source Code Pro", 9))
        for i, day_name in enumerate(days_es):
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
        painter.setFont(QFont("Source Code Pro", 8))
        for i, hour in enumerate(self.hours):
            y = header_height + i * hour_height
            
            # Hour label
            painter.setPen(text_color)
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
            # Group overlapping events
            grouped_events = self.group_overlapping_events(day_events)
            
            for group in grouped_events:
                num_cols = len(group)
                for col_idx, event_tuple in enumerate(group):
                    start_time, end_time, title, color = event_tuple[:4]
                    is_custom = event_tuple[4] if len(event_tuple) > 4 else False
                    event_data = event_tuple[5] if len(event_tuple) > 5 else None
                    self.draw_event(painter, day_idx, start_time, end_time, title, color,
                                  hour_label_width, header_height, day_width, hour_height,
                                  col_idx, num_cols, is_custom, event_data)
    
    def group_overlapping_events(self, events):
        """Group events that overlap in time"""
        if not events:
            return []
        
        # Sort by start time
        sorted_events = sorted(events, key=lambda e: self.time_to_minutes(e[0]))
        
        groups = []
        current_group = [sorted_events[0]]
        group_end = self.time_to_minutes(sorted_events[0][1])
        
        for event in sorted_events[1:]:
            event_start = self.time_to_minutes(event[0])
            event_end = self.time_to_minutes(event[1])
            
            if event_start < group_end:
                # Overlaps with current group
                current_group.append(event)
                group_end = max(group_end, event_end)
            else:
                # Start new group
                groups.append(current_group)
                current_group = [event]
                group_end = event_end
        
        groups.append(current_group)
        return groups
    
    def time_to_minutes(self, time_str):
        h, m = map(int, time_str.split(":"))
        return h * 60 + m
    
    def draw_event(self, painter, day_idx, start_time, end_time, title, color_hex,
                   hour_label_width, header_height, day_width, hour_height,
                   col_idx=0, num_cols=1, is_custom=False, event_data=None):
        """Draw a single event with translucent color"""
        start_h, start_m = map(int, start_time.split(":"))
        end_h, end_m = map(int, end_time.split(":"))
        
        # Calculate position
        start_offset = (start_h - self.hour_start) + start_m / 60
        end_offset = (end_h - self.hour_start) + end_m / 60
        
        if start_offset < 0:
            start_offset = 0
        if end_offset > len(self.hours):
            end_offset = len(self.hours)
        
        # Calculate x position with column offset for overlapping events
        col_width = day_width / num_cols
        x = hour_label_width + day_idx * day_width + col_idx * col_width + 2
        y = header_height + start_offset * hour_height + 1
        w = col_width - 4
        h = (end_offset - start_offset) * hour_height - 2
        
        if h < 10:
            h = 10
        
        # Store event rectangle for click detection (only custom events)
        if is_custom and event_data:
            from PyQt6.QtCore import QRectF
            rect = QRectF(x, y, w, h)
            self.event_rects.append((rect, event_data))
        
        # Parse color and make translucent
        color = QColor(color_hex)
        color.setAlpha(180)  # Translucent
        
        # Draw event rectangle with rounded corners
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(int(x), int(y), int(w), int(h), 4, 4)
        
        # Draw left border accent (like Teams)
        accent_color = QColor(color_hex)
        accent_color.setAlpha(255)
        painter.setBrush(QBrush(accent_color))
        painter.drawRoundedRect(int(x), int(y), 3, int(h), 2, 2)
        
        # Draw text
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Source Code Pro", 7))
        
        text_rect_x = int(x) + 6
        text_rect_y = int(y) + 2
        text_rect_w = int(w) - 12
        text_rect_h = int(h) - 4
        
        if h > 25:
            display_text = f"{title}\n{start_time}-{end_time}"
        else:
            display_text = title
        
        painter.drawText(text_rect_x, text_rect_y, text_rect_w, text_rect_h,
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | 
                        Qt.TextFlag.TextWordWrap, display_text)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle click to add event or right-click for context menu"""
        pos = event.position()
        
        if event.button() == Qt.MouseButton.RightButton:
            # Check if click is on a custom event
            for rect, event_data in self.event_rects:
                if rect.contains(pos):
                    self.show_context_menu(event.globalPosition().toPoint(), event_data)
                    return
        
        elif event.button() == Qt.MouseButton.LeftButton:
            # Use fixed dimensions
            hour_label_width = self.hour_label_width
            header_height = self.header_height
            day_width = self.day_width
            hour_height = self.hour_height
            
            # Check if click is in the schedule area
            if pos.x() > hour_label_width and pos.y() > header_height:
                day = int((pos.x() - hour_label_width) / day_width)
                hour_offset = (pos.y() - header_height) / hour_height
                hour = self.hour_start + int(hour_offset)
                
                if 0 <= day < 7 and self.hour_start <= hour <= self.hour_end:
                    self.cell_clicked.emit(day, hour)
    
    def show_context_menu(self, pos, event_data):
        """Show context menu for event editing/deletion"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(45, 45, 50, 240);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 6px;
                padding: 5px;
            }
            QMenu::item {
                color: rgb(200, 200, 210);
                padding: 8px 20px;
                font-family: 'Source Code Pro';
                font-size: 10pt;
            }
            QMenu::item:selected {
                background-color: rgba(66, 133, 244, 150);
                border-radius: 4px;
            }
        """)
        
        edit_action = QAction("Editar", self)
        delete_action = QAction("Eliminar", self)
        
        edit_action.triggered.connect(lambda: self.event_edit_requested.emit(event_data))
        delete_action.triggered.connect(lambda: self.event_delete_requested.emit(event_data))
        
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.exec(pos)


# ============== OBSIDIAN TASKS ==============
class AddTaskDialog(QDialog):
    """Dialog to add or edit a task"""
    
    def __init__(self, parent=None, edit_data=None):
        super().__init__(parent)
        self.edit_mode = edit_data is not None
        self.setWindowTitle("Editar Tarea" if self.edit_mode else "Nueva Tarea")
        self.setFixedSize(380, 420)
        self.setStyleSheet("""
            QDialog {
                background-color: rgb(35, 35, 40);
                border-radius: 10px;
            }
            QLabel {
                color: white;
                font-family: "Source Code Pro";
                background: transparent;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
                padding: 10px;
                color: white;
                font-family: "Source Code Pro";
                min-height: 20px;
            }
            QComboBox {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
                padding: 8px;
                color: white;
                font-family: "Source Code Pro";
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid white;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: rgb(45, 45, 50);
                color: white;
                selection-background-color: rgba(66, 133, 244, 0.5);
                selection-color: white;
                border: 1px solid rgba(60, 60, 65, 1);
                border-radius: 4px;
                outline: 0;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                background-color: rgb(45, 45, 50);
                color: white;
                padding: 8px;
                border: none;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: rgba(66, 133, 244, 0.5);
            }
            QDateEdit {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
                padding: 8px;
                color: white;
                font-family: "Source Code Pro";
            }
            QDateEdit::drop-down {
                border: none;
                padding-right: 10px;
            }
            QDateEdit::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid white;
                margin-right: 5px;
            }
            QCalendarWidget {
                background-color: rgb(45, 45, 50);
                color: white;
            }
            QCalendarWidget QToolButton {
                color: white;
                background-color: transparent;
            }
            QCalendarWidget QMenu {
                background-color: rgb(45, 45, 50);
                color: white;
            }
            QCalendarWidget QSpinBox {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
            }
            QCalendarWidget QTableView {
                background-color: rgb(45, 45, 50);
                selection-background-color: rgba(66, 133, 244, 0.5);
            }
            QCheckBox {
                color: white;
                font-family: "Source Code Pro";
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid rgba(200, 200, 210, 0.4);
                border-radius: 4px;
                background: transparent;
            }
            QCheckBox::indicator:checked {
                background-color: rgba(66, 133, 244, 0.8);
                border-color: rgba(66, 133, 244, 0.8);
            }
            QPushButton {
                background-color: rgba(66, 133, 244, 0.8);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-family: "Source Code Pro";
            }
            QPushButton:hover {
                background-color: rgba(66, 133, 244, 1);
            }
            QPushButton#cancelBtn {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton#cancelBtn:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.setup_ui(edit_data)
        
    def setup_ui(self, edit_data):
        from PyQt6.QtWidgets import QDateEdit, QCheckBox, QTextEdit
        from PyQt6.QtCore import QDate
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Task title
        layout.addWidget(QLabel("Título:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Título de la tarea")
        self.title_input.setMinimumHeight(36)
        if edit_data:
            self.title_input.setText(edit_data.get('title', edit_data.get('text', '')))
        layout.addWidget(self.title_input)
        
        # Task description (optional)
        layout.addWidget(QLabel("Descripción (opcional):"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Descripción detallada...")
        self.desc_input.setMinimumHeight(100)
        self.desc_input.setMaximumHeight(120)
        self.desc_input.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
                padding: 8px;
                color: white;
                font-family: "Source Code Pro";
                font-size: 10pt;
            }
        """)
        if edit_data and edit_data.get('description'):
            self.desc_input.setPlainText(edit_data['description'])
        layout.addWidget(self.desc_input)
        
        # Category selector
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("Categoría:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Personal", "Universidad", "Fedora"])
        self.category_combo.setMinimumHeight(36)
        if edit_data:
            idx = self.category_combo.findText(edit_data.get('category', 'Personal'))
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
        cat_layout.addWidget(self.category_combo, 1)
        layout.addLayout(cat_layout)
        
        # Deadline section
        deadline_layout = QHBoxLayout()
        self.deadline_check = QCheckBox("Deadline:")
        self.deadline_check.setChecked(edit_data.get('deadline') is not None if edit_data else False)
        deadline_layout.addWidget(self.deadline_check)
        
        self.deadline_date = QDateEdit()
        self.deadline_date.setCalendarPopup(True)
        self.deadline_date.setDisplayFormat("dd/MM/yyyy")
        self.deadline_date.setMinimumHeight(36)
        self.deadline_date.setMinimumWidth(140)
        # Style the calendar popup
        self.deadline_date.calendarWidget().setStyleSheet("""
            QCalendarWidget {
                background-color: rgb(40, 40, 45);
            }
            QCalendarWidget QWidget {
                alternate-background-color: rgb(50, 50, 55);
            }
            QCalendarWidget QAbstractItemView:enabled {
                background-color: rgb(40, 40, 45);
                color: white;
                selection-background-color: rgba(66, 133, 244, 0.5);
                selection-color: white;
            }
            QCalendarWidget QToolButton {
                color: white;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px;
                font-family: "Source Code Pro";
            }
            QCalendarWidget QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QCalendarWidget QMenu {
                background-color: rgb(45, 45, 50);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QCalendarWidget QSpinBox {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
            QCalendarWidget #qt_calendar_navigationbar {
                background-color: rgb(35, 35, 40);
                padding: 4px;
            }
            QCalendarWidget #qt_calendar_prevmonth, 
            QCalendarWidget #qt_calendar_nextmonth {
                qproperty-icon: none;
                border: none;
                color: white;
                font-size: 16px;
                padding: 4px 8px;
            }
        """)
        if edit_data and edit_data.get('deadline'):
            date = QDate.fromString(edit_data['deadline'], "yyyy-MM-dd")
            self.deadline_date.setDate(date)
        else:
            self.deadline_date.setDate(QDate.currentDate().addDays(7))
        self.deadline_date.setEnabled(self.deadline_check.isChecked())
        self.deadline_check.toggled.connect(self.deadline_date.setEnabled)
        deadline_layout.addWidget(self.deadline_date, 1)
        layout.addLayout(deadline_layout)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
    def get_task_data(self):
        deadline = None
        if self.deadline_check.isChecked():
            deadline = self.deadline_date.date().toString("yyyy-MM-dd")
        return {
            'title': self.title_input.text().strip(),
            'description': self.desc_input.toPlainText().strip(),
            'category': self.category_combo.currentText(),
            'deadline': deadline
        }


class TaskDetailDialog(QDialog):
    """Dialog to show task details"""
    
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle("Detalle de Tarea")
        self.setFixedSize(320, 300)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setup_ui()
        
    def setup_ui(self):
        from PyQt6.QtWidgets import QTextEdit
        
        # Main container with glass effect
        container = QFrame(self)
        container.setGeometry(0, 0, 320, 300)
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 35, 245);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header with category color
        colors = {
            "Personal": "66, 133, 244",
            "Fedora": "81, 162, 218",
            "Universidad": "52, 168, 83"
        }
        color = colors.get(self.task.get('category', ''), "136, 136, 136")
        
        # Title
        title = self.task.get('title', self.task.get('text', ''))
        title_label = QLabel(title)
        title_label.setFont(QFont("Source Code Pro", 12, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: rgb({color}); background: transparent; border: none;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Description in scrollable text area
        desc = self.task.get('description', '')
        desc_edit = QTextEdit()
        desc_edit.setPlainText(desc if desc else "Sin descripción")
        desc_edit.setReadOnly(True)
        desc_edit.setFont(QFont("Source Code Pro", 9))
        desc_edit.setFrameShape(QFrame.Shape.NoFrame)
        desc_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 6px;
                padding: 8px;
                color: {"rgb(200, 200, 210)" if desc else "rgba(150, 150, 160, 0.6)"};
            }}
        """)
        desc_edit.setMinimumHeight(100)
        layout.addWidget(desc_edit, 1)
        
        # Deadline info (only if exists)
        if self.task.get('deadline'):
            from datetime import datetime, date as dt_date
            deadline_date = datetime.strptime(self.task['deadline'], "%Y-%m-%d").date()
            today = dt_date.today()
            days_left = (deadline_date - today).days
            
            if days_left < 0:
                deadline_color = "rgba(255, 77, 79, 0.9)"
                deadline_icon = "⚠️"
                status_text = f" (vencido hace {-days_left} días)"
            elif days_left == 0:
                deadline_color = "rgba(250, 173, 20, 0.9)"
                deadline_icon = "⏰"
                status_text = " (hoy)"
            elif days_left == 1:
                deadline_color = "rgba(250, 219, 20, 0.9)"
                deadline_icon = "📅"
                status_text = " (mañana)"
            elif days_left <= 7:
                deadline_color = "rgba(250, 219, 20, 0.9)"
                deadline_icon = "📅"
                status_text = f" (en {days_left} días)"
            else:
                deadline_color = "rgba(180, 180, 190, 0.8)"
                deadline_icon = "📅"
                status_text = ""
            
            deadline_text = deadline_date.strftime("%d/%m/%Y")
            dl_label = QLabel(f"{deadline_icon} Deadline: {deadline_text}{status_text}")
            dl_label.setFont(QFont("Source Code Pro", 9))
            dl_label.setStyleSheet(f"color: {deadline_color}; background: transparent; border: none;")
            layout.addWidget(dl_label)
        
        # Completed date (only if completed)
        if self.task.get('completed_date'):
            comp_label = QLabel(f"✓ Completado: {self.task['completed_date']}")
            comp_label.setFont(QFont("Source Code Pro", 9))
            comp_label.setStyleSheet("color: rgba(82, 196, 26, 0.9); background: transparent; border: none;")
            layout.addWidget(comp_label)
        
        # Close button
        close_btn = QPushButton("Cerrar")
        close_btn.setFont(QFont("Source Code Pro", 9))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: rgb(200, 200, 210);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class DraggableTaskCard(QFrame):
    """A draggable task card for the Kanban board"""
    
    task_dropped = pyqtSignal(dict, str)  # task, new_status
    task_edit_requested = pyqtSignal(dict)
    task_delete_requested = pyqtSignal(dict)
    task_detail_requested = pyqtSignal(dict)
    
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.drag_start_position = None
        self.is_dragging = False
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedHeight(60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)
        
        # Card styling
        colors = {
            "Personal": "66, 133, 244",
            "Fedora": "81, 162, 218",
            "Universidad": "52, 168, 83"
        }
        color = colors.get(self.task['category'], "136, 136, 136")
        
        self.setStyleSheet(f"""
            DraggableTaskCard {{
                background-color: rgba(50, 50, 55, 200);
                border-left: 3px solid rgba({color}, 200);
                border-radius: 6px;
                margin: 2px;
            }}
            DraggableTaskCard:hover {{
                background-color: rgba(60, 60, 65, 220);
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Task title (not description)
        title = self.task.get('title', self.task.get('text', ''))
        if len(title) > 40:
            title = title[:40] + "..."
        task_label = QLabel(title)
        task_label.setFont(QFont("Source Code Pro", 8))
        task_label.setStyleSheet("color: rgb(220, 220, 225); background: transparent;")
        task_label.setWordWrap(False)
        task_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(task_label, 0, Qt.AlignmentFlag.AlignTop)
        
        # Bottom row: category badge and deadline/date
        bottom = QHBoxLayout()
        bottom.setSpacing(4)
        
        # Category badge
        badge = QLabel(self.task['category'][:3])
        badge.setFixedSize(24, 14)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFont(QFont("Source Code Pro", 6))
        badge.setStyleSheet(f"""
            background-color: rgba({color}, 180);
            color: white;
            border-radius: 3px;
        """)
        bottom.addWidget(badge)
        
        # Completion date if completed
        if self.task.get('completed_date'):
            date_label = QLabel(f"✓ {self.task['completed_date']}")
            date_label.setFont(QFont("Source Code Pro", 6))
            date_label.setStyleSheet("color: rgba(82, 196, 26, 0.9); background: transparent;")
            bottom.addWidget(date_label)
        # Deadline if set and not completed
        elif self.task.get('deadline'):
            from datetime import datetime, date as dt_date
            deadline_str = self.task['deadline']
            deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
            today = dt_date.today()
            days_left = (deadline_date - today).days
            
            # Format display date
            display_date = deadline_date.strftime("%d/%m")
            
            # Color based on urgency
            if days_left < 0:
                # Overdue - red
                deadline_color = "rgba(255, 77, 79, 0.9)"
                deadline_text = f"⚠ {display_date}"
            elif days_left == 0:
                # Due today - orange
                deadline_color = "rgba(250, 173, 20, 0.9)"
                deadline_text = f"⏰ Hoy"
            elif days_left <= 2:
                # Due soon - yellow
                deadline_color = "rgba(250, 219, 20, 0.9)"
                deadline_text = f"📅 {display_date}"
            else:
                # Normal - muted
                deadline_color = "rgba(180, 180, 190, 0.8)"
                deadline_text = f"📅 {display_date}"
            
            date_label = QLabel(deadline_text)
            date_label.setFont(QFont("Source Code Pro", 6))
            date_label.setStyleSheet(f"color: {deadline_color}; background: transparent;")
            bottom.addWidget(date_label)
        
        bottom.addStretch()
        layout.addLayout(bottom)
        
    def show_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(45, 45, 50, 245);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                color: rgb(200, 200, 210);
                padding: 6px 16px;
                font-family: 'Source Code Pro';
                font-size: 9pt;
            }
            QMenu::item:selected {
                background-color: rgba(66, 133, 244, 150);
                border-radius: 4px;
            }
        """)
        
        detail_action = QAction("Ver detalle", self)
        edit_action = QAction("Editar", self)
        delete_action = QAction("Eliminar", self)
        
        detail_action.triggered.connect(lambda: self.task_detail_requested.emit(self.task))
        edit_action.triggered.connect(lambda: self.task_edit_requested.emit(self.task))
        delete_action.triggered.connect(lambda: self.task_delete_requested.emit(self.task))
        
        menu.addAction(detail_action)
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.exec(self.mapToGlobal(pos))
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
            self.is_dragging = False
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not self.drag_start_position:
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < 15:
            return
            
        self.is_dragging = True
        
        # Start drag
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Serialize task data - ensure all values are serializable
        import json
        task_copy = {
            'title': self.task.get('title', ''),
            'text': self.task.get('text', ''),
            'description': self.task.get('description', ''),
            'category': self.task.get('category', ''),
            'status': self.task.get('status', 'todo'),
            'deadline': self.task.get('deadline'),
            'completed': self.task.get('completed', False),
            'completed_date': self.task.get('completed_date'),
            'file': str(self.task.get('file', '')),
            'line': self.task.get('line', 0)
        }
        mime_data.setText(json.dumps(task_copy))
        drag.setMimeData(mime_data)
        
        # Create drag pixmap
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        
        # Execute drag
        result = drag.exec(Qt.DropAction.MoveAction)
        
        try:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.drag_start_position = None
        except RuntimeError:
            # Object was deleted during drag
            pass
        
    def mouseReleaseEvent(self, event):
        try:
            # Show detail on click only if not dragging
            if event.button() == Qt.MouseButton.LeftButton:
                if self.drag_start_position and not getattr(self, 'is_dragging', False):
                    if (event.pos() - self.drag_start_position).manhattanLength() < 15:
                        self.task_detail_requested.emit(self.task)
            
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.drag_start_position = None
            self.is_dragging = False
            super().mouseReleaseEvent(event)
        except RuntimeError:
            # Object was deleted during drag operation
            pass


class KanbanColumn(QFrame):
    """A column in the Kanban board that accepts dropped tasks"""
    
    task_moved = pyqtSignal(dict, str)  # task, new_status
    
    def __init__(self, title, status, color, parent=None):
        super().__init__(parent)
        self.title = title
        self.status = status  # "todo", "progress", "done"
        self.color = color
        self.setAcceptDrops(True)
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet(f"""
            KanbanColumn {{
                background-color: rgba(40, 40, 45, 150);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 10);
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        
        # Header
        header = QHBoxLayout()
        
        # Color indicator
        indicator = QFrame()
        indicator.setFixedSize(8, 8)
        indicator.setStyleSheet(f"background-color: {self.color}; border-radius: 4px;")
        header.addWidget(indicator)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Source Code Pro", 9, QFont.Weight.Bold))
        title_label.setStyleSheet("color: rgb(200, 200, 210); background: transparent;")
        header.addWidget(title_label)
        
        # Count badge
        self.count_label = QLabel("0")
        self.count_label.setFixedSize(20, 16)
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setFont(QFont("Source Code Pro", 7))
        self.count_label.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.1);
            color: rgba(200, 200, 210, 0.8);
            border-radius: 8px;
        """)
        header.addWidget(self.count_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Scroll area for tasks
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 2px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        scroll.viewport().setStyleSheet("background: transparent;")
        
        self.tasks_widget = QWidget()
        self.tasks_widget.setStyleSheet("background: transparent;")
        self.tasks_layout = QVBoxLayout(self.tasks_widget)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(4)
        self.tasks_layout.addStretch()
        
        scroll.setWidget(self.tasks_widget)
        layout.addWidget(scroll, 1)
        
    def add_task_card(self, task, kanban_parent):
        """Add a task card to this column"""
        card = DraggableTaskCard(task, self)
        card.task_edit_requested.connect(kanban_parent.edit_task)
        card.task_delete_requested.connect(kanban_parent.delete_task)
        card.task_detail_requested.connect(kanban_parent.show_task_detail)
        self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, card)
        self.update_count()
        
    def clear_tasks(self):
        """Remove all task cards"""
        while self.tasks_layout.count() > 1:
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.update_count()
        
    def update_count(self):
        count = self.tasks_layout.count() - 1  # Exclude stretch
        self.count_label.setText(str(count))
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            self.setStyleSheet(f"""
                KanbanColumn {{
                    background-color: rgba(66, 133, 244, 30);
                    border-radius: 8px;
                    border: 2px dashed rgba(66, 133, 244, 150);
                }}
            """)
            event.acceptProposedAction()
            
    def dragLeaveEvent(self, event):
        self.setStyleSheet(f"""
            KanbanColumn {{
                background-color: rgba(40, 40, 45, 150);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 10);
            }}
        """)
        
    def dropEvent(self, event):
        self.setStyleSheet(f"""
            KanbanColumn {{
                background-color: rgba(40, 40, 45, 150);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 10);
            }}
        """)
        
        import json
        try:
            text = event.mimeData().text()
            if not text:
                print("Drop error: Empty mime data")
                event.ignore()
                return
                
            task_data = json.loads(text)
            # Convert file path back to Path object
            if task_data.get('file'):
                task_data['file'] = Path(task_data['file'])
            self.task_moved.emit(task_data, self.status)
            event.acceptProposedAction()
        except json.JSONDecodeError as e:
            print(f"Drop JSON error: {e}")
            event.ignore()
        except Exception as e:
            print(f"Drop error: {e}")
            event.ignore()


class ObsidianTasks(QWidget):
    """Kanban board for Obsidian tasks"""
    
    tasks_updated = pyqtSignal()  # Signal when tasks are loaded/updated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_category = "all"
        self.tasks = []
        self.setup_ui()
        self.load_all_tasks()
        
        # Auto-refresh every 30 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_all_tasks)
        self.timer.start(30000)
        
    def get_file_for_category(self, category):
        """Get the markdown file path for a category"""
        files = {
            "Personal": Path("/home/jjulianleon/Documents/Obsidian/Personal/Pendientes Personal.md"),
            "Universidad": Path("/home/jjulianleon/Documents/Obsidian/Universidad/8vo Semestre/Pendientes Universidad.md"),
            "Fedora": Path("/home/jjulianleon/Documents/Obsidian/Pendientes Fedora.md")
        }
        return files.get(category)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        
        # Header with add button only
        header = QHBoxLayout()
        header.addStretch()
        
        add_btn = QPushButton("+")
        add_btn.setFixedSize(26, 26)
        add_btn.clicked.connect(self.add_task)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(66, 133, 244, 0.3);
                color: white;
                border: none;
                border-radius: 13px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(66, 133, 244, 0.5);
            }
        """)
        header.addWidget(add_btn)
        layout.addLayout(header)
        
        # Category filter tabs
        cat_tabs = QHBoxLayout()
        cat_tabs.setSpacing(3)
        
        self.cat_buttons = {}
        for cat in ["Todas", "Personal", "Uni", "Fedora"]:
            btn = QPushButton(cat)
            btn.setCheckable(True)
            btn.setChecked(cat == "Todas")
            actual_cat = "Universidad" if cat == "Uni" else cat
            btn.clicked.connect(lambda checked, c=actual_cat: self.set_category(c))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.05);
                    color: rgba(200, 200, 210, 0.6);
                    border: none;
                    border-radius: 6px;
                    padding: 4px 6px;
                    font-size: 8px;
                    font-family: "Source Code Pro";
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
                QPushButton:checked {
                    background-color: rgba(66, 133, 244, 0.3);
                    color: rgb(200, 200, 210);
                }
            """)
            self.cat_buttons[cat] = btn
            cat_tabs.addWidget(btn)
        
        layout.addLayout(cat_tabs)
        
        # Kanban columns
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(6)
        
        self.columns = {}
        column_configs = [
            ("Por hacer", "todo", "#F4B400"),
            ("En progreso", "progress", "#4285F4"),
            ("Finalizado", "done", "#34A853")
        ]
        
        for title, status, color in column_configs:
            column = KanbanColumn(title, status, color, self)
            column.task_moved.connect(self.on_task_moved)
            self.columns[status] = column
            columns_layout.addWidget(column)
        
        layout.addLayout(columns_layout, 1)
        
    def set_category(self, category):
        for cat, btn in self.cat_buttons.items():
            actual = "Universidad" if cat == "Uni" else cat
            btn.setChecked(actual == category or (category == "Todas" and cat == "Todas"))
        self.current_category = "all" if category == "Todas" else category
        self.refresh_display()
        
    def load_all_tasks(self):
        """Load tasks from all Obsidian markdown files"""
        self.tasks = []
        
        for category in ["Personal", "Universidad", "Fedora"]:
            file_path = self.get_file_for_category(category)
            if file_path and file_path.exists():
                tasks = self.parse_markdown_file(file_path, category)
                self.tasks.extend(tasks)
        
        self.refresh_display()
        self.tasks_updated.emit()  # Notify calendar to sync deadlines
        
    def parse_markdown_file(self, file_path, category):
        """Parse tasks from markdown file with status detection"""
        tasks = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Match uncompleted: - [ ] title | description [deadline: YYYY-MM-DD] (en progreso)?
                    # Format with optional description separated by |
                    uncompleted = re.match(r'^- \[ \] (.+?)(?:\s*\|\s*(.+?))?(?:\s*\[deadline:\s*(\d{4}-\d{2}-\d{2})\])?(?:\s*\((en progreso)\))?$', line)
                    if uncompleted:
                        title = uncompleted.group(1).strip()
                        description = uncompleted.group(2).strip() if uncompleted.group(2) else ''
                        deadline = uncompleted.group(3)
                        in_progress = uncompleted.group(4) is not None
                        tasks.append({
                            'title': title,
                            'text': title,  # Keep for backwards compatibility
                            'description': description,
                            'category': category,
                            'status': 'progress' if in_progress else 'todo',
                            'completed': False,
                            'completed_date': None,
                            'deadline': deadline,
                            'line': line_num,
                            'file': file_path
                        })
                        continue
                    
                    # Match completed: - [x] title | description (completado: YYYY-MM-DD)
                    completed = re.match(r'^- \[x\] (.+?)(?:\s*\|\s*(.+?))?(?:\s*\[deadline:\s*\d{4}-\d{2}-\d{2}\])?(?:\s*(?:\(completado:\s*(\d{4}-\d{2}-\d{2})\)|✅\s*(\d{4}-\d{2}-\d{2})))?$', line)
                    if completed:
                        title = completed.group(1).strip()
                        description = completed.group(2).strip() if completed.group(2) else ''
                        date = completed.group(3) or completed.group(4)
                        tasks.append({
                            'title': title,
                            'text': title,  # Keep for backwards compatibility
                            'description': description,
                            'category': category,
                            'status': 'done',
                            'completed': True,
                            'completed_date': date,
                            'deadline': None,
                            'line': line_num,
                            'file': file_path
                        })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return tasks
        
    def refresh_display(self):
        """Refresh all Kanban columns"""
        # Clear all columns
        for column in self.columns.values():
            column.clear_tasks()
        
        # Filter and add tasks to columns
        for task in self.tasks:
            # Category filter
            if self.current_category != "all" and task['category'] != self.current_category:
                continue
            
            # Add to appropriate column
            status = task.get('status', 'todo')
            if status in self.columns:
                self.columns[status].add_task_card(task, self)
                
    def on_task_moved(self, task, new_status):
        """Handle task being moved to a new column"""
        old_status = task.get('status', 'todo')
        if old_status == new_status:
            return
            
        # Update task status
        task['status'] = new_status
        
        if new_status == 'done':
            task['completed'] = True
            task['completed_date'] = datetime.now().strftime("%Y-%m-%d")
        else:
            task['completed'] = False
            task['completed_date'] = None
        
        # Update in file
        self.update_task_in_file(task, old_status, new_status)
        self.load_all_tasks()
        
    def update_task_in_file(self, task, old_status, new_status):
        """Update task status in the markdown file"""
        file_path = task['file']
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            task_title = task.get('title', task.get('text', ''))
            description = task.get('description', '')
            deadline = task.get('deadline')
            
            desc_part = f" | {description}" if description else ""
            deadline_part = f" [deadline: {deadline}]" if deadline else ""
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Find the task line based on old status (with or without deadline)
                found = False
                if old_status == 'todo' and f"- [ ] {task_title}" in stripped and "(en progreso)" not in stripped:
                    found = True
                elif old_status == 'progress' and f"- [ ] {task_title}" in stripped and "(en progreso)" in stripped:
                    found = True
                elif old_status == 'done' and f"- [x] {task_title}" in stripped:
                    found = True
                
                if found:
                    # Write new line based on new status
                    if new_status == 'todo':
                        lines[i] = f"- [ ] {task_title}{desc_part}{deadline_part}\n"
                    elif new_status == 'progress':
                        lines[i] = f"- [ ] {task_title}{desc_part}{deadline_part} (en progreso)\n"
                    elif new_status == 'done':
                        # When completed, remove deadline and add completion date
                        date = datetime.now().strftime("%Y-%m-%d")
                        lines[i] = f"- [x] {task_title}{desc_part} (completado: {date})\n"
                    break
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        except Exception as e:
            print(f"Error updating task: {e}")
            
    def add_task(self):
        """Add a new task"""
        default_cat = self.current_category if self.current_category != "all" else "Personal"
        
        dialog = AddTaskDialog(self)
        idx = dialog.category_combo.findText(default_cat)
        if idx >= 0:
            dialog.category_combo.setCurrentIndex(idx)
            
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_task_data()
            if data['title']:
                self.save_task_to_file(data['title'], data.get('description', ''), data['category'], data.get('deadline'))
                self.load_all_tasks()
                
    def save_task_to_file(self, title, description, category, deadline=None):
        """Save a new task to the appropriate markdown file"""
        file_path = self.get_file_for_category(category)
        if not file_path:
            return
            
        # Create file if doesn't exist
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Pendientes {category}\n\n")
        
        # Build task line: - [ ] title | description [deadline: ...]
        desc_part = f" | {description}" if description else ""
        deadline_part = f" [deadline: {deadline}]" if deadline else ""
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"- [ ] {title}{desc_part}{deadline_part}\n")
            
    def edit_task(self, task):
        """Edit an existing task"""
        dialog = AddTaskDialog(self, edit_data={
            'title': task.get('title', task.get('text', '')),
            'description': task.get('description', ''),
            'category': task['category'],
            'deadline': task.get('deadline')
        })
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_task_data()
            if new_data['title']:
                self.update_task_text(task, new_data)
                self.load_all_tasks()
                
    def show_task_detail(self, task):
        """Show task detail dialog"""
        dialog = TaskDetailDialog(task, self)
        dialog.exec()
                
    def update_task_text(self, old_task, new_data):
        """Update task text in file"""
        # If category changed, move to new file
        if old_task['category'] != new_data['category']:
            self.remove_task_from_file(old_task)
            new_deadline = new_data.get('deadline') or old_task.get('deadline')
            self.save_task_to_file(new_data['title'], new_data.get('description', ''), new_data['category'], new_deadline)
        else:
            file_path = old_task['file']
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                old_title = old_task.get('title', old_task.get('text', ''))
                new_title = new_data['title']
                new_desc = new_data.get('description', '')
                new_deadline = new_data.get('deadline')
                status = old_task.get('status', 'todo')
                
                # Build parts
                desc_part = f" | {new_desc}" if new_desc else ""
                deadline_part = f" [deadline: {new_deadline}]" if new_deadline else ""
                
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    
                    # Match line with or without deadline/description
                    if status == 'todo' and f"- [ ] {old_title}" in stripped and "(en progreso)" not in stripped:
                        lines[i] = f"- [ ] {new_title}{desc_part}{deadline_part}\n"
                        break
                    elif status == 'progress' and f"- [ ] {old_title}" in stripped and "(en progreso)" in stripped:
                        lines[i] = f"- [ ] {new_title}{desc_part}{deadline_part} (en progreso)\n"
                        break
                    elif status == 'done' and f"- [x] {old_title}" in stripped:
                        date = old_task.get('completed_date', datetime.now().strftime("%Y-%m-%d"))
                        lines[i] = f"- [x] {new_title}{desc_part} (completado: {date})\n"
                        break
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            except Exception as e:
                print(f"Error updating task: {e})")
                
    def delete_task(self, task):
        """Delete a task with confirmation"""
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirmar")
        text = task['text']
        msg.setText(f"Eliminar '{text[:25]}...'?" if len(text) > 25 else f"Eliminar '{text}'?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: rgba(30, 30, 35, 240);
            }
            QMessageBox QLabel {
                color: rgb(200, 200, 210);
                font-family: 'Source Code Pro';
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: rgb(200, 200, 210);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 6px 16px;
                font-family: 'Source Code Pro';
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.remove_task_from_file(task)
            self.load_all_tasks()
            
    def remove_task_from_file(self, task):
        """Remove a task from the markdown file"""
        file_path = task['file']
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            task_title = task.get('title', task.get('text', ''))
            new_lines = []
            
            for line in lines:
                stripped = line.strip()
                # Skip any line that matches this task (with or without deadline/description)
                if f"- [ ] {task_title}" in stripped and "(en progreso)" not in stripped:
                    continue
                if f"- [ ] {task_title}" in stripped and "(en progreso)" in stripped:
                    continue
                if f"- [x] {task_title}" in stripped:
                    continue
                new_lines.append(line)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
        except Exception as e:
            print(f"Error removing task: {e}")


# ============== MAIN WIDGET ==============
class CalendarWidget(GlassWidget):
    """Main calendar widget with tabs"""
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
        self.setup_ui()
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            screen.width() - self.width() - 50,
            50
        )
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 10)
        layout.setSpacing(0)
        
        # Header with close button only (minimal height)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 4)
        
        close_btn = QPushButton("x")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Config.TEXT_SECONDARY.name()};
                border: none;
                border-radius: 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 100, 100, 0.3);
                color: white;
            }}
        """)
        
        header.addStretch()
        header.addWidget(close_btn)
        layout.addLayout(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
                margin-top: 12px;
            }}
            QTabWidget::tab-bar {{
                alignment: center;
            }}
            QTabBar::tab {{
                background: rgba(255, 255, 255, 0.1);
                color: {Config.TEXT_SECONDARY.name()};
                padding: 6px 18px;
                margin: 0 4px;
                border-radius: 10px;
                font-size: 11px;
                font-family: "Source Code Pro";
                min-width: 60px;
                text-align: center;
            }}
            QTabBar::tab:selected {{
                background: rgba(66, 133, 244, 0.3);
                color: {Config.TEXT_COLOR.name()};
            }}
            QTabBar::tab:hover {{
                background: rgba(255, 255, 255, 0.15);
            }}
        """)
        
        # Create tabs
        self.monthly_calendar = MonthlyCalendar()
        self.weekly_schedule = WeeklySchedule()
        self.obsidian_tasks = ObsidianTasks()
        
        # Connect deadline click to show tasks
        self.monthly_calendar.deadline_clicked.connect(self.show_deadline_tasks)
        
        # Connect tasks updated signal to sync calendar
        self.obsidian_tasks.tasks_updated.connect(self.sync_deadlines)
        
        # Add tabs
        self.tabs.addTab(self.monthly_calendar, "Mes")
        self.tabs.addTab(self.weekly_schedule, "Semana")
        self.tabs.addTab(self.obsidian_tasks, "Pendientes")
        
        # Connect tab change to sync deadlines
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tabs)
        
        # Time display
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont("Source Code Pro", 10))
        self.time_label.setStyleSheet(f"color: {Config.TEXT_SECONDARY.name()};")
        layout.addWidget(self.time_label)
        
        # Update time every second
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        self.update_time()
        
        # Initial sync of deadlines
        QTimer.singleShot(500, self.sync_deadlines)
        
    def on_tab_changed(self, index):
        """Sync deadlines when switching to calendar tab"""
        if index == 0:  # Monthly tab
            self.sync_deadlines()
            
    def sync_deadlines(self):
        """Sync deadlines from tasks to calendar"""
        self.monthly_calendar.set_deadlines(self.obsidian_tasks.tasks)
        
    def show_deadline_tasks(self, tasks):
        """Show a dialog with tasks for clicked deadline date"""
        if len(tasks) == 1:
            # Solo una tarea - mostrar directamente el detalle
            dialog = TaskDetailDialog(tasks[0], self)
            dialog.exec()
        else:
            # Múltiples tareas - mostrar lista
            dialog = DeadlineTasksDialog(tasks, self)
            dialog.exec()
        
    def update_time(self):
        now = datetime.now()
        days_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        self.time_label.setText(
            f"{days_es[now.weekday()]}, {now.strftime('%d/%m/%Y')} - {now.strftime('%H:%M:%S')}"
        )


# ============== CLICKABLE TASK FRAME ==============
class ClickableTaskFrame(QFrame):
    """Clickable task card for DeadlineTasksDialog"""
    clicked = pyqtSignal(dict)
    
    def __init__(self, task, color, parent=None):
        super().__init__(parent)
        self.task = task
        self.color = color
        self.setup_ui()
        
    def setup_ui(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(50, 50, 55, 180);
                border-left: 3px solid rgba({self.color}, 200);
                border-radius: 8px;
            }}
            QFrame:hover {{
                background-color: rgba(60, 60, 65, 200);
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        
        # Title
        title = self.task.get('title', self.task.get('text', ''))
        title_label = QLabel(title)
        title_label.setFont(QFont("Source Code Pro", 10, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: rgb({self.color}); background: transparent; border: none;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Description
        desc = self.task.get('description', '')
        if desc:
            desc_label = QLabel(desc)
            desc_label.setFont(QFont("Source Code Pro", 9))
            desc_label.setStyleSheet("color: rgb(200, 200, 210); background: transparent; border: none;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.task)
        super().mousePressEvent(event)


# ============== DEADLINE TASKS DIALOG ==============
class DeadlineTasksDialog(QDialog):
    """Dialog to show tasks for a specific deadline date"""
    
    def __init__(self, tasks, parent=None):
        super().__init__(parent)
        self.tasks = tasks
        self.setWindowTitle("Tareas con Deadline")
        self.setFixedSize(320, 350)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setup_ui()
        
    def setup_ui(self):
        from PyQt6.QtWidgets import QTextEdit
        
        container = QFrame(self)
        container.setGeometry(0, 0, 320, 350)
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 35, 245);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header with date
        if self.tasks:
            date_str = self.tasks[0].get('deadline', '')
            if date_str:
                from datetime import datetime
                deadline_date = datetime.strptime(date_str, "%Y-%m-%d")
                header = QLabel(f"📅 {deadline_date.strftime('%d/%m/%Y')}")
            else:
                header = QLabel("📅 Tareas")
        else:
            header = QLabel("📅 Tareas")
        header.setFont(QFont("Source Code Pro", 12, QFont.Weight.Bold))
        header.setStyleSheet("color: rgb(66, 133, 244); background: transparent; border: none;")
        layout.addWidget(header)
        
        # Scroll area for tasks
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.05);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
        
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        tasks_layout.setContentsMargins(0, 0, 8, 0)
        tasks_layout.setSpacing(10)
        
        colors = {
            "Personal": "66, 133, 244",
            "Fedora": "81, 162, 218",
            "Universidad": "52, 168, 83"
        }
        
        for task in self.tasks:
            color = colors.get(task.get('category', ''), "136, 136, 136")
            
            # Clickable task card
            task_frame = ClickableTaskFrame(task, color, self)
            task_frame.clicked.connect(self.on_task_clicked)
            tasks_layout.addWidget(task_frame)
        
        tasks_layout.addStretch()
        scroll.setWidget(tasks_widget)
        layout.addWidget(scroll, 1)
        
        # Close button
        close_btn = QPushButton("Cerrar")
        close_btn.setFont(QFont("Source Code Pro", 9))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: rgb(200, 200, 210);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def on_task_clicked(self, task):
        """Show task detail when a task card is clicked"""
        dialog = TaskDetailDialog(task, self)
        dialog.exec()


# ============== ENTRY POINT ==============
def main():
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    widget = CalendarWidget()
    widget.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
