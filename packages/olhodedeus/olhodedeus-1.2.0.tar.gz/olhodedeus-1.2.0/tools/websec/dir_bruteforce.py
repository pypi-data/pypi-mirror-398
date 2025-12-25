#!/usr/bin/env python3
"""
Directory Bruteforce - Olho de Deus
Descoberta de diretórios e arquivos ocultos em servidores web
"""

import requests
import threading
import queue
import time
import re
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urljoin, urlparse

# Adicionar path para imports locais
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from tools.utilities.progress_bar import ProgressBar, Spinner
except ImportError:
    ProgressBar = None
    Spinner = None


@dataclass
class BruteforceResult:
    """Resultado de descoberta"""
    url: str
    status_code: int
    content_length: int = 0
    content_type: str = ""
    redirect_url: str = ""
    response_time: float = 0.0
    is_directory: bool = False
    title: str = ""


@dataclass
class ScanStats:
    """Estatísticas do scan"""
    total_requests: int = 0
    found: int = 0
    errors: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    
    @property
    def duration(self) -> float:
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def requests_per_second(self) -> float:
        if self.duration > 0:
            return self.total_requests / self.duration
        return 0


class DirectoryBruteforce:
    """Bruteforce de diretórios e arquivos"""
    
    # Wordlist básica embutida
    DEFAULT_WORDLIST = [
        # Diretórios comuns
        "admin", "administrator", "login", "wp-admin", "dashboard",
        "panel", "cpanel", "phpmyadmin", "adminer", "manager",
        "api", "v1", "v2", "rest", "graphql", "swagger", "docs",
        "backup", "backups", "bak", "old", "temp", "tmp", "cache",
        "uploads", "upload", "files", "static", "assets", "media",
        "images", "img", "css", "js", "fonts", "scripts",
        "config", "conf", "cfg", "settings", "setup", "install",
        "test", "testing", "dev", "development", "staging", "demo",
        "private", "secret", "hidden", ".git", ".svn", ".env",
        "logs", "log", "debug", "error", "errors",
        "data", "database", "db", "sql", "mysql", "dump",
        "include", "includes", "inc", "lib", "libs", "vendor",
        "cgi-bin", "bin", "scripts", "shell", "cmd",
        "user", "users", "member", "members", "account", "accounts",
        "blog", "news", "post", "posts", "article", "articles",
        "shop", "store", "cart", "checkout", "payment",
        # Arquivos comuns
        "index.php", "index.html", "index.htm", "default.asp",
        "login.php", "admin.php", "config.php", "wp-config.php",
        "robots.txt", "sitemap.xml", "crossdomain.xml", ".htaccess",
        "web.config", "phpinfo.php", "info.php", "test.php",
        "readme.txt", "readme.md", "README.md", "LICENSE",
        "changelog.txt", "CHANGELOG.md", "VERSION", "version.txt",
        ".env", ".env.local", ".env.production", ".env.example",
        "composer.json", "package.json", "Gemfile", "requirements.txt",
        "backup.sql", "database.sql", "dump.sql", "db.sql",
        "backup.zip", "backup.tar.gz", "site.zip", "www.zip",
    ]
    
    # Extensões para testar
    EXTENSIONS = ["", ".php", ".html", ".asp", ".aspx", ".jsp", ".txt", ".bak", ".old"]
    
    # Status codes interessantes
    INTERESTING_CODES = [200, 201, 301, 302, 307, 308, 401, 403, 405, 500]
    
    def __init__(self, timeout: float = 10.0, threads: int = 20):
        self.timeout = timeout
        self.threads = threads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        self.stats = ScanStats()
        self.found_urls: List[BruteforceResult] = []
        self._stop_event = threading.Event()
    
    def scan(self, base_url: str, wordlist: List[str] = None, 
             extensions: List[str] = None, recursive: bool = False) -> List[BruteforceResult]:
        """Executa bruteforce de diretórios"""
        
        if not base_url.startswith(('http://', 'https://')):
            base_url = 'http://' + base_url
        
        if not base_url.endswith('/'):
            base_url += '/'
        
        wordlist = wordlist or self.DEFAULT_WORDLIST
        extensions = extensions or [""]
        
        print(f"\n🔍 Directory Bruteforce: {base_url}")
        print(f"   Wordlist: {len(wordlist)} palavras")
        print(f"   Extensões: {extensions}")
        print(f"   Threads: {self.threads}")
        print("-" * 50)
        
        self.stats = ScanStats()
        self.found_urls = []
        
        # Gerar URLs para testar
        urls_to_test = []
        for word in wordlist:
            for ext in extensions:
                urls_to_test.append(urljoin(base_url, word + ext))
        
        # Criar barra de progresso (usa estilo configurado pelo usuário)
        pbar = None
        if ProgressBar:
            pbar = ProgressBar(
                len(urls_to_test),
                "   Scanning",
                show_percentage=True,
                show_speed=True,
                show_eta=True
            )
        
        # Executar scan
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {
                executor.submit(self._check_url, url): url 
                for url in urls_to_test
            }
            
            completed = 0
            for future in as_completed(futures):
                if self._stop_event.is_set():
                    break
                    
                try:
                    result = future.result()
                    self.stats.total_requests += 1
                    
                    if result:
                        self.found_urls.append(result)
                        self.stats.found += 1
                        self._print_result(result)
                        
                except Exception as e:
                    self.stats.errors += 1
                
                completed += 1
                if pbar:
                    pbar.set(completed)
        
        # Finalizar barra de progresso
        if pbar:
            pbar.finish()
        
        # Resumo
        print("\n" + "-" * 50)
        print(f"📊 Resumo:")
        print(f"   Requisições: {self.stats.total_requests}")
        print(f"   Encontrados: {self.stats.found}")
        print(f"   Erros: {self.stats.errors}")
        print(f"   Tempo: {self.stats.duration:.1f}s")
        print(f"   Velocidade: {self.stats.requests_per_second:.1f} req/s")
        
        return self.found_urls
    
    def _check_url(self, url: str) -> Optional[BruteforceResult]:
        """Verifica uma URL específica"""
        try:
            start = time.time()
            resp = self.session.get(
                url, 
                timeout=self.timeout, 
                allow_redirects=False,
                verify=False
            )
            elapsed = time.time() - start
            
            if resp.status_code in self.INTERESTING_CODES:
                result = BruteforceResult(
                    url=url,
                    status_code=resp.status_code,
                    content_length=len(resp.content),
                    content_type=resp.headers.get('Content-Type', ''),
                    response_time=elapsed
                )
                
                # Verificar redirect
                if resp.status_code in [301, 302, 307, 308]:
                    result.redirect_url = resp.headers.get('Location', '')
                
                # Verificar se é diretório
                if url.endswith('/') or 'directory' in resp.text.lower():
                    result.is_directory = True
                
                # Extrair título
                title_match = re.search(r'<title>([^<]+)</title>', resp.text, re.IGNORECASE)
                if title_match:
                    result.title = title_match.group(1).strip()[:50]
                
                return result
                
        except requests.exceptions.Timeout:
            pass
        except requests.exceptions.ConnectionError:
            pass
        except Exception:
            pass
        
        return None
    
    def _print_result(self, result: BruteforceResult):
        """Imprime resultado encontrado"""
        status_colors = {
            200: "✅",
            201: "✅",
            301: "↪️",
            302: "↪️",
            307: "↪️",
            308: "↪️",
            401: "🔒",
            403: "🚫",
            405: "⚠️",
            500: "💥",
        }
        
        icon = status_colors.get(result.status_code, "❓")
        size = self._format_size(result.content_length)
        
        line = f"   {icon} [{result.status_code}] {result.url} ({size})"
        
        if result.redirect_url:
            line += f" -> {result.redirect_url}"
        elif result.title:
            line += f" [{result.title}]"
        
        print(line)
    
    def _format_size(self, size: int) -> str:
        """Formata tamanho em bytes"""
        for unit in ['B', 'KB', 'MB']:
            if size < 1024:
                return f"{size:.0f}{unit}"
            size /= 1024
        return f"{size:.1f}GB"
    
    def scan_with_extensions(self, base_url: str, wordlist: List[str] = None) -> List[BruteforceResult]:
        """Scan com múltiplas extensões"""
        return self.scan(base_url, wordlist, self.EXTENSIONS)
    
    def load_wordlist(self, filepath: str) -> List[str]:
        """Carrega wordlist de arquivo"""
        words = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith('#'):
                        words.append(word)
            print(f"   📄 Wordlist carregada: {len(words)} palavras")
        except FileNotFoundError:
            print(f"   ⚠️ Arquivo não encontrado: {filepath}")
        return words
    
    def stop(self):
        """Para o scan"""
        self._stop_event.set()
    
    def export_results(self, filepath: str):
        """Exporta resultados para arquivo"""
        with open(filepath, 'w') as f:
            for result in self.found_urls:
                f.write(f"{result.status_code},{result.url},{result.content_length}\n")
        print(f"\n📄 Resultados salvos: {filepath}")
    
    def filter_by_status(self, status: int) -> List[BruteforceResult]:
        """Filtra resultados por status code"""
        return [r for r in self.found_urls if r.status_code == status]
    
    def get_directories(self) -> List[str]:
        """Retorna apenas diretórios encontrados"""
        return [r.url for r in self.found_urls if r.is_directory or r.url.endswith('/')]


# Suprimir warnings de SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    """Função principal"""
    import sys
    
    print("\n" + "=" * 50)
    print("🔍 Directory Bruteforce - Olho de Deus")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        url = input("\n🌐 URL alvo: ").strip()
    else:
        url = sys.argv[1]
    
    wordlist_file = None
    if len(sys.argv) > 2:
        wordlist_file = sys.argv[2]
    
    scanner = DirectoryBruteforce(threads=30)
    
    if wordlist_file:
        wordlist = scanner.load_wordlist(wordlist_file)
    else:
        wordlist = None
    
    try:
        results = scanner.scan(url, wordlist)
        
        # Mostrar resumo por status
        print("\n📋 Por status:")
        for status in [200, 301, 302, 403, 401]:
            count = len(scanner.filter_by_status(status))
            if count:
                print(f"   {status}: {count}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Scan interrompido!")
        scanner.stop()
    
    print("\n✅ Scan concluído!")


if __name__ == "__main__":
    main()
