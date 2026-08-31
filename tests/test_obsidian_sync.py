"""
Tests de la sincronizacion con Obsidian.

Las rutas se INYECTAN en ObsidianSync, nunca se toca el vault real: una
variable de entorno no bastaria porque constants.py resuelve las rutas al
importarse y el orden de imports entre modulos de test no esta garantizado.
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.obsidian_sync import ObsidianSync
from src.utils.constants import OBSIDIAN_VAULT_PATHS as REAL_VAULT_PATHS


class TestObsidianSync(unittest.TestCase):
    """Formato markdown, ida y vuelta, y edicion de tareas concretas"""

    def setUp(self):
        self.vault = Path(tempfile.mkdtemp(prefix="unidex-vault-"))
        self.addCleanup(shutil.rmtree, self.vault, ignore_errors=True)

        self.sync = ObsidianSync(
            vault_paths={
                "Personal": self.vault / "Personal" / "Pendientes Personal.md",
                "Universidad": self.vault / "Universidad" / "Pendientes Universidad.md",
                "Fedora": self.vault / "Pendientes Fedora.md",
            },
            rough_notes_folder=self.vault / "Rough Notes",
        )

    def test_los_tests_no_apuntan_al_vault_real(self):
        """Red de seguridad: un fallo aqui significa que se escribiria en iCloud"""
        for path in self.sync.vault_paths.values():
            self.assertTrue(path.is_relative_to(self.vault), path)
        self.assertTrue(self.sync.rough_notes_folder.is_relative_to(self.vault))
        for real in REAL_VAULT_PATHS.values():
            self.assertNotIn(real, self.sync.vault_paths.values())

    def titles(self):
        return [t['title'] for t in self.sync.read_all_tasks()]

    def by_title(self):
        return {t['title']: t for t in self.sync.read_all_tasks()}

    # ------------------------------------------------------------ formato
    def test_roundtrip_conserva_todos_los_campos(self):
        self.sync.add_task("Entregar informe", "Universidad", status="en progreso",
                           deadline="2026-09-15", priority="alta",
                           description="seccion de resultados")
        task = self.by_title()["Entregar informe"]
        self.assertEqual(task['status'], "en progreso")
        self.assertEqual(task['deadline'], "2026-09-15")
        self.assertEqual(task['priority'], "alta")
        self.assertEqual(task['description'], "seccion de resultados")
        self.assertEqual(task['category'], "Universidad")

    def test_lee_el_formato_emoji_de_obsidian_tasks(self):
        path = self.sync.vault_paths["Personal"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Pendientes Personal\n\n- [ ] Renovar pasaporte 📅 2026-10-01\n",
                        encoding="utf-8")
        task = self.by_title()["Renovar pasaporte"]
        self.assertEqual(task['deadline'], "2026-10-01")

    def test_tarea_marcada_se_lee_como_completada(self):
        self.sync.add_task("Ya hecha", "Personal", status="completado")
        self.assertEqual(self.by_title()["Ya hecha"]['status'], "completado")

    def test_categoria_desconocida_no_escribe_nada(self):
        self.sync.add_task("Huerfana", "NoExiste")
        self.assertNotIn("Huerfana", self.titles())

    def test_no_se_pega_a_la_ultima_linea_sin_salto_final(self):
        path = self.sync.vault_paths["Personal"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Pendientes Personal\n\n- [ ] Ya existia", encoding="utf-8")
        self.sync.add_task("Nueva", "Personal")
        self.assertEqual(self.titles(), ["Ya existia", "Nueva"])

    # ------------------------------------------- descripcion multilinea
    def test_descripcion_multilinea_va_indentada_bajo_la_tarea(self):
        desc = "Introduccion\nDesarrollo\nConclusion"
        self.sync.add_task("Ensayo", "Personal", description=desc)

        texto = self.sync.vault_paths["Personal"].read_text(encoding="utf-8")
        self.assertIn("- [ ] Ensayo\n  Introduccion\n  Desarrollo\n  Conclusion", texto)
        self.assertNotIn("\\n", texto)  # nada de saltos escapados a la vista
        self.assertEqual(self.by_title()["Ensayo"]['description'], desc)

    def test_sigue_leyendo_el_formato_antiguo_en_una_linea(self):
        path = self.sync.vault_paths["Personal"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# P\n\n- [ ] Vieja | escrita a mano [priority: baja]\n",
                        encoding="utf-8")
        task = self.by_title()["Vieja"]
        self.assertEqual(task['description'], "escrita a mano")
        self.assertEqual(task['priority'], "baja")

    def test_una_subtarea_indentada_no_es_descripcion(self):
        path = self.sync.vault_paths["Personal"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# P\n\n- [ ] Padre\n  - [ ] Hija\n", encoding="utf-8")
        self.assertEqual(self.titles(), ["Padre", "Hija"])

    def test_borrar_se_lleva_su_descripcion_y_no_la_de_al_lado(self):
        self.sync.add_task("Uno", "Personal", description="linea A\nlinea B")
        self.sync.add_task("Dos", "Personal", description="suya")

        self.sync.delete_task("Uno", "Personal")

        self.assertEqual(self.titles(), ["Dos"])
        self.assertEqual(self.by_title()["Dos"]['description'], "suya")
        self.assertNotIn("linea A", self.sync.vault_paths["Personal"].read_text(encoding="utf-8"))

    # ------------------------------------------- edicion de UNA sola tarea
    def test_borrar_no_arrastra_titulos_que_la_contienen(self):
        for title in ("Estudiar", "Estudiar calculo", "Estudiar fisica"):
            self.sync.add_task(title, "Personal")

        self.sync.delete_task("Estudiar", "Personal")

        self.assertEqual(self.titles(), ["Estudiar calculo", "Estudiar fisica"])

    def test_actualizar_no_arrastra_titulos_que_la_contienen(self):
        self.sync.add_task("Estudiar", "Personal")
        self.sync.add_task("Estudiar calculo", "Personal")

        self.sync.update_task("Estudiar", "Personal", status="completado")

        tasks = self.by_title()
        self.assertEqual(tasks["Estudiar"]['status'], "completado")
        self.assertEqual(tasks["Estudiar calculo"]['status'], "pendiente")

    def test_actualizar_conserva_los_campos_no_tocados(self):
        self.sync.add_task("Leer", "Personal", deadline="2026-09-20",
                           priority="alta", description="capitulo 3")

        self.sync.update_task("Leer", "Personal", status="en progreso")

        task = self.by_title()["Leer"]
        self.assertEqual(task['status'], "en progreso")
        self.assertEqual(task['deadline'], "2026-09-20")
        self.assertEqual(task['priority'], "alta")
        self.assertEqual(task['description'], "capitulo 3")

    def test_renombrar_una_tarea(self):
        self.sync.add_task("Titulo viejo", "Personal")
        self.sync.update_task("Titulo viejo", "Personal", title="Titulo nuevo")
        self.assertEqual(self.titles(), ["Titulo nuevo"])

    # ------------------------------------------------------- rough notes
    def test_guardar_y_listar_notas(self):
        path = self.sync.save_quick_note("Idea suelta", "cuerpo de la nota")
        self.assertTrue(Path(path).exists())

        notes = self.sync.get_quick_notes()
        self.assertIn("Idea suelta", [n['title'] for n in notes])
        self.assertIn("cuerpo de la nota", Path(path).read_text(encoding="utf-8"))

    def test_actualizar_nota_conserva_la_fecha_de_creacion(self):
        path = self.sync.save_quick_note("Nota", "v1")
        created = [l for l in Path(path).read_text(encoding="utf-8").splitlines()
                   if l.startswith("Created:")][0]

        self.assertTrue(self.sync.update_quick_note(path, "Nota", "v2"))

        text = Path(path).read_text(encoding="utf-8")
        self.assertIn(created, text)
        self.assertIn("Updated:", text)
        self.assertIn("v2", text)

    def test_actualizar_nota_inexistente_devuelve_false(self):
        self.assertFalse(self.sync.update_quick_note("/no/existe.md", "x", "y"))


if __name__ == "__main__":
    unittest.main()


class TestDescripcionExtremoAExtremo(unittest.TestCase):
    """La descripcion tiene que llegar a la base de datos Y al .md, y volver.

    Cubre el cableado task_manager -> obsidian_sync, que los tests de arriba
    (que hablan con ObsidianSync directamente) no tocan.
    """

    def setUp(self):
        from src.core.database import Database, db
        from src.core.task_manager import TaskManager

        self.vault = Path(tempfile.mkdtemp(prefix="unidex-e2e-"))
        self.addCleanup(shutil.rmtree, self.vault, ignore_errors=True)
        self.md = self.vault / "Pendientes Personal.md"

        fresh = Database(":memory:")
        db.conn, db.db_path = fresh.conn, fresh.db_path
        self.db = db

        TaskManager._instance = None
        self.tm = TaskManager.get_instance()
        self.tm.obsidian = ObsidianSync(
            vault_paths={"Personal": self.md},
            rough_notes_folder=self.vault / "Rough Notes")

    def obsidian_task(self, title):
        return {t['title']: t for t in self.tm.obsidian.read_all_tasks()}[title]

    def test_la_descripcion_llega_a_la_base_de_datos_y_al_markdown(self):
        desc = "Repasar el capitulo 4\nHacer los ejercicios impares"
        task_id = self.tm.add_task("Estudiar Redes", "Personal", description=desc,
                                   priority="alta", deadline="2026-09-12")

        self.assertEqual(self.db.get_task(task_id)['description'], desc)
        self.assertEqual(self.obsidian_task("Estudiar Redes")['description'], desc)

    def test_completar_desde_la_app_conserva_la_descripcion(self):
        desc = "linea A\nlinea B"
        task_id = self.tm.add_task("Tarea", "Personal", description=desc)

        self.tm.update_task(task_id, status="completado")

        task = self.obsidian_task("Tarea")
        self.assertEqual(task['status'], "completado")
        self.assertEqual(task['description'], desc)

    def test_borrar_desde_la_app_limpia_tarea_y_descripcion(self):
        task_id = self.tm.add_task("Tarea", "Personal", description="algo que borrar")

        self.tm.delete_task(task_id)

        self.assertEqual(self.tm.obsidian.read_all_tasks(), [])
        self.assertNotIn("algo que borrar", self.md.read_text(encoding="utf-8"))
