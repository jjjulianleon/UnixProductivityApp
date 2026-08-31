"""
Brightspace D2L Integration for Calendar Widget

IMPORTANTE: Brightspace D2L requiere credenciales institucionales.
La API de D2L usa OAuth2 o tokens de aplicación que tu universidad debe proporcionar.

OPCIONES DE INTEGRACIÓN:

1. API OFICIAL (Requiere acceso institucional):
   - Tu universidad debe habilitar API access
   - Necesitas App ID y App Key de tu administrador
   - Documentación: https://docs.valence.desire2learn.com/

2. WEB SCRAPING (Alternativa):
   - Menos estable pero no requiere permisos especiales
   - Usa tus credenciales normales de estudiante
   - Puede romperse si Brightspace actualiza su interfaz

3. ICS/ICAL (Recomendado):
   - Brightspace puede exportar calendarios en formato iCal
   - No requiere API access
   - Busca en Brightspace: Calendar > Subscribe
"""

import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

# Try to import icalendar for ICS parsing
try:
    from icalendar import Calendar
    HAS_ICALENDAR = True
except ImportError:
    HAS_ICALENDAR = False
    print("Para soporte ICS: pip install icalendar")

import requests


# ============== CONFIGURATION ==============
# Opción 1: URL del calendario ICS de Brightspace
# Para obtenerla: Brightspace > Calendar > Suscribirse/Subscribe > Copiar URL
BRIGHTSPACE_ICS_URL = ""

# Opción 2: Credenciales para web scraping (menos recomendado)
BRIGHTSPACE_URL = ""  # ej: "https://tu-universidad.brightspace.com"
BRIGHTSPACE_USERNAME = ""
BRIGHTSPACE_PASSWORD = ""

# Cache de deadlines
import sys
sys.path.insert(0, str(Path(__file__).parent))
from src.utils.system import config_dir, obsidian_vault

CACHE_FILE = str(config_dir("calendar_widget") / "brightspace_cache.json")
CACHE_DURATION_MINUTES = 30


class BrightspaceCalendar:
    """Fetch assignments and deadlines from Brightspace D2L"""
    
    def __init__(self):
        self.session = requests.Session()
        self.cache = self.load_cache()
        
    def load_cache(self) -> Dict:
        """Load cached deadlines"""
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                cache_time = datetime.fromisoformat(data.get('timestamp', '2000-01-01'))
                if datetime.now() - cache_time < timedelta(minutes=CACHE_DURATION_MINUTES):
                    return data
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return {}
        
    def save_cache(self, deadlines: List[Dict]):
        """Save deadlines to cache"""
        import os
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'deadlines': deadlines
            }, f)
            
    def get_deadlines_from_ics(self) -> List[Dict]:
        """
        Fetch deadlines from Brightspace ICS calendar feed.
        This is the recommended method as it doesn't require API access.
        """
        if not BRIGHTSPACE_ICS_URL:
            return []
            
        if not HAS_ICALENDAR:
            print("Instala icalendar: pip install icalendar")
            return []
            
        try:
            response = self.session.get(BRIGHTSPACE_ICS_URL, timeout=10)
            if not response.ok:
                print(f"Error fetching ICS: {response.status_code}")
                return []
                
            cal = Calendar.from_ical(response.content)
            deadlines = []
            now = datetime.now()
            
            for component in cal.walk():
                if component.name == "VEVENT":
                    summary = str(component.get('SUMMARY', ''))
                    dtstart = component.get('DTSTART')
                    dtend = component.get('DTEND')
                    description = str(component.get('DESCRIPTION', ''))
                    
                    if dtstart:
                        start_dt = dtstart.dt
                        if isinstance(start_dt, datetime):
                            if start_dt > now:
                                deadlines.append({
                                    'title': summary,
                                    'due_date': start_dt.isoformat(),
                                    'course': self.extract_course(summary, description),
                                    'type': self.detect_type(summary),
                                    'description': description[:200] if description else ''
                                })
                                
            # Sort by due date
            deadlines.sort(key=lambda x: x['due_date'])
            self.save_cache(deadlines)
            return deadlines[:20]  # Limit to 20 upcoming
            
        except Exception as e:
            print(f"Error parsing ICS: {e}")
            return []
            
    def extract_course(self, summary: str, description: str) -> str:
        """Try to extract course name from event"""
        # Common patterns in Brightspace
        patterns = [
            r'\[([^\]]+)\]',  # [Course Name]
            r'^([A-Z]{2,4}\s*\d{3,4})',  # ABC 123
            r'Course:\s*([^\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, summary + ' ' + description)
            if match:
                return match.group(1).strip()
        return "Universidad"
        
    def detect_type(self, summary: str) -> str:
        """Detect assignment type from summary"""
        summary_lower = summary.lower()
        
        if any(word in summary_lower for word in ['quiz', 'examen', 'test', 'exam']):
            return 'exam'
        elif any(word in summary_lower for word in ['tarea', 'assignment', 'homework', 'hw']):
            return 'assignment'
        elif any(word in summary_lower for word in ['proyecto', 'project']):
            return 'project'
        elif any(word in summary_lower for word in ['foro', 'discussion', 'forum']):
            return 'discussion'
        else:
            return 'other'
            
    def get_deadlines(self) -> List[Dict]:
        """Get all upcoming deadlines"""
        # Check cache first
        if self.cache.get('deadlines'):
            return self.cache['deadlines']
            
        # Try ICS method
        if BRIGHTSPACE_ICS_URL:
            return self.get_deadlines_from_ics()
            
        print("No hay configuración de Brightspace. Edita brightspace_integration.py")
        return []
        
    def get_week_deadlines(self) -> List[Dict]:
        """Get deadlines for the next 7 days"""
        deadlines = self.get_deadlines()
        week_end = datetime.now() + timedelta(days=7)
        
        return [
            d for d in deadlines
            if datetime.fromisoformat(d['due_date']) <= week_end
        ]


# ============== MANUAL ENTRY (Fallback) ==============
class ManualDeadlines:
    """
    Si no puedes conectar con Brightspace, puedes agregar deadlines manualmente.
    Esto se sincroniza con un archivo JSON que puedes editar.
    """
    
    DEADLINES_FILE = str(obsidian_vault() / "Universidad" / "8vo Semestre" / "deadlines.json")
    
    @classmethod
    def load(cls) -> List[Dict]:
        """Load manual deadlines from JSON file"""
        try:
            with open(cls.DEADLINES_FILE, 'r') as f:
                data = json.load(f)
                # Filter past deadlines
                now = datetime.now()
                return [
                    d for d in data.get('deadlines', [])
                    if datetime.fromisoformat(d['due_date']) > now
                ]
        except (FileNotFoundError, json.JSONDecodeError):
            # Create template file
            cls.create_template()
            return []
            
    @classmethod
    def create_template(cls):
        """Create a template deadlines file"""
        import os
        os.makedirs(os.path.dirname(cls.DEADLINES_FILE), exist_ok=True)
        
        template = {
            "deadlines": [
                {
                    "title": "Ejemplo: Tarea de Data Mining",
                    "course": "Data Mining",
                    "due_date": "2026-01-20T23:59:00",
                    "type": "assignment",
                    "description": "Descripción opcional"
                }
            ]
        }
        
        with open(cls.DEADLINES_FILE, 'w') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
            
        print(f"Archivo de deadlines creado: {cls.DEADLINES_FILE}")
        print("Edítalo para agregar tus deadlines manualmente.")


# ============== HOW TO GET BRIGHTSPACE ICS URL ==============
def print_instructions():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║          CÓMO OBTENER LA URL DEL CALENDARIO ICS                 ║
╚══════════════════════════════════════════════════════════════════╝

MÉTODO 1: Desde Brightspace Web

1. Inicia sesión en Brightspace de tu universidad
2. Ve al Calendario (Calendar)
3. Busca el botón "Suscribirse" o "Subscribe"
4. Copia la URL del feed (termina en .ics)
5. Pega la URL en BRIGHTSPACE_ICS_URL en este archivo

MÉTODO 2: Desde Brightspace Pulse (App móvil)

1. Abre la app Brightspace Pulse
2. Ve a Configuración > Calendario
3. Busca "Exportar calendario" o "Calendar feed"
4. Copia el enlace

MÉTODO 3: Usar deadlines manuales

Si no puedes obtener la URL, usa el archivo JSON:
""" + ManualDeadlines.DEADLINES_FILE + """

Edita ese archivo para agregar tus deadlines manualmente.

══════════════════════════════════════════════════════════════════
""")


# ============== TEST ==============
if __name__ == "__main__":
    if not BRIGHTSPACE_ICS_URL:
        print_instructions()
        
        # Create manual deadlines template
        ManualDeadlines.load()
    else:
        print("Obteniendo deadlines de Brightspace...")
        calendar = BrightspaceCalendar()
        deadlines = calendar.get_deadlines()
        
        if deadlines:
            print(f"\n📚 Próximos deadlines ({len(deadlines)}):\n")
            for dl in deadlines:
                due = datetime.fromisoformat(dl['due_date'])
                days_left = (due - datetime.now()).days
                
                emoji = "🔴" if days_left <= 2 else "🟡" if days_left <= 5 else "🟢"
                print(f"  {emoji} {dl['title']}")
                print(f"     {due.strftime('%d/%m/%Y %H:%M')} ({days_left} dias)")
                print(f"     📖 {dl['course']}")
                print()
        else:
            print("No se encontraron deadlines")
