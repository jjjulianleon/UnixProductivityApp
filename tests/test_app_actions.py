"""
Smoke test de la capa de aplicacion GTK: acciones, aceleradores por plataforma
y navegacion entre vistas.

Necesita una sesion grafica (GTK4). Se omite automaticamente si no la hay.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, GLib

HAS_DISPLAY = Gtk.init_check()

from main_gtk import UniDexApp, NAV_KEYS, accel
from src.utils.system import IS_MAC


@unittest.skipUnless(HAS_DISPLAY, "requiere sesion grafica")
class TestAppActions(unittest.TestCase):

    def test_accelerators_and_navigation(self):
        app = UniDexApp()
        problems = []

        def check():
            window = app.window
            try:
                # En macOS los atajos deben usar Command (<Meta>), no Control
                if IS_MAC:
                    self.assertEqual(accel("n"), ["<Meta>n", "<Control>n"])
                else:
                    self.assertEqual(accel("n"), ["<Control>n"])

                for action, key in [("app.quit", "q"), ("app.new-task", "n"),
                                    ("app.settings", "comma"), ("app.close-window", "w")]:
                    self.assertEqual(app.get_accels_for_action(action), accel(key), action)

                # ⌘1..⌘8 navegan a cada vista
                for index, view in enumerate(NAV_KEYS, start=1):
                    self.assertEqual(app.get_accels_for_action(f"app.nav::{view}"),
                                     accel(str(index)), view)
                    app.activate_action("nav", GLib.Variant("s", view))
                    self.assertEqual(window.stack.get_visible_child_name(), view)

                # Las acciones del menu estan implementadas (no solo declaradas)
                for name in ("backup", "export", "import", "about", "settings",
                             "new-task", "close-window", "quit"):
                    self.assertTrue(app.lookup_action(name), f"falta la accion {name}")

                # El tamaño de ventana se persiste al cerrar.
                # get_width() es 0 hasta que la ventana esta mapeada, asi que se
                # espera a que lo este en vez de confiar en un timeout fijo.
                self.assertGreater(window.get_width(), 0, "la ventana no llego a mapearse")

                from src.core.task_manager import task_manager
                task_manager.set_setting('window_width', 0)
                window._on_close_request()
                self.assertGreater(task_manager.get_setting('window_width', 0), 100)
            except Exception as error:  # se reporta fuera del bucle GTK
                problems.append(error)
            app.quit()
            return False

        def wait_for_window():
            """Reintenta hasta que la ventana tenga tamano real (max ~5 s)"""
            wait_for_window.tries += 1
            if app.window and app.window.get_width() > 0:
                return check()
            if wait_for_window.tries > 50:
                problems.append(AssertionError("la ventana nunca se mapeo"))
                app.quit()
                return False
            return True  # seguir reintentando

        wait_for_window.tries = 0
        GLib.timeout_add(100, wait_for_window)
        app.run([])

        if problems:
            raise problems[0]


if __name__ == "__main__":
    unittest.main()
