#!/usr/bin/env python3
"""
Subdomain Enumeration - Olho de Deus
Enumeração completa de subdomínios com múltiplas técnicas
"""

import socket
import ssl
import json
import re
import sys
import os
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Adicionar path para imports locais
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from tools.utilities.progress_bar import ProgressBar, Spinner
except ImportError:
    ProgressBar = None
    Spinner = None


@dataclass
class SubdomainInfo:
    """Informações de um subdomínio"""
    subdomain: str
    ip_addresses: List[str] = field(default_factory=list)
    cname: str = ""
    source: str = ""
    http_status: int = 0
    https_status: int = 0
    title: str = ""
    server: str = ""
    is_alive: bool = False


@dataclass
class EnumerationResult:
    """Resultado da enumeração"""
    domain: str
    total_found: int = 0
    alive_count: int = 0
    subdomains: List[SubdomainInfo] = field(default_factory=list)
    sources_used: List[str] = field(default_factory=list)
    duration: float = 0.0


class SubdomainEnumerator:
    """Enumerador de subdomínios multi-técnica"""
    
    # Wordlist básica de subdomínios
    COMMON_SUBDOMAINS = [
        "www", "mail", "ftp", "localhost", "webmail", "smtp", "pop", "ns1", "ns2",
        "ns3", "ns4", "admin", "administrator", "api", "app", "dev", "staging",
        "test", "beta", "demo", "cdn", "static", "assets", "img", "images",
        "media", "files", "download", "downloads", "upload", "uploads", "blog",
        "news", "forum", "shop", "store", "portal", "secure", "ssl", "vpn",
        "remote", "m", "mobile", "wap", "imap", "mx", "mx1", "mx2", "email",
        "gateway", "proxy", "firewall", "dns", "ns", "web", "www2", "www3",
        "cloud", "backup", "db", "database", "sql", "mysql", "postgres", "mongo",
        "redis", "elastic", "search", "git", "gitlab", "github", "jenkins",
        "ci", "cd", "deploy", "prod", "production", "uat", "qa",
        "internal", "intranet", "extranet", "corp", "corporate", "hr", "crm",
        "erp", "docs", "doc", "wiki", "help", "support", "helpdesk", "status",
        "monitor", "grafana", "prometheus", "kibana", "logs", "analytics",
        "dashboard", "panel", "cpanel", "plesk", "whm", "webmin", "auth",
        "login", "sso", "oauth", "account", "accounts", "user", "users",
        "profile", "member", "members", "client", "clients", "customer",
        "partner", "partners", "vendor", "vendors", "billing", "payment",
        "checkout", "cart", "order", "orders", "tracking", "autodiscover",
        "autoconfig", "exchange", "outlook", "calendar", "contacts", "owa",
        "smtp", "pop3", "imap", "mail2", "webmail2", "relay", "mailhost",
        "mx01", "mx02", "mail01", "mail02", "ns01", "ns02", "dns1", "dns2",
        "vpn1", "vpn2", "fw", "fw1", "firewall1", "router", "switch",
        "server", "server1", "server2", "host", "host1", "node", "node1",
        "cluster", "k8s", "kubernetes", "docker", "container", "registry",
        "repo", "repository", "artifactory", "nexus", "sonar", "jenkins",
        "bamboo", "travis", "circleci", "actions", "workflow", "build",
    ]
    
    def __init__(self, timeout: float = 5.0, threads: int = 50):
        self.timeout = timeout
        self.threads = threads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.found_subdomains: Set[str] = set()
    
    def enumerate(self, domain: str, methods: List[str] = None) -> EnumerationResult:
        """Enumera subdomínios usando múltiplos métodos"""
        
        start_time = datetime.now()
        
        print(f"\n🔍 Enumeração de Subdomínios: {domain}")
        print("=" * 50)
        
        result = EnumerationResult(domain=domain)
        
        # Métodos padrão
        if methods is None:
            methods = ['dns_bruteforce', 'crtsh', 'hackertarget', 'threatcrowd']
        
        # Executar métodos
        for method in methods:
            print(f"\n📡 Método: {method}")
            
            if method == 'dns_bruteforce':
                subs = self._dns_bruteforce(domain)
            elif method == 'crtsh':
                subs = self._crtsh_search(domain)
            elif method == 'hackertarget':
                subs = self._hackertarget_search(domain)
            elif method == 'threatcrowd':
                subs = self._threatcrowd_search(domain)
            elif method == 'certspotter':
                subs = self._certspotter_search(domain)
            elif method == 'bufferover':
                subs = self._bufferover_search(domain)
            else:
                subs = []
            
            for sub in subs:
                self.found_subdomains.add(sub)
            
            result.sources_used.append(method)
            print(f"   ✅ Encontrados: {len(subs)}")
        
        # Verificar quais estão vivos
        print(f"\n🔍 Verificando {len(self.found_subdomains)} subdomínios...")
        result.subdomains = self._check_alive(list(self.found_subdomains))
        
        result.total_found = len(result.subdomains)
        result.alive_count = len([s for s in result.subdomains if s.is_alive])
        result.duration = (datetime.now() - start_time).total_seconds()
        
        # Resumo
        print(f"\n" + "=" * 50)
        print(f"📊 Resumo:")
        print(f"   Total encontrados: {result.total_found}")
        print(f"   Ativos: {result.alive_count}")
        print(f"   Tempo: {result.duration:.1f}s")
        
        return result
    
    def _dns_bruteforce(self, domain: str, wordlist: List[str] = None) -> List[str]:
        """Bruteforce via DNS"""
        if wordlist is None:
            wordlist = self.COMMON_SUBDOMAINS
        
        found = []
        
        # Criar barra de progresso (usa estilo configurado pelo usuário)
        pbar = None
        if ProgressBar:
            pbar = ProgressBar(
                len(wordlist),
                "   Bruteforce",
                show_percentage=True,
                show_speed=True
            )
        
        def check_subdomain(sub):
            fqdn = f"{sub}.{domain}"
            try:
                socket.setdefaulttimeout(self.timeout)
                socket.gethostbyname(fqdn)
                return fqdn
            except:
                return None
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(check_subdomain, sub): sub for sub in wordlist}
            
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                if result:
                    found.append(result)
                
                completed += 1
                if pbar:
                    pbar.set(completed)
        
        if pbar:
            pbar.finish()
        
        return found
    
    def _crtsh_search(self, domain: str) -> List[str]:
        """Busca via crt.sh (Certificate Transparency)"""
        subdomains = []
        
        # Spinner para busca
        spinner = None
        if Spinner:
            spinner = Spinner("   Buscando em crt.sh...", "dots")
            spinner.start()
        
        try:
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            resp = self.session.get(url, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                for entry in data:
                    name = entry.get('name_value', '')
                    for sub in name.split('\n'):
                        sub = sub.strip().lower()
                        if sub.endswith(domain) and '*' not in sub:
                            subdomains.append(sub)
        except:
            pass
        finally:
            if spinner:
                spinner.stop()
        
        return list(set(subdomains))
    
    def _hackertarget_search(self, domain: str) -> List[str]:
        """Busca via HackerTarget"""
        subdomains = []
        
        try:
            url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code == 200 and 'error' not in resp.text.lower():
                for line in resp.text.split('\n'):
                    if ',' in line:
                        sub = line.split(',')[0].strip()
                        if sub.endswith(domain):
                            subdomains.append(sub)
        except:
            pass
        
        return list(set(subdomains))
    
    def _threatcrowd_search(self, domain: str) -> List[str]:
        """Busca via ThreatCrowd"""
        subdomains = []
        
        try:
            url = f"https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={domain}"
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                subs = data.get('subdomains', [])
                for sub in subs:
                    if sub.endswith(domain):
                        subdomains.append(sub)
        except:
            pass
        
        return list(set(subdomains))
    
    def _certspotter_search(self, domain: str) -> List[str]:
        """Busca via CertSpotter"""
        subdomains = []
        
        try:
            url = f"https://api.certspotter.com/v1/issuances?domain={domain}&include_subdomains=true&expand=dns_names"
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                for cert in data:
                    for name in cert.get('dns_names', []):
                        if name.endswith(domain) and '*' not in name:
                            subdomains.append(name)
        except:
            pass
        
        return list(set(subdomains))
    
    def _bufferover_search(self, domain: str) -> List[str]:
        """Busca via BufferOver.run"""
        subdomains = []
        
        try:
            url = f"https://dns.bufferover.run/dns?q=.{domain}"
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                records = data.get('FDNS_A', []) + data.get('RDNS', [])
                for record in records:
                    if ',' in record:
                        sub = record.split(',')[1].strip()
                        if sub.endswith(domain):
                            subdomains.append(sub)
        except:
            pass
        
        return list(set(subdomains))
    
    def _check_alive(self, subdomains: List[str]) -> List[SubdomainInfo]:
        """Verifica quais subdomínios estão ativos"""
        results = []
        
        def check_one(subdomain: str) -> SubdomainInfo:
            info = SubdomainInfo(subdomain=subdomain)
            
            # Resolver DNS
            try:
                ips = socket.gethostbyname_ex(subdomain)[2]
                info.ip_addresses = ips
            except:
                pass
            
            # Verificar HTTP/HTTPS
            for protocol in ['https', 'http']:
                try:
                    url = f"{protocol}://{subdomain}"
                    resp = self.session.get(url, timeout=5, verify=False, allow_redirects=True)
                    
                    if protocol == 'https':
                        info.https_status = resp.status_code
                    else:
                        info.http_status = resp.status_code
                    
                    info.is_alive = True
                    info.server = resp.headers.get('Server', '')
                    
                    # Extrair título
                    title_match = re.search(r'<title>([^<]+)</title>', resp.text, re.IGNORECASE)
                    if title_match:
                        info.title = title_match.group(1).strip()[:50]
                    
                    break
                except:
                    pass
            
            return info
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(check_one, sub): sub for sub in subdomains}
            
            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                results.append(result)
                
                if result.is_alive:
                    status = result.https_status or result.http_status
                    ip = result.ip_addresses[0] if result.ip_addresses else 'N/A'
                    print(f"   ✅ {result.subdomain} ({ip}) [{status}]")
                
                if (i + 1) % 20 == 0:
                    print(f"   ... verificados {i+1}/{len(subdomains)}")
        
        return sorted(results, key=lambda x: (not x.is_alive, x.subdomain))
    
    def export_results(self, result: EnumerationResult, filepath: str):
        """Exporta resultados para JSON"""
        data = {
            'domain': result.domain,
            'total_found': result.total_found,
            'alive_count': result.alive_count,
            'sources': result.sources_used,
            'duration': result.duration,
            'subdomains': [
                {
                    'subdomain': s.subdomain,
                    'ips': s.ip_addresses,
                    'alive': s.is_alive,
                    'http': s.http_status,
                    'https': s.https_status,
                    'title': s.title,
                    'server': s.server
                }
                for s in result.subdomains
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n📄 Resultados salvos: {filepath}")
    
    def export_list(self, result: EnumerationResult, filepath: str, alive_only: bool = True):
        """Exporta lista simples de subdomínios"""
        with open(filepath, 'w') as f:
            for sub in result.subdomains:
                if not alive_only or sub.is_alive:
                    f.write(f"{sub.subdomain}\n")
        
        print(f"📄 Lista salva: {filepath}")


# Suprimir warnings de SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    """Função principal"""
    import sys
    
    print("\n" + "=" * 50)
    print("🔍 Subdomain Enumeration - Olho de Deus")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        domain = input("\n🌐 Domínio alvo: ").strip()
    else:
        domain = sys.argv[1]
    
    # Remover protocolo se presente
    domain = domain.replace('https://', '').replace('http://', '').split('/')[0]
    
    enumerator = SubdomainEnumerator()
    result = enumerator.enumerate(domain)
    
    # Listar ativos
    alive = [s for s in result.subdomains if s.is_alive]
    if alive:
        print(f"\n📋 Subdomínios Ativos ({len(alive)}):")
        for sub in alive[:20]:
            print(f"   • {sub.subdomain}")
        if len(alive) > 20:
            print(f"   ... e mais {len(alive) - 20}")
    
    print("\n✅ Enumeração concluída!")


if __name__ == "__main__":
    main()
