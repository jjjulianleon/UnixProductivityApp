"""
Quick Notes Widget - GTK4
Simple note taking widget
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.core.task_manager import task_manager


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
        dialog = AddNoteDialog(parent=self.get_root())
        dialog.connect("response", self._on_note_dialog_response)
        dialog.present()
        
    def _on_note_dialog_response(self, dialog, response):
        """Handle add note dialog response"""
        if response == "save":
            title = dialog.title_entry.get_text()
            buffer = dialog.content_view.get_buffer()
            start, end = buffer.get_bounds()
            content = buffer.get_text(start, end, False)
            
            if title:
                try:
                    task_manager.add_quick_note(title, content)
                    self.refresh()
                except Exception as e:
                    print(f"Error adding note: {e}")
        dialog.close()
        
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
            
    def _create_note_card(self, note: dict) -> Gtk.Box:
        """Create a note card"""
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
        
        # Actions
        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        actions.set_halign(Gtk.Align.END)
        
        delete_btn = Gtk.Button()
        delete_btn.set_icon_name("user-trash-symbolic")
        delete_btn.add_css_class("flat")
        delete_btn.add_css_class("circular")
        delete_btn.connect("clicked", self._on_delete_note, note.get('id'))
        actions.append(delete_btn)
        
        card.append(actions)
        
        return card
        
    def _on_delete_note(self, btn, note_id):
        """Delete a note"""
        if note_id:
            try:
                task_manager.delete_quick_note(note_id)
                self.refresh()
            except Exception as e:
                print(f"Error deleting note: {e}")


class AddNoteDialog(Adw.MessageDialog):
    """Dialog to add a new note"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.set_heading("Nueva Nota")
        self.set_transient_for(parent)
        self.set_modal(True)
        
        self.add_response("cancel", "Cancelar")
        self.add_response("save", "Guardar")
        self.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        
        # Content
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(12)
        
        self.title_entry = Gtk.Entry()
        self.title_entry.set_placeholder_text("Título")
        box.append(self.title_entry)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(100)
        
        self.content_view = Gtk.TextView()
        self.content_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scroll.set_child(self.content_view)
        box.append(scroll)
        
        self.set_extra_child(box)
