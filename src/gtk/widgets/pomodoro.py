"""
Pomodoro Timer Widget - GTK4
Focus timer with work/break cycles
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager


class PomodoroTimer(Gtk.Box):
    """Pomodoro timer widget"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.add_css_class("glass-card")
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        
        # Timer state
        self.work_duration = 25 * 60  # 25 minutes
        self.break_duration = 5 * 60   # 5 minutes
        self.remaining_seconds = self.work_duration
        self.is_running = False
        self.is_break = False
        self.current_session_id = None
        self.timer_id = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup timer UI"""
        # Title
        title = Gtk.Label(label="Pomodoro")
        title.add_css_class("title-3")
        self.append(title)
        
        # Timer display
        self.timer_label = Gtk.Label(label="25:00")
        self.timer_label.add_css_class("pomodoro-timer")
        self.append(self.timer_label)
        
        # Status
        self.status_label = Gtk.Label(label="Listo para comenzar")
        self.status_label.add_css_class("dim-label")
        self.append(self.status_label)
        
        # Progress bar
        self.progress = Gtk.ProgressBar()
        self.progress.set_fraction(1.0)
        self.progress.set_size_request(200, -1)
        self.append(self.progress)
        
        # Controls
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        controls.set_halign(Gtk.Align.CENTER)
        controls.set_margin_top(16)
        
        self.start_btn = Gtk.Button(label="Iniciar")
        self.start_btn.add_css_class("suggested-action")
        self.start_btn.add_css_class("pill")
        self.start_btn.connect("clicked", self._on_start_pause)
        controls.append(self.start_btn)
        
        reset_btn = Gtk.Button(label="Reiniciar")
        reset_btn.add_css_class("flat")
        reset_btn.connect("clicked", self._on_reset)
        controls.append(reset_btn)
        
        self.append(controls)
        
        # Session info
        self.sessions_label = Gtk.Label(label="Sesiones hoy: 0")
        self.sessions_label.add_css_class("dim-label")
        self.sessions_label.add_css_class("caption")
        self.sessions_label.set_margin_top(20)
        self.append(self.sessions_label)
        
        self._update_sessions_count()
        
    def _on_start_pause(self, btn):
        """Start or pause timer"""
        if self.is_running:
            self._pause()
        else:
            self._start()
            
    def _start(self):
        """Start the timer"""
        self.is_running = True
        self.start_btn.set_label("Pausar")
        self.start_btn.remove_css_class("suggested-action")
        self.start_btn.add_css_class("destructive-action")
        
        if not self.is_break:
            self.status_label.set_text("¡Enfócate!")
            self.timer_label.add_css_class("pomodoro-active")
            # Start session in DB
            try:
                self.current_session_id = task_manager.start_pomodoro(duration=25)
            except:
                pass
        else:
            self.status_label.set_text("Descansando...")
            self.timer_label.remove_css_class("pomodoro-active")
            self.timer_label.add_css_class("pomodoro-break")
            
        # Start timer tick
        self.timer_id = GLib.timeout_add(1000, self._tick)
        
    def _pause(self):
        """Pause the timer"""
        self.is_running = False
        self.start_btn.set_label("Continuar")
        self.start_btn.remove_css_class("destructive-action")
        self.start_btn.add_css_class("suggested-action")
        self.status_label.set_text("Pausado")
        
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = None
            
    def _on_reset(self, btn):
        """Reset timer"""
        self._pause()
        self.is_break = False
        self.remaining_seconds = self.work_duration
        self._update_display()
        self.status_label.set_text("Listo para comenzar")
        self.timer_label.remove_css_class("pomodoro-active")
        self.timer_label.remove_css_class("pomodoro-break")
        self.progress.set_fraction(1.0)
        self.start_btn.set_label("Iniciar")
        
    def _tick(self) -> bool:
        """Timer tick callback"""
        if not self.is_running:
            return False
            
        self.remaining_seconds -= 1
        self._update_display()
        
        # Update progress
        total = self.break_duration if self.is_break else self.work_duration
        self.progress.set_fraction(self.remaining_seconds / total)
        
        if self.remaining_seconds <= 0:
            self._on_timer_complete()
            return False
            
        return True
        
    def _update_display(self):
        """Update timer display"""
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.timer_label.set_text(f"{minutes:02d}:{seconds:02d}")
        
    def _on_timer_complete(self):
        """Handle timer completion"""
        if not self.is_break:
            # Work session complete
            if self.current_session_id:
                try:
                    task_manager.complete_pomodoro(self.current_session_id)
                except:
                    pass
            self._update_sessions_count()
            
            # Switch to break
            self.is_break = True
            self.remaining_seconds = self.break_duration
            self.status_label.set_text("¡Tiempo de descanso!")
            self.timer_label.remove_css_class("pomodoro-active")
            self.timer_label.add_css_class("pomodoro-break")
        else:
            # Break complete
            self.is_break = False
            self.remaining_seconds = self.work_duration
            self.status_label.set_text("¡Listo para otra sesión!")
            self.timer_label.remove_css_class("pomodoro-break")
            
        self._update_display()
        self.progress.set_fraction(1.0)
        self.is_running = False
        self.start_btn.set_label("Iniciar")
        self.start_btn.remove_css_class("destructive-action")
        self.start_btn.add_css_class("suggested-action")
        
        # Show notification
        # TODO: Use libnotify
        
    def _update_sessions_count(self):
        """Update today's sessions count"""
        try:
            sessions = task_manager.get_today_pomodoros()
            self.sessions_label.set_text(f"Sesiones hoy: {len(sessions)}")
        except:
            pass
