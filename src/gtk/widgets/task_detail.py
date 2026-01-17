"""
Task Detail Dialog - GTK4
View and edit task details
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, GObject
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager


class TaskDetailDialog(Adw.Window):
    """Dialog to view and edit task details"""
    
    __gsignals__ = {
        'task-updated': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, task: dict, parent=None):
        super().__init__()
        self.task = task
        self.task_id = task.get('id')
        
        self.set_title(task.get('title', 'Tarea'))
        self.set_default_size(450, 500)
        self.set_modal(True)
        if parent:
            self.set_transient_for(parent)
            
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup dialog UI"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)
        
        # Header bar
        header = Adw.HeaderBar()
        header.add_css_class("flat")
        
        close_btn = Gtk.Button(label="Cerrar")
        close_btn.connect("clicked", lambda _: self.close())
        header.pack_start(close_btn)
        
        save_btn = Gtk.Button(label="Guardar")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save)
        header.pack_end(save_btn)
        
        delete_btn = Gtk.Button()
        delete_btn.set_icon_name("user-trash-symbolic")
        delete_btn.add_css_class("destructive-action")
        delete_btn.connect("clicked", self._on_delete)
        header.pack_end(delete_btn)
        
        main_box.append(header)
        
        # Content
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        
        # Title
        title_group = Adw.PreferencesGroup()
        self.title_entry = Adw.EntryRow()
        self.title_entry.set_title("Título")
        self.title_entry.set_text(self.task.get('title', ''))
        title_group.add(self.title_entry)
        content.append(title_group)
        
        # Status and Priority
        status_group = Adw.PreferencesGroup()
        
        self.status_row = Adw.ComboRow()
        self.status_row.set_title("Estado")
        statuses = Gtk.StringList.new(["Pendiente", "En Progreso", "Completado"])
        self.status_row.set_model(statuses)
        status_map = {"pendiente": 0, "en progreso": 1, "completado": 2}
        self.status_row.set_selected(status_map.get(self.task.get('status', 'pendiente'), 0))
        status_group.add(self.status_row)
        
        self.priority_row = Adw.ComboRow()
        self.priority_row.set_title("Prioridad")
        priorities = Gtk.StringList.new(["Alta", "Media", "Baja"])
        self.priority_row.set_model(priorities)
        priority_map = {"alta": 0, "media": 1, "baja": 2}
        self.priority_row.set_selected(priority_map.get(self.task.get('priority', 'media'), 1))
        status_group.add(self.priority_row)
        
        content.append(status_group)
        
        # Category
        cat_group = Adw.PreferencesGroup()
        self.category_row = Adw.ComboRow()
        self.category_row.set_title("Categoría")
        categories = Gtk.StringList.new(["Universidad", "Trabajo", "Personal", "Otro"])
        self.category_row.set_model(categories)
        cat_list = ["Universidad", "Trabajo", "Personal", "Otro"]
        current_cat = self.task.get('category', 'Otro')
        self.category_row.set_selected(cat_list.index(current_cat) if current_cat in cat_list else 3)
        cat_group.add(self.category_row)
        content.append(cat_group)
        
        # Deadline
        deadline_group = Adw.PreferencesGroup()
        self.deadline_row = Adw.ActionRow()
        self.deadline_row.set_title("Fecha límite")
        self.selected_deadline = self.task.get('deadline')
        self.deadline_row.set_subtitle(self.selected_deadline or "Sin fecha")
        
        date_btn = Gtk.Button()
        date_btn.set_icon_name("month-symbolic")
        date_btn.set_valign(Gtk.Align.CENTER)
        date_btn.connect("clicked", self._show_date_picker)
        self.deadline_row.add_suffix(date_btn)
        
        clear_btn = Gtk.Button()
        clear_btn.set_icon_name("edit-clear-symbolic")
        clear_btn.set_valign(Gtk.Align.CENTER)
        clear_btn.connect("clicked", self._clear_deadline)
        self.deadline_row.add_suffix(clear_btn)
        
        deadline_group.add(self.deadline_row)
        content.append(deadline_group)
        
        # Description
        desc_group = Adw.PreferencesGroup()
        desc_group.set_title("Descripción")
        
        self.desc_view = Gtk.TextView()
        self.desc_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.desc_view.add_css_class("card")
        self.desc_view.get_buffer().set_text(self.task.get('description', ''))
        
        desc_scroll = Gtk.ScrolledWindow()
        desc_scroll.set_child(self.desc_view)
        desc_scroll.set_min_content_height(120)
        desc_group.add(desc_scroll)
        content.append(desc_group)
        
        # Metadata
        if self.task.get('created_at'):
            meta_group = Adw.PreferencesGroup()
            meta_group.set_title("Información")
            
            created_row = Adw.ActionRow()
            created_row.set_title("Creada")
            created_row.set_subtitle(self.task.get('created_at', ''))
            meta_group.add(created_row)
            
            content.append(meta_group)
        
        scroll.set_child(content)
        main_box.append(scroll)
        
    def _show_date_picker(self, btn):
        """Show date picker"""
        popover = Gtk.Popover()
        popover.set_parent(btn)
        
        calendar = Gtk.Calendar()
        if self.selected_deadline:
            try:
                date = datetime.strptime(self.selected_deadline, "%Y-%m-%d")
                calendar.select_day(GLib.DateTime.new_local(date.year, date.month, date.day, 0, 0, 0))
            except:
                pass
        calendar.connect("day-selected", self._on_date_selected, popover)
        
        popover.set_child(calendar)
        popover.popup()
        
    def _on_date_selected(self, calendar, popover):
        """Handle date selection"""
        date = calendar.get_date()
        self.selected_deadline = f"{date.get_year()}-{date.get_month():02d}-{date.get_day_of_month():02d}"
        self.deadline_row.set_subtitle(self.selected_deadline)
        popover.popdown()
        
    def _clear_deadline(self, btn):
        """Clear deadline"""
        self.selected_deadline = None
        self.deadline_row.set_subtitle("Sin fecha")
        
    def _on_save(self, btn):
        """Save task changes"""
        statuses = ["pendiente", "en progreso", "completado"]
        priorities = ["alta", "media", "baja"]
        categories = ["Universidad", "Trabajo", "Personal", "Otro"]
        
        buffer = self.desc_view.get_buffer()
        start, end = buffer.get_bounds()
        
        try:
            task_manager.update_task(
                self.task_id,
                title=self.title_entry.get_text(),
                status=statuses[self.status_row.get_selected()],
                priority=priorities[self.priority_row.get_selected()],
                category=categories[self.category_row.get_selected()],
                deadline=self.selected_deadline,
                description=buffer.get_text(start, end, False)
            )
            self.emit("task-updated")
            self.close()
        except Exception as e:
            print(f"Error saving task: {e}")
            
    def _on_delete(self, btn):
        """Delete task with confirmation"""
        dialog = Adw.MessageDialog(transient_for=self)
        dialog.set_heading("Eliminar tarea")
        dialog.set_body(f"¿Seguro que quieres eliminar '{self.task.get('title')}'?")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("delete", "Eliminar")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self._on_delete_response)
        dialog.present()
        
    def _on_delete_response(self, dialog, response):
        """Handle delete confirmation"""
        if response == "delete":
            try:
                task_manager.delete_task(self.task_id)
                self.emit("task-updated")
                self.close()
            except Exception as e:
                print(f"Error deleting task: {e}")
        dialog.close()
