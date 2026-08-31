"""
Main Window - GTK4 + Libadwaita

Layout nativo de Adwaita: NavigationSplitView con una ToolbarView (y su propia
HeaderBar) a cada lado. Es lo que usan Archivos, Ajustes o Correo, y es lo que
hace que en macOS los botones semaforo caigan dentro de una barra de titulo real
en vez de flotar sobre el sidebar.
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio
from pathlib import Path

# Import views
from .views.dashboard import DashboardView
from .views.tasks import TasksView
from .views.calendar import CalendarView
from .views.stats import StatsView

# Import widgets as views
from .widgets.kanban import KanbanBoard
from .widgets.pomodoro import PomodoroTimer
from .widgets.notes import QuickNotes
from .widgets.schedule import WeeklySchedule

# Import backend
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.core.task_manager import task_manager
from src.core.signals import signals
from src.gtk.widgets.common import bind_signals
from src.utils.system import IS_MAC

# (clave, etiqueta del sidebar, titulo de la vista, icono)
# El orden define los atajos Cmd/Ctrl+1..8 (ver NAV_KEYS en main_gtk.py).
NAV_ITEMS = [
    ("dashboard", "Dashboard",     "Dashboard",        "view-grid-symbolic"),
    ("tasks",     "Tareas",        "Tareas",           "checkbox-checked-symbolic"),
    ("kanban",    "Kanban",        "Kanban",           "view-dual-symbolic"),
    ("calendar",  "Calendario",    "Calendario",       "x-office-calendar-symbolic"),
    ("schedule",  "Horario",       "Horario Semanal",  "preferences-system-time-symbolic"),
    ("pomodoro",  "Pomodoro",      "Pomodoro",         "alarm-symbolic"),
    ("notes",     "Rough Notes",   "Rough Notes",      "text-editor-symbolic"),
    ("stats",     "Estadísticas",  "Estadísticas",     "unidex-stats-symbolic"),
]


class MainWindow(Adw.ApplicationWindow):
    """Ventana principal con sidebar de navegacion"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_title("UniDex")
        self.set_default_size(*self._saved_size())
        self.set_size_request(820, 560)
        self.add_css_class("main-window")

        self._setup_ui()
        self._connect_signals()
        self.connect("close-request", self._on_close_request)

    def _saved_size(self) -> tuple:
        """Restore the last window size, as native apps do"""
        try:
            width = int(task_manager.get_setting('window_width', 1100) or 1100)
            height = int(task_manager.get_setting('window_height', 700) or 700)
            return max(width, 900), max(height, 600)
        except Exception:
            return 1100, 700

    def _on_close_request(self, *_):
        """Remember window size before closing.

        get_width() devuelve 0 mientras la ventana no esta mapeada; guardar ese
        0 borraria el tamano bueno del usuario, asi que solo se persiste una
        medida real.
        """
        try:
            width, height = self.get_width(), self.get_height()
            if width > 0 and height > 0:
                task_manager.set_setting('window_width', width)
                task_manager.set_setting('window_height', height)
        except Exception:
            pass
        return False

    # ------------------------------------------------------------------ UI
    def _setup_ui(self):
        self._build_stack()

        self.content_page = Adw.NavigationPage(title="Dashboard",
                                               child=self._build_content())

        split = Adw.NavigationSplitView()
        split.set_min_sidebar_width(200)
        split.set_max_sidebar_width(240)
        split.set_sidebar(Adw.NavigationPage(title="UniDex",
                                             child=self._build_sidebar()))
        split.set_content(self.content_page)
        self.set_content(split)

    def _build_stack(self):
        """Una vista por cada entrada de NAV_ITEMS"""
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(120)
        self.stack.set_vexpand(True)
        self.stack.set_hexpand(True)

        self.dashboard_view = DashboardView()
        self.tasks_view = TasksView()
        self.kanban_view = KanbanBoard()
        self.calendar_view = CalendarView()
        self.schedule_view = WeeklySchedule()
        self.pomodoro_view = PomodoroTimer()
        self.notes_view = QuickNotes()
        self.stats_view = StatsView()

        self.views = {
            "dashboard": self.dashboard_view,
            "tasks": self.tasks_view,
            "kanban": self.kanban_view,
            "calendar": self.calendar_view,
            "schedule": self.schedule_view,
            "pomodoro": self.pomodoro_view,
            "notes": self.notes_view,
            "stats": self.stats_view,
        }
        for key, label, _title, _icon in NAV_ITEMS:
            self.stack.add_titled(self.views[key], key, label)

    def _build_sidebar(self) -> Adw.ToolbarView:
        """Sidebar nativo: ToolbarView + HeaderBar + ListBox .navigation-sidebar"""
        # ListBox de navegacion: seleccion, foco y teclado los da Adwaita.
        self.nav_list = Gtk.ListBox()
        self.nav_list.add_css_class("navigation-sidebar")
        self.nav_list.set_selection_mode(Gtk.SelectionMode.SINGLE)

        self.nav_rows = {}
        for key, label, _title, icon in NAV_ITEMS:
            row = Gtk.ListBoxRow()
            row.nav_key = key

            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            box.append(Gtk.Image.new_from_icon_name(icon))
            text = Gtk.Label(label=label, halign=Gtk.Align.START, hexpand=True)
            box.append(text)
            row.set_child(box)

            self.nav_rows[key] = row
            self.nav_list.append(row)

        self.current_nav_key = "dashboard"
        self.nav_list.select_row(self.nav_rows["dashboard"])
        self.nav_list.connect("row-selected", self._on_nav_row_selected)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(self.nav_list)

        # Configuracion al pie, separado de la navegacion
        settings_btn = Gtk.Button(margin_start=6, margin_end=6, margin_bottom=6)
        settings_btn.add_css_class("flat")
        settings_btn.add_css_class("sidebar-footer-button")
        settings_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        settings_content.append(Gtk.Image.new_from_icon_name("preferences-system-symbolic"))
        settings_content.append(Gtk.Label(label="Configuración", halign=Gtk.Align.START,
                                          hexpand=True))
        settings_btn.set_child(settings_content)
        settings_btn.set_tooltip_text("Configuración (⌘,)" if IS_MAC else "Configuración (Ctrl+,)")
        settings_btn.connect("clicked", self._on_settings_clicked)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        body.append(scroll)
        body.append(settings_btn)

        toolbar = Adw.ToolbarView()
        # La HeaderBar del sidebar es la que aloja los semaforos en macOS.
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="UniDex"))
        toolbar.add_top_bar(header)
        toolbar.set_content(body)
        return toolbar

    def _build_content(self) -> Adw.ToolbarView:
        """Area de contenido: HeaderBar + Stack de vistas"""
        header = Adw.HeaderBar()

        add_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_btn.set_tooltip_text("Nueva Tarea (⌘N)" if IS_MAC else "Nueva Tarea (Ctrl+N)")
        add_btn.connect("clicked", lambda _: self.show_add_task_dialog())
        header.pack_start(add_btn)

        menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu_btn.set_tooltip_text("Menú principal")
        menu_btn.set_menu_model(self._build_menu())
        header.pack_end(menu_btn)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(header)
        toolbar.set_content(self.stack)
        return toolbar

    def _build_menu(self) -> Gio.Menu:
        menu = Gio.Menu()

        actions = Gio.Menu()
        actions.append("Nueva Tarea", "app.new-task")
        actions.append("Configuración", "app.settings")
        menu.append_section(None, actions)

        data = Gio.Menu()
        data.append("Crear Backup", "app.backup")
        data.append("Exportar…", "app.export")
        data.append("Importar…", "app.import")
        menu.append_section(None, data)

        about = Gio.Menu()
        about.append("Acerca de UniDex", "app.about")
        menu.append_section(None, about)
        return menu

    # ---------------------------------------------------------- navegacion
    def _on_nav_row_selected(self, _list, row):
        if row is None:
            return
        key = row.nav_key
        self.current_nav_key = key
        self.stack.set_visible_child_name(key)
        title = next(t for k, _l, t, _i in NAV_ITEMS if k == key)
        self.content_page.set_title(title)

    def navigate_to(self, key: str):
        """Switch to a view by key (used by the ⌘1-8 shortcuts)"""
        if key in self.nav_rows:
            self.nav_list.select_row(self.nav_rows[key])

    def _on_settings_clicked(self, button):
        """Open settings dialog"""
        from .dialogs.settings import SettingsDialog
        dialog = SettingsDialog(parent=self)
        dialog.present()

    def _connect_signals(self):
        """Un cambio en una tarea refresca las vistas que no se auto-actualizan.

        Tareas y Kanban ya escuchan signals por su cuenta; el resto (dashboard,
        calendario, horario, estadisticas) se quedaba desincronizado.
        """
        # ponytail: refresca todas las vistas en cada cambio; si con muchas
        # tareas se nota lento, refrescar solo la vista visible.
        refresh = lambda *_: self.refresh_views()
        bind_signals(self, [(signal, refresh) for signal in (
            signals.task_added, signals.task_updated,
            signals.task_deleted, signals.tasks_reloaded)])

    def show_add_task_dialog(self):
        """Show add task dialog"""
        from .dialogs.add_task import AddTaskDialog
        dialog = AddTaskDialog(parent=self)
        dialog.present()

    def refresh_views(self):
        """Refresh every view that knows how to refresh itself"""
        for view in self.views.values():
            refresh = getattr(view, "refresh", None)
            if callable(refresh):
                try:
                    refresh()
                except Exception as error:
                    print(f"Refresh error in {type(view).__name__}: {error}")
