"""
Settings Dialog for UniDex
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QSpinBox, QTabWidget, QWidget, QGroupBox, QGridLayout,
    QCheckBox, QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.utils.styles import (
    COLORS, FONT_FAMILY, get_button_style, get_input_style, get_groupbox_style
)


class SettingsDialog(QDialog):
    """Settings configuration dialog"""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Configuracion")
        self.setFixedSize(700, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._load_settings()
        self.setup_ui()
    
    def _load_settings(self):
        """Load current settings from database or defaults"""
        from src.core.database import db
        self.settings = db.get_all_settings()
        
        # Set defaults if not exist
        if 'pomodoro_work' not in self.settings:
            self.settings['pomodoro_work'] = 25
        if 'pomodoro_short_break' not in self.settings:
            self.settings['pomodoro_short_break'] = 5
        if 'pomodoro_long_break' not in self.settings:
            self.settings['pomodoro_long_break'] = 15
        if 'pomodoro_sessions' not in self.settings:
            self.settings['pomodoro_sessions'] = 4
        if 'auto_sync_obsidian' not in self.settings:
            self.settings['auto_sync_obsidian'] = True
        if 'sync_interval' not in self.settings:
            self.settings['sync_interval'] = 5  # minutes
            
        # Load external configs
        try:
            from icloud_integration import ICloudSync
            self.icloud = ICloudSync()
            self.icloud_config = self.icloud.config
        except ImportError:
            self.icloud = None
            self.icloud_config = {}
            
        try:
            from ics_integration import ICSConfig
            self.ics_config = ICSConfig().config
        except ImportError:
            self.ics_config = {}
    
    def setup_ui(self):
        container = QFrame(self)
        container.setGeometry(0, 0, 700, 600)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(30, 30, 35, 248);
                border: none;
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header with close button
        header_layout = QHBoxLayout()
        
        header = QLabel("Configuracion")
        header.setFont(QFont(FONT_FAMILY, 16, QFont.Weight.Bold))
        header.setStyleSheet(f"color: rgb({COLORS['primary']}); background: transparent;")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("X")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: rgb({COLORS['text_muted']});
                border: none;
                border-radius: 15px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 100, 100, 0.3);
                color: rgb({COLORS['danger']});
            }}
        """)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Tab widget for sections
        tabs = QTabWidget()
        tabs.setStyleSheet(self._get_tab_style())
        
        # Pomodoro Tab
        pomodoro_tab = self._create_pomodoro_tab()
        tabs.addTab(pomodoro_tab, "Pomodoro")
        
        # Sync Tab
        sync_tab = self._create_sync_tab()
        tabs.addTab(sync_tab, "Sincronizacion")
        
        # Integrations Tab
        integrations_tab = self._create_integrations_tab()
        tabs.addTab(integrations_tab, "Integraciones")
        
        # General Tab
        general_tab = self._create_general_tab()
        tabs.addTab(general_tab, "General")
        
        layout.addWidget(tabs, 1)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFont(QFont(FONT_FAMILY, 10))
        cancel_btn.setStyleSheet(get_button_style())
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Guardar")
        save_btn.setFont(QFont(FONT_FAMILY, 10))
        save_btn.setStyleSheet(get_button_style('primary'))
        save_btn.setMinimumWidth(100)
        save_btn.clicked.connect(self._save_settings)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
    
    def _get_tab_style(self):
        return f"""
            QTabWidget::pane {{
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                background-color: rgba(20, 20, 25, 150);
                padding: 10px;
            }}
            QTabBar::tab {{
                background-color: rgba(255, 255, 255, 0.05);
                color: rgb({COLORS['text_secondary']});
                border: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 4px;
                font-family: "{FONT_FAMILY}";
                font-size: 10px;
            }}
            QTabBar::tab:selected {{
                background-color: rgba({COLORS['primary']}, 0.2);
                color: rgb({COLORS['primary']});
            }}
            QTabBar::tab:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
        """
    
    def _get_spinbox_style(self):
        return f"""
            QSpinBox {{
                background-color: rgba(20, 20, 25, 200);
                color: rgb({COLORS['text_primary']});
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 6px 10px;
                font-family: "{FONT_FAMILY}";
                font-size: 11px;
                min-width: 80px;
            }}
            QSpinBox:focus {{
                border: 1px solid rgba({COLORS['primary']}, 0.5);
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 20px;
                border: none;
                background: transparent;
            }}
            QSpinBox::up-arrow {{
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid rgb({COLORS['text_secondary']});
            }}
            QSpinBox::down-arrow {{
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid rgb({COLORS['text_secondary']});
            }}
            QSpinBox::up-arrow:hover, QSpinBox::down-arrow:hover {{
                border-bottom-color: rgb({COLORS['primary']});
                border-top-color: rgb({COLORS['primary']});
            }}
        """
    
    def _get_group_style(self):
        return f"""
            QGroupBox {{
                color: rgb({COLORS['text_secondary']});
                font-family: "{FONT_FAMILY}";
                font-size: 10px;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                margin-top: 12px;
                padding: 12px;
                padding-top: 20px;
                background: transparent;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                background: transparent;
            }}
        """
    
    def _get_checkbox_style(self):
        return f"""
            QCheckBox {{
                color: rgb({COLORS['text_primary']});
                font-family: "{FONT_FAMILY}";
                font-size: 10px;
                spacing: 8px;
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                background: rgba(20, 20, 25, 200);
            }}
            QCheckBox::indicator:checked {{
                background: rgba({COLORS['primary']}, 0.8);
                border: 1px solid rgba({COLORS['primary']}, 0.9);
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid rgba({COLORS['primary']}, 0.5);
            }}
        """
    
    def _create_pomodoro_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # Timer durations group
        durations_group = QGroupBox("Duracion de Sesiones")
        durations_group.setStyleSheet(self._get_group_style())
        durations_layout = QGridLayout(durations_group)
        durations_layout.setSpacing(12)
        
        # Work duration
        work_label = QLabel("Trabajo (minutos):")
        work_label.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        durations_layout.addWidget(work_label, 0, 0)
        
        self.work_spin = QSpinBox()
        self.work_spin.setRange(1, 120)
        self.work_spin.setValue(int(self.settings.get('pomodoro_work', 25)))
        self.work_spin.setStyleSheet(self._get_spinbox_style())
        durations_layout.addWidget(self.work_spin, 0, 1)
        
        # Short break
        short_label = QLabel("Descanso corto (minutos):")
        short_label.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        durations_layout.addWidget(short_label, 1, 0)
        
        self.short_break_spin = QSpinBox()
        self.short_break_spin.setRange(1, 60)
        self.short_break_spin.setValue(int(self.settings.get('pomodoro_short_break', 5)))
        self.short_break_spin.setStyleSheet(self._get_spinbox_style())
        durations_layout.addWidget(self.short_break_spin, 1, 1)
        
        # Long break
        long_label = QLabel("Descanso largo (minutos):")
        long_label.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        durations_layout.addWidget(long_label, 2, 0)
        
        self.long_break_spin = QSpinBox()
        self.long_break_spin.setRange(1, 120)
        self.long_break_spin.setValue(int(self.settings.get('pomodoro_long_break', 15)))
        self.long_break_spin.setStyleSheet(self._get_spinbox_style())
        durations_layout.addWidget(self.long_break_spin, 2, 1)
        
        # Sessions before long break
        sessions_label = QLabel("Sesiones antes de descanso largo:")
        sessions_label.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        durations_layout.addWidget(sessions_label, 3, 0)
        
        self.sessions_spin = QSpinBox()
        self.sessions_spin.setRange(1, 10)
        self.sessions_spin.setValue(int(self.settings.get('pomodoro_sessions', 4)))
        self.sessions_spin.setStyleSheet(self._get_spinbox_style())
        durations_layout.addWidget(self.sessions_spin, 3, 1)
        
        layout.addWidget(durations_group)
        
        # Info label
        info = QLabel("Los cambios se aplicaran en la proxima sesion de Pomodoro.")
        info.setStyleSheet(f"color: rgb({COLORS['text_muted']}); font-size: 9px; background: transparent;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        layout.addStretch()
        return tab
    
    def _create_sync_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # Obsidian sync group
        obsidian_group = QGroupBox("Sincronizacion con Obsidian")
        obsidian_group.setStyleSheet(self._get_group_style())
        obsidian_layout = QVBoxLayout(obsidian_group)
        obsidian_layout.setSpacing(12)
        
        self.auto_sync_check = QCheckBox("Sincronizar automaticamente al iniciar")
        self.auto_sync_check.setChecked(bool(self.settings.get('auto_sync_obsidian', True)))
        self.auto_sync_check.setStyleSheet(self._get_checkbox_style())
        obsidian_layout.addWidget(self.auto_sync_check)
        
        # Sync interval
        interval_layout = QHBoxLayout()
        interval_label = QLabel("Intervalo de sincronizacion (minutos):")
        interval_label.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        interval_layout.addWidget(interval_label)
        
        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setRange(1, 60)
        self.sync_interval_spin.setValue(int(self.settings.get('sync_interval', 5)))
        self.sync_interval_spin.setStyleSheet(self._get_spinbox_style())
        interval_layout.addWidget(self.sync_interval_spin)
        interval_layout.addStretch()
        obsidian_layout.addLayout(interval_layout)
        
        layout.addWidget(obsidian_group)
        
        # Paths info
        paths_info = QLabel(
            "Las rutas de sincronizacion de Obsidian estan configuradas en:\n"
            "src/utils/constants.py -> OBSIDIAN_VAULT_PATHS"
        )
        paths_info.setStyleSheet(f"color: rgb({COLORS['text_muted']}); font-size: 9px; background: transparent;")
        paths_info.setWordWrap(True)
        layout.addWidget(paths_info)
        
        layout.addStretch()
        layout.addWidget(paths_info)
        
        layout.addStretch()
        return tab
        
    def _create_integrations_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # iCloud Group
        icloud_group = QGroupBox("iCloud Calendar (iPhone)")
        icloud_group.setStyleSheet(get_groupbox_style())
        icloud_layout = QGridLayout(icloud_group)
        icloud_layout.setSpacing(10)
        
        self.icloud_enabled = QCheckBox("Habilitar sincronizacion")
        self.icloud_enabled.setChecked(self.icloud_config.get('enabled', False))
        self.icloud_enabled.setStyleSheet(self._get_checkbox_style())
        icloud_layout.addWidget(self.icloud_enabled, 0, 0, 1, 2)
        
        # Username
        user_lbl = QLabel("Apple ID:")
        user_lbl.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        icloud_layout.addWidget(user_lbl, 1, 0)
        
        self.icloud_user = QLineEdit(self.icloud_config.get('username', ''))
        self.icloud_user.setPlaceholderText("ejemplo@icloud.com")
        self.icloud_user.setStyleSheet(get_input_style())
        icloud_layout.addWidget(self.icloud_user, 1, 1)
        
        # Password
        pass_lbl = QLabel("App-Specific Password:")
        pass_lbl.setStyleSheet(f"color: rgb({COLORS['text_primary']}); background: transparent;")
        icloud_layout.addWidget(pass_lbl, 2, 0)
        
        self.icloud_pass = QLineEdit(self.icloud_config.get('password', ''))
        self.icloud_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.icloud_pass.setPlaceholderText("xxxx-xxxx-xxxx-xxxx")
        self.icloud_pass.setStyleSheet(get_input_style())
        icloud_layout.addWidget(self.icloud_pass, 2, 1)
        
        # Info
        info_lbl = QLabel("Debes generar una contrasena especifica en appleid.apple.com")
        info_lbl.setStyleSheet(f"color: rgb({COLORS['text_muted']}); font-size: 9px; background: transparent;")
        icloud_layout.addWidget(info_lbl, 3, 0, 1, 2)
        
        layout.addWidget(icloud_group)
        
        # Brightspace Group
        bs_group = QGroupBox("Brightspace D2L (Universidad)")
        bs_group.setStyleSheet(get_groupbox_style())
        bs_layout = QVBoxLayout(bs_group)
        bs_layout.setSpacing(10)
        
        bs_info = QLabel("Pega el enlace de suscripcion (ICS) para actualizaciones automaticas:")
        bs_info.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent; font-size: 9px;")
        bs_layout.addWidget(bs_info)
        
        current_bs_url = self.ics_config.get('brightspace', {}).get('url', '')
        self.bs_url = QLineEdit(current_bs_url)
        self.bs_url.setPlaceholderText("https://brightspace.../feed.ics")
        self.bs_url.setStyleSheet(get_input_style())
        bs_layout.addWidget(self.bs_url)
        
        layout.addWidget(bs_group)
        
        layout.addStretch()
        
        return tab
    
    def _create_general_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # App info
        info_group = QGroupBox("Informacion de la Aplicacion")
        info_group.setStyleSheet(self._get_group_style())
        info_layout = QVBoxLayout(info_group)
        
        app_name = QLabel("UniDex v1.0")
        app_name.setStyleSheet(f"color: rgb({COLORS['text_primary']}); font-weight: bold; background: transparent;")
        info_layout.addWidget(app_name)
        
        desc = QLabel("Aplicacion de productividad con integracion Obsidian,\nPomodoro, calendario y gestion de tareas.")
        desc.setStyleSheet(f"color: rgb({COLORS['text_secondary']}); background: transparent;")
        info_layout.addWidget(desc)
        
        layout.addWidget(info_group)
        
        # Data location
        data_group = QGroupBox("Ubicacion de Datos")
        data_group.setStyleSheet(self._get_group_style())
        data_layout = QVBoxLayout(data_group)
        
        data_path = QLabel("~/.local/share/UniDex/")
        data_path.setStyleSheet(f"color: rgb({COLORS['text_muted']}); font-family: monospace; background: transparent;")
        data_layout.addWidget(data_path)
        
        layout.addWidget(data_group)
        
        layout.addStretch()
        return tab
    
    def _save_settings(self):
        """Save all settings to database"""
        from src.core.database import db
        
        # Pomodoro settings
        db.set_setting('pomodoro_work', self.work_spin.value())
        db.set_setting('pomodoro_short_break', self.short_break_spin.value())
        db.set_setting('pomodoro_long_break', self.long_break_spin.value())
        db.set_setting('pomodoro_sessions', self.sessions_spin.value())
        
        # Sync settings
        db.set_setting('auto_sync_obsidian', 1 if self.auto_sync_check.isChecked() else 0)
        db.set_setting('sync_interval', self.sync_interval_spin.value())
        
        # Save iCloud settings
        if self.icloud:
            self.icloud.save_config(
                username=self.icloud_user.text(),
                password=self.icloud_pass.text(),
                enabled=self.icloud_enabled.isChecked()
            )
            
        # Save Brightspace settings
        if self.ics_config:
            from ics_integration import ICSConfig
            config_mgr = ICSConfig()
            bs_config = config_mgr.get('brightspace', {})
            new_url = self.bs_url.text().strip()
            
            bs_config['url'] = new_url
            if new_url:
                bs_config['source'] = 'url'
            else:
                bs_config['source'] = 'file'
                
            config_mgr.set('brightspace', bs_config)
        
        # Emit signal with new settings
        new_settings = {
            'pomodoro_work': self.work_spin.value(),
            'pomodoro_short_break': self.short_break_spin.value(),
            'pomodoro_long_break': self.long_break_spin.value(),
            'pomodoro_sessions': self.sessions_spin.value(),
            'auto_sync_obsidian': self.auto_sync_check.isChecked(),
            'sync_interval': self.sync_interval_spin.value()
        }
        self.settings_changed.emit(new_settings)
        
        self.accept()
