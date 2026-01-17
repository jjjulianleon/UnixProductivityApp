"""
Quick Notes Widget - GTK4
With click to view/edit notes
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, GObject
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager


class NoteDetailDialog(Adw.Window):
    """Dialog to view and edit a note"""
    
    __gsignals__ = {
        'note-updated': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, note: dict = None, parent=None):
        super().__init__()
        self.note = note
        self.note_id = note.get('id') if note else None
        self.is_new = note is None
        
        self.set_title("Nueva Nota" if self.is_new else note.get('title', 'Nota'))
        self.set_default_size(400, 400)
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
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        
        # Title
        title_group = Adw.PreferencesGroup()
        self.title_entry = Adw.EntryRow()
        self.title_entry.set_title("Título")
        if self.note:
            self.title_entry.set_text(self.note.get('title', ''))
        title_group.add(self.title_entry)
        content.append(title_group)
        
        # Content
        content_group = Adw.PreferencesGroup()
        content_group.set_title("Contenido")
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(200)
        scroll.set_vexpand(True)
        
        self.content_view = Gtk.TextView()
        self.content_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.content_view.add_css_class("card")
        if self.note:
            self.content_view.get_buffer().set_text(self.note.get('content', ''))
        scroll.set_child(self.content_view)
        content_group.add(scroll)
        content.append(content_group)
        
        main_box.append(content)
        
    def _on_save(self, btn):
        """Save the note"""
        title = self.title_entry.get_text()
        if not title:
            self.title_entry.add_css_class("error")
            return
            
        buffer = self.content_view.get_buffer()
        start, end = buffer.get_bounds()
        content = buffer.get_text(start, end, False)
        
        try:
            if self.is_new:
                task_manager.add_quick_note(title, content)
            else:
                task_manager.update_quick_note(self.note_id, title=title, content=content)
            self.emit("note-updated")
            self.close()
        except Exception as e:
            print(f"Error saving note: {e}")
            
    def _on_delete(self, btn):
        """Delete note"""
        dialog = Adw.MessageDialog(transient_for=self)
        dialog.set_heading("Eliminar nota")
        dialog.set_body(f"¿Eliminar '{self.note.get('title')}'?")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("delete", "Eliminar")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self._on_delete_response)
        dialog.present()
        
    def _on_delete_response(self, dialog, response):
        """Handle delete response"""
        if response == "delete":
            try:
                task_manager.delete_quick_note(self.note_id)
                self.emit("note-updated")
                self.close()
            except Exception as e:
                print(f"Error deleting note: {e}")
        dialog.close()


class QuickNotes(Gtk.Box):
    """Quick notes widget"""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(24)
        self.set_margin_end(24)
        
        self._setup_ui()
        self.refresh()
        
    def _setup_ui(self):
        """Setup notes UI"""
        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        title = Gtk.Label(label="Notas Rápidas")
        title.add_css_class("title-2")
        title.set_halign(Gtk.Align.START)
        title.set_hexpand(True)
        header.append(title)
        
        add_btn = Gtk.Button()
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.add_css_class("suggested-action")
        add_btn.add_css_class("circular")
        add_btn.connect("clicked", self._on_add_note)
        header.append(add_btn)
        
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
        
        self.append(scroll)
        
    def _on_add_note(self, btn):
        """Show add note dialog"""
        dialog = NoteDetailDialog(parent=self.get_root())
        dialog.connect("note-updated", lambda d: self.refresh())
        dialog.present()
        
    def refresh(self):
        """Refresh notes"""
        # Clear existing
        while True:
            child = self.notes_flow.get_first_child()
            if child:
                self.notes_flow.remove(child)
            else:
                break
                
        try:
            notes = task_manager.get_all_quick_notes()
        except:
            notes = []
            
        if not notes:
            empty = Adw.StatusPage()
            empty.set_icon_name("accessories-text-editor-symbolic")
            empty.set_title("Sin notas")
            empty.set_description("Crea tu primera nota con el botón +")
            self.notes_flow.append(empty)
            return
            
        for note in notes:
            card = self._create_note_card(note)
            self.notes_flow.append(card)
            
    def _create_note_card(self, note: dict) -> Gtk.Button:
        """Create a clickable note card"""
        btn = Gtk.Button()
        btn.add_css_class("flat")
        btn.connect("clicked", self._on_note_clicked, note)
        
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.add_css_class("note-card")
        card.set_size_request(250, 150)
        
        # Title
        title = Gtk.Label(label=note.get('title', 'Sin título'))
        title.add_css_class("title-4")
        title.set_halign(Gtk.Align.START)
        title.set_ellipsize(3)
        card.append(title)
        
        # Content preview
        content = note.get('content', '')[:100]
        if len(note.get('content', '')) > 100:
            content += "..."
        content_label = Gtk.Label(label=content)
        content_label.add_css_class("dim-label")
        content_label.set_halign(Gtk.Align.START)
        content_label.set_valign(Gtk.Align.START)
        content_label.set_wrap(True)
        content_label.set_vexpand(True)
        card.append(content_label)
        
        btn.set_child(card)
        return btn
        
    def _on_note_clicked(self, btn, note):
        """Open note for viewing/editing"""
        dialog = NoteDetailDialog(note, parent=self.get_root())
        dialog.connect("note-updated", lambda d: self.refresh())
        dialog.present()
