"""
Main Application Window
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QSystemTrayIcon,
    QMenu, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction, QShortcut, QKeySequence

from src.utils.styles import COLORS, FONT_FAMILY, get_button_style, get_main_window_style
from src.utils.constants import APP_NAME, MAIN_APP_MIN_WIDTH, MAIN_APP_MIN_HEIGHT
from src.core.task_manager import task_manager
from src.core.notifications import notification_manager
from src.core.database import db
from src.ui.views.dashboard import DashboardView
from src.ui.views.tasks_view import TasksView
from src.ui.views.calendar_view import CalendarView
from src.ui.views.statistics_view import StatisticsView
from src.ui.widgets.quick_notes import QuickNotesWidget


class SidebarButton(QPushButton):
    """Custom sidebar navigation button"""
    
    def __init__(self, text: str, icon: str, parent=None):
        super().__init__(f"{icon}  {text}", parent)
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
        
        # Initialize components
        self._setup_tray_icon()
        self._setup_ui()
        self._setup_shortcuts()
        
        # Notifications - simplified (no signals)
    
    def _setup_tray_icon(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        # Use a default icon - in production you'd use a custom icon
        self.tray_icon.setIcon(QIcon.fromTheme("appointment-soon"))
        
        tray_menu = QMenu()
        
        show_action = QAction("Mostrar", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Salir", self)
        quit_action.triggered.connect(QApplication.quit)
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
        
        # App title
        app_title = QLabel(f"🚀 {APP_NAME}")
        app_title.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        app_title.setStyleSheet(f"color: rgb({COLORS['primary']}); background: transparent;")
        sidebar_layout.addWidget(app_title)
        
        sidebar_layout.addSpacing(20)
        
        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "🏠", "Dashboard"),
            ("tasks", "📋", "Tareas"),
            ("calendar", "📅", "Calendario"),
            ("notes", "📝", "Notas"),
            ("stats", "📈", "Estadísticas"),
        ]
        
        for key, icon, text in nav_items:
            btn = SidebarButton(text, icon)
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
            self.nav_buttons[key] = btn
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()
        
        # Settings button at bottom
        settings_btn = SidebarButton("Configuración", "⚙️")
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
            ("F5", self._refresh_current_view),
        ]
        
        for key, callback in shortcuts:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)
    
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
            task_manager.update_task(task_id, status=task.get('status'))
    
    def _on_task_deleted(self, task_id: int):
        """Handle task deletion"""
        task_manager.delete_task(task_id)
    
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
            deadline=task.get('deadline')
        )
    
    def _focus_search(self):
        """Focus on search input"""
        self._navigate("tasks")
        self.tasks_view.search_input.setFocus()
    
    def _refresh_current_view(self):
        """Refresh current view"""
        current = self.stack.currentWidget()
        if hasattr(current, 'refresh'):
            current.refresh()
    
    def _open_settings(self):
        """Open settings dialog"""
        # TODO: Implement settings dialog
        pass
    
    def _on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()
    
    def _on_notification(self, title: str, message: str):
        """Handle notification from notification manager"""
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)
    
    def closeEvent(self, event):
        """Handle window close - minimize to tray instead"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            APP_NAME,
            "La aplicación sigue ejecutándose en segundo plano",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )


def main():
    """Main entry point"""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    
    # Prevent app from closing when last window is closed (for tray)
    app.setQuitOnLastWindowClosed(False)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
