#!/usr/bin/env python3
"""
UnixProductivityApp - GTK4 + Libadwaita Version
Main entry point with translucent window support
"""
import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib, Gdk
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gtk.window import MainWindow


class UnixProductivityApp(Adw.Application):
    """Main GTK4 Application"""
    
    def __init__(self):
        super().__init__(
            application_id="com.github.jjjulianleon.unixproductivity",
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.window = None
        
    def do_startup(self):
        """Load CSS and setup application"""
        Adw.Application.do_startup(self)
        
        # Load custom CSS
        css_provider = Gtk.CssProvider()
        css_path = Path(__file__).parent / "src" / "gtk" / "styles" / "style.css"
        
        if css_path.exists():
            css_provider.load_from_path(str(css_path))
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        
        # Load saved font setting
        self._apply_saved_font()
        
        # Setup actions
        self._setup_actions()
        
    def _apply_saved_font(self):
        """Apply saved font from settings on startup"""
        try:
            from src.core.task_manager import task_manager
            fonts = [
                "",  # System default
                "'Source Code Pro'",
                "'Inter'",
                "'Roboto'",
                "'Ubuntu'",
                "'Fira Code'"
            ]
            saved_font_idx = task_manager.get_setting('app_font', 0)
            if saved_font_idx and saved_font_idx > 0 and saved_font_idx < len(fonts):
                font_family = fonts[saved_font_idx]
                css = Gtk.CssProvider()
                css.load_from_data(f"* {{ font-family: {font_family}, sans-serif; }}".encode())
                Gtk.StyleContext.add_provider_for_display(
                    Gdk.Display.get_default(),
                    css,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
        except Exception as e:
            print(f"Font loading error: {e}")
        
    def _setup_actions(self):
        """Setup application actions"""
        # Quit action
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Ctrl>q"])
        
        # New task action
        new_task_action = Gio.SimpleAction.new("new-task", None)
        new_task_action.connect("activate", self._on_new_task)
        self.add_action(new_task_action)
        self.set_accels_for_action("app.new-task", ["<Ctrl>n"])
        
    def do_activate(self):
        """Create and show main window"""
        if not self.window:
            self.window = MainWindow(application=self)
        self.window.present()
        
    def _on_new_task(self, action, param):
        """Handle new task action"""
        if self.window:
            self.window.show_add_task_dialog()


def main():
    """Main entry point"""
    app = UnixProductivityApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
