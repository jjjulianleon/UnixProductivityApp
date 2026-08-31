#!/usr/bin/env python3
"""
UniDex - GTK4 + Libadwaita Version
Main entry point with translucent window support
"""
import sys
import gi
from pathlib import Path

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib, Gdk

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gtk import init_theme
from src.gtk.window import MainWindow
from src.utils.system import IS_MAC, notify

# Vistas alcanzables con ⌘1-⌘8 (Ctrl+1-8 en Linux)
NAV_KEYS = ["dashboard", "tasks", "kanban", "calendar",
            "schedule", "pomodoro", "notes", "stats"]


def accel(key: str) -> list:
    """
    Acelerador para la plataforma actual.

    GTK4 define <Primary> como Control en todos los sistemas, asi que en macOS
    hay que pedir <Meta> explicitamente para obtener la tecla Command.
    """
    return [f"<Meta>{key}", f"<Control>{key}"] if IS_MAC else [f"<Control>{key}"]


class UniDexApp(Adw.Application):
    """Main GTK4 Application"""

    def __init__(self):
        super().__init__(
            application_id="com.github.jjjulianleon.unidex",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.window = None
        self.auto_sync = None
        self.notification_manager = None

    def do_startup(self):
        """Load CSS and setup application"""
        Adw.Application.do_startup(self)
        init_theme()
        self._setup_actions()

    def _setup_actions(self):
        """Setup application actions and their keyboard shortcuts"""
        simple_actions = {
            "quit": lambda *_: self.quit(),
            "close-window": lambda *_: self.window and self.window.close(),
            "new-task": self._on_new_task,
            "settings": self._on_settings,
            "backup": self._on_backup,
            "export": self._on_export,
            "import": self._on_import,
            "about": self._on_about,
        }
        for name, callback in simple_actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)

        self.set_accels_for_action("app.quit", accel("q"))
        self.set_accels_for_action("app.close-window", accel("w"))
        self.set_accels_for_action("app.new-task", accel("n"))
        self.set_accels_for_action("app.settings", accel("comma"))

        # Navegacion por seccion: ⌘1 … ⌘8
        nav_action = Gio.SimpleAction.new("nav", GLib.VariantType.new("s"))
        nav_action.connect("activate", self._on_nav)
        self.add_action(nav_action)
        for index, key in enumerate(NAV_KEYS, start=1):
            self.set_accels_for_action(f"app.nav::{key}", accel(str(index)))

    def do_activate(self):
        """Create and show main window"""
        if not self.window:
            self.window = MainWindow(application=self)

        # Start auto-sync for Brightspace/Teams
        self._start_auto_sync()

        # Start notification manager for deadline reminders
        self._start_notifications()

        self.window.present()

    def _start_auto_sync(self):
        """Start automatic calendar synchronization"""
        try:
            from src.core.auto_sync import auto_sync

            self.auto_sync = auto_sync

            # Add callback to refresh views after sync
            def on_sync_complete(result):
                # Schedule UI update on main thread
                GLib.idle_add(self._on_sync_complete, result)

            self.auto_sync.add_callback(on_sync_complete)
            self.auto_sync.start_background_sync()
            print("Auto-sync started for Brightspace D2L")
        except Exception as e:
            print(f"Auto-sync init error: {e}")

    def _start_notifications(self):
        """Start notification manager for deadline reminders"""
        try:
            from src.core.notifications import notification_manager

            self.notification_manager = notification_manager
            self.notification_manager.start()
            print("Notification manager started (deadline reminders at 3d, 1d, same day)")
        except Exception as e:
            print(f"Notification manager init error: {e}")

    def _on_sync_complete(self, result):
        """Handle sync completion - refresh UI"""
        try:
            if self.window:
                self.window.refresh_views()

            imported = result.get('brightspace', {}).get('imported', 0)
            if imported > 0:
                print(f"Synced {imported} new deadlines from Brightspace")
        except Exception as e:
            print(f"Sync UI update error: {e}")
        return False  # Don't repeat

    # ------------------------------------------------------------- acciones
    def _on_new_task(self, action, param):
        """Handle new task action"""
        if self.window:
            self.window.show_add_task_dialog()

    def _on_settings(self, action, param):
        if self.window:
            self.window._on_settings_clicked(None)

    def _on_nav(self, action, param):
        if self.window:
            self.window.navigate_to(param.get_string())

    def _on_backup(self, action, param):
        from src.core.task_manager import task_manager
        try:
            path = task_manager.create_backup()
            notify("Backup creado", str(path), app_name="UniDex")
        except Exception as e:
            notify("Error al crear backup", str(e), "critical", app_name="UniDex")

    def _on_export(self, action, param):
        """Export the database to JSON through a native save dialog"""
        from src.core.task_manager import task_manager

        dialog = Gtk.FileDialog(initial_name="unidex-export.json")

        def done(dlg, result):
            try:
                gfile = dlg.save_finish(result)
            except GLib.Error:
                return  # cancelado
            try:
                task_manager.export_to_json(gfile.get_path())
                notify("Exportacion completada", gfile.get_path(), app_name="UniDex")
            except Exception as e:
                notify("Error al exportar", str(e), "critical", app_name="UniDex")

        dialog.save(self.window, None, done)

    def _on_import(self, action, param):
        """Import a JSON export chosen by the user"""
        from src.core.task_manager import task_manager

        dialog = Gtk.FileDialog(title="Importar respaldo JSON")

        def done(dlg, result):
            try:
                gfile = dlg.open_finish(result)
            except GLib.Error:
                return  # cancelado
            try:
                stats = task_manager.import_from_json(gfile.get_path())
                summary = ", ".join(f"{v} {k}" for k, v in stats.items())
                if self.window:
                    self.window.refresh_views()
                notify("Importacion completada", summary or "Sin cambios", app_name="UniDex")
            except Exception as e:
                notify("Error al importar", str(e), "critical", app_name="UniDex")

        dialog.open(self.window, None, done)

    def _on_about(self, action, param):
        about = Adw.AboutDialog(
            application_name="UniDex",
            application_icon="appointment-soon-symbolic",
            version="1.0.0",
            developer_name="Julian Leon",
            comments="Tareas, calendario, Kanban, Pomodoro y notas, "
                     "sincronizados con Obsidian, Brightspace e iCloud.",
            license_type=Gtk.License.MIT_X11,
        )
        about.present(self.window)


def main():
    """Main entry point"""
    # Nombre visible del proceso (menu de aplicacion en macOS, .desktop en Linux)
    GLib.set_application_name("UniDex")
    GLib.set_prgname("UniDex")

    app = UniDexApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
