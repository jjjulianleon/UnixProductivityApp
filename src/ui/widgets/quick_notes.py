"""
Quick Notes Widget
"""
import os
from datetime import datetime
from pathlib import Path
import re
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QScrollArea, QFrame, QListWidget,
    QListWidgetItem, QDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.utils.styles import (
    COLORS, FONT_FAMILY, get_button_style, get_input_style,
    get_scroll_area_style
)
from src.core.database import db
from src.core.obsidian_sync import ObsidianSync
from src.core.signals import SignalHub


class QuickNoteDialog(QDialog):
    """Dialog to create a quick note"""
    
    note_created = pyqtSignal(str, str)  # title, content
    note_updated = pyqtSignal(int, str, str, str) # id, title, content, path
    
    def __init__(self, note_data: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        self.note_data = note_data
        self.is_edit = note_data is not None
        
        self.setWindowTitle("Editar Nota" if self.is_edit else "Nueva Nota Rapida")
        self.setFixedSize(600, 450)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
        if self.is_edit:
            self._load_data()
            
    def _load_data(self):
        self.title_input.setText(self.note_data.get('title', ''))
        
        # Try to load content from file
        path = self.note_data.get('file_path')
        content = self.note_data.get('content', '')
        
        if path and os.path.exists(path):
            try:
                full_content = Path(path).read_text(encoding='utf-8')
                # Try to strip header
                parts = full_content.split('---', 2)
                if len(parts) >= 3:
                     content = parts[2].strip()
                else:
                     content = full_content
            except Exception:
                pass
                
        self.content_input.setText(content)
    
    def setup_ui(self):
        container = QFrame(self)
        container.setGeometry(0, 0, 600, 450)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(30, 30, 35, 245);
                border: none;
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header_text = "Editar Nota" if self.is_edit else "Nueva Nota Rapida"
        header = QLabel(header_text)
        header.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        header.setStyleSheet(f"color: rgb({COLORS['primary']}); background: transparent;")
        layout.addWidget(header)
        
        # Title input
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Titulo de la nota...")
        self.title_input.setFont(QFont(FONT_FAMILY, 10))
        self.title_input.setStyleSheet(get_input_style())
        layout.addWidget(self.title_input)
        
        # Content input
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Contenido (opcional)...")
        self.content_input.setFont(QFont(FONT_FAMILY, 10))
        self.content_input.setStyleSheet(get_input_style())
        layout.addWidget(self.content_input, 1)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFont(QFont(FONT_FAMILY, 9))
        cancel_btn.setStyleSheet(get_button_style())
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Guardar")
        save_btn.setFont(QFont(FONT_FAMILY, 9))
        save_btn.setStyleSheet(get_button_style('primary'))
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _save(self):
        title = self.title_input.text().strip()
        if not title:
            title = f"Nota {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        content = self.content_input.toPlainText()
        
        if self.is_edit:
            self.note_updated.emit(
                self.note_data.get('id', 0) or 0,
                title, 
                content, 
                self.note_data.get('file_path', '')
            )
        else:
            self.note_created.emit(title, content)
            
        self.accept()


class QuickNoteCard(QFrame):
    """Single note card"""
    
    clicked = pyqtSignal(dict)
    
    def __init__(self, note: Dict, parent=None):
        super().__init__(parent)
        self.note = note
        self.setup_ui()
    
    def setup_ui(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(50, 50, 55, 150);
                border-left: 3px solid rgba({COLORS['warning']}, 200);
                border-radius: 6px;
            }}
            QFrame:hover {{
                background-color: rgba(60, 60, 65, 180);
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        # Title
        title = QLabel(self.note.get('title', 'Sin titulo'))
        title.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        title.setStyleSheet(f"color: rgb({COLORS['warning']}); background: transparent;")
        title.setWordWrap(True)
        layout.addWidget(title)
        
        # Date
        modified = self.note.get('updated_at', self.note.get('modified', ''))
        if modified:
            try:
                if 'T' in str(modified):
                    dt = datetime.fromisoformat(modified)
                else:
                    dt = datetime.strptime(modified, "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%d/%m/%Y %H:%M")
            except:
                date_str = str(modified)[:16]
            
            date_label = QLabel(date_str)
            date_label.setFont(QFont(FONT_FAMILY, 8))
            date_label.setStyleSheet(f"color: rgb({COLORS['text_muted']}); background: transparent;")
            layout.addWidget(date_label)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.note)


class QuickNotesWidget(QWidget):
    """Quick notes list widget"""
    
    note_clicked = pyqtSignal(dict)
    
    def __init__(self, compact: bool = False, parent=None):
        super().__init__(parent)
        self.compact = compact
        self.signals = SignalHub.get_instance()
        self.obsidian = ObsidianSync()
        
        self.setup_ui()
        self._load_notes()
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect to signal hub"""
        self.signals.note_added.connect(self._load_notes)
        self.signals.note_updated.connect(self._load_notes)
        self.signals.note_deleted.connect(self._load_notes)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        margin = 8 if self.compact else 16
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Notas Rapidas")
        title.setFont(QFont(FONT_FAMILY, 11 if self.compact else 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color: rgb({COLORS['warning']}); background: transparent;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        add_btn = QPushButton("+ Nueva")
        add_btn.setFont(QFont(FONT_FAMILY, 9))
        add_btn.setStyleSheet(get_button_style('primary'))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_note)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Notes list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(get_scroll_area_style())
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.notes_widget = QWidget()
        self.notes_layout = QVBoxLayout(self.notes_widget)
        self.notes_layout.setContentsMargins(0, 0, 4, 0)
        self.notes_layout.setSpacing(6)
        self.notes_layout.addStretch()
        
        scroll.setWidget(self.notes_widget)
        layout.addWidget(scroll, 1)
    
    def _load_notes(self, *args):
        """Load notes from database and Obsidian"""
        # Clear existing
        while self.notes_layout.count() > 1:
            item = self.notes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get from database
        db_notes = db.get_all_quick_notes()
        
        # Get from Obsidian Rough Notes
        obsidian_notes = self.obsidian.get_quick_notes()
        
        # Combine (prioritize DB notes to avoid duplicates)
        db_titles = {n['title'] for n in db_notes}
        all_notes = db_notes.copy()
        
        for note in obsidian_notes:
            if note['title'] not in db_titles:
                all_notes.append(note)
        
        # Sort by date - handle mixed str/datetime types
        def get_sort_key(x):
            val = x.get('updated_at', x.get('modified', ''))
            if isinstance(val, datetime):
                return val.isoformat()
            return str(val) if val else ''
        
        all_notes.sort(key=get_sort_key, reverse=True)
        
        # Limit for compact view
        if self.compact:
            all_notes = all_notes[:5]
        
        # Add cards
        for note in all_notes:
            card = QuickNoteCard(note)
            card.clicked.connect(self._on_note_clicked)
            self.notes_layout.insertWidget(self.notes_layout.count() - 1, card)
        
        if not all_notes:
            from .common import EmptyState
            empty = EmptyState("Sin notas")
            self.notes_layout.insertWidget(0, empty)
    
    def _add_note(self):
        """Show dialog to add new note"""
        dialog = QuickNoteDialog(self)
        dialog.note_created.connect(self._create_note)
        dialog.exec()
    
    def _create_note(self, title: str, content: str):
        """Create a new note"""
        # Save to Obsidian
        file_path = self.obsidian.save_quick_note(title, content)
        
        # Save to database
        db.add_quick_note(title, content, file_path)
        
        # Emit signal
        self.signals.note_added.emit({'title': title, 'content': content})
        
        # Refresh
        self._load_notes()
        
    def _update_note(self, note_id: int, title: str, content: str, file_path: str):
        """Update existing note"""
        # Update Obsidian
        if file_path:
            self.obsidian.update_quick_note(file_path, title, content)
            
        # Update DB
        if note_id:
            db.update_quick_note(note_id, title=title, content=content)
            
        # Emit signal
        self.signals.note_updated.emit({'title': title, 'content': content})
        self._load_notes()
    
    def _on_note_clicked(self, note: Dict):
        """Handle note click - Open Edit Dialog"""
        self.note_clicked.emit(note)
        
        dialog = QuickNoteDialog(note_data=note, parent=self)
        dialog.note_updated.connect(self._update_note)
        dialog.exec()
    
    def refresh(self):
        """Refresh notes list"""
        self._load_notes()
