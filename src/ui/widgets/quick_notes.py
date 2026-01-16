"""
Quick Notes Widget
"""
import os
from datetime import datetime
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


class QuickNoteDialog(QDialog):
    """Dialog to create a quick note"""
    
    note_created = pyqtSignal(str, str)  # title, content
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva Nota Rápida")
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
    
    def setup_ui(self):
        container = QFrame(self)
        container.setGeometry(0, 0, 400, 300)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(30, 30, 35, 245);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("📝 Nueva Nota Rápida")
        header.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        header.setStyleSheet(f"color: rgb({COLORS['primary']}); background: transparent;")
        layout.addWidget(header)
        
        # Title input
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Título de la nota...")
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
        
        save_btn = QPushButton("💾 Guardar")
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
        title = QLabel(self.note.get('title', 'Sin título'))
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
        self.obsidian = ObsidianSync()
        
        self.setup_ui()
        self._load_notes()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        margin = 8 if self.compact else 16
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📝 Notas Rápidas")
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
    
    def _load_notes(self):
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
        
        # Sort by date
        all_notes.sort(
            key=lambda x: x.get('updated_at', x.get('modified', '')),
            reverse=True
        )
        
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
            empty = EmptyState("Sin notas", "📝")
            self.notes_layout.insertWidget(0, empty)
    
    def _add_note(self):
        """Show dialog to add new note"""
        dialog = QuickNoteDialog(self)
        dialog.note_created.connect(self._create_note)
        dialog.exec()
    
    def _create_note(self, title: str, content: str):
        """Create a new note"""
        # Save to Obsidian
        file_path = self.obsidian.create_quick_note(title, content)
        
        # Save to database
        db.add_quick_note(title, content, file_path)
        
        # Refresh
        self._load_notes()
    
    def _on_note_clicked(self, note: Dict):
        """Handle note click"""
        self.note_clicked.emit(note)
        
        # Open in default editor if has file path
        file_path = note.get('file_path')
        if file_path and os.path.exists(file_path):
            try:
                os.system(f'xdg-open "{file_path}" &')
            except:
                pass
    
    def refresh(self):
        """Refresh notes list"""
        self._load_notes()
