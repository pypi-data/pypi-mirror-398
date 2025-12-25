#!/usr/bin/env python3
"""
paste_monitor.py

Monitor de pastes e fontes públicas de vazamentos.
Monitora Pastebin, Ghostbin, e outras fontes em tempo real.

AVISO LEGAL: Use apenas para fins de pesquisa de segurança.
"""
import os
import re
import json
import time
import hashlib
import requests
from datetime import datetime
from typing import Optional, Dict, List, Any
from concurrent.futures import ThreadPoolExecutor


class PasteMonitor:
    """
    Monitor de pastes públicos para buscar vazamentos.
    """
    
    # Sites de paste conhecidos
    PASTE_SITES = {
        "pastebin": {
            "scrape_url": "https://scrape.pastebin.com/api_scraping.php",  # Requer IP whitelist
            "raw_url": "https://pastebin.com/raw/",
            "search_via": "google_dork"
        },
        "paste.ee": {
            "base_url": "https://paste.ee/",
            "raw_url": "https://paste.ee/r/",
            "search_via": "google_dork"
        },
        "gist.github.com": {
            "search_url": "https://gist.github.com/search?q=",
            "search_via": "api"
        },
        "rentry.co": {
            "raw_url": "https://rentry.co/",
            "search_via": "google_dork"
        }
    }
    
    # Padrões para identificar dados sensíveis
    SENSITIVE_PATTERNS = {
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "password_combo": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[:;|][^\s\n]+',
        "credit_card": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b',
        "cpf": r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
        "phone_br": r'\+?55?\s?(?:\(?\d{2}\)?[\s-]?)?\d{4,5}[\s-]?\d{4}',
        "hash_md5": r'\b[a-fA-F0-9]{32}\b',
        "hash_sha1": r'\b[a-fA-F0-9]{40}\b',
        "hash_sha256": r'\b[a-fA-F0-9]{64}\b',
        "bitcoin_address": r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',
        "api_key": r'(?i)(?:api[_-]?key|apikey|access[_-]?token)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})',
        "aws_key": r'AKIA[0-9A-Z]{16}',
        "jwt_token": r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
        "private_key": r'-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----',
        "ssh_key": r'ssh-(?:rsa|dss|ed25519) [A-Za-z0-9+/=]+'
    }
    
    def __init__(self, output_dir: str = "data/pastes"):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_google_dorks(self, query: str) -> List[str]:
        """
        Gera Google Dorks para buscar dados vazados.
        
        Args:
            query: Termo de busca (email, domínio, etc.)
            
        Returns:
            Lista de dorks para usar no Google
        """
        dorks = [
            # Pastes
            f'site:pastebin.com "{query}"',
            f'site:paste.ee "{query}"',
            f'site:ghostbin.com "{query}"',
            f'site:hastebin.com "{query}"',
            f'site:justpaste.it "{query}"',
            f'site:rentry.co "{query}"',
            f'site:pastebin.pl "{query}"',
            f'site:dpaste.org "{query}"',
            
            # GitHub/GitLab
            f'site:github.com "{query}" password OR pwd OR pass',
            f'site:gitlab.com "{query}" password OR token',
            f'site:gist.github.com "{query}"',
            
            # Documentos
            f'filetype:txt "{query}" password',
            f'filetype:sql "{query}"',
            f'filetype:log "{query}" email',
            f'filetype:csv "{query}" password OR email',
            f'filetype:xls OR filetype:xlsx "{query}" password',
            
            # Leaks específicos
            f'intitle:"index of" "{query}"',
            f'"{query}" + password leak',
            f'"{query}" + database dump',
            f'"{query}" + combo list',
            f'"{query}" + @gmail.com filetype:txt',
            
            # Exposed directories
            f'intitle:"index of" "passwords" OR "credentials"',
            f'intitle:"index of" "backup" ext:sql',
            f'intitle:"index of" ".env"',
            
            # Error messages exposing data
            f'"{query}" + "mysql" + "syntax error"',
            f'"{query}" + "postgresql" + "error"',
        ]
        
        return dorks
    
    def analyze_paste_content(self, content: str) -> Dict:
        """
        Analisa o conteúdo de um paste buscando dados sensíveis.
        
        Args:
            content: Texto do paste
            
        Returns:
            Dict com dados encontrados
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_lines": len(content.splitlines()),
            "findings": {},
            "sample_data": {}
        }
        
        for pattern_name, pattern in self.SENSITIVE_PATTERNS.items():
            matches = re.findall(pattern, content)
            if matches:
                results["findings"][pattern_name] = len(matches)
                # Guardar amostra (censurada para emails/senhas)
                if pattern_name == "email":
                    results["sample_data"][pattern_name] = [
                        m[:3] + "***@" + m.split("@")[1][:5] + "***"
                        for m in matches[:5]
                    ]
                elif pattern_name in ["password_combo", "credit_card", "cpf"]:
                    results["sample_data"][pattern_name] = [
                        m[:5] + "***CENSURADO***"
                        for m in matches[:3]
                    ]
                else:
                    results["sample_data"][pattern_name] = matches[:5]
        
        return results
    
    def fetch_raw_paste(self, paste_id: str, site: str = "pastebin") -> Optional[str]:
        """Busca conteúdo raw de um paste."""
        if site == "pastebin":
            url = f"https://pastebin.com/raw/{paste_id}"
        elif site == "paste.ee":
            url = f"https://paste.ee/r/{paste_id}"
        elif site == "rentry.co":
            url = f"https://rentry.co/{paste_id}/raw"
        else:
            return None
        
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.text
        except Exception:
            pass
        
        return None
    
    def search_gist(self, query: str, max_results: int = 50) -> List[Dict]:
        """
        Busca em GitHub Gists (API pública).
        
        Nota: Rate limited, requer token para mais requests.
        """
        results = []
        search_url = f"https://api.github.com/gists/public"
        
        try:
            resp = self.session.get(search_url, timeout=15)
            if resp.status_code == 200:
                gists = resp.json()
                for gist in gists[:max_results]:
                    gist_info = {
                        "id": gist["id"],
                        "url": gist["html_url"],
                        "description": gist.get("description", ""),
                        "created_at": gist["created_at"],
                        "files": list(gist.get("files", {}).keys())
                    }
                    results.append(gist_info)
        except Exception:
            pass
        
        return results
    
    def save_findings(self, findings: Dict, query: str):
        """Salva achados em arquivo JSON."""
        filename = f"findings_{hashlib.md5(query.encode()).hexdigest()[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(findings, f, indent=2, ensure_ascii=False)
        
        return filepath


class TelegramLeakSearch:
    """
    Busca em canais públicos do Telegram.
    Nota: Muitos canais de leaks foram removidos.
    """
    
    # Mecanismos de busca de canais
    SEARCH_ENGINES = [
        "https://t.me/s/",  # Formato de preview público
        "https://telegram.me/s/"
    ]
    
    # Palavras-chave relacionadas a leaks
    KEYWORDS = [
        "leaked", "dump", "database", "combo", "breach",
        "passwords", "credentials", "hacked", "fullz",
        "logs", "stealer", "carding"
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_public_channel(self, channel_name: str) -> Optional[Dict]:
        """
        Busca mensagens públicas de um canal.
        
        Args:
            channel_name: Nome do canal (sem @)
            
        Returns:
            Dict com informações do canal e mensagens
        """
        url = f"https://t.me/s/{channel_name}"
        
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                # Parse básico
                messages = re.findall(r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', 
                                     resp.text, re.DOTALL)
                
                return {
                    "channel": channel_name,
                    "accessible": True,
                    "message_count": len(messages),
                    "sample_messages": [
                        re.sub(r'<[^>]+>', '', m)[:200]
                        for m in messages[:5]
                    ]
                }
            else:
                return {"channel": channel_name, "accessible": False}
        except Exception as e:
            return {"channel": channel_name, "error": str(e)}
    
    def generate_search_suggestions(self, target: str) -> List[str]:
        """Gera sugestões de busca para Telegram."""
        suggestions = []
        
        # Canais conhecidos de pesquisa de segurança
        security_channels = [
            "SecNews",
            "bugbountytips",
            "hackersnet",
            "cybersecuritynews"
        ]
        
        for ch in security_channels:
            suggestions.append(f"https://t.me/s/{ch}?q={target}")
        
        return suggestions


class BreachForumMonitor:
    """
    Classe para monitorar fóruns públicos de breach.
    NOTA: Muitos fóruns são na dark web (.onion) e requerem Tor.
    """
    
    # Fóruns de pesquisa de segurança (surface web)
    SURFACE_FORUMS = {
        "raidforums_archive": {
            "description": "Arquivo de RaidForums (fechado)",
            "status": "archived"
        },
        "breachforums": {
            "description": "Continuação do RaidForums",
            "status": "onion_only"
        },
        "leaked_forums": {
            "description": "Diversos fóruns de leaks",
            "status": "varies"
        }
    }
    
    # Fontes de pesquisa acessíveis
    RESEARCH_SOURCES = [
        {
            "name": "DataBreaches.net",
            "url": "https://www.databreaches.net/",
            "description": "Notícias sobre breaches",
            "type": "news"
        },
        {
            "name": "HackerNews",
            "url": "https://news.ycombinator.com/",
            "description": "Notícias de tech/security",
            "type": "news"
        },
        {
            "name": "BreachTalk",
            "url": "https://breachtalk.org/",
            "description": "Fórum de discussão sobre breaches",
            "type": "forum"
        },
        {
            "name": "Krebs on Security",
            "url": "https://krebsonsecurity.com/",
            "description": "Blog de Brian Krebs sobre security",
            "type": "blog"
        },
        {
            "name": "BleepingComputer",
            "url": "https://www.bleepingcomputer.com/",
            "description": "Notícias de cybersecurity",
            "type": "news"
        },
        {
            "name": "Troy Hunt Blog",
            "url": "https://www.troyhunt.com/",
            "description": "Criador do HIBP",
            "type": "blog"
        }
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_research_sources(self) -> List[Dict]:
        """Retorna lista de fontes de pesquisa."""
        return self.RESEARCH_SOURCES
    
    def check_source_status(self, source: Dict) -> Dict:
        """Verifica se uma fonte está online."""
        try:
            resp = self.session.head(source["url"], timeout=10)
            source["online"] = resp.status_code == 200
        except:
            source["online"] = False
        return source


def interactive_menu():
    """Menu interativo para o monitor de pastes."""
    monitor = PasteMonitor()
    tg_search = TelegramLeakSearch()
    forums = BreachForumMonitor()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║       📋 PASTE & LEAK MONITOR - Monitoramento                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔍 Gerar Google Dorks para busca                        ║
║  [2] 📄 Analisar conteúdo de paste                           ║
║  [3] 📱 Buscar em canais Telegram                            ║
║  [4] 📰 Ver fontes de pesquisa                               ║
║  [5] 🔎 Analisar arquivo local (CSV/TXT)                     ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            query = input("\nDigite o termo de busca (email, domínio, etc): ").strip()
            if query:
                print("\n📋 GOOGLE DORKS GERADOS:\n")
                dorks = monitor.generate_google_dorks(query)
                for i, dork in enumerate(dorks, 1):
                    print(f"  {i:2}. {dork}")
                
                print("\n💡 COMO USAR:")
                print("   1. Copie o dork desejado")
                print("   2. Cole no Google (google.com)")
                print("   3. Analise os resultados encontrados")
            input("\nPressione Enter para continuar...")
        
        elif choice == '2':
            print("\n[1] Colar conteúdo aqui")
            print("[2] Buscar paste por ID (Pastebin)")
            sub = input("\nOpção: ").strip()
            
            if sub == '1':
                print("\nCole o conteúdo (digite 'FIM' em uma linha para terminar):")
                lines = []
                while True:
                    line = input()
                    if line == 'FIM':
                        break
                    lines.append(line)
                content = '\n'.join(lines)
                
                if content:
                    results = monitor.analyze_paste_content(content)
                    print("\n📊 ANÁLISE DO CONTEÚDO:")
                    print(f"   Linhas: {results['total_lines']}")
                    
                    if results['findings']:
                        print("\n   🔍 Dados encontrados:")
                        for pattern, count in results['findings'].items():
                            print(f"      • {pattern}: {count} ocorrências")
                        
                        if results['sample_data']:
                            print("\n   📝 Amostras (censuradas):")
                            for pattern, samples in results['sample_data'].items():
                                print(f"      {pattern}:")
                                for s in samples[:3]:
                                    print(f"         - {s}")
                    else:
                        print("   Nenhum dado sensível detectado.")
            
            elif sub == '2':
                paste_id = input("\nID do paste (ex: abc123): ").strip()
                if paste_id:
                    print("\nBuscando paste...")
                    content = monitor.fetch_raw_paste(paste_id)
                    if content:
                        results = monitor.analyze_paste_content(content)
                        print(f"\n📊 Linhas: {results['total_lines']}")
                        if results['findings']:
                            for pattern, count in results['findings'].items():
                                print(f"   • {pattern}: {count}")
                    else:
                        print("❌ Paste não encontrado ou inacessível")
            
            input("\nPressione Enter para continuar...")
        
        elif choice == '3':
            channel = input("\nNome do canal (sem @): ").strip()
            if channel:
                print(f"\n🔍 Buscando canal @{channel}...")
                result = tg_search.search_public_channel(channel)
                
                if result.get("accessible"):
                    print(f"\n✅ Canal acessível!")
                    print(f"   Mensagens encontradas: {result['message_count']}")
                    if result.get("sample_messages"):
                        print("\n   Amostras de mensagens:")
                        for msg in result["sample_messages"][:3]:
                            print(f"   - {msg[:100]}...")
                elif result.get("error"):
                    print(f"\n❌ Erro: {result['error']}")
                else:
                    print("\n❌ Canal não acessível ou não existe")
            
            input("\nPressione Enter para continuar...")
        
        elif choice == '4':
            print("\n📰 FONTES DE PESQUISA DE SECURITY:\n")
            
            sources = forums.get_research_sources()
            for source in sources:
                status = forums.check_source_status(source)
                online = "🟢" if status.get("online") else "🔴"
                print(f"   {online} {source['name']}")
                print(f"      {source['url']}")
                print(f"      {source['description']}")
                print()
            
            input("\nPressione Enter para continuar...")
        
        elif choice == '5':
            filepath = input("\nCaminho do arquivo: ").strip()
            if os.path.exists(filepath):
                print(f"\n📄 Analisando {filepath}...")
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    results = monitor.analyze_paste_content(content)
                    print(f"\n📊 ANÁLISE:")
                    print(f"   Linhas: {results['total_lines']}")
                    
                    if results['findings']:
                        print("\n   🔍 Dados encontrados:")
                        for pattern, count in results['findings'].items():
                            print(f"      • {pattern}: {count} ocorrências")
                    
                    # Salvar achados
                    save = input("\nSalvar relatório? (s/n): ").strip().lower()
                    if save == 's':
                        saved = monitor.save_findings(results, filepath)
                        print(f"✅ Salvo em: {saved}")
                except Exception as e:
                    print(f"❌ Erro: {e}")
            else:
                print("❌ Arquivo não encontrado")
            
            input("\nPressione Enter para continuar...")
        
        elif choice == '0':
            break


if __name__ == '__main__':
    interactive_menu()
