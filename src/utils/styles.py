"""
Shared styles and theming for UniDex
"""

# Color palette
COLORS = {
    'primary': '66, 133, 244',
    'secondary': '81, 162, 218',
    'success': '52, 168, 83',
    'warning': '251, 188, 4',
    'danger': '234, 67, 53',
    'text_primary': '230, 230, 240',
    'text_secondary': '180, 180, 190',
    'text_muted': '140, 140, 150',
    'bg_dark': '25, 25, 30',
    'bg_medium': '35, 35, 40',
    'bg_light': '50, 50, 55',
    'border': '255, 255, 255, 0.1',
    
    # Category colors
    'personal': '66, 133, 244',
    'universidad': '52, 168, 83',
    'fedora': '81, 162, 218',
    
    # Priority colors
    'priority_high': '234, 67, 53',
    'priority_medium': '251, 188, 4',
    'priority_low': '52, 168, 83',
}

# Base stylesheet components
GLASSMORPHISM_BG = """
    background-color: rgba(25, 25, 30, 200);
"""

GLASSMORPHISM_WIDGET = """
    background-color: rgba(35, 35, 40, 180);
    border: none;
    border-radius: 12px;
"""

GLASSMORPHISM_CARD = """
    background-color: rgba(45, 45, 50, 150);
    border: none;
    border-radius: 8px;
"""

# Font family
FONT_FAMILY = "Source Code Pro"

# Complete stylesheets
def get_main_window_style():
    return f"""
        QMainWindow {{
            {GLASSMORPHISM_BG}
        }}
        QWidget {{
            font-family: "{FONT_FAMILY}";
            color: rgb({COLORS['text_primary']});
        }}
        {get_scrollbar_style()}
    """

def get_widget_style():
    return f"""
        QWidget {{
            font-family: "{FONT_FAMILY}";
            color: rgb({COLORS['text_primary']});
            background-color: rgba(30, 30, 35, 220);
        }}
    """

def get_button_style(variant='default'):
    colors = {
        'default': COLORS['text_secondary'],
        'primary': COLORS['primary'],
        'success': COLORS['success'],
        'danger': COLORS['danger'],
    }
    color = colors.get(variant, colors['default'])
    
    return f"""
        QPushButton {{
            background-color: rgba(255, 255, 255, 0.08);
            color: rgb({color});
            border: 1px solid rgba({color}, 0.3);
            border-radius: 6px;
            padding: 8px 16px;
            font-family: "{FONT_FAMILY}";
            font-size: 10px;
        }}
        QPushButton:hover {{
            background-color: rgba({color}, 0.15);
            border: 1px solid rgba({color}, 0.5);
        }}
        QPushButton:pressed {{
            background-color: rgba({color}, 0.25);
        }}
        QPushButton:disabled {{
            background-color: rgba(255, 255, 255, 0.03);
            color: rgb({COLORS['text_muted']});
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
    """

def get_nav_button_style():
    """Style for navigation arrows (< >) in calendar and schedule"""
    color = COLORS['text_secondary']
    return f"""
        QPushButton {{
            background-color: rgba(255, 255, 255, 0.08);
            color: rgb({color});
            border: 1px solid rgba({color}, 0.3);
            border-radius: 6px;
            padding: 0px;
            font-family: "DejaVu Sans", "Noto Sans", sans-serif;
            font-size: 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: rgba({color}, 0.15);
            border: 1px solid rgba({color}, 0.5);
        }}
        QPushButton:pressed {{
            background-color: rgba({color}, 0.25);
        }}
    """

def get_input_style():
    return f"""
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: rgba(20, 20, 25, 200);
            color: rgb({COLORS['text_primary']});
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            padding: 8px 12px;
            font-family: "{FONT_FAMILY}";
            font-size: 10px;
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid rgba({COLORS['primary']}, 0.5);
        }}
    """

def get_combobox_style():
    return f"""
        QComboBox {{
            background-color: rgb(25, 25, 30);
            color: rgb({COLORS['text_primary']});
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            padding: 8px 12px;
            padding-right: 30px;
            font-family: "{FONT_FAMILY}";
            font-size: 10px;
            min-width: 100px;
        }}
        QComboBox:hover {{
            border: 1px solid rgba({COLORS['primary']}, 0.4);
        }}
        QComboBox:focus {{
            border: 1px solid rgba({COLORS['primary']}, 0.6);
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: right center;
            width: 24px;
            border: none;
            background: transparent;
        }}
        QComboBox::down-arrow {{
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid rgb({COLORS['text_secondary']});
        }}
        QComboBox::down-arrow:hover {{
            border-top-color: rgb({COLORS['primary']});
        }}
        QComboBox QAbstractItemView {{
            background-color: rgb(30, 30, 35);
            color: rgb({COLORS['text_primary']});
            border: 1px solid rgb(50, 50, 55);
            selection-background-color: rgba({COLORS['primary']}, 0.4);
            selection-color: rgb({COLORS['text_primary']});
            padding: 4px;
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 8px 12px;
            min-height: 24px;
            background-color: rgb(30, 30, 35);
            color: rgb({COLORS['text_primary']});
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: rgba({COLORS['primary']}, 0.3);
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: rgba({COLORS['primary']}, 0.4);
        }}
        QListView {{
            background-color: rgb(30, 30, 35);
            color: rgb({COLORS['text_primary']});
            border: none;
            outline: none;
        }}
        QListView::item {{
            background-color: rgb(30, 30, 35);
            color: rgb({COLORS['text_primary']});
            padding: 8px 12px;
        }}
        QListView::item:hover {{
            background-color: rgba({COLORS['primary']}, 0.3);
        }}
        QListView::item:selected {{
            background-color: rgba({COLORS['primary']}, 0.4);
        }}
    """

def get_scrollbar_style():
    return f"""
        QScrollBar:vertical {{
            background: rgba(255, 255, 255, 0.03);
            width: 8px;
            border-radius: 4px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(255, 255, 255, 0.15);
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: rgba(255, 255, 255, 0.25);
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background: rgba(255, 255, 255, 0.03);
            height: 8px;
            border-radius: 4px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: rgba(255, 255, 255, 0.15);
            border-radius: 4px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: rgba(255, 255, 255, 0.25);
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
    """

def get_tab_style():
    return f"""
        QTabWidget::pane {{
            border: none;
            background: transparent;
        }}
        QTabBar::tab {{
            background-color: transparent;
            color: rgb({COLORS['text_muted']});
            border: none;
            border-radius: 8px;
            padding: 6px 14px;
            margin-right: 2px;
            font-family: "{FONT_FAMILY}";
            font-size: 10px;
        }}
        QTabBar::tab:selected {{
            background-color: rgba({COLORS['primary']}, 0.25);
            color: rgb({COLORS['primary']});
        }}
        QTabBar::tab:hover:!selected {{
            background-color: rgba(255, 255, 255, 0.08);
            color: rgb({COLORS['text_secondary']});
        }}
    """

def get_label_style(variant='default'):
    colors = {
        'default': COLORS['text_primary'],
        'secondary': COLORS['text_secondary'],
        'muted': COLORS['text_muted'],
        'primary': COLORS['primary'],
        'success': COLORS['success'],
        'danger': COLORS['danger'],
    }
    color = colors.get(variant, colors['default'])
    
    return f"""
        QLabel {{
            color: rgb({color});
            background: transparent;
            border: none;
            font-family: "{FONT_FAMILY}";
        }}
    """

def get_card_style(border_color=None):
    border = f"border-left: 3px solid rgba({border_color}, 200);" if border_color else ""
    return f"""
        QFrame {{
            {GLASSMORPHISM_CARD}
            {border}
        }}
    """

def get_dialog_style():
    return f"""
        QDialog {{
            {GLASSMORPHISM_BG}
        }}
        QDialog QWidget {{
            font-family: "{FONT_FAMILY}";
            color: rgb({COLORS['text_primary']});
        }}
    """

def get_scroll_area_style():
    return f"""
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        QScrollArea > QWidget > QWidget {{
            background: transparent;
        }}
        {get_scrollbar_style()}
    """

def get_calendar_style():
    return f"""
        QCalendarWidget {{
            background-color: rgba(30, 30, 35, 220);
            color: rgb({COLORS['text_primary']});
            font-family: "{FONT_FAMILY}";
        }}
        QCalendarWidget QToolButton {{
            color: rgb({COLORS['text_primary']});
            background: transparent;
            border: none;
            padding: 4px;
        }}
        QCalendarWidget QToolButton:hover {{
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }}
        QCalendarWidget QMenu {{
            background-color: rgba(35, 35, 40, 250);
            color: rgb({COLORS['text_primary']});
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        QCalendarWidget QSpinBox {{
            background-color: rgba(20, 20, 25, 200);
            color: rgb({COLORS['text_primary']});
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }}
        QCalendarWidget QAbstractItemView {{
            background-color: transparent;
            selection-background-color: rgba({COLORS['primary']}, 0.3);
            selection-color: rgb({COLORS['text_primary']});
        }}
        QCalendarWidget QAbstractItemView:enabled {{
            color: rgb({COLORS['text_primary']});
        }}
        QCalendarWidget QAbstractItemView:disabled {{
            color: rgb({COLORS['text_muted']});
        }}
    """

def get_progress_bar_style():
    return f"""
        QProgressBar {{
            background-color: rgba(255, 255, 255, 0.05);
            border: none;
            border-radius: 4px;
            height: 8px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: rgba({COLORS['primary']}, 200);
            border-radius: 4px;
        }}
    """


# Priority indicator colors
def get_priority_color(priority: str) -> str:
    priority_colors = {
        'alta': COLORS['priority_high'],
        'media': COLORS['priority_medium'],
        'baja': COLORS['priority_low'],
    }
    return priority_colors.get(priority.lower(), COLORS['priority_medium'])


# Category colors
def get_category_color(category: str) -> str:
    category_colors = {
        'Personal': COLORS['personal'],
        'Universidad': COLORS['universidad'],
        'Fedora': COLORS['fedora'],
    }
    return category_colors.get(category, COLORS['text_secondary'])


# Deadline urgency colors
def get_deadline_color(days_until: int) -> str:
    if days_until < 0:
        return COLORS['danger']
    elif days_until == 0:
        return COLORS['danger']
    elif days_until <= 3:
        return COLORS['warning']
    elif days_until <= 7:
        return COLORS['primary']
    else:
        return COLORS['success']


def get_menu_style():
    """Style for QMenu (context menus, dropdowns)"""
    return f"""
        QMenu {{
            background-color: rgba(35, 35, 40, 250);
            color: rgb({COLORS['text_primary']});
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 4px;
        }}
        QMenu::item {{
            padding: 8px 24px 8px 16px;
            border-radius: 4px;
            margin: 2px 4px;
        }}
        QMenu::item:selected {{
            background-color: rgba({COLORS['primary']}, 0.3);
            color: rgb({COLORS['primary']});
        }}
        QMenu::separator {{
            height: 1px;
            background-color: rgba(255, 255, 255, 0.1);
            margin: 4px 8px;
        }}
        QMenu::indicator {{
            width: 16px;
            height: 16px;
        }}
    """

def get_groupbox_style():
    return f"""
        QGroupBox {{
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            margin-top: 1.5em; /* leave space at the top for the title */
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding: 0 5px;
            color: rgb({COLORS['primary']});
            font-weight: bold;
        }}
    """
