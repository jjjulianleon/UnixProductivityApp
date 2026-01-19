"""
Add Task Dialog - GTK4
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager


class AddTaskDialog(Adw.Window):
    """Dialog to add a new task"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.set_title("Nueva Tarea")
        self.set_default_size(400, 450)
        self.set_modal(True)
        if parent:
            self.set_transient_for(parent)
            
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup dialog UI"""
        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)
        
        # Header bar
        header = Adw.HeaderBar()
        header.add_css_class("flat")
        
        cancel_btn = Gtk.Button(label="Cancelar")
        cancel_btn.connect("clicked", lambda _: self.close())
        header.pack_start(cancel_btn)
        
        save_btn = Gtk.Button(label="Guardar")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save)
        header.pack_end(save_btn)
        
        main_box.append(header)
        
        # Content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        
        # Title entry
        self.title_entry = Adw.EntryRow()
        self.title_entry.set_title("Título")
        title_group = Adw.PreferencesGroup()
        title_group.add(self.title_entry)
        content.append(title_group)
        
        # Category dropdown
        category_group = Adw.PreferencesGroup()
        self.category_row = Adw.ComboRow()
        self.category_row.set_title("Categoría")
        categories = Gtk.StringList.new(["Universidad", "Trabajo", "Personal", "Fedora"])
        self.category_row.set_model(categories)
        category_group.add(self.category_row)
        content.append(category_group)
        
        # Priority dropdown
        priority_group = Adw.PreferencesGroup()
        self.priority_row = Adw.ComboRow()
        self.priority_row.set_title("Prioridad")
        priorities = Gtk.StringList.new(["Alta", "Media", "Baja"])
        self.priority_row.set_model(priorities)
        self.priority_row.set_selected(1)  # Default to Media
        priority_group.add(self.priority_row)
        content.append(priority_group)
        
        # Deadline
        deadline_group = Adw.PreferencesGroup()
        self.deadline_row = Adw.ActionRow()
        self.deadline_row.set_title("Fecha límite")
        self.deadline_row.set_subtitle("Sin fecha")
        
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
        self.desc_view.set_size_request(-1, 100)
        self.desc_view.add_css_class("card")
        # Add padding inside the text area
        self.desc_view.set_left_margin(12)
        self.desc_view.set_right_margin(12)
        self.desc_view.set_top_margin(10)
        self.desc_view.set_bottom_margin(10)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(self.desc_view)
        scroll.set_min_content_height(100)
        desc_group.add(scroll)
        content.append(desc_group)
        
        main_box.append(content)
        
        self.selected_deadline = None
        
    def _show_date_picker(self, btn):
        """Show date picker popover"""
        popover = Gtk.Popover()
        popover.set_parent(btn)
        
        calendar = Gtk.Calendar()
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
        """Save the task"""
        title = self.title_entry.get_text()
        if not title:
            # Show error
            self.title_entry.add_css_class("error")
            return
            
        categories = ["Universidad", "Trabajo", "Personal", "Fedora"]
        priorities = ["alta", "media", "baja"]
        
        category = categories[self.category_row.get_selected()]
        priority = priorities[self.priority_row.get_selected()]
        
        # Get description
        buffer = self.desc_view.get_buffer()
        start, end = buffer.get_bounds()
        description = buffer.get_text(start, end, False)
        
        # Save task to database
        try:
            task_manager.add_task(
                title=title,
                category=category,
                description=description,
                priority=priority,
                deadline=self.selected_deadline
            )
            
            # If Trabajo category, also save to Obsidian Pasantías file
            if category == "Trabajo":
                self._save_to_obsidian_pasantias(title)
                
            self.close()
        except Exception as e:
            print(f"Error saving task: {e}")
            
    def _save_to_obsidian_pasantias(self, title: str):
        """Append task to Obsidian Pasantías .md file"""
        PASANTIAS_MD_PATH = Path("/home/jjulianleon/Documents/Obsidian/Pasantías/Pendientes Pasantía.md")
        try:
            if not PASANTIAS_MD_PATH.parent.exists():
                PASANTIAS_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
                
            # Create or append
            if PASANTIAS_MD_PATH.exists():
                content = PASANTIAS_MD_PATH.read_text()
            else:
                content = "# Pendientes Pasantía\n\n"
                
            # Add new task
            content += f"\n- [ ] {title}"
            PASANTIAS_MD_PATH.write_text(content)
        except Exception as e:
            print(f"Error saving to Obsidian: {e}")
