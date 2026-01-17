"""
Settings Dialog - GTK4
Application preferences
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager


class SettingsDialog(Adw.PreferencesWindow):
    """Settings dialog"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.set_title("Configuración")
        self.set_default_size(600, 500)
        self.set_modal(True)
        if parent:
            self.set_transient_for(parent)
            
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self):
        """Setup settings UI"""
        # Appearance page
        appearance_page = Adw.PreferencesPage()
        appearance_page.set_title("Apariencia")
        appearance_page.set_icon_name("preferences-desktop-appearance-symbolic")
        
        # Translucency group
        translucency_group = Adw.PreferencesGroup()
        translucency_group.set_title("Transparencia")
        translucency_group.set_description("Ajusta la transparencia de la ventana")
        
        self.opacity_row = Adw.ActionRow()
        self.opacity_row.set_title("Opacidad")
        self.opacity_row.set_subtitle("88%")
        
        opacity_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 50, 100, 5)
        opacity_scale.set_value(88)
        opacity_scale.set_size_request(200, -1)
        opacity_scale.set_valign(Gtk.Align.CENTER)
        opacity_scale.connect("value-changed", self._on_opacity_changed)
        self.opacity_row.add_suffix(opacity_scale)
        self.opacity_scale = opacity_scale
        
        translucency_group.add(self.opacity_row)
        appearance_page.add(translucency_group)
        
        self.add(appearance_page)
        
        # Pomodoro page
        pomodoro_page = Adw.PreferencesPage()
        pomodoro_page.set_title("Pomodoro")
        pomodoro_page.set_icon_name("alarm-symbolic")
        
        timer_group = Adw.PreferencesGroup()
        timer_group.set_title("Duraciones")
        
        self.work_row = Adw.SpinRow.new_with_range(1, 60, 1)
        self.work_row.set_title("Tiempo de trabajo (min)")
        self.work_row.set_value(25)
        timer_group.add(self.work_row)
        
        self.break_row = Adw.SpinRow.new_with_range(1, 30, 1)
        self.break_row.set_title("Tiempo de descanso (min)")
        self.break_row.set_value(5)
        timer_group.add(self.break_row)
        
        self.long_break_row = Adw.SpinRow.new_with_range(5, 60, 5)
        self.long_break_row.set_title("Descanso largo (min)")
        self.long_break_row.set_value(15)
        timer_group.add(self.long_break_row)
        
        pomodoro_page.add(timer_group)
        self.add(pomodoro_page)
        
        # Sync page
        sync_page = Adw.PreferencesPage()
        sync_page.set_title("Sincronización")
        sync_page.set_icon_name("emblem-synchronizing-symbolic")
        
        # iCloud group
        icloud_group = Adw.PreferencesGroup()
        icloud_group.set_title("iCloud Calendar")
        icloud_group.set_description("Sincroniza tus tareas con el calendario de iPhone")
        
        self.icloud_enabled = Adw.SwitchRow()
        self.icloud_enabled.set_title("Habilitar sincronización")
        icloud_group.add(self.icloud_enabled)
        
        self.icloud_user = Adw.EntryRow()
        self.icloud_user.set_title("Apple ID")
        icloud_group.add(self.icloud_user)
        
        self.icloud_pass = Adw.PasswordEntryRow()
        self.icloud_pass.set_title("App-Specific Password")
        icloud_group.add(self.icloud_pass)
        
        sync_page.add(icloud_group)
        
        # D2L group
        d2l_group = Adw.PreferencesGroup()
        d2l_group.set_title("Brightspace D2L")
        
        self.d2l_url = Adw.EntryRow()
        self.d2l_url.set_title("URL del calendario ICS")
        d2l_group.add(self.d2l_url)
        
        sync_page.add(d2l_group)
        self.add(sync_page)
        
        # About page
        about_page = Adw.PreferencesPage()
        about_page.set_title("Acerca de")
        about_page.set_icon_name("help-about-symbolic")
        
        about_group = Adw.PreferencesGroup()
        
        version_row = Adw.ActionRow()
        version_row.set_title("Unix Productivity App")
        version_row.set_subtitle("Versión 2.0 (GTK4)")
        about_group.add(version_row)
        
        author_row = Adw.ActionRow()
        author_row.set_title("Autor")
        author_row.set_subtitle("jjjulianleon")
        about_group.add(author_row)
        
        about_page.add(about_group)
        self.add(about_page)
        
    def _on_opacity_changed(self, scale):
        """Handle opacity change"""
        value = int(scale.get_value())
        self.opacity_row.set_subtitle(f"{value}%")
        # TODO: Apply opacity to main window
        
    def _load_settings(self):
        """Load settings from database"""
        try:
            settings = task_manager.get_all_settings()
            
            # Pomodoro
            self.work_row.set_value(settings.get('pomodoro_work', 25))
            self.break_row.set_value(settings.get('pomodoro_break', 5))
            self.long_break_row.set_value(settings.get('pomodoro_long_break', 15))
            
        except Exception as e:
            print(f"Error loading settings: {e}")
            
    def _save_settings(self):
        """Save settings to database"""
        try:
            task_manager.set_setting('pomodoro_work', int(self.work_row.get_value()))
            task_manager.set_setting('pomodoro_break', int(self.break_row.get_value()))
            task_manager.set_setting('pomodoro_long_break', int(self.long_break_row.get_value()))
        except Exception as e:
            print(f"Error saving settings: {e}")
