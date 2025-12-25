#!/usr/bin/env python3
"""
Domain Intelligence - Olho de Deus
Coleta de inteligência sobre domínios
"""

import socket
import ssl
import json
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DomainInfo:
    """Informações de um domínio"""
    domain: str
    registrar: str = ""
    creation_date: str = ""
    expiration_date: str = ""
    updated_date: str = ""
    name_servers: List[str] = field(default_factory=list)
    status: List[str] = field(default_factory=list)
    registrant: Dict[str, str] = field(default_factory=dict)


@dataclass
class DNSInfo:
    """Informações DNS"""
    a_records: List[str] = field(default_factory=list)
    aaaa_records: List[str] = field(default_factory=list)
    mx_records: List[str] = field(default_factory=list)
    ns_records: List[str] = field(default_factory=list)
    txt_records: List[str] = field(default_factory=list)
    cname_records: List[str] = field(default_factory=list)
    soa_record: str = ""


@dataclass
class WebInfo:
    """Informações web"""
    ip_address: str = ""
    server: str = ""
    powered_by: str = ""
    technologies: List[str] = field(default_factory=list)
    cms: str = ""
    has_ssl: bool = False
    ssl_issuer: str = ""
    ssl_expiry: str = ""
    title: str = ""
    redirects_to: str = ""


@dataclass
class DomainIntelResult:
    """Resultado completo de inteligência"""
    domain: str
    domain_info: Optional[DomainInfo] = None
    dns_info: Optional[DNSInfo] = None
    web_info: Optional[WebInfo] = None
    subdomains: List[str] = field(default_factory=list)
    related_domains: List[str] = field(default_factory=list)
    ip_history: List[Dict] = field(default_factory=list)
    reputation: Dict[str, Any] = field(default_factory=dict)
    security_headers: Dict[str, str] = field(default_factory=dict)


class DomainIntelligence:
    """Coleta de inteligência sobre domínios"""
    
    # Tecnologias conhecidas
    TECH_PATTERNS = {
        'WordPress': [r'wp-content', r'wp-includes', r'wordpress'],
        'Joomla': [r'joomla', r'/administrator/'],
        'Drupal': [r'drupal', r'/sites/default/'],
        'Magento': [r'magento', r'mage/'],
        'Shopify': [r'cdn\.shopify\.com', r'shopify'],
        'Wix': [r'wix\.com', r'wixsite'],
        'Squarespace': [r'squarespace', r'sqsp'],
        'React': [r'react', r'__NEXT_DATA__'],
        'Angular': [r'ng-version', r'angular'],
        'Vue.js': [r'vue', r'__vue__'],
        'jQuery': [r'jquery'],
        'Bootstrap': [r'bootstrap'],
        'Cloudflare': [r'cloudflare'],
        'AWS': [r'amazonaws\.com', r'aws'],
        'Google Cloud': [r'googlecloud', r'googleapis'],
        'Azure': [r'azure', r'microsoft'],
    }
    
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def analyze(self, domain: str) -> DomainIntelResult:
        """Análise completa de um domínio"""
        
        # Limpar domínio
        domain = domain.replace('https://', '').replace('http://', '').split('/')[0]
        
        print(f"\n🔍 Domain Intelligence: {domain}")
        print("=" * 50)
        
        result = DomainIntelResult(domain=domain)
        
        # DNS Info
        print("\n📡 Coletando informações DNS...")
        result.dns_info = self._get_dns_info(domain)
        
        # Web Info
        print("🌐 Analisando presença web...")
        result.web_info = self._get_web_info(domain)
        
        # WHOIS
        print("📋 Consultando WHOIS...")
        result.domain_info = self._get_whois_info(domain)
        
        # Security Headers
        print("🔒 Verificando headers de segurança...")
        result.security_headers = self._get_security_headers(domain)
        
        # Subdomínios (básico)
        print("🔍 Buscando subdomínios...")
        result.subdomains = self._find_subdomains(domain)
        
        # Reputação
        print("⚠️ Verificando reputação...")
        result.reputation = self._check_reputation(domain)
        
        # Imprimir resultados
        self._print_results(result)
        
        return result
    
    def _get_dns_info(self, domain: str) -> DNSInfo:
        """Coleta informações DNS"""
        dns = DNSInfo()
        
        # A records
        try:
            ips = socket.gethostbyname_ex(domain)[2]
            dns.a_records = ips
        except:
            pass
        
        # Usando API pública para outros registros
        try:
            resp = self.session.get(
                f"https://dns.google/resolve?name={domain}&type=ANY",
                timeout=self.timeout
            )
            if resp.status_code == 200:
                data = resp.json()
                for answer in data.get('Answer', []):
                    rtype = answer.get('type')
                    rdata = answer.get('data', '')
                    
                    if rtype == 1:  # A
                        if rdata not in dns.a_records:
                            dns.a_records.append(rdata)
                    elif rtype == 28:  # AAAA
                        dns.aaaa_records.append(rdata)
                    elif rtype == 15:  # MX
                        dns.mx_records.append(rdata)
                    elif rtype == 2:  # NS
                        dns.ns_records.append(rdata)
                    elif rtype == 16:  # TXT
                        dns.txt_records.append(rdata)
                    elif rtype == 5:  # CNAME
                        dns.cname_records.append(rdata)
        except:
            pass
        
        return dns
    
    def _get_web_info(self, domain: str) -> WebInfo:
        """Coleta informações web"""
        web = WebInfo()
        
        # IP
        try:
            web.ip_address = socket.gethostbyname(domain)
        except:
            pass
        
        # HTTP(S) request
        for protocol in ['https', 'http']:
            try:
                url = f"{protocol}://{domain}"
                resp = self.session.get(url, timeout=self.timeout, verify=False, allow_redirects=True)
                
                web.has_ssl = protocol == 'https'
                web.server = resp.headers.get('Server', '')
                web.powered_by = resp.headers.get('X-Powered-By', '')
                
                # Título
                title_match = re.search(r'<title>([^<]+)</title>', resp.text, re.IGNORECASE)
                if title_match:
                    web.title = title_match.group(1).strip()[:100]
                
                # Redirect
                if resp.history:
                    web.redirects_to = resp.url
                
                # Detectar tecnologias
                web.technologies = self._detect_technologies(resp.text, str(resp.headers))
                
                # Detectar CMS
                web.cms = self._detect_cms(resp.text)
                
                break
            except:
                continue
        
        # SSL Info
        if web.has_ssl:
            try:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                with socket.create_connection((domain, 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert()
                        if cert:
                            issuer = dict(x[0] for x in cert.get('issuer', []))
                            web.ssl_issuer = issuer.get('organizationName', '')
                            web.ssl_expiry = cert.get('notAfter', '')
            except:
                pass
        
        return web
    
    def _detect_technologies(self, html: str, headers: str) -> List[str]:
        """Detecta tecnologias usadas"""
        found = []
        combined = html + headers
        
        for tech, patterns in self.TECH_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    if tech not in found:
                        found.append(tech)
                    break
        
        return found
    
    def _detect_cms(self, html: str) -> str:
        """Detecta CMS"""
        cms_patterns = {
            'WordPress': r'wp-content|wordpress',
            'Joomla': r'joomla|/administrator/',
            'Drupal': r'drupal|/sites/default/',
            'Magento': r'magento|mage/',
            'Shopify': r'shopify',
            'Wix': r'wix\.com',
            'Squarespace': r'squarespace',
        }
        
        for cms, pattern in cms_patterns.items():
            if re.search(pattern, html, re.IGNORECASE):
                return cms
        
        return ""
    
    def _get_whois_info(self, domain: str) -> DomainInfo:
        """Consulta WHOIS via API"""
        info = DomainInfo(domain=domain)
        
        # Tentar API gratuita
        try:
            resp = self.session.get(
                f"https://api.hackertarget.com/whois/?q={domain}",
                timeout=self.timeout
            )
            
            if resp.status_code == 200 and 'error' not in resp.text.lower():
                text = resp.text
                
                # Parse básico
                patterns = {
                    'registrar': r'Registrar:\s*(.+)',
                    'creation_date': r'Creation Date:\s*(.+)',
                    'expiration_date': r'(?:Expir(?:y|ation) Date|Registry Expiry Date):\s*(.+)',
                    'updated_date': r'Updated Date:\s*(.+)',
                }
                
                for field, pattern in patterns.items():
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        setattr(info, field, match.group(1).strip())
                
                # Name servers
                ns_matches = re.findall(r'Name Server:\s*(.+)', text, re.IGNORECASE)
                info.name_servers = [ns.strip().lower() for ns in ns_matches]
                
                # Status
                status_matches = re.findall(r'Domain Status:\s*(.+)', text, re.IGNORECASE)
                info.status = [s.strip() for s in status_matches]
        except:
            pass
        
        return info
    
    def _get_security_headers(self, domain: str) -> Dict[str, str]:
        """Verifica headers de segurança"""
        headers = {}
        
        security_headers = [
            'Strict-Transport-Security',
            'Content-Security-Policy',
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Referrer-Policy',
        ]
        
        try:
            resp = self.session.get(f"https://{domain}", timeout=self.timeout, verify=False)
            
            for header in security_headers:
                value = resp.headers.get(header, '')
                headers[header] = value if value else 'MISSING'
        except:
            pass
        
        return headers
    
    def _find_subdomains(self, domain: str) -> List[str]:
        """Busca subdomínios via crt.sh"""
        subdomains = []
        
        try:
            resp = self.session.get(
                f"https://crt.sh/?q=%.{domain}&output=json",
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                for entry in data[:100]:  # Limite de 100
                    name = entry.get('name_value', '')
                    for sub in name.split('\n'):
                        sub = sub.strip().lower()
                        if sub.endswith(domain) and '*' not in sub:
                            if sub not in subdomains:
                                subdomains.append(sub)
        except:
            pass
        
        return subdomains[:20]  # Top 20
    
    def _check_reputation(self, domain: str) -> Dict:
        """Verifica reputação do domínio"""
        reputation = {
            'status': 'unknown',
            'blacklists': [],
            'safe': True
        }
        
        # Verificar em algumas listas
        try:
            # Google Safe Browsing (simplificado)
            resp = self.session.get(
                f"https://transparencyreport.google.com/transparencyreport/api/v3/safebrowsing/status?site={domain}",
                timeout=5
            )
            if 'unsafe' in resp.text.lower():
                reputation['safe'] = False
                reputation['status'] = 'potentially unsafe'
        except:
            pass
        
        return reputation
    
    def _print_results(self, result: DomainIntelResult):
        """Imprime resultados formatados"""
        print("\n" + "=" * 50)
        print(f"📊 Resultados para: {result.domain}")
        print("=" * 50)
        
        # DNS
        if result.dns_info:
            dns = result.dns_info
            print(f"\n📡 DNS:")
            if dns.a_records:
                print(f"   A: {', '.join(dns.a_records)}")
            if dns.mx_records:
                print(f"   MX: {', '.join(dns.mx_records[:3])}")
            if dns.ns_records:
                print(f"   NS: {', '.join(dns.ns_records[:3])}")
        
        # Web
        if result.web_info:
            web = result.web_info
            print(f"\n🌐 Web:")
            print(f"   IP: {web.ip_address}")
            print(f"   Server: {web.server or 'N/A'}")
            print(f"   SSL: {'✅' if web.has_ssl else '❌'}")
            if web.ssl_issuer:
                print(f"   SSL Issuer: {web.ssl_issuer}")
            if web.title:
                print(f"   Título: {web.title}")
            if web.cms:
                print(f"   CMS: {web.cms}")
            if web.technologies:
                print(f"   Tecnologias: {', '.join(web.technologies)}")
        
        # WHOIS
        if result.domain_info:
            info = result.domain_info
            print(f"\n📋 WHOIS:")
            if info.registrar:
                print(f"   Registrar: {info.registrar}")
            if info.creation_date:
                print(f"   Criação: {info.creation_date}")
            if info.expiration_date:
                print(f"   Expiração: {info.expiration_date}")
        
        # Security
        if result.security_headers:
            missing = [h for h, v in result.security_headers.items() if v == 'MISSING']
            present = [h for h, v in result.security_headers.items() if v != 'MISSING']
            print(f"\n🔒 Security Headers:")
            print(f"   ✅ Presentes: {len(present)}")
            print(f"   ❌ Ausentes: {len(missing)}")
            if missing:
                print(f"   Faltando: {', '.join(missing[:3])}")
        
        # Subdomains
        if result.subdomains:
            print(f"\n🔍 Subdomínios ({len(result.subdomains)}):")
            for sub in result.subdomains[:5]:
                print(f"   • {sub}")
            if len(result.subdomains) > 5:
                print(f"   ... e mais {len(result.subdomains) - 5}")
    
    def export_report(self, result: DomainIntelResult, filepath: str):
        """Exporta relatório para JSON"""
        report = {
            'domain': result.domain,
            'timestamp': datetime.now().isoformat(),
            'dns': {
                'a_records': result.dns_info.a_records if result.dns_info else [],
                'mx_records': result.dns_info.mx_records if result.dns_info else [],
                'ns_records': result.dns_info.ns_records if result.dns_info else [],
                'txt_records': result.dns_info.txt_records if result.dns_info else [],
            } if result.dns_info else {},
            'web': {
                'ip': result.web_info.ip_address if result.web_info else '',
                'server': result.web_info.server if result.web_info else '',
                'ssl': result.web_info.has_ssl if result.web_info else False,
                'technologies': result.web_info.technologies if result.web_info else [],
                'cms': result.web_info.cms if result.web_info else '',
            } if result.web_info else {},
            'whois': {
                'registrar': result.domain_info.registrar if result.domain_info else '',
                'creation': result.domain_info.creation_date if result.domain_info else '',
                'expiration': result.domain_info.expiration_date if result.domain_info else '',
            } if result.domain_info else {},
            'security_headers': result.security_headers,
            'subdomains': result.subdomains,
            'reputation': result.reputation,
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Relatório salvo: {filepath}")


# Suprimir warnings de SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    """Função principal"""
    import sys
    
    print("\n" + "=" * 50)
    print("🔍 Domain Intelligence - Olho de Deus")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        domain = input("\n🌐 Domínio para analisar: ").strip()
    else:
        domain = sys.argv[1]
    
    intel = DomainIntelligence()
    result = intel.analyze(domain)
    
    print("\n✅ Análise concluída!")


if __name__ == "__main__":
    main()
