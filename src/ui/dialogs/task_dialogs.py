"""
Task-related dialogs
"""
from datetime import datetime
from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QFrame, QDateEdit,
    QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont

from src.utils.styles import (
    COLORS, FONT_FAMILY, get_button_style, get_input_style,
    get_combobox_style, get_scroll_area_style, get_category_color,
    get_priority_color, get_deadline_color
)
from src.utils.constants import TASK_CATEGORIES, TASK_PRIORITIES


class AddTaskDialog(QDialog):
    """Dialog to add a new task"""
    
    task_created = pyqtSignal(dict)
    
    def __init__(self, default_status: str = "pendiente", 
                 default_category: str = None, parent=None):
        super().__init__(parent)
        self.default_status = default_status
        self.default_category = default_category
        
        self.setWindowTitle("Nueva Tarea")
        self.setFixedSize(400, 420)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
    
    def setup_ui(self):
        container = QFrame(self)
        container.setGeometry(0, 0, 400, 420)
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
        header = QLabel("Nueva Tarea")
        header.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        header.setStyleSheet(f"color: rgb({COLORS['primary']}); background: transparent;")
        layout.addWidget(header)
        
        # Title
        title_label = QLabel("Titulo *")
        title_label.setFont(QFont(FONT_FAMILY, 9))
        title_label.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
        layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Titulo de la tarea...")
        self.title_input.setFont(QFont(FONT_FAMILY, 10))
        self.title_input.setStyleSheet(get_input_style())
        layout.addWidget(self.title_input)
        
        # Description
        desc_label = QLabel("Descripcion")
        desc_label.setFont(QFont(FONT_FAMILY, 9))
        desc_label.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
        layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Descripcion opcional...")
        self.desc_input.setFont(QFont(FONT_FAMILY, 10))
        self.desc_input.setStyleSheet(get_input_style())
        self.desc_input.setMaximumHeight(80)
        layout.addWidget(self.desc_input)
        
        # Category and Priority row
        row1 = QHBoxLayout()
        
        # Category
        cat_container = QVBoxLayout()
        cat_label = QLabel("Categoria")
        cat_label.setFont(QFont(FONT_FAMILY, 9))
        cat_label.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
        cat_container.addWidget(cat_label)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(TASK_CATEGORIES)
        if self.default_category:
            idx = self.category_combo.findText(self.default_category)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
        self.category_combo.setFont(QFont(FONT_FAMILY, 10))
        self.category_combo.setStyleSheet(get_combobox_style())
        cat_container.addWidget(self.category_combo)
        row1.addLayout(cat_container)
        
        # Priority
        pri_container = QVBoxLayout()
        pri_label = QLabel("Prioridad")
        pri_label.setFont(QFont(FONT_FAMILY, 9))
        pri_label.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
        pri_container.addWidget(pri_label)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems([p.capitalize() for p in TASK_PRIORITIES])
        self.priority_combo.setCurrentIndex(1)  # media
        self.priority_combo.setFont(QFont(FONT_FAMILY, 10))
        self.priority_combo.setStyleSheet(get_combobox_style())
        pri_container.addWidget(self.priority_combo)
        row1.addLayout(pri_container)
        
        layout.addLayout(row1)
        
        # Deadline
        deadline_label = QLabel("Fecha Limite")
        deadline_label.setFont(QFont(FONT_FAMILY, 9))
        deadline_label.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
        layout.addWidget(deadline_label)
        
        deadline_row = QHBoxLayout()
        
        self.deadline_check = QPushButton("Sin fecha limite")
        self.deadline_check.setCheckable(True)
        self.deadline_check.setChecked(True)
        self.deadline_check.setFont(QFont(FONT_FAMILY, 9))
        self.deadline_check.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.05);
                color: rgb({COLORS['text_muted']});
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:checked {{
                background-color: rgba({COLORS['primary']}, 0.2);
                color: rgb({COLORS['primary']});
                border: 1px solid rgba({COLORS['primary']}, 0.3);
            }}
        """)
        self.deadline_check.clicked.connect(self._toggle_deadline)
        deadline_row.addWidget(self.deadline_check)
        
        self.deadline_date = QDateEdit()
        self.deadline_date.setDate(QDate.currentDate().addDays(7))
        self.deadline_date.setCalendarPopup(True)
        self.deadline_date.setFont(QFont(FONT_FAMILY, 10))
        self.deadline_date.setStyleSheet(get_input_style())
        self.deadline_date.setVisible(False)
        deadline_row.addWidget(self.deadline_date)
        
        deadline_row.addStretch()
        layout.addLayout(deadline_row)
        
        layout.addStretch()
        
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
    
    def _toggle_deadline(self):
        has_deadline = not self.deadline_check.isChecked()
        self.deadline_date.setVisible(has_deadline)
        self.deadline_check.setText("Sin fecha limite" if self.deadline_check.isChecked() else "Con fecha limite")
    
    def _save(self):
        title = self.title_input.text().strip()
        if not title:
            return
        
        task = {
            'title': title,
            'description': self.desc_input.toPlainText().strip(),
            'category': self.category_combo.currentText(),
            'priority': self.priority_combo.currentText().lower(),
            'status': self.default_status,
            'deadline': None
        }
        
        if not self.deadline_check.isChecked():
            task['deadline'] = self.deadline_date.date().toString("yyyy-MM-dd")
        
        self.task_created.emit(task)
        self.accept()


class TaskDetailDialog(QDialog):
    """Dialog to view task details"""
    
    task_updated = pyqtSignal(dict)
    task_deleted = pyqtSignal(int)
    
    def __init__(self, task: Dict, parent=None):
        super().__init__(parent)
        self.task = task
        
        self.setWindowTitle("Detalle de Tarea")
        self.setFixedSize(380, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
    
    def setup_ui(self):
        container = QFrame(self)
        container.setGeometry(0, 0, 380, 400)
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
        
        # Category indicator
        category = self.task.get('category', '')
        color = get_category_color(category)
        
        cat_label = QLabel(f"[{category}]")
        cat_label.setFont(QFont(FONT_FAMILY, 9))
        cat_label.setStyleSheet(f"color: rgb({color}); background: transparent;")
        layout.addWidget(cat_label)
        
        # Title
        title = self.task.get('title', '')
        title_label = QLabel(title)
        title_label.setFont(QFont(FONT_FAMILY, 14, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Description
        desc = self.task.get('description', '')
        if desc:
            desc_scroll = QScrollArea()
            desc_scroll.setWidgetResizable(True)
            desc_scroll.setFrameShape(QFrame.Shape.NoFrame)
            desc_scroll.setStyleSheet(get_scroll_area_style())
            desc_scroll.setMaximumHeight(100)
            
            desc_widget = QWidget()
            desc_layout = QVBoxLayout(desc_widget)
            desc_layout.setContentsMargins(0, 0, 0, 0)
            
            desc_label = QLabel(desc)
            desc_label.setFont(QFont(FONT_FAMILY, 10))
            desc_label.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
            desc_label.setWordWrap(True)
            desc_label.setOpenExternalLinks(True)
            desc_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.LinksAccessibleByMouse)
            desc_layout.addWidget(desc_label)
            
            desc_scroll.setWidget(desc_widget)
            layout.addWidget(desc_scroll)
        
        # Info grid
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(50, 50, 55, 100);
                border-radius: 8px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.setSpacing(8)
        
        # Status
        status = self.task.get('status', 'pendiente')
        status_colors = {
            'pendiente': COLORS['warning'],
            'en progreso': COLORS['primary'],
            'completado': COLORS['success']
        }
        status_color = status_colors.get(status, COLORS['text_secondary'])
        
        status_row = QHBoxLayout()
        status_row.addWidget(self._info_label("Estado:"))
        status_val = QLabel(status.capitalize())
        status_val.setFont(QFont(FONT_FAMILY, 10))
        status_val.setStyleSheet(f"color: rgb({status_color}); background: transparent;")
        status_row.addWidget(status_val)
        status_row.addStretch()
        info_layout.addLayout(status_row)
        
        # Priority
        priority = self.task.get('priority', 'media')
        priority_color = get_priority_color(priority)
        
        priority_row = QHBoxLayout()
        priority_row.addWidget(self._info_label("Prioridad:"))
        priority_val = QLabel(f"[{priority.upper()[0]}] {priority.capitalize()}")
        priority_val.setFont(QFont(FONT_FAMILY, 10))
        priority_val.setStyleSheet(f"color: rgb({priority_color}); background: transparent;")
        priority_row.addWidget(priority_val)
        priority_row.addStretch()
        info_layout.addLayout(priority_row)
        
        # Deadline
        deadline = self.task.get('deadline')
        if deadline:
            try:
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
                days_until = (deadline_date - datetime.now().date()).days
                deadline_color = get_deadline_color(days_until)
                
                if days_until < 0:
                    deadline_text = f"VENCIDO ({deadline_date.strftime('%d/%m/%Y')})"
                elif days_until == 0:
                    deadline_text = "Hoy"
                elif days_until == 1:
                    deadline_text = "Manana"
                else:
                    deadline_text = f"{deadline_date.strftime('%d/%m/%Y')} ({days_until} dias)"
                
                deadline_row = QHBoxLayout()
                deadline_row.addWidget(self._info_label("Deadline:"))
                deadline_val = QLabel(deadline_text)
                deadline_val.setFont(QFont(FONT_FAMILY, 10))
                deadline_val.setStyleSheet(f"color: rgb({deadline_color}); background: transparent;")
                deadline_row.addWidget(deadline_val)
                deadline_row.addStretch()
                info_layout.addLayout(deadline_row)
            except ValueError:
                pass
        
        layout.addWidget(info_frame)
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        if self.task.get('status') != 'completado':
            complete_btn = QPushButton("Completar")
            complete_btn.setFont(QFont(FONT_FAMILY, 9))
            complete_btn.setStyleSheet(get_button_style('success'))
            complete_btn.clicked.connect(self._complete_task)
            btn_layout.addWidget(complete_btn)
        
        delete_btn = QPushButton("Eliminar")
        delete_btn.setFont(QFont(FONT_FAMILY, 9))
        delete_btn.setStyleSheet(get_button_style('danger'))
        delete_btn.setMinimumWidth(85)
        delete_btn.clicked.connect(self._delete_task)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Cerrar")
        close_btn.setFont(QFont(FONT_FAMILY, 9))
        close_btn.setStyleSheet(get_button_style())
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _info_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setFont(QFont(FONT_FAMILY, 9))
        label.setStyleSheet(f"color: rgb({COLORS['text_muted']}); background: transparent;")
        label.setFixedWidth(70)
        return label
    
    def _complete_task(self):
        self.task['status'] = 'completado'
        self.task_updated.emit(self.task)
        self.accept()
    
    def _delete_task(self):
        task_id = self.task.get('id')
        if task_id:
            self.task_deleted.emit(task_id)
        self.accept()


class DeadlineTasksDialog(QDialog):
    """Dialog showing tasks for a specific deadline"""
    
    task_clicked = pyqtSignal(dict)
    
    def __init__(self, tasks: list, parent=None):
        super().__init__(parent)
        self.tasks = tasks
        
        self.setWindowTitle("Tareas con Deadline")
        self.setFixedSize(350, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
    
    def setup_ui(self):
        container = QFrame(self)
        container.setGeometry(0, 0, 350, 400)
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
        if self.tasks:
            deadline = self.tasks[0].get('deadline', '')
            if deadline:
                try:
                    deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                    header_text = f"Tareas - {deadline_date.strftime('%d/%m/%Y')}"
                except:
                    header_text = "Tareas"
            else:
                header_text = "Tareas"
        else:
            header_text = "Tareas"
        
        header = QLabel(header_text)
        header.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        header.setStyleSheet(f"color: rgb({COLORS['primary']}); background: transparent;")
        layout.addWidget(header)
        
        # Tasks scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(get_scroll_area_style())
        
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        tasks_layout.setContentsMargins(0, 0, 4, 0)
        tasks_layout.setSpacing(8)
        
        for task in self.tasks:
            card = self._create_task_card(task)
            tasks_layout.addWidget(card)
        
        tasks_layout.addStretch()
        scroll.setWidget(tasks_widget)
        layout.addWidget(scroll, 1)
        
        # Close button
        close_btn = QPushButton("Cerrar")
        close_btn.setFont(QFont(FONT_FAMILY, 9))
        close_btn.setStyleSheet(get_button_style())
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def _create_task_card(self, task: Dict) -> QFrame:
        category = task.get('category', '')
        color = get_category_color(category)
        
        card = QFrame()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(50, 50, 55, 150);
                border-left: 3px solid rgba({color}, 200);
                border-radius: 6px;
            }}
            QFrame:hover {{
                background-color: rgba(60, 60, 65, 180);
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        title = QLabel(task.get('title', ''))
        title.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        title.setStyleSheet(f"color: rgb({color}); background: transparent;")
        title.setWordWrap(True)
        layout.addWidget(title)
        
        desc = task.get('description', '')
        if desc:
            desc_label = QLabel(desc[:60] + "..." if len(desc) > 60 else desc)
            desc_label.setFont(QFont(FONT_FAMILY, 9))
            desc_label.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
            layout.addWidget(desc_label)
        
        # Make clickable
        card.mousePressEvent = lambda e, t=task: self._on_task_clicked(t)
        
        return card
    
    def _on_task_clicked(self, task: Dict):
        self.task_clicked.emit(task)
        dialog = TaskDetailDialog(task, self)
        dialog.exec()


class ScheduleEventDialog(QDialog):
    """Dialog to add/edit a schedule event"""
    
    event_saved = pyqtSignal(dict)
    event_deleted = pyqtSignal(int)
    
    def __init__(self, day_index: int = 0, hour: int = 9, 
                 event: Dict = None, parent=None):
        super().__init__(parent)
        self.day_index = day_index
        self.hour = hour
        self.event = event
        self.is_edit = event is not None
        
        self.setWindowTitle("Editar Evento" if self.is_edit else "Nuevo Evento")
        self.setFixedSize(380, 350)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
    
    def setup_ui(self):
        container = QFrame(self)
        container.setGeometry(0, 0, 380, 350)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(30, 30, 35, 245);
                border: none;
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("Editar Evento" if self.is_edit else "Nuevo Evento")
        header.setFont(QFont(FONT_FAMILY, 14, QFont.Weight.Bold))
        header.setStyleSheet(f"color: rgb({COLORS['primary']}); background: transparent;")
        layout.addWidget(header)
        
        # Source Selection (only for new events)
        if not self.is_edit:
            source_layout = QHBoxLayout()
            source_lbl = QLabel("Guardar en:")
            source_lbl.setFont(QFont(FONT_FAMILY, 9))
            source_lbl.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
            source_layout.addWidget(source_lbl)
            
            self.source_combo = QComboBox()
            self.source_combo.addItems(["Local (Semanal Recurrente)", "Local (Fecha Unica)", "iCloud (Fecha Unica)"])
            self.source_combo.setFont(QFont(FONT_FAMILY, 10))
            self.source_combo.setStyleSheet(get_combobox_style())
            self.source_combo.currentIndexChanged.connect(self._toggle_source)
            source_layout.addWidget(self.source_combo)
            layout.addLayout(source_layout)
        
        # Title input
        title_label = QLabel("Titulo")
        title_label.setFont(QFont(FONT_FAMILY, 9))
        title_label.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
        layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setFont(QFont(FONT_FAMILY, 10))
        self.title_input.setStyleSheet(get_input_style())
        self.title_input.setPlaceholderText("Nombre del evento")
        if self.event:
            self.title_input.setText(self.event.get('title', ''))
        layout.addWidget(self.title_input)
        
        # Date/Day selection
        self.day_label = QLabel("Dia de la semana")
        self.day_label.setFont(QFont(FONT_FAMILY, 9))
        self.day_label.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
        layout.addWidget(self.day_label)
        
        self.day_combo = QComboBox()
        self.day_combo.setFont(QFont(FONT_FAMILY, 10))
        self.day_combo.setStyleSheet(get_combobox_style())
        days = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
        self.day_combo.addItems(days)
        if self.event:
            self.day_combo.setCurrentIndex(self.event.get('day_of_week', 0))
        else:
            self.day_combo.setCurrentIndex(self.day_index)
        layout.addWidget(self.day_combo)
        
        # Specific Date (for iCloud)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setFont(QFont(FONT_FAMILY, 10))
        self.date_edit.setStyleSheet(get_input_style())
        self.date_edit.setVisible(False)
        layout.addWidget(self.date_edit)
        
        # Time row
        time_layout = QHBoxLayout()
        
        # Start time
        start_layout = QVBoxLayout()
        start_label = QLabel("Hora inicio")
        start_label.setFont(QFont(FONT_FAMILY, 9))
        start_label.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
        start_layout.addWidget(start_label)
        
        self.start_time = QComboBox()
        self.start_time.setFont(QFont(FONT_FAMILY, 10))
        self.start_time.setStyleSheet(get_combobox_style())
        for h in range(6, 23):
            self.start_time.addItem(f"{h:02d}:00")
        if self.event:
            start_h = int(self.event.get('start_time', '09:00').split(':')[0])
            self.start_time.setCurrentIndex(max(0, start_h - 6))
        else:
            self.start_time.setCurrentIndex(max(0, self.hour - 6))
        start_layout.addWidget(self.start_time)
        time_layout.addLayout(start_layout)
        
        # End time
        end_layout = QVBoxLayout()
        end_label = QLabel("Hora fin")
        end_label.setFont(QFont(FONT_FAMILY, 9))
        end_label.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
        end_layout.addWidget(end_label)
        
        self.end_time = QComboBox()
        self.end_time.setFont(QFont(FONT_FAMILY, 10))
        self.end_time.setStyleSheet(get_combobox_style())
        for h in range(6, 23):
            self.end_time.addItem(f"{h:02d}:00")
        if self.event:
            end_h = int(self.event.get('end_time', '10:00').split(':')[0])
            self.end_time.setCurrentIndex(max(0, end_h - 6))
        else:
            self.end_time.setCurrentIndex(max(0, self.hour - 5))
        end_layout.addWidget(self.end_time)
        time_layout.addLayout(end_layout)
        
        layout.addLayout(time_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        if self.is_edit:
            delete_btn = QPushButton("Eliminar")
            delete_btn.setFont(QFont(FONT_FAMILY, 9))
            delete_btn.setStyleSheet(get_button_style('danger'))
            delete_btn.clicked.connect(self._delete)
            buttons_layout.addWidget(delete_btn)
        
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFont(QFont(FONT_FAMILY, 9))
        cancel_btn.setStyleSheet(get_button_style())
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Guardar")
        save_btn.setFont(QFont(FONT_FAMILY, 9))
        save_btn.setStyleSheet(get_button_style('primary'))
        save_btn.clicked.connect(self._save)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
    
    def _toggle_source(self):
        # 0 = Local recurring, 1 = Local one-time, 2 = iCloud
        source_index = self.source_combo.currentIndex()
        is_one_time = source_index in (1, 2)
        self.day_label.setText("Fecha" if is_one_time else "Dia de la semana")
        self.day_combo.setVisible(not is_one_time)
        self.date_edit.setVisible(is_one_time)
        
    def _save(self):
        title = self.title_input.text().strip()
        if not title:
            return

        event_data = {
            'title': title,
            'start_time': self.start_time.currentText(),
            'end_time': self.end_time.currentText(),
            'color': COLORS['primary']
        }

        if not self.is_edit:
            source_index = self.source_combo.currentIndex()
            if source_index == 2:
                # iCloud Event
                event_data['target'] = 'icloud'
                event_data['date'] = self.date_edit.date().toString("yyyy-MM-dd")
            elif source_index == 1:
                # Local one-time event
                event_data['target'] = 'local'
                selected_date = self.date_edit.date()
                event_data['day_of_week'] = selected_date.dayOfWeek() - 1  # Qt: 1=Mon, we need 0=Mon
                event_data['event_date'] = selected_date.toString("yyyy-MM-dd")
                event_data['recurring'] = 0
            else:
                # Local recurring event
                event_data['target'] = 'local'
                event_data['day_of_week'] = self.day_combo.currentIndex()
                event_data['recurring'] = 1
        else:
            # Editing existing event
            event_data['target'] = 'local'
            event_data['day_of_week'] = self.day_combo.currentIndex()

        if self.event:
            event_data['id'] = self.event.get('id')

        self.event_saved.emit(event_data)
        self.accept()
    
    def _delete(self):
        if self.event:
            self.event_deleted.emit(self.event.get('id'))
            self.accept()
