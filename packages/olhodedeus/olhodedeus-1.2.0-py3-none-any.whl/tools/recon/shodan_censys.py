#!/usr/bin/env python3
"""
shodan_censys.py

Integração com Shodan e Censys para busca de dispositivos expostos.
"""
import os
import json
import requests
import socket
from typing import Optional, Dict, List
from datetime import datetime


class ShodanClient:
    """Cliente para API do Shodan."""
    
    BASE_URL = "https://api.shodan.io"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("SHODAN_API_KEY", "")
        self.session = requests.Session()
    
    def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """Faz request à API."""
        if not self.api_key:
            return {"error": "API key não configurada"}
        
        if params is None:
            params = {}
        params["key"] = self.api_key
        
        try:
            resp = self.session.get(f"{self.BASE_URL}{endpoint}", params=params, timeout=30)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def host_info(self, ip: str) -> Dict:
        """Informações sobre um IP."""
        return self._request(f"/shodan/host/{ip}")
    
    def search(self, query: str, page: int = 1) -> Dict:
        """Busca no Shodan."""
        return self._request("/shodan/host/search", {"query": query, "page": page})
    
    def search_count(self, query: str) -> Dict:
        """Conta resultados de busca."""
        return self._request("/shodan/host/count", {"query": query})
    
    def dns_resolve(self, hostnames: str) -> Dict:
        """Resolve hostnames para IPs."""
        return self._request("/dns/resolve", {"hostnames": hostnames})
    
    def dns_reverse(self, ips: str) -> Dict:
        """Reverse DNS lookup."""
        return self._request("/dns/reverse", {"ips": ips})
    
    def exploits_search(self, query: str) -> Dict:
        """Busca exploits relacionados."""
        return self._request("/api-ms/exploits/search", {"query": query})
    
    def api_info(self) -> Dict:
        """Info sobre a API key."""
        return self._request("/api-info")


class CensysClient:
    """Cliente para API do Censys."""
    
    BASE_URL = "https://search.censys.io/api"
    
    def __init__(self, api_id: str = None, api_secret: str = None):
        self.api_id = api_id or os.getenv("CENSYS_API_ID", "")
        self.api_secret = api_secret or os.getenv("CENSYS_API_SECRET", "")
        self.session = requests.Session()
        if self.api_id and self.api_secret:
            self.session.auth = (self.api_id, self.api_secret)
    
    def _request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """Faz request à API."""
        if not self.api_id or not self.api_secret:
            return {"error": "API credentials não configuradas"}
        
        try:
            if method == "GET":
                resp = self.session.get(f"{self.BASE_URL}{endpoint}", timeout=30)
            else:
                resp = self.session.post(f"{self.BASE_URL}{endpoint}", json=data, timeout=30)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def search_hosts(self, query: str, per_page: int = 25) -> Dict:
        """Busca hosts."""
        return self._request("/v2/hosts/search", "POST", {
            "q": query,
            "per_page": per_page
        })
    
    def view_host(self, ip: str) -> Dict:
        """Detalhes de um host."""
        return self._request(f"/v2/hosts/{ip}")
    
    def search_certificates(self, query: str) -> Dict:
        """Busca certificados."""
        return self._request("/v2/certificates/search", "POST", {"q": query})


class DeviceScanner:
    """Scanner de dispositivos usando Shodan + Censys + técnicas locais."""
    
    COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 
                   3306, 3389, 5432, 5900, 6379, 8080, 8443, 27017]
    
    def __init__(self, shodan_key: str = None, censys_id: str = None, censys_secret: str = None):
        self.shodan = ShodanClient(shodan_key)
        self.censys = CensysClient(censys_id, censys_secret)
        self.session = requests.Session()
    
    def scan_ip_basic(self, ip: str) -> Dict:
        """Scan básico de IP (sem API)."""
        results = {
            "ip": ip,
            "timestamp": datetime.now().isoformat(),
            "open_ports": [],
            "services": {}
        }
        
        print(f"🔍 Scanning {ip}...")
        
        for port in self.COMMON_PORTS:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((ip, port))
                if result == 0:
                    results["open_ports"].append(port)
                    print(f"  ✅ Porta {port} aberta")
                sock.close()
            except Exception:
                pass
        
        # Reverse DNS
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            results["hostname"] = hostname
        except Exception:
            results["hostname"] = None
        
        return results
    
    def scan_ip_shodan(self, ip: str) -> Dict:
        """Scan usando Shodan API."""
        print(f"🔍 Shodan: {ip}")
        
        result = self.shodan.host_info(ip)
        
        if "error" not in result:
            print(f"  ✅ Encontrado!")
            print(f"     Org: {result.get('org', 'N/A')}")
            print(f"     Portas: {result.get('ports', [])}")
            print(f"     Vulns: {len(result.get('vulns', []))}")
        else:
            print(f"  ❌ {result.get('error')}")
        
        return result
    
    def search_shodan(self, query: str) -> Dict:
        """Busca no Shodan."""
        print(f"🔍 Shodan Search: {query}")
        
        result = self.shodan.search(query)
        
        if "error" not in result:
            print(f"  ✅ {result.get('total', 0)} resultados")
        else:
            print(f"  ❌ {result.get('error')}")
        
        return result
    
    def scan_domain(self, domain: str) -> Dict:
        """Scan completo de um domínio."""
        results = {
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
            "ips": [],
            "hosts": []
        }
        
        print(f"\n🌐 Scanning domínio: {domain}\n")
        
        # Resolver DNS
        try:
            ip = socket.gethostbyname(domain)
            results["ips"].append(ip)
            print(f"  📍 IP: {ip}")
            
            # Scan Shodan
            if self.shodan.api_key:
                shodan_result = self.scan_ip_shodan(ip)
                if "error" not in shodan_result:
                    results["hosts"].append(shodan_result)
        except Exception as e:
            print(f"  ❌ Erro DNS: {e}")
        
        return results
    
    def search_vulnerabilities(self, query: str) -> Dict:
        """Busca vulnerabilidades/exploits."""
        print(f"🔍 Buscando exploits: {query}")
        return self.shodan.exploits_search(query)
    
    def get_ip_geolocation(self, ip: str) -> Dict:
        """Geolocalização de IP (gratuito)."""
        try:
            resp = self.session.get(f"http://ip-api.com/json/{ip}", timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            return {"error": str(e)}
        return {}


def interactive_menu():
    """Menu interativo."""
    # Carregar configurações
    config_path = "config/shodan_censys.json"
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    scanner = DeviceScanner(
        shodan_key=config.get("shodan_api_key"),
        censys_id=config.get("censys_api_id"),
        censys_secret=config.get("censys_api_secret")
    )
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        shodan_ok = "✅" if scanner.shodan.api_key else "❌"
        censys_ok = "✅" if scanner.censys.api_id else "❌"
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║              🔎 SHODAN / CENSYS SCANNER                      ║
╠══════════════════════════════════════════════════════════════╣
║  Shodan API: {shodan_ok}  |  Censys API: {censys_ok}                        
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ──── 🔍 BUSCA ────                                          ║
║  [1] 🖥️  Scan IP (Shodan + básico)                            ║
║  [2] 🌐 Scan Domínio                                         ║
║  [3] 🔎 Busca Shodan (query)                                 ║
║  [4] ⚠️  Buscar Vulnerabilidades/Exploits                     ║
║                                                              ║
║  ──── 📍 GEOLOCALIZAÇÃO ────                                 ║
║  [5] 📍 Geolocalização de IP                                 ║
║  [6] 🔄 DNS Resolve/Reverse                                  ║
║                                                              ║
║  ──── ⚙️ CONFIGURAÇÃO ────                                    ║
║  [7] ⚙️  Configurar API Keys                                  ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            ip = input("\n🖥️ IP para scan: ").strip()
            if ip:
                # Scan básico
                basic = scanner.scan_ip_basic(ip)
                print(f"\n📊 Portas abertas: {basic['open_ports']}")
                
                # Shodan
                if scanner.shodan.api_key:
                    shodan = scanner.scan_ip_shodan(ip)
                    if "error" not in shodan:
                        print(f"\n📊 SHODAN:")
                        print(f"   Organização: {shodan.get('org', 'N/A')}")
                        print(f"   ASN: {shodan.get('asn', 'N/A')}")
                        print(f"   ISP: {shodan.get('isp', 'N/A')}")
                        print(f"   Portas: {shodan.get('ports', [])}")
                        vulns = shodan.get('vulns', [])
                        if vulns:
                            print(f"   ⚠️ Vulnerabilidades: {vulns[:5]}")
            input("\nPressione Enter...")
        
        elif choice == '2':
            domain = input("\n🌐 Domínio: ").strip()
            if domain:
                scanner.scan_domain(domain)
            input("\nPressione Enter...")
        
        elif choice == '3':
            print("\n📝 Exemplos de queries:")
            print("   apache country:br")
            print("   port:22 country:us")
            print("   webcam has_screenshot:true")
            print("   mongodb -authentication")
            query = input("\n🔎 Query Shodan: ").strip()
            if query:
                result = scanner.search_shodan(query)
                if "matches" in result:
                    print(f"\n📊 {result['total']} resultados:\n")
                    for m in result['matches'][:10]:
                        print(f"  {m.get('ip_str')}:{m.get('port')} - {m.get('org', 'N/A')}")
            input("\nPressione Enter...")
        
        elif choice == '4':
            query = input("\n⚠️ CVE ou termo de busca: ").strip()
            if query:
                result = scanner.search_vulnerabilities(query)
                if "matches" in result:
                    print(f"\n⚠️ Exploits encontrados:\n")
                    for e in result.get('matches', [])[:10]:
                        print(f"  • {e.get('description', 'N/A')[:60]}...")
            input("\nPressione Enter...")
        
        elif choice == '5':
            ip = input("\n📍 IP: ").strip()
            if ip:
                geo = scanner.get_ip_geolocation(ip)
                if "error" not in geo:
                    print(f"\n📍 GEOLOCALIZAÇÃO:")
                    print(f"   País: {geo.get('country')} ({geo.get('countryCode')})")
                    print(f"   Região: {geo.get('regionName')}")
                    print(f"   Cidade: {geo.get('city')}")
                    print(f"   ISP: {geo.get('isp')}")
                    print(f"   Org: {geo.get('org')}")
                    print(f"   Lat/Lon: {geo.get('lat')}, {geo.get('lon')}")
            input("\nPressione Enter...")
        
        elif choice == '6':
            host = input("\nHostname ou IP: ").strip()
            if host:
                try:
                    if host.replace('.', '').isdigit():
                        hostname = socket.gethostbyaddr(host)[0]
                        print(f"\n🔄 {host} -> {hostname}")
                    else:
                        ip = socket.gethostbyname(host)
                        print(f"\n🔄 {host} -> {ip}")
                except Exception as e:
                    print(f"❌ Erro: {e}")
            input("\nPressione Enter...")
        
        elif choice == '7':
            print("\n⚙️ CONFIGURAÇÃO DE APIs\n")
            print("Shodan: https://account.shodan.io (API Key)")
            print("Censys: https://search.censys.io/account/api (ID + Secret)\n")
            
            shodan_key = input(f"Shodan API Key [{config.get('shodan_api_key', '')[:10]}...]: ").strip()
            if shodan_key:
                config['shodan_api_key'] = shodan_key
            
            censys_id = input(f"Censys API ID [{config.get('censys_api_id', '')}]: ").strip()
            if censys_id:
                config['censys_api_id'] = censys_id
            
            censys_secret = input("Censys API Secret: ").strip()
            if censys_secret:
                config['censys_api_secret'] = censys_secret
            
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print("✅ Configuração salva!")
            
            # Recarregar scanner
            scanner = DeviceScanner(
                shodan_key=config.get("shodan_api_key"),
                censys_id=config.get("censys_api_id"),
                censys_secret=config.get("censys_api_secret")
            )
            input("\nPressione Enter...")
        
        elif choice == '0':
            break


if __name__ == '__main__':
    interactive_menu()
