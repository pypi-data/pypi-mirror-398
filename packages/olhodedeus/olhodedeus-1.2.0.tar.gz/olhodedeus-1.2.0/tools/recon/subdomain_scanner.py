#!/usr/bin/env python3
"""
subdomain_scanner.py

Scanner de subdomínios com múltiplas técnicas.
"""
import os
import re
import json
import socket
import requests
import time
import dns.resolver
from typing import Optional, Dict, List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed


class SubdomainScanner:
    """Scanner de subdomínios multi-técnica."""
    
    # Wordlist básica de subdomínios comuns
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
        "ci", "cd", "deploy", "staging", "prod", "production", "uat", "qa",
        "internal", "intranet", "extranet", "corp", "corporate", "hr", "crm",
        "erp", "sap", "oracle", "salesforce", "zendesk", "jira", "confluence",
        "docs", "doc", "wiki", "help", "support", "helpdesk", "ticket", "status",
        "monitor", "grafana", "prometheus", "kibana", "logs", "analytics",
        "tracking", "stats", "metrics", "dashboard", "panel", "cpanel", "plesk",
        "whm", "webmin", "phpmyadmin", "adminer", "manager", "console", "auth",
        "login", "sso", "oauth", "iam", "identity", "account", "accounts", "user",
        "users", "profile", "my", "member", "members", "client", "clients",
        "customer", "customers", "partner", "partners", "vendor", "vendors"
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 3
        self.resolver.lifetime = 3
    
    def dns_bruteforce(self, domain: str, wordlist: List[str] = None, threads: int = 20) -> List[Dict]:
        """Bruteforce de subdomínios via DNS."""
        if wordlist is None:
            wordlist = self.COMMON_SUBDOMAINS
        
        found = []
        total = len(wordlist)
        
        print(f"🔍 DNS Bruteforce: {domain} ({total} subdomínios)")
        
        def check_subdomain(sub):
            fqdn = f"{sub}.{domain}"
            try:
                answers = self.resolver.resolve(fqdn, 'A')
                ips = [str(rdata) for rdata in answers]
                return {"subdomain": fqdn, "ips": ips, "method": "dns_bruteforce"}
            except Exception:
                return None
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(check_subdomain, sub): sub for sub in wordlist}
            
            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                if result:
                    found.append(result)
                    print(f"  ✅ {result['subdomain']} -> {', '.join(result['ips'])}")
                
                if (i + 1) % 50 == 0:
                    print(f"\r  Progresso: {i+1}/{total}", end="", flush=True)
        
        print(f"\n✅ Encontrados: {len(found)} subdomínios")
        return found
    
    def crtsh_search(self, domain: str) -> List[Dict]:
        """Busca subdomínios via crt.sh (Certificate Transparency)."""
        print(f"🔍 crt.sh: {domain}")
        
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        found = []
        
        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                subdomains = set()
                
                for entry in data:
                    name = entry.get("name_value", "")
                    for sub in name.split('\n'):
                        sub = sub.strip().lower()
                        if sub.endswith(domain) and '*' not in sub:
                            subdomains.add(sub)
                
                for sub in subdomains:
                    found.append({"subdomain": sub, "method": "crt.sh"})
                
                print(f"  ✅ {len(found)} subdomínios via Certificate Transparency")
        except Exception as e:
            print(f"  ❌ Erro: {e}")
        
        return found
    
    def securitytrails_search(self, domain: str, api_key: str = None) -> List[Dict]:
        """Busca via SecurityTrails API."""
        if not api_key:
            print("  ⚠️ SecurityTrails requer API key")
            return []
        
        print(f"🔍 SecurityTrails: {domain}")
        
        url = f"https://api.securitytrails.com/v1/domain/{domain}/subdomains"
        headers = {"APIKEY": api_key}
        found = []
        
        try:
            resp = self.session.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                for sub in data.get("subdomains", []):
                    found.append({
                        "subdomain": f"{sub}.{domain}",
                        "method": "securitytrails"
                    })
                print(f"  ✅ {len(found)} subdomínios")
        except Exception as e:
            print(f"  ❌ Erro: {e}")
        
        return found
    
    def hackertarget_search(self, domain: str) -> List[Dict]:
        """Busca via HackerTarget (gratuito)."""
        print(f"🔍 HackerTarget: {domain}")
        
        url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
        found = []
        
        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 200 and "error" not in resp.text.lower():
                for line in resp.text.strip().split('\n'):
                    if ',' in line:
                        subdomain, ip = line.split(',', 1)
                        found.append({
                            "subdomain": subdomain.strip(),
                            "ip": ip.strip(),
                            "method": "hackertarget"
                        })
                print(f"  ✅ {len(found)} subdomínios")
        except Exception as e:
            print(f"  ❌ Erro: {e}")
        
        return found
    
    def rapiddns_search(self, domain: str) -> List[Dict]:
        """Busca via RapidDNS."""
        print(f"🔍 RapidDNS: {domain}")
        
        url = f"https://rapiddns.io/subdomain/{domain}?full=1"
        found = []
        
        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 200:
                pattern = r'<td>([a-zA-Z0-9\-\.]+\.' + re.escape(domain) + r')</td>'
                matches = re.findall(pattern, resp.text)
                
                for sub in set(matches):
                    found.append({"subdomain": sub, "method": "rapiddns"})
                
                print(f"  ✅ {len(found)} subdomínios")
        except Exception as e:
            print(f"  ❌ Erro: {e}")
        
        return found
    
    def check_takeover(self, subdomain: str) -> Optional[Dict]:
        """Verifica possibilidade de subdomain takeover."""
        takeover_signatures = {
            "github": "There isn't a GitHub Pages site here",
            "heroku": "No such app",
            "aws_s3": "NoSuchBucket",
            "shopify": "Sorry, this shop is currently unavailable",
            "tumblr": "There's nothing here",
            "wordpress": "Do you want to register",
            "azure": "404 Web Site not found",
            "bitbucket": "Repository not found",
            "ghost": "The thing you were looking for is no longer here",
            "surge": "project not found",
            "netlify": "Not Found - Request ID",
        }
        
        try:
            # Verificar CNAME
            try:
                answers = self.resolver.resolve(subdomain, 'CNAME')
                cname = str(answers[0].target).rstrip('.')
            except Exception:
                cname = None
            
            # Verificar resposta HTTP
            for proto in ['https', 'http']:
                try:
                    resp = self.session.get(f"{proto}://{subdomain}", timeout=10, allow_redirects=True)
                    
                    for service, signature in takeover_signatures.items():
                        if signature.lower() in resp.text.lower():
                            return {
                                "subdomain": subdomain,
                                "vulnerable": True,
                                "service": service,
                                "cname": cname
                            }
                    break
                except Exception:
                    continue
        except Exception:
            pass
        
        return None
    
    def full_scan(self, domain: str, bruteforce: bool = True) -> Dict:
        """Scan completo usando todas as técnicas."""
        all_subdomains = {}
        
        print(f"\n{'='*60}")
        print(f"🌐 SCAN COMPLETO: {domain}")
        print(f"{'='*60}\n")
        
        # 1. crt.sh
        for sub in self.crtsh_search(domain):
            all_subdomains[sub['subdomain']] = sub
        
        time.sleep(1)
        
        # 2. HackerTarget
        for sub in self.hackertarget_search(domain):
            if sub['subdomain'] not in all_subdomains:
                all_subdomains[sub['subdomain']] = sub
        
        time.sleep(1)
        
        # 3. RapidDNS
        for sub in self.rapiddns_search(domain):
            if sub['subdomain'] not in all_subdomains:
                all_subdomains[sub['subdomain']] = sub
        
        # 4. DNS Bruteforce (opcional)
        if bruteforce:
            time.sleep(1)
            for sub in self.dns_bruteforce(domain):
                if sub['subdomain'] not in all_subdomains:
                    all_subdomains[sub['subdomain']] = sub
        
        results = {
            "domain": domain,
            "total_found": len(all_subdomains),
            "subdomains": list(all_subdomains.values())
        }
        
        print(f"\n{'='*60}")
        print(f"📊 TOTAL: {len(all_subdomains)} subdomínios únicos")
        print(f"{'='*60}")
        
        return results


def interactive_menu():
    """Menu interativo."""
    scanner = SubdomainScanner()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║              🌐 SUBDOMAIN SCANNER                            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔍 Scan COMPLETO (todas as técnicas)                    ║
║  [2] 📜 crt.sh (Certificate Transparency)                    ║
║  [3] 🎯 HackerTarget (gratuito)                              ║
║  [4] ⚡ RapidDNS                                             ║
║  [5] 💪 DNS Bruteforce                                       ║
║  [6] ⚠️  Verificar Subdomain Takeover                         ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            domain = input("\n🌐 Domínio: ").strip()
            if domain:
                results = scanner.full_scan(domain)
                
                save = input("\nSalvar resultados? (s/n): ").strip().lower()
                if save == 's':
                    os.makedirs("data/recon", exist_ok=True)
                    filename = f"data/recon/{domain}_subdomains.json"
                    with open(filename, 'w') as f:
                        json.dump(results, f, indent=2)
                    print(f"✅ Salvo: {filename}")
            input("\nPressione Enter...")
        
        elif choice == '2':
            domain = input("\n🌐 Domínio: ").strip()
            if domain:
                scanner.crtsh_search(domain)
            input("\nPressione Enter...")
        
        elif choice == '3':
            domain = input("\n🌐 Domínio: ").strip()
            if domain:
                scanner.hackertarget_search(domain)
            input("\nPressione Enter...")
        
        elif choice == '4':
            domain = input("\n🌐 Domínio: ").strip()
            if domain:
                scanner.rapiddns_search(domain)
            input("\nPressione Enter...")
        
        elif choice == '5':
            domain = input("\n🌐 Domínio: ").strip()
            if domain:
                scanner.dns_bruteforce(domain)
            input("\nPressione Enter...")
        
        elif choice == '6':
            subdomain = input("\n🌐 Subdomínio para verificar: ").strip()
            if subdomain:
                result = scanner.check_takeover(subdomain)
                if result and result.get("vulnerable"):
                    print(f"\n⚠️ VULNERÁVEL! Serviço: {result['service']}")
                else:
                    print("\n✅ Não parece vulnerável a takeover")
            input("\nPressione Enter...")
        
        elif choice == '0':
            break


if __name__ == '__main__':
    interactive_menu()
