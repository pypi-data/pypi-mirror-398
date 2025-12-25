#!/usr/bin/env python3
"""
Port Scanner Avançado - Olho de Deus
Scanner de portas TCP/UDP com múltiplos métodos de scan
"""

import socket
import threading
import queue
import time
import struct
import random
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

# Adicionar path para imports locais
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from tools.utilities.progress_bar import ProgressBar, Spinner
except ImportError:
    ProgressBar = None
    Spinner = None


@dataclass
class PortResult:
    """Resultado de scan de porta"""
    port: int
    state: str  # open, closed, filtered
    protocol: str  # tcp, udp
    service: str = ""
    banner: str = ""
    response_time: float = 0.0


@dataclass
class ScanResult:
    """Resultado completo de um scan"""
    target: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    ports: List[PortResult] = field(default_factory=list)
    scan_type: str = "tcp_connect"
    total_ports: int = 0
    open_ports: int = 0
    
    def duration(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


class ServiceDatabase:
    """Banco de dados de serviços conhecidos"""
    
    COMMON_SERVICES = {
        21: ("FTP", "File Transfer Protocol"),
        22: ("SSH", "Secure Shell"),
        23: ("Telnet", "Telnet Protocol"),
        25: ("SMTP", "Simple Mail Transfer Protocol"),
        53: ("DNS", "Domain Name System"),
        67: ("DHCP", "Dynamic Host Configuration"),
        68: ("DHCP", "Dynamic Host Configuration"),
        69: ("TFTP", "Trivial File Transfer Protocol"),
        80: ("HTTP", "Hypertext Transfer Protocol"),
        110: ("POP3", "Post Office Protocol v3"),
        111: ("RPC", "Remote Procedure Call"),
        123: ("NTP", "Network Time Protocol"),
        135: ("MSRPC", "Microsoft RPC"),
        137: ("NetBIOS-NS", "NetBIOS Name Service"),
        138: ("NetBIOS-DGM", "NetBIOS Datagram"),
        139: ("NetBIOS-SSN", "NetBIOS Session"),
        143: ("IMAP", "Internet Message Access Protocol"),
        161: ("SNMP", "Simple Network Management Protocol"),
        162: ("SNMP-TRAP", "SNMP Trap"),
        389: ("LDAP", "Lightweight Directory Access Protocol"),
        443: ("HTTPS", "HTTP Secure"),
        445: ("SMB", "Server Message Block"),
        465: ("SMTPS", "SMTP Secure"),
        500: ("IKE", "Internet Key Exchange"),
        514: ("Syslog", "System Logging"),
        515: ("LPD", "Line Printer Daemon"),
        520: ("RIP", "Routing Information Protocol"),
        587: ("SMTP", "SMTP Submission"),
        631: ("IPP", "Internet Printing Protocol"),
        636: ("LDAPS", "LDAP Secure"),
        993: ("IMAPS", "IMAP Secure"),
        995: ("POP3S", "POP3 Secure"),
        1080: ("SOCKS", "SOCKS Proxy"),
        1433: ("MSSQL", "Microsoft SQL Server"),
        1434: ("MSSQL-UDP", "MSSQL Browser"),
        1521: ("Oracle", "Oracle Database"),
        1723: ("PPTP", "Point-to-Point Tunneling"),
        2049: ("NFS", "Network File System"),
        3306: ("MySQL", "MySQL Database"),
        3389: ("RDP", "Remote Desktop Protocol"),
        3690: ("SVN", "Subversion"),
        4444: ("Metasploit", "Metasploit Default"),
        5432: ("PostgreSQL", "PostgreSQL Database"),
        5900: ("VNC", "Virtual Network Computing"),
        5901: ("VNC-1", "VNC Display :1"),
        5902: ("VNC-2", "VNC Display :2"),
        5984: ("CouchDB", "CouchDB Database"),
        6379: ("Redis", "Redis Database"),
        6667: ("IRC", "Internet Relay Chat"),
        8000: ("HTTP-Alt", "HTTP Alternative"),
        8008: ("HTTP-Alt", "HTTP Alternative"),
        8080: ("HTTP-Proxy", "HTTP Proxy"),
        8443: ("HTTPS-Alt", "HTTPS Alternative"),
        8888: ("HTTP-Alt", "HTTP Alternative"),
        9000: ("PHP-FPM", "PHP FastCGI Process Manager"),
        9200: ("Elasticsearch", "Elasticsearch"),
        9300: ("Elasticsearch", "Elasticsearch Cluster"),
        9418: ("Git", "Git Protocol"),
        11211: ("Memcached", "Memcached"),
        27017: ("MongoDB", "MongoDB Database"),
        27018: ("MongoDB", "MongoDB Shard"),
        28017: ("MongoDB", "MongoDB Web Interface"),
    }
    
    # Portas para scans específicos
    TOP_100_PORTS = [
        7, 9, 13, 21, 22, 23, 25, 26, 37, 53, 79, 80, 81, 82, 83, 84, 85, 88, 89,
        90, 99, 100, 106, 110, 111, 113, 119, 135, 139, 143, 144, 179, 199, 211,
        212, 222, 254, 255, 256, 259, 264, 280, 301, 306, 311, 340, 366, 389, 406,
        407, 416, 417, 425, 427, 443, 444, 445, 458, 464, 465, 481, 497, 500, 512,
        513, 514, 515, 524, 541, 543, 544, 545, 548, 554, 555, 563, 587, 593, 616,
        617, 625, 631, 636, 646, 648, 666, 667, 668, 683, 687, 691, 700, 705, 711,
        714, 720, 722, 726, 749
    ]
    
    TOP_1000_PORTS = TOP_100_PORTS + list(range(750, 1000)) + [
        1000, 1024, 1025, 1026, 1027, 1028, 1029, 1030, 1110, 1433, 1434, 1521,
        1720, 1723, 1755, 1900, 2000, 2001, 2049, 2121, 2717, 3000, 3128, 3306,
        3389, 3986, 4899, 5000, 5009, 5051, 5060, 5101, 5190, 5357, 5432, 5631,
        5666, 5800, 5900, 5901, 6000, 6001, 6379, 6646, 7000, 7070, 8000, 8008,
        8009, 8080, 8081, 8443, 8888, 9000, 9001, 9090, 9100, 9200, 10000, 32768
    ]
    
    @classmethod
    def get_service(cls, port: int) -> Tuple[str, str]:
        """Retorna nome e descrição do serviço"""
        return cls.COMMON_SERVICES.get(port, ("unknown", "Unknown Service"))


class PortScanner:
    """Scanner de portas avançado"""
    
    def __init__(self, target: str, timeout: float = 1.0, threads: int = 100):
        self.target = target
        self.timeout = timeout
        self.threads = threads
        self.results: List[PortResult] = []
        self.lock = threading.Lock()
        self.stop_flag = threading.Event()
        
        # Resolver hostname
        try:
            self.ip = socket.gethostbyname(target)
        except socket.gaierror:
            self.ip = target
    
    def tcp_connect_scan(self, port: int) -> PortResult:
        """TCP Connect Scan - Mais rápido, mais detectável"""
        start = time.time()
        result = PortResult(port=port, protocol="tcp", state="filtered")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            error = sock.connect_ex((self.ip, port))
            response_time = time.time() - start
            
            if error == 0:
                result.state = "open"
                result.response_time = response_time
                service_name, _ = ServiceDatabase.get_service(port)
                result.service = service_name
                
                # Tentar pegar banner
                try:
                    sock.settimeout(0.5)
                    sock.send(b"\r\n\r\n")
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                    if banner:
                        result.banner = banner[:200]
                except:
                    pass
            else:
                result.state = "closed"
            
            sock.close()
        except socket.timeout:
            result.state = "filtered"
        except Exception:
            result.state = "filtered"
        
        return result
    
    def syn_scan(self, port: int) -> PortResult:
        """
        SYN Scan (Half-open) - Requer privilégios de root/admin
        Nota: Implementação simplificada para demonstração
        """
        # Em Windows, precisa de bibliotecas especiais (scapy)
        # Fallback para TCP Connect
        return self.tcp_connect_scan(port)
    
    def udp_scan(self, port: int) -> PortResult:
        """UDP Scan - Mais lento, menos confiável"""
        start = time.time()
        result = PortResult(port=port, protocol="udp", state="open|filtered")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            
            # Enviar pacote vazio
            sock.sendto(b"", (self.ip, port))
            
            try:
                data, _ = sock.recvfrom(1024)
                result.state = "open"
                result.response_time = time.time() - start
                result.banner = data.decode('utf-8', errors='ignore')[:100]
            except socket.timeout:
                # Sem resposta = open|filtered (comportamento normal UDP)
                result.state = "open|filtered"
            
            sock.close()
        except socket.error as e:
            # ICMP port unreachable = closed
            if "unreachable" in str(e).lower():
                result.state = "closed"
            else:
                result.state = "open|filtered"
        except Exception:
            result.state = "filtered"
        
        return result
    
    def xmas_scan(self, port: int) -> PortResult:
        """XMAS Scan - Envia pacotes com flags FIN, PSH, URG"""
        # Requer raw sockets - fallback para connect
        return self.tcp_connect_scan(port)
    
    def null_scan(self, port: int) -> PortResult:
        """NULL Scan - Envia pacotes sem flags"""
        # Requer raw sockets - fallback para connect
        return self.tcp_connect_scan(port)
    
    def fin_scan(self, port: int) -> PortResult:
        """FIN Scan - Envia apenas flag FIN"""
        # Requer raw sockets - fallback para connect
        return self.tcp_connect_scan(port)
    
    def scan_port(self, port: int, scan_type: str = "tcp") -> Optional[PortResult]:
        """Escaneia uma porta específica"""
        if self.stop_flag.is_set():
            return None
        
        if scan_type == "tcp" or scan_type == "connect":
            return self.tcp_connect_scan(port)
        elif scan_type == "syn":
            return self.syn_scan(port)
        elif scan_type == "udp":
            return self.udp_scan(port)
        elif scan_type == "xmas":
            return self.xmas_scan(port)
        elif scan_type == "null":
            return self.null_scan(port)
        elif scan_type == "fin":
            return self.fin_scan(port)
        else:
            return self.tcp_connect_scan(port)
    
    def scan(self, ports: List[int], scan_type: str = "tcp", 
             callback=None, show_progress: bool = True) -> ScanResult:
        """Executa scan em múltiplas portas"""
        result = ScanResult(
            target=self.target,
            scan_type=scan_type,
            total_ports=len(ports)
        )
        
        # Randomizar ordem das portas para evasão
        shuffled_ports = ports.copy()
        random.shuffle(shuffled_ports)
        
        # Criar barra de progresso (usa estilo configurado pelo usuário)
        pbar = None
        if show_progress and ProgressBar:
            pbar = ProgressBar(
                len(ports),
                "   Scanning",
                show_percentage=True,
                show_speed=True,
                show_eta=True
            )
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {
                executor.submit(self.scan_port, port, scan_type): port 
                for port in shuffled_ports
            }
            
            completed = 0
            for future in as_completed(futures):
                if self.stop_flag.is_set():
                    break
                
                port_result = future.result()
                if port_result:
                    with self.lock:
                        result.ports.append(port_result)
                    if port_result.state == "open":
                        result.open_ports += 1
                
                completed += 1
                if pbar:
                    pbar.set(completed)
                elif show_progress and completed % 100 == 0:
                    print(f"\r   Progresso: {completed}/{len(ports)}", end="", flush=True)
                
                if callback:
                    callback(completed, len(ports))
        
        # Finalizar barra de progresso
        if pbar:
            pbar.finish()
        
        result.end_time = datetime.now()
        result.ports.sort(key=lambda x: x.port)
        return result
    
    def quick_scan(self, callback=None) -> ScanResult:
        """Scan rápido - Top 100 portas"""
        return self.scan(ServiceDatabase.TOP_100_PORTS, "tcp", callback)
    
    def full_scan(self, callback=None) -> ScanResult:
        """Scan completo - Todas as 65535 portas"""
        return self.scan(list(range(1, 65536)), "tcp", callback)
    
    def common_scan(self, callback=None) -> ScanResult:
        """Scan comum - Top 1000 portas"""
        return self.scan(ServiceDatabase.TOP_1000_PORTS, "tcp", callback)
    
    def custom_scan(self, port_range: str, callback=None) -> ScanResult:
        """Scan customizado - Range de portas"""
        ports = self._parse_port_range(port_range)
        return self.scan(ports, "tcp", callback)
    
    def _parse_port_range(self, port_range: str) -> List[int]:
        """Parse de range de portas (ex: 1-100,443,8080-8090)"""
        ports = []
        for part in port_range.split(','):
            part = part.strip()
            if '-' in part:
                start, end = part.split('-')
                ports.extend(range(int(start), int(end) + 1))
            else:
                ports.append(int(part))
        return sorted(set(ports))
    
    def stop(self):
        """Para o scan"""
        self.stop_flag.set()


class ServiceProbe:
    """Sondagem de serviços para identificação"""
    
    PROBES = {
        "http": b"GET / HTTP/1.0\r\nHost: target\r\n\r\n",
        "https": b"GET / HTTP/1.0\r\nHost: target\r\n\r\n",
        "ftp": b"USER anonymous\r\n",
        "smtp": b"EHLO test\r\n",
        "ssh": b"SSH-2.0-OpenSSH_8.0\r\n",
        "mysql": b"\x00\x00\x00\x00",
        "redis": b"*1\r\n$4\r\nPING\r\n",
    }
    
    @classmethod
    def probe(cls, ip: str, port: int, timeout: float = 2.0) -> str:
        """Sonda porta para identificar serviço"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            
            # Primeiro tenta receber banner
            sock.settimeout(0.5)
            try:
                banner = sock.recv(1024)
                if banner:
                    return banner.decode('utf-8', errors='ignore')[:200]
            except socket.timeout:
                pass
            
            # Tenta probes específicos
            for service, probe in cls.PROBES.items():
                try:
                    sock.send(probe)
                    sock.settimeout(0.5)
                    response = sock.recv(1024)
                    if response:
                        sock.close()
                        return f"[{service}] {response.decode('utf-8', errors='ignore')[:150]}"
                except:
                    pass
            
            sock.close()
        except Exception:
            pass
        
        return ""


def print_banner():
    """Exibe banner da ferramenta"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                     🔍 PORT SCANNER AVANÇADO                      ║
║                        Olho de Deus v2.0                          ║
╠══════════════════════════════════════════════════════════════════╣
║  Métodos: TCP Connect | SYN | UDP | XMAS | NULL | FIN            ║
║  Features: Multi-thread | Banner Grabbing | Service Detection    ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_results(result: ScanResult):
    """Exibe resultados do scan"""
    print("\n" + "=" * 70)
    print(f"📊 RESULTADOS DO SCAN")
    print("=" * 70)
    print(f"🎯 Alvo: {result.target}")
    print(f"⏱️  Duração: {result.duration():.2f}s")
    print(f"🔍 Tipo: {result.scan_type.upper()}")
    print(f"📈 Portas scaneadas: {result.total_ports}")
    print(f"✅ Portas abertas: {result.open_ports}")
    print("-" * 70)
    
    open_ports = [p for p in result.ports if p.state == "open"]
    
    if open_ports:
        print(f"\n{'PORTA':<10}{'ESTADO':<12}{'SERVIÇO':<15}{'TEMPO':<10}BANNER")
        print("-" * 70)
        for port in open_ports:
            print(f"{port.port:<10}{port.state:<12}{port.service:<15}{port.response_time*1000:.0f}ms")
            if port.banner:
                print(f"    └─ {port.banner[:60]}")
    else:
        print("\n⚠️ Nenhuma porta aberta encontrada.")
    
    print("=" * 70)


def progress_callback(current: int, total: int):
    """Callback de progresso"""
    percent = (current / total) * 100
    bar_length = 40
    filled = int(bar_length * current / total)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\r⏳ Progresso: [{bar}] {percent:.1f}% ({current}/{total})", end="", flush=True)


def interactive_menu():
    """Menu interativo do Port Scanner"""
    print_banner()
    
    while True:
        print("\n📋 MENU PRINCIPAL")
        print("-" * 40)
        print("[1] 🚀 Quick Scan (Top 100 portas)")
        print("[2] 📊 Common Scan (Top 1000 portas)")
        print("[3] 🔥 Full Scan (Todas as 65535 portas)")
        print("[4] 🎯 Custom Scan (Range específico)")
        print("[5] 📡 UDP Scan")
        print("[6] 🔍 Scan com probe de serviços")
        print("[7] 📖 Listar serviços conhecidos")
        print("[0] ❌ Voltar")
        
        choice = input("\n🔹 Escolha: ").strip()
        
        if choice == "0":
            print("👋 Saindo...")
            break
        
        elif choice == "1":
            target = input("🎯 Alvo (IP/hostname): ").strip()
            if not target:
                print("❌ Alvo inválido!")
                continue
            
            threads = input("⚡ Threads [100]: ").strip() or "100"
            timeout = input("⏱️ Timeout (seg) [1.0]: ").strip() or "1.0"
            
            scanner = PortScanner(target, float(timeout), int(threads))
            print(f"\n🔍 Iniciando Quick Scan em {target}...")
            print(f"   IP resolvido: {scanner.ip}")
            
            result = scanner.quick_scan(progress_callback)
            print()  # Nova linha após progress bar
            print_results(result)
        
        elif choice == "2":
            target = input("🎯 Alvo (IP/hostname): ").strip()
            if not target:
                print("❌ Alvo inválido!")
                continue
            
            threads = input("⚡ Threads [100]: ").strip() or "100"
            
            scanner = PortScanner(target, 1.0, int(threads))
            print(f"\n🔍 Iniciando Common Scan em {target}...")
            
            result = scanner.common_scan(progress_callback)
            print()
            print_results(result)
        
        elif choice == "3":
            target = input("🎯 Alvo (IP/hostname): ").strip()
            if not target:
                print("❌ Alvo inválido!")
                continue
            
            print("\n⚠️ AVISO: Full Scan pode levar vários minutos!")
            confirm = input("📌 Confirmar? (s/n): ").strip().lower()
            if confirm != 's':
                continue
            
            threads = input("⚡ Threads [200]: ").strip() or "200"
            
            scanner = PortScanner(target, 0.5, int(threads))
            print(f"\n🔍 Iniciando Full Scan em {target}...")
            
            result = scanner.full_scan(progress_callback)
            print()
            print_results(result)
        
        elif choice == "4":
            target = input("🎯 Alvo (IP/hostname): ").strip()
            if not target:
                print("❌ Alvo inválido!")
                continue
            
            print("\n📌 Exemplos de range:")
            print("   • 1-1000 (portas 1 a 1000)")
            print("   • 80,443,8080 (portas específicas)")
            print("   • 1-100,443,8000-9000 (combinação)")
            
            port_range = input("🔢 Range de portas: ").strip()
            if not port_range:
                print("❌ Range inválido!")
                continue
            
            threads = input("⚡ Threads [100]: ").strip() or "100"
            
            scanner = PortScanner(target, 1.0, int(threads))
            print(f"\n🔍 Iniciando Custom Scan em {target}...")
            
            result = scanner.custom_scan(port_range, progress_callback)
            print()
            print_results(result)
        
        elif choice == "5":
            target = input("🎯 Alvo (IP/hostname): ").strip()
            if not target:
                print("❌ Alvo inválido!")
                continue
            
            print("\n⚠️ UDP Scan é mais lento e menos confiável!")
            port_range = input("🔢 Portas (ex: 53,67,68,123,161) [Top 20 UDP]: ").strip()
            
            if not port_range:
                port_range = "53,67,68,69,123,135,137,138,139,161,162,389,445,500,514,520,631,1434,1900,5353"
            
            scanner = PortScanner(target, 2.0, 20)
            ports = scanner._parse_port_range(port_range)
            
            print(f"\n🔍 Iniciando UDP Scan em {target}...")
            result = scanner.scan(ports, "udp", progress_callback)
            print()
            print_results(result)
        
        elif choice == "6":
            target = input("🎯 Alvo (IP/hostname): ").strip()
            if not target:
                print("❌ Alvo inválido!")
                continue
            
            port_range = input("🔢 Portas para probe (ex: 80,443,22): ").strip()
            if not port_range:
                print("❌ Range inválido!")
                continue
            
            scanner = PortScanner(target, 2.0, 50)
            ports = scanner._parse_port_range(port_range)
            
            print(f"\n🔍 Probing {len(ports)} portas em {target}...")
            
            for port in ports:
                result = scanner.tcp_connect_scan(port)
                if result.state == "open":
                    print(f"\n✅ Porta {port}: OPEN")
                    print(f"   Serviço: {result.service}")
                    
                    # Probe adicional
                    probe_result = ServiceProbe.probe(scanner.ip, port)
                    if probe_result:
                        print(f"   Banner: {probe_result[:100]}")
        
        elif choice == "7":
            print("\n📖 SERVIÇOS CONHECIDOS")
            print("-" * 50)
            for port, (name, desc) in sorted(ServiceDatabase.COMMON_SERVICES.items()):
                print(f"  {port:>5} - {name:<15} ({desc})")
        
        else:
            print("❌ Opção inválida!")
        
        input("\n⏎ Pressione ENTER para continuar...")


if __name__ == "__main__":
    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Scan cancelado pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
