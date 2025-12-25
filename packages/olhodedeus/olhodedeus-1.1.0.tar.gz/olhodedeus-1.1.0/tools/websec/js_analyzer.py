#!/usr/bin/env python3
"""
JavaScript Analyzer - Análise de JS para secrets, APIs, endpoints
Parte do toolkit Olho de Deus
"""

import os
import sys
import json
import re
import hashlib
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from urllib.parse import urlparse, urljoin
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class JSSecret:
    """Representa um secret encontrado."""
    type: str
    value: str
    context: str
    file: str
    line: int
    confidence: str  # high, medium, low
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "value": self.value[:50] + "..." if len(self.value) > 50 else self.value,
            "context": self.context[:100],
            "file": self.file,
            "line": self.line,
            "confidence": self.confidence
        }


@dataclass
class JSEndpoint:
    """Representa um endpoint encontrado."""
    url: str
    method: str
    file: str
    params: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "method": self.method,
            "file": self.file,
            "params": self.params
        }


class SecretPatterns:
    """Padrões para detecção de secrets."""
    
    PATTERNS = {
        # API Keys
        "aws_access_key": (r"AKIA[0-9A-Z]{16}", "high"),
        "aws_secret_key": (r"['\"][0-9a-zA-Z/+]{40}['\"]", "medium"),
        "google_api_key": (r"AIza[0-9A-Za-z\-_]{35}", "high"),
        "google_oauth": (r"[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com", "high"),
        "firebase_api_key": (r"AIza[0-9A-Za-z\-_]{35}", "high"),
        "github_token": (r"gh[pousr]_[0-9a-zA-Z]{36}", "high"),
        "github_oauth": (r"gho_[0-9a-zA-Z]{36}", "high"),
        "slack_token": (r"xox[baprs]-[0-9]{10,12}-[0-9]{10,12}-[a-zA-Z0-9]{24}", "high"),
        "slack_webhook": (r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{8,}/[a-zA-Z0-9_]{24}", "high"),
        "stripe_key": (r"sk_live_[0-9a-zA-Z]{24}", "high"),
        "stripe_publishable": (r"pk_live_[0-9a-zA-Z]{24}", "medium"),
        "twilio_sid": (r"AC[a-z0-9]{32}", "high"),
        "twilio_token": (r"SK[a-z0-9]{32}", "high"),
        "sendgrid_key": (r"SG\.[a-zA-Z0-9]{22}\.[a-zA-Z0-9-_]{43}", "high"),
        "mailgun_key": (r"key-[0-9a-zA-Z]{32}", "high"),
        "jwt_token": (r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*", "high"),
        "bearer_token": (r"['\"]Bearer\s+[a-zA-Z0-9_\-\.]+['\"]", "medium"),
        "basic_auth": (r"['\"]Basic\s+[a-zA-Z0-9+/=]+['\"]", "high"),
        "private_key": (r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----", "high"),
        "ssh_private": (r"-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----", "high"),
        
        # Database
        "mongodb_uri": (r"mongodb(\+srv)?://[^'\"\s]+", "high"),
        "postgres_uri": (r"postgres://[^'\"\s]+", "high"),
        "mysql_uri": (r"mysql://[^'\"\s]+", "high"),
        "redis_uri": (r"redis://[^'\"\s]+", "high"),
        
        # Cloud
        "azure_storage": (r"DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[^;]+", "high"),
        "azure_connection": (r"AccountKey=[a-zA-Z0-9+/=]{88}", "high"),
        
        # Generic
        "api_key_generic": (r"['\"]?api[_-]?key['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", "medium"),
        "secret_generic": (r"['\"]?secret['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", "medium"),
        "password_hardcoded": (r"['\"]?password['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]", "medium"),
        "token_generic": (r"['\"]?(?:access_?)?token['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_\-\.]{20,}['\"]", "medium"),
        
        # Internal URLs
        "internal_ip": (r"https?://(?:10\.|172\.(?:1[6-9]|2[0-9]|3[0-1])\.|192\.168\.)[0-9.]+", "medium"),
        "localhost": (r"https?://(?:localhost|127\.0\.0\.1)(?::\d+)?", "low"),
    }
    
    @classmethod
    def get_all(cls) -> Dict[str, Tuple[str, str]]:
        return cls.PATTERNS


class EndpointPatterns:
    """Padrões para extração de endpoints."""
    
    # Padrões de URL
    URL_PATTERNS = [
        r'["\'](/api/[^"\']*)["\']',
        r'["\'](/v[0-9]+/[^"\']*)["\']',
        r'["\'](https?://[^"\']+)["\']',
        r'fetch\s*\(\s*["\']([^"\']+)["\']',
        r'axios\s*\.\s*(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
        r'\.ajax\s*\(\s*\{[^}]*url\s*:\s*["\']([^"\']+)["\']',
        r'XMLHttpRequest[^;]+\.open\s*\([^,]+,\s*["\']([^"\']+)["\']',
        r'\.(?:get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']',
        r'baseURL\s*[:=]\s*["\']([^"\']+)["\']',
        r'endpoint\s*[:=]\s*["\']([^"\']+)["\']',
    ]
    
    # Métodos HTTP
    METHOD_PATTERNS = [
        (r'fetch\s*\([^)]+method\s*:\s*["\'](\w+)["\']', 1),
        (r'axios\.(\w+)\s*\(', 1),
        (r'\.ajax\s*\([^)]+type\s*:\s*["\'](\w+)["\']', 1),
        (r'XMLHttpRequest[^;]+\.open\s*\(["\'](\w+)["\']', 1),
    ]


class JavaScriptAnalyzer:
    """Analisador de código JavaScript."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self.secrets: List[JSSecret] = []
        self.endpoints: List[JSEndpoint] = []
        self.js_files: Set[str] = set()
    
    def analyze_url(self, url: str) -> Dict:
        """Analisa uma URL buscando arquivos JS."""
        results = {
            "url": url,
            "js_files": [],
            "secrets": [],
            "endpoints": [],
            "interesting": []
        }
        
        try:
            response = self.session.get(url, timeout=30)
            html = response.text
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            
            # Encontrar arquivos JS
            js_patterns = [
                r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']',
                r'["\']([^"\']+\.js)["\']',
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, html, re.I)
                for match in matches:
                    if match.startswith('//'):
                        js_url = f"https:{match}"
                    elif match.startswith('/'):
                        js_url = urljoin(base_url, match)
                    elif not match.startswith('http'):
                        js_url = urljoin(url, match)
                    else:
                        js_url = match
                    
                    self.js_files.add(js_url)
            
            results["js_files"] = list(self.js_files)
            
            # Analisar cada arquivo JS
            for js_url in self.js_files:
                file_results = self.analyze_js_file(js_url)
                results["secrets"].extend(file_results.get("secrets", []))
                results["endpoints"].extend(file_results.get("endpoints", []))
                results["interesting"].extend(file_results.get("interesting", []))
            
            # Analisar inline scripts
            inline_scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.I)
            for i, script in enumerate(inline_scripts):
                if script.strip():
                    inline_results = self.analyze_js_content(script, f"{url}#inline_{i}")
                    results["secrets"].extend(inline_results.get("secrets", []))
                    results["endpoints"].extend(inline_results.get("endpoints", []))
            
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def analyze_js_file(self, js_url: str) -> Dict:
        """Analisa um arquivo JS específico."""
        try:
            response = self.session.get(js_url, timeout=30)
            content = response.text
            return self.analyze_js_content(content, js_url)
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_js_content(self, content: str, source: str) -> Dict:
        """Analisa conteúdo JavaScript."""
        results = {
            "source": source,
            "secrets": [],
            "endpoints": [],
            "interesting": []
        }
        
        lines = content.split('\n')
        
        # Buscar secrets
        for pattern_name, (pattern, confidence) in SecretPatterns.get_all().items():
            for i, line in enumerate(lines, 1):
                matches = re.finditer(pattern, line, re.I)
                for match in matches:
                    # Contexto
                    start = max(0, match.start() - 20)
                    end = min(len(line), match.end() + 20)
                    context = line[start:end]
                    
                    secret = JSSecret(
                        type=pattern_name,
                        value=match.group(0),
                        context=context,
                        file=source,
                        line=i,
                        confidence=confidence
                    )
                    results["secrets"].append(secret.to_dict())
        
        # Buscar endpoints
        for pattern in EndpointPatterns.URL_PATTERNS:
            matches = re.findall(pattern, content, re.I)
            for match in matches:
                if self._is_valid_endpoint(match):
                    endpoint = JSEndpoint(
                        url=match,
                        method="GET",  # Default
                        file=source,
                        params=self._extract_params(match)
                    )
                    results["endpoints"].append(endpoint.to_dict())
        
        # Buscar coisas interessantes
        interesting_patterns = [
            (r'(?:admin|debug|test|dev)[_-]?(?:mode|flag|enabled)\s*[:=]\s*true', "Debug mode enabled"),
            (r'console\.log\s*\([^)]*(?:password|token|key|secret)', "Sensitive data in console.log"),
            (r'eval\s*\([^)]+\)', "eval() usage"),
            (r'innerHTML\s*=', "innerHTML assignment (XSS risk)"),
            (r'document\.write\s*\(', "document.write usage"),
            (r'\.html\s*\([^)]*\$', "jQuery .html() with variable (XSS risk)"),
            (r'localStorage\.setItem\s*\([^,]+,\s*[^)]*(?:token|key|password)', "Sensitive data in localStorage"),
            (r'postMessage\s*\([^)]+,\s*["\'\*]', "postMessage with wildcard origin"),
        ]
        
        for pattern, description in interesting_patterns:
            if re.search(pattern, content, re.I):
                results["interesting"].append({
                    "pattern": description,
                    "file": source
                })
        
        return results
    
    def _is_valid_endpoint(self, url: str) -> bool:
        """Verifica se é um endpoint válido."""
        # Ignorar arquivos estáticos
        static_ext = ['.js', '.css', '.png', '.jpg', '.gif', '.svg', '.ico', '.woff', '.ttf']
        for ext in static_ext:
            if url.lower().endswith(ext):
                return False
        
        # Deve parecer uma API ou rota
        if '/api/' in url or '/v1/' in url or '/v2/' in url:
            return True
        if re.match(r'^/[a-z]', url):
            return True
        if url.startswith('http'):
            return True
        
        return False
    
    def _extract_params(self, url: str) -> List[str]:
        """Extrai parâmetros de uma URL."""
        params = []
        
        # Query string
        if '?' in url:
            query = url.split('?')[1]
            for param in query.split('&'):
                if '=' in param:
                    params.append(param.split('=')[0])
        
        # Path parameters
        path_params = re.findall(r':(\w+)', url)
        params.extend(path_params)
        
        # Template literals
        template_params = re.findall(r'\$\{(\w+)\}', url)
        params.extend(template_params)
        
        return list(set(params))
    
    def analyze_directory(self, directory: str) -> Dict:
        """Analisa diretório de arquivos JS."""
        results = {
            "directory": directory,
            "files_analyzed": 0,
            "secrets": [],
            "endpoints": [],
            "interesting": []
        }
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.js'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        file_results = self.analyze_js_content(content, filepath)
                        results["secrets"].extend(file_results.get("secrets", []))
                        results["endpoints"].extend(file_results.get("endpoints", []))
                        results["interesting"].extend(file_results.get("interesting", []))
                        results["files_analyzed"] += 1
                        
                    except Exception as e:
                        continue
        
        return results
    
    def beautify_js(self, content: str) -> str:
        """Tenta beautificar JS minificado."""
        # Adicionar quebras de linha após ; { }
        content = re.sub(r';', ';\n', content)
        content = re.sub(r'\{', '{\n', content)
        content = re.sub(r'\}', '\n}\n', content)
        return content
    
    def export_results(self, results: Dict, output_file: str):
        """Exporta resultados para arquivo."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)


def interactive_menu():
    """Menu interativo do JavaScript Analyzer."""
    analyzer = JavaScriptAnalyzer()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║          📜 JAVASCRIPT ANALYZER - Olho de Deus               ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🌐 Analisar Website (busca JS automaticamente)          ║
║  [2] 📄 Analisar Arquivo JS Específico                       ║
║  [3] 📁 Analisar Diretório Local                             ║
║  [4] 🔗 Analisar URL de Arquivo JS                           ║
║  [5] 📋 Ver Padrões de Secrets                               ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Analisar Website ===")
            url = input("URL do website: ").strip()
            if not url:
                continue
            
            if not url.startswith('http'):
                url = f"https://{url}"
            
            print(f"\nAnalisando {url}...")
            results = analyzer.analyze_url(url)
            
            print(f"\n📁 {len(results.get('js_files', []))} arquivos JS encontrados")
            
            if results.get("secrets"):
                print(f"\n🔑 {len(results['secrets'])} SECRETS ENCONTRADOS:")
                for secret in results["secrets"][:10]:
                    conf_icon = {"high": "🔴", "medium": "🟠", "low": "🟡"}.get(secret["confidence"], "⚪")
                    print(f"  {conf_icon} [{secret['type']}] {secret['value']}")
                    print(f"      File: {secret['file']}")
            
            if results.get("endpoints"):
                print(f"\n🔗 {len(results['endpoints'])} ENDPOINTS ENCONTRADOS:")
                for ep in results["endpoints"][:15]:
                    print(f"  • [{ep['method']}] {ep['url']}")
                    if ep['params']:
                        print(f"      Params: {', '.join(ep['params'])}")
            
            if results.get("interesting"):
                print(f"\n⚠️  {len(results['interesting'])} PONTOS INTERESSANTES:")
                for item in results["interesting"][:10]:
                    print(f"  • {item['pattern']}")
            
            save = input("\nSalvar resultados? (s/n): ").lower()
            if save == 's':
                analyzer.export_results(results, "js_analysis.json")
                print("✅ Salvo em js_analysis.json")
        
        elif escolha == '2':
            print("\n=== Analisar Arquivo Local ===")
            filepath = input("Caminho do arquivo .js: ").strip()
            
            if not os.path.exists(filepath):
                print("Arquivo não encontrado!")
                input("Enter para continuar...")
                continue
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            results = analyzer.analyze_js_content(content, filepath)
            
            if results.get("secrets"):
                print(f"\n🔑 {len(results['secrets'])} secrets encontrados")
                for secret in results["secrets"]:
                    print(f"  • [{secret['type']}] Linha {secret['line']}: {secret['value']}")
            
            if results.get("endpoints"):
                print(f"\n🔗 {len(results['endpoints'])} endpoints encontrados")
                for ep in results["endpoints"]:
                    print(f"  • {ep['url']}")
        
        elif escolha == '3':
            print("\n=== Analisar Diretório ===")
            directory = input("Caminho do diretório: ").strip()
            
            if not os.path.isdir(directory):
                print("Diretório não encontrado!")
                input("Enter para continuar...")
                continue
            
            print(f"\nAnalisando {directory}...")
            results = analyzer.analyze_directory(directory)
            
            print(f"\n📁 {results['files_analyzed']} arquivos analisados")
            print(f"🔑 {len(results['secrets'])} secrets encontrados")
            print(f"🔗 {len(results['endpoints'])} endpoints encontrados")
            print(f"⚠️  {len(results['interesting'])} pontos interessantes")
            
            if results["secrets"]:
                print("\nSecrets por tipo:")
                by_type = {}
                for s in results["secrets"]:
                    by_type[s["type"]] = by_type.get(s["type"], 0) + 1
                for t, c in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
                    print(f"  • {t}: {c}")
        
        elif escolha == '4':
            print("\n=== Analisar URL de JS ===")
            js_url = input("URL do arquivo .js: ").strip()
            if not js_url:
                continue
            
            print(f"\nAnalisando {js_url}...")
            results = analyzer.analyze_js_file(js_url)
            
            if results.get("error"):
                print(f"Erro: {results['error']}")
            else:
                if results.get("secrets"):
                    print(f"\n🔑 {len(results['secrets'])} secrets:")
                    for s in results["secrets"]:
                        print(f"  • [{s['type']}] {s['value']}")
                
                if results.get("endpoints"):
                    print(f"\n🔗 {len(results['endpoints'])} endpoints")
        
        elif escolha == '5':
            print("\n=== Padrões de Secrets ===\n")
            for name, (pattern, confidence) in SecretPatterns.get_all().items():
                conf_icon = {"high": "🔴", "medium": "🟠", "low": "🟡"}.get(confidence, "⚪")
                print(f"  {conf_icon} {name}")
                print(f"      Pattern: {pattern[:60]}...")
                print()
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
