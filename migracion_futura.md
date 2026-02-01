# Migración Futura - UniDex

## Estado Actual

| Aspecto | Tecnología |
|---------|------------|
| Lenguaje | Python 3.13 |
| UI Principal | GTK4 + Libadwaita |
| UI Alternativa | PyQt6 |
| Base de Datos | SQLite3 |
| Plataforma | Linux (Fedora/GNOME/KDE) |

---

## Objetivo de Migración

Convertir la app en **multiplataforma** para soportar:

- Desktop: Windows, macOS, Linux
- Mobile: iOS, Android
- Web (opcional)

---

## Opciones de Migración

### 1. Flutter (Dart) - Recomendado

| Plataforma | Soporte |
|------------|---------|
| iOS | Nativo |
| Android | Nativo |
| Windows | Nativo |
| macOS | Nativo |
| Linux | Nativo |
| Web | Soportado |

**Ventajas:**
- Un solo código para 6 plataformas
- Rendimiento casi nativo
- UI moderna y personalizable
- Hot reload para desarrollo rápido
- SQLite funciona igual (paquete `sqflite`)
- Dart es fácil de aprender viniendo de Python

**Desventajas:**
- Requiere aprender Dart
- UI debe ser reimplementada desde cero

**Librerías equivalentes en Flutter:**
| Python | Flutter/Dart |
|--------|--------------|
| sqlite3 | sqflite |
| caldav | enough_mail / http |
| icalendar | icalendar_parser |
| requests | http / dio |

---

### 2. React Native + Electron

| Plataforma | Tecnología |
|------------|------------|
| Web | React |
| Desktop | Electron |
| Mobile | React Native |

**Ventajas:**
- JavaScript/TypeScript (lenguaje muy popular)
- Gran ecosistema de librerías
- Comunidad muy activa

**Desventajas:**
- Dos codebases separadas (React + React Native)
- Electron es pesado (~150MB por app)
- Rendimiento inferior a nativo

---

### 3. Tauri + React/Vue (Solo Desktop)

| Plataforma | Soporte |
|------------|---------|
| Windows | Nativo (~10MB) |
| macOS | Nativo |
| Linux | Nativo |
| Mobile | Tauri 2.0 (futuro) |

**Ventajas:**
- Muy ligero (usa WebView nativo, no Chromium)
- Backend en Rust (muy rápido)
- Frontend en cualquier framework web

**Desventajas:**
- Solo desktop por ahora
- Mobile aún no está listo

---

### 4. Kotlin Multiplatform + Compose

| Plataforma | Soporte |
|------------|---------|
| Android | Nativo |
| iOS | Nativo |
| Desktop | Nativo |
| Web | Experimental |

**Ventajas:**
- Rendimiento excelente
- Comparte lógica de negocio entre plataformas
- Compose UI es moderno y declarativo

**Desventajas:**
- Curva de aprendizaje mayor
- Ecosistema más pequeño que Flutter

---

## Componentes Reusables

| Componente | Reusable | Notas |
|------------|----------|-------|
| Esquema SQLite | 100% | SQLite es universal, mismo schema |
| Datos existentes | 100% | Se puede migrar la DB directamente |
| Lógica de sync | ~70% | Reescribir en nuevo lenguaje |
| Integraciones CalDAV/ICS | ~50% | Usar librerías equivalentes |
| UI/Widgets | 0% | Reimplementar completamente |

---

## Arquitectura Propuesta (Flutter)

```
┌─────────────────────────────────────────────────────────┐
│                    Flutter App                          │
├─────────────────────────────────────────────────────────┤
│  UI Layer (Widgets)                                     │
│  ├── Dashboard                                          │
│  ├── Tasks View                                         │
│  ├── Kanban Board                                       │
│  ├── Calendar View                                      │
│  ├── Schedule View                                      │
│  ├── Pomodoro Timer                                     │
│  └── Quick Notes                                        │
├─────────────────────────────────────────────────────────┤
│  State Management (Riverpod / BLoC)                     │
├─────────────────────────────────────────────────────────┤
│  Services Layer                                         │
│  ├── TaskService                                        │
│  ├── SyncService (CalDAV, ICS)                          │
│  ├── NotificationService                                │
│  └── BackupService                                      │
├─────────────────────────────────────────────────────────┤
│  Data Layer                                             │
│  ├── SQLite Database (sqflite)                          │
│  ├── Local Storage                                      │
│  └── API Clients                                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────┬────────┬────────┬────────┬────────┬────────┐
│  iOS   │Android │ macOS  │Windows │ Linux  │  Web   │
└────────┴────────┴────────┴────────┴────────┴────────┘
```

---

## Plan de Migración (Estimado)

### Fase 1: Setup y Core (2-3 semanas)
- [ ] Crear proyecto Flutter
- [ ] Configurar SQLite con schema existente
- [ ] Implementar modelos de datos (Task, Note, Event, etc.)
- [ ] Crear servicios básicos (CRUD de tareas)

### Fase 2: UI Principal (3-4 semanas)
- [ ] Dashboard
- [ ] Lista de tareas
- [ ] Kanban board
- [ ] Calendario
- [ ] Horario semanal

### Fase 3: Features Avanzados (2-3 semanas)
- [ ] Pomodoro timer
- [ ] Quick notes
- [ ] Estadísticas
- [ ] Notificaciones locales

### Fase 4: Integraciones (2-3 semanas)
- [ ] Sincronización CalDAV (iCloud)
- [ ] Importación ICS (Brightspace, Teams)
- [ ] Sincronización Obsidian (opcional)

### Fase 5: Polish y Deploy (1-2 semanas)
- [ ] Testing en todas las plataformas
- [ ] Optimización de rendimiento
- [ ] Publicar en App Store, Play Store, etc.

**Tiempo total estimado: 10-15 semanas**

---

## Recursos para Aprender Flutter

- [Flutter Official Docs](https://docs.flutter.dev/)
- [Dart Language Tour](https://dart.dev/language)
- [Flutter Codelabs](https://docs.flutter.dev/codelabs)
- [Riverpod (State Management)](https://riverpod.dev/)
- [sqflite (SQLite para Flutter)](https://pub.dev/packages/sqflite)

---

## Decisión

**Recomendación:** Migrar a **Flutter** por:

1. Una sola codebase para 6 plataformas
2. Rendimiento cercano a nativo
3. SQLite compatible (migración de datos fácil)
4. Comunidad activa y en crecimiento
5. Soporte oficial de Google

La versión actual en Python + GTK4 seguirá funcionando para Linux mientras se desarrolla la versión Flutter.
