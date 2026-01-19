"""
Settings Dialog - GTK4
Application preferences with save functionality
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gdk
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager


class SettingsDialog(Adw.PreferencesWindow):
    """Settings dialog with save functionality"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent
        self.set_title("Configuración")
        self.set_default_size(600, 500)
        self.set_modal(True)
        if parent:
            self.set_transient_for(parent)
            
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self):
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
        
        self.opacity_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 50, 100, 5)
        self.opacity_scale.set_value(88)
        self.opacity_scale.set_size_request(150, -1)
        self.opacity_scale.set_valign(Gtk.Align.CENTER)
        self.opacity_scale.connect("value-changed", self._on_opacity_changed)
        self.opacity_row.add_suffix(self.opacity_scale)
        
        # Save opacity button
        save_opacity_btn = Gtk.Button(label="Aplicar")
        save_opacity_btn.add_css_class("suggested-action")
        save_opacity_btn.set_valign(Gtk.Align.CENTER)
        save_opacity_btn.connect("clicked", self._on_save_opacity)
        self.opacity_row.add_suffix(save_opacity_btn)
        
        translucency_group.add(self.opacity_row)
        appearance_page.add(translucency_group)
        
        # Font group
        font_group = Adw.PreferencesGroup()
        font_group.set_title("Fuente")
        font_group.set_description("Selecciona la fuente de la aplicación")
        
        self.font_row = Adw.ComboRow()
        self.font_row.set_title("Familia de fuente")
        fonts = Gtk.StringList.new([
            "Sistema (predeterminado)",
            "Source Code Pro",
            "Inter",
            "Roboto",
            "Ubuntu",
            "Fira Code"
        ])
        self.font_row.set_model(fonts)
        self.font_row.connect("notify::selected", self._on_font_changed)
        font_group.add(self.font_row)
        
        appearance_page.add(font_group)
        
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
        
        # Save pomodoro button
        save_pomodoro_row = Adw.ActionRow()
        save_pomodoro_row.set_title("")
        
        save_pomodoro_btn = Gtk.Button(label="Guardar configuración")
        save_pomodoro_btn.add_css_class("suggested-action")
        save_pomodoro_btn.set_valign(Gtk.Align.CENTER)
        save_pomodoro_btn.connect("clicked", self._on_save_pomodoro)
        save_pomodoro_row.add_suffix(save_pomodoro_btn)
        timer_group.add(save_pomodoro_row)
        
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
        
        # Teams group
        teams_group = Adw.PreferencesGroup()
        teams_group.set_title("Microsoft Teams / Outlook")
        
        self.teams_url = Adw.EntryRow()
        self.teams_url.set_title("URL del calendario ICS")
        teams_group.add(self.teams_url)
        
        sync_page.add(teams_group)
        
        # Save button group
        save_group = Adw.PreferencesGroup()
        
        save_sync_btn = Gtk.Button(label="Guardar configuración")
        save_sync_btn.add_css_class("suggested-action")
        save_sync_btn.set_margin_top(12)
        save_sync_btn.connect("clicked", self._on_save_sync)
        save_group.add(save_sync_btn)
        
        # Push all button
        push_btn = Gtk.Button(label="⬆ Sincronizar todo ahora")
        push_btn.set_margin_top(8)
        push_btn.set_tooltip_text("Envía todas las tareas con deadline a iCloud")
        push_btn.connect("clicked", self._on_push_all_to_icloud)
        save_group.add(push_btn)
        
        sync_page.add(save_group)
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
        value = int(scale.get_value())
        self.opacity_row.set_subtitle(f"{value}%")
        
    def _on_save_opacity(self, btn):
        """Apply and save opacity"""
        value = int(self.opacity_scale.get_value())
        
        # Save to database
        try:
            task_manager.set_setting('window_opacity', value)
        except:
            pass
            
        # Apply to main window CSS
        if self.parent_window:
            css = Gtk.CssProvider()
            opacity = value / 100
            css.load_from_data(f"window.main-window {{ background-color: alpha(@window_bg_color, {opacity}); }}".encode())
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            
        # Show confirmation
        self.opacity_row.set_subtitle(f"{value}% ✓")
        
    def _on_font_changed(self, row, param):
        """Apply selected font"""
        fonts = [
            "",  # System default
            "'Source Code Pro'",
            "'Inter'",
            "'Roboto'",
            "'Ubuntu'",
            "'Fira Code'"
        ]
        selected = row.get_selected()
        font_family = fonts[selected] if selected < len(fonts) else ""
        
        # Save to database
        try:
            task_manager.set_setting('app_font', selected)
        except:
            pass
            
        # Apply font via CSS
        if font_family:
            css = Gtk.CssProvider()
            css.load_from_data(f"* {{ font-family: {font_family}, sans-serif; }}".encode())
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        
    def _on_save_pomodoro(self, btn):
        """Save pomodoro settings"""
        try:
            task_manager.set_setting('pomodoro_work', int(self.work_row.get_value()))
            task_manager.set_setting('pomodoro_break', int(self.break_row.get_value()))
            task_manager.set_setting('pomodoro_long_break', int(self.long_break_row.get_value()))
            btn.set_label("Guardado ✓")
        except Exception as e:
            print(f"Error saving: {e}")
    
    def _on_save_sync(self, btn):
        """Save sync configuration"""
        import json
        from pathlib import Path
        
        config_dir = Path.home() / ".config" / "calendar_widget"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Save iCloud config
        icloud_config = {
            "enabled": self.icloud_enabled.get_active(),
            "apple_id": self.icloud_user.get_text(),
            "app_password": self.icloud_pass.get_text()
        }
        with open(config_dir / "icloud_config.json", 'w') as f:
            json.dump(icloud_config, f, indent=2)
            
        # Save ICS config
        ics_config = {
            "brightspace": {
                "enabled": True,
                "source": "url",
                "url": self.d2l_url.get_text()
            },
            "teams": {
                "enabled": True,
                "source": "url", 
                "url": self.teams_url.get_text()
            }
        }
        with open(config_dir / "ics_config.json", 'w') as f:
            json.dump(ics_config, f, indent=2)
            
        btn.set_label("✓ Guardado")
        
    def _load_settings(self):
        try:
            settings = task_manager.get_all_settings()
            self.work_row.set_value(settings.get('pomodoro_work', 25))
            self.break_row.set_value(settings.get('pomodoro_break', 5))
            self.long_break_row.set_value(settings.get('pomodoro_long_break', 15))
            
            opacity = settings.get('window_opacity', 88)
            self.opacity_scale.set_value(opacity)
            self.opacity_row.set_subtitle(f"{opacity}%")
            
            # Load font
            font_idx = settings.get('app_font', 0)
            self.font_row.set_selected(font_idx)
            
            # Load sync config
            self._load_sync_config()
        except Exception as e:
            print(f"Error loading settings: {e}")
            
    def _load_sync_config(self):
        """Load sync configuration from files"""
        import json
        from pathlib import Path
        
        config_dir = Path.home() / ".config" / "calendar_widget"
        
        # Load iCloud
        icloud_file = config_dir / "icloud_config.json"
        if icloud_file.exists():
            try:
                with open(icloud_file) as f:
                    config = json.load(f)
                    self.icloud_enabled.set_active(config.get("enabled", False))
                    self.icloud_user.set_text(config.get("apple_id", ""))
                    self.icloud_pass.set_text(config.get("app_password", ""))
            except:
                pass
                
        # Load ICS
        ics_file = config_dir / "ics_config.json"
        if ics_file.exists():
            try:
                with open(ics_file) as f:
                    config = json.load(f)
                    bs = config.get("brightspace", {})
                    self.d2l_url.set_text(bs.get("url", ""))
                    teams = config.get("teams", {})
                    self.teams_url.set_text(teams.get("url", ""))
            except:
                pass
                
    def _on_push_all_to_icloud(self, btn):
        """Push all existing tasks with deadlines to iCloud"""
        btn.set_label("Sincronizando...")
        btn.set_sensitive(False)
        
        try:
            # Get all tasks with deadlines
            tasks = task_manager.get_tasks_with_deadlines()
            pending = [t for t in tasks if t.get('status') != 'completado' and t.get('deadline')]
            
            if not pending:
                btn.set_label("Sin tareas para sincronizar")
                btn.set_sensitive(True)
                return
                
            # Try to sync with iCloud
            try:
                from icloud_integration import ICloudSync
                icloud = ICloudSync()
                
                if not icloud.config.get("enabled"):
                    btn.set_label("⚠ iCloud no habilitado")
                    btn.set_sensitive(True)
                    return
                    
                # Convert tasks to deadline format
                deadlines = []
                for task in pending:
                    deadlines.append({
                        'title': task.get('title', ''),
                        'due_date': task['deadline'] + 'T23:59:00',
                        'description': task.get('description', ''),
                        'type': 'task'
                    })
                    
                result = icloud.sync_deadlines_to_icloud(deadlines)
                created = result.get('created', 0)
                skipped = result.get('skipped', 0)
                
                btn.set_label(f"✓ {created} nuevos, {skipped} existentes")
                
            except ImportError:
                btn.set_label("⚠ caldav no instalado")
            except Exception as e:
                btn.set_label(f"⚠ Error: {str(e)[:20]}")
                print(f"iCloud sync error: {e}")
                
        except Exception as e:
            btn.set_label(f"⚠ Error")
            print(f"Push error: {e}")
            
        btn.set_sensitive(True)
