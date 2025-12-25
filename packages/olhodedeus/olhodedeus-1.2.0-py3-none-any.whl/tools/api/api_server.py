#!/usr/bin/env python3
"""
api_server.py

API REST para o Olho de Deus.
Expõe funcionalidades via HTTP endpoints.
"""
import os
import sys
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Callable
from datetime import datetime
from functools import wraps

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class APIResponse:
    """Helper para respostas da API."""
    
    @staticmethod
    def success(data: Any = None, message: str = None) -> Dict:
        return {
            'success': True,
            'data': data,
            'message': message,
            'timestamp': datetime.now().isoformat(),
        }
    
    @staticmethod
    def error(message: str, code: int = 400) -> Dict:
        return {
            'success': False,
            'error': message,
            'code': code,
            'timestamp': datetime.now().isoformat(),
        }


class APIHandler(BaseHTTPRequestHandler):
    """Handler para requests da API."""
    
    # Configurações
    api_key = None
    routes = {}
    
    def log_message(self, format, *args):
        """Customiza log."""
        print(f"[API] {self.address_string()} - {args[0]}")
    
    def _set_headers(self, status_code: int = 200, content_type: str = 'application/json'):
        """Define headers da resposta."""
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
        self.end_headers()
    
    def _send_json(self, data: Dict, status_code: int = 200):
        """Envia resposta JSON."""
        self._set_headers(status_code)
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def _check_auth(self) -> bool:
        """Verifica autenticação usando o AuthManager."""
        # Obtém a key do header ou query param
        provided_key = self.headers.get('X-API-Key', '')
        
        if not provided_key:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            provided_key = params.get('api_key', [''])[0]
        
        if not provided_key:
            # Sem key fornecida
            if not self.api_key:
                return True  # Sem API key configurada, permite tudo
            return False
        
        # Verifica se é a key estática configurada
        if self.api_key and provided_key == self.api_key:
            return True
        
        # Verifica se é uma API key válida do AuthManager
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from olhodedeus.auth import AuthManager
            auth = AuthManager()
            key_data = auth.validate_api_key(provided_key)
            if key_data:
                return True
        except ImportError:
            pass
        
        return False
    
    def _get_body(self) -> Dict:
        """Obtém corpo do request como JSON."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                return json.loads(body.decode('utf-8'))
        except:
            pass
        return {}
    
    def _route(self, method: str):
        """Roteia request para handler apropriado."""
        if not self._check_auth():
            self._send_json(APIResponse.error('Unauthorized', 401), 401)
            return
        
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        # Procura rota
        for route_path, handlers in self.routes.items():
            if path == route_path and method in handlers:
                try:
                    body = self._get_body() if method == 'POST' else {}
                    result = handlers[method](params=params, body=body)
                    self._send_json(result)
                except Exception as e:
                    self._send_json(APIResponse.error(str(e), 500), 500)
                return
        
        self._send_json(APIResponse.error('Not Found', 404), 404)
    
    def do_OPTIONS(self):
        """Handle preflight CORS."""
        self._set_headers(200)
    
    def do_GET(self):
        """Handle GET requests."""
        self._route('GET')
    
    def do_POST(self):
        """Handle POST requests."""
        self._route('POST')


class OlhoDeDuesAPI:
    """API do Olho de Deus."""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8080, api_key: str = None):
        self.host = host
        self.port = port
        self.api_key = api_key
        self.server = None
        self.thread = None
        
        # Registra rotas
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura rotas da API."""
        APIHandler.api_key = self.api_key
        APIHandler.routes = {
            '/': {'GET': self._handle_root},
            '/api': {'GET': self._handle_api_info},
            '/api/health': {'GET': self._handle_health},
            
            # IP/Geolocation
            '/api/ip/lookup': {'GET': self._handle_ip_lookup},
            '/api/ip/my': {'GET': self._handle_my_ip},
            
            # Leaks
            '/api/leaks/check': {'GET': self._handle_leak_check, 'POST': self._handle_leak_check},
            
            # OSINT
            '/api/osint/username': {'GET': self._handle_username_check},
            '/api/osint/phone': {'GET': self._handle_phone_lookup},
            
            # Subdomain
            '/api/subdomain/scan': {'GET': self._handle_subdomain_scan},
            
            # Hashes
            '/api/hash/file': {'POST': self._handle_file_hash},
            '/api/hash/text': {'GET': self._handle_text_hash},
        }
    
    # === Handlers ===
    
    def _handle_root(self, **kwargs):
        """Rota raiz."""
        return APIResponse.success({
            'name': 'Olho de Deus API',
            'version': '1.0.0',
            'docs': f'http://{self.host}:{self.port}/api',
        })
    
    def _handle_api_info(self, **kwargs):
        """Informações da API."""
        return APIResponse.success({
            'endpoints': [
                {'path': '/api/health', 'method': 'GET', 'description': 'Health check'},
                {'path': '/api/ip/lookup', 'method': 'GET', 'params': ['ip'], 'description': 'IP geolocation'},
                {'path': '/api/ip/my', 'method': 'GET', 'description': 'Get my public IP'},
                {'path': '/api/leaks/check', 'method': 'GET/POST', 'params': ['email'], 'description': 'Check email in leaks'},
                {'path': '/api/osint/username', 'method': 'GET', 'params': ['username'], 'description': 'Username OSINT'},
                {'path': '/api/osint/phone', 'method': 'GET', 'params': ['phone'], 'description': 'Phone lookup'},
                {'path': '/api/subdomain/scan', 'method': 'GET', 'params': ['domain'], 'description': 'Subdomain scanner'},
                {'path': '/api/hash/text', 'method': 'GET', 'params': ['text'], 'description': 'Hash text'},
            ]
        })
    
    def _handle_health(self, **kwargs):
        """Health check."""
        return APIResponse.success({
            'status': 'healthy',
            'uptime': 'ok',
        })
    
    def _handle_ip_lookup(self, params: Dict, **kwargs):
        """Geolocalização de IP."""
        ip = params.get('ip', [''])[0]
        if not ip:
            return APIResponse.error('IP parameter required')
        
        try:
            from tools.recon.geolocation import IPGeolocation
            geo = IPGeolocation()
            result = geo.geolocate_ip_api(ip)
            return APIResponse.success({
                'ip': result.ip,
                'country': result.country,
                'country_code': result.country_code,
                'region': result.region,
                'city': result.city,
                'latitude': result.latitude,
                'longitude': result.longitude,
                'isp': result.isp,
                'timezone': result.timezone,
            })
        except Exception as e:
            return APIResponse.error(str(e))
    
    def _handle_my_ip(self, **kwargs):
        """Meu IP público."""
        try:
            from tools.recon.geolocation import IPGeolocation
            geo = IPGeolocation()
            ip = geo.get_my_ip()
            return APIResponse.success({'ip': ip})
        except Exception as e:
            return APIResponse.error(str(e))
    
    def _handle_leak_check(self, params: Dict, body: Dict = None, **kwargs):
        """Verifica email em leaks."""
        email = params.get('email', [''])[0] or (body or {}).get('email', '')
        if not email:
            return APIResponse.error('Email parameter required')
        
        try:
            from tools.ingest.leak_sources import FreeLeakChecker
            checker = FreeLeakChecker()
            result = checker.check_email(email)
            return APIResponse.success(result)
        except Exception as e:
            return APIResponse.error(str(e))
    
    def _handle_username_check(self, params: Dict, **kwargs):
        """Verifica username em plataformas."""
        username = params.get('username', [''])[0]
        if not username:
            return APIResponse.error('Username parameter required')
        
        try:
            from tools.recon.social_osint import SocialMediaOSINT
            osint = SocialMediaOSINT()
            
            # Verifica apenas algumas plataformas principais para resposta rápida
            platforms = {
                'github': f'https://github.com/{username}',
                'twitter': f'https://twitter.com/{username}',
                'instagram': f'https://www.instagram.com/{username}/',
            }
            
            results = {}
            import requests
            session = requests.Session()
            session.headers.update({'User-Agent': 'Mozilla/5.0'})
            
            for platform, url in platforms.items():
                try:
                    resp = session.get(url, timeout=5, allow_redirects=False)
                    results[platform] = {
                        'exists': resp.status_code == 200,
                        'url': url,
                    }
                except:
                    results[platform] = {'exists': None, 'url': url}
            
            return APIResponse.success({
                'username': username,
                'platforms': results,
            })
        except Exception as e:
            return APIResponse.error(str(e))
    
    def _handle_phone_lookup(self, params: Dict, **kwargs):
        """Lookup de telefone."""
        phone = params.get('phone', [''])[0]
        if not phone:
            return APIResponse.error('Phone parameter required')
        
        try:
            from tools.recon.phone_lookup import PhoneLookup
            lookup = PhoneLookup()
            result = lookup.lookup_ip_api(phone)
            result['links'] = lookup.generate_links(phone)
            return APIResponse.success(result)
        except Exception as e:
            return APIResponse.error(str(e))
    
    def _handle_subdomain_scan(self, params: Dict, **kwargs):
        """Scan de subdomínios."""
        domain = params.get('domain', [''])[0]
        if not domain:
            return APIResponse.error('Domain parameter required')
        
        try:
            from tools.recon.subdomain_scanner import SubdomainScanner
            scanner = SubdomainScanner()
            
            # Apenas crt.sh para resposta rápida
            subdomains = scanner.search_crtsh(domain)
            
            return APIResponse.success({
                'domain': domain,
                'subdomains': list(subdomains)[:50],
                'count': len(subdomains),
            })
        except Exception as e:
            return APIResponse.error(str(e))
    
    def _handle_file_hash(self, body: Dict, **kwargs):
        """Calcula hash de arquivo (base64)."""
        import base64
        import hashlib
        
        data = body.get('data', '')
        if not data:
            return APIResponse.error('File data (base64) required')
        
        try:
            file_bytes = base64.b64decode(data)
            return APIResponse.success({
                'md5': hashlib.md5(file_bytes).hexdigest(),
                'sha1': hashlib.sha1(file_bytes).hexdigest(),
                'sha256': hashlib.sha256(file_bytes).hexdigest(),
            })
        except Exception as e:
            return APIResponse.error(str(e))
    
    def _handle_text_hash(self, params: Dict, **kwargs):
        """Calcula hash de texto."""
        import hashlib
        
        text = params.get('text', [''])[0]
        if not text:
            return APIResponse.error('Text parameter required')
        
        data = text.encode('utf-8')
        return APIResponse.success({
            'text': text,
            'md5': hashlib.md5(data).hexdigest(),
            'sha1': hashlib.sha1(data).hexdigest(),
            'sha256': hashlib.sha256(data).hexdigest(),
        })
    
    # === Server Control ===
    
    def start(self, background: bool = False):
        """Inicia servidor."""
        self.server = HTTPServer((self.host, self.port), APIHandler)
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                   🌐 API SERVER STARTED                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📍 URL: http://{self.host}:{self.port:<5}                            
║  📚 Docs: http://{self.host}:{self.port}/api                        
║  🔑 API Key: {'Required' if self.api_key else 'Not Required'}                               
║                                                              ║
║  Press Ctrl+C to stop                                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        if background:
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
        else:
            try:
                self.server.serve_forever()
            except KeyboardInterrupt:
                print("\n🛑 Servidor parado.")
    
    def stop(self):
        """Para servidor."""
        if self.server:
            self.server.shutdown()


def interactive_menu():
    """Menu interativo."""
    # Carrega config
    config_path = "config/api.json"
    config = {
        'host': '127.0.0.1',
        'port': 8080,
        'api_key': None,
    }
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config.update(json.load(f))
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                     🌐 API REST SERVER                       ║
╠══════════════════════════════════════════════════════════════╣
║  Host: {config['host']:<15} | Port: {config['port']:<6}                
║  API Key: {'Configurada' if config.get('api_key') else 'Não configurada'}                                      
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🚀 Iniciar Servidor                                     ║
║  [2] ⚙️  Configurar Host/Porta                                ║
║  [3] 🔑 Configurar API Key                                   ║
║  [4] 📚 Ver Endpoints                                        ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            api = OlhoDeDuesAPI(
                host=config['host'],
                port=config['port'],
                api_key=config.get('api_key'),
            )
            api.start()
        
        elif choice == '2':
            host = input(f"\nHost [{config['host']}]: ").strip()
            if host:
                config['host'] = host
            
            port = input(f"Porta [{config['port']}]: ").strip()
            if port:
                config['port'] = int(port)
            
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print("✅ Salvo!")
            input("\nPressione Enter...")
        
        elif choice == '3':
            print("\n🔑 API Key para autenticação")
            print("   Deixe vazio para desabilitar autenticação")
            
            key = input("\nAPI Key: ").strip()
            config['api_key'] = key if key else None
            
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print("✅ Salvo!")
            input("\nPressione Enter...")
        
        elif choice == '4':
            print("""
📚 ENDPOINTS DISPONÍVEIS:

   GET  /api                - Informações da API
   GET  /api/health         - Health check
   
   GET  /api/ip/my          - Meu IP público
   GET  /api/ip/lookup?ip=  - Geolocalização de IP
   
   GET  /api/leaks/check?email=  - Verificar email em leaks
   
   GET  /api/osint/username?username=  - Verificar username
   GET  /api/osint/phone?phone=        - Lookup de telefone
   
   GET  /api/subdomain/scan?domain=    - Scan de subdomínios
   
   GET  /api/hash/text?text=           - Hash de texto
   POST /api/hash/file                 - Hash de arquivo (base64)

Autenticação:
   - Header: X-API-Key: <sua-key>
   - Query: ?api_key=<sua-key>
            """)
            input("\nPressione Enter...")
        
        elif choice == '0':
            break


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--start':
        # Modo direto
        api = OlhoDeDuesAPI()
        api.start()
    else:
        interactive_menu()
