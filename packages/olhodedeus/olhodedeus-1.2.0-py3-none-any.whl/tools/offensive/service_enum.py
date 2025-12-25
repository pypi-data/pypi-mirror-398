#!/usr/bin/env python3
"""
Service Enumeration - Olho de Deus
Enumeração avançada de serviços em portas abertas
"""

import socket
import ssl
import re
import json
import struct
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ServiceInfo:
    """Informações de um serviço"""
    port: int
    protocol: str
    name: str
    version: str = ""
    product: str = ""
    os_info: str = ""
    banner: str = ""
    cpe: str = ""  # Common Platform Enumeration
    extra_info: Dict[str, Any] = field(default_factory=dict)
    vulnerabilities: List[str] = field(default_factory=list)


class ServiceProbes:
    """Sondas para identificação de serviços"""
    
    # Probes para diferentes serviços
    PROBES = {
        "NULL": b"",
        "GenericLines": b"\r\n\r\n",
        "GetRequest": b"GET / HTTP/1.0\r\n\r\n",
        "HTTPOptions": b"OPTIONS / HTTP/1.0\r\n\r\n",
        "RTSPRequest": b"OPTIONS / RTSP/1.0\r\n\r\n",
        "RPCCheck": b"\x80\x00\x00\x28\x00\x00\x00\x01",
        "DNSVersionBind": b"\x00\x06\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07version\x04bind\x00\x00\x10\x00\x03",
        "DNSStatusRequest": b"\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        "SSLSessionReq": b"\x16\x03\x00\x00S\x01\x00\x00O\x03\x00",
        "SMBProgNeg": b"\x00\x00\x00\x85\xff\x53\x4d\x42\x72\x00\x00\x00\x00\x18\x53\xc8",
        "X11Probe": b"\x6c\x00\x0b\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        "FourOhFourRequest": b"GET /nice404 HTTP/1.0\r\n\r\n",
        "LPDString": b"\x01default\n",
        "LDAPSearchReq": b"\x30\x84\x00\x00\x00\x2d\x02\x01\x07",
        "SIPOptions": b"OPTIONS sip:test@test SIP/2.0\r\nVia: SIP/2.0/UDP test\r\n\r\n",
    }
    
    # Padrões de identificação
    PATTERNS = {
        # HTTP
        r"HTTP/[\d.]+\s+\d+": ("http", "HTTP Server"),
        r"Apache[/\s]+([\d.]+)": ("http", "Apache httpd"),
        r"nginx[/\s]+([\d.]+)": ("http", "nginx"),
        r"Microsoft-IIS[/\s]+([\d.]+)": ("http", "Microsoft IIS"),
        r"Server:\s*([^\r\n]+)": ("http", "HTTP Server"),
        
        # SSH
        r"SSH-([\d.]+)-OpenSSH[_\s]*([\d.p]+)": ("ssh", "OpenSSH"),
        r"SSH-([\d.]+)-dropbear[_\s]*([\d.]+)?": ("ssh", "Dropbear SSH"),
        r"SSH-": ("ssh", "SSH Server"),
        
        # FTP
        r"220[\s-]+.*FTP": ("ftp", "FTP Server"),
        r"220[\s-]+.*FileZilla": ("ftp", "FileZilla FTP"),
        r"220[\s-]+.*vsftpd": ("ftp", "vsftpd"),
        r"220[\s-]+.*ProFTPD": ("ftp", "ProFTPD"),
        
        # SMTP
        r"220[\s-]+.*ESMTP": ("smtp", "SMTP Server"),
        r"220[\s-]+.*Postfix": ("smtp", "Postfix"),
        r"220[\s-]+.*Exim": ("smtp", "Exim"),
        r"220[\s-]+.*Microsoft Exchange": ("smtp", "Microsoft Exchange"),
        
        # MySQL
        r"mysql_native_password": ("mysql", "MySQL"),
        r"MariaDB": ("mysql", "MariaDB"),
        r"[\x00-\x20][\x00-\x10].*mysql": ("mysql", "MySQL"),
        
        # PostgreSQL
        r"PostgreSQL": ("postgresql", "PostgreSQL"),
        
        # Redis
        r"-ERR wrong number of arguments": ("redis", "Redis"),
        r"\+PONG": ("redis", "Redis"),
        r"-NOAUTH": ("redis", "Redis"),
        
        # MongoDB
        r"MongoDB": ("mongodb", "MongoDB"),
        r"ismaster": ("mongodb", "MongoDB"),
        
        # SMB
        r"\x00\x00\x00.\xffSMB": ("smb", "SMB/CIFS"),
        r"Windows": ("smb", "Windows SMB"),
        
        # RDP
        r"\x03\x00\x00": ("rdp", "RDP"),
        
        # VNC
        r"RFB\s+([\d.]+)": ("vnc", "VNC"),
        
        # Telnet
        r"\xff[\xfb\xfc\xfd\xfe]": ("telnet", "Telnet"),
        
        # DNS
        r"BIND\s+([\d.]+)": ("dns", "BIND DNS"),
        
        # LDAP
        r"LDAP": ("ldap", "LDAP Server"),
    }


class ServiceEnumerator:
    """Enumerador de serviços"""
    
    def __init__(self, target: str, timeout: float = 3.0):
        self.target = target
        self.timeout = timeout
        self.results: Dict[int, ServiceInfo] = {}
        
        # Resolver hostname
        try:
            self.ip = socket.gethostbyname(target)
        except socket.gaierror:
            self.ip = target
    
    def enumerate_port(self, port: int) -> Optional[ServiceInfo]:
        """Enumera serviço em uma porta"""
        service = ServiceInfo(port=port, protocol="tcp", name="unknown")
        
        # Primeiro, verifica se a porta está aberta
        if not self._is_port_open(port):
            return None
        
        # Tenta diferentes probes
        banner = self._get_banner(port)
        if banner:
            service.banner = banner
            service = self._identify_service(service, banner)
        
        # Probes específicos baseado na porta
        service = self._specific_probe(service, port)
        
        # Tenta SSL/TLS
        if self._check_ssl(port):
            ssl_info = self._get_ssl_info(port)
            if ssl_info:
                service.extra_info["ssl"] = ssl_info
                if service.name == "unknown":
                    if port == 443:
                        service.name = "https"
                    elif port == 993:
                        service.name = "imaps"
                    elif port == 995:
                        service.name = "pop3s"
                    elif port == 636:
                        service.name = "ldaps"
        
        self.results[port] = service
        return service
    
    def _is_port_open(self, port: int) -> bool:
        """Verifica se porta está aberta"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def _get_banner(self, port: int) -> str:
        """Captura banner do serviço"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.ip, port))
            
            # Primeiro tenta receber sem enviar nada
            sock.settimeout(1.0)
            try:
                banner = sock.recv(2048)
                if banner:
                    sock.close()
                    return banner.decode('utf-8', errors='replace')
            except socket.timeout:
                pass
            
            # Tenta com diferentes probes
            for probe_name, probe_data in ServiceProbes.PROBES.items():
                try:
                    sock.send(probe_data)
                    sock.settimeout(1.0)
                    response = sock.recv(2048)
                    if response:
                        sock.close()
                        return response.decode('utf-8', errors='replace')
                except:
                    continue
            
            sock.close()
        except Exception:
            pass
        
        return ""
    
    def _identify_service(self, service: ServiceInfo, banner: str) -> ServiceInfo:
        """Identifica serviço baseado no banner"""
        for pattern, (name, product) in ServiceProbes.PATTERNS.items():
            match = re.search(pattern, banner, re.IGNORECASE)
            if match:
                service.name = name
                service.product = product
                
                # Tentar extrair versão
                groups = match.groups()
                if groups:
                    service.version = groups[-1] if groups[-1] else ""
                
                break
        
        return service
    
    def _specific_probe(self, service: ServiceInfo, port: int) -> ServiceInfo:
        """Probes específicos por porta"""
        
        # HTTP/HTTPS
        if port in [80, 8080, 8000, 8008, 8888] or service.name == "http":
            http_info = self._probe_http(port)
            if http_info:
                service.extra_info.update(http_info)
                if "server" in http_info:
                    service.product = http_info["server"]
        
        # SSH
        elif port == 22 or service.name == "ssh":
            ssh_info = self._probe_ssh(port)
            if ssh_info:
                service.extra_info.update(ssh_info)
        
        # FTP
        elif port == 21 or service.name == "ftp":
            ftp_info = self._probe_ftp(port)
            if ftp_info:
                service.extra_info.update(ftp_info)
        
        # SMB
        elif port in [139, 445] or service.name == "smb":
            smb_info = self._probe_smb(port)
            if smb_info:
                service.extra_info.update(smb_info)
        
        # MySQL
        elif port == 3306 or service.name == "mysql":
            mysql_info = self._probe_mysql(port)
            if mysql_info:
                service.extra_info.update(mysql_info)
        
        return service
    
    def _probe_http(self, port: int) -> Dict[str, Any]:
        """Probe HTTP detalhado"""
        info = {}
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.ip, port))
            
            request = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {self.target}\r\n"
                f"User-Agent: ServiceEnumerator/1.0\r\n"
                f"Accept: */*\r\n"
                f"Connection: close\r\n\r\n"
            )
            sock.send(request.encode())
            
            response = b""
            while True:
                try:
                    data = sock.recv(4096)
                    if not data:
                        break
                    response += data
                    if len(response) > 8192:
                        break
                except:
                    break
            
            sock.close()
            
            # Parse headers
            response_str = response.decode('utf-8', errors='replace')
            headers = response_str.split('\r\n\r\n')[0]
            
            for line in headers.split('\r\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'server':
                        info['server'] = value
                    elif key == 'x-powered-by':
                        info['powered_by'] = value
                    elif key == 'x-aspnet-version':
                        info['aspnet_version'] = value
                    elif key == 'x-generator':
                        info['generator'] = value
            
            # Extrair título
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', response_str, re.IGNORECASE)
            if title_match:
                info['title'] = title_match.group(1).strip()
            
        except Exception:
            pass
        
        return info
    
    def _probe_ssh(self, port: int) -> Dict[str, Any]:
        """Probe SSH"""
        info = {}
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.ip, port))
            
            banner = sock.recv(1024).decode('utf-8', errors='replace')
            sock.close()
            
            # Parse SSH banner
            if banner.startswith('SSH-'):
                parts = banner.strip().split('-')
                if len(parts) >= 3:
                    info['protocol_version'] = parts[1]
                    info['software'] = '-'.join(parts[2:])
                    
                    # Extrair versão OpenSSH
                    match = re.search(r'OpenSSH[_\s]*([\d.p]+)', banner)
                    if match:
                        info['openssh_version'] = match.group(1)
            
        except Exception:
            pass
        
        return info
    
    def _probe_ftp(self, port: int) -> Dict[str, Any]:
        """Probe FTP"""
        info = {}
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.ip, port))
            
            # Receber banner
            banner = sock.recv(1024).decode('utf-8', errors='replace')
            info['banner'] = banner.strip()
            
            # Tentar login anônimo
            sock.send(b"USER anonymous\r\n")
            response1 = sock.recv(1024).decode('utf-8', errors='replace')
            
            if "331" in response1:  # Password required
                sock.send(b"PASS anonymous@test.com\r\n")
                response2 = sock.recv(1024).decode('utf-8', errors='replace')
                
                if "230" in response2:  # Login successful
                    info['anonymous_login'] = True
                    
                    # Tentar obter mais info
                    sock.send(b"SYST\r\n")
                    syst = sock.recv(1024).decode('utf-8', errors='replace')
                    if "215" in syst:
                        info['system'] = syst.split('\n')[0].strip()
                else:
                    info['anonymous_login'] = False
            
            sock.send(b"QUIT\r\n")
            sock.close()
            
        except Exception:
            pass
        
        return info
    
    def _probe_smb(self, port: int) -> Dict[str, Any]:
        """Probe SMB"""
        info = {}
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.ip, port))
            
            # SMB Negotiate Protocol Request
            negotiate = bytes.fromhex(
                "00000085ff534d4272000000001853c8" +
                "00000000000000000000000000002f4b" +
                "00000000006200025043204e4554574f" +
                "524b2050524f4752414d20312e300002" +
                "4c414e4d414e312e30000253716d6220" +
                "312e30000253716d6220322e30303200" +
                "0253716d6220322e3f3f3f00"
            )
            
            sock.send(negotiate)
            response = sock.recv(1024)
            
            if len(response) > 36:
                info['smb_detected'] = True
                # Tentar extrair info do OS
                if b'Windows' in response:
                    info['os_hint'] = 'Windows'
            
            sock.close()
        except Exception:
            pass
        
        return info
    
    def _probe_mysql(self, port: int) -> Dict[str, Any]:
        """Probe MySQL"""
        info = {}
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.ip, port))
            
            # MySQL envia greeting packet
            greeting = sock.recv(1024)
            sock.close()
            
            if len(greeting) > 5:
                # Parse MySQL protocol
                packet_len = struct.unpack('<I', greeting[:3] + b'\x00')[0]
                if len(greeting) >= packet_len + 4:
                    protocol = greeting[4]
                    
                    # Versão começa após byte de protocolo
                    version_end = greeting.find(b'\x00', 5)
                    if version_end > 5:
                        version = greeting[5:version_end].decode('utf-8', errors='replace')
                        info['version'] = version
                        info['protocol'] = protocol
                        
                        if 'MariaDB' in version:
                            info['product'] = 'MariaDB'
                        else:
                            info['product'] = 'MySQL'
            
        except Exception:
            pass
        
        return info
    
    def _check_ssl(self, port: int) -> bool:
        """Verifica se porta usa SSL/TLS"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.ip, port))
            
            ssl_sock = context.wrap_socket(sock, server_hostname=self.target)
            ssl_sock.close()
            return True
        except:
            return False
    
    def _get_ssl_info(self, port: int) -> Dict[str, Any]:
        """Obtém informações SSL/TLS"""
        info = {}
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.ip, port))
            
            ssl_sock = context.wrap_socket(sock, server_hostname=self.target)
            
            # Informações da conexão
            info['version'] = ssl_sock.version()
            info['cipher'] = ssl_sock.cipher()
            
            # Certificado
            cert = ssl_sock.getpeercert(binary_form=False)
            if cert:
                info['subject'] = dict(x[0] for x in cert.get('subject', []))
                info['issuer'] = dict(x[0] for x in cert.get('issuer', []))
                info['not_before'] = cert.get('notBefore')
                info['not_after'] = cert.get('notAfter')
                info['serial'] = cert.get('serialNumber')
            
            ssl_sock.close()
        except Exception:
            pass
        
        return info
    
    def enumerate_ports(self, ports: List[int], threads: int = 10) -> Dict[int, ServiceInfo]:
        """Enumera múltiplas portas"""
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(self.enumerate_port, port): port for port in ports}
            
            for future in as_completed(futures):
                port = futures[future]
                try:
                    result = future.result()
                except Exception:
                    pass
        
        return self.results


def print_banner():
    """Exibe banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                   📡 SERVICE ENUMERATOR                          ║
║                     Olho de Deus v2.0                            ║
╠══════════════════════════════════════════════════════════════════╣
║  Identificação avançada de serviços com probes específicos       ║
║  Features: Banner Grabbing | SSL/TLS | Service Detection         ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_service_info(service: ServiceInfo):
    """Exibe informações de um serviço"""
    print(f"\n📍 Porta {service.port}/{service.protocol}")
    print("-" * 50)
    print(f"   Serviço: {service.name}")
    if service.product:
        print(f"   Produto: {service.product}")
    if service.version:
        print(f"   Versão: {service.version}")
    if service.banner:
        print(f"   Banner: {service.banner[:100]}...")
    
    if service.extra_info:
        print("   Informações extras:")
        for key, value in service.extra_info.items():
            if isinstance(value, dict):
                print(f"      {key}:")
                for k, v in value.items():
                    print(f"         {k}: {v}")
            else:
                print(f"      {key}: {value}")


def interactive_menu():
    """Menu interativo"""
    print_banner()
    
    while True:
        print("\n📋 MENU")
        print("-" * 40)
        print("[1] 🔍 Enumerar porta específica")
        print("[2] 📊 Enumerar múltiplas portas")
        print("[3] 🚀 Enumerar portas comuns")
        print("[4] 🌐 Enumerar com scan integrado")
        print("[0] ❌ Voltar")
        
        choice = input("\n🔹 Escolha: ").strip()
        
        if choice == "0":
            break
        
        elif choice == "1":
            target = input("🎯 Alvo (IP/hostname): ").strip()
            port = input("🔢 Porta: ").strip()
            
            if not target or not port:
                print("❌ Dados inválidos!")
                continue
            
            enum = ServiceEnumerator(target, 5.0)
            print(f"\n🔍 Enumerando porta {port} em {target}...")
            
            result = enum.enumerate_port(int(port))
            if result:
                print_service_info(result)
            else:
                print(f"\n❌ Porta {port} fechada ou filtrada")
        
        elif choice == "2":
            target = input("🎯 Alvo (IP/hostname): ").strip()
            ports_str = input("🔢 Portas (ex: 22,80,443,8080): ").strip()
            
            if not target or not ports_str:
                print("❌ Dados inválidos!")
                continue
            
            ports = [int(p.strip()) for p in ports_str.split(',')]
            
            enum = ServiceEnumerator(target, 5.0)
            print(f"\n🔍 Enumerando {len(ports)} portas em {target}...")
            
            results = enum.enumerate_ports(ports)
            
            if results:
                print(f"\n✅ {len(results)} serviços encontrados:")
                for port, service in sorted(results.items()):
                    print_service_info(service)
            else:
                print("\n❌ Nenhum serviço encontrado")
        
        elif choice == "3":
            target = input("🎯 Alvo (IP/hostname): ").strip()
            
            if not target:
                print("❌ Alvo inválido!")
                continue
            
            common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 
                          1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 27017]
            
            enum = ServiceEnumerator(target, 3.0)
            print(f"\n🔍 Enumerando portas comuns em {target}...")
            
            results = enum.enumerate_ports(common_ports, threads=10)
            
            if results:
                print(f"\n✅ {len(results)} serviços encontrados:")
                for port, service in sorted(results.items()):
                    print_service_info(service)
            else:
                print("\n❌ Nenhum serviço encontrado")
        
        elif choice == "4":
            target = input("🎯 Alvo (IP/hostname): ").strip()
            port_range = input("🔢 Range (ex: 1-1000): ").strip() or "1-1000"
            
            if not target:
                print("❌ Alvo inválido!")
                continue
            
            # Parse range
            if '-' in port_range:
                start, end = port_range.split('-')
                ports = list(range(int(start), int(end) + 1))
            else:
                ports = [int(p.strip()) for p in port_range.split(',')]
            
            # Primeiro faz port scan básico
            print(f"\n🔍 Fase 1: Scan de portas...")
            open_ports = []
            
            import socket
            for port in ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    result = sock.connect_ex((socket.gethostbyname(target), port))
                    sock.close()
                    if result == 0:
                        open_ports.append(port)
                        print(f"   ✅ Porta {port} aberta")
                except:
                    pass
            
            if open_ports:
                print(f"\n🔍 Fase 2: Enumeração de {len(open_ports)} serviços...")
                enum = ServiceEnumerator(target, 5.0)
                results = enum.enumerate_ports(open_ports, threads=5)
                
                for port, service in sorted(results.items()):
                    print_service_info(service)
            else:
                print("\n❌ Nenhuma porta aberta encontrada")
        
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
