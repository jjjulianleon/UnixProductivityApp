"""
Main Application Window - Unix Productivity App
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QSystemTrayIcon,
    QMenu, QSizePolicy, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction, QShortcut, QKeySequence, QPixmap

from src.utils.styles import COLORS, FONT_FAMILY, get_button_style, get_main_window_style, get_menu_style
from src.utils.constants import APP_NAME, MAIN_APP_MIN_WIDTH, MAIN_APP_MIN_HEIGHT
from src.core.task_manager import task_manager
from src.core.notifications import notification_manager
from src.core.signals import SignalHub
from src.core.database import db
from src.ui.views.dashboard import DashboardView
from src.ui.views.tasks_view import TasksView
from src.ui.views.calendar_view import CalendarView
from src.ui.views.statistics_view import StatisticsView
from src.ui.widgets.quick_notes import QuickNotesWidget


# Get assets directory
ASSETS_DIR = Path(__file__).parent / "assets"


class SidebarButton(QPushButton):
    """Custom sidebar navigation button"""
    
    def __init__(self, text: str, icon_name: str = None, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFont(QFont(FONT_FAMILY, 11))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        self._update_style()
    
    def _update_style(self):
        checked = self.isChecked()
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {'rgba(66, 133, 244, 0.15)' if checked else 'transparent'};
                color: rgb({'66, 133, 244' if checked else COLORS['text_secondary']});
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 16px;
            }}
            QPushButton:hover {{
                background-color: {'rgba(66, 133, 244, 0.2)' if checked else 'rgba(255, 255, 255, 0.05)'};
            }}
        """)
    
    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._update_style()


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(MAIN_APP_MIN_WIDTH, MAIN_APP_MIN_HEIGHT)
        self.setStyleSheet(get_main_window_style())
        
        # Get signal hub
        self.signals = SignalHub.get_instance()
        
        # Initialize components
        self._setup_app_icon()
        self._setup_tray_icon()
        self._setup_ui()
        self._setup_shortcuts()
        self._connect_signals()
        
        # Initialize notification manager
        notification_manager.start()
    
    def _setup_app_icon(self):
        """Setup application icon"""
        icon_path = ASSETS_DIR / "app_icon.svg"
        if icon_path.exists():
            self.app_icon = QIcon(str(icon_path))
            self.setWindowIcon(self.app_icon)
        else:
            self.app_icon = QIcon.fromTheme("appointment-soon")
    
    def _setup_tray_icon(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.app_icon)
        self.tray_icon.setToolTip(APP_NAME)
        
        tray_menu = QMenu()
        tray_menu.setStyleSheet(get_menu_style())
        
        # Show/Hide
        show_action = QAction("Mostrar", self)
        show_action.triggered.connect(self._show_window)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Ocultar", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        # Quick actions
        add_task_action = QAction("Nueva Tarea", self)
        add_task_action.triggered.connect(self._quick_add_task)
        tray_menu.addAction(add_task_action)
        
        tray_menu.addSeparator()
        
        # Backup/Export submenu
        data_menu = tray_menu.addMenu("Datos")
        data_menu.setStyleSheet(get_menu_style())
        
        backup_action = QAction("Crear Backup", self)
        backup_action.triggered.connect(self._create_backup)
        data_menu.addAction(backup_action)
        
        export_action = QAction("Exportar Tareas (JSON)", self)
        export_action.triggered.connect(self._export_tasks_json)
        data_menu.addAction(export_action)
        
        export_csv_action = QAction("Exportar Tareas (CSV)", self)
        export_csv_action.triggered.connect(self._export_tasks_csv)
        data_menu.addAction(export_csv_action)
        
        import_action = QAction("Importar Tareas", self)
        import_action.triggered.connect(self._import_tasks)
        data_menu.addAction(import_action)
        
        restore_action = QAction("Restaurar Backup", self)
        restore_action.triggered.connect(self._restore_backup)
        data_menu.addAction(restore_action)
        
        tray_menu.addSeparator()
        
        # Quit
        quit_action = QAction("Salir", self)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()
    
    def _setup_ui(self):
        """Setup the main UI"""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(25, 25, 30, 250);
                border-right: 1px solid rgba(255, 255, 255, 0.05);
            }}
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(8)
        
        # App title with icon
        title_container = QWidget()
        title_container.setStyleSheet("background: transparent;")
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel()
        icon_pixmap = self.app_icon.pixmap(24, 24)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setStyleSheet("background: transparent;")
        title_layout.addWidget(icon_label)
        
        # Title
        app_title = QLabel(APP_NAME)
        app_title.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        app_title.setStyleSheet(f"color: rgb({COLORS['primary']}); background: transparent;")
        title_layout.addWidget(app_title)
        title_layout.addStretch()
        
        sidebar_layout.addWidget(title_container)
        sidebar_layout.addSpacing(20)
        
        # Navigation buttons (no emojis)
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "Dashboard"),
            ("tasks", "Tareas"),
            ("calendar", "Calendario"),
            ("notes", "Notas"),
            ("stats", "Estadisticas"),
        ]
        
        for key, text in nav_items:
            btn = SidebarButton(text)
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
            self.nav_buttons[key] = btn
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()
        
        # Data operations button
        data_btn = SidebarButton("Backup/Export")
        data_btn.clicked.connect(self._show_data_menu)
        sidebar_layout.addWidget(data_btn)
        
        # Settings button at bottom
        settings_btn = SidebarButton("Configuracion")
        settings_btn.clicked.connect(self._open_settings)
        sidebar_layout.addWidget(settings_btn)
        
        main_layout.addWidget(sidebar)
        
        # Content area
        content_area = QWidget()
        content_area.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(30, 30, 35, 255);
            }}
        """)
        
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for views
        self.stack = QStackedWidget()
        
        # Add views
        self.dashboard_view = DashboardView()
        self.dashboard_view.task_clicked.connect(self._on_task_clicked)
        self.stack.addWidget(self.dashboard_view)
        
        self.tasks_view = TasksView()
        self.stack.addWidget(self.tasks_view)
        
        self.calendar_view = CalendarView()
        self.stack.addWidget(self.calendar_view)
        
        self.notes_view = QuickNotesWidget()
        self.stack.addWidget(self.notes_view)
        
        self.stats_view = StatisticsView()
        self.stack.addWidget(self.stats_view)
        
        content_layout.addWidget(self.stack)
        main_layout.addWidget(content_area, 1)
        
        # Set initial view
        self._navigate("dashboard")
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        shortcuts = [
            ("Ctrl+1", lambda: self._navigate("dashboard")),
            ("Ctrl+2", lambda: self._navigate("tasks")),
            ("Ctrl+3", lambda: self._navigate("calendar")),
            ("Ctrl+4", lambda: self._navigate("notes")),
            ("Ctrl+5", lambda: self._navigate("stats")),
            ("Ctrl+N", self._quick_add_task),
            ("Ctrl+F", self._focus_search),
            ("Ctrl+B", self._create_backup),
            ("Ctrl+E", self._export_tasks_json),
            ("Ctrl+I", self._import_tasks),
            ("F5", self._refresh_current_view),
        ]
        
        for key, callback in shortcuts:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)
    
    def _connect_signals(self):
        """Connect to SignalHub signals"""
        # Task signals
        self.signals.task_added.connect(self._on_data_changed)
        self.signals.task_updated.connect(self._on_data_changed)
        self.signals.task_deleted.connect(self._on_data_changed)
        
        # Note signals
        self.signals.note_added.connect(self._on_data_changed)
        self.signals.note_updated.connect(self._on_data_changed)
        self.signals.note_deleted.connect(self._on_data_changed)
        
        # Reminder signal
        self.signals.reminder_due.connect(self._on_reminder)
        
        # Backup signal
        self.signals.backup_completed.connect(self._on_backup_completed)
    
    def _navigate(self, key: str):
        """Navigate to a view"""
        views = {
            "dashboard": 0,
            "tasks": 1,
            "calendar": 2,
            "notes": 3,
            "stats": 4,
        }
        
        if key in views:
            self.stack.setCurrentIndex(views[key])
            
            # Update button states
            for btn_key, btn in self.nav_buttons.items():
                btn.setChecked(btn_key == key)
    
    def _on_task_clicked(self, task: dict):
        """Handle task click from any view"""
        from src.ui.dialogs.task_dialogs import TaskDetailDialog
        dialog = TaskDetailDialog(task, self)
        dialog.task_updated.connect(self._on_task_updated)
        dialog.task_deleted.connect(self._on_task_deleted)
        dialog.exec()
    
    def _on_task_updated(self, task: dict):
        """Handle task update"""
        task_id = task.get('id')
        if task_id:
            task_manager.update_task(task_id, **task)
    
    def _on_task_deleted(self, task_id: int):
        """Handle task deletion"""
        task_manager.delete_task(task_id)
    
    def _on_data_changed(self, *args):
        """Handle data change - refresh views"""
        self._refresh_current_view()
    
    def _on_reminder(self, reminder: dict):
        """Handle reminder due notification"""
        self.tray_icon.showMessage(
            "Recordatorio",
            reminder.get('message', 'Tienes un recordatorio pendiente'),
            QSystemTrayIcon.MessageIcon.Information,
            10000
        )
    
    def _on_backup_completed(self, path: str):
        """Handle backup completion"""
        self.tray_icon.showMessage(
            "Backup Completado",
            f"Backup guardado exitosamente",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
    
    def _quick_add_task(self):
        """Quick add task shortcut"""
        from src.ui.dialogs.task_dialogs import AddTaskDialog
        dialog = AddTaskDialog(parent=self)
        dialog.task_created.connect(self._create_task)
        dialog.exec()
    
    def _create_task(self, task: dict):
        """Create a new task"""
        task_manager.add_task(
            title=task['title'],
            category=task['category'],
            description=task.get('description', ''),
            status=task.get('status', 'pendiente'),
            priority=task.get('priority', 'media'),
            deadline=task.get('deadline'),
            tags=task.get('tags', [])
        )
    
    def _focus_search(self):
        """Focus on search input"""
        self._navigate("tasks")
        if hasattr(self.tasks_view, 'search_input'):
            self.tasks_view.search_input.setFocus()
    
    def _refresh_current_view(self):
        """Refresh current view"""
        current = self.stack.currentWidget()
        if hasattr(current, 'refresh'):
            current.refresh()
    
    def _show_data_menu(self):
        """Show data operations menu"""
        menu = QMenu(self)
        
        backup_action = menu.addAction("Crear Backup")
        backup_action.triggered.connect(self._create_backup)
        
        menu.addSeparator()
        
        export_json = menu.addAction("Exportar a JSON")
        export_json.triggered.connect(self._export_tasks_json)
        
        export_csv = menu.addAction("Exportar a CSV")
        export_csv.triggered.connect(self._export_tasks_csv)
        
        menu.addSeparator()
        
        import_action = menu.addAction("Importar desde JSON")
        import_action.triggered.connect(self._import_tasks)
        
        restore_action = menu.addAction("Restaurar desde Backup")
        restore_action.triggered.connect(self._restore_backup)
        
        # Show menu at cursor
        menu.exec(self.cursor().pos())
    
    def _create_backup(self):
        """Create database backup"""
        try:
            backup_path = task_manager.create_backup()
            if backup_path:
                QMessageBox.information(
                    self,
                    "Backup Creado",
                    f"Backup guardado en:\n{backup_path}"
                )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Error al crear backup: {e}"
            )
    
    def _export_tasks_json(self):
        """Export tasks to JSON"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Tareas",
            str(Path.home() / "tasks_export.json"),
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                task_manager.export_to_json(file_path)
                QMessageBox.information(
                    self,
                    "Exportacion Exitosa",
                    f"Tareas exportadas a:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Error al exportar: {e}"
                )
    
    def _export_tasks_csv(self):
        """Export tasks to CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Tareas",
            str(Path.home() / "tasks_export.csv"),
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                db.export_tasks_to_csv(file_path)
                QMessageBox.information(
                    self,
                    "Exportacion Exitosa",
                    f"Tareas exportadas a:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Error al exportar: {e}"
                )
    
    def _import_tasks(self):
        """Import tasks from JSON"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar Tareas",
            str(Path.home()),
            "JSON Files (*.json)"
        )
        
        if file_path:
            reply = QMessageBox.question(
                self,
                "Confirmar Importacion",
                "Deseas agregar las tareas importadas a las existentes?\n\n"
                "Si: Agregar a las existentes\n"
                "No: Reemplazar todas las tareas",
                QMessageBox.StandardButton.Yes | 
                QMessageBox.StandardButton.No |
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                return
            
            merge = reply == QMessageBox.StandardButton.Yes
            
            try:
                count = task_manager.import_from_json(file_path, merge=merge)
                QMessageBox.information(
                    self,
                    "Importacion Exitosa",
                    f"Se importaron {count} tareas"
                )
                self._refresh_current_view()
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Error al importar: {e}"
                )
    
    def _restore_backup(self):
        """Restore from backup"""
        from src.utils.constants import DATA_DIR
        backup_dir = DATA_DIR / "backups"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Restaurar Backup",
            str(backup_dir) if backup_dir.exists() else str(Path.home()),
            "SQLite Database (*.db)"
        )
        
        if file_path:
            reply = QMessageBox.warning(
                self,
                "Confirmar Restauracion",
                "ADVERTENCIA: Esto reemplazara todos los datos actuales.\n\n"
                "Deseas continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    task_manager.restore_from_backup(file_path)
                    QMessageBox.information(
                        self,
                        "Restauracion Exitosa",
                        "Datos restaurados correctamente"
                    )
                    self._refresh_current_view()
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"Error al restaurar: {e}"
                    )
    
    def _open_settings(self):
        """Open settings dialog"""
        from src.ui.dialogs.settings_dialog import SettingsDialog
        try:
            dialog = SettingsDialog(self)
            dialog.settings_changed.connect(self._on_settings_changed)
            dialog.exec()
        except ImportError:
            QMessageBox.information(
                self,
                "Configuracion",
                "El dialogo de configuracion estara disponible pronto."
            )
    
    def _on_settings_changed(self, settings: dict):
        """Handle settings changes"""
        # Reload pomodoro settings
        if hasattr(self, 'main_pomodoro'):
            self.main_pomodoro.reload_settings()
        # Reload pomodoro in calendar view if exists
        if hasattr(self, 'calendar_view') and hasattr(self.calendar_view, 'pomodoro'):
            self.calendar_view.pomodoro.reload_settings()
    
    def _show_window(self):
        """Show and activate window"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def _on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click - toggle visibility
            if self.isVisible():
                self.hide()
            else:
                self._show_window()
    
    def closeEvent(self, event):
        """Handle window close - minimize to tray instead"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            APP_NAME,
            "La aplicacion sigue ejecutandose en segundo plano",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
    
    def _quit_app(self):
        """Actually quit the application"""
        # Sync to iCloud before quitting
        try:
            from src.core.task_manager import task_manager
            result = task_manager.sync_to_icloud()
            if result.get('created', 0) > 0:
                print(f"☁️ Final iCloud sync: {result['created']} events synced")
        except Exception as e:
            print(f"Final iCloud sync error: {e}")
        
        notification_manager.stop()
        QApplication.quit()


def main():
    """Main entry point"""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    
    # Set app icon
    icon_path = ASSETS_DIR / "app_icon.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Prevent app from closing when last window is closed (for tray)
    app.setQuitOnLastWindowClosed(False)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
