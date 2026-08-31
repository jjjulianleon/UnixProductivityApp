"""
Rough Notes Widget - GTK4
Reads and writes to Obsidian vault
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, GObject
from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.utils.constants import OBSIDIAN_ROUGH_NOTES as OBSIDIAN_NOTES_PATH


def _short_path(path: Path) -> str:
    """~/…/Rough Notes en vez de la ruta absoluta entera"""
    try:
        return "~/" + str(path.relative_to(Path.home()))
    except ValueError:
        return str(path)


class NoteDetailDialog(Adw.Window):
    """Dialog to view and edit a note"""
    
    __gsignals__ = {
        'note-updated': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, note_path: Path = None, parent=None):
        super().__init__()
        self.note_path = note_path
        self.is_new = note_path is None
        
        title = "Nueva Nota" if self.is_new else note_path.stem
        self.set_title(title)
        self.set_default_size(500, 500)
        self.set_modal(True)
        if parent:
            self.set_transient_for(parent)
            
        self._setup_ui()
        
    def _setup_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)
        
        # Header
        header = Adw.HeaderBar()
        header.add_css_class("flat")
        
        close_btn = Gtk.Button(label="Cancelar")
        close_btn.connect("clicked", lambda _: self.close())
        header.pack_start(close_btn)
        
        save_btn = Gtk.Button(label="Guardar")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save)
        header.pack_end(save_btn)
        
        if not self.is_new:
            delete_btn = Gtk.Button()
            delete_btn.set_icon_name("user-trash-symbolic")
            delete_btn.add_css_class("destructive-action")
            delete_btn.connect("clicked", self._on_delete)
            header.pack_end(delete_btn)
        
        main_box.append(header)
        
        # Content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        content.set_margin_start(16)
        content.set_margin_end(16)
        
        # Title
        title_group = Adw.PreferencesGroup()
        self.title_entry = Adw.EntryRow()
        self.title_entry.set_title("Nombre del archivo")
        if self.note_path:
            self.title_entry.set_text(self.note_path.stem)
        title_group.add(self.title_entry)
        content.append(title_group)
        
        # Content editor
        content_label = Gtk.Label(label="Contenido")
        content_label.set_halign(Gtk.Align.START)
        content_label.add_css_class("title-4")
        content.append(content_label)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_min_content_height(250)
        
        self.content_view = Gtk.TextView()
        self.content_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.content_view.add_css_class("card")
        self.content_view.set_left_margin(8)
        self.content_view.set_right_margin(8)
        self.content_view.set_top_margin(8)
        self.content_view.set_bottom_margin(8)
        
        # Load content if existing
        if self.note_path and self.note_path.exists():
            try:
                text = self.note_path.read_text()
                self.content_view.get_buffer().set_text(text)
            except:
                pass
                
        scroll.set_child(self.content_view)
        content.append(scroll)
        
        main_box.append(content)
        
    def _on_save(self, btn):
        title = self.title_entry.get_text().strip()
        if not title:
            self.title_entry.add_css_class("error")
            return
            
        # Sanitize filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_title:
            safe_title = "nota"
            
        buffer = self.content_view.get_buffer()
        start, end = buffer.get_bounds()
        content = buffer.get_text(start, end, False)
        
        # Ensure directory exists
        OBSIDIAN_NOTES_PATH.mkdir(parents=True, exist_ok=True)
        
        # Determine file path
        if self.is_new or self.title_entry.get_text() != self.note_path.stem:
            new_path = OBSIDIAN_NOTES_PATH / f"{safe_title}.md"
            # Delete old file if renamed
            if not self.is_new and self.note_path.exists():
                self.note_path.unlink()
        else:
            new_path = self.note_path
            
        try:
            new_path.write_text(content)
            self.emit("note-updated")
            self.close()
        except Exception as e:
            print(f"Error saving note: {e}")
            
    def _on_delete(self, btn):
        dialog = Adw.MessageDialog(transient_for=self)
        dialog.set_heading("Eliminar nota")
        dialog.set_body(f"¿Eliminar '{self.note_path.stem}'?")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("delete", "Eliminar")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self._on_delete_response)
        dialog.present()
        
    def _on_delete_response(self, dialog, response):
        if response == "delete":
            try:
                if self.note_path.exists():
                    self.note_path.unlink()
                self.emit("note-updated")
                self.close()
            except Exception as e:
                print(f"Error deleting note: {e}")
        dialog.close()


class QuickNotes(Gtk.Box):
    """Rough Notes widget - reads from Obsidian vault"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)
        
        self._setup_ui()
        self.refresh()
        
    def _setup_ui(self):
        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        # Ruta del vault abreviada: la completa va en el tooltip, no ocupando
        # media cabecera.
        path_label = Gtk.Label(label=_short_path(OBSIDIAN_NOTES_PATH))
        path_label.add_css_class("dim-label")
        path_label.add_css_class("caption")
        path_label.set_ellipsize(3)
        path_label.set_halign(Gtk.Align.START)
        path_label.set_hexpand(True)
        path_label.set_tooltip_text(str(OBSIDIAN_NOTES_PATH))
        header.append(path_label)

        add_btn = Gtk.Button()
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.add_css_class("flat")
        add_btn.add_css_class("circular")
        add_btn.set_tooltip_text("Nueva nota")
        add_btn.set_margin_start(12)
        add_btn.connect("clicked", self._on_add_note)
        header.append(add_btn)
        
        refresh_btn = Gtk.Button()
        refresh_btn.set_icon_name("view-refresh-symbolic")
        refresh_btn.add_css_class("flat")
        refresh_btn.add_css_class("circular")
        refresh_btn.set_tooltip_text("Recargar desde el vault")
        refresh_btn.connect("clicked", lambda _: self.refresh())
        header.append(refresh_btn)
        
        self.append(header)
        
        # Notes grid
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.notes_flow = Gtk.FlowBox()
        self.notes_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.notes_flow.set_homogeneous(True)
        self.notes_flow.set_max_children_per_line(3)
        self.notes_flow.set_min_children_per_line(1)
        self.notes_flow.set_column_spacing(12)
        self.notes_flow.set_row_spacing(12)
        scroll.set_child(self.notes_flow)

        self.empty_page = Adw.StatusPage()
        self.empty_page.set_icon_name("text-editor-symbolic")
        self.empty_page.set_title("Sin notas")
        self.empty_page.set_description(f"Crea notas en {_short_path(OBSIDIAN_NOTES_PATH)}")

        # Stack en vez de meter el estado vacio como hijo del FlowBox, donde
        # heredaba el ancho de una columna.
        self.body = Gtk.Stack()
        self.body.set_vexpand(True)
        self.body.add_named(scroll, "list")
        self.body.add_named(self.empty_page, "empty")

        self.append(self.body)
        
    def _on_add_note(self, btn):
        dialog = NoteDetailDialog(parent=self.get_root())
        dialog.connect("note-updated", lambda d: self.refresh())
        dialog.present()
        
    def refresh(self):
        # Clear existing
        while child := self.notes_flow.get_first_child():
            self.notes_flow.remove(child)
            
        # Load notes from Obsidian vault
        notes = []
        if OBSIDIAN_NOTES_PATH.exists():
            for file in OBSIDIAN_NOTES_PATH.glob("*.md"):
                try:
                    stat = file.stat()
                    notes.append({
                        'path': file,
                        'title': file.stem,
                        'modified': stat.st_mtime,
                        'preview': file.read_text()[:150] if file.stat().st_size > 0 else ""
                    })
                except:
                    pass
                    
        # Sort by modified time (newest first)
        notes.sort(key=lambda n: n['modified'], reverse=True)
        
        if not notes:
            self.body.set_visible_child_name("empty")
            return

        self.body.set_visible_child_name("list")

        for note in notes:
            card = self._create_note_card(note)
            self.notes_flow.append(card)
            
    def _create_note_card(self, note: dict) -> Gtk.Button:
        btn = Gtk.Button()
        btn.add_css_class("flat")
        btn.connect("clicked", self._on_note_clicked, note['path'])
        
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.add_css_class("note-card")
        card.set_size_request(250, 150)
        
        # Title
        title = Gtk.Label(label=note['title'])
        title.add_css_class("title-4")
        title.set_halign(Gtk.Align.START)
        title.set_ellipsize(3)
        card.append(title)
        
        # Preview
        preview = note['preview'][:100]
        if len(note['preview']) > 100:
            preview += "..."
        content_label = Gtk.Label(label=preview)
        content_label.add_css_class("dim-label")
        content_label.set_halign(Gtk.Align.START)
        content_label.set_valign(Gtk.Align.START)
        content_label.set_wrap(True)
        content_label.set_vexpand(True)
        card.append(content_label)
        
        btn.set_child(card)
        return btn
        
    def _on_note_clicked(self, btn, note_path):
        dialog = NoteDetailDialog(note_path, parent=self.get_root())
        dialog.connect("note-updated", lambda d: self.refresh())
        dialog.present()
