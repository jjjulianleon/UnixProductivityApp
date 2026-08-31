"""
Todos los iconos que nombra el codigo tienen que existir en el tema.

GTK no avisa cuando un nombre no existe: dibuja un cuadro gris y sigue. Asi
llegaron a produccion view-column-symbolic, utilities-system-monitor-symbolic,
emblem-synchronizing-symbolic y month-symbolic, que no estan en Adwaita.
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

HAS_DISPLAY = Gtk.init_check()

from src.gtk import load_icons

# Cualquier literal "algo-symbolic" del codigo de UI
ICON_PATTERN = re.compile(r'["\']([a-z0-9][a-z0-9+.-]*-symbolic)["\']')
SOURCES = [ROOT / "main_gtk.py", ROOT / "widget_gtk.py", *(ROOT / "src" / "gtk").rglob("*.py")]


def icon_names():
    names = set()
    for path in SOURCES:
        names |= set(ICON_PATTERN.findall(path.read_text()))
    return names


@unittest.skipUnless(HAS_DISPLAY, "requiere sesion grafica")
class TestIcons(unittest.TestCase):

    def test_every_icon_name_resolves(self):
        load_icons()
        theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())

        names = icon_names()
        self.assertGreater(len(names), 15, "el escaneo no encontro iconos")

        missing = sorted(n for n in names if not theme.has_icon(n))
        self.assertEqual(missing, [], f"iconos inexistentes en el tema: {missing}")


if __name__ == "__main__":
    unittest.main()
