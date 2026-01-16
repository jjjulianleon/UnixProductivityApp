# UnixProductivityApp

A productivity desktop application for Linux (KDE Plasma) with calendar, task management, Pomodoro timer, and Obsidian integration.

## Features

### Main Application
- 🏠 **Dashboard** - Today's overview with upcoming deadlines and tasks
- 📋 **Kanban Board** - Drag & drop task management (Pendiente → En Progreso → Completado)
- 📅 **Calendar** - Monthly calendar with deadline indicators + weekly schedule
- 📝 **Quick Notes** - Fast notes synced with Obsidian Rough Notes
- 🍅 **Pomodoro Timer** - 25/5 productivity timer with statistics
- 📈 **Statistics** - Weekly/monthly productivity tracking
- 🔔 **Notifications** - Desktop alerts for upcoming deadlines
- ⌨️ **Keyboard Shortcuts** - Ctrl+1-5 for navigation, Ctrl+N for new task

### Desktop Widget (520x320)
- Compact calendar with deadline dots
- Weekly schedule view
- Mini Kanban with pending/in-progress tasks
- Today/Tomorrow deadlines list
- Mini Pomodoro timer
- Quick note button
- Draggable, stays on desktop

### Obsidian Integration
- Bidirectional sync with markdown files
- Supports:
  - Personal: `~/Documents/Obsidian/Personal/Pendientes Personal.md`
  - Universidad: `~/Documents/Obsidian/Universidad/8vo Semestre/Pendientes Universidad.md`
  - Fedora: `~/Documents/Obsidian/Pendientes Fedora.md`
- Quick notes saved to: `~/Documents/Obsidian/Rough Notes/`

### Task Format
```markdown
- [ ] Task Title | Optional description [deadline: 2024-12-31] [priority: alta] (en progreso)
```

## Installation

### Requirements
- Python 3.10+
- PyQt6
- SQLite (included with Python)

### Install Dependencies
```bash
pip install PyQt6
```

### Run the Application

**Main App:**
```bash
python main_app.py
```

**Desktop Widget:**
```bash
python widget.py
```

## Project Structure
```
CalendarWidget/
├── main_app.py          # Main application entry
├── widget.py            # Desktop widget entry
├── src/
│   ├── core/
│   │   ├── database.py      # SQLite persistence
│   │   ├── task_manager.py  # Task CRUD operations
│   │   ├── obsidian_sync.py # Obsidian integration
│   │   └── notifications.py # Desktop notifications
│   ├── ui/
│   │   ├── widgets/
│   │   │   ├── calendar.py   # Monthly calendar
│   │   │   ├── schedule.py   # Weekly schedule
│   │   │   ├── kanban.py     # Kanban board
│   │   │   ├── pomodoro.py   # Pomodoro timer
│   │   │   ├── quick_notes.py
│   │   │   └── common.py     # Shared components
│   │   ├── dialogs/
│   │   │   └── task_dialogs.py
│   │   └── views/
│   │       ├── dashboard.py
│   │       ├── tasks_view.py
│   │       ├── calendar_view.py
│   │       └── statistics_view.py
│   └── utils/
│       ├── styles.py     # Glassmorphism theme
│       └── constants.py  # App configuration
└── assets/
    └── icons/
```

## Data Storage
- Database: `~/.local/share/UnixProductivityApp/data.db`
- All data persists across restarts

## Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| Ctrl+1 | Dashboard |
| Ctrl+2 | Tasks |
| Ctrl+3 | Calendar |
| Ctrl+4 | Notes |
| Ctrl+5 | Statistics |
| Ctrl+N | New Task |
| Ctrl+F | Focus Search |
| F5 | Refresh |

## KDE Plasma Widget Setup
1. Run `python widget.py`
2. Position the widget where you want it
3. (Optional) Add to autostart: `~/.config/autostart/`
4. Configure window rules in System Settings for "Dodge Windows" behavior

## License
MIT
