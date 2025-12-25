#!/usr/bin/env python3
"""
darkweb_access.py

Sistema avançado para acessar vazamentos da Dark Web.
Inclui Tor, Telegram, Paste Sites e Fóruns de Breach.
Integrado com TorManager para gerenciamento completo.

⚠️ AVISO LEGAL: Use apenas para pesquisa de segurança legítima.
O acesso não autorizado a dados é crime em muitos países.
"""
import os
import sys
import json
import hashlib
import requests
import time
import re
import sqlite3
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from urllib.parse import quote, urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Adicionar diretório pai ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Tentar importar TorManager
try:
    from tools.tor.tor_manager import TorManager, get_tor_manager
    TOR_MANAGER_AVAILABLE = True
except ImportError:
    TOR_MANAGER_AVAILABLE = False

# Tentar importar bibliotecas opcionais
try:
    import socks
    SOCKS_AVAILABLE = True
except ImportError:
    SOCKS_AVAILABLE = False

try:
    from stem import Signal
    from stem.control import Controller
    STEM_AVAILABLE = True
except ImportError:
    STEM_AVAILABLE = False


class TorConnection:
    """
    Gerenciador de conexão Tor para acesso à dark web.
    Integrado com TorManager quando disponível.
    """
    
    def __init__(self, 
                 socks_port: int = 9050,
                 control_port: int = 9051,
                 control_password: str = ""):
        self.socks_port = socks_port
        self.control_port = control_port
        self.control_password = control_password
        self.session = None
        self.is_connected = False
        
        # Usar TorManager se disponível
        if TOR_MANAGER_AVAILABLE:
            self.tor_manager = get_tor_manager()
            self.socks_port = self.tor_manager.config.get("socks_port", 9050)
            self.control_port = self.tor_manager.config.get("control_port", 9051)
        else:
            self.tor_manager = None
    
    def create_session(self) -> requests.Session:
        """Cria sessão HTTP que roteia pelo Tor."""
        if self.tor_manager:
            return self.tor_manager.get_session()
        
        session = requests.Session()
        session.proxies = {
            'http': f'socks5h://127.0.0.1:{self.socks_port}',
            'https': f'socks5h://127.0.0.1:{self.socks_port}'
        }
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.session = session
        return session
    
    def check_tor_connection(self) -> Dict:
        """Verifica se Tor está funcionando."""
        if self.tor_manager:
            return self.tor_manager.check_connection()
        
        try:
            session = self.create_session()
            # Verificar IP via Tor
            resp = session.get('https://check.torproject.org/api/ip', timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                self.is_connected = data.get('IsTor', False)
                return {
                    "connected": self.is_connected,
                    "ip": data.get('IP', 'Unknown'),
                    "is_tor": data.get('IsTor', False),
                    "message": "✅ Conectado via Tor!" if self.is_connected else "❌ Não está usando Tor"
                }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "message": f"❌ Erro de conexão: {e}"
            }
        
        return {"connected": False, "message": "❌ Tor não disponível"}
    
    def renew_identity(self) -> bool:
        """Renova identidade Tor (novo IP)."""
        if not STEM_AVAILABLE:
            print("⚠️ stem não instalado. Execute: pip install stem")
            return False
        
        try:
            with Controller.from_port(port=self.control_port) as controller:
                controller.authenticate(password=self.control_password)
                controller.signal(Signal.NEWNYM)
                time.sleep(5)  # Aguardar novo circuito
                return True
        except Exception as e:
            print(f"❌ Erro ao renovar identidade: {e}")
            return False
    
    def get(self, url: str, timeout: int = 60) -> Optional[requests.Response]:
        """GET request via Tor."""
        if not self.session:
            self.create_session()
        
        try:
            return self.session.get(url, timeout=timeout)
        except Exception as e:
            print(f"❌ Erro Tor GET: {e}")
            return None


class DarkWebSearcher:
    """
    Buscador em fontes da Dark Web.
    """
    
    # Fontes conhecidas (alguns podem estar offline)
    ONION_SOURCES = {
        "ahmia": {
            "name": "Ahmia Search",
            "url": "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion",
            "clearnet": "https://ahmia.fi",
            "type": "search_engine",
            "description": "Motor de busca da dark web"
        },
        "torch": {
            "name": "Torch Search",
            "url": "http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5aygthi7d6rplyvk3noyd.onion",
            "type": "search_engine",
            "description": "Motor de busca antigo da dark web"
        },
        "haystak": {
            "name": "Haystak",
            "url": "http://haystak5njsmn2hqkewecpaxetahtwhsbsa64jom2k22z5afxhnpxfid.onion",
            "type": "search_engine",
            "description": "Motor de busca com 1.5B+ páginas indexadas"
        },
        "dark_search": {
            "name": "DarkSearch",
            "clearnet": "https://darksearch.io",
            "type": "search_engine",
            "description": "API de busca dark web (clearnet)"
        }
    }
    
    BREACH_FORUMS = {
        "breachforums": {
            "name": "BreachForums",
            "description": "Fórum principal de vazamentos (requer registro)",
            "status": "online"
        },
        "leakbase": {
            "name": "LeakBase",
            "description": "Base de dados de leaks",
            "status": "variável"
        },
        "cracked": {
            "name": "Cracked.io",
            "description": "Fórum de cracking e leaks",
            "status": "online"
        },
        "nulled": {
            "name": "Nulled.to",
            "description": "Fórum de leaks e tools",
            "status": "online"
        }
    }
    
    def __init__(self, use_tor: bool = True):
        self.use_tor = use_tor
        self.tor = TorConnection() if use_tor else None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.rate_limit = 3.0
    
    def search_ahmia(self, query: str, use_clearnet: bool = True) -> List[Dict]:
        """
        Busca no Ahmia (clearnet ou onion).
        """
        results = []
        
        if use_clearnet:
            url = f"https://ahmia.fi/search/?q={quote(query)}"
            session = self.session
        else:
            if not self.tor:
                return [{"error": "Tor não configurado"}]
            url = f"{self.ONION_SOURCES['ahmia']['url']}/search/?q={quote(query)}"
            session = self.tor.create_session()
        
        try:
            time.sleep(self.rate_limit)
            resp = session.get(url, timeout=60)
            
            if resp.status_code == 200:
                # Parse simples dos resultados
                from html.parser import HTMLParser
                
                # Extrair links .onion
                onion_pattern = r'(http[s]?://[a-z2-7]{16,56}\.onion[^\s"<>]*)'
                onions = re.findall(onion_pattern, resp.text, re.IGNORECASE)
                
                for onion in set(onions)[:20]:
                    results.append({
                        "source": "Ahmia",
                        "url": onion,
                        "query": query
                    })
                
                return results
        except Exception as e:
            return [{"error": str(e), "source": "Ahmia"}]
        
        return results
    
    def search_darksearch_api(self, query: str, page: int = 1) -> Dict:
        """
        Busca via DarkSearch API (clearnet, gratuita).
        """
        url = f"https://darksearch.io/api/search?query={quote(query)}&page={page}"
        
        try:
            time.sleep(self.rate_limit)
            resp = self.session.get(url, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "source": "DarkSearch",
                    "total": data.get("total", 0),
                    "page": data.get("current_page", 1),
                    "results": data.get("data", [])[:20],
                    "success": True
                }
            elif resp.status_code == 429:
                return {"source": "DarkSearch", "error": "Rate limit - aguarde 1 minuto"}
        except Exception as e:
            return {"source": "DarkSearch", "error": str(e)}
        
        return {"source": "DarkSearch", "results": [], "success": False}
    
    def search_intelx_free(self, query: str) -> Dict:
        """
        IntelligenceX - Tier gratuito (limitado).
        """
        # Primeiro, obter API key gratuita
        url = "https://2.intelx.io/phonebook/search"
        
        try:
            time.sleep(self.rate_limit)
            
            # Iniciar busca
            data = {
                "term": query,
                "maxresults": 100,
                "media": 0,
                "target": 0,
                "timeout": 20
            }
            
            headers = {
                "x-key": "9df61df0-84f7-4dc7-b34c-8ccfb8646ace",  # Free tier key
                "Content-Type": "application/json"
            }
            
            resp = self.session.post(url, json=data, headers=headers, timeout=30)
            
            if resp.status_code == 200:
                result = resp.json()
                search_id = result.get("id")
                
                if search_id:
                    # Buscar resultados
                    time.sleep(3)
                    results_url = f"https://2.intelx.io/phonebook/search/result?id={search_id}&limit=100"
                    resp2 = self.session.get(results_url, headers=headers, timeout=30)
                    
                    if resp2.status_code == 200:
                        data = resp2.json()
                        selectors = data.get("selectors", [])
                        return {
                            "source": "IntelligenceX",
                            "found": len(selectors) > 0,
                            "count": len(selectors),
                            "results": selectors[:50],
                            "success": True
                        }
            
            return {"source": "IntelligenceX", "found": False, "success": False}
        except Exception as e:
            return {"source": "IntelligenceX", "error": str(e)}


class TelegramLeakMonitor:
    """
    Monitor de canais do Telegram que postam leaks.
    Usa a API pública do Telegram (t.me).
    """
    
    # Canais conhecidos de leaks (públicos)
    LEAK_CHANNELS = [
        {"name": "daborern", "url": "https://t.me/s/daborern", "type": "combolist"},
        {"name": "comaborern", "url": "https://t.me/s/comaborern", "type": "combolist"},
        {"name": "LeakBase", "url": "https://t.me/s/leakbase", "type": "database"},
        {"name": "Data Leaks", "url": "https://t.me/s/dataleaks", "type": "general"},
        {"name": "Dark Leaks", "url": "https://t.me/s/darkleaks", "type": "general"},
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        self.rate_limit = 2.0
    
    def scrape_channel(self, channel_url: str, keyword: str = None) -> List[Dict]:
        """
        Scrape mensagens públicas de um canal do Telegram.
        """
        results = []
        
        try:
            time.sleep(self.rate_limit)
            resp = self.session.get(channel_url, timeout=30)
            
            if resp.status_code == 200:
                # Extrair mensagens
                msg_pattern = r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>'
                messages = re.findall(msg_pattern, resp.text, re.DOTALL)
                
                # Extrair links de download
                link_pattern = r'href="([^"]+(?:mega\.nz|drive\.google|mediafire|anonfiles|gofile|pixeldrain)[^"]*)"'
                links = re.findall(link_pattern, resp.text, re.IGNORECASE)
                
                for i, msg in enumerate(messages[:30]):
                    # Limpar HTML
                    clean_msg = re.sub(r'<[^>]+>', '', msg).strip()
                    
                    if keyword:
                        if keyword.lower() not in clean_msg.lower():
                            continue
                    
                    result = {
                        "source": "Telegram",
                        "channel": channel_url,
                        "message": clean_msg[:500],
                        "has_download": any(l in msg for l in ['mega.nz', 'drive.google', 'mediafire'])
                    }
                    
                    # Extrair link de download da mensagem
                    msg_links = re.findall(link_pattern, msg, re.IGNORECASE)
                    if msg_links:
                        result["download_links"] = msg_links
                    
                    results.append(result)
                
                # Adicionar links encontrados
                for link in set(links)[:10]:
                    results.append({
                        "source": "Telegram",
                        "channel": channel_url,
                        "type": "download_link",
                        "url": link
                    })
        
        except Exception as e:
            results.append({"error": str(e), "channel": channel_url})
        
        return results
    
    def search_all_channels(self, keyword: str) -> List[Dict]:
        """Busca keyword em todos os canais conhecidos."""
        all_results = []
        
        print(f"\n🔍 Buscando '{keyword}' em canais do Telegram...\n")
        
        for channel in self.LEAK_CHANNELS:
            print(f"  📱 {channel['name']}...", end=" ", flush=True)
            results = self.scrape_channel(channel['url'], keyword)
            
            relevant = [r for r in results if not r.get('error')]
            print(f"✅ {len(relevant)} mensagens")
            
            all_results.extend(results)
        
        return all_results


class PasteSiteSearcher:
    """
    Buscador em sites de paste para leaks.
    """
    
    PASTE_SITES = {
        "pastebin": {
            "name": "Pastebin",
            "search_url": "https://pastebin.com/search?q=",
            "raw_url": "https://pastebin.com/raw/",
            "status": "requires_pro"
        },
        "ghostbin": {
            "name": "Ghostbin",
            "base_url": "https://ghostbin.com/",
            "status": "active"
        },
        "dpaste": {
            "name": "Dpaste",
            "base_url": "https://dpaste.org/",
            "status": "active"
        },
        "rentry": {
            "name": "Rentry.co",
            "base_url": "https://rentry.co/",
            "raw_url": "https://rentry.co/{}/raw",
            "status": "active"
        },
        "paste_ee": {
            "name": "Paste.ee",
            "base_url": "https://paste.ee/",
            "status": "active"
        }
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.rate_limit = 2.0
    
    def search_via_google(self, query: str, site: str = "pastebin.com") -> List[Dict]:
        """
        Busca pastes via Google Dorks.
        """
        results = []
        
        # Construir dork
        dork = f'site:{site} "{query}"'
        url = f"https://www.google.com/search?q={quote(dork)}&num=20"
        
        try:
            time.sleep(self.rate_limit)
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code == 200:
                # Extrair URLs do site alvo
                pattern = rf'(https?://{re.escape(site)}/[a-zA-Z0-9]+)'
                urls = re.findall(pattern, resp.text)
                
                for paste_url in set(urls)[:10]:
                    results.append({
                        "source": "Google Dork",
                        "site": site,
                        "url": paste_url,
                        "query": query
                    })
        except Exception as e:
            results.append({"error": str(e)})
        
        return results
    
    def fetch_paste(self, url: str) -> Optional[str]:
        """Baixa conteúdo de um paste."""
        try:
            # Converter para URL raw se possível
            if "pastebin.com" in url and "/raw/" not in url:
                paste_id = url.split("/")[-1]
                url = f"https://pastebin.com/raw/{paste_id}"
            elif "rentry.co" in url and "/raw" not in url:
                paste_id = url.rstrip('/').split("/")[-1]
                url = f"https://rentry.co/{paste_id}/raw"
            
            time.sleep(self.rate_limit)
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code == 200:
                return resp.text
        except Exception:
            pass
        
        return None
    
    def search_psbdmp(self, query: str) -> List[Dict]:
        """
        PSBDMP - Pastebin Dump Searcher.
        https://psbdmp.ws
        """
        url = f"https://psbdmp.ws/api/v3/search/{quote(query)}"
        
        try:
            time.sleep(self.rate_limit)
            resp = self.session.get(url, timeout=20)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("data"):
                    return [{
                        "source": "PSBDMP",
                        "id": item.get("id"),
                        "time": item.get("time"),
                        "tags": item.get("tags", ""),
                        "url": f"https://psbdmp.ws/{item.get('id')}"
                    } for item in data["data"][:20]]
        except Exception as e:
            return [{"source": "PSBDMP", "error": str(e)}]
        
        return []


class BreachDatabaseAggregator:
    """
    Agregador de bases de dados de vazamentos.
    """
    
    KNOWN_BREACHES = {
        "major": [
            {"name": "Collection #1-5", "records": "2.2B", "year": 2019, "type": "email:password"},
            {"name": "LinkedIn 2021", "records": "700M", "year": 2021, "type": "profile data"},
            {"name": "Facebook 2021", "records": "533M", "year": 2021, "type": "phone:name:email"},
            {"name": "Clubhouse", "records": "1.3M", "year": 2021, "type": "profile data"},
            {"name": "RockYou2024", "records": "10B", "year": 2024, "type": "passwords"},
            {"name": "MOAB", "records": "26B", "year": 2024, "type": "compiled"},
            {"name": "Twitter/X 2023", "records": "200M", "year": 2023, "type": "email:profile"},
            {"name": "Deezer", "records": "229M", "year": 2023, "type": "email:profile"},
            {"name": "Duolingo", "records": "2.6M", "year": 2023, "type": "email:name"},
        ],
        "brazil": [
            {"name": "Serasa Experian", "records": "223M", "year": 2021, "type": "cpf:nome:score"},
            {"name": "DataSUS", "records": "243M", "year": 2021, "type": "cpf:nome:endereco"},
            {"name": "Poupatempo", "records": "13M", "year": 2021, "type": "cpf:rg:foto"},
            {"name": "Detran", "records": "70M", "year": 2021, "type": "cpf:cnh:placa"},
            {"name": "Polícia Federal", "records": "426M", "year": 2022, "type": "cpf:passaporte"},
            {"name": "INSS", "records": "39M", "year": 2022, "type": "cpf:beneficio"},
            {"name": "Receita Federal", "records": "223M", "year": 2023, "type": "cpf:cnpj:endereco"},
            {"name": "Netshoes", "records": "2M", "year": 2018, "type": "email:cpf:compras"},
            {"name": "Banco Inter", "records": "19K", "year": 2018, "type": "dados bancários"},
        ],
        "gaming": [
            {"name": "Zynga", "records": "173M", "year": 2019, "type": "email:password"},
            {"name": "Roblox", "records": "4M", "year": 2023, "type": "profile:email"},
            {"name": "Epic Games", "records": "800K", "year": 2019, "type": "email:password"},
            {"name": "Steam (3rd party)", "records": "35M", "year": 2023, "type": "email:password"},
        ]
    }
    
    def __init__(self, db_path: str = "data/breaches.db"):
        self.db_path = db_path
        self.darkweb = DarkWebSearcher(use_tor=False)
        self.telegram = TelegramLeakMonitor()
        self.pastes = PasteSiteSearcher()
        self._init_db()
    
    def _init_db(self):
        """Inicializa banco de dados local."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                query_type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                sources_checked TEXT,
                results_count INTEGER,
                results_json TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS found_leaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                source TEXT,
                data_type TEXT,
                data_hash TEXT UNIQUE,
                data_preview TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_search(self, query: str, query_type: str, sources: List[str], results: List[Dict]):
        """Salva busca no histórico."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO search_history (query, query_type, sources_checked, results_count, results_json)
            VALUES (?, ?, ?, ?, ?)
        ''', (query, query_type, json.dumps(sources), len(results), json.dumps(results, default=str)))
        
        conn.commit()
        conn.close()
    
    def comprehensive_search(self, query: str, query_type: str = "email") -> Dict:
        """
        Busca abrangente em todas as fontes disponíveis.
        """
        results = {
            "query": query,
            "query_type": query_type,
            "timestamp": datetime.now().isoformat(),
            "sources": {},
            "total_results": 0,
            "errors": []
        }
        
        print(f"\n{'='*60}")
        print(f"🔍 BUSCA DARK WEB: {query}")
        print(f"{'='*60}\n")
        
        sources_checked = []
        
        # 1. DarkSearch API
        print("  🌐 [1/5] DarkSearch API...", end=" ", flush=True)
        try:
            ds_results = self.darkweb.search_darksearch_api(query)
            results["sources"]["darksearch"] = ds_results
            sources_checked.append("DarkSearch")
            
            if ds_results.get("success"):
                count = len(ds_results.get("results", []))
                results["total_results"] += count
                print(f"✅ {count} resultados")
            else:
                print(f"❌ {ds_results.get('error', 'Sem resultados')}")
        except Exception as e:
            results["errors"].append(f"DarkSearch: {e}")
            print(f"❌ {e}")
        
        # 2. IntelligenceX
        print("  🔎 [2/5] IntelligenceX...", end=" ", flush=True)
        try:
            ix_results = self.darkweb.search_intelx_free(query)
            results["sources"]["intelx"] = ix_results
            sources_checked.append("IntelligenceX")
            
            if ix_results.get("found"):
                count = ix_results.get("count", 0)
                results["total_results"] += count
                print(f"✅ {count} resultados")
            else:
                print(f"❌ Sem resultados")
        except Exception as e:
            results["errors"].append(f"IntelX: {e}")
            print(f"❌ {e}")
        
        # 3. Ahmia (clearnet)
        print("  🧅 [3/5] Ahmia (Clearnet)...", end=" ", flush=True)
        try:
            ahmia_results = self.darkweb.search_ahmia(query, use_clearnet=True)
            results["sources"]["ahmia"] = ahmia_results
            sources_checked.append("Ahmia")
            
            valid_results = [r for r in ahmia_results if not r.get("error")]
            results["total_results"] += len(valid_results)
            print(f"✅ {len(valid_results)} links .onion")
        except Exception as e:
            results["errors"].append(f"Ahmia: {e}")
            print(f"❌ {e}")
        
        # 4. Telegram Channels
        print("  📱 [4/5] Telegram Channels...", end=" ", flush=True)
        try:
            tg_results = self.telegram.search_all_channels(query)
            results["sources"]["telegram"] = tg_results
            sources_checked.append("Telegram")
            
            valid_results = [r for r in tg_results if not r.get("error")]
            results["total_results"] += len(valid_results)
            print(f"✅ {len(valid_results)} mensagens")
        except Exception as e:
            results["errors"].append(f"Telegram: {e}")
            print(f"❌ {e}")
        
        # 5. PSBDMP (Paste dumps)
        print("  📋 [5/5] PSBDMP (Pastes)...", end=" ", flush=True)
        try:
            paste_results = self.pastes.search_psbdmp(query)
            results["sources"]["pastes"] = paste_results
            sources_checked.append("PSBDMP")
            
            valid_results = [r for r in paste_results if not r.get("error")]
            results["total_results"] += len(valid_results)
            print(f"✅ {len(valid_results)} pastes")
        except Exception as e:
            results["errors"].append(f"PSBDMP: {e}")
            print(f"❌ {e}")
        
        # Salvar no banco
        self.save_search(query, query_type, sources_checked, results)
        
        return results
    
    def print_results(self, results: Dict):
        """Imprime resultados formatados."""
        print(f"\n{'='*60}")
        print(f"📊 RESULTADOS DA BUSCA")
        print(f"{'='*60}")
        
        print(f"\nQuery: {results.get('query')}")
        print(f"Total de resultados: {results.get('total_results', 0)}")
        
        sources = results.get("sources", {})
        
        # DarkSearch
        if "darksearch" in sources:
            ds = sources["darksearch"]
            if ds.get("results"):
                print(f"\n🌐 DARKSEARCH ({len(ds['results'])} resultados):")
                for r in ds["results"][:5]:
                    print(f"   • {r.get('title', 'Sem título')[:60]}")
                    print(f"     {r.get('link', 'N/A')[:80]}")
        
        # IntelX
        if "intelx" in sources:
            ix = sources["intelx"]
            if ix.get("results"):
                print(f"\n🔎 INTELLIGENCEX ({ix.get('count', 0)} resultados):")
                for r in ix["results"][:5]:
                    print(f"   • {r.get('selectorvalue', r)}")
        
        # Ahmia
        if "ahmia" in sources:
            ahmia = sources["ahmia"]
            valid = [r for r in ahmia if not r.get("error") and r.get("url")]
            if valid:
                print(f"\n🧅 AHMIA ({len(valid)} links .onion):")
                for r in valid[:5]:
                    print(f"   • {r.get('url', 'N/A')[:70]}...")
        
        # Telegram
        if "telegram" in sources:
            tg = sources["telegram"]
            valid = [r for r in tg if not r.get("error") and r.get("message")]
            if valid:
                print(f"\n📱 TELEGRAM ({len(valid)} mensagens):")
                for r in valid[:3]:
                    msg = r.get("message", "")[:100]
                    print(f"   • {msg}...")
        
        # Pastes
        if "pastes" in sources:
            pastes = sources["pastes"]
            valid = [r for r in pastes if not r.get("error")]
            if valid:
                print(f"\n📋 PASTES ({len(valid)} encontrados):")
                for r in valid[:5]:
                    print(f"   • {r.get('url', 'N/A')}")
        
        if results.get("errors"):
            print(f"\n⚠️ Erros: {len(results['errors'])}")
        
        print(f"\n{'='*60}")
    
    def list_known_breaches(self, category: str = "all") -> List[Dict]:
        """Lista breaches conhecidos por categoria."""
        if category == "all":
            all_breaches = []
            for cat, breaches in self.KNOWN_BREACHES.items():
                for b in breaches:
                    b["category"] = cat
                    all_breaches.append(b)
            return all_breaches
        
        return self.KNOWN_BREACHES.get(category, [])


def check_tor_setup():
    """Verifica e mostra instruções de setup do Tor."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    🧅 SETUP DO TOR                            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Para acessar sites .onion, você precisa do Tor:             ║
║                                                              ║
║  WINDOWS:                                                    ║
║  1. Baixe Tor Browser: https://www.torproject.org/           ║
║  2. Ou instale Expert Bundle:                                ║
║     https://www.torproject.org/download/tor/                 ║
║  3. Execute tor.exe (porta SOCKS: 9050)                      ║
║                                                              ║
║  LINUX:                                                      ║
║  sudo apt install tor                                        ║
║  sudo systemctl start tor                                    ║
║                                                              ║
║  VERIFICAR:                                                  ║
║  curl --socks5 127.0.0.1:9050 https://check.torproject.org   ║
║                                                              ║
║  PYTHON:                                                     ║
║  pip install PySocks stem requests[socks]                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)


def interactive_menu():
    """Menu interativo para acesso dark web."""
    aggregator = BreachDatabaseAggregator()
    darkweb = DarkWebSearcher(use_tor=False)
    tor = TorConnection()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║            🌑 DARK WEB LEAK AGGREGATOR                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ──── 🔍 BUSCA ────                                          ║
║  [1] 🔍 Busca COMPLETA (todas as fontes)                     ║
║  [2] 🌐 DarkSearch API (dark web via clearnet)               ║
║  [3] 🔎 IntelligenceX (free tier)                            ║
║  [4] 🧅 Ahmia Search (dark web index)                        ║
║                                                              ║
║  ──── 📱 TELEGRAM & PASTES ────                              ║
║  [5] 📱 Buscar em canais do Telegram                         ║
║  [6] 📋 Buscar em Paste Sites (PSBDMP)                       ║
║                                                              ║
║  ──── 📂 DATABASES ────                                      ║
║  [7] 📂 Ver breaches conhecidos                              ║
║  [8] 📂 Ver breaches BRASIL                                  ║
║                                                              ║
║  ──── 🧅 TOR ────                                            ║
║  [9] 🧅 Verificar conexão Tor                                ║
║  [10] 📖 Setup do Tor                                        ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            query = input("\n🔍 Digite a busca (email, domínio, nome, etc): ").strip()
            if query:
                results = aggregator.comprehensive_search(query)
                aggregator.print_results(results)
                
                save = input("\nSalvar resultados? (s/n): ").strip().lower()
                if save == 's':
                    os.makedirs("data/darkweb_results", exist_ok=True)
                    filename = f"data/darkweb_results/{query.replace('@', '_at_').replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
                    print(f"✅ Salvo: {filename}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '2':
            query = input("\n🌐 Digite a busca: ").strip()
            if query:
                print("\nBuscando no DarkSearch...")
                results = darkweb.search_darksearch_api(query)
                
                if results.get("success"):
                    print(f"\n✅ {results.get('total', 0)} resultados encontrados:\n")
                    for r in results.get("results", [])[:10]:
                        print(f"  • {r.get('title', 'Sem título')[:60]}")
                        print(f"    {r.get('link', 'N/A')}")
                        print()
                else:
                    print(f"❌ {results.get('error', 'Sem resultados')}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '3':
            query = input("\n🔎 Digite a busca: ").strip()
            if query:
                print("\nBuscando no IntelligenceX...")
                results = darkweb.search_intelx_free(query)
                
                if results.get("found"):
                    print(f"\n✅ {results.get('count', 0)} resultados:\n")
                    for r in results.get("results", [])[:15]:
                        if isinstance(r, dict):
                            print(f"  • {r.get('selectorvalue', r)}")
                        else:
                            print(f"  • {r}")
                else:
                    print("❌ Nenhum resultado encontrado")
            input("\nPressione Enter para continuar...")
        
        elif choice == '4':
            query = input("\n🧅 Digite a busca: ").strip()
            if query:
                print("\nBuscando no Ahmia (clearnet)...")
                results = darkweb.search_ahmia(query, use_clearnet=True)
                
                valid = [r for r in results if not r.get("error") and r.get("url")]
                if valid:
                    print(f"\n✅ {len(valid)} links .onion encontrados:\n")
                    for r in valid[:15]:
                        print(f"  🧅 {r.get('url')}")
                else:
                    print("❌ Nenhum link .onion encontrado")
            input("\nPressione Enter para continuar...")
        
        elif choice == '5':
            keyword = input("\n📱 Keyword para buscar: ").strip()
            if keyword:
                tg_monitor = TelegramLeakMonitor()
                results = tg_monitor.search_all_channels(keyword)
                
                valid = [r for r in results if not r.get("error")]
                print(f"\n✅ {len(valid)} resultados encontrados")
                
                for r in valid[:10]:
                    if r.get("message"):
                        print(f"\n  📱 {r.get('channel', 'Unknown')}")
                        print(f"     {r.get('message', '')[:150]}...")
                        if r.get("download_links"):
                            print(f"     📥 Links: {', '.join(r['download_links'][:3])}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '6':
            query = input("\n📋 Digite a busca: ").strip()
            if query:
                pastes = PasteSiteSearcher()
                print("\nBuscando no PSBDMP...")
                results = pastes.search_psbdmp(query)
                
                valid = [r for r in results if not r.get("error")]
                if valid:
                    print(f"\n✅ {len(valid)} pastes encontrados:\n")
                    for r in valid[:15]:
                        print(f"  📋 {r.get('url')}")
                        print(f"     Tags: {r.get('tags', 'N/A')}")
                else:
                    print("❌ Nenhum paste encontrado")
            input("\nPressione Enter para continuar...")
        
        elif choice == '7':
            print("\n📂 BREACHES CONHECIDOS (Major):\n")
            breaches = aggregator.list_known_breaches("major")
            for b in breaches:
                print(f"  • {b['name']} ({b['year']})")
                print(f"    {b['records']} registros - Tipo: {b['type']}")
                print()
            input("\nPressione Enter para continuar...")
        
        elif choice == '8':
            print("\n🇧🇷 BREACHES BRASIL:\n")
            breaches = aggregator.list_known_breaches("brazil")
            for b in breaches:
                print(f"  • {b['name']} ({b['year']})")
                print(f"    {b['records']} registros - Tipo: {b['type']}")
                print()
            input("\nPressione Enter para continuar...")
        
        elif choice == '9':
            print("\n🧅 Verificando conexão Tor...")
            result = tor.check_tor_connection()
            print(f"\n{result.get('message')}")
            if result.get("connected"):
                print(f"   IP Tor: {result.get('ip')}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '10':
            check_tor_setup()
            input("\nPressione Enter para continuar...")
        
        elif choice == '0':
            break


if __name__ == '__main__':
    interactive_menu()
