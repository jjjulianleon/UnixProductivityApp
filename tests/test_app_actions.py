"""
Smoke test de la capa de aplicacion GTK: acciones, aceleradores por plataforma
y navegacion entre vistas.

Necesita una sesion grafica (GTK4). Se omite automaticamente si no la hay.
"""
import sys
import unittest
from datetime import date
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


@unittest.skipUnless(HAS_DISPLAY, "requiere sesion grafica")
class TestEventoVariosDias(unittest.TestCase):
    """Un evento puede crearse en varios dias a la vez (misma clase L y X)"""

    def setUp(self):
        from src.core.database import Database, db
        from src.core.task_manager import TaskManager

        fresh = Database(":memory:")
        db.conn, db.db_path = fresh.conn, fresh.db_path
        self.db = db
        TaskManager._instance = None

    def dialog(self, **kwargs):
        from src.gtk.widgets.schedule import AddEventDialog
        return AddEventDialog(**kwargs)

    def test_guardar_crea_un_evento_por_dia_marcado(self):
        dialog = self.dialog(default_day=0, default_hour=7)
        dialog.title_entry.set_text("Proyecto Integrador CMP")
        dialog.start_entry.set_text("07:00")
        dialog.end_entry.set_text("08:20")
        dialog.start_date_row.set_date(date(2026, 8, 17))
        dialog.day_buttons[2].set_active(True)  # ademas del lunes, miercoles

        self.assertEqual(dialog.selected_days(), [0, 2])
        dialog._on_save(None)

        creados = sorted(self.db.get_schedule_events(), key=lambda e: e['day_of_week'])
        self.assertEqual([e['day_of_week'] for e in creados], [0, 2])
        for evento in creados:
            self.assertEqual(evento['title'], "Proyecto Integrador CMP")
            self.assertEqual(evento['start_time'], "07:00")
            self.assertEqual(evento['end_time'], "08:20")
            self.assertEqual(evento['start_date'], "2026-08-17")
            self.assertIsNone(evento['end_date'])

    def test_repetir_exige_fecha_de_inicio(self):
        """Si repite cada semana, sin inicio no se guarda nada"""
        dialog = self.dialog(default_day=0, default_hour=7)
        dialog.title_entry.set_text("Clase sin fecha")

        self.assertTrue(dialog.recurring.get_active())
        self.assertTrue(dialog.range_group.get_visible())
        dialog._on_save(None)

        self.assertEqual(self.db.get_schedule_events(), [])
        self.assertTrue(dialog.start_date_row.has_css_class("error"))

    def test_sin_repetir_no_pide_rango(self):
        dialog = self.dialog(default_day=0, default_hour=7)
        dialog.title_entry.set_text("Charla suelta")
        dialog.recurring.set_active(False)

        self.assertFalse(dialog.range_group.get_visible())
        dialog._on_save(None)

        creados = self.db.get_schedule_events()
        self.assertEqual(len(creados), 1)
        self.assertEqual(creados[0]['recurring'], 0)
        self.assertIsNone(creados[0]['start_date'])

    def test_no_se_puede_dejar_sin_ningun_dia(self):
        dialog = self.dialog(default_day=1, default_hour=9)
        self.assertEqual(dialog.selected_days(), [1])

        dialog.day_buttons[1].set_active(False)  # apagar el unico marcado

        self.assertEqual(dialog.selected_days(), [1], "vuelve a marcarse solo")

    def test_editar_mueve_el_evento_y_crea_los_dias_extra(self):
        event_id = self.db.add_schedule_event(title="Clase", day_of_week=1,
                                              start_time="08:30", end_time="09:50",
                                              color="#4285f4")
        evento = dict(self.db.get_schedule_events(1)[0])
        evento['start'], evento['end'] = evento['start_time'], evento['end_time']

        dialog = self.dialog(event=evento)
        dialog.start_date_row.set_date(date(2026, 8, 18))
        dialog.day_buttons[3].set_active(True)  # martes + jueves
        dialog._on_save(None)

        creados = sorted(self.db.get_schedule_events(), key=lambda e: e['day_of_week'])
        self.assertEqual([e['day_of_week'] for e in creados], [1, 3])
        # el original se reutiliza, no se duplica
        self.assertIn(event_id, [e['id'] for e in creados])
