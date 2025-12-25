#!/usr/bin/env python3
"""
Darkweb Monitor - Monitoramento de vazamentos na darkweb
Parte do toolkit Olho de Deus

NOTA: Requer Tor para acessar serviços .onion
"""

import os
import sys
import re
import json
import hashlib
import sqlite3
import shutil
import csv
import gzip
import time
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except ImportError:
    requests = None

# Importar progress bar
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utilities.progress_bar import ProgressBar, Spinner
except ImportError:
    ProgressBar = None
    Spinner = None


# ============================================
# BANCO DE DADOS DE SITES DE VAZAMENTO
# ============================================

LEAK_SITES = {
    # Sites .onion conhecidos (Tor required)
    "onion_sites": [
        {
            "name": "BreachForums",
            "onion_url": "breachforums.st",
            "mirrors": [
                "breached65xqh64s7xbkvqgg7bmj4nj7656hcb7x4g42x753r7zmejqd.onion",
                "breachforums.cx"
            ],
            "category": "forum",
            "active": True,
            "description": "Maior fórum de vazamentos atual (substituto do RaidForums)"
        },
        {
            "name": "XSS.is",
            "onion_url": "xss.is",
            "mirrors": ["xssforumv3isucukbxhdhwz67hoa5e2voakcfkuieq4ch257vsburuid.onion"],
            "category": "forum", 
            "active": True,
            "description": "Fórum russo de hackers e vazamentos"
        },
        {
            "name": "Exploit.in",
            "onion_url": "exploit.in",
            "mirrors": [],
            "category": "forum",
            "active": True,
            "description": "Fórum russo premium de exploits e leaks"
        },
        {
            "name": "Cracked.io",
            "onion_url": "cracked.io",
            "mirrors": [],
            "category": "forum",
            "active": True,
            "description": "Fórum de cracking e leaks"
        },
        {
            "name": "Nulled.to",
            "onion_url": "nulled.to",
            "mirrors": [],
            "category": "forum",
            "active": True,
            "description": "Fórum de leaks e ferramentas"
        },
        {
            "name": "LeakBase",
            "onion_url": None,
            "clearnet_url": "leakbase.io",
            "category": "database",
            "active": False,
            "description": "Base de dados de leaks (status incerto)"
        },
        {
            "name": "Raid Forums",
            "onion_url": None,
            "clearnet_url": None,
            "category": "archive",
            "active": False,
            "description": "Fechado - apreendido pelo FBI em 2022"
        },
    ],
    
    # APIs públicas de verificação de vazamentos
    "public_apis": [
        {
            "name": "Have I Been Pwned",
            "url": "https://haveibeenpwned.com/api/v3",
            "test_url": "https://haveibeenpwned.com",
            "requires_key": True,
            "free_tier": True,
            "description": "API principal de verificação de vazamentos"
        },
        {
            "name": "DeHashed",
            "url": "https://api.dehashed.com",
            "test_url": "https://dehashed.com",
            "requires_key": True,
            "free_tier": False,
            "description": "Busca em múltiplos breaches"
        },
        {
            "name": "LeakCheck",
            "url": "https://leakcheck.io/api/public",
            "test_url": "https://leakcheck.io",
            "requires_key": True,
            "free_tier": True,
            "description": "Verificação de email/senha"
        },
        {
            "name": "IntelX",
            "url": "https://2.intelx.io",
            "test_url": "https://intelx.io",
            "requires_key": True,
            "free_tier": True,
            "description": "Intelligence X - busca em pastes e leaks"
        },
        {
            "name": "Snusbase",
            "url": "https://api.snusbase.com",
            "test_url": "https://snusbase.com",
            "requires_key": True,
            "free_tier": False,
            "description": "Base de dados de credenciais vazadas"
        },
        {
            "name": "LeakPeek",
            "url": "https://leakpeek.com/api",
            "test_url": "https://leakpeek.com",
            "requires_key": True,
            "free_tier": True,
            "description": "Busca de emails vazados"
        },
        {
            "name": "HaveIBeenSold",
            "url": "https://haveibeensold.app/api",
            "test_url": "https://haveibeensold.app",
            "requires_key": False,
            "free_tier": True,
            "description": "Verifica se dados foram vendidos"
        },
    ],
    
    # Fontes de pastes
    "paste_sites": [
        {
            "name": "Pastebin",
            "url": "https://pastebin.com",
            "scraping_url": "https://scrape.pastebin.com/api_scraping.php",
            "requires_key": True,
            "description": "Maior site de pastes"
        },
        {
            "name": "Ghostbin",
            "url": "https://ghostbin.com",
            "description": "Paste anônimo"
        },
        {
            "name": "Rentry",
            "url": "https://rentry.co",
            "description": "Paste markdown"
        },
        {
            "name": "Dpaste",
            "url": "https://dpaste.org",
            "description": "Paste simples"
        },
        {
            "name": "ControlC",
            "url": "https://controlc.com",
            "description": "Paste alternativo"
        },
        {
            "name": "JustPaste.it",
            "url": "https://justpaste.it",
            "description": "Paste anônimo"
        },
    ],
    
    # Buscadores de leaks (clearnet)
    "leak_search_engines": [
        {
            "name": "Pwndb2",
            "url": "http://pwndb2am4tzkvold.onion",
            "clearnet_mirror": None,
            "type": "onion",
            "description": "Busca em dumps de credenciais"
        },
        {
            "name": "Ahmia",
            "url": "https://ahmia.fi",
            "type": "clearnet",
            "description": "Buscador de sites .onion"
        },
        {
            "name": "Torch",
            "url": "http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5aygthi7d6rplyvk3noyd.onion",
            "type": "onion",
            "description": "Buscador da darkweb"
        },
        {
            "name": "DarkSearch",
            "url": "https://darksearch.io",
            "type": "clearnet",
            "description": "API de busca na darkweb"
        },
        {
            "name": "OnionSearch",
            "url": "https://onionsearchengine.com",
            "type": "clearnet",
            "description": "Buscador de onion sites"
        },
    ],
    
    # Ransomware groups (para monitoramento)
    "ransomware_groups": [
        {"name": "LockBit", "active": True},
        {"name": "BlackCat/ALPHV", "active": True},
        {"name": "Cl0p", "active": True},
        {"name": "Play", "active": True},
        {"name": "8Base", "active": True},
        {"name": "Akira", "active": True},
        {"name": "NoEscape", "active": True},
        {"name": "Medusa", "active": True},
        {"name": "BianLian", "active": True},
        {"name": "Royal", "active": False},
    ]
}


# ============================================
# VERIFICADOR DE URLS E STATUS DOS SITES
# ============================================

class SiteChecker:
    """Verifica status e acessibilidade dos sites de vazamento"""
    
    def __init__(self, tor_proxy: str = "socks5h://127.0.0.1:9050", timeout: int = 15):
        self.timeout = timeout
        self.tor_proxy = tor_proxy
        self.results = {}
        
        # Session normal para clearnet
        self.session = None
        if requests:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
        
        # Session com Tor para .onion
        self.tor_session = None
        if requests:
            self.tor_session = requests.Session()
            self.tor_session.proxies = {
                'http': self.tor_proxy,
                'https': self.tor_proxy
            }
            self.tor_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0'
            })
    
    def check_url(self, url: str, use_tor: bool = False) -> Dict:
        """Verifica uma URL específica"""
        result = {
            'url': url,
            'status': 'unknown',
            'status_code': None,
            'response_time': None,
            'error': None,
            'checked_at': datetime.now().isoformat()
        }
        
        if not self.session:
            result['error'] = 'requests module not available'
            return result
        
        session = self.tor_session if use_tor else self.session
        
        # Adicionar protocolo se não tiver
        if not url.startswith('http'):
            if '.onion' in url:
                url = f'http://{url}'
            else:
                url = f'https://{url}'
        
        try:
            start_time = time.time()
            response = session.get(url, timeout=self.timeout, allow_redirects=True)
            elapsed = time.time() - start_time
            
            result['status_code'] = response.status_code
            result['response_time'] = round(elapsed, 2)
            
            if response.status_code == 200:
                result['status'] = 'online'
            elif response.status_code in [301, 302, 303, 307, 308]:
                result['status'] = 'redirect'
            elif response.status_code == 403:
                result['status'] = 'forbidden'
            elif response.status_code == 404:
                result['status'] = 'not_found'
            elif response.status_code >= 500:
                result['status'] = 'server_error'
            else:
                result['status'] = 'accessible'
                
        except requests.exceptions.Timeout:
            result['status'] = 'timeout'
            result['error'] = 'Connection timeout'
        except requests.exceptions.ConnectionError as e:
            result['status'] = 'offline'
            result['error'] = 'Connection failed'
        except requests.exceptions.SSLError:
            result['status'] = 'ssl_error'
            result['error'] = 'SSL certificate error'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)[:100]
        
        return result
    
    def check_all_sites(self, include_onion: bool = False) -> Dict:
        """Verifica todos os sites conhecidos"""
        results = {
            'public_apis': [],
            'paste_sites': [],
            'leak_search_engines': [],
            'onion_sites': [],
            'summary': {
                'total': 0,
                'online': 0,
                'offline': 0,
                'errors': 0
            }
        }
        
        # Verificar APIs públicas
        print("\n\033[96m   Verificando APIs públicas...\033[0m")
        for api in LEAK_SITES.get('public_apis', []):
            test_url = api.get('test_url', api.get('url'))
            if test_url:
                result = self.check_url(test_url)
                result['name'] = api['name']
                results['public_apis'].append(result)
                results['summary']['total'] += 1
                if result['status'] == 'online':
                    results['summary']['online'] += 1
                elif result['status'] in ['offline', 'timeout']:
                    results['summary']['offline'] += 1
                else:
                    results['summary']['errors'] += 1
                self._print_status(api['name'], result)
        
        # Verificar sites de paste
        print("\n\033[96m   Verificando sites de paste...\033[0m")
        for paste in LEAK_SITES.get('paste_sites', []):
            url = paste.get('url')
            if url:
                result = self.check_url(url)
                result['name'] = paste['name']
                results['paste_sites'].append(result)
                results['summary']['total'] += 1
                if result['status'] == 'online':
                    results['summary']['online'] += 1
                elif result['status'] in ['offline', 'timeout']:
                    results['summary']['offline'] += 1
                else:
                    results['summary']['errors'] += 1
                self._print_status(paste['name'], result)
        
        # Verificar buscadores (apenas clearnet)
        print("\n\033[96m   Verificando buscadores de leaks...\033[0m")
        for engine in LEAK_SITES.get('leak_search_engines', []):
            if engine.get('type') == 'clearnet':
                url = engine.get('url')
                if url:
                    result = self.check_url(url)
                    result['name'] = engine['name']
                    results['leak_search_engines'].append(result)
                    results['summary']['total'] += 1
                    if result['status'] == 'online':
                        results['summary']['online'] += 1
                    elif result['status'] in ['offline', 'timeout']:
                        results['summary']['offline'] += 1
                    else:
                        results['summary']['errors'] += 1
                    self._print_status(engine['name'], result)
        
        # Verificar sites .onion (requer Tor)
        if include_onion:
            print("\n\033[96m   Verificando sites .onion (via Tor)...\033[0m")
            
            # Primeiro verificar se Tor está ativo
            tor_ok = self._check_tor()
            if not tor_ok:
                print("   \033[91m❌ Tor não está conectado. Sites .onion não serão verificados.\033[0m")
            else:
                for site in LEAK_SITES.get('onion_sites', []):
                    if not site.get('active', False):
                        continue
                    
                    # Tentar clearnet primeiro, depois onion
                    url = site.get('clearnet_url') or site.get('onion_url')
                    if url:
                        use_tor = '.onion' in str(url) if url else False
                        result = self.check_url(url, use_tor=use_tor)
                        result['name'] = site['name']
                        results['onion_sites'].append(result)
                        results['summary']['total'] += 1
                        if result['status'] == 'online':
                            results['summary']['online'] += 1
                        elif result['status'] in ['offline', 'timeout']:
                            results['summary']['offline'] += 1
                        else:
                            results['summary']['errors'] += 1
                        self._print_status(site['name'], result)
        
        return results
    
    def _check_tor(self) -> bool:
        """Verifica se Tor está funcionando"""
        try:
            response = self.tor_session.get(
                "https://check.torproject.org/api/ip",
                timeout=10
            )
            data = response.json()
            return data.get("IsTor", False)
        except:
            return False
    
    def _print_status(self, name: str, result: Dict):
        """Imprime status formatado"""
        status = result['status']
        
        if status == 'online':
            icon = "\033[92m✓\033[0m"
            status_text = f"\033[92m{status}\033[0m"
        elif status in ['offline', 'timeout']:
            icon = "\033[91m✗\033[0m"
            status_text = f"\033[91m{status}\033[0m"
        elif status == 'forbidden':
            icon = "\033[93m⚠\033[0m"
            status_text = f"\033[93m{status}\033[0m"
        else:
            icon = "\033[93m?\033[0m"
            status_text = f"\033[93m{status}\033[0m"
        
        time_str = f"{result['response_time']}s" if result['response_time'] else "N/A"
        print(f"   {icon} {name:20} [{status_text:15}] {time_str}")
    
    def search_new_urls(self, site_name: str) -> List[str]:
        """Busca URLs atualizadas para um site"""
        found_urls = []
        
        # Buscadores para encontrar mirrors/novas URLs
        search_engines = [
            f"https://ahmia.fi/search/?q={site_name}",
        ]
        
        print(f"\n\033[96m   Buscando URLs para: {site_name}\033[0m")
        
        for engine_url in search_engines:
            try:
                response = self.session.get(engine_url, timeout=self.timeout)
                if response.status_code == 200:
                    # Extrair URLs do conteúdo (básico)
                    import re
                    onion_pattern = r'[a-z2-7]{56}\.onion'
                    matches = re.findall(onion_pattern, response.text)
                    found_urls.extend(list(set(matches)))
            except:
                pass
        
        return list(set(found_urls))
    
    def export_results(self, results: Dict, filename: str = "site_check_results.json"):
        """Exporta resultados para arquivo"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n\033[92m   ✓ Resultados salvos em {filename}\033[0m")


# ============================================
# DOWNLOADER DE VAZAMENTOS
# ============================================

class LeakDownloader:
    """Baixa dados de vazamentos de APIs e fontes públicas"""
    
    def __init__(self, output_dir: str = "data/downloads", 
                 tor_proxy: str = "socks5h://127.0.0.1:9050"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tor_proxy = tor_proxy
        
        # Criar subpastas
        self.dirs = {
            'breaches': self.output_dir / 'breaches',
            'pastes': self.output_dir / 'pastes',
            'apis': self.output_dir / 'api_results',
            'raw': self.output_dir / 'raw_data',
        }
        for d in self.dirs.values():
            d.mkdir(exist_ok=True)
        
        # Sessions
        self.session = None
        self.tor_session = None
        if requests:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            self.tor_session = requests.Session()
            self.tor_session.proxies = {
                'http': self.tor_proxy,
                'https': self.tor_proxy
            }
        
        # API Keys (carregar de config)
        self.api_keys = self._load_api_keys()
        
        # Stats
        self.stats = {
            'files_downloaded': 0,
            'bytes_downloaded': 0,
            'errors': 0
        }
    
    def _load_api_keys(self) -> Dict:
        """Carrega API keys do arquivo de configuração"""
        config_path = Path(__file__).parent.parent.parent / 'config' / 'api_keys.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_api_key(self, service: str, key: str):
        """Salva API key"""
        self.api_keys[service] = key
        config_path = Path(__file__).parent.parent.parent / 'config' / 'api_keys.json'
        config_path.parent.mkdir(exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(self.api_keys, f, indent=2)
    
    def download_hibp_breaches(self) -> List[Dict]:
        """Baixa lista completa de breaches do HIBP"""
        print("\n\033[96m   Baixando lista de breaches do HIBP...\033[0m")
        
        try:
            response = self.session.get(
                "https://haveibeenpwned.com/api/v3/breaches",
                timeout=30
            )
            
            if response.status_code == 200:
                breaches = response.json()
                
                # Salvar
                output_file = self.dirs['breaches'] / f"hibp_breaches_{datetime.now().strftime('%Y%m%d')}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(breaches, f, indent=2, ensure_ascii=False)
                
                self.stats['files_downloaded'] += 1
                self.stats['bytes_downloaded'] += len(response.content)
                
                print(f"\033[92m   ✓ {len(breaches)} breaches salvos em {output_file.name}\033[0m")
                return breaches
            else:
                print(f"\033[91m   ✗ Erro: HTTP {response.status_code}\033[0m")
        except Exception as e:
            print(f"\033[91m   ✗ Erro: {e}\033[0m")
            self.stats['errors'] += 1
        
        return []
    
    def check_email_leaks(self, email: str) -> Dict:
        """Verifica vazamentos de um email usando múltiplas APIs"""
        results = {
            'email': email,
            'checked_at': datetime.now().isoformat(),
            'sources': {}
        }
        
        # HIBP (requer API key)
        hibp_key = self.api_keys.get('hibp')
        if hibp_key:
            print(f"   Verificando HIBP...")
            try:
                response = self.session.get(
                    f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                    headers={'hibp-api-key': hibp_key},
                    timeout=10
                )
                if response.status_code == 200:
                    results['sources']['hibp'] = response.json()
                elif response.status_code == 404:
                    results['sources']['hibp'] = []
            except:
                pass
        
        # LeakCheck (free tier)
        print(f"   Verificando LeakCheck...")
        try:
            response = self.session.get(
                f"https://leakcheck.io/api/public?check={email}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    results['sources']['leakcheck'] = data
        except:
            pass
        
        # HaveIBeenSold (free)
        print(f"   Verificando HaveIBeenSold...")
        try:
            response = self.session.get(
                f"https://haveibeensold.app/api/v2/email/{email}",
                timeout=10
            )
            if response.status_code == 200:
                results['sources']['haveibeensold'] = response.json()
        except:
            pass
        
        # Salvar resultado
        safe_email = email.replace('@', '_at_').replace('.', '_')
        output_file = self.dirs['apis'] / f"email_{safe_email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results
    
    def download_paste(self, url: str) -> Optional[str]:
        """Baixa conteúdo de um paste"""
        print(f"\n\033[96m   Baixando paste: {url}\033[0m")
        
        try:
            # Detectar tipo de paste
            if 'pastebin.com' in url:
                # Converter para raw
                paste_id = url.split('/')[-1]
                raw_url = f"https://pastebin.com/raw/{paste_id}"
            elif 'rentry.co' in url:
                paste_id = url.split('/')[-1]
                raw_url = f"https://rentry.co/api/raw/{paste_id}"
            else:
                raw_url = url
            
            response = self.session.get(raw_url, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                
                # Salvar
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = self.dirs['pastes'] / f"paste_{timestamp}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.stats['files_downloaded'] += 1
                self.stats['bytes_downloaded'] += len(content)
                
                print(f"\033[92m   ✓ Salvo em {output_file.name} ({len(content)} bytes)\033[0m")
                return content
            else:
                print(f"\033[91m   ✗ Erro: HTTP {response.status_code}\033[0m")
        except Exception as e:
            print(f"\033[91m   ✗ Erro: {e}\033[0m")
            self.stats['errors'] += 1
        
        return None
    
    def search_intelx(self, query: str, max_results: int = 100) -> List[Dict]:
        """Busca no Intelligence X"""
        api_key = self.api_keys.get('intelx')
        if not api_key:
            print("\033[93m   ⚠ API key do IntelX não configurada\033[0m")
            return []
        
        print(f"\n\033[96m   Buscando no IntelX: {query}\033[0m")
        
        results = []
        try:
            # Iniciar busca
            response = self.session.post(
                "https://2.intelx.io/intelligent/search",
                headers={'x-key': api_key},
                json={
                    'term': query,
                    'maxresults': max_results,
                    'media': 0,
                    'sort': 2,
                    'terminate': []
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                search_id = data.get('id')
                
                if search_id:
                    # Buscar resultados
                    time.sleep(2)
                    
                    result_response = self.session.get(
                        f"https://2.intelx.io/intelligent/search/result?id={search_id}",
                        headers={'x-key': api_key},
                        timeout=30
                    )
                    
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        results = result_data.get('records', [])
                        
                        # Salvar
                        safe_query = re.sub(r'[^\w]', '_', query)[:50]
                        output_file = self.dirs['apis'] / f"intelx_{safe_query}_{datetime.now().strftime('%Y%m%d')}.json"
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(results, f, indent=2, ensure_ascii=False)
                        
                        print(f"\033[92m   ✓ {len(results)} resultados salvos\033[0m")
        except Exception as e:
            print(f"\033[91m   ✗ Erro: {e}\033[0m")
        
        return results
    
    def download_from_url(self, url: str, filename: str = None) -> Optional[str]:
        """Baixa arquivo de qualquer URL"""
        print(f"\n\033[96m   Baixando: {url}\033[0m")
        
        use_tor = '.onion' in url
        session = self.tor_session if use_tor else self.session
        
        try:
            response = session.get(url, timeout=60, stream=True)
            
            if response.status_code == 200:
                # Determinar nome do arquivo
                if not filename:
                    filename = url.split('/')[-1] or f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                output_file = self.dirs['raw'] / filename
                
                # Baixar em chunks
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(output_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if total_size and ProgressBar:
                                # Mostrar progresso
                                pass
                
                self.stats['files_downloaded'] += 1
                self.stats['bytes_downloaded'] += downloaded
                
                print(f"\033[92m   ✓ Salvo: {output_file.name} ({downloaded:,} bytes)\033[0m")
                return str(output_file)
            else:
                print(f"\033[91m   ✗ Erro: HTTP {response.status_code}\033[0m")
        except Exception as e:
            print(f"\033[91m   ✗ Erro: {e}\033[0m")
            self.stats['errors'] += 1
        
        return None
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas"""
        return self.stats.copy()


# ============================================
# SCANNER AUTOMATIZADO DE FONTES DE VAZAMENTOS
# ============================================

class LeakSourceScanner:
    """
    Scanner automatizado para descobrir e verificar fontes de vazamentos.
    Verifica status de sites, busca novos links e faz scraping automatizado.
    """
    
    # Lista COMPLETA de fontes conhecidas
    ALL_SOURCES = {
        # ========== AGREGADORES E BUSCADORES (MAIS CONFIÁVEIS) ==========
        'aggregators': [
            {'name': 'LeakIX', 'url': 'https://leakix.net', 'type': 'aggregator', 'reliability': 'high'},
            {'name': 'Ransomwatch', 'url': 'https://ransomwatch.telemetry.ltd', 'type': 'aggregator', 'reliability': 'high'},
            {'name': 'RansomLook', 'url': 'https://www.ransomlook.io', 'type': 'aggregator', 'reliability': 'high'},
            {'name': 'CVEDB', 'url': 'https://cvedb.shodan.io', 'type': 'aggregator', 'reliability': 'high'},
            {'name': 'FullHunt', 'url': 'https://fullhunt.io', 'type': 'aggregator', 'reliability': 'high'},
            {'name': 'URLhaus', 'url': 'https://urlhaus.abuse.ch', 'type': 'malware', 'reliability': 'high'},
            {'name': 'ThreatFox', 'url': 'https://threatfox.abuse.ch', 'type': 'ioc', 'reliability': 'high'},
            {'name': 'MalwareBazaar', 'url': 'https://bazaar.abuse.ch', 'type': 'malware', 'reliability': 'high'},
        ],
        
        # ========== PASTES (FUNCIONAIS) ==========
        'pastes': [
            {'name': 'Pastebin', 'url': 'https://pastebin.com/archive', 'type': 'paste', 'reliability': 'high'},
            {'name': 'Rentry', 'url': 'https://rentry.co', 'type': 'paste', 'reliability': 'high'},
            {'name': 'Ghostbin', 'url': 'https://ghostbin.com', 'type': 'paste', 'reliability': 'medium'},
            {'name': 'ControlC', 'url': 'https://controlc.com', 'type': 'paste', 'reliability': 'medium'},
            {'name': 'Dpaste', 'url': 'https://dpaste.org', 'type': 'paste', 'reliability': 'high'},
            {'name': 'Paste.ee', 'url': 'https://paste.ee', 'type': 'paste', 'reliability': 'medium'},
            {'name': 'JustPaste', 'url': 'https://justpaste.it', 'type': 'paste', 'reliability': 'medium'},
            {'name': 'Ideone', 'url': 'https://ideone.com/recent', 'type': 'paste', 'reliability': 'medium'},
        ],
        
        # ========== REPOSITÓRIOS DE CÓDIGO ==========
        'repositories': [
            {'name': 'GitHub', 'url': 'https://github.com', 'type': 'repo', 'reliability': 'high'},
            {'name': 'GitLab', 'url': 'https://gitlab.com/explore/projects', 'type': 'repo', 'reliability': 'high'},
            {'name': 'Gist GitHub', 'url': 'https://gist.github.com/discover', 'type': 'gist', 'reliability': 'high'},
            {'name': 'Codeberg', 'url': 'https://codeberg.org/explore/repos', 'type': 'repo', 'reliability': 'low'},
        ],
        
        # ========== BUSCADORES ESPECIALIZADOS ==========
        'search_engines': [
            {'name': 'Ahmia', 'url': 'https://ahmia.fi', 'type': 'onion_search', 'reliability': 'high'},
            {'name': 'DarkSearch', 'url': 'https://darksearch.io', 'type': 'onion_search', 'reliability': 'medium'},
            {'name': 'Onion.live', 'url': 'https://onion.live', 'type': 'onion_search', 'reliability': 'medium'},
            {'name': 'PublicWWW', 'url': 'https://publicwww.com', 'type': 'code_search', 'reliability': 'high'},
            {'name': 'SearchCode', 'url': 'https://searchcode.com', 'type': 'code_search', 'reliability': 'high'},
            {'name': 'Grep.app', 'url': 'https://grep.app', 'type': 'code_search', 'reliability': 'high'},
        ],
        
        # ========== VERIFICAÇÃO DE VAZAMENTOS ==========
        'leak_checkers': [
            {'name': 'HIBP', 'url': 'https://haveibeenpwned.com', 'type': 'checker', 'reliability': 'high'},
            {'name': 'Dehashed', 'url': 'https://dehashed.com', 'type': 'checker', 'reliability': 'high'},
            {'name': 'LeakCheck', 'url': 'https://leakcheck.io', 'type': 'checker', 'reliability': 'high'},
            {'name': 'BreachDirectory', 'url': 'https://breachdirectory.org', 'type': 'checker', 'reliability': 'medium'},
            {'name': 'HaveIBeenSold', 'url': 'https://haveibeensold.app', 'type': 'checker', 'reliability': 'medium'},
            {'name': 'IntelX', 'url': 'https://intelx.io', 'type': 'checker', 'reliability': 'high'},
        ],
        
        # ========== FÓRUNS (STATUS VARIÁVEL) ==========
        'forums': [
            {'name': 'BreachForums', 'urls': ['https://breachforums.st', 'https://breachforums.cx', 'https://breachforums.is'], 'type': 'forum', 'reliability': 'variable'},
            {'name': 'XSS.is', 'urls': ['https://xss.is'], 'type': 'forum', 'reliability': 'variable'},
            {'name': 'Exploit.in', 'urls': ['https://exploit.in'], 'type': 'forum', 'reliability': 'variable'},
            {'name': 'Cracked', 'urls': ['https://cracked.io', 'https://cracked.sh'], 'type': 'forum', 'reliability': 'variable'},
            {'name': 'Nulled', 'urls': ['https://nulled.to', 'https://nulled.cc'], 'type': 'forum', 'reliability': 'variable'},
        ],
        
        # ========== ARQUIVOS ==========
        'archives': [
            {'name': 'Archive.org', 'url': 'https://archive.org', 'type': 'archive', 'reliability': 'high'},
            {'name': 'Wayback Machine', 'url': 'https://web.archive.org', 'type': 'archive', 'reliability': 'high'},
            {'name': 'Archive.today', 'url': 'https://archive.today', 'type': 'archive', 'reliability': 'medium'},
        ],
        
        # ========== IOC E THREAT INTEL ==========
        'threat_intel': [
            {'name': 'OTX AlienVault', 'url': 'https://otx.alienvault.com', 'type': 'threat_intel', 'reliability': 'high'},
            {'name': 'VirusTotal', 'url': 'https://www.virustotal.com', 'type': 'threat_intel', 'reliability': 'high'},
            {'name': 'Pulsedive', 'url': 'https://pulsedive.com', 'type': 'threat_intel', 'reliability': 'high'},
            {'name': 'GreyNoise', 'url': 'https://viz.greynoise.io', 'type': 'threat_intel', 'reliability': 'high'},
        ],
        
        # ========== FILE SHARING ==========
        'file_sharing': [
            {'name': 'Gofile', 'url': 'https://gofile.io', 'type': 'file_sharing', 'reliability': 'medium'},
            {'name': 'Pixeldrain', 'url': 'https://pixeldrain.com', 'type': 'file_sharing', 'reliability': 'medium'},
            {'name': 'Catbox', 'url': 'https://catbox.moe', 'type': 'file_sharing', 'reliability': 'medium'},
            {'name': 'Transfer.sh', 'url': 'https://transfer.sh', 'type': 'file_sharing', 'reliability': 'medium'},
        ],
    }
    
    def __init__(self, dump_dir: str = "Dump", tor_proxy: str = "socks5h://127.0.0.1:9050"):
        self.dump_dir = Path(dump_dir)
        self.dump_dir.mkdir(parents=True, exist_ok=True)
        self.tor_proxy = tor_proxy
        
        self.scanner_dir = self.dump_dir / 'scanner_results'
        self.scanner_dir.mkdir(exist_ok=True)
        
        self.db_path = self.dump_dir / 'source_scanner.db'
        self._init_db()
        
        self.session = None
        self.tor_session = None
        if requests:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            })
            self.tor_session = requests.Session()
            self.tor_session.proxies = {'http': self.tor_proxy, 'https': self.tor_proxy}
    
    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS source_status (
            id INTEGER PRIMARY KEY, name TEXT, url TEXT UNIQUE, category TEXT, 
            type TEXT, status TEXT, response_time REAL, last_check TEXT, fail_count INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS discovered_sources (
            id INTEGER PRIMARY KEY, url TEXT UNIQUE, found_on TEXT, found_date TEXT, verified INTEGER DEFAULT 0)''')
        conn.commit()
        conn.close()
    
    def check_source(self, url: str, use_tor: bool = False, timeout: int = 10) -> Dict:
        result = {'url': url, 'status': 'unknown', 'response_time': None}
        session = self.tor_session if use_tor else self.session
        try:
            start = time.time()
            response = session.get(url, timeout=timeout, allow_redirects=True)
            result['response_time'] = round(time.time() - start, 2)
            result['status'] = 'online' if response.status_code == 200 else f'http_{response.status_code}'
        except requests.exceptions.Timeout:
            result['status'] = 'timeout'
        except:
            result['status'] = 'offline'
        return result
    
    def scan_all_sources(self, categories: List[str] = None, use_tor: bool = False) -> Dict:
        print("\n\033[96m" + "="*60 + "\033[0m")
        print("\033[96m   🔍 ESCANEANDO FONTES DE VAZAMENTOS\033[0m")
        print("\033[96m" + "="*60 + "\033[0m\n")
        
        results = {'online': [], 'offline': [], 'summary': {}}
        cats = categories or list(self.ALL_SOURCES.keys())
        total = sum(len(self.ALL_SOURCES.get(c, [])) for c in cats)
        current = 0
        
        for cat in cats:
            sources = self.ALL_SOURCES.get(cat, [])
            print(f"\n   \033[93m━━━ {cat.upper()} ━━━\033[0m")
            
            for src in sources:
                current += 1
                urls = src.get('urls', [src.get('url')])
                name = src.get('name', 'Unknown')
                
                for url in [u for u in urls if u]:
                    status = self.check_source(url, use_tor)
                    icon = "\033[92m✓\033[0m" if status['status'] == 'online' else "\033[91m✗\033[0m"
                    time_str = f"{status['response_time']}s" if status['response_time'] else "N/A"
                    print(f"   [{current}/{total}] {icon} {name:25} {time_str}")
                    
                    if status['status'] == 'online':
                        results['online'].append({**src, 'working_url': url})
                        break
                    else:
                        results['offline'].append(src)
                    
                    self._save_status(name, url, cat, status)
        
        results['summary'] = {'total': total, 'online': len(results['online']), 'offline': len(results['offline'])}
        print(f"\n\033[92m✓ Online: {results['summary']['online']} | \033[91m✗ Offline: {results['summary']['offline']}\033[0m")
        
        self._save_results(results)
        return results
    
    def _save_status(self, name, url, cat, status):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO source_status (name,url,category,status,response_time,last_check) VALUES (?,?,?,?,?,?)',
                (name, url, cat, status['status'], status['response_time'], datetime.now().isoformat()))
            conn.commit()
        except: pass
        finally: conn.close()
    
    def _save_results(self, results):
        output = self.scanner_dir / f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n   💾 Salvo: {output.name}")
    
    def discover_new_sources(self, use_tor: bool = False) -> List[Dict]:
        print("\n\033[96m   🔎 DESCOBRINDO NOVAS FONTES...\033[0m\n")
        discovered = []
        
        # Ahmia
        print("   [1/4] Ahmia (sites .onion)...")
        for q in ['database leak', 'breach forum']:
            try:
                r = self.session.get(f'https://ahmia.fi/search/?q={q}', timeout=15)
                onions = re.findall(r'([a-z2-7]{56}\.onion)', r.text)
                for o in set(onions):
                    discovered.append({'url': f'http://{o}', 'source': 'ahmia', 'requires_tor': True})
            except: pass
        print(f"       → {len([d for d in discovered if d['source']=='ahmia'])} encontrados")
        
        # GitHub
        print("   [2/4] GitHub (repositórios)...")
        try:
            r = self.session.get('https://github.com/search?q=leaked+database&type=repositories', timeout=15)
            repos = re.findall(r'href="/([^/]+/[^"]+)"[^>]*data-hovercard', r.text)
            for repo in repos[:15]:
                discovered.append({'url': f'https://github.com/{repo}', 'source': 'github'})
        except: pass
        print(f"       → {len([d for d in discovered if d['source']=='github'])} encontrados")
        
        # Ransomwatch
        print("   [3/4] Ransomwatch (grupos ransomware)...")
        try:
            r = self.session.get('https://ransomwatch.telemetry.ltd/groups', timeout=20)
            for g in r.json():
                for loc in g.get('locations', []):
                    fqdn = loc.get('fqdn', '')
                    if fqdn:
                        discovered.append({'url': f'http://{fqdn}', 'source': 'ransomwatch', 'group': g.get('name')})
        except: pass
        print(f"       → {len([d for d in discovered if d['source']=='ransomwatch'])} encontrados")
        
        # Pastebin
        print("   [4/4] Pastebin (links em pastes)...")
        try:
            r = self.session.get('https://pastebin.com/archive', timeout=15)
            ids = re.findall(r'href="/([a-zA-Z0-9]{8})"', r.text)[:10]
            for pid in ids:
                try:
                    pr = self.session.get(f'https://pastebin.com/raw/{pid}', timeout=10)
                    urls = re.findall(r'https?://[^\s<>"\']+', pr.text)
                    for u in urls:
                        if any(k in u.lower() for k in ['leak', 'breach', 'dump', 'mega.nz', 'gofile']):
                            discovered.append({'url': u, 'source': f'paste:{pid}'})
                except: pass
                time.sleep(0.5)
        except: pass
        print(f"       → {len([d for d in discovered if 'paste' in d['source']])} encontrados")
        
        # Dedupe
        seen = set()
        unique = [d for d in discovered if d['url'] not in seen and not seen.add(d['url'])]
        
        self._save_discovered(unique)
        print(f"\n   \033[92m✓ Total: {len(unique)} novas fontes descobertas\033[0m")
        return unique
    
    def _save_discovered(self, sources):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        for s in sources:
            try:
                c.execute('INSERT OR IGNORE INTO discovered_sources (url,found_on,found_date) VALUES (?,?,?)',
                    (s['url'], s.get('source'), datetime.now().isoformat()))
            except: pass
        conn.commit()
        conn.close()
    
    def get_working_sources(self) -> List[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT name,url,category,response_time FROM source_status WHERE status='online' ORDER BY response_time")
        rows = c.fetchall()
        conn.close()
        return [{'name': r[0], 'url': r[1], 'category': r[2], 'response_time': r[3]} for r in rows]


# ============================================
# SCRAPER DE SITES DE VAZAMENTOS (SEM APIs)
# ============================================

class SiteLeakScraper:
    """
    Scraper direto dos sites de vazamentos.
    Baixa dados e salva na pasta Dump/ (DB local).
    NÃO USA APIs - acessa diretamente os sites.
    """
    
    def __init__(self, dump_dir: str = "Dump", 
                 tor_proxy: str = "socks5h://127.0.0.1:9050"):
        self.dump_dir = Path(dump_dir)
        self.dump_dir.mkdir(parents=True, exist_ok=True)
        self.tor_proxy = tor_proxy
        
        # Subpastas organizadas
        self.dirs = {
            'breachforums': self.dump_dir / 'breachforums',
            'xss': self.dump_dir / 'xss_is',
            'exploit': self.dump_dir / 'exploit_in',
            'cracked': self.dump_dir / 'cracked_io',
            'nulled': self.dump_dir / 'nulled_to',
            'leakbase': self.dump_dir / 'leakbase',
            'pastes': self.dump_dir / 'pastes',
            'ransomware': self.dump_dir / 'ransomware_leaks',
            'temp': self.dump_dir / 'temp_downloads',
            'parsed': self.dump_dir / 'parsed_data',
            # Novas pastas
            'leakix': self.dump_dir / 'leakix',
            'pwndb': self.dump_dir / 'pwndb',
            'github_leaks': self.dump_dir / 'github_leaks',
            'gitlab_leaks': self.dump_dir / 'gitlab_leaks',
            'pastebin': self.dump_dir / 'pastebin',
            'rentry': self.dump_dir / 'rentry',
            'ahmia': self.dump_dir / 'ahmia_results',
            'intelx_free': self.dump_dir / 'intelx',
            'ransomwatch': self.dump_dir / 'ransomwatch',
            'ransomlook': self.dump_dir / 'ransomlook',
            'archive_org': self.dump_dir / 'archive_org',
            'telegram_search': self.dump_dir / 'telegram',
            'dehashed_free': self.dump_dir / 'dehashed',
        }
        for d in self.dirs.values():
            d.mkdir(exist_ok=True)
        
        # Database para tracking
        self.db_path = self.dump_dir / 'scraper_index.db'
        self._init_db()
        
        # Sessions
        self.session = None
        self.tor_session = None
        if requests:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            })
            
            self.tor_session = requests.Session()
            self.tor_session.proxies = {
                'http': self.tor_proxy,
                'https': self.tor_proxy
            }
            self.tor_session.headers.update(self.session.headers)
        
        # Stats
        self.stats = {
            'sites_scraped': 0,
            'files_downloaded': 0,
            'bytes_downloaded': 0,
            'leaks_found': 0,
            'errors': 0
        }
    
    def _init_db(self):
        """Inicializa DB para tracking de downloads"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS downloaded_files (
                id INTEGER PRIMARY KEY,
                url TEXT UNIQUE,
                filename TEXT,
                source_site TEXT,
                download_date TEXT,
                file_size INTEGER,
                file_hash TEXT,
                parsed INTEGER DEFAULT 0
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS scraped_pages (
                id INTEGER PRIMARY KEY,
                url TEXT UNIQUE,
                site_name TEXT,
                scrape_date TEXT,
                leaks_found INTEGER,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _was_downloaded(self, url: str) -> bool:
        """Verifica se URL já foi baixada"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute('SELECT 1 FROM downloaded_files WHERE url = ?', (url,))
        result = c.fetchone() is not None
        conn.close()
        return result
    
    def _record_download(self, url: str, filename: str, source: str, size: int, file_hash: str):
        """Registra download no DB"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO downloaded_files (url, filename, source_site, download_date, file_size, file_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (url, filename, source, datetime.now().isoformat(), size, file_hash))
            conn.commit()
        except:
            pass
        finally:
            conn.close()
    
    def _hash_file(self, filepath: Path) -> str:
        """Calcula hash do arquivo"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def get_available_sites(self) -> List[Dict]:
        """Retorna lista de sites disponíveis para scraping"""
        return [
            # ========== FÓRUNS (podem requerer registro) ==========
            {
                'id': 'breachforums',
                'name': 'BreachForums',
                'urls': ['https://breachforums.st', 'https://breachforums.cx', 'https://breachforums.is'],
                'onion': 'breached65xqh64s7xbkvqgg7bmj4nj7656hcb7x4g42x753r7zmejqd.onion',
                'type': 'forum',
                'requires_tor': False,
                'description': 'Maior fórum de vazamentos'
            },
            {
                'id': 'xss',
                'name': 'XSS.is',
                'urls': ['https://xss.is'],
                'onion': 'xssforumv3isucukbxhdhwz67hoa5e2voakcfkuieq4ch257vsburuid.onion',
                'type': 'forum',
                'requires_tor': False,
                'description': 'Fórum russo de hackers'
            },
            {
                'id': 'exploit',
                'name': 'Exploit.in',
                'urls': ['https://exploit.in'],
                'type': 'forum',
                'requires_tor': False,
                'description': 'Fórum russo premium'
            },
            {
                'id': 'cracked',
                'name': 'Cracked.io',
                'urls': ['https://cracked.io', 'https://cracked.sh'],
                'type': 'forum',
                'requires_tor': False,
                'description': 'Fórum de cracking'
            },
            {
                'id': 'nulled',
                'name': 'Nulled.to',
                'urls': ['https://nulled.to', 'https://nulled.cc'],
                'type': 'forum',
                'requires_tor': False,
                'description': 'Fórum de leaks'
            },
            {
                'id': 'leakbase',
                'name': 'LeakBase.io',
                'urls': ['https://leakbase.io', 'https://leakbase.cc'],
                'type': 'database',
                'requires_tor': False,
                'description': 'Base de dados de leaks'
            },
            
            # ========== AGREGADORES DE LEAKS (FUNCIONAIS) ==========
            {
                'id': 'leakix',
                'name': 'LeakIX',
                'urls': ['https://leakix.net'],
                'type': 'aggregator',
                'requires_tor': False,
                'description': 'Agregador de serviços expostos e leaks'
            },
            {
                'id': 'pwndb',
                'name': 'PwnDB (Mirror)',
                'urls': ['https://pwndb2am4tzkvold.onion.ly', 'https://pwndb.github.io'],
                'type': 'database',
                'requires_tor': False,
                'description': 'Base de dados de credenciais vazadas'
            },
            {
                'id': 'dehashed_free',
                'name': 'Dehashed Search',
                'urls': ['https://dehashed.com/search'],
                'type': 'search',
                'requires_tor': False,
                'description': 'Busca em leaks (preview grátis)'
            },
            
            # ========== PASTES E DUMPS (MAIS ACESSÍVEIS) ==========
            {
                'id': 'pastebin',
                'name': 'Pastebin',
                'urls': ['https://pastebin.com/archive'],
                'type': 'paste',
                'requires_tor': False,
                'description': 'Arquivo público de pastes'
            },
            {
                'id': 'rentry',
                'name': 'Rentry.co',
                'urls': ['https://rentry.co'],
                'type': 'paste',
                'requires_tor': False,
                'description': 'Pastes markdown'
            },
            {
                'id': 'github_leaks',
                'name': 'GitHub (Leaked DBs)',
                'urls': ['https://github.com/search?q=leaked+database&type=repositories',
                         'https://github.com/search?q=combo+list&type=repositories',
                         'https://github.com/search?q=breach+data&type=repositories'],
                'type': 'repository',
                'requires_tor': False,
                'description': 'Repositórios com dados vazados'
            },
            {
                'id': 'gitlab_leaks',
                'name': 'GitLab (Leaked DBs)',
                'urls': ['https://gitlab.com/explore/projects?name=leak',
                         'https://gitlab.com/explore/projects?name=breach'],
                'type': 'repository',
                'requires_tor': False,
                'description': 'Repositórios GitLab com leaks'
            },
            
            # ========== BUSCADORES ESPECIAIS ==========
            {
                'id': 'ahmia',
                'name': 'Ahmia Search',
                'urls': ['https://ahmia.fi/search/?q=database+leak',
                         'https://ahmia.fi/search/?q=combo+list'],
                'type': 'search_engine',
                'requires_tor': False,
                'description': 'Buscador de sites .onion'
            },
            {
                'id': 'intelx_free',
                'name': 'IntelX (Free)',
                'urls': ['https://intelx.io'],
                'type': 'search',
                'requires_tor': False,
                'description': 'Intelligence X - busca gratuita limitada'
            },
            
            # ========== RANSOMWARE LEAK SITES ==========
            {
                'id': 'ransomwatch',
                'name': 'Ransomwatch',
                'urls': ['https://ransomwatch.telemetry.ltd'],
                'type': 'aggregator',
                'requires_tor': False,
                'description': 'Agregador de sites de ransomware'
            },
            {
                'id': 'ransomlook',
                'name': 'RansomLook',
                'urls': ['https://www.ransomlook.io'],
                'type': 'aggregator',
                'requires_tor': False,
                'description': 'Monitoramento de grupos ransomware'
            },
            
            # ========== ARQUIVO/HISTÓRICO ==========
            {
                'id': 'archive_org',
                'name': 'Archive.org',
                'urls': ['https://archive.org/search?query=database+dump',
                         'https://archive.org/search?query=leaked+credentials'],
                'type': 'archive',
                'requires_tor': False,
                'description': 'Arquivo histórico da internet'
            },
            
            # ========== TELEGRAM CHANNELS (Manual) ==========
            {
                'id': 'telegram_search',
                'name': 'Telegram (Busca)',
                'urls': ['https://t.me/s/daborern', 'https://t.me/s/leaborern'],
                'type': 'telegram',
                'requires_tor': False,
                'description': 'Canais públicos de leaks no Telegram'
            }
        ]
    
    def scrape_site(self, site_id: str, search_term: str = None, 
                    max_pages: int = 5, use_tor: bool = False) -> Dict:
        """
        Faz scraping de um site de vazamentos
        
        Args:
            site_id: ID do site (breachforums, xss, etc)
            search_term: Termo de busca (opcional)
            max_pages: Número máximo de páginas
            use_tor: Usar Tor para acesso
        
        Returns:
            Dict com resultados e arquivos baixados
        """
        sites = {s['id']: s for s in self.get_available_sites()}
        
        if site_id not in sites:
            print(f"\033[91m❌ Site '{site_id}' não encontrado\033[0m")
            return {'error': 'Site não encontrado'}
        
        site = sites[site_id]
        session = self.tor_session if use_tor else self.session
        
        result = {
            'site': site['name'],
            'search_term': search_term,
            'pages_scraped': 0,
            'leaks_found': [],
            'files_downloaded': [],
            'errors': []
        }
        
        print(f"\n\033[96m{'='*50}\033[0m")
        print(f"\033[96m   Scraping: {site['name']}\033[0m")
        print(f"\033[96m{'='*50}\033[0m")
        
        # Tentar cada URL do site
        base_url = None
        for url in site.get('urls', []):
            try:
                print(f"   Testando: {url}")
                response = session.get(url, timeout=15)
                if response.status_code == 200:
                    base_url = url
                    print(f"\033[92m   ✓ Site acessível\033[0m")
                    break
            except Exception as e:
                print(f"\033[91m   ✗ {url}: {e}\033[0m")
                continue
        
        # Se não conseguiu clearnet, tentar onion
        if not base_url and site.get('onion') and use_tor:
            try:
                onion_url = f"http://{site['onion']}"
                print(f"   Testando onion: {onion_url}")
                response = self.tor_session.get(onion_url, timeout=30)
                if response.status_code == 200:
                    base_url = onion_url
                    print(f"\033[92m   ✓ Onion acessível\033[0m")
            except Exception as e:
                print(f"\033[91m   ✗ Onion: {e}\033[0m")
        
        if not base_url:
            result['errors'].append("Nenhuma URL acessível")
            return result
        
        # Scrape específico por tipo de site
        site_type = site.get('type', 'forum')
        
        if site_id == 'breachforums':
            result = self._scrape_breachforums(base_url, session, search_term, max_pages, result)
        elif site_id == 'leakix':
            result = self._scrape_leakix(base_url, session, search_term, result)
        elif site_id == 'github_leaks':
            result = self._scrape_github(session, search_term, result)
        elif site_id == 'pastebin':
            result = self._scrape_pastebin(base_url, session, search_term, result)
        elif site_id == 'ahmia':
            result = self._scrape_ahmia(session, search_term, result)
        elif site_id == 'ransomwatch':
            result = self._scrape_ransomwatch(base_url, session, result)
        elif site_id == 'archive_org':
            result = self._scrape_archive_org(session, search_term, result)
        elif site_type in ['forum']:
            result = self._scrape_generic_forum(base_url, session, site_id, search_term, max_pages, result)
        else:
            result = self._scrape_generic_forum(base_url, session, site_id, search_term, max_pages, result)
        
        self.stats['sites_scraped'] += 1
        return result
    
    def _scrape_breachforums(self, base_url: str, session, search_term: str, 
                             max_pages: int, result: Dict) -> Dict:
        """Scrape específico para BreachForums"""
        print(f"\n   \033[93mBuscando leaks em BreachForums...\033[0m")
        
        # Seções conhecidas de leaks
        leak_sections = [
            '/Forum-Databases',
            '/Forum-Leaks',
            '/Forum-Combolists',
            '/Forum-Downloads'
        ]
        
        for section in leak_sections:
            try:
                url = f"{base_url}{section}"
                print(f"   Acessando: {section}")
                
                response = session.get(url, timeout=20)
                if response.status_code != 200:
                    continue
                
                result['pages_scraped'] += 1
                
                # Extrair links de threads (padrão simplificado)
                threads = re.findall(r'href="(/Thread[^"]+)"[^>]*>([^<]+)</a>', response.text)
                
                for thread_url, title in threads[:20]:  # Limitar por seção
                    if search_term and search_term.lower() not in title.lower():
                        continue
                    
                    result['leaks_found'].append({
                        'title': title.strip(),
                        'url': f"{base_url}{thread_url}",
                        'section': section,
                        'date': datetime.now().strftime('%Y-%m-%d')
                    })
                
            except Exception as e:
                result['errors'].append(f"{section}: {str(e)}")
                continue
        
        print(f"\n   \033[92m✓ Encontrados: {len(result['leaks_found'])} leaks\033[0m")
        
        # Salvar índice
        if result['leaks_found']:
            self._save_leak_index(result, 'breachforums')
        
        return result
    
    def _scrape_generic_forum(self, base_url: str, session, site_id: str,
                               search_term: str, max_pages: int, result: Dict) -> Dict:
        """Scrape genérico para fóruns"""
        print(f"\n   \033[93mBuscando leaks em {site_id}...\033[0m")
        
        try:
            response = session.get(base_url, timeout=20)
            if response.status_code != 200:
                result['errors'].append(f"Erro HTTP: {response.status_code}")
                return result
            
            result['pages_scraped'] += 1
            
            # Padrões genéricos de links
            patterns = [
                r'href="([^"]*(?:leak|breach|dump|database|combo)[^"]*)"[^>]*>([^<]+)</a>',
                r'href="(/(?:thread|topic)[^"]+)"[^>]*>([^<]+)</a>',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                
                for url, title in matches[:30]:
                    if search_term and search_term.lower() not in title.lower():
                        continue
                    
                    full_url = url if url.startswith('http') else f"{base_url}{url}"
                    
                    result['leaks_found'].append({
                        'title': title.strip()[:100],
                        'url': full_url,
                        'section': 'main',
                        'date': datetime.now().strftime('%Y-%m-%d')
                    })
            
        except Exception as e:
            result['errors'].append(str(e))
        
        print(f"\n   \033[92m✓ Encontrados: {len(result['leaks_found'])} potenciais leaks\033[0m")
        
        if result['leaks_found']:
            self._save_leak_index(result, site_id)
        
        return result
    
    def _scrape_leakix(self, base_url: str, session, search_term: str, result: Dict) -> Dict:
        """Scrape do LeakIX - Agregador de serviços expostos"""
        print(f"\n   \033[93mBuscando em LeakIX...\033[0m")
        
        try:
            # LeakIX tem uma API pública
            search_url = f"https://leakix.net/search?scope=leak&q={search_term or 'database'}"
            
            response = session.get(search_url, timeout=20)
            if response.status_code == 200:
                result['pages_scraped'] += 1
                
                # Extrair resultados da página
                # Padrão: links para /host/ com informações
                hosts = re.findall(r'href="/host/([^"]+)"', response.text)
                titles = re.findall(r'<h5[^>]*>([^<]+)</h5>', response.text)
                
                for i, host in enumerate(hosts[:50]):
                    title = titles[i] if i < len(titles) else f"Host: {host}"
                    result['leaks_found'].append({
                        'title': title.strip(),
                        'url': f"https://leakix.net/host/{host}",
                        'section': 'leakix',
                        'type': 'exposed_service',
                        'date': datetime.now().strftime('%Y-%m-%d')
                    })
                
                print(f"   \033[92m✓ Encontrados: {len(result['leaks_found'])} serviços expostos\033[0m")
        
        except Exception as e:
            result['errors'].append(f"LeakIX: {str(e)}")
        
        if result['leaks_found']:
            self._save_leak_index(result, 'leakix')
        
        return result
    
    def _scrape_github(self, session, search_term: str, result: Dict) -> Dict:
        """Scrape do GitHub - Repositórios com dados vazados"""
        print(f"\n   \033[93mBuscando no GitHub...\033[0m")
        
        search_queries = [
            f"{search_term} database leaked" if search_term else "database leaked credentials",
            f"{search_term} combo list" if search_term else "combo list breach",
            f"{search_term} dump sql" if search_term else "dump sql credentials"
        ]
        
        seen_repos = set()
        
        for query in search_queries:
            try:
                # Usar a busca do GitHub (rate limited mas funciona)
                search_url = f"https://github.com/search?q={query.replace(' ', '+')}&type=repositories"
                
                response = session.get(search_url, timeout=20)
                if response.status_code == 200:
                    result['pages_scraped'] += 1
                    
                    # Extrair repositórios
                    repos = re.findall(r'href="/([^/]+/[^"]+)" data-hydro-click', response.text)
                    
                    for repo in repos[:20]:
                        if repo in seen_repos or '/search' in repo:
                            continue
                        seen_repos.add(repo)
                        
                        result['leaks_found'].append({
                            'title': repo,
                            'url': f"https://github.com/{repo}",
                            'section': 'github',
                            'type': 'repository',
                            'date': datetime.now().strftime('%Y-%m-%d')
                        })
                
                time.sleep(1)  # Rate limit
                
            except Exception as e:
                result['errors'].append(f"GitHub: {str(e)}")
        
        print(f"   \033[92m✓ Encontrados: {len(result['leaks_found'])} repositórios\033[0m")
        
        if result['leaks_found']:
            self._save_leak_index(result, 'github_leaks')
        
        return result
    
    def _scrape_pastebin(self, base_url: str, session, search_term: str, result: Dict) -> Dict:
        """Scrape do Pastebin - Pastes públicos"""
        print(f"\n   \033[93mBuscando no Pastebin Archive...\033[0m")
        
        try:
            # Pastebin archive (últimos pastes públicos)
            archive_url = "https://pastebin.com/archive"
            
            response = session.get(archive_url, timeout=20)
            if response.status_code == 200:
                result['pages_scraped'] += 1
                
                # Extrair links de pastes
                pastes = re.findall(r'href="/([a-zA-Z0-9]{8})"', response.text)
                titles = re.findall(r'<a href="/[a-zA-Z0-9]{8}">([^<]+)</a>', response.text)
                
                keywords = ['password', 'email', 'combo', 'leak', 'dump', 'database', 'credential', 
                           'account', 'login', 'breach', search_term] if search_term else [
                           'password', 'email', 'combo', 'leak', 'dump', 'database']
                
                for i, paste_id in enumerate(pastes[:100]):
                    title = titles[i] if i < len(titles) else f"Paste {paste_id}"
                    
                    # Filtrar por keywords relevantes
                    if any(kw and kw.lower() in title.lower() for kw in keywords):
                        result['leaks_found'].append({
                            'title': title.strip(),
                            'url': f"https://pastebin.com/raw/{paste_id}",
                            'paste_id': paste_id,
                            'section': 'pastebin',
                            'type': 'paste',
                            'date': datetime.now().strftime('%Y-%m-%d')
                        })
                
                print(f"   \033[92m✓ Encontrados: {len(result['leaks_found'])} pastes relevantes\033[0m")
        
        except Exception as e:
            result['errors'].append(f"Pastebin: {str(e)}")
        
        if result['leaks_found']:
            self._save_leak_index(result, 'pastebin')
        
        return result
    
    def _scrape_ahmia(self, session, search_term: str, result: Dict) -> Dict:
        """Scrape do Ahmia - Buscador de sites .onion"""
        print(f"\n   \033[93mBuscando no Ahmia (onion search)...\033[0m")
        
        search_queries = [
            search_term or "database leak",
            "combo list",
            "breach dump"
        ]
        
        for query in search_queries[:2]:  # Limitar queries
            try:
                search_url = f"https://ahmia.fi/search/?q={query.replace(' ', '+')}"
                
                response = session.get(search_url, timeout=20)
                if response.status_code == 200:
                    result['pages_scraped'] += 1
                    
                    # Extrair resultados (onion URLs)
                    onions = re.findall(r'href="(https?://[a-z2-7]{56}\.onion[^"]*)"', response.text)
                    titles = re.findall(r'<h4>([^<]+)</h4>', response.text)
                    
                    for i, onion_url in enumerate(onions[:20]):
                        title = titles[i] if i < len(titles) else f"Onion site"
                        
                        result['leaks_found'].append({
                            'title': title.strip()[:80],
                            'url': onion_url,
                            'section': 'ahmia',
                            'type': 'onion_site',
                            'requires_tor': True,
                            'date': datetime.now().strftime('%Y-%m-%d')
                        })
                
                time.sleep(1)
                
            except Exception as e:
                result['errors'].append(f"Ahmia: {str(e)}")
        
        print(f"   \033[92m✓ Encontrados: {len(result['leaks_found'])} sites .onion\033[0m")
        
        if result['leaks_found']:
            self._save_leak_index(result, 'ahmia')
        
        return result
    
    def _scrape_ransomwatch(self, base_url: str, session, result: Dict) -> Dict:
        """Scrape do Ransomwatch - Agregador de sites de ransomware"""
        print(f"\n   \033[93mBuscando em Ransomwatch...\033[0m")
        
        try:
            # Ransomwatch tem uma API JSON
            api_url = "https://ransomwatch.telemetry.ltd/groups"
            
            response = session.get(api_url, timeout=20)
            if response.status_code == 200:
                result['pages_scraped'] += 1
                
                try:
                    groups = response.json()
                    
                    for group in groups:
                        group_name = group.get('name', 'Unknown')
                        locations = group.get('locations', [])
                        
                        for loc in locations:
                            result['leaks_found'].append({
                                'title': f"{group_name} - {loc.get('fqdn', 'Unknown')}",
                                'url': loc.get('slug', ''),
                                'group': group_name,
                                'section': 'ransomwatch',
                                'type': 'ransomware_group',
                                'requires_tor': '.onion' in str(loc.get('fqdn', '')),
                                'date': datetime.now().strftime('%Y-%m-%d')
                            })
                    
                    print(f"   \033[92m✓ Encontrados: {len(groups)} grupos de ransomware\033[0m")
                    
                except json.JSONDecodeError:
                    result['errors'].append("Ransomwatch: resposta não é JSON válido")
        
        except Exception as e:
            result['errors'].append(f"Ransomwatch: {str(e)}")
        
        if result['leaks_found']:
            self._save_leak_index(result, 'ransomwatch')
        
        return result
    
    def _scrape_archive_org(self, session, search_term: str, result: Dict) -> Dict:
        """Scrape do Archive.org - Arquivos históricos"""
        print(f"\n   \033[93mBuscando no Archive.org...\033[0m")
        
        search_queries = [
            search_term or "database dump",
            "leaked passwords",
            "combo list"
        ]
        
        for query in search_queries[:2]:
            try:
                # Archive.org search API
                search_url = f"https://archive.org/advancedsearch.php?q={query.replace(' ', '+')}&output=json&rows=50"
                
                response = session.get(search_url, timeout=20)
                if response.status_code == 200:
                    result['pages_scraped'] += 1
                    
                    try:
                        data = response.json()
                        docs = data.get('response', {}).get('docs', [])
                        
                        for doc in docs:
                            identifier = doc.get('identifier', '')
                            title = doc.get('title', identifier)
                            
                            result['leaks_found'].append({
                                'title': title[:100],
                                'url': f"https://archive.org/details/{identifier}",
                                'identifier': identifier,
                                'section': 'archive_org',
                                'type': 'archive',
                                'date': datetime.now().strftime('%Y-%m-%d')
                            })
                    
                    except json.JSONDecodeError:
                        pass
                
                time.sleep(1)
                
            except Exception as e:
                result['errors'].append(f"Archive.org: {str(e)}")
        
        print(f"   \033[92m✓ Encontrados: {len(result['leaks_found'])} arquivos\033[0m")
        
        if result['leaks_found']:
            self._save_leak_index(result, 'archive_org')
        
        return result
    
    def _save_leak_index(self, result: Dict, site_id: str):
        """Salva índice de leaks encontrados"""
        output_dir = self.dirs.get(site_id, self.dirs['temp'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Salvar JSON
        index_file = output_dir / f'leak_index_{timestamp}.json'
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"   \033[92m✓ Índice salvo: {index_file.name}\033[0m")
    
    def download_leak(self, url: str, site_id: str = 'temp', 
                      filename: str = None, use_tor: bool = False) -> Optional[str]:
        """
        Baixa um arquivo de leak específico
        
        Args:
            url: URL do arquivo
            site_id: ID do site para organizar pasta
            filename: Nome do arquivo (opcional)
            use_tor: Usar Tor
        
        Returns:
            Caminho do arquivo baixado
        """
        if self._was_downloaded(url):
            print(f"\033[93m   ⚠ URL já foi baixada anteriormente\033[0m")
            return None
        
        session = self.tor_session if use_tor else self.session
        output_dir = self.dirs.get(site_id, self.dirs['temp'])
        
        print(f"\n\033[96m   Baixando leak...\033[0m")
        print(f"   URL: {url[:80]}...")
        
        try:
            response = session.get(url, timeout=120, stream=True)
            
            if response.status_code != 200:
                print(f"\033[91m   ✗ Erro HTTP: {response.status_code}\033[0m")
                return None
            
            # Determinar nome do arquivo
            if not filename:
                # Tentar do header
                cd = response.headers.get('content-disposition', '')
                if 'filename=' in cd:
                    filename = re.findall(r'filename="?([^";\n]+)"?', cd)
                    filename = filename[0] if filename else None
                
                if not filename:
                    # Usar URL
                    filename = url.split('/')[-1].split('?')[0]
                    if not filename or len(filename) < 3:
                        filename = f"leak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Sanitizar filename
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            output_file = output_dir / filename
            
            # Verificar se já existe
            counter = 1
            original_name = output_file.stem
            while output_file.exists():
                output_file = output_dir / f"{original_name}_{counter}{output_file.suffix}"
                counter += 1
            
            # Baixar com progresso
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            if ProgressBar and total_size:
                pbar = ProgressBar(total=total_size, desc="Baixando", unit="B")
            else:
                pbar = None
            
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if pbar:
                            pbar.update(len(chunk))
            
            if pbar:
                pbar.finish()
            
            # Calcular hash e registrar
            file_hash = self._hash_file(output_file)
            self._record_download(url, str(output_file), site_id, downloaded, file_hash)
            
            self.stats['files_downloaded'] += 1
            self.stats['bytes_downloaded'] += downloaded
            
            print(f"\033[92m   ✓ Salvo: {output_file}\033[0m")
            print(f"   Tamanho: {downloaded:,} bytes")
            print(f"   Hash: {file_hash[:16]}...")
            
            return str(output_file)
            
        except Exception as e:
            print(f"\033[91m   ✗ Erro: {e}\033[0m")
            self.stats['errors'] += 1
            return None
    
    def parse_downloaded_file(self, filepath: str) -> Dict:
        """
        Parseia arquivo baixado e extrai dados
        
        Suporta: .txt, .csv, .json, .sql, .db
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            return {'error': 'Arquivo não encontrado'}
        
        result = {
            'file': str(filepath),
            'type': filepath.suffix,
            'size': filepath.stat().st_size,
            'credentials': [],
            'emails': [],
            'errors': []
        }
        
        print(f"\n\033[96m   Parseando: {filepath.name}\033[0m")
        
        try:
            if filepath.suffix in ['.txt', '.csv', '']:
                result = self._parse_text_file(filepath, result)
            elif filepath.suffix == '.json':
                result = self._parse_json_file(filepath, result)
            elif filepath.suffix in ['.db', '.sqlite', '.sqlite3']:
                # Usar DatabaseReader existente
                from .darkweb_monitor import DatabaseReader
                reader = DatabaseReader()
                db_result = reader.read_db_file(str(filepath))
                result['credentials'] = db_result.get('credentials', [])
            elif filepath.suffix == '.sql':
                result = self._parse_sql_file(filepath, result)
            else:
                result['errors'].append(f"Tipo não suportado: {filepath.suffix}")
        except Exception as e:
            result['errors'].append(str(e))
        
        # Salvar dados parseados
        if result['credentials'] or result['emails']:
            self._save_parsed_data(filepath, result)
        
        print(f"   \033[92m✓ Encontrados: {len(result['credentials'])} credenciais, {len(result['emails'])} emails\033[0m")
        
        return result
    
    def _parse_text_file(self, filepath: Path, result: Dict) -> Dict:
        """Parseia arquivo de texto/combo"""
        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        combo_pattern = re.compile(r'([^:;\s]+@[^:;\s]+)[;:]([^:;\s]+)')
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f):
                if line_num > 1000000:  # Limitar a 1M linhas
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Tentar extrair combo (email:senha)
                combo = combo_pattern.search(line)
                if combo:
                    result['credentials'].append({
                        'email': combo.group(1),
                        'password': combo.group(2),
                        'line': line_num + 1
                    })
                    continue
                
                # Extrair apenas emails
                emails = email_pattern.findall(line)
                result['emails'].extend(emails)
        
        # Remover duplicados de emails
        result['emails'] = list(set(result['emails']))
        
        return result
    
    def _parse_json_file(self, filepath: Path, result: Dict) -> Dict:
        """Parseia arquivo JSON"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
        
        # Se é lista, iterar
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    cred = {}
                    for key in ['email', 'mail', 'username', 'user']:
                        if key in item:
                            cred['email'] = item[key]
                            break
                    for key in ['password', 'pass', 'pwd', 'senha']:
                        if key in item:
                            cred['password'] = item[key]
                            break
                    if cred:
                        result['credentials'].append(cred)
        
        return result
    
    def _parse_sql_file(self, filepath: Path, result: Dict) -> Dict:
        """Parseia dump SQL"""
        insert_pattern = re.compile(
            r"INSERT INTO.*?VALUES\s*\((.*?)\)",
            re.IGNORECASE | re.DOTALL
        )
        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extrair valores de INSERTs
        inserts = insert_pattern.findall(content)
        
        for values in inserts:
            emails = email_pattern.findall(values)
            result['emails'].extend(emails)
        
        result['emails'] = list(set(result['emails']))
        
        return result
    
    def _save_parsed_data(self, original_file: Path, result: Dict):
        """Salva dados parseados"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = original_file.stem
        
        # Salvar credenciais
        if result['credentials']:
            cred_file = self.dirs['parsed'] / f"{base_name}_creds_{timestamp}.json"
            with open(cred_file, 'w', encoding='utf-8') as f:
                json.dump(result['credentials'], f, indent=2, ensure_ascii=False)
            print(f"   \033[92m→ Credenciais: {cred_file.name}\033[0m")
        
        # Salvar emails
        if result['emails']:
            email_file = self.dirs['parsed'] / f"{base_name}_emails_{timestamp}.txt"
            with open(email_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(result['emails']))
            print(f"   \033[92m→ Emails: {email_file.name}\033[0m")
    
    def list_downloaded_files(self) -> List[Dict]:
        """Lista arquivos já baixados"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute('''
            SELECT filename, source_site, download_date, file_size, parsed 
            FROM downloaded_files ORDER BY download_date DESC LIMIT 100
        ''')
        rows = c.fetchall()
        conn.close()
        
        return [
            {
                'filename': r[0],
                'source': r[1],
                'date': r[2],
                'size': r[3],
                'parsed': bool(r[4])
            }
            for r in rows
        ]
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas"""
        return self.stats.copy()


# ============================================
# LEITOR DE ARQUIVOS .DB (SQLite)
# ============================================

class DatabaseReader:
    """Leitor de arquivos .db de vazamentos"""
    
    # Padrões comuns de colunas em DBs de vazamento
    CREDENTIAL_PATTERNS = {
        'email': ['email', 'mail', 'e-mail', 'user_email', 'email_address', 'emailaddress'],
        'password': ['password', 'pass', 'pwd', 'senha', 'passwd', 'user_password', 'hash'],
        'username': ['username', 'user', 'login', 'user_name', 'nick', 'nickname', 'usuario'],
        'phone': ['phone', 'telefone', 'celular', 'mobile', 'phone_number', 'tel'],
        'name': ['name', 'nome', 'full_name', 'fullname', 'first_name', 'last_name'],
        'ip': ['ip', 'ip_address', 'ipaddress', 'user_ip', 'last_ip'],
        'hash': ['hash', 'password_hash', 'pwd_hash', 'md5', 'sha1', 'sha256', 'bcrypt'],
        'document': ['cpf', 'rg', 'ssn', 'document', 'documento', 'cnpj'],
        'address': ['address', 'endereco', 'street', 'city', 'state', 'zip', 'cep'],
        'card': ['card', 'credit_card', 'cc', 'card_number', 'cvv', 'expiry'],
    }
    
    def __init__(self, output_dir: str = "data/leaks"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {
            'files_processed': 0,
            'tables_found': 0,
            'records_extracted': 0,
            'credentials_found': 0,
            'duplicates_skipped': 0
        }
    
    def read_db_file(self, db_path: str) -> Dict:
        """Lê um arquivo .db e retorna estrutura completa"""
        result = {
            'file': db_path,
            'tables': [],
            'total_records': 0,
            'credentials': [],
            'errors': []
        }
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Listar todas as tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table_name in tables:
                if table_name.startswith('sqlite_'):
                    continue
                    
                table_info = self._analyze_table(conn, table_name)
                result['tables'].append(table_info)
                result['total_records'] += table_info['row_count']
                
                # Extrair credenciais se encontradas
                if table_info['has_credentials']:
                    creds = self._extract_credentials(conn, table_name, table_info)
                    result['credentials'].extend(creds)
            
            conn.close()
            self.stats['files_processed'] += 1
            self.stats['tables_found'] += len(tables)
            
        except sqlite3.Error as e:
            result['errors'].append(f"SQLite error: {str(e)}")
        except Exception as e:
            result['errors'].append(f"Error: {str(e)}")
        
        return result
    
    def _analyze_table(self, conn: sqlite3.Connection, table_name: str) -> Dict:
        """Analisa estrutura de uma tabela"""
        cursor = conn.cursor()
        
        # Obter colunas
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        columns = []
        credential_columns = {}
        
        for col in cursor.fetchall():
            col_name = col[1].lower()
            col_type = col[2]
            columns.append({'name': col[1], 'type': col_type})
            
            # Identificar colunas de credenciais
            for cred_type, patterns in self.CREDENTIAL_PATTERNS.items():
                if any(p in col_name for p in patterns):
                    credential_columns[cred_type] = col[1]
                    break
        
        # Contar registros
        cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
        row_count = cursor.fetchone()[0]
        
        return {
            'name': table_name,
            'columns': columns,
            'row_count': row_count,
            'credential_columns': credential_columns,
            'has_credentials': len(credential_columns) > 0
        }
    
    def _extract_credentials(self, conn: sqlite3.Connection, table_name: str, 
                            table_info: Dict, limit: int = None) -> List[Dict]:
        """Extrai credenciais de uma tabela"""
        credentials = []
        cursor = conn.cursor()
        
        cred_cols = table_info['credential_columns']
        if not cred_cols:
            return credentials
        
        # Construir query
        select_cols = list(cred_cols.values())
        query = f"SELECT {', '.join(select_cols)} FROM '{table_name}'"
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            cursor.execute(query)
            
            for row in cursor.fetchall():
                cred = {}
                for i, (cred_type, col_name) in enumerate(cred_cols.items()):
                    value = row[i]
                    if value:
                        cred[cred_type] = str(value)
                
                if cred:
                    cred['source_table'] = table_name
                    credentials.append(cred)
                    self.stats['credentials_found'] += 1
                    
        except Exception as e:
            pass
        
        return credentials
    
    def scan_directory(self, directory: str, recursive: bool = True) -> List[Dict]:
        """Escaneia diretório em busca de arquivos .db"""
        results = []
        path = Path(directory)
        
        if not path.exists():
            return results
        
        pattern = "**/*.db" if recursive else "*.db"
        db_files = list(path.glob(pattern))
        
        # Também buscar .sqlite e .sqlite3
        db_files.extend(path.glob("**/*.sqlite" if recursive else "*.sqlite"))
        db_files.extend(path.glob("**/*.sqlite3" if recursive else "*.sqlite3"))
        
        if ProgressBar and db_files:
            pbar = ProgressBar(len(db_files), "   Processando DBs", show_speed=True)
        else:
            pbar = None
        
        for db_file in db_files:
            result = self.read_db_file(str(db_file))
            results.append(result)
            
            if pbar:
                pbar.update(1)
        
        if pbar:
            pbar.finish(f"{len(db_files)} arquivos processados")
        
        return results
    
    def export_credentials(self, credentials: List[Dict], output_file: str, 
                          format: str = 'csv') -> bool:
        """Exporta credenciais para arquivo"""
        try:
            output_path = self.output_dir / output_file
            
            if format == 'csv':
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    if credentials:
                        writer = csv.DictWriter(f, fieldnames=credentials[0].keys())
                        writer.writeheader()
                        writer.writerows(credentials)
            
            elif format == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(credentials, f, indent=2, ensure_ascii=False)
            
            elif format == 'txt':
                with open(output_path, 'w', encoding='utf-8') as f:
                    for cred in credentials:
                        if 'email' in cred and 'password' in cred:
                            f.write(f"{cred['email']}:{cred['password']}\n")
                        elif 'username' in cred and 'password' in cred:
                            f.write(f"{cred['username']}:{cred['password']}\n")
            
            return True
        except Exception as e:
            print(f"Erro ao exportar: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas de processamento"""
        return self.stats.copy()


# ============================================
# SISTEMA DE ORGANIZAÇÃO E DEDUPLICAÇÃO
# ============================================

class LeakOrganizer:
    """Organiza e deduplica vazamentos em pastas estruturadas"""
    
    def __init__(self, base_dir: str = "data/leaks_organized"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Estrutura de pastas
        self.dirs = {
            'emails': self.base_dir / 'emails',
            'passwords': self.base_dir / 'passwords', 
            'combos': self.base_dir / 'combos',
            'usernames': self.base_dir / 'usernames',
            'phones': self.base_dir / 'phones',
            'documents': self.base_dir / 'documents',  # CPF, RG, etc
            'cards': self.base_dir / 'cards',
            'hashes': self.base_dir / 'hashes',
            'raw': self.base_dir / 'raw_imports',
            'by_domain': self.base_dir / 'by_domain',
            'by_source': self.base_dir / 'by_source',
        }
        
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Banco de dados de deduplicação
        self.dedup_db_path = self.base_dir / 'deduplication.db'
        self._init_dedup_db()
        
        # Estatísticas
        self.stats = {
            'total_processed': 0,
            'unique_added': 0,
            'duplicates_skipped': 0,
            'emails': 0,
            'passwords': 0,
            'combos': 0,
        }
    
    def _init_dedup_db(self):
        """Inicializa banco de dados de deduplicação"""
        conn = sqlite3.connect(str(self.dedup_db_path))
        c = conn.cursor()
        
        # Tabela de hashes para deduplicação rápida
        c.execute('''
            CREATE TABLE IF NOT EXISTS seen_hashes (
                hash TEXT PRIMARY KEY,
                data_type TEXT,
                source TEXT,
                added_date TEXT
            )
        ''')
        
        # Índice de emails
        c.execute('''
            CREATE TABLE IF NOT EXISTS email_index (
                email TEXT PRIMARY KEY,
                domain TEXT,
                first_seen TEXT,
                sources TEXT,
                breach_count INTEGER DEFAULT 1
            )
        ''')
        
        # Índice de senhas (apenas hashes, nunca plaintext para segurança)
        c.execute('''
            CREATE TABLE IF NOT EXISTS password_hashes (
                hash TEXT PRIMARY KEY,
                occurrences INTEGER DEFAULT 1,
                first_seen TEXT
            )
        ''')
        
        # Histórico de imports
        c.execute('''
            CREATE TABLE IF NOT EXISTS import_history (
                id INTEGER PRIMARY KEY,
                filename TEXT,
                file_hash TEXT UNIQUE,
                import_date TEXT,
                records_count INTEGER,
                unique_count INTEGER,
                duplicate_count INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _hash_data(self, data: str) -> str:
        """Gera hash SHA256 de dados"""
        return hashlib.sha256(data.encode('utf-8', errors='ignore')).hexdigest()
    
    def _hash_file(self, file_path: str) -> str:
        """Gera hash de arquivo para verificar duplicatas"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def is_duplicate(self, data: str, data_type: str = 'generic') -> bool:
        """Verifica se dado já foi processado"""
        data_hash = self._hash_data(data)
        
        conn = sqlite3.connect(str(self.dedup_db_path))
        c = conn.cursor()
        
        c.execute('SELECT 1 FROM seen_hashes WHERE hash = ?', (data_hash,))
        exists = c.fetchone() is not None
        
        conn.close()
        return exists
    
    def mark_as_seen(self, data: str, data_type: str, source: str = 'unknown'):
        """Marca dado como processado"""
        data_hash = self._hash_data(data)
        
        conn = sqlite3.connect(str(self.dedup_db_path))
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT OR IGNORE INTO seen_hashes (hash, data_type, source, added_date)
                VALUES (?, ?, ?, ?)
            ''', (data_hash, data_type, source, datetime.now().isoformat()))
            conn.commit()
        except:
            pass
        finally:
            conn.close()
    
    def was_file_imported(self, file_path: str) -> bool:
        """Verifica se arquivo já foi importado"""
        file_hash = self._hash_file(file_path)
        
        conn = sqlite3.connect(str(self.dedup_db_path))
        c = conn.cursor()
        
        c.execute('SELECT 1 FROM import_history WHERE file_hash = ?', (file_hash,))
        exists = c.fetchone() is not None
        
        conn.close()
        return exists
    
    def record_import(self, file_path: str, records: int, unique: int, duplicates: int):
        """Registra import no histórico"""
        file_hash = self._hash_file(file_path)
        filename = Path(file_path).name
        
        conn = sqlite3.connect(str(self.dedup_db_path))
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT OR REPLACE INTO import_history 
                (filename, file_hash, import_date, records_count, unique_count, duplicate_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (filename, file_hash, datetime.now().isoformat(), records, unique, duplicates))
            conn.commit()
        except:
            pass
        finally:
            conn.close()
    
    def organize_credentials(self, credentials: List[Dict], source: str = 'unknown') -> Dict:
        """Organiza credenciais em pastas e deduplica"""
        result = {
            'processed': 0,
            'unique': 0,
            'duplicates': 0,
            'by_type': {}
        }
        
        # Arquivos de saída
        output_files = {}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if ProgressBar and credentials:
            pbar = ProgressBar(len(credentials), "   Organizando", show_speed=True)
        else:
            pbar = None
        
        for cred in credentials:
            result['processed'] += 1
            self.stats['total_processed'] += 1
            
            # Criar chave única para deduplicação
            unique_key = json.dumps(cred, sort_keys=True)
            
            if self.is_duplicate(unique_key, 'credential'):
                result['duplicates'] += 1
                self.stats['duplicates_skipped'] += 1
                if pbar:
                    pbar.update(1)
                continue
            
            result['unique'] += 1
            self.stats['unique_added'] += 1
            self.mark_as_seen(unique_key, 'credential', source)
            
            # Organizar por tipo
            if 'email' in cred:
                email = cred['email']
                domain = email.split('@')[-1] if '@' in email else 'unknown'
                
                # Salvar em emails
                self._append_to_file(
                    self.dirs['emails'] / f'emails_{timestamp}.txt',
                    email
                )
                
                # Salvar por domínio
                domain_dir = self.dirs['by_domain'] / domain
                domain_dir.mkdir(exist_ok=True)
                self._append_to_file(domain_dir / 'emails.txt', email)
                
                # Indexar email
                self._index_email(email, domain, source)
                self.stats['emails'] += 1
                result['by_type']['emails'] = result['by_type'].get('emails', 0) + 1
            
            if 'password' in cred:
                password = cred['password']
                
                # Salvar senha (hash do arquivo para referência)
                self._append_to_file(
                    self.dirs['passwords'] / f'passwords_{timestamp}.txt',
                    password
                )
                
                # Indexar hash da senha
                self._index_password_hash(password)
                self.stats['passwords'] += 1
                result['by_type']['passwords'] = result['by_type'].get('passwords', 0) + 1
            
            # Se tem email E senha, é um combo
            if 'email' in cred and 'password' in cred:
                combo = f"{cred['email']}:{cred['password']}"
                self._append_to_file(
                    self.dirs['combos'] / f'combos_{timestamp}.txt',
                    combo
                )
                self.stats['combos'] += 1
                result['by_type']['combos'] = result['by_type'].get('combos', 0) + 1
            
            # Username
            if 'username' in cred:
                self._append_to_file(
                    self.dirs['usernames'] / f'usernames_{timestamp}.txt',
                    cred['username']
                )
                result['by_type']['usernames'] = result['by_type'].get('usernames', 0) + 1
            
            # Telefone
            if 'phone' in cred:
                self._append_to_file(
                    self.dirs['phones'] / f'phones_{timestamp}.txt',
                    cred['phone']
                )
                result['by_type']['phones'] = result['by_type'].get('phones', 0) + 1
            
            # Documentos (CPF, etc)
            if 'document' in cred:
                self._append_to_file(
                    self.dirs['documents'] / f'documents_{timestamp}.txt',
                    cred['document']
                )
                result['by_type']['documents'] = result['by_type'].get('documents', 0) + 1
            
            # Por fonte
            source_dir = self.dirs['by_source'] / source.replace('/', '_').replace('\\', '_')
            source_dir.mkdir(exist_ok=True)
            self._append_to_file(
                source_dir / f'data_{timestamp}.json',
                json.dumps(cred, ensure_ascii=False),
                mode='jsonl'
            )
            
            if pbar:
                pbar.update(1)
        
        if pbar:
            pbar.finish(f"✓ {result['unique']} únicos, {result['duplicates']} duplicados")
        
        return result
    
    def _append_to_file(self, file_path: Path, data: str, mode: str = 'txt'):
        """Adiciona dados a arquivo"""
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(data + '\n')
    
    def _index_email(self, email: str, domain: str, source: str):
        """Indexa email no banco de dados"""
        conn = sqlite3.connect(str(self.dedup_db_path))
        c = conn.cursor()
        
        try:
            # Verificar se existe
            c.execute('SELECT sources, breach_count FROM email_index WHERE email = ?', (email,))
            row = c.fetchone()
            
            if row:
                # Atualizar
                sources = row[0] + ',' + source if source not in row[0] else row[0]
                c.execute('''
                    UPDATE email_index 
                    SET sources = ?, breach_count = breach_count + 1
                    WHERE email = ?
                ''', (sources, email))
            else:
                # Inserir
                c.execute('''
                    INSERT INTO email_index (email, domain, first_seen, sources)
                    VALUES (?, ?, ?, ?)
                ''', (email, domain, datetime.now().isoformat(), source))
            
            conn.commit()
        except:
            pass
        finally:
            conn.close()
    
    def _index_password_hash(self, password: str):
        """Indexa hash de senha"""
        pwd_hash = self._hash_data(password)
        
        conn = sqlite3.connect(str(self.dedup_db_path))
        c = conn.cursor()
        
        try:
            c.execute('SELECT occurrences FROM password_hashes WHERE hash = ?', (pwd_hash,))
            row = c.fetchone()
            
            if row:
                c.execute('''
                    UPDATE password_hashes SET occurrences = occurrences + 1 WHERE hash = ?
                ''', (pwd_hash,))
            else:
                c.execute('''
                    INSERT INTO password_hashes (hash, first_seen) VALUES (?, ?)
                ''', (pwd_hash, datetime.now().isoformat()))
            
            conn.commit()
        except:
            pass
        finally:
            conn.close()
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas"""
        return self.stats.copy()
    
    def get_import_history(self) -> List[Dict]:
        """Retorna histórico de imports"""
        conn = sqlite3.connect(str(self.dedup_db_path))
        c = conn.cursor()
        
        c.execute('''
            SELECT filename, import_date, records_count, unique_count, duplicate_count 
            FROM import_history ORDER BY import_date DESC LIMIT 50
        ''')
        rows = c.fetchall()
        conn.close()
        
        return [
            {
                'filename': r[0],
                'date': r[1],
                'records': r[2],
                'unique': r[3],
                'duplicates': r[4]
            }
            for r in rows
        ]
    
    def search_email(self, email: str) -> Optional[Dict]:
        """Busca email no índice"""
        conn = sqlite3.connect(str(self.dedup_db_path))
        c = conn.cursor()
        
        c.execute('SELECT * FROM email_index WHERE email = ?', (email,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                'email': row[0],
                'domain': row[1],
                'first_seen': row[2],
                'sources': row[3].split(',') if row[3] else [],
                'breach_count': row[4]
            }
        return None
    
    def search_by_domain(self, domain: str) -> List[str]:
        """Busca emails por domínio"""
        conn = sqlite3.connect(str(self.dedup_db_path))
        c = conn.cursor()
        
        c.execute('SELECT email FROM email_index WHERE domain = ?', (domain,))
        rows = c.fetchall()
        conn.close()
        
        return [r[0] for r in rows]


@dataclass
class LeakAlert:
    """Alerta de vazamento."""
    source: str
    date_found: str
    data_type: str
    affected_emails: List[str]
    affected_domains: List[str]
    severity: str
    description: str
    raw_data: Optional[Dict]
    
    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "date_found": self.date_found,
            "data_type": self.data_type,
            "affected_emails": self.affected_emails,
            "affected_domains": self.affected_domains,
            "severity": self.severity,
            "description": self.description
        }


@dataclass
class MonitoredTarget:
    """Alvo monitorado."""
    target_type: str  # email, domain, keyword
    value: str
    added_date: str
    last_check: Optional[str]
    alerts_count: int
    active: bool
    
    def to_dict(self) -> Dict:
        return {
            "target_type": self.target_type,
            "value": self.value,
            "added_date": self.added_date,
            "last_check": self.last_check,
            "alerts_count": self.alerts_count,
            "active": self.active
        }


class HIBPChecker:
    """Verificador Have I Been Pwned."""
    
    API_URL = "https://haveibeenpwned.com/api/v3"
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session() if requests else None
        
        if self.session:
            headers = {
                'User-Agent': 'DarkwebMonitor/1.0',
            }
            if api_key:
                headers['hibp-api-key'] = api_key
            self.session.headers.update(headers)
    
    def check_email(self, email: str) -> List[Dict]:
        """Verifica se email foi vazado."""
        if not self.session or not self.api_key:
            return [{"note": "API key HIBP necessária para verificação de email"}]
        
        try:
            url = f"{self.API_URL}/breachedaccount/{email}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return []
        except Exception as e:
            return [{"error": str(e)}]
        
        return []
    
    def check_password(self, password: str) -> Dict:
        """Verifica se senha foi vazada usando k-anonymity."""
        # Hash SHA-1 da senha
        sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]
        
        try:
            url = f"https://api.pwnedpasswords.com/range/{prefix}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                hashes = response.text.splitlines()
                
                for line in hashes:
                    h, count = line.split(':')
                    if h == suffix:
                        return {
                            "pwned": True,
                            "count": int(count),
                            "message": f"Senha encontrada {count} vezes em vazamentos"
                        }
                
                return {
                    "pwned": False,
                    "count": 0,
                    "message": "Senha não encontrada em vazamentos conhecidos"
                }
        except Exception as e:
            return {"error": str(e)}
        
        return {"error": "Falha na verificação"}
    
    def get_breaches(self, domain: Optional[str] = None) -> List[Dict]:
        """Lista todos os breaches conhecidos."""
        try:
            url = f"{self.API_URL}/breaches"
            if domain:
                url += f"?domain={domain}"
            
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        
        return []


class DarkwebMonitor:
    """Monitor de vazamentos na darkweb."""
    
    def __init__(self, db_path: str = "darkweb_monitor.db", 
                 tor_proxy: Optional[str] = None):
        self.db_path = db_path
        self.tor_proxy = tor_proxy or "socks5h://127.0.0.1:9050"
        self.hibp = HIBPChecker()
        self._init_db()
        
        # Session com Tor
        self.tor_session = None
        if requests:
            self.tor_session = requests.Session()
            self.tor_session.proxies = {
                'http': self.tor_proxy,
                'https': self.tor_proxy
            }
    
    def _init_db(self):
        """Inicializa banco de dados."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Tabela de alvos monitorados
        c.execute('''
            CREATE TABLE IF NOT EXISTS monitored_targets (
                id INTEGER PRIMARY KEY,
                target_type TEXT,
                value TEXT UNIQUE,
                added_date TEXT,
                last_check TEXT,
                alerts_count INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1
            )
        ''')
        
        # Tabela de alertas
        c.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY,
                target_id INTEGER,
                source TEXT,
                date_found TEXT,
                data_type TEXT,
                severity TEXT,
                description TEXT,
                raw_data TEXT,
                notified INTEGER DEFAULT 0,
                FOREIGN KEY (target_id) REFERENCES monitored_targets(id)
            )
        ''')
        
        # Tabela de fontes conhecidas
        c.execute('''
            CREATE TABLE IF NOT EXISTS known_sources (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                url TEXT,
                onion_url TEXT,
                last_scraped TEXT,
                active INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_target(self, target_type: str, value: str) -> bool:
        """Adiciona alvo para monitoramento."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT INTO monitored_targets (target_type, value, added_date)
                VALUES (?, ?, ?)
            ''', (target_type, value.lower(), datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def remove_target(self, value: str) -> bool:
        """Remove alvo do monitoramento."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('DELETE FROM monitored_targets WHERE value = ?', (value.lower(),))
        deleted = c.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def list_targets(self) -> List[MonitoredTarget]:
        """Lista todos os alvos monitorados."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT target_type, value, added_date, last_check, alerts_count, active FROM monitored_targets')
        rows = c.fetchall()
        conn.close()
        
        return [
            MonitoredTarget(
                target_type=row[0],
                value=row[1],
                added_date=row[2],
                last_check=row[3],
                alerts_count=row[4],
                active=bool(row[5])
            )
            for row in rows
        ]
    
    def check_target(self, value: str) -> List[Dict]:
        """Verifica um alvo específico."""
        results = []
        
        # Verificar HIBP
        if '@' in value:
            hibp_results = self.hibp.check_email(value)
            for breach in hibp_results:
                if not breach.get("error") and not breach.get("note"):
                    results.append({
                        "source": "HIBP",
                        "breach": breach.get("Name", "Unknown"),
                        "date": breach.get("BreachDate", "Unknown"),
                        "data_classes": breach.get("DataClasses", []),
                        "is_verified": breach.get("IsVerified", False)
                    })
        
        return results
    
    def check_password_leak(self, password: str) -> Dict:
        """Verifica se senha foi vazada."""
        return self.hibp.check_password(password)
    
    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """Retorna alertas recentes."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT a.source, a.date_found, a.data_type, a.severity, a.description, t.value
            FROM alerts a
            JOIN monitored_targets t ON a.target_id = t.id
            ORDER BY a.date_found DESC
            LIMIT ?
        ''', (limit,))
        
        rows = c.fetchall()
        conn.close()
        
        return [
            {
                "source": row[0],
                "date_found": row[1],
                "data_type": row[2],
                "severity": row[3],
                "description": row[4],
                "target": row[5]
            }
            for row in rows
        ]
    
    def add_known_source(self, name: str, url: str, onion_url: Optional[str] = None):
        """Adiciona fonte conhecida de vazamentos."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT INTO known_sources (name, url, onion_url)
                VALUES (?, ?, ?)
            ''', (name, url, onion_url))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()
    
    def get_known_sources(self) -> List[Dict]:
        """Lista fontes conhecidas."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT name, url, onion_url, last_scraped, active FROM known_sources')
        rows = c.fetchall()
        conn.close()
        
        return [
            {
                "name": row[0],
                "url": row[1],
                "onion_url": row[2],
                "last_scraped": row[3],
                "active": bool(row[4])
            }
            for row in rows
        ]
    
    def check_tor_connection(self) -> bool:
        """Verifica conexão com Tor."""
        if not self.tor_session:
            return False
        
        try:
            response = self.tor_session.get(
                "https://check.torproject.org/api/ip",
                timeout=10
            )
            data = response.json()
            return data.get("IsTor", False)
        except Exception:
            return False
    
    def start_tor(self) -> bool:
        """Inicia o Tor usando o TorManager do projeto."""
        print("\n\033[93m🧅 Iniciando Tor via TorManager...\033[0m")
        
        try:
            # Importar TorManager do projeto
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from tor.tor_manager import TorManager
            
            # Inicializar TorManager
            tor_manager = TorManager()
            
            # Verificar se Tor está instalado
            if not tor_manager.is_tor_installed():
                print("\n\033[93m⚠️ Tor não instalado. Instalando...\033[0m")
                if not tor_manager.download_tor():
                    print("\033[91m❌ Falha ao instalar Tor\033[0m")
                    return False
            
            # Iniciar Tor
            if tor_manager.start_tor():
                # Atualizar session com as novas configurações
                self.tor_proxy = f"socks5h://127.0.0.1:{tor_manager.config.get('socks_port', 9050)}"
                if requests:
                    self.tor_session = requests.Session()
                    self.tor_session.proxies = {
                        'http': self.tor_proxy,
                        'https': self.tor_proxy
                    }
                return True
            else:
                print("\033[91m❌ Falha ao iniciar Tor\033[0m")
                return False
                
        except ImportError as e:
            print(f"\033[91m❌ TorManager não encontrado: {e}\033[0m")
            print("\n\033[93mTentando método alternativo...\033[0m")
            return self._start_tor_fallback()
        except Exception as e:
            print(f"\033[91m❌ Erro ao iniciar Tor: {e}\033[0m")
            return self._start_tor_fallback()
    
    def _start_tor_fallback(self) -> bool:
        """Método alternativo para iniciar Tor."""
        import subprocess
        import platform
        
        print("\n\033[93m🧅 Tentando iniciar Tor (fallback)...\033[0m")
        
        system = platform.system().lower()
        
        # Primeiro, tentar o Tor do projeto
        project_tor = Path(__file__).parent.parent / "tor" / "tor_bundle" / "tor"
        if system == 'windows':
            project_tor = project_tor / "tor.exe"
        else:
            project_tor = project_tor / "tor"
        
        torrc_path = Path(__file__).parent.parent / "tor" / "tor_bundle" / "torrc"
        
        if project_tor.exists():
            print(f"   Encontrado Tor do projeto: {project_tor}")
            try:
                if system == 'windows':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 6
                    
                    cmd = [str(project_tor)]
                    if torrc_path.exists():
                        cmd.extend(["-f", str(torrc_path)])
                    
                    subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        startupinfo=startupinfo
                    )
                else:
                    cmd = [str(project_tor)]
                    if torrc_path.exists():
                        cmd.extend(["-f", str(torrc_path)])
                    
                    subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                
                print("\033[92m   ✓ Tor do projeto iniciado!\033[0m")
                print("   Aguardando conexão...")
                
                for i in range(60):
                    time.sleep(1)
                    if self.check_tor_connection():
                        print(f"\033[92m   ✓ Tor conectado! (levou {i+1}s)\033[0m")
                        return True
                    if i % 10 == 0 and i > 0:
                        print(f"   Aguardando... {i}s")
                
                print("\033[93m   ⚠ Tor iniciou mas não conectou em 60s\033[0m")
                
            except Exception as e:
                print(f"\033[91m   Erro: {e}\033[0m")
        
        print("\033[91m   ❌ Não foi possível iniciar o Tor.\033[0m")
        print("\n\033[93m   Você pode iniciar manualmente:\033[0m")
        print(f"   python -c \"from tools.tor.tor_manager import TorManager; t = TorManager(); t.start_tor()\"")
        print("\n   Ou instalar o Tor:")
        print("   • Windows: https://www.torproject.org/download/")
        print("   • Linux: sudo apt install tor")
        
        return False
    
    def export_data(self, output_file: str):
        """Exporta dados para JSON."""
        data = {
            "targets": [t.to_dict() for t in self.list_targets()],
            "alerts": self.get_alerts(),
            "sources": self.get_known_sources(),
            "exported_at": datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def interactive_menu():
    """Menu interativo do Darkweb Monitor."""
    if not requests:
        print("❌ Módulo requests não encontrado. Instale com: pip install requests")
        input("Pressione Enter...")
        return
    
    # Inicializar componentes
    monitor = DarkwebMonitor()
    db_reader = DatabaseReader()
    organizer = LeakOrganizer()
    site_checker = SiteChecker()
    downloader = LeakDownloader()
    scraper = SiteLeakScraper()  # Novo scraper de sites
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
\033[95m╔══════════════════════════════════════════════════════════════╗
║\033[0m          \033[1;35m🌑 DARKWEB MONITOR - Olho de Deus\033[0m                   \033[95m║
╠══════════════════════════════════════════════════════════════╣\033[0m
║                                                              ║
║  \033[93m━━━ MONITORAMENTO ━━━\033[0m                                      ║
║  \033[93m[1]\033[0m ➕ Adicionar Alvo para Monitoramento                    ║
║  \033[93m[2]\033[0m 📋 Listar Alvos Monitorados                             ║
║  \033[93m[3]\033[0m 🔍 Verificar Email (HIBP)                               ║
║  \033[93m[4]\033[0m 🔐 Verificar Senha Vazada                               ║
║  \033[93m[5]\033[0m 🚨 Ver Alertas                                          ║
║                                                              ║
║  \033[96m━━━ IMPORTAR LEAKS ━━━\033[0m                                     ║
║  \033[96m[6]\033[0m 📂 Importar Arquivo .db/.sqlite                         ║
║  \033[96m[7]\033[0m 📁 Escanear Pasta (múltiplos DBs)                       ║
║  \033[96m[8]\033[0m 📜 Histórico de Imports                                 ║
║                                                              ║
║  \033[91m━━━ SCRAPING DE SITES (SEM API) ━━━\033[0m                        ║
║  \033[91m[24]\033[0m 🌐 Ver Sites Disponíveis                                ║
║  \033[91m[25]\033[0m 🔍 Fazer Scraping de Site                               ║
║  \033[91m[26]\033[0m 📥 Baixar Leak de URL                                   ║
║  \033[91m[27]\033[0m 📋 Parsear Arquivo Baixado                              ║
║  \033[91m[28]\033[0m 📊 Listar Arquivos Baixados                             ║
║                                                              ║
║  \033[97m━━━ SCANNER AUTOMÁTICO DE FONTES ━━━\033[0m                       ║
║  \033[97m[29]\033[0m 🔍 Escanear TODAS as Fontes (online/offline)           ║
║  \033[97m[30]\033[0m 🔎 Descobrir NOVAS Fontes Automaticamente              ║
║  \033[97m[31]\033[0m 📋 Ver Fontes Funcionais                               ║
║                                                              ║
║  \033[90m━━━ APIS (STANDBY) ━━━\033[0m                                     ║
║  \033[90m[18]\033[0m 📥 Baixar Lista de Breaches (HIBP)                     ║
║  \033[90m[19]\033[0m 🔎 Buscar Email em Múltiplas APIs                      ║
║  \033[90m[20]\033[0m 📋 Baixar Paste                                        ║
║  \033[90m[21]\033[0m 🔍 Buscar no IntelX                                    ║
║  \033[90m[22]\033[0m 📥 Baixar de URL (API)                                 ║
║  \033[90m[23]\033[0m 🔑 Configurar API Keys                                 ║
║                                                              ║
║  \033[92m━━━ BUSCAR DADOS ━━━\033[0m                                       ║
║  \033[92m[9]\033[0m 🔎 Buscar Email no Índice                               ║
║  \033[92m[10]\033[0m 🌐 Buscar por Domínio                                   ║
║  \033[92m[11]\033[0m 📊 Estatísticas do Banco                               ║
║                                                              ║
║  \033[94m━━━ FONTES & TOR ━━━\033[0m                                       ║
║  \033[94m[12]\033[0m 🌑 Listar Sites de Vazamento                           ║
║  \033[94m[13]\033[0m 🧅 Verificar Conexão Tor                               ║
║  \033[94m[14]\033[0m 📊 Listar Breaches (HIBP)                              ║
║  \033[94m[15]\033[0m 🔗 Testar Status dos Sites                             ║
║  \033[94m[16]\033[0m 🔍 Buscar URLs Atualizadas                             ║
║                                                              ║
║  \033[95m[17]\033[0m 💾 Exportar Dados                                      ║
║  \033[91m[0]\033[0m  Voltar                                                 ║
\033[95m╚══════════════════════════════════════════════════════════════╝\033[0m
        """)
        
        escolha = input("\033[92mOpção: \033[0m").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n\033[93m=== Adicionar Alvo ===\033[0m")
            print("Tipos: [1] Email [2] Domínio [3] Keyword")
            tipo_op = input("Tipo: ").strip()
            
            tipos = {"1": "email", "2": "domain", "3": "keyword"}
            target_type = tipos.get(tipo_op, "email")
            
            value = input(f"Valor ({target_type}): ").strip()
            
            if not value:
                continue
            
            if monitor.add_target(target_type, value):
                print(f"\n\033[92m✅ Alvo '{value}' adicionado para monitoramento\033[0m")
            else:
                print(f"\n\033[93m⚠️ Alvo '{value}' já está sendo monitorado\033[0m")
        
        elif escolha == '2':
            print("\n\033[93m=== Alvos Monitorados ===\033[0m")
            targets = monitor.list_targets()
            
            if targets:
                print(f"\n📋 {len(targets)} alvo(s) monitorado(s):")
                for t in targets:
                    status = "\033[92m🟢\033[0m" if t.active else "\033[91m🔴\033[0m"
                    print(f"\n   {status} [{t.target_type.upper()}] {t.value}")
                    print(f"      Adicionado: {t.added_date[:10]}")
                    print(f"      Alertas: {t.alerts_count}")
                    if t.last_check:
                        print(f"      Última verificação: {t.last_check[:10]}")
            else:
                print("\n📭 Nenhum alvo monitorado")
        
        elif escolha == '3':
            print("\n\033[93m=== Verificar Email ===\033[0m")
            email = input("Email: ").strip()
            
            if not email:
                continue
            
            print(f"\nVerificando {email}...")
            results = monitor.check_target(email)
            
            if results:
                print(f"\n\033[91m⚠️ {len(results)} vazamento(s) encontrado(s):\033[0m")
                for r in results:
                    print(f"\n   \033[91m🔴 {r.get('breach', 'Unknown')}\033[0m")
                    print(f"      Data: {r.get('date', 'Unknown')}")
                    print(f"      Verificado: {'Sim' if r.get('is_verified') else 'Não'}")
                    
                    data_classes = r.get('data_classes', [])
                    if data_classes:
                        print(f"      Dados vazados: {', '.join(data_classes[:5])}")
            else:
                print(f"\n\033[92m✅ Nenhum vazamento encontrado para {email}\033[0m")
                print("   (Nota: Pode requerer API key do HIBP para resultados completos)")
        
        elif escolha == '4':
            print("\n\033[93m=== Verificar Senha ===\033[0m")
            print("\033[96m⚠️ A senha NÃO é enviada para nenhum servidor (usa k-anonymity)\033[0m")
            import getpass
            password = getpass.getpass("Senha: ")
            
            if not password:
                continue
            
            result = monitor.check_password_leak(password)
            
            if result.get("error"):
                print(f"\n\033[91m❌ Erro: {result['error']}\033[0m")
            elif result.get("pwned"):
                count = result.get("count", 0)
                print(f"\n\033[91m🔴 SENHA VAZADA!\033[0m")
                print(f"   Encontrada \033[91m{count:,}\033[0m vezes em vazamentos")
                print(f"   \033[93m⚠️ NÃO use esta senha!\033[0m")
            else:
                print(f"\n\033[92m✅ Senha não encontrada em vazamentos conhecidos\033[0m")
                print(f"   Isso não garante que seja segura, apenas que não foi vazada publicamente")
        
        elif escolha == '5':
            print("\n\033[93m=== Alertas Recentes ===\033[0m")
            alerts = monitor.get_alerts()
            
            if alerts:
                print(f"\n🚨 {len(alerts)} alerta(s):")
                for a in alerts:
                    sev_icon = {"critical": "\033[91m🔴\033[0m", "high": "\033[93m🟠\033[0m", "medium": "\033[93m🟡\033[0m", "low": "\033[92m🟢\033[0m"}.get(a["severity"], "⚪")
                    print(f"\n   {sev_icon} [{a['severity'].upper()}] {a['source']}")
                    print(f"      Alvo: {a['target']}")
                    print(f"      Data: {a['date_found']}")
                    print(f"      {a['description']}")
            else:
                print("\n\033[92m✅ Nenhum alerta\033[0m")
        
        elif escolha == '6':
            # Importar arquivo .db
            print("\n\033[96m=== Importar Arquivo .db/.sqlite ===\033[0m")
            file_path = input("Caminho do arquivo: ").strip()
            
            if not file_path or not os.path.exists(file_path):
                print("\033[91m❌ Arquivo não encontrado\033[0m")
                input("\nPressione Enter...")
                continue
            
            # Verificar se já foi importado
            if organizer.was_file_imported(file_path):
                print(f"\n\033[93m⚠️ Este arquivo já foi importado anteriormente!\033[0m")
                confirm = input("Deseja reimportar? (s/N): ").strip().lower()
                if confirm != 's':
                    continue
            
            print(f"\n\033[96mLendo arquivo...\033[0m")
            result = db_reader.read_db_file(file_path)
            
            if result['errors']:
                print(f"\033[91m❌ Erros: {result['errors']}\033[0m")
            else:
                print(f"\n\033[92m✅ Arquivo lido com sucesso!\033[0m")
                print(f"   📊 Tabelas encontradas: {len(result['tables'])}")
                print(f"   📝 Total de registros: {result['total_records']}")
                print(f"   🔑 Credenciais encontradas: {len(result['credentials'])}")
                
                for table in result['tables']:
                    if table['has_credentials']:
                        print(f"\n   📋 Tabela: {table['name']}")
                        print(f"      Registros: {table['row_count']}")
                        print(f"      Colunas de credenciais: {list(table['credential_columns'].keys())}")
                
                if result['credentials']:
                    print(f"\n\033[96mOrganizando e deduplicando...\033[0m")
                    org_result = organizer.organize_credentials(
                        result['credentials'], 
                        source=Path(file_path).stem
                    )
                    
                    print(f"\n\033[92m✅ Organização concluída!\033[0m")
                    print(f"   Processados: {org_result['processed']}")
                    print(f"   Únicos: \033[92m{org_result['unique']}\033[0m")
                    print(f"   Duplicados: \033[93m{org_result['duplicates']}\033[0m")
                    
                    # Registrar import
                    organizer.record_import(
                        file_path, 
                        org_result['processed'],
                        org_result['unique'],
                        org_result['duplicates']
                    )
        
        elif escolha == '7':
            # Escanear pasta
            print("\n\033[96m=== Escanear Pasta ===\033[0m")
            dir_path = input("Caminho da pasta: ").strip()
            
            if not dir_path or not os.path.isdir(dir_path):
                print("\033[91m❌ Pasta não encontrada\033[0m")
                input("\nPressione Enter...")
                continue
            
            recursive = input("Buscar em subpastas? (S/n): ").strip().lower() != 'n'
            
            print(f"\n\033[96mEscaneando pasta...\033[0m")
            results = db_reader.scan_directory(dir_path, recursive)
            
            total_creds = 0
            for result in results:
                total_creds += len(result.get('credentials', []))
            
            print(f"\n\033[92m✅ Scan concluído!\033[0m")
            print(f"   Arquivos processados: {len(results)}")
            print(f"   Credenciais encontradas: {total_creds}")
            
            if total_creds > 0:
                confirm = input("\nOrganizar e importar todas? (S/n): ").strip().lower()
                if confirm != 'n':
                    for result in results:
                        if result['credentials']:
                            org_result = organizer.organize_credentials(
                                result['credentials'],
                                source=Path(result['file']).stem
                            )
                            organizer.record_import(
                                result['file'],
                                org_result['processed'],
                                org_result['unique'],
                                org_result['duplicates']
                            )
                    
                    stats = organizer.get_stats()
                    print(f"\n\033[92m✅ Importação concluída!\033[0m")
                    print(f"   Total processado: {stats['total_processed']}")
                    print(f"   Únicos adicionados: \033[92m{stats['unique_added']}\033[0m")
                    print(f"   Duplicados ignorados: \033[93m{stats['duplicates_skipped']}\033[0m")
        
        elif escolha == '8':
            # Histórico de imports
            print("\n\033[96m=== Histórico de Imports ===\033[0m")
            history = organizer.get_import_history()
            
            if history:
                print(f"\n📜 Últimos {len(history)} imports:")
                for h in history:
                    print(f"\n   📁 {h['filename']}")
                    print(f"      Data: {h['date'][:19]}")
                    print(f"      Registros: {h['records']} | Únicos: \033[92m{h['unique']}\033[0m | Dup: \033[93m{h['duplicates']}\033[0m")
            else:
                print("\n📭 Nenhum import realizado ainda")
        
        elif escolha == '9':
            # Buscar email
            print("\n\033[92m=== Buscar Email no Índice ===\033[0m")
            email = input("Email: ").strip()
            
            if not email:
                continue
            
            result = organizer.search_email(email)
            
            if result:
                print(f"\n\033[91m🔴 Email encontrado no banco!\033[0m")
                print(f"   📧 Email: {result['email']}")
                print(f"   🌐 Domínio: {result['domain']}")
                print(f"   📅 Primeira vez visto: {result['first_seen'][:10]}")
                print(f"   🔢 Apareceu em: {result['breach_count']} vazamento(s)")
                print(f"   📂 Fontes: {', '.join(result['sources'][:5])}")
            else:
                print(f"\n\033[92m✅ Email não encontrado no banco local\033[0m")
        
        elif escolha == '10':
            # Buscar por domínio
            print("\n\033[92m=== Buscar por Domínio ===\033[0m")
            domain = input("Domínio (ex: gmail.com): ").strip()
            
            if not domain:
                continue
            
            emails = organizer.search_by_domain(domain)
            
            if emails:
                print(f"\n\033[91m🔴 {len(emails)} email(s) encontrado(s) para {domain}:\033[0m")
                for email in emails[:20]:
                    print(f"   • {email}")
                if len(emails) > 20:
                    print(f"\n   ... e mais {len(emails) - 20} emails")
            else:
                print(f"\n\033[92m✅ Nenhum email encontrado para {domain}\033[0m")
        
        elif escolha == '11':
            # Estatísticas
            print("\n\033[92m=== Estatísticas do Banco ===\033[0m")
            stats = organizer.get_stats()
            db_stats = db_reader.get_stats()
            
            print(f"\n   📊 \033[1mResumo Geral:\033[0m")
            print(f"   ─────────────────────────────")
            print(f"   📁 Arquivos processados: {db_stats['files_processed']}")
            print(f"   📋 Tabelas analisadas: {db_stats['tables_found']}")
            print(f"   📝 Credenciais extraídas: {db_stats['credentials_found']}")
            print(f"\n   🗃️ \033[1mBanco Organizado:\033[0m")
            print(f"   ─────────────────────────────")
            print(f"   ✅ Total processado: {stats['total_processed']}")
            print(f"   ➕ Únicos adicionados: \033[92m{stats['unique_added']}\033[0m")
            print(f"   🔄 Duplicados ignorados: \033[93m{stats['duplicates_skipped']}\033[0m")
            print(f"   📧 Emails: {stats['emails']}")
            print(f"   🔑 Senhas: {stats['passwords']}")
            print(f"   🔗 Combos: {stats['combos']}")
        
        elif escolha == '12':
            # Listar sites de vazamento
            print("\n\033[94m=== Sites de Vazamento ===\033[0m")
            
            print(f"\n   \033[1;91m🧅 Sites .onion (Tor):\033[0m")
            for site in LEAK_SITES['onion_sites']:
                status = "\033[92m●\033[0m" if site['active'] else "\033[91m●\033[0m"
                print(f"   {status} {site['name']}")
                if site['onion_url']:
                    print(f"      \033[90m{site['onion_url']}\033[0m")
                print(f"      {site['description']}")
            
            print(f"\n   \033[1;96m🌐 APIs Públicas:\033[0m")
            for api in LEAK_SITES['public_apis']:
                key_req = "\033[93m[KEY]\033[0m" if api['requires_key'] else "\033[92m[FREE]\033[0m"
                print(f"   {key_req} {api['name']}")
                print(f"      {api['url']}")
            
            print(f"\n   \033[1;95m📋 Sites de Paste:\033[0m")
            for paste in LEAK_SITES['paste_sites']:
                print(f"   • {paste['name']} - {paste['url']}")
            
            print(f"\n   \033[1;91m💀 Grupos Ransomware (Monitorar):\033[0m")
            active_groups = [g['name'] for g in LEAK_SITES['ransomware_groups'] if g['active']]
            print(f"   {', '.join(active_groups)}")
        
        elif escolha == '13':
            print("\n\033[94m=== Verificar Conexão Tor ===\033[0m")
            
            if Spinner:
                spinner = Spinner("Verificando conexão Tor", "dots")
                spinner.start()
            
            is_tor = monitor.check_tor_connection()
            
            if Spinner:
                spinner.stop()
            
            if is_tor:
                print("\n\033[92m✅ Conectado à rede Tor!\033[0m")
                print("   Você pode acessar serviços .onion")
            else:
                print("\n\033[91m❌ Não conectado à rede Tor\033[0m")
                auto_start = input("\nDeseja iniciar o Tor automaticamente? (S/n): ").strip().lower()
                if auto_start != 'n':
                    monitor.start_tor()
                else:
                    print("   \033[93mPara conectar manualmente:\033[0m")
                print("   1. Instale Tor: sudo apt install tor")
                print("   2. Inicie: sudo service tor start")
                print("   3. Ou use Tor Browser")
        
        elif escolha == '14':
            print("\n\033[94m=== Breaches Conhecidos (HIBP) ===\033[0m")
            domain = input("Filtrar por domínio (Enter para todos): ").strip()
            
            if Spinner:
                spinner = Spinner("Carregando breaches", "dots")
                spinner.start()
            
            breaches = monitor.hibp.get_breaches(domain if domain else None)
            
            if Spinner:
                spinner.stop()
            
            if breaches:
                print(f"\n📊 {len(breaches)} breach(es) encontrado(s):")
                for b in breaches[:20]:
                    count = b.get("PwnCount", 0)
                    print(f"\n   • \033[1m{b.get('Title', 'Unknown')}\033[0m")
                    print(f"     Data: {b.get('BreachDate', 'Unknown')}")
                    print(f"     Registros: \033[91m{count:,}\033[0m")
                    
                if len(breaches) > 20:
                    print(f"\n   ... e mais {len(breaches) - 20} breaches")
            else:
                print("\n\033[91m❌ Não foi possível carregar breaches\033[0m")
        
        elif escolha == '15':
            # Testar status dos sites
            print("\n\033[94m=== Testar Status dos Sites ===\033[0m")
            print("\nOpções:")
            print("  [1] Testar apenas APIs e sites clearnet")
            print("  [2] Testar tudo (inclui .onion via Tor)")
            print("  [3] Testar URL específica")
            
            sub_op = input("\nOpção: ").strip()
            
            if sub_op == '1':
                print("\n\033[96mTestando sites clearnet...\033[0m\n")
                results = site_checker.check_all_sites(include_onion=False)
                
                print(f"\n\033[1m━━━ RESUMO ━━━\033[0m")
                print(f"   Total testado: {results['summary']['total']}")
                print(f"   \033[92mOnline: {results['summary']['online']}\033[0m")
                print(f"   \033[91mOffline: {results['summary']['offline']}\033[0m")
                print(f"   \033[93mErros: {results['summary']['errors']}\033[0m")
                
                save = input("\nSalvar resultados? (s/N): ").strip().lower()
                if save == 's':
                    site_checker.export_results(results)
            
            elif sub_op == '2':
                print("\n\033[96mTestando todos os sites (inclui Tor)...\033[0m\n")
                results = site_checker.check_all_sites(include_onion=True)
                
                print(f"\n\033[1m━━━ RESUMO ━━━\033[0m")
                print(f"   Total testado: {results['summary']['total']}")
                print(f"   \033[92mOnline: {results['summary']['online']}\033[0m")
                print(f"   \033[91mOffline: {results['summary']['offline']}\033[0m")
                print(f"   \033[93mErros: {results['summary']['errors']}\033[0m")
                
                save = input("\nSalvar resultados? (s/N): ").strip().lower()
                if save == 's':
                    site_checker.export_results(results)
            
            elif sub_op == '3':
                url = input("URL para testar: ").strip()
                if url:
                    use_tor = '.onion' in url
                    if use_tor:
                        print("\n\033[93m⚠️ URL .onion detectada, usando Tor...\033[0m")
                    
                    print(f"\nTestando {url}...")
                    result = site_checker.check_url(url, use_tor=use_tor)
                    
                    status_color = "\033[92m" if result['status'] == 'online' else "\033[91m"
                    print(f"\n   Status: {status_color}{result['status']}\033[0m")
                    if result['status_code']:
                        print(f"   Código: {result['status_code']}")
                    if result['response_time']:
                        print(f"   Tempo: {result['response_time']}s")
                    if result['error']:
                        print(f"   Erro: {result['error']}")
        
        elif escolha == '16':
            # Buscar URLs atualizadas
            print("\n\033[94m=== Buscar URLs Atualizadas ===\033[0m")
            print("\nSites disponíveis para busca:")
            
            sites = LEAK_SITES.get('onion_sites', [])
            for i, site in enumerate(sites, 1):
                status = "\033[92m●\033[0m" if site.get('active') else "\033[91m●\033[0m"
                print(f"   {status} [{i}] {site['name']}")
            
            print(f"\n   [0] Buscar todos")
            
            site_op = input("\nEscolha o site: ").strip()
            
            if site_op == '0':
                # Buscar todos
                print("\n\033[96mBuscando URLs atualizadas para todos os sites...\033[0m")
                for site in sites:
                    urls = site_checker.search_new_urls(site['name'])
                    if urls:
                        print(f"\n   \033[92m✓ {site['name']}:\033[0m")
                        for url in urls[:3]:
                            print(f"      • {url}")
                    else:
                        print(f"\n   \033[93m- {site['name']}: Nenhuma URL encontrada\033[0m")
            
            else:
                try:
                    idx = int(site_op) - 1
                    if 0 <= idx < len(sites):
                        site = sites[idx]
                        print(f"\n\033[96mBuscando URLs para {site['name']}...\033[0m")
                        urls = site_checker.search_new_urls(site['name'])
                        
                        if urls:
                            print(f"\n   \033[92m✓ URLs encontradas:\033[0m")
                            for url in urls:
                                print(f"      • {url}")
                        else:
                            print(f"\n   \033[93mNenhuma URL encontrada\033[0m")
                            print("   Tente buscar manualmente em:")
                            print("   • https://ahmia.fi")
                            print("   • https://darksearch.io")
                except:
                    pass
        
        elif escolha == '17':
            print("\n\033[95m=== Exportar Dados ===\033[0m")
            filename = input("Nome do arquivo (default: darkweb_export.json): ").strip()
            filename = filename or "darkweb_export.json"
            
            monitor.export_data(filename)
            print(f"\n\033[92m✅ Dados exportados para {filename}\033[0m")
        
        elif escolha == '18':
            # Baixar lista de breaches do HIBP
            print("\n\033[91m=== Baixar Lista de Breaches (HIBP) ===\033[0m")
            print("Isso irá baixar a lista completa de todos os breaches conhecidos.\n")
            
            breaches = downloader.download_hibp_breaches()
            
            if breaches:
                print(f"\n\033[1m📊 Resumo dos Breaches:\033[0m")
                
                # Calcular estatísticas
                total_records = sum(b.get('PwnCount', 0) for b in breaches)
                verified = len([b for b in breaches if b.get('IsVerified')])
                
                print(f"   Total de breaches: {len(breaches)}")
                print(f"   Registros vazados: \033[91m{total_records:,}\033[0m")
                print(f"   Verificados: {verified}")
                
                # Top 10 maiores
                print(f"\n\033[1m🔝 Top 10 maiores vazamentos:\033[0m")
                sorted_breaches = sorted(breaches, key=lambda x: x.get('PwnCount', 0), reverse=True)
                for b in sorted_breaches[:10]:
                    print(f"   • {b.get('Title', 'Unknown')}: \033[91m{b.get('PwnCount', 0):,}\033[0m")
        
        elif escolha == '19':
            # Buscar email em múltiplas APIs
            print("\n\033[91m=== Buscar Email em Múltiplas APIs ===\033[0m")
            email = input("Email para buscar: ").strip()
            
            if email:
                print(f"\n\033[96mBuscando vazamentos para: {email}\033[0m\n")
                results = downloader.check_email_leaks(email)
                
                print(f"\n\033[1m📊 Resultados:\033[0m")
                
                for source, data in results.get('sources', {}).items():
                    if data:
                        if isinstance(data, list):
                            print(f"\n   \033[91m🔴 {source.upper()}: {len(data)} vazamentos\033[0m")
                            for item in data[:5]:
                                if isinstance(item, dict):
                                    print(f"      • {item.get('Name', item.get('name', str(item)[:50]))}")
                        elif isinstance(data, dict):
                            if data.get('found') or data.get('success'):
                                print(f"\n   \033[91m🔴 {source.upper()}: Encontrado\033[0m")
                            else:
                                print(f"\n   \033[92m✓ {source.upper()}: Não encontrado\033[0m")
                    else:
                        print(f"\n   \033[92m✓ {source.upper()}: Não encontrado\033[0m")
                
                print(f"\n   Resultados salvos em: data/downloads/api_results/")
        
        elif escolha == '20':
            # Baixar paste
            print("\n\033[91m=== Baixar Paste ===\033[0m")
            print("Sites suportados: Pastebin, Rentry, outros\n")
            
            url = input("URL do paste: ").strip()
            
            if url:
                content = downloader.download_paste(url)
                
                if content:
                    # Mostrar preview
                    print(f"\n\033[1m📋 Preview (primeiros 500 chars):\033[0m")
                    print("-" * 50)
                    print(content[:500])
                    if len(content) > 500:
                        print(f"\n... ({len(content) - 500} chars restantes)")
                    print("-" * 50)
                    
                    # Perguntar se quer processar
                    if '@' in content or 'password' in content.lower():
                        process = input("\n\033[93mParece conter credenciais. Processar e organizar? (s/N): \033[0m").strip().lower()
                        if process == 's':
                            # Tentar extrair credenciais
                            lines = content.split('\n')
                            creds = []
                            for line in lines:
                                if ':' in line:
                                    parts = line.strip().split(':')
                                    if len(parts) >= 2 and '@' in parts[0]:
                                        creds.append({
                                            'email': parts[0],
                                            'password': ':'.join(parts[1:])
                                        })
                            
                            if creds:
                                result = organizer.organize_credentials(creds, source='paste')
                                print(f"\n\033[92m✓ {result['unique']} credenciais extraídas e organizadas\033[0m")
        
        elif escolha == '21':
            # Buscar no IntelX
            print("\n\033[91m=== Buscar no IntelX ===\033[0m")
            
            if not downloader.api_keys.get('intelx'):
                print("\033[93m⚠️ API key do IntelX não configurada.\033[0m")
                print("Use a opção [23] para configurar.")
                input("\nPressione Enter...")
                continue
            
            query = input("Buscar (email, domínio, etc): ").strip()
            
            if query:
                results = downloader.search_intelx(query)
                
                if results:
                    print(f"\n\033[1m📊 {len(results)} resultados encontrados:\033[0m")
                    for r in results[:10]:
                        print(f"\n   • {r.get('name', 'Unknown')}")
                        print(f"     Tipo: {r.get('type', 'N/A')}")
                        print(f"     Data: {r.get('date', 'N/A')}")
                else:
                    print("\n\033[93mNenhum resultado encontrado\033[0m")
        
        elif escolha == '22':
            # Baixar de URL
            print("\n\033[91m=== Baixar de URL ===\033[0m")
            print("Suporta HTTP, HTTPS e .onion (via Tor)\n")
            
            url = input("URL: ").strip()
            filename = input("Nome do arquivo (Enter para auto): ").strip() or None
            
            if url:
                result = downloader.download_from_url(url, filename)
                
                if result:
                    # Verificar se é um DB
                    if result.endswith('.db') or result.endswith('.sqlite'):
                        process = input("\n\033[93mArquivo .db detectado. Importar? (s/N): \033[0m").strip().lower()
                        if process == 's':
                            db_result = db_reader.read_db_file(result)
                            if db_result['credentials']:
                                org_result = organizer.organize_credentials(
                                    db_result['credentials'],
                                    source=Path(result).stem
                                )
                                print(f"\n\033[92m✓ {org_result['unique']} credenciais importadas\033[0m")
        
        elif escolha == '23':
            # Configurar API Keys
            print("\n\033[91m=== Configurar API Keys ===\033[0m")
            print("\nAPIs disponíveis:")
            print("  [1] HIBP (Have I Been Pwned)")
            print("  [2] IntelX (Intelligence X)")
            print("  [3] DeHashed")
            print("  [4] LeakCheck")
            print("  [5] Snusbase")
            
            print(f"\n\033[96mChaves configuradas:\033[0m")
            for key, value in downloader.api_keys.items():
                masked = value[:8] + "..." if len(value) > 8 else value
                print(f"   • {key}: {masked}")
            
            api_op = input("\nQual API configurar? ").strip()
            
            api_map = {
                '1': 'hibp',
                '2': 'intelx',
                '3': 'dehashed',
                '4': 'leakcheck',
                '5': 'snusbase'
            }
            
            if api_op in api_map:
                api_name = api_map[api_op]
                key = input(f"API Key para {api_name}: ").strip()
                if key:
                    downloader.save_api_key(api_name, key)
                    print(f"\n\033[92m✓ API key salva para {api_name}\033[0m")
        
        # ============================================
        # NOVAS OPÇÕES - SCRAPING SEM API
        # ============================================
        
        elif escolha == '24':
            # Ver sites disponíveis para scraping
            print("\n\033[91m=== Sites Disponíveis para Scraping ===\033[0m")
            print("\033[93m⚠️ Estes sites podem requerer Tor ou estar temporariamente offline\033[0m\n")
            
            sites = scraper.get_available_sites()
            
            for i, site in enumerate(sites, 1):
                status = "\033[92m●\033[0m" if site.get('type') == 'forum' else "\033[94m●\033[0m"
                tor_icon = " 🧅" if site.get('requires_tor') else ""
                
                print(f"   {status} [{i}] \033[1m{site['name']}\033[0m{tor_icon}")
                print(f"       URLs: {', '.join(site.get('urls', []))}")
                if site.get('onion'):
                    print(f"       Onion: {site['onion'][:30]}...")
                print(f"       Tipo: {site['type']}")
                print(f"       {site['description']}")
                print()
            
            print("\n\033[96mDica:\033[0m Use a opção [25] para fazer scraping de um site")
            print("       Os dados serão salvos na pasta Dump/")
        
        elif escolha == '25':
            # Fazer scraping de site
            print("\n\033[91m=== Fazer Scraping de Site ===\033[0m")
            print("\033[96mOs dados serão salvos em: Dump/<nome_do_site>/\033[0m\n")
            
            sites = scraper.get_available_sites()
            
            for i, site in enumerate(sites, 1):
                tor_icon = " 🧅" if site.get('requires_tor') else ""
                print(f"   [{i}] {site['name']}{tor_icon}")
            
            print("\n   [0] Cancelar")
            
            site_op = input("\n\033[92mEscolha o site: \033[0m").strip()
            
            if site_op == '0' or not site_op:
                continue
            
            try:
                idx = int(site_op) - 1
                if 0 <= idx < len(sites):
                    site = sites[idx]
                    
                    print(f"\n\033[1mSite selecionado: {site['name']}\033[0m")
                    
                    search_term = input("Termo de busca (Enter para todos): ").strip() or None
                    use_tor = input("Usar Tor? (s/N): ").strip().lower() == 's'
                    
                    if use_tor:
                        print("\n\033[93m⚠️ Verificando conexão Tor...\033[0m")
                        if not monitor.check_tor_connection():
                            print("\033[91m❌ Tor não está conectado.\033[0m")
                            auto_start = input("\nDeseja iniciar o Tor automaticamente? (S/n): ").strip().lower()
                            if auto_start != 'n':
                                if not monitor.start_tor():
                                    print("\033[91m❌ Não foi possível iniciar o Tor.\033[0m")
                                    input("\nPressione Enter...")
                                    continue
                            else:
                                input("\nPressione Enter...")
                                continue
                        else:
                            print("\033[92m✓ Tor conectado\033[0m")
                    
                    result = scraper.scrape_site(
                        site['id'],
                        search_term=search_term,
                        max_pages=5,
                        use_tor=use_tor
                    )
                    
                    if result.get('leaks_found'):
                        print(f"\n\033[1m📊 Resultados:\033[0m")
                        print(f"   Páginas scaneadas: {result['pages_scraped']}")
                        print(f"   Leaks encontrados: \033[92m{len(result['leaks_found'])}\033[0m")
                        
                        print(f"\n\033[1mPrimeiros 10 leaks:\033[0m")
                        for leak in result['leaks_found'][:10]:
                            print(f"\n   📁 {leak['title'][:60]}")
                            print(f"      URL: {leak['url'][:50]}...")
                        
                        # Perguntar se quer baixar
                        print("\n\033[93mDeseja baixar algum leak?\033[0m")
                        print("   Digite o número do leak (1-10) ou 0 para pular")
                        
                        dl_op = input("\nBaixar: ").strip()
                        if dl_op and dl_op != '0':
                            try:
                                dl_idx = int(dl_op) - 1
                                if 0 <= dl_idx < len(result['leaks_found']):
                                    leak = result['leaks_found'][dl_idx]
                                    print(f"\n\033[96mBaixando: {leak['title'][:50]}...\033[0m")
                                    scraper.download_leak(leak['url'], site['id'], use_tor=use_tor)
                            except:
                                pass
                    
                    if result.get('errors'):
                        print(f"\n\033[93m⚠️ Erros: {len(result['errors'])}\033[0m")
                        for err in result['errors'][:3]:
                            print(f"   • {err}")
            except Exception as e:
                print(f"\033[91m❌ Erro: {e}\033[0m")
        
        elif escolha == '26':
            # Baixar leak de URL direta
            print("\n\033[91m=== Baixar Leak de URL ===\033[0m")
            print("\033[96mBaixa direto para: Dump/<site_id>/\033[0m\n")
            
            url = input("URL do arquivo/página: ").strip()
            
            if not url:
                continue
            
            # Detectar site
            site_id = 'temp'
            for site in scraper.get_available_sites():
                for site_url in site.get('urls', []):
                    if site_url.replace('https://', '').replace('http://', '') in url:
                        site_id = site['id']
                        break
            
            use_tor = '.onion' in url or input("Usar Tor? (s/N): ").strip().lower() == 's'
            
            if use_tor:
                print("\n\033[93m⚠️ Verificando conexão Tor...\033[0m")
                if not monitor.check_tor_connection():
                    print("\033[91m❌ Tor não está conectado.\033[0m")
                    auto_start = input("\nDeseja iniciar o Tor automaticamente? (S/n): ").strip().lower()
                    if auto_start != 'n':
                        if not monitor.start_tor():
                            print("\033[91m❌ Não foi possível iniciar o Tor.\033[0m")
                            input("\nPressione Enter...")
                            continue
                    else:
                        input("\nPressione Enter...")
                        continue
                else:
                    print("\033[92m✓ Tor conectado\033[0m")
            
            result = scraper.download_leak(url, site_id, use_tor=use_tor)
            
            if result:
                # Perguntar se quer parsear
                process = input("\n\033[93mDeseja parsear o arquivo baixado? (s/N): \033[0m").strip().lower()
                if process == 's':
                    parse_result = scraper.parse_downloaded_file(result)
                    
                    if parse_result['credentials']:
                        # Organizar no banco principal
                        org_op = input("\n\033[93mOrganizar credenciais no banco principal? (s/N): \033[0m").strip().lower()
                        if org_op == 's':
                            org_result = organizer.organize_credentials(
                                parse_result['credentials'],
                                source=Path(result).stem
                            )
                            print(f"\n\033[92m✓ {org_result['unique']} credenciais organizadas\033[0m")
        
        elif escolha == '27':
            # Parsear arquivo baixado
            print("\n\033[91m=== Parsear Arquivo Baixado ===\033[0m")
            print("Suporta: .txt, .csv, .json, .sql, .db\n")
            
            filepath = input("Caminho do arquivo: ").strip()
            
            if not filepath or not os.path.exists(filepath):
                print("\033[91m❌ Arquivo não encontrado\033[0m")
                input("\nPressione Enter...")
                continue
            
            result = scraper.parse_downloaded_file(filepath)
            
            print(f"\n\033[1m📊 Resultado do parsing:\033[0m")
            print(f"   Arquivo: {result['file']}")
            print(f"   Tipo: {result['type']}")
            print(f"   Tamanho: {result['size']:,} bytes")
            print(f"   Credenciais: \033[92m{len(result['credentials'])}\033[0m")
            print(f"   Emails: \033[92m{len(result['emails'])}\033[0m")
            
            if result['errors']:
                print(f"\n\033[93m⚠️ Erros:\033[0m")
                for err in result['errors']:
                    print(f"   • {err}")
            
            if result['credentials']:
                # Organizar
                org_op = input("\n\033[93mOrganizar credenciais no banco principal? (s/N): \033[0m").strip().lower()
                if org_op == 's':
                    org_result = organizer.organize_credentials(
                        result['credentials'],
                        source=Path(filepath).stem
                    )
                    print(f"\n\033[92m✓ {org_result['unique']} credenciais organizadas\033[0m")
                    print(f"   Duplicados ignorados: {org_result['duplicates']}")
        
        elif escolha == '28':
            # Listar arquivos baixados
            print("\n\033[91m=== Arquivos Baixados ===\033[0m")
            
            files = scraper.list_downloaded_files()
            
            if files:
                print(f"\n📁 Últimos {len(files)} arquivos:\n")
                
                for i, f in enumerate(files, 1):
                    parsed_icon = "\033[92m✓\033[0m" if f['parsed'] else "\033[93m○\033[0m"
                    size_mb = f['size'] / (1024 * 1024)
                    
                    print(f"   {parsed_icon} [{i}] {Path(f['filename']).name[:40]}")
                    print(f"       Fonte: {f['source']}")
                    print(f"       Data: {f['date'][:10]}")
                    print(f"       Tamanho: {size_mb:.2f} MB")
                    print()
                
                # Estatísticas
                stats = scraper.get_stats()
                total_size = stats['bytes_downloaded'] / (1024 * 1024)
                
                print(f"\n\033[1m📊 Estatísticas:\033[0m")
                print(f"   Arquivos baixados: {stats['files_downloaded']}")
                print(f"   Total baixado: {total_size:.2f} MB")
                print(f"   Sites scaneados: {stats['sites_scraped']}")
                print(f"   Erros: {stats['errors']}")
            else:
                print("\n📭 Nenhum arquivo baixado ainda")
                print("   Use as opções [25] ou [26] para baixar dados")
        
        elif escolha == '29':
            # Scanner automático de fontes
            print("\n\033[97m=== Scanner Automático de Fontes ===\033[0m")
            print("\n   Este scanner verifica o status de 60+ fontes de vazamentos")
            print("   incluindo agregadores, pastes, repositórios, fóruns e mais.\n")
            
            scanner = LeakSourceScanner(dump_dir="Dump")
            
            print("   Categorias disponíveis:")
            for i, cat in enumerate(scanner.ALL_SOURCES.keys(), 1):
                count = len(scanner.ALL_SOURCES[cat])
                print(f"      [{i}] {cat.capitalize()} ({count} fontes)")
            print(f"      [0] Todas as categorias")
            
            cat_input = input("\n   Escolha (0-8): ").strip()
            
            use_tor_input = input("   Usar Tor para fóruns/onion? (s/N): ").strip().lower()
            use_tor = use_tor_input == 's'
            
            categories = None
            if cat_input != '0' and cat_input.isdigit():
                cat_list = list(scanner.ALL_SOURCES.keys())
                idx = int(cat_input) - 1
                if 0 <= idx < len(cat_list):
                    categories = [cat_list[idx]]
            
            results = scanner.scan_all_sources(categories=categories, use_tor=use_tor)
            
            print(f"\n\033[1m📊 Resumo do Scan:\033[0m")
            print(f"   ✓ Online: \033[92m{results['summary']['online']}\033[0m")
            print(f"   ✗ Offline: \033[91m{results['summary']['offline']}\033[0m")
            print(f"   Total: {results['summary']['total']}")
        
        elif escolha == '30':
            # Descobrir novas fontes
            print("\n\033[97m=== Descobrir Novas Fontes ===\033[0m")
            print("\n   Busca automaticamente por novas fontes de vazamentos em:")
            print("      • Ahmia (sites .onion)")
            print("      • GitHub (repositórios)")
            print("      • Ransomwatch (grupos ransomware)")
            print("      • Pastebin (links em pastes)\n")
            
            scanner = LeakSourceScanner(dump_dir="Dump")
            
            use_tor_input = input("   Usar Tor? (s/N): ").strip().lower()
            use_tor = use_tor_input == 's'
            
            discovered = scanner.discover_new_sources(use_tor=use_tor)
            
            if discovered:
                print(f"\n\033[1m📋 Fontes Descobertas:\033[0m\n")
                by_source = {}
                for d in discovered:
                    src = d.get('source', 'unknown')
                    if src not in by_source:
                        by_source[src] = []
                    by_source[src].append(d)
                
                for src, items in by_source.items():
                    print(f"   \033[93m{src.upper()} ({len(items)})\033[0m")
                    for item in items[:5]:
                        url = item['url'][:60] + '...' if len(item['url']) > 60 else item['url']
                        print(f"      • {url}")
                    if len(items) > 5:
                        print(f"      ... e mais {len(items)-5}")
                    print()
            else:
                print("\n   Nenhuma nova fonte descoberta")
        
        elif escolha == '31':
            # Ver fontes funcionais
            print("\n\033[97m=== Fontes Funcionais ===\033[0m")
            
            scanner = LeakSourceScanner(dump_dir="Dump")
            working = scanner.get_working_sources()
            
            if working:
                print(f"\n   \033[92m{len(working)} fontes online:\033[0m\n")
                
                by_cat = {}
                for w in working:
                    cat = w.get('category', 'unknown')
                    if cat not in by_cat:
                        by_cat[cat] = []
                    by_cat[cat].append(w)
                
                for cat, sources in by_cat.items():
                    print(f"   \033[93m━━━ {cat.upper()} ━━━\033[0m")
                    for s in sources:
                        print(f"      ✓ {s['name']:25} {s['url']}")
                    print()
            else:
                print("\n   Nenhuma fonte verificada ainda.")
                print("   Use [29] para escanear as fontes primeiro.")
        
        input("\n\033[90mPressione Enter para continuar...\033[0m")


if __name__ == "__main__":
    interactive_menu()
