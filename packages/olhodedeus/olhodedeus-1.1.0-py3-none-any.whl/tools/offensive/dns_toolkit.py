#!/usr/bin/env python3
"""
DNS Toolkit - Olho de Deus
Ferramentas DNS avançadas para reconhecimento
"""

import socket
import struct
import random
import threading
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DNSRecord:
    """Representa um registro DNS"""
    name: str
    record_type: str
    value: str
    ttl: int = 0
    priority: int = 0  # Para MX
    extra: Dict = field(default_factory=dict)


@dataclass
class DNSResult:
    """Resultado de consulta DNS"""
    domain: str
    records: List[DNSRecord] = field(default_factory=list)
    nameservers: List[str] = field(default_factory=list)
    zone_transfer: bool = False
    subdomains: List[str] = field(default_factory=list)


class DNSResolver:
    """Resolver DNS customizado"""
    
    # Tipos de registro DNS
    RECORD_TYPES = {
        'A': 1,
        'NS': 2,
        'CNAME': 5,
        'SOA': 6,
        'PTR': 12,
        'MX': 15,
        'TXT': 16,
        'AAAA': 28,
        'SRV': 33,
        'ANY': 255,
    }
    
    # DNS públicos
    PUBLIC_DNS = [
        "8.8.8.8",        # Google
        "8.8.4.4",        # Google
        "1.1.1.1",        # Cloudflare
        "1.0.0.1",        # Cloudflare
        "9.9.9.9",        # Quad9
        "208.67.222.222", # OpenDNS
        "208.67.220.220", # OpenDNS
    ]
    
    def __init__(self, dns_server: str = "8.8.8.8", timeout: float = 3.0):
        self.dns_server = dns_server
        self.timeout = timeout
    
    def build_query(self, domain: str, record_type: str = 'A') -> bytes:
        """Constrói pacote de consulta DNS"""
        # Header
        transaction_id = random.randint(0, 65535)
        flags = 0x0100  # Standard query
        questions = 1
        answers = 0
        authority = 0
        additional = 0
        
        header = struct.pack('>HHHHHH', 
            transaction_id, flags, questions, 
            answers, authority, additional
        )
        
        # Question
        question = b''
        for part in domain.split('.'):
            question += bytes([len(part)]) + part.encode()
        question += b'\x00'  # End of domain
        
        # Type and Class
        qtype = self.RECORD_TYPES.get(record_type.upper(), 1)
        qclass = 1  # IN (Internet)
        question += struct.pack('>HH', qtype, qclass)
        
        return header + question
    
    def parse_response(self, response: bytes, record_type: str = 'A') -> List[DNSRecord]:
        """Parse de resposta DNS"""
        records = []
        
        try:
            # Pular header (12 bytes)
            offset = 12
            
            # Pular question section
            while response[offset] != 0:
                length = response[offset]
                offset += length + 1
            offset += 5  # Null byte + type + class
            
            # Parse answers
            answer_count = struct.unpack('>H', response[4:6])[0]
            
            for _ in range(answer_count):
                # Name (pode ser ponteiro)
                if response[offset] & 0xC0 == 0xC0:
                    # Ponteiro de compressão
                    offset += 2
                else:
                    while response[offset] != 0:
                        offset += response[offset] + 1
                    offset += 1
                
                # Type, Class, TTL, Data length
                rtype, rclass, ttl, rdlength = struct.unpack('>HHIH', response[offset:offset+10])
                offset += 10
                
                rdata = response[offset:offset+rdlength]
                offset += rdlength
                
                # Parse based on type
                record = DNSRecord(name="", record_type=record_type, value="", ttl=ttl)
                
                if rtype == 1:  # A
                    record.record_type = "A"
                    record.value = '.'.join(str(b) for b in rdata)
                elif rtype == 28:  # AAAA
                    record.record_type = "AAAA"
                    record.value = ':'.join(f'{rdata[i]:02x}{rdata[i+1]:02x}' 
                                           for i in range(0, 16, 2))
                elif rtype == 5:  # CNAME
                    record.record_type = "CNAME"
                    record.value = self._parse_name(response, response.index(rdata))
                elif rtype == 15:  # MX
                    record.record_type = "MX"
                    record.priority = struct.unpack('>H', rdata[:2])[0]
                    record.value = self._parse_name(response, offset - rdlength + 2)
                elif rtype == 16:  # TXT
                    record.record_type = "TXT"
                    txt_len = rdata[0]
                    record.value = rdata[1:1+txt_len].decode('utf-8', errors='replace')
                elif rtype == 2:  # NS
                    record.record_type = "NS"
                    record.value = self._parse_name(response, offset - rdlength)
                
                records.append(record)
        
        except Exception:
            pass
        
        return records
    
    def _parse_name(self, data: bytes, offset: int) -> str:
        """Parse de nome DNS com compressão"""
        name_parts = []
        while True:
            length = data[offset]
            if length == 0:
                break
            if length & 0xC0 == 0xC0:
                # Ponteiro de compressão
                pointer = struct.unpack('>H', data[offset:offset+2])[0] & 0x3FFF
                return '.'.join(name_parts) + '.' + self._parse_name(data, pointer)
            else:
                offset += 1
                name_parts.append(data[offset:offset+length].decode('utf-8', errors='replace'))
                offset += length
        return '.'.join(name_parts)
    
    def resolve(self, domain: str, record_type: str = 'A') -> List[DNSRecord]:
        """Resolve domínio"""
        try:
            query = self.build_query(domain, record_type)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            sock.sendto(query, (self.dns_server, 53))
            
            response, _ = sock.recvfrom(4096)
            sock.close()
            
            return self.parse_response(response, record_type)
        except Exception:
            return []
    
    def resolve_all(self, domain: str) -> Dict[str, List[DNSRecord]]:
        """Resolve todos os tipos de registro comuns"""
        results = {}
        
        for record_type in ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']:
            records = self.resolve(domain, record_type)
            if records:
                results[record_type] = records
        
        return results


class DNSEnumerator:
    """Enumerador DNS avançado"""
    
    # Subdomínios comuns para bruteforce
    COMMON_SUBDOMAINS = [
        "www", "mail", "ftp", "smtp", "pop", "imap", "webmail", "admin", "portal",
        "ns1", "ns2", "ns3", "dns", "dns1", "dns2", "mx", "mx1", "mx2", "email",
        "vpn", "remote", "gateway", "proxy", "firewall", "router", "switch",
        "api", "dev", "development", "staging", "test", "testing", "qa", "uat",
        "prod", "production", "live", "demo", "beta", "alpha", "preview",
        "app", "apps", "mobile", "m", "wap", "i", "ios", "android",
        "blog", "news", "forum", "wiki", "docs", "documentation", "help", "support",
        "shop", "store", "cart", "checkout", "payment", "pay", "billing",
        "cdn", "static", "assets", "images", "img", "media", "files", "download",
        "db", "database", "mysql", "postgres", "mongodb", "redis", "cache",
        "ldap", "ad", "directory", "auth", "login", "sso", "oauth", "identity",
        "git", "gitlab", "github", "svn", "repo", "repository", "ci", "jenkins",
        "monitor", "monitoring", "status", "health", "metrics", "logs", "logging",
        "backup", "backups", "archive", "old", "legacy", "v1", "v2", "v3",
        "internal", "intranet", "extranet", "private", "public", "external",
        "crm", "erp", "hr", "finance", "sales", "marketing", "it", "helpdesk",
        "cloud", "aws", "azure", "gcp", "k8s", "kubernetes", "docker", "container",
        "cpanel", "plesk", "whm", "panel", "control", "manage", "manager",
        "autodiscover", "autoconfig", "exchange", "owa", "outlook",
        "conference", "meet", "video", "chat", "im", "messaging",
        "sftp", "ssh", "terminal", "console", "shell", "bastion",
        "a", "b", "c", "1", "2", "3", "server", "host", "node", "cluster",
    ]
    
    def __init__(self, domain: str, dns_servers: List[str] = None, threads: int = 20):
        self.domain = domain
        self.dns_servers = dns_servers or DNSResolver.PUBLIC_DNS[:3]
        self.threads = threads
        self.found_subdomains: Set[str] = set()
        self.lock = threading.Lock()
    
    def check_subdomain(self, subdomain: str) -> Optional[Tuple[str, List[str]]]:
        """Verifica se subdomínio existe"""
        fqdn = f"{subdomain}.{self.domain}"
        
        for dns in self.dns_servers:
            try:
                resolver = DNSResolver(dns, timeout=2.0)
                records = resolver.resolve(fqdn, 'A')
                
                if records:
                    ips = [r.value for r in records]
                    with self.lock:
                        self.found_subdomains.add(fqdn)
                    return (fqdn, ips)
            except Exception:
                continue
        
        return None
    
    def bruteforce_subdomains(self, wordlist: List[str] = None, 
                              callback=None) -> Dict[str, List[str]]:
        """Bruteforce de subdomínios"""
        wordlist = wordlist or self.COMMON_SUBDOMAINS
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {
                executor.submit(self.check_subdomain, sub): sub 
                for sub in wordlist
            }
            
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                if result:
                    fqdn, ips = result
                    results[fqdn] = ips
                
                completed += 1
                if callback:
                    callback(completed, len(wordlist))
        
        return results
    
    def zone_transfer(self) -> List[str]:
        """Tenta zone transfer (AXFR)"""
        subdomains = []
        
        # Primeiro obtém nameservers
        resolver = DNSResolver(self.dns_servers[0])
        ns_records = resolver.resolve(self.domain, 'NS')
        
        for ns in ns_records:
            try:
                # Resolve NS para IP
                ns_ip_records = resolver.resolve(ns.value.rstrip('.'), 'A')
                if not ns_ip_records:
                    continue
                
                ns_ip = ns_ip_records[0].value
                
                # Tenta AXFR (Zone Transfer)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((ns_ip, 53))
                
                # Constrói query AXFR
                query = resolver.build_query(self.domain, 'ANY')
                # Adiciona length prefix para TCP
                query = struct.pack('>H', len(query)) + query
                
                sock.send(query)
                
                # Recebe resposta
                response = b''
                while True:
                    try:
                        data = sock.recv(4096)
                        if not data:
                            break
                        response += data
                    except:
                        break
                
                sock.close()
                
                # Parse de nomes na resposta
                for match in re.finditer(rb'([a-zA-Z0-9\-]+\.' + 
                                        self.domain.encode() + rb')', response):
                    subdomain = match.group(1).decode('utf-8', errors='ignore')
                    if subdomain not in subdomains:
                        subdomains.append(subdomain)
                
            except Exception:
                continue
        
        return subdomains
    
    def reverse_lookup(self, ip: str) -> Optional[str]:
        """Reverse DNS lookup"""
        try:
            # Constrói PTR query
            octets = ip.split('.')
            ptr_domain = '.'.join(reversed(octets)) + '.in-addr.arpa'
            
            resolver = DNSResolver(self.dns_servers[0])
            records = resolver.resolve(ptr_domain, 'PTR')
            
            if records:
                return records[0].value
        except Exception:
            pass
        
        return None
    
    def reverse_range(self, ip_range: str) -> Dict[str, str]:
        """Reverse lookup em range de IPs"""
        results = {}
        
        # Parse range (ex: 192.168.1.0/24)
        if '/' in ip_range:
            base_ip, cidr = ip_range.split('/')
            cidr = int(cidr)
            
            if cidr >= 24:
                # Apenas últimos octetos variam
                base = '.'.join(base_ip.split('.')[:3])
                hosts = 2 ** (32 - cidr)
                start = int(base_ip.split('.')[3])
                
                for i in range(hosts):
                    ip = f"{base}.{start + i}"
                    hostname = self.reverse_lookup(ip)
                    if hostname:
                        results[ip] = hostname
        else:
            # IP único
            hostname = self.reverse_lookup(ip_range)
            if hostname:
                results[ip_range] = hostname
        
        return results


class DNSAnalyzer:
    """Analisador de configuração DNS"""
    
    def __init__(self, domain: str):
        self.domain = domain
        self.resolver = DNSResolver()
    
    def analyze_spf(self) -> Dict:
        """Analisa registro SPF"""
        result = {
            'found': False,
            'record': '',
            'issues': [],
            'mechanisms': []
        }
        
        records = self.resolver.resolve(self.domain, 'TXT')
        
        for record in records:
            if 'v=spf1' in record.value:
                result['found'] = True
                result['record'] = record.value
                
                # Parse mechanisms
                parts = record.value.split()
                for part in parts[1:]:
                    if part.startswith('+') or part.startswith('-') or \
                       part.startswith('~') or part.startswith('?'):
                        result['mechanisms'].append(part)
                    elif part not in ['v=spf1', 'all', '-all', '~all', '+all']:
                        result['mechanisms'].append('+' + part)
                
                # Check issues
                if '+all' in record.value:
                    result['issues'].append("CRÍTICO: +all permite qualquer servidor")
                if '~all' in record.value:
                    result['issues'].append("AVISO: ~all (softfail) é mais fraco que -all")
                if 'include:' not in record.value and 'ip4:' not in record.value:
                    result['issues'].append("AVISO: Nenhum mecanismo de autorização")
        
        return result
    
    def analyze_dmarc(self) -> Dict:
        """Analisa registro DMARC"""
        result = {
            'found': False,
            'record': '',
            'policy': '',
            'issues': []
        }
        
        dmarc_domain = f"_dmarc.{self.domain}"
        records = self.resolver.resolve(dmarc_domain, 'TXT')
        
        for record in records:
            if 'v=DMARC1' in record.value:
                result['found'] = True
                result['record'] = record.value
                
                # Parse policy
                for part in record.value.split(';'):
                    part = part.strip()
                    if part.startswith('p='):
                        result['policy'] = part[2:]
                
                # Check issues
                if result['policy'] == 'none':
                    result['issues'].append("AVISO: Política 'none' apenas monitora")
                if 'rua=' not in record.value:
                    result['issues'].append("AVISO: Sem endereço para relatórios agregados")
        
        return result
    
    def analyze_dkim(self, selector: str = "default") -> Dict:
        """Analisa registro DKIM"""
        result = {
            'found': False,
            'record': '',
            'issues': []
        }
        
        dkim_domain = f"{selector}._domainkey.{self.domain}"
        records = self.resolver.resolve(dkim_domain, 'TXT')
        
        for record in records:
            if 'v=DKIM1' in record.value or 'p=' in record.value:
                result['found'] = True
                result['record'] = record.value
        
        return result
    
    def check_dnssec(self) -> Dict:
        """Verifica DNSSEC"""
        result = {
            'enabled': False,
            'dnskey': False,
            'ds': False
        }
        
        # Verifica DNSKEY
        try:
            socket.setdefaulttimeout(5)
            # Simplificado - apenas verifica se há resposta para DNSKEY
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)
            
            # Query DNSKEY (type 48)
            query = self._build_dnssec_query(self.domain, 48)
            sock.sendto(query, ("8.8.8.8", 53))
            response, _ = sock.recvfrom(4096)
            
            # Verifica se há respostas
            answer_count = struct.unpack('>H', response[6:8])[0]
            if answer_count > 0:
                result['dnskey'] = True
                result['enabled'] = True
            
            sock.close()
        except:
            pass
        
        return result
    
    def _build_dnssec_query(self, domain: str, qtype: int) -> bytes:
        """Constrói query DNSSEC"""
        tid = random.randint(0, 65535)
        flags = 0x0100
        header = struct.pack('>HHHHHH', tid, flags, 1, 0, 0, 0)
        
        question = b''
        for part in domain.split('.'):
            question += bytes([len(part)]) + part.encode()
        question += b'\x00'
        question += struct.pack('>HH', qtype, 1)
        
        return header + question
    
    def full_analysis(self) -> Dict:
        """Análise completa de segurança DNS"""
        return {
            'domain': self.domain,
            'spf': self.analyze_spf(),
            'dmarc': self.analyze_dmarc(),
            'dkim': self.analyze_dkim(),
            'dnssec': self.check_dnssec(),
            'timestamp': datetime.now().isoformat()
        }


def print_banner():
    """Exibe banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                      🌐 DNS TOOLKIT                               ║
║                     Olho de Deus v2.0                             ║
╠══════════════════════════════════════════════════════════════════╣
║  Features: DNS Lookup | Zone Transfer | Subdomain Enum           ║
║           | Reverse DNS | Security Analysis | DNSSEC Check       ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def progress_callback(current: int, total: int):
    """Callback de progresso"""
    percent = (current / total) * 100
    bar_length = 40
    filled = int(bar_length * current / total)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\r⏳ [{bar}] {percent:.1f}% ({current}/{total})", end="", flush=True)


def interactive_menu():
    """Menu interativo"""
    print_banner()
    
    while True:
        print("\n📋 MENU DNS TOOLKIT")
        print("-" * 40)
        print("[1] 🔍 Lookup DNS (todos os registros)")
        print("[2] 📡 Lookup por tipo específico")
        print("[3] 🔄 Reverse DNS")
        print("[4] 🎯 Bruteforce de subdomínios")
        print("[5] 📋 Zone Transfer (AXFR)")
        print("[6] 🔒 Análise de segurança (SPF/DMARC/DKIM)")
        print("[7] 🛡️ Verificar DNSSEC")
        print("[8] 📊 Análise completa")
        print("[0] ❌ Voltar")
        
        choice = input("\n🔹 Escolha: ").strip()
        
        if choice == "0":
            break
        
        elif choice == "1":
            domain = input("🌐 Domínio: ").strip()
            if not domain:
                print("❌ Domínio inválido!")
                continue
            
            resolver = DNSResolver()
            print(f"\n🔍 Consultando registros de {domain}...")
            
            results = resolver.resolve_all(domain)
            
            if results:
                for rtype, records in results.items():
                    print(f"\n📌 {rtype}:")
                    for r in records:
                        if r.priority:
                            print(f"   [{r.priority}] {r.value} (TTL: {r.ttl})")
                        else:
                            print(f"   {r.value} (TTL: {r.ttl})")
            else:
                print("❌ Nenhum registro encontrado")
        
        elif choice == "2":
            domain = input("🌐 Domínio: ").strip()
            print("\nTipos: A, AAAA, MX, NS, TXT, CNAME, SOA, SRV")
            rtype = input("📌 Tipo: ").strip().upper()
            
            if not domain or rtype not in DNSResolver.RECORD_TYPES:
                print("❌ Dados inválidos!")
                continue
            
            resolver = DNSResolver()
            print(f"\n🔍 Consultando {rtype} de {domain}...")
            
            records = resolver.resolve(domain, rtype)
            
            if records:
                print(f"\n📌 {rtype} Records:")
                for r in records:
                    print(f"   {r.value} (TTL: {r.ttl})")
            else:
                print("❌ Nenhum registro encontrado")
        
        elif choice == "3":
            ip = input("🔢 IP: ").strip()
            if not ip:
                print("❌ IP inválido!")
                continue
            
            enum = DNSEnumerator("")
            print(f"\n🔍 Reverse lookup de {ip}...")
            
            hostname = enum.reverse_lookup(ip)
            if hostname:
                print(f"✅ {ip} → {hostname}")
            else:
                print("❌ Nenhum PTR encontrado")
        
        elif choice == "4":
            domain = input("🌐 Domínio: ").strip()
            if not domain:
                print("❌ Domínio inválido!")
                continue
            
            threads = input("⚡ Threads [20]: ").strip() or "20"
            
            enum = DNSEnumerator(domain, threads=int(threads))
            print(f"\n🔍 Bruteforce de subdomínios em {domain}...")
            print(f"   Wordlist: {len(DNSEnumerator.COMMON_SUBDOMAINS)} palavras")
            
            results = enum.bruteforce_subdomains(callback=progress_callback)
            print()
            
            if results:
                print(f"\n✅ {len(results)} subdomínios encontrados:")
                for subdomain, ips in sorted(results.items()):
                    print(f"   {subdomain} → {', '.join(ips)}")
            else:
                print("\n❌ Nenhum subdomínio encontrado")
        
        elif choice == "5":
            domain = input("🌐 Domínio: ").strip()
            if not domain:
                print("❌ Domínio inválido!")
                continue
            
            enum = DNSEnumerator(domain)
            print(f"\n🔍 Tentando Zone Transfer em {domain}...")
            
            subdomains = enum.zone_transfer()
            
            if subdomains:
                print(f"\n✅ Zone Transfer bem sucedido! {len(subdomains)} registros:")
                for sub in sorted(set(subdomains)):
                    print(f"   {sub}")
            else:
                print("\n❌ Zone Transfer falhou (bloqueado ou não permitido)")
        
        elif choice == "6":
            domain = input("🌐 Domínio: ").strip()
            if not domain:
                print("❌ Domínio inválido!")
                continue
            
            analyzer = DNSAnalyzer(domain)
            print(f"\n🔍 Analisando segurança DNS de {domain}...")
            
            # SPF
            spf = analyzer.analyze_spf()
            print("\n📌 SPF (Sender Policy Framework):")
            if spf['found']:
                print(f"   ✅ Encontrado: {spf['record'][:80]}...")
                for issue in spf['issues']:
                    print(f"   ⚠️ {issue}")
            else:
                print("   ❌ Não encontrado")
            
            # DMARC
            dmarc = analyzer.analyze_dmarc()
            print("\n📌 DMARC:")
            if dmarc['found']:
                print(f"   ✅ Encontrado: Política = {dmarc['policy']}")
                for issue in dmarc['issues']:
                    print(f"   ⚠️ {issue}")
            else:
                print("   ❌ Não encontrado")
            
            # DKIM
            selectors = ["default", "google", "selector1", "selector2", "k1", "dkim"]
            print("\n📌 DKIM:")
            dkim_found = False
            for sel in selectors:
                dkim = analyzer.analyze_dkim(sel)
                if dkim['found']:
                    print(f"   ✅ Encontrado (selector: {sel})")
                    dkim_found = True
                    break
            if not dkim_found:
                print("   ❌ Não encontrado (testados: " + ", ".join(selectors) + ")")
        
        elif choice == "7":
            domain = input("🌐 Domínio: ").strip()
            if not domain:
                print("❌ Domínio inválido!")
                continue
            
            analyzer = DNSAnalyzer(domain)
            print(f"\n🔍 Verificando DNSSEC para {domain}...")
            
            dnssec = analyzer.check_dnssec()
            
            if dnssec['enabled']:
                print("   ✅ DNSSEC está habilitado!")
                if dnssec['dnskey']:
                    print("   ✅ DNSKEY presente")
            else:
                print("   ❌ DNSSEC não está habilitado")
        
        elif choice == "8":
            domain = input("🌐 Domínio: ").strip()
            if not domain:
                print("❌ Domínio inválido!")
                continue
            
            print(f"\n🔍 Análise completa de {domain}...")
            print("=" * 60)
            
            # DNS Records
            resolver = DNSResolver()
            records = resolver.resolve_all(domain)
            
            print("\n📋 REGISTROS DNS:")
            for rtype, recs in records.items():
                print(f"   {rtype}: {len(recs)} registro(s)")
            
            # Subdomains
            enum = DNSEnumerator(domain, threads=30)
            print("\n🎯 SUBDOMÍNIOS (bruteforce):")
            subs = enum.bruteforce_subdomains()
            print(f"   Encontrados: {len(subs)}")
            for sub in list(subs.keys())[:10]:
                print(f"      {sub}")
            if len(subs) > 10:
                print(f"      ... e mais {len(subs) - 10}")
            
            # Security
            analyzer = DNSAnalyzer(domain)
            analysis = analyzer.full_analysis()
            
            print("\n🔒 SEGURANÇA:")
            print(f"   SPF: {'✅' if analysis['spf']['found'] else '❌'}")
            print(f"   DMARC: {'✅' if analysis['dmarc']['found'] else '❌'}")
            print(f"   DNSSEC: {'✅' if analysis['dnssec']['enabled'] else '❌'}")
            
            print("\n" + "=" * 60)
        
        else:
            print("❌ Opção inválida!")
        
        input("\n⏎ Pressione ENTER para continuar...")


if __name__ == "__main__":
    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelado pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
