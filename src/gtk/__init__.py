"""
GTK4 UI Package for UniDex
"""
from pathlib import Path

STYLES_DIR = Path(__file__).parent / "styles"
ICONS_DIR = Path(__file__).parent.parent.parent / "assets" / "icons"


def load_css(display=None):
    """Carga el tema de UniDex en el display.

    Una sola hoja para la app y para el widget: si cada una define sus propios
    .glass-card o .task-card acaban pareciendo dos programas distintos.
    En macOS se anade macos.css encima para sobreescribir lo especifico de Linux.
    """
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk

    from src.utils.system import IS_MAC

    display = display or Gdk.Display.get_default()
    if display is None:
        return

    sheets = [STYLES_DIR / "style.css"]
    if IS_MAC:
        sheets.append(STYLES_DIR / "macos.css")

    for path in sheets:
        if not path.exists():
            continue
        provider = Gtk.CssProvider()
        provider.load_from_path(str(path))
        Gtk.StyleContext.add_provider_for_display(
            display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


def load_font_css(display=None):
    """Aplica la fuente elegida en Configuracion (indice en settings['app_font'])"""
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk

    from src.core.task_manager import task_manager
    from src.utils.constants import font_css

    display = display or Gdk.Display.get_default()
    if display is None:
        return

    try:
        family = font_css(task_manager.get_setting('app_font', 0))
    except Exception as error:
        print(f"Font setting error: {error}")
        return

    if not family:
        return  # fuente del sistema

    provider = Gtk.CssProvider()
    provider.load_from_data(f"* {{ font-family: {family}, sans-serif; }}".encode())
    Gtk.StyleContext.add_provider_for_display(
        display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def load_icons(display=None):
    """Anade los iconos propios de UniDex al tema.

    El tema Adwaita no trae ninguno de grafico de barras, y los sustitutos
    disponibles se dibujan como un simple "+".
    """
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk

    display = display or Gdk.Display.get_default()
    if display is None or not ICONS_DIR.is_dir():
        return
    Gtk.IconTheme.get_for_display(display).add_search_path(str(ICONS_DIR))


def init_theme(display=None):
    """Todo lo visual de arranque, en una llamada. La usan la app y el widget."""
    load_icons(display)
    load_css(display)
    load_font_css(display)
