#!/usr/bin/env python3
"""
Desktop Widget - GTK4 Version (Full Featured)
Compact widget with calendar, tasks, pomodoro, and quick actions
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gdk
from datetime import datetime, timedelta
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.core.task_manager import task_manager
from src.core.database import db
from src.gtk import init_theme
from src.utils.system import IS_MAC
from src.utils.constants import INTERNSHIP_END


class WidgetApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.jjjulianleon.productivitywidget")
        
    def do_activate(self):
        self.window = WidgetWindow(application=self)
        self._load_css()
        self.window.present()
        
    def _load_css(self):
        """Mismo tema que la app principal: una sola hoja, no una copia."""
        init_theme()


class WidgetWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Productivity Widget")
        self.set_default_size(520, 380)
        self.add_css_class("widget-window")
        
        # Pomodoro state
        self.pomodoro_running = False
        self.pomodoro_seconds = 25 * 60
        self.pomodoro_mode = "work"  # work, break
        
        self._setup_ui()
        self._start_timers()
        
    def _setup_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        # En macOS los botones semaforo se dibujan sobre la esquina superior
        # izquierda: se deja espacio para que no tapen el contenido.
        main_box.set_margin_top(34 if IS_MAC else 10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        
        # === TOP BAR ===
        top_bar = self._create_top_bar()
        main_box.append(top_bar)
        
        # === STATS ROW ===
        stats_row = self._create_stats_row()
        main_box.append(stats_row)
        
        # === MAIN CONTENT (2 columns) ===
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        content.set_vexpand(True)
        
        # Left: Calendar + Next class
        left_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left_col.set_hexpand(True)
        left_col.append(self._create_calendar())
        left_col.append(self._create_next_class_card())
        content.append(left_col)
        
        # Right: Urgent deadline + Pomodoro
        right_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right_col.set_size_request(180, -1)
        right_col.append(self._create_urgent_deadline())
        right_col.append(self._create_pomodoro())
        content.append(right_col)
        
        main_box.append(content)
        
        # === BOTTOM: Progress bar ===
        main_box.append(self._create_progress_bar())
        
        self.set_content(main_box)
        
    def _create_top_bar(self) -> Gtk.Box:
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Time
        self.time_label = Gtk.Label()
        self.time_label.add_css_class("dim-label")
        bar.append(self.time_label)
        
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        bar.append(spacer)
        
        # Quick note button
        note_btn = Gtk.Button()
        note_btn.set_icon_name("document-new-symbolic")
        note_btn.add_css_class("flat")
        note_btn.add_css_class("circular")
        note_btn.set_tooltip_text("Nota rápida")
        note_btn.connect("clicked", self._show_quick_note)
        bar.append(note_btn)
        
        # Open app button
        app_btn = Gtk.Button(label="Abrir App")
        app_btn.add_css_class("translucent-btn")
        app_btn.connect("clicked", self._open_main_app)
        bar.append(app_btn)
        
        return bar




        
    def _create_stats_row(self) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        stats = self._get_stats()
        
        # Pending
        self.pending_label = self._create_stat_box(
            str(stats['pending']), "pendientes", "accent"
        )
        row.append(self.pending_label)
        
        # Today
        self.today_label = self._create_stat_box(
            str(stats['today']), "hoy", "warning"
        )
        row.append(self.today_label)
        
        # Overdue
        self.overdue_label = self._create_stat_box(
            str(stats['overdue']), "atrasadas", "error"
        )
        row.append(self.overdue_label)
        
        # Completed
        self.completed_label = self._create_stat_box(
            str(stats['completed_today']), "completadas", "success"
        )
        row.append(self.completed_label)
        
        return row
        
    def _create_stat_box(self, value: str, label: str, style: str) -> Gtk.Box:
        """style: clase de Adwaita (accent / warning / error / success)"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.add_css_class("glass-card")
        box.set_hexpand(True)
        box.set_halign(Gtk.Align.CENTER)
        
        val_lbl = Gtk.Label(label=value)
        val_lbl.add_css_class("stat-mini")
        val_lbl.add_css_class(style)
        box.append(val_lbl)
        
        txt_lbl = Gtk.Label(label=label)
        txt_lbl.add_css_class("caption")
        txt_lbl.add_css_class("dim-label")
        box.append(txt_lbl)
        
        return box
        
    def _get_stats(self) -> dict:
        try:
            tasks = task_manager.get_all_tasks()
            today = datetime.now().strftime('%Y-%m-%d')
            
            pending = len([t for t in tasks if t.get('status') == 'pendiente'])
            today_count = len([t for t in tasks if t.get('deadline') == today and t.get('status') != 'completado'])
            overdue = len([t for t in tasks if t.get('deadline') and t['deadline'] < today and t.get('status') != 'completado'])
            completed = len([t for t in tasks if t.get('status') == 'completado'])
            
            return {'pending': pending, 'today': today_count, 'overdue': overdue, 'completed_today': completed}
        except:
            return {'pending': 0, 'today': 0, 'overdue': 0, 'completed_today': 0}
            
    def _create_calendar(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.add_css_class("glass-card")
        
        self.current_month = datetime.now()
        
        # Navigation
        nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        prev_btn = Gtk.Button()
        prev_btn.set_icon_name("go-previous-symbolic")
        prev_btn.add_css_class("flat")
        prev_btn.add_css_class("circular")
        prev_btn.connect("clicked", lambda _: self._change_month(-1))
        nav.append(prev_btn)
        
        self.month_label = Gtk.Label()
        self.month_label.add_css_class("heading")
        self.month_label.set_hexpand(True)
        nav.append(self.month_label)
        
        next_btn = Gtk.Button()
        next_btn.set_icon_name("go-next-symbolic")
        next_btn.add_css_class("flat")
        next_btn.add_css_class("circular")
        next_btn.connect("clicked", lambda _: self._change_month(1))
        nav.append(next_btn)
        
        box.append(nav)
        
        # Grid
        self.calendar_grid = Gtk.Grid()
        self.calendar_grid.set_column_homogeneous(True)
        self.calendar_grid.set_row_homogeneous(True)
        self.calendar_grid.set_column_spacing(1)
        self.calendar_grid.set_row_spacing(1)
        box.append(self.calendar_grid)
        
        self._update_calendar()
        
        return box
        
    def _change_month(self, delta):
        month = self.current_month.month + delta
        year = self.current_month.year
        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1
        self.current_month = self.current_month.replace(year=year, month=month)
        self._update_calendar()
        
    def _update_calendar(self):
        while child := self.calendar_grid.get_first_child():
            self.calendar_grid.remove(child)
            
        months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        self.month_label.set_text(f"{months[self.current_month.month - 1]} {self.current_month.year}")
        
        # Headers
        for col, day in enumerate(["L", "M", "X", "J", "V", "S", "D"]):
            lbl = Gtk.Label(label=day)
            lbl.add_css_class("caption")
            lbl.add_css_class("dim-label")
            self.calendar_grid.attach(lbl, col, 0, 1, 1)
            
        # Get deadlines
        self.deadlines = {}
        try:
            tasks = task_manager.get_tasks_with_deadlines()
            for t in tasks:
                if t.get('deadline') and t.get('status') != 'completado':
                    d = t['deadline']
                    if d not in self.deadlines:
                        self.deadlines[d] = []
                    self.deadlines[d].append(t)
        except:
            pass
            
        import calendar
        cal = calendar.Calendar(firstweekday=0)
        today = datetime.now()
        
        for row_idx, week in enumerate(cal.monthdayscalendar(self.current_month.year, self.current_month.month)):
            for col_idx, day in enumerate(week):
                if day == 0:
                    self.calendar_grid.attach(Gtk.Label(label=""), col_idx, row_idx + 1, 1, 1)
                else:
                    is_today = (day == today.day and self.current_month.month == today.month and self.current_month.year == today.year)
                    date_str = f"{self.current_month.year}-{self.current_month.month:02d}-{day:02d}"
                    has_deadline = date_str in self.deadlines
                    
                    btn = Gtk.Button()
                    btn.add_css_class("flat")
                    
                    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    box.set_halign(Gtk.Align.CENTER)
                    
                    lbl = Gtk.Label(label=str(day))
                    if is_today:
                        lbl.add_css_class("today-highlight")
                    box.append(lbl)
                    
                    if has_deadline:
                        dot = Gtk.Label(label="●")
                        dot.add_css_class("deadline-dot")
                        box.append(dot)
                        btn.connect("clicked", self._on_date_clicked, date_str)
                        btn.set_tooltip_text(f"{len(self.deadlines[date_str])} tarea(s)")
                        
                    btn.set_child(box)
                    self.calendar_grid.attach(btn, col_idx, row_idx + 1, 1, 1)
                    
    def _on_date_clicked(self, btn, date_str):
        tasks = self.deadlines.get(date_str, [])
        if not tasks:
            return
            
        popover = Gtk.Popover()
        popover.set_parent(btn)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(8)
        box.set_margin_end(8)
        
        header = Gtk.Label(label=f"Tareas: {date_str}")
        header.add_css_class("heading")
        box.append(header)
        
        for task in tasks[:5]:
            row = Gtk.Label(label=f"• {task.get('title', '')[:30]}")
            row.set_halign(Gtk.Align.START)
            box.append(row)
            
        popover.set_child(box)
        popover.popup()
                    
    def _create_next_class_card(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.add_css_class("next-class-card")
        
        header = Gtk.Label(label="Próxima clase")
        header.add_css_class("caption")
        header.add_css_class("dim-label")
        header.set_halign(Gtk.Align.START)
        box.append(header)
        
        self.next_class_label = Gtk.Label()
        self.next_class_label.add_css_class("heading")
        self.next_class_label.set_halign(Gtk.Align.START)
        box.append(self.next_class_label)
        
        self.next_class_time = Gtk.Label()
        self.next_class_time.add_css_class("caption")
        self.next_class_time.set_halign(Gtk.Align.START)
        box.append(self.next_class_time)
        
        self._update_next_class()
        
        return box
        
    def _update_next_class(self):
        """Get next class from database schedule events"""
        now = datetime.now()
        today = now.date()

        # Get schedule events for today from database
        # for_date aplica el fin de semestre y los eventos de un solo dia
        today_events = db.get_schedule_events(now.weekday(), for_date=today)

        # Filter by internship dates
        filtered_events = []
        for evt in today_events:
            # Filter internship events
            title_lower = evt.get('title', '').lower()
            is_internship = any(kw in title_lower for kw in ['pasant', 'trabajo', 'intern', 'work'])
            if is_internship and datetime.combine(today, datetime.min.time()) > INTERNSHIP_END:
                continue

            filtered_events.append(evt)

        # Find next upcoming event
        next_class = None
        for evt in sorted(filtered_events, key=lambda e: e.get('start_time', '00:00')):
            start_time = evt.get('start_time', '09:00')
            start_h, start_m = map(int, start_time.split(':'))
            class_time = now.replace(hour=start_h, minute=start_m, second=0)

            if class_time > now:
                diff = class_time - now
                mins = int(diff.total_seconds() // 60)
                next_class = (evt.get('title', 'Evento'), mins)
                break

        if next_class:
            self.next_class_label.set_text(next_class[0])
            if next_class[1] < 60:
                self.next_class_time.set_text(f"en {next_class[1]} min")
            else:
                h = next_class[1] // 60
                m = next_class[1] % 60
                self.next_class_time.set_text(f"en {h}h {m}m")
        else:
            self.next_class_label.set_text("Sin más clases")
            self.next_class_time.set_text("hoy")
            
    def _create_urgent_deadline(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.add_css_class("urgent-card")
        
        header = Gtk.Label(label="⚠ Más urgente")
        header.add_css_class("caption")
        header.set_halign(Gtk.Align.START)
        box.append(header)
        
        self.urgent_title = Gtk.Label()
        self.urgent_title.add_css_class("heading")
        self.urgent_title.set_halign(Gtk.Align.START)
        self.urgent_title.set_ellipsize(3)
        self.urgent_title.set_max_width_chars(20)
        box.append(self.urgent_title)
        
        self.urgent_date = Gtk.Label()
        self.urgent_date.add_css_class("caption")
        self.urgent_date.set_halign(Gtk.Align.START)
        box.append(self.urgent_date)
        
        self._update_urgent()
        
        return box
        
    def _update_urgent(self):
        try:
            tasks = task_manager.get_tasks_with_deadlines()
            pending = [t for t in tasks if t.get('status') != 'completado' and t.get('deadline')]
            pending.sort(key=lambda x: x['deadline'])
            
            if pending:
                task = pending[0]
                self.urgent_title.set_text(task.get('title', '')[:25])
                
                deadline = datetime.strptime(task['deadline'], '%Y-%m-%d')
                diff = (deadline.date() - datetime.now().date()).days
                
                if diff < 0:
                    self.urgent_date.set_text(f"¡{abs(diff)} días atrasado!")
                elif diff == 0:
                    self.urgent_date.set_text("¡HOY!")
                elif diff == 1:
                    self.urgent_date.set_text("Mañana")
                else:
                    self.urgent_date.set_text(f"en {diff} días")
            else:
                self.urgent_title.set_text("Sin deadlines")
                self.urgent_date.set_text("pendientes")
        except:
            self.urgent_title.set_text("—")
            self.urgent_date.set_text("")
            
    def _create_pomodoro(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.add_css_class("glass-card")
        box.set_vexpand(True)
        
        header = Gtk.Label(label="Pomodoro")
        header.add_css_class("caption")
        header.add_css_class("dim-label")
        box.append(header)
        
        self.pomodoro_label = Gtk.Label(label="25:00")
        self.pomodoro_label.add_css_class("pomodoro-time")
        box.append(self.pomodoro_label)
        
        # Buttons
        btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        btns.set_halign(Gtk.Align.CENTER)
        
        self.pomo_play_btn = Gtk.Button()
        self.pomo_play_btn.set_icon_name("media-playback-start-symbolic")
        self.pomo_play_btn.add_css_class("circular")
        self.pomo_play_btn.add_css_class("translucent-btn")
        self.pomo_play_btn.connect("clicked", self._toggle_pomodoro)
        btns.append(self.pomo_play_btn)
        
        reset_btn = Gtk.Button()
        reset_btn.set_icon_name("view-refresh-symbolic")
        reset_btn.add_css_class("circular")
        reset_btn.add_css_class("flat")
        reset_btn.connect("clicked", self._reset_pomodoro)
        btns.append(reset_btn)
        
        box.append(btns)
        
        return box
        
    def _toggle_pomodoro(self, btn):
        self.pomodoro_running = not self.pomodoro_running
        if self.pomodoro_running:
            btn.set_icon_name("media-playback-pause-symbolic")
        else:
            btn.set_icon_name("media-playback-start-symbolic")
            
    def _reset_pomodoro(self, btn):
        self.pomodoro_running = False
        self.pomodoro_seconds = 25 * 60
        self.pomodoro_mode = "work"
        self.pomo_play_btn.set_icon_name("media-playback-start-symbolic")
        self._update_pomodoro_display()
        
    def _update_pomodoro_display(self):
        mins = self.pomodoro_seconds // 60
        secs = self.pomodoro_seconds % 60
        self.pomodoro_label.set_text(f"{mins:02d}:{secs:02d}")
        
    def _pomodoro_tick(self) -> bool:
        if self.pomodoro_running and self.pomodoro_seconds > 0:
            self.pomodoro_seconds -= 1
            self._update_pomodoro_display()
            
            if self.pomodoro_seconds == 0:
                self.pomodoro_running = False
                self.pomo_play_btn.set_icon_name("media-playback-start-symbolic")
                # Switch mode
                if self.pomodoro_mode == "work":
                    self.pomodoro_mode = "break"
                    self.pomodoro_seconds = 5 * 60
                else:
                    self.pomodoro_mode = "work"
                    self.pomodoro_seconds = 25 * 60
                self._update_pomodoro_display()
                
        return True
        
    def _create_progress_bar(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        label = Gtk.Label(label="Progreso hoy:")
        label.add_css_class("caption")
        label.add_css_class("dim-label")
        box.append(label)
        
        self.progress = Gtk.ProgressBar()
        self.progress.add_css_class("progress-bar")
        self.progress.set_hexpand(True)
        box.append(self.progress)
        
        self.progress_label = Gtk.Label()
        self.progress_label.add_css_class("caption")
        box.append(self.progress_label)
        
        self._update_progress()
        
        return box
        
    def _update_progress(self):
        try:
            tasks = task_manager.get_all_tasks()
            today = datetime.now().strftime('%Y-%m-%d')
            
            today_tasks = [t for t in tasks if t.get('deadline') == today]
            if today_tasks:
                completed = len([t for t in today_tasks if t.get('status') == 'completado'])
                total = len(today_tasks)
                fraction = completed / total if total > 0 else 0
                self.progress.set_fraction(fraction)
                self.progress_label.set_text(f"{completed}/{total}")
            else:
                self.progress.set_fraction(0)
                self.progress_label.set_text("0/0")
        except:
            self.progress.set_fraction(0)
            self.progress_label.set_text("—")
            
    def _show_quick_note(self, btn):
        dialog = Adw.MessageDialog(transient_for=self, heading="Nota rápida")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("save", "Guardar")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Title entry with Adw style
        title_group = Adw.PreferencesGroup()
        entry = Adw.EntryRow()
        entry.set_title("Título")
        title_group.add(entry)
        box.append(title_group)
        
        # Description label
        desc_label = Gtk.Label(label="Descripción")
        desc_label.set_halign(Gtk.Align.START)
        desc_label.add_css_class("heading")
        box.append(desc_label)
        
        # Styled text view
        text_frame = Gtk.Frame()
        text_frame.add_css_class("card")
        
        text_view = Gtk.TextView()
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        text_view.set_size_request(280, 100)
        text_view.set_top_margin(8)
        text_view.set_bottom_margin(8)
        text_view.set_left_margin(8)
        text_view.set_right_margin(8)
        
        # Placeholder
        buffer = text_view.get_buffer()
        buffer.set_text("Escribe tu nota aquí...")
        
        # Clear placeholder on focus
        def on_focus_in(controller):
            if buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True) == "Escribe tu nota aquí...":
                buffer.set_text("")
                
        focus_controller = Gtk.EventControllerFocus()
        focus_controller.connect("enter", on_focus_in)
        text_view.add_controller(focus_controller)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(text_view)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        text_frame.set_child(scroll)
        box.append(text_frame)
        
        dialog.set_extra_child(box)
        
        def on_response(d, response):
            if response == "save":
                title = entry.get_text()
                content = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
                if content == "Escribe tu nota aquí...":
                    content = ""
                if title:
                    try:
                        task_manager.add_quick_note(title, content)
                    except:
                        pass
                        
        dialog.connect("response", on_response)
        dialog.present()
            
    def _start_timers(self):
        self._update_time()
        GLib.timeout_add_seconds(1, self._update_time)
        GLib.timeout_add_seconds(1, self._pomodoro_tick)
        GLib.timeout_add_seconds(60, self._update_next_class_wrapper)
        # Auto-refresh data every 30 seconds to sync with main app changes
        GLib.timeout_add_seconds(30, self._refresh_all_data)

    def _refresh_all_data(self) -> bool:
        """Refresh all widget data from database"""
        try:
            self._update_stats_display()
            self._update_calendar()
            self._update_urgent()
            self._update_progress()
            self._update_next_class()
        except Exception as e:
            print(f"Widget refresh error: {e}")
        return True

    def _update_stats_display(self):
        """Update the stats row with fresh data"""
        stats = self._get_stats()
        # Find and update the value labels in stat boxes
        self._update_stat_value(self.pending_label, str(stats['pending']))
        self._update_stat_value(self.today_label, str(stats['today']))
        self._update_stat_value(self.overdue_label, str(stats['overdue']))
        self._update_stat_value(self.completed_label, str(stats['completed_today']))

    def _update_stat_value(self, stat_box, new_value):
        """Update the value label in a stat box"""
        child = stat_box.get_first_child()
        if child and isinstance(child, Gtk.Label):
            child.set_text(new_value)
        
    def _update_next_class_wrapper(self) -> bool:
        self._update_next_class()
        return True
        
    def _update_time(self) -> bool:
        now = datetime.now()
        days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        self.time_label.set_text(f"{days[now.weekday()]} {now.strftime('%d/%m %H:%M')}")
        return True
        
    def _open_main_app(self, btn):
        app_dir = Path(__file__).parent
        subprocess.Popen([sys.executable, "main_gtk.py"], cwd=str(app_dir))


def main():
    app = WidgetApp()
    app.run(None)


if __name__ == "__main__":
    main()
