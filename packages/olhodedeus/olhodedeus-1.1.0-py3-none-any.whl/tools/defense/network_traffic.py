#!/usr/bin/env python3
"""
Network Traffic Analyzer - Análise de tráfego de rede
Parte do toolkit Olho de Deus
"""

import os
import sys
import re
import json
import socket
import struct
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import Counter, defaultdict
from pathlib import Path


@dataclass
class PacketInfo:
    """Informações de pacote."""
    timestamp: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    length: int
    flags: str
    payload: Optional[bytes]
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "protocol": self.protocol,
            "length": self.length,
            "flags": self.flags
        }


@dataclass
class ConnectionInfo:
    """Informações de conexão."""
    src_ip: str
    src_port: int
    dst_ip: str
    dst_port: int
    protocol: str
    state: str
    bytes_sent: int
    bytes_recv: int
    packets: int
    duration: float
    
    def to_dict(self) -> Dict:
        return {
            "src_ip": self.src_ip,
            "src_port": self.src_port,
            "dst_ip": self.dst_ip,
            "dst_port": self.dst_port,
            "protocol": self.protocol,
            "state": self.state,
            "bytes_sent": self.bytes_sent,
            "bytes_recv": self.bytes_recv,
            "packets": self.packets,
            "duration": self.duration
        }


@dataclass
class TrafficAnomaly:
    """Anomalia de tráfego detectada."""
    anomaly_type: str
    severity: str
    description: str
    source: str
    destination: str
    evidence: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "description": self.description,
            "source": self.source,
            "destination": self.destination,
            "evidence": self.evidence
        }


class ProtocolDB:
    """Database de protocolos e portas."""
    
    COMMON_PORTS = {
        20: ("FTP Data", "tcp"),
        21: ("FTP Control", "tcp"),
        22: ("SSH", "tcp"),
        23: ("Telnet", "tcp"),
        25: ("SMTP", "tcp"),
        53: ("DNS", "udp/tcp"),
        67: ("DHCP Server", "udp"),
        68: ("DHCP Client", "udp"),
        80: ("HTTP", "tcp"),
        110: ("POP3", "tcp"),
        123: ("NTP", "udp"),
        137: ("NetBIOS Name", "udp"),
        138: ("NetBIOS Datagram", "udp"),
        139: ("NetBIOS Session", "tcp"),
        143: ("IMAP", "tcp"),
        161: ("SNMP", "udp"),
        162: ("SNMP Trap", "udp"),
        389: ("LDAP", "tcp"),
        443: ("HTTPS", "tcp"),
        445: ("SMB", "tcp"),
        465: ("SMTPS", "tcp"),
        514: ("Syslog", "udp"),
        587: ("SMTP Submission", "tcp"),
        636: ("LDAPS", "tcp"),
        993: ("IMAPS", "tcp"),
        995: ("POP3S", "tcp"),
        1433: ("MSSQL", "tcp"),
        1521: ("Oracle", "tcp"),
        3306: ("MySQL", "tcp"),
        3389: ("RDP", "tcp"),
        5432: ("PostgreSQL", "tcp"),
        5900: ("VNC", "tcp"),
        6379: ("Redis", "tcp"),
        8080: ("HTTP Alt", "tcp"),
        8443: ("HTTPS Alt", "tcp"),
        27017: ("MongoDB", "tcp"),
    }
    
    MALICIOUS_PORTS = {
        4444: "Metasploit default",
        5555: "Android ADB",
        6666: "IRC (possible botnet)",
        6667: "IRC",
        31337: "Back Orifice",
        12345: "NetBus",
        1234: "Common malware",
        9001: "Tor default",
    }
    
    PROTOCOL_NUMBERS = {
        1: "ICMP",
        6: "TCP",
        17: "UDP",
        47: "GRE",
        50: "ESP",
        51: "AH",
    }
    
    @classmethod
    def get_service(cls, port: int) -> Optional[str]:
        """Retorna nome do serviço pela porta."""
        if port in cls.COMMON_PORTS:
            return cls.COMMON_PORTS[port][0]
        return None
    
    @classmethod
    def is_malicious_port(cls, port: int) -> Optional[str]:
        """Verifica se é porta associada a malware."""
        return cls.MALICIOUS_PORTS.get(port)


class PcapParser:
    """Parser básico de arquivos PCAP."""
    
    PCAP_MAGIC = b'\xa1\xb2\xc3\xd4'
    PCAP_MAGIC_SWAPPED = b'\xd4\xc3\xb2\xa1'
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.packets = []
    
    def parse(self) -> List[PacketInfo]:
        """Parse arquivo PCAP."""
        try:
            with open(self.file_path, 'rb') as f:
                # Ler global header
                header = f.read(24)
                if len(header) < 24:
                    return []
                
                magic = header[:4]
                if magic not in [self.PCAP_MAGIC, self.PCAP_MAGIC_SWAPPED]:
                    print("Formato PCAP não reconhecido")
                    return []
                
                swapped = magic == self.PCAP_MAGIC_SWAPPED
                
                # Ler pacotes
                while True:
                    packet_header = f.read(16)
                    if len(packet_header) < 16:
                        break
                    
                    if swapped:
                        ts_sec, ts_usec, incl_len, orig_len = struct.unpack('<IIII', packet_header)
                    else:
                        ts_sec, ts_usec, incl_len, orig_len = struct.unpack('>IIII', packet_header)
                    
                    packet_data = f.read(incl_len)
                    if len(packet_data) < incl_len:
                        break
                    
                    packet = self._parse_packet(packet_data, ts_sec)
                    if packet:
                        self.packets.append(packet)
                
                return self.packets
        except Exception as e:
            print(f"Erro ao parsear PCAP: {e}")
            return []
    
    def _parse_packet(self, data: bytes, timestamp: int) -> Optional[PacketInfo]:
        """Parse um pacote individual."""
        try:
            # Ethernet header (14 bytes)
            if len(data) < 14:
                return None
            
            eth_type = struct.unpack('!H', data[12:14])[0]
            
            # IPv4 (0x0800)
            if eth_type != 0x0800:
                return None
            
            # IP header
            ip_data = data[14:]
            if len(ip_data) < 20:
                return None
            
            ip_header = ip_data[:20]
            ihl = (ip_header[0] & 0x0F) * 4
            total_length = struct.unpack('!H', ip_header[2:4])[0]
            protocol = ip_header[9]
            src_ip = socket.inet_ntoa(ip_header[12:16])
            dst_ip = socket.inet_ntoa(ip_header[16:20])
            
            src_port = 0
            dst_port = 0
            flags = ""
            
            # TCP (6)
            if protocol == 6 and len(ip_data) >= ihl + 20:
                tcp_header = ip_data[ihl:ihl + 20]
                src_port = struct.unpack('!H', tcp_header[0:2])[0]
                dst_port = struct.unpack('!H', tcp_header[2:4])[0]
                
                tcp_flags = tcp_header[13]
                if tcp_flags & 0x01:
                    flags += "F"
                if tcp_flags & 0x02:
                    flags += "S"
                if tcp_flags & 0x04:
                    flags += "R"
                if tcp_flags & 0x08:
                    flags += "P"
                if tcp_flags & 0x10:
                    flags += "A"
            
            # UDP (17)
            elif protocol == 17 and len(ip_data) >= ihl + 8:
                udp_header = ip_data[ihl:ihl + 8]
                src_port = struct.unpack('!H', udp_header[0:2])[0]
                dst_port = struct.unpack('!H', udp_header[2:4])[0]
            
            proto_name = ProtocolDB.PROTOCOL_NUMBERS.get(protocol, str(protocol))
            
            return PacketInfo(
                timestamp=datetime.fromtimestamp(timestamp).isoformat(),
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                protocol=proto_name,
                length=total_length,
                flags=flags,
                payload=None
            )
        except Exception:
            return None


class NetstatParser:
    """Parser de saída do netstat."""
    
    NETSTAT_PATTERN = re.compile(
        r'^\s*(TCP|UDP)\s+(\S+):(\d+)\s+(\S+):(\d+)\s+(\w+)?',
        re.IGNORECASE
    )
    
    @classmethod
    def parse_netstat_output(cls, output: str) -> List[ConnectionInfo]:
        """Parse saída do netstat."""
        connections = []
        
        for line in output.splitlines():
            match = cls.NETSTAT_PATTERN.match(line)
            if match:
                proto = match.group(1).upper()
                src_addr = match.group(2)
                src_port = int(match.group(3))
                dst_addr = match.group(4)
                dst_port = int(match.group(5))
                state = match.group(6) if match.group(6) else ""
                
                connections.append(ConnectionInfo(
                    src_ip=src_addr,
                    src_port=src_port,
                    dst_ip=dst_addr,
                    dst_port=dst_port,
                    protocol=proto,
                    state=state,
                    bytes_sent=0,
                    bytes_recv=0,
                    packets=0,
                    duration=0.0
                ))
        
        return connections


class TrafficAnalyzer:
    """Analisador de tráfego de rede."""
    
    def __init__(self):
        self.packets = []
        self.connections = []
        self.anomalies = []
    
    def analyze_pcap(self, file_path: str) -> Dict:
        """Analisa arquivo PCAP."""
        parser = PcapParser(file_path)
        self.packets = parser.parse()
        
        if not self.packets:
            return {"error": "Nenhum pacote encontrado ou formato inválido"}
        
        stats = self._calculate_stats()
        anomalies = self._detect_anomalies()
        
        return {
            "file": file_path,
            "total_packets": len(self.packets),
            "stats": stats,
            "anomalies": [a.to_dict() for a in anomalies]
        }
    
    def _calculate_stats(self) -> Dict:
        """Calcula estatísticas do tráfego."""
        stats = {
            "protocols": Counter(),
            "src_ips": Counter(),
            "dst_ips": Counter(),
            "src_ports": Counter(),
            "dst_ports": Counter(),
            "total_bytes": 0,
            "services": Counter(),
        }
        
        for packet in self.packets:
            stats["protocols"][packet.protocol] += 1
            stats["src_ips"][packet.src_ip] += 1
            stats["dst_ips"][packet.dst_ip] += 1
            stats["src_ports"][packet.src_port] += 1
            stats["dst_ports"][packet.dst_port] += 1
            stats["total_bytes"] += packet.length
            
            service = ProtocolDB.get_service(packet.dst_port)
            if service:
                stats["services"][service] += 1
        
        return {
            "protocols": dict(stats["protocols"]),
            "top_talkers": dict(stats["src_ips"].most_common(10)),
            "top_destinations": dict(stats["dst_ips"].most_common(10)),
            "top_services": dict(stats["services"].most_common(10)),
            "total_bytes": stats["total_bytes"],
        }
    
    def _detect_anomalies(self) -> List[TrafficAnomaly]:
        """Detecta anomalias no tráfego."""
        anomalies = []
        
        # Detectar scan de portas
        port_scan_threshold = 20
        src_ports_by_ip = defaultdict(set)
        
        for packet in self.packets:
            src_ports_by_ip[packet.src_ip].add(packet.dst_port)
        
        for ip, ports in src_ports_by_ip.items():
            if len(ports) >= port_scan_threshold:
                anomalies.append(TrafficAnomaly(
                    anomaly_type="port_scan",
                    severity="high",
                    description=f"Possível port scan de {ip}",
                    source=ip,
                    destination="múltiplos",
                    evidence=[f"Acessou {len(ports)} portas diferentes"]
                ))
        
        # Detectar portas maliciosas
        for packet in self.packets:
            mal_port = ProtocolDB.is_malicious_port(packet.dst_port)
            if mal_port:
                anomalies.append(TrafficAnomaly(
                    anomaly_type="malicious_port",
                    severity="medium",
                    description=f"Tráfego para porta suspeita {packet.dst_port}",
                    source=packet.src_ip,
                    destination=f"{packet.dst_ip}:{packet.dst_port}",
                    evidence=[mal_port]
                ))
        
        # Detectar SYN flood
        syn_counts = Counter()
        for packet in self.packets:
            if packet.protocol == "TCP" and "S" in packet.flags and "A" not in packet.flags:
                syn_counts[packet.src_ip] += 1
        
        for ip, count in syn_counts.items():
            if count > 100:
                anomalies.append(TrafficAnomaly(
                    anomaly_type="syn_flood",
                    severity="critical",
                    description=f"Possível SYN flood de {ip}",
                    source=ip,
                    destination="múltiplos",
                    evidence=[f"{count} pacotes SYN"]
                ))
        
        return anomalies
    
    def analyze_connections(self, netstat_output: str = None) -> Dict:
        """Analisa conexões de rede atuais."""
        import subprocess
        
        if netstat_output is None:
            try:
                if os.name == 'nt':
                    result = subprocess.run(
                        ['netstat', '-an'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                else:
                    result = subprocess.run(
                        ['netstat', '-tuln'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                netstat_output = result.stdout
            except Exception as e:
                return {"error": str(e)}
        
        connections = NetstatParser.parse_netstat_output(netstat_output)
        
        # Análise
        stats = {
            "total_connections": len(connections),
            "by_state": Counter(),
            "by_protocol": Counter(),
            "listening_ports": [],
            "external_connections": [],
            "suspicious": [],
        }
        
        for conn in connections:
            stats["by_state"][conn.state] += 1
            stats["by_protocol"][conn.protocol] += 1
            
            if conn.state in ["LISTENING", "LISTEN"]:
                service = ProtocolDB.get_service(conn.src_port)
                stats["listening_ports"].append({
                    "port": conn.src_port,
                    "protocol": conn.protocol,
                    "service": service
                })
            
            # Conexões externas
            if conn.state == "ESTABLISHED" and not conn.dst_ip.startswith(('127.', '0.0.0.0', '*')):
                stats["external_connections"].append(conn.to_dict())
            
            # Verificar portas maliciosas
            mal_port = ProtocolDB.is_malicious_port(conn.src_port) or \
                       ProtocolDB.is_malicious_port(conn.dst_port)
            if mal_port:
                stats["suspicious"].append({
                    "connection": conn.to_dict(),
                    "reason": mal_port
                })
        
        return {
            "total_connections": stats["total_connections"],
            "by_state": dict(stats["by_state"]),
            "by_protocol": dict(stats["by_protocol"]),
            "listening_ports": stats["listening_ports"],
            "external_connections": stats["external_connections"][:20],
            "suspicious": stats["suspicious"]
        }
    
    def get_port_info(self, port: int) -> Dict:
        """Retorna informações sobre uma porta."""
        service = ProtocolDB.get_service(port)
        malicious = ProtocolDB.is_malicious_port(port)
        
        return {
            "port": port,
            "service": service,
            "is_well_known": port < 1024,
            "is_registered": 1024 <= port < 49152,
            "is_dynamic": port >= 49152,
            "malicious_association": malicious
        }


def interactive_menu():
    """Menu interativo do Network Traffic Analyzer."""
    analyzer = TrafficAnalyzer()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║         🌐 NETWORK TRAFFIC ANALYZER - Olho de Deus           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 📦 Analisar Arquivo PCAP                                ║
║  [2] 🔌 Analisar Conexões Atuais                             ║
║  [3] 🔍 Info de Porta                                        ║
║  [4] 📋 Listar Portas Conhecidas                             ║
║  [5] 🚨 Portas Maliciosas                                    ║
║  [6] 📊 Estatísticas de Rede                                 ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Analisar PCAP ===")
            file_path = input("Caminho do arquivo PCAP: ").strip()
            
            if not file_path or not os.path.exists(file_path):
                print("❌ Arquivo não encontrado")
                input("Enter para continuar...")
                continue
            
            print(f"\nAnalisando {file_path}...")
            result = analyzer.analyze_pcap(file_path)
            
            if "error" in result:
                print(f"❌ {result['error']}")
            else:
                print(f"\n📊 ANÁLISE DE TRÁFEGO:")
                print(f"   Total de pacotes: {result['total_packets']:,}")
                
                stats = result.get('stats', {})
                
                if stats.get('protocols'):
                    print(f"\n   📡 Protocolos:")
                    for proto, count in stats['protocols'].items():
                        print(f"      {proto}: {count:,}")
                
                if stats.get('top_talkers'):
                    print(f"\n   🔗 Top IPs de Origem:")
                    for ip, count in list(stats['top_talkers'].items())[:5]:
                        print(f"      {ip}: {count:,}")
                
                if stats.get('top_services'):
                    print(f"\n   📋 Serviços:")
                    for svc, count in stats['top_services'].items():
                        print(f"      {svc}: {count:,}")
                
                print(f"\n   📦 Total de bytes: {stats.get('total_bytes', 0):,}")
                
                anomalies = result.get('anomalies', [])
                if anomalies:
                    print(f"\n🚨 ANOMALIAS DETECTADAS ({len(anomalies)}):")
                    for anom in anomalies[:5]:
                        sev = anom['severity']
                        icon = "🔴" if sev == "critical" else "🟠" if sev == "high" else "🟡"
                        print(f"\n   {icon} [{anom['anomaly_type']}]")
                        print(f"      {anom['description']}")
        
        elif escolha == '2':
            print("\n=== Conexões Atuais ===")
            print("Executando netstat...")
            
            result = analyzer.analyze_connections()
            
            if "error" in result:
                print(f"❌ Erro: {result['error']}")
            else:
                print(f"\n📊 CONEXÕES DE REDE:")
                print(f"   Total: {result['total_connections']}")
                
                if result.get('by_state'):
                    print(f"\n   📋 Por Estado:")
                    for state, count in result['by_state'].items():
                        print(f"      {state}: {count}")
                
                if result.get('listening_ports'):
                    print(f"\n   🎧 Portas em LISTEN:")
                    for port_info in result['listening_ports'][:10]:
                        svc = port_info.get('service', 'Desconhecido')
                        print(f"      {port_info['port']} ({port_info['protocol']}) - {svc}")
                
                if result.get('external_connections'):
                    print(f"\n   🌐 Conexões Externas ({len(result['external_connections'])}):")
                    for conn in result['external_connections'][:5]:
                        print(f"      {conn['src_ip']}:{conn['src_port']} -> {conn['dst_ip']}:{conn['dst_port']}")
                
                if result.get('suspicious'):
                    print(f"\n   🚨 CONEXÕES SUSPEITAS:")
                    for susp in result['suspicious']:
                        conn = susp['connection']
                        print(f"      {conn['src_port']} -> {conn['dst_port']}: {susp['reason']}")
        
        elif escolha == '3':
            print("\n=== Informações de Porta ===")
            try:
                port = int(input("Número da porta: ").strip())
                info = analyzer.get_port_info(port)
                
                print(f"\n📋 PORTA {port}:")
                print(f"   Serviço: {info['service'] or 'Desconhecido'}")
                print(f"   Well-known (<1024): {'✅' if info['is_well_known'] else '❌'}")
                print(f"   Registrada (1024-49151): {'✅' if info['is_registered'] else '❌'}")
                print(f"   Dinâmica (>=49152): {'✅' if info['is_dynamic'] else '❌'}")
                
                if info['malicious_association']:
                    print(f"   ⚠️  ASSOCIAÇÃO MALICIOSA: {info['malicious_association']}")
            except ValueError:
                print("❌ Porta inválida")
        
        elif escolha == '4':
            print("\n=== Portas Conhecidas ===")
            print("\n📋 SERVIÇOS COMUNS:")
            
            for port, (service, proto) in sorted(ProtocolDB.COMMON_PORTS.items()):
                print(f"   {port:>5} {proto:<7} {service}")
        
        elif escolha == '5':
            print("\n=== Portas Associadas a Malware ===")
            print("\n⚠️  PORTAS MALICIOSAS:")
            
            for port, desc in sorted(ProtocolDB.MALICIOUS_PORTS.items()):
                print(f"   {port:>5} - {desc}")
            
            print("\n⚠️ Tráfego nessas portas requer investigação!")
        
        elif escolha == '6':
            print("\n=== Estatísticas de Rede ===")
            print("\nColetando dados...")
            
            result = analyzer.analyze_connections()
            
            if "error" not in result:
                print(f"\n📊 RESUMO DA REDE:")
                print(f"   Conexões totais: {result['total_connections']}")
                print(f"   Portas em escuta: {len(result.get('listening_ports', []))}")
                print(f"   Conexões externas: {len(result.get('external_connections', []))}")
                print(f"   Suspeitas: {len(result.get('suspicious', []))}")
                
                if result.get('by_protocol'):
                    print(f"\n   Por Protocolo:")
                    for proto, count in result['by_protocol'].items():
                        print(f"      {proto}: {count}")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
