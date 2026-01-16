"""
Pomodoro Timer Widget
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QProgressBar, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from src.utils.styles import COLORS, FONT_FAMILY, get_button_style
from src.utils.constants import (
    POMODORO_WORK_DURATION, POMODORO_SHORT_BREAK, 
    POMODORO_LONG_BREAK, POMODORO_SESSIONS_BEFORE_LONG_BREAK
)
from src.core.database import db
from src.core.signals import SignalHub


class PomodoroTimer(QWidget):
    """Pomodoro timer widget"""
    
    session_completed = pyqtSignal(str)  # 'work' or 'break'
    
    def __init__(self, compact: bool = False, parent=None):
        super().__init__(parent)
        self.compact = compact
        self.signals = SignalHub.get_instance()
        
        # Timer state
        self.is_running = False
        self.is_work_session = True
        self.sessions_completed = 0
        self.current_session_id = None
        
        # Load durations from settings or use defaults
        self._load_durations()
        self.remaining_seconds = self.work_duration
        
        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        
        self.setup_ui()
    
    def _load_durations(self):
        """Load durations from database settings"""
        settings = db.get_all_settings()
        work_mins = settings.get('pomodoro_work', POMODORO_WORK_DURATION)
        short_break_mins = settings.get('pomodoro_short_break', POMODORO_SHORT_BREAK)
        long_break_mins = settings.get('pomodoro_long_break', POMODORO_LONG_BREAK)
        self.sessions_before_long = settings.get('pomodoro_sessions', POMODORO_SESSIONS_BEFORE_LONG_BREAK)
        
        self.work_duration = int(work_mins) * 60
        self.short_break = int(short_break_mins) * 60
        self.long_break = int(long_break_mins) * 60
    
    def reload_settings(self):
        """Reload settings from database (call after settings change)"""
        self._load_durations()
        if not self.is_running:
            # Reset to work session with new duration
            self.remaining_seconds = self.work_duration
            self._update_display()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        margin = 8 if self.compact else 16
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(8 if self.compact else 12)
        
        # Header
        if not self.compact:
            header = QLabel("Pomodoro")
            header.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
            header.setStyleSheet(f"color: rgb({COLORS['danger']}); background: transparent;")
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(header)
        
        # Timer display
        self.time_label = QLabel(self._format_time())
        font_size = 24 if self.compact else 36
        self.time_label.setFont(QFont(FONT_FAMILY, font_size, QFont.Weight.Bold))
        self.time_label.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)
        
        # Session type indicator
        self.session_label = QLabel("Trabajo")
        self.session_label.setFont(QFont(FONT_FAMILY, 10))
        self.session_label.setStyleSheet(f"color: rgb({COLORS['danger']}); background: transparent;")
        self.session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.session_label)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(100)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6 if self.compact else 8)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: rgba({COLORS['danger']}, 200);
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress)
        
        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        
        # Start/Pause button
        self.start_btn = QPushButton("Iniciar")
        self.start_btn.setFont(QFont(FONT_FAMILY, 9))
        self.start_btn.setStyleSheet(get_button_style('success'))
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self._toggle_timer)
        controls_layout.addWidget(self.start_btn)
        
        # Reset button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFont(QFont(FONT_FAMILY, 9))
        self.reset_btn.setStyleSheet(get_button_style())
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setFixedWidth(60)
        self.reset_btn.clicked.connect(self._reset)
        controls_layout.addWidget(self.reset_btn)
        
        # Skip button
        if not self.compact:
            self.skip_btn = QPushButton("Saltar")
            self.skip_btn.setFont(QFont(FONT_FAMILY, 9))
            self.skip_btn.setStyleSheet(get_button_style())
            self.skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.skip_btn.setFixedWidth(60)
            self.skip_btn.setToolTip("Saltar sesion")
            self.skip_btn.clicked.connect(self._skip)
            controls_layout.addWidget(self.skip_btn)
        
        layout.addLayout(controls_layout)
        
        # Sessions counter (only if not compact)
        if not self.compact:
            self.sessions_label = QLabel("Sesiones: 0/4")
            self.sessions_label.setFont(QFont(FONT_FAMILY, 9))
            self.sessions_label.setStyleSheet(f"color: rgb({COLORS['text_muted']}); background: transparent;")
            self.sessions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.sessions_label)
    
    def _format_time(self) -> str:
        """Format remaining time as MM:SS"""
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def _update_display(self):
        """Update all display elements"""
        self.time_label.setText(self._format_time())
        
        # Calculate progress
        if self.is_work_session:
            total = self.work_duration
            color = COLORS['danger']
            session_text = "Trabajo"
        else:
            total = self.short_break if self.sessions_completed % self.sessions_before_long != 0 else self.long_break
            color = COLORS['success']
            session_text = "Descanso"
        
        progress = int((self.remaining_seconds / total) * 100)
        self.progress.setValue(progress)
        
        self.session_label.setText(session_text)
        self.session_label.setStyleSheet(f"color: rgb({color}); background: transparent;")
        
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: rgba({color}, 200);
                border-radius: 3px;
            }}
        """)
        
        if not self.compact:
            self.sessions_label.setText(f"Sesiones: {self.sessions_completed}/{self.sessions_before_long}")
    
    def _toggle_timer(self):
        """Start or pause the timer"""
        if self.is_running:
            self._pause()
        else:
            self._start()
    
    def _start(self):
        """Start the timer"""
        self.is_running = True
        self.timer.start(1000)
        self.start_btn.setText("Pausar")
        self.start_btn.setStyleSheet(get_button_style('danger'))
        
        # Start pomodoro session in DB
        if self.is_work_session and not self.current_session_id:
            self.current_session_id = db.start_pomodoro(
                duration=POMODORO_WORK_DURATION,
                session_type='work'
            )
    
    def _pause(self):
        """Pause the timer"""
        self.is_running = False
        self.timer.stop()
        self.start_btn.setText("Continuar")
        self.start_btn.setStyleSheet(get_button_style('success'))
    
    def _reset(self):
        """Reset current session"""
        self.is_running = False
        self.timer.stop()
        
        if self.is_work_session:
            self.remaining_seconds = self.work_duration
        else:
            if self.sessions_completed % self.sessions_before_long == 0:
                self.remaining_seconds = self.long_break
            else:
                self.remaining_seconds = self.short_break
        
        self.start_btn.setText("Iniciar")
        self.start_btn.setStyleSheet(get_button_style('success'))
        self.current_session_id = None
        self._update_display()
    
    def _skip(self):
        """Skip to next session"""
        self._complete_session()
    
    def _tick(self):
        """Timer tick - called every second"""
        self.remaining_seconds -= 1
        
        if self.remaining_seconds <= 0:
            self._complete_session()
        else:
            self._update_display()
    
    def _complete_session(self):
        """Complete current session and switch"""
        self.timer.stop()
        self.is_running = False
        
        if self.is_work_session:
            # Complete work session
            if self.current_session_id:
                db.complete_pomodoro(self.current_session_id)
                self.current_session_id = None
            
            self.sessions_completed += 1
            self.session_completed.emit('work')
            
            # Emit signal to hub
            self.signals.pomodoro_completed.emit({
                'session_type': 'work',
                'sessions_completed': self.sessions_completed
            })
            
            # Switch to break
            self.is_work_session = False
            if self.sessions_completed % self.sessions_before_long == 0:
                self.remaining_seconds = self.long_break
            else:
                self.remaining_seconds = self.short_break
        else:
            # Complete break session
            self.session_completed.emit('break')
            
            # Switch to work
            self.is_work_session = True
            self.remaining_seconds = self.work_duration
        
        self.start_btn.setText("Iniciar")
        self.start_btn.setStyleSheet(get_button_style('success'))
        self._update_display()
    
    def get_today_stats(self) -> dict:
        """Get today's pomodoro statistics"""
        pomodoros = db.get_today_pomodoros()
        return {
            'completed': len(pomodoros),
            'total_minutes': len(pomodoros) * POMODORO_WORK_DURATION
        }


class MiniPomodoro(PomodoroTimer):
    """Compact pomodoro for widget view"""
    
    def __init__(self, parent=None):
        super().__init__(compact=True, parent=parent)
