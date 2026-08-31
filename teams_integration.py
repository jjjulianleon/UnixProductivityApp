"""
Microsoft Teams Calendar Integration via Graph API

SETUP INSTRUCTIONS:
1. Go to https://portal.azure.com
2. Navigate to Azure Active Directory > App registrations
3. Click "New registration"
4. Name: "Calendar Widget"
5. Supported account types: "Accounts in this organizational directory only"
6. Redirect URI: "http://localhost:8000/callback" (Web)
7. After creation, note the "Application (client) ID"
8. Go to "Certificates & secrets" > New client secret
9. Go to "API permissions" > Add permission > Microsoft Graph > Delegated
10. Add: Calendars.Read, User.Read
11. Click "Grant admin consent" (or ask your IT admin)

Fill in the values below after setup.
"""

import json
import webbrowser
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse
from typing import Optional, List, Dict
import requests

# ============== CONFIGURATION ==============
# Fill these after registering your app in Azure
CLIENT_ID = ""  # Your Application (client) ID
CLIENT_SECRET = ""  # Your client secret (optional for public clients)
TENANT_ID = ""  # Your tenant ID or "common"
REDIRECT_URI = "http://localhost:8000/callback"
SCOPES = ["Calendars.Read", "User.Read"]

# Token storage
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from src.utils.system import config_dir

TOKEN_FILE = str(config_dir("calendar_widget") / "ms_token.json")


class MSGraphAuth:
    """Handle Microsoft Graph OAuth2 authentication"""
    
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None
        self.load_token()
        
    def load_token(self):
        """Load saved token from file"""
        try:
            import os
            os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
            with open(TOKEN_FILE, 'r') as f:
                data = json.load(f)
                self.access_token = data.get('access_token')
                self.refresh_token = data.get('refresh_token')
                self.expires_at = datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None
        except (FileNotFoundError, json.JSONDecodeError):
            pass
            
    def save_token(self):
        """Save token to file"""
        import os
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, 'w') as f:
            json.dump({
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None
            }, f)
            
    def is_valid(self) -> bool:
        """Check if current token is valid"""
        if not self.access_token or not self.expires_at:
            return False
        return datetime.now() < self.expires_at - timedelta(minutes=5)
        
    def get_auth_url(self) -> str:
        """Generate OAuth2 authorization URL"""
        params = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'scope': ' '.join(SCOPES),
            'response_mode': 'query'
        }
        base_url = f"https://login.microsoftonline.com/{TENANT_ID or 'common'}/oauth2/v2.0/authorize"
        return f"{base_url}?{urlencode(params)}"
        
    def exchange_code(self, code: str) -> bool:
        """Exchange authorization code for tokens"""
        url = f"https://login.microsoftonline.com/{TENANT_ID or 'common'}/oauth2/v2.0/token"
        data = {
            'client_id': CLIENT_ID,
            'scope': ' '.join(SCOPES),
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        if CLIENT_SECRET:
            data['client_secret'] = CLIENT_SECRET
            
        response = requests.post(url, data=data)
        if response.ok:
            tokens = response.json()
            self.access_token = tokens['access_token']
            self.refresh_token = tokens.get('refresh_token')
            self.expires_at = datetime.now() + timedelta(seconds=tokens['expires_in'])
            self.save_token()
            return True
        print(f"Token exchange failed: {response.text}")
        return False
        
    def refresh_access_token(self) -> bool:
        """Refresh the access token"""
        if not self.refresh_token:
            return False
            
        url = f"https://login.microsoftonline.com/{TENANT_ID or 'common'}/oauth2/v2.0/token"
        data = {
            'client_id': CLIENT_ID,
            'scope': ' '.join(SCOPES),
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        if CLIENT_SECRET:
            data['client_secret'] = CLIENT_SECRET
            
        response = requests.post(url, data=data)
        if response.ok:
            tokens = response.json()
            self.access_token = tokens['access_token']
            self.refresh_token = tokens.get('refresh_token', self.refresh_token)
            self.expires_at = datetime.now() + timedelta(seconds=tokens['expires_in'])
            self.save_token()
            return True
        return False
        
    def authenticate_interactive(self) -> bool:
        """Start interactive OAuth flow"""
        auth_code = [None]
        
        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                query = parse_qs(urlparse(self.path).query)
                if 'code' in query:
                    auth_code[0] = query['code'][0]
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"""
                        <html><body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
                        <h1>Autenticacion exitosa!</h1>
                        <p>Puedes cerrar esta ventana.</p>
                        </body></html>
                    """)
                else:
                    self.send_response(400)
                    self.end_headers()
                    
            def log_message(self, format, *args):
                pass
                
        # Start local server
        server = HTTPServer(('localhost', 8000), CallbackHandler)
        server.timeout = 120
        
        # Open browser
        webbrowser.open(self.get_auth_url())
        print("Abriendo navegador para autenticación...")
        print("Esperando respuesta...")
        
        # Wait for callback
        server.handle_request()
        server.server_close()
        
        if auth_code[0]:
            return self.exchange_code(auth_code[0])
        return False


class TeamsCalendar:
    """Fetch calendar events from Microsoft Teams/Outlook"""
    
    def __init__(self):
        self.auth = MSGraphAuth()
        
    def ensure_auth(self) -> bool:
        """Ensure we have valid authentication"""
        if not CLIENT_ID:
            print("ERROR: CLIENT_ID no configurado. Edita teams_integration.py")
            return False
            
        if self.auth.is_valid():
            return True
            
        if self.auth.refresh_token and self.auth.refresh_access_token():
            return True
            
        return self.auth.authenticate_interactive()
        
    def get_events(self, days_ahead: int = 7) -> List[Dict]:
        """Fetch calendar events for the next N days"""
        if not self.ensure_auth():
            return []
            
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=days_ahead)
        
        url = "https://graph.microsoft.com/v1.0/me/calendarView"
        params = {
            'startDateTime': start.isoformat() + 'Z',
            'endDateTime': end.isoformat() + 'Z',
            '$orderby': 'start/dateTime',
            '$top': 50
        }
        headers = {
            'Authorization': f'Bearer {self.auth.access_token}',
            'Prefer': 'outlook.timezone="America/Mexico_City"'
        }
        
        response = requests.get(url, params=params, headers=headers)
        if response.ok:
            data = response.json()
            events = []
            for event in data.get('value', []):
                events.append({
                    'id': event['id'],
                    'subject': event['subject'],
                    'start': event['start']['dateTime'],
                    'end': event['end']['dateTime'],
                    'location': event.get('location', {}).get('displayName', ''),
                    'is_online': event.get('isOnlineMeeting', False),
                    'online_url': event.get('onlineMeeting', {}).get('joinUrl', ''),
                    'organizer': event.get('organizer', {}).get('emailAddress', {}).get('name', '')
                })
            return events
        else:
            print(f"Error fetching events: {response.status_code}")
            return []
            
    def get_today_events(self) -> List[Dict]:
        """Get events for today only"""
        return self.get_events(days_ahead=1)


# ============== TEST ==============
if __name__ == "__main__":
    if not CLIENT_ID:
        print("=" * 60)
        print("CONFIGURACIÓN REQUERIDA")
        print("=" * 60)
        print("""
Para usar la integración con Teams:

1. Ve a https://portal.azure.com
2. Azure Active Directory > App registrations > New registration
3. Nombre: "Calendar Widget"
4. Redirect URI: http://localhost:8000/callback (Web)
5. Copia el "Application (client) ID"
6. API permissions > Add > Microsoft Graph > Delegars
   - Calendars.Read
   - User.Read
7. Grant admin consent

Luego edita este archivo y llena:
- CLIENT_ID = "tu-client-id"
- TENANT_ID = "tu-tenant-id" (o déjalo vacío para "common")
        """)
    else:
        calendar = TeamsCalendar()
        print("Obteniendo eventos...")
        events = calendar.get_events()
        
        if events:
            print(f"\nProximos eventos ({len(events)}):\n")
            for event in events:
                print(f"  • {event['subject']}")
                print(f"    {event['start']} - {event['end']}")
                if event['is_online']:
                    print(f"    🔗 {event['online_url']}")
                print()
        else:
            print("No se encontraron eventos")
