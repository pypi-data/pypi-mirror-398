#!/usr/bin/env python3
"""
Banner Grabber - Olho de Deus
Coleta de banners de serviços para identificação
"""

import socket
import ssl
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BannerResult:
    """Resultado de banner grabbing"""
    host: str
    port: int
    protocol: str
    banner: str = ""
    service: str = ""
    version: str = ""
    os_hint: str = ""
    response_time: float = 0.0
    ssl_enabled: bool = False
    raw_response: bytes = b""


class BannerGrabber:
    """Grabber de banners de serviços"""
    
    # Probes para diferentes serviços
    SERVICE_PROBES = {
        'http': b"GET / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n",
        'http_head': b"HEAD / HTTP/1.0\r\n\r\n",
        'ftp': b"",  # FTP envia banner automaticamente
        'ssh': b"",  # SSH envia banner automaticamente
        'smtp': b"",  # SMTP envia banner automaticamente
        'pop3': b"",  # POP3 envia banner automaticamente
        'imap': b"",  # IMAP envia banner automaticamente
        'mysql': b"",  # MySQL envia banner automaticamente
        'telnet': b"",  # Telnet envia banner automaticamente
        'redis': b"INFO\r\n",
        'mongodb': b"\x3a\x00\x00\x00\xa7\x41\x00\x00\x00\x00\x00\x00\xd4\x07\x00\x00",
        'generic': b"\r\n\r\n",
    }
    
    # Portas e serviços comuns
    PORT_SERVICES = {
        21: 'ftp',
        22: 'ssh',
        23: 'telnet',
        25: 'smtp',
        80: 'http',
        110: 'pop3',
        143: 'imap',
        443: 'https',
        465: 'smtps',
        587: 'smtp',
        993: 'imaps',
        995: 'pop3s',
        3306: 'mysql',
        3389: 'rdp',
        5432: 'postgresql',
        6379: 'redis',
        8080: 'http',
        8443: 'https',
        27017: 'mongodb',
    }
    
    # Padrões para identificação de serviços
    SERVICE_PATTERNS = {
        # HTTP
        r'Server:\s*([^\r\n]+)': ('http_server', 1),
        r'Apache[/\s]*([\d.]+)?': ('Apache', 1),
        r'nginx[/\s]*([\d.]+)?': ('nginx', 1),
        r'Microsoft-IIS[/\s]*([\d.]+)?': ('IIS', 1),
        r'LiteSpeed': ('LiteSpeed', None),
        
        # SSH
        r'SSH-([\d.]+)-OpenSSH[_\s]*([\d.p]+)?': ('OpenSSH', 2),
        r'SSH-([\d.]+)-dropbear': ('Dropbear', None),
        r'SSH-([\d.]+)-libssh': ('libssh', None),
        
        # FTP
        r'220[- ].*vsftpd\s*([\d.]+)?': ('vsftpd', 1),
        r'220[- ].*ProFTPD\s*([\d.]+)?': ('ProFTPD', 1),
        r'220[- ].*FileZilla': ('FileZilla FTP', None),
        r'220[- ].*Pure-FTPd': ('Pure-FTPd', None),
        
        # SMTP
        r'220[- ].*Postfix': ('Postfix', None),
        r'220[- ].*Exim\s*([\d.]+)?': ('Exim', 1),
        r'220[- ].*Microsoft Exchange': ('Exchange', None),
        r'220[- ].*Sendmail': ('Sendmail', None),
        
        # Database
        r'mysql_native_password': ('MySQL', None),
        r'MariaDB': ('MariaDB', None),
        r'PostgreSQL': ('PostgreSQL', None),
        r'\-ERR.*Redis': ('Redis', None),
        r'MongoDB': ('MongoDB', None),
        
        # OS hints
        r'Ubuntu': ('OS:Ubuntu', None),
        r'Debian': ('OS:Debian', None),
        r'CentOS': ('OS:CentOS', None),
        r'Windows': ('OS:Windows', None),
        r'FreeBSD': ('OS:FreeBSD', None),
    }
    
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
    
    def grab(self, host: str, port: int, use_ssl: bool = None) -> BannerResult:
        """Coleta banner de um serviço"""
        result = BannerResult(host=host, port=port, protocol='tcp')
        
        # Determinar se deve usar SSL
        if use_ssl is None:
            use_ssl = port in [443, 465, 636, 993, 995, 8443]
        
        result.ssl_enabled = use_ssl
        
        # Determinar probe baseado na porta
        service_type = self.PORT_SERVICES.get(port, 'generic')
        probe = self.SERVICE_PROBES.get(service_type, self.SERVICE_PROBES['generic'])
        
        if isinstance(probe, bytes) and b'{host}' in probe:
            probe = probe.replace(b'{host}', host.encode())
        
        start_time = datetime.now()
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((host, port))
            
            if use_ssl:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=host)
            
            # Enviar probe se necessário
            if probe:
                sock.send(probe)
            
            # Receber resposta
            response = b""
            try:
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    if len(response) > 8192:  # Limite de 8KB
                        break
            except socket.timeout:
                pass
            
            sock.close()
            
            result.response_time = (datetime.now() - start_time).total_seconds()
            result.raw_response = response
            
            # Decodificar resposta
            try:
                result.banner = response.decode('utf-8', errors='ignore').strip()
            except:
                result.banner = response.decode('latin-1', errors='ignore').strip()
            
            # Identificar serviço
            self._identify_service(result)
            
        except socket.timeout:
            result.banner = "[TIMEOUT]"
        except ConnectionRefusedError:
            result.banner = "[CONNECTION REFUSED]"
        except Exception as e:
            result.banner = f"[ERROR: {str(e)}]"
        
        return result
    
    def _identify_service(self, result: BannerResult):
        """Identifica o serviço baseado no banner"""
        banner = result.banner
        
        for pattern, (service, version_group) in self.SERVICE_PATTERNS.items():
            match = re.search(pattern, banner, re.IGNORECASE)
            if match:
                if service.startswith('OS:'):
                    result.os_hint = service[3:]
                else:
                    result.service = service
                    if version_group and match.lastindex and match.lastindex >= version_group:
                        result.version = match.group(version_group) or ""
    
    def grab_multiple(self, host: str, ports: List[int], threads: int = 10) -> List[BannerResult]:
        """Coleta banners de múltiplas portas"""
        results = []
        
        print(f"\n🎯 Coletando banners: {host}")
        print(f"   Portas: {len(ports)}")
        print("-" * 40)
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {
                executor.submit(self.grab, host, port): port 
                for port in ports
            }
            
            for future in as_completed(futures):
                port = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result.banner and not result.banner.startswith('['):
                        service = result.service or 'Unknown'
                        version = f" {result.version}" if result.version else ""
                        ssl_tag = " [SSL]" if result.ssl_enabled else ""
                        print(f"   ✅ {port}: {service}{version}{ssl_tag}")
                except Exception as e:
                    print(f"   ❌ {port}: Error - {e}")
        
        return sorted(results, key=lambda x: x.port)
    
    def scan_common_ports(self, host: str) -> List[BannerResult]:
        """Escaneia portas comuns e coleta banners"""
        common_ports = list(self.PORT_SERVICES.keys())
        return self.grab_multiple(host, common_ports)
    
    def fingerprint_service(self, host: str, port: int) -> Dict:
        """Fingerprinting detalhado de um serviço"""
        result = self.grab(host, port)
        
        fingerprint = {
            'host': host,
            'port': port,
            'service': result.service,
            'version': result.version,
            'os_hint': result.os_hint,
            'ssl': result.ssl_enabled,
            'banner_length': len(result.banner),
            'response_time_ms': result.response_time * 1000,
            'banner_preview': result.banner[:200] if result.banner else ""
        }
        
        # Análise adicional baseada no serviço
        if result.service == 'OpenSSH':
            fingerprint['protocol_version'] = self._extract_ssh_version(result.banner)
        elif 'http' in result.service.lower():
            fingerprint['headers'] = self._parse_http_headers(result.banner)
        
        return fingerprint
    
    def _extract_ssh_version(self, banner: str) -> str:
        """Extrai versão do protocolo SSH"""
        match = re.search(r'SSH-([\d.]+)', banner)
        return match.group(1) if match else ""
    
    def _parse_http_headers(self, response: str) -> Dict[str, str]:
        """Parse de headers HTTP"""
        headers = {}
        lines = response.split('\r\n')
        
        for line in lines[1:]:  # Skip status line
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
            elif not line:
                break
        
        return headers
    
    def export_results(self, results: List[BannerResult], filepath: str):
        """Exporta resultados para JSON"""
        data = []
        for r in results:
            data.append({
                'host': r.host,
                'port': r.port,
                'service': r.service,
                'version': r.version,
                'os_hint': r.os_hint,
                'ssl': r.ssl_enabled,
                'response_time': r.response_time,
                'banner': r.banner[:500] if r.banner else ""
            })
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n📄 Resultados salvos: {filepath}")


def main():
    """Função principal"""
    import sys
    
    print("\n" + "=" * 50)
    print("🎯 Banner Grabber - Olho de Deus")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        host = input("\n🌐 Host alvo: ").strip()
    else:
        host = sys.argv[1]
    
    port = None
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    
    grabber = BannerGrabber()
    
    if port:
        # Single port
        result = grabber.grab(host, port)
        print(f"\n📋 Resultado para {host}:{port}")
        print("-" * 40)
        print(f"   Serviço: {result.service or 'Desconhecido'}")
        print(f"   Versão: {result.version or 'N/A'}")
        print(f"   SSL: {'Sim' if result.ssl_enabled else 'Não'}")
        print(f"   Tempo: {result.response_time*1000:.0f}ms")
        print(f"\n   Banner:")
        for line in result.banner.split('\n')[:10]:
            print(f"   | {line}")
    else:
        # Scan common ports
        results = grabber.scan_common_ports(host)
        
        print(f"\n📊 Resumo: {len([r for r in results if r.service])} serviços identificados")
    
    print("\n✅ Coleta concluída!")


if __name__ == "__main__":
    main()
