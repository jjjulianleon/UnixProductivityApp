"""
Statistics View - GTK4
Show productivity statistics and charts
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager
from src.gtk.widgets.common import empty_state

# Alto util del grafico semanal, en px. MIN_BAR deja visible el dia sin actividad.
CHART_HEIGHT = 140
MIN_BAR = 6


class StatsView(Gtk.Box):
    """Statistics view"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_spacing(20)
        
        self._setup_ui()
        self.refresh()
        
    def _setup_ui(self):
        """Setup stats UI"""
        # Stats grid
        stats_grid = Gtk.Grid()
        stats_grid.set_column_spacing(16)
        stats_grid.set_row_spacing(16)
        stats_grid.set_column_homogeneous(True)
        
        # Weekly stats card
        self.weekly_card = self._create_stats_card("Esta Semana")
        stats_grid.attach(self.weekly_card, 0, 0, 1, 1)
        
        # Monthly stats card  
        self.monthly_card = self._create_stats_card("Este Mes")
        stats_grid.attach(self.monthly_card, 1, 0, 1, 1)
        
        # All time card
        self.alltime_card = self._create_stats_card("Total")
        stats_grid.attach(self.alltime_card, 2, 0, 1, 1)
        
        self.append(stats_grid)
        
        # Productivity chart placeholder
        chart_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        chart_card.add_css_class("glass-card")
        chart_card.set_valign(Gtk.Align.START)
        
        chart_title = Gtk.Label(label="Actividad Semanal")
        chart_title.add_css_class("title-4")
        chart_title.set_halign(Gtk.Align.START)
        chart_card.append(chart_title)
        
        # Simple bar chart representation
        self.chart_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.chart_box.set_valign(Gtk.Align.END)
        self.chart_box.set_size_request(-1, CHART_HEIGHT + 24)
        self.chart_box.set_homogeneous(True)
        chart_card.append(self.chart_box)
        
        self.append(chart_card)
        
    def _create_stats_card(self, title: str) -> Gtk.Box:
        """Create a stats summary card"""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.add_css_class("glass-card")
        
        title_label = Gtk.Label(label=title)
        title_label.add_css_class("title-4")
        title_label.set_halign(Gtk.Align.START)
        card.append(title_label)
        
        # Stats rows
        stats_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        completed_row = self._create_stat_row("Completadas", "0")
        stats_box.append(completed_row)
        
        pomodoros_row = self._create_stat_row("Pomodoros", "0")
        stats_box.append(pomodoros_row)
        
        card.append(stats_box)
        return card
        
    def _create_stat_row(self, label: str, value: str) -> Gtk.Box:
        """Create a stat row"""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        label_widget = Gtk.Label(label=label)
        label_widget.add_css_class("dim-label")
        label_widget.set_halign(Gtk.Align.START)
        label_widget.set_hexpand(True)
        row.append(label_widget)
        
        value_widget = Gtk.Label(label=value)
        value_widget.add_css_class("title-3")
        row.append(value_widget)
        
        return row
        
    def refresh(self):
        """Refresh statistics"""
        try:
            # Get weekly stats
            weekly = task_manager.get_weekly_stats()
            self._update_card(self.weekly_card, weekly)
            
            # Get monthly stats
            monthly = task_manager.get_monthly_stats()
            self._update_card(self.monthly_card, monthly)

            # Total historico (la tarjeta existia pero se quedaba en cero)
            self._update_card(self.alltime_card, task_manager.get_alltime_stats())
            
            # Update chart
            self._update_chart()
            
        except Exception as e:
            print(f"Stats refresh error: {e}")
            
    def _update_card(self, card: Gtk.Box, stats: dict):
        """Update stats card values"""
        # Find stats box (second child)
        child = card.get_first_child()
        if child:
            child = child.get_next_sibling()
            if child:
                # Update completed row
                completed_row = child.get_first_child()
                if completed_row:
                    value_label = completed_row.get_last_child()
                    if value_label:
                        value_label.set_text(str(stats.get('tasks_completed', 0)))
                        
                # Update pomodoros row
                pomodoros_row = completed_row.get_next_sibling() if completed_row else None
                if pomodoros_row:
                    value_label = pomodoros_row.get_last_child()
                    if value_label:
                        value_label.set_text(str(stats.get('pomodoros_completed', 0)))
                        
    def _update_chart(self):
        """Update weekly activity chart"""
        # Clear existing
        while True:
            child = self.chart_box.get_first_child()
            if child:
                self.chart_box.remove(child)
            else:
                break
                
        days = ["L", "M", "X", "J", "V", "S", "D"]

        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        counts = []
        for i in range(7):
            try:
                counts.append(task_manager.get_daily_stats(
                    (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
                ).get('tasks_completed', 0))
            except Exception:
                counts.append(0)
        if not any(counts):
            # Siete barras minimas al fondo de un recuadro vacio parecen un
            # grafico roto; mejor decir que aun no hay nada.
            self.chart_box.append(
                empty_state("unidex-stats-symbolic", "Sin actividad esta semana",
                            "Las tareas que completes apareceran aqui"))
            return

        peak = max(counts)

        for i, day_label in enumerate(days):
            day_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            day_box.set_valign(Gtk.Align.END)
            
            # Lunes..Domingo de ESTA semana. El calculo anterior, con
            # (weekday - i) % 7, devolvia dias de la semana pasada.
            day_date = week_start + timedelta(days=i)

            completed = counts[i]

            # Escala relativa al mejor dia, para que el grafico se lea siempre
            height = MIN_BAR + round((CHART_HEIGHT - MIN_BAR) * completed / peak)

            bar = Gtk.Box()
            bar.set_size_request(30, height)
            bar.add_css_class("chart-bar")
            bar.set_valign(Gtk.Align.END)
            bar.set_tooltip_text(f"{day_date.strftime('%d/%m')}: {completed} completadas")
            day_box.append(bar)
            
            # Label
            label = Gtk.Label(label=day_label)
            label.add_css_class("caption")
            day_box.append(label)
            
            self.chart_box.append(day_box)
