#!/usr/bin/env python3
"""
Log Analyzer - Análise de logs de segurança
Parte do toolkit Olho de Deus
"""

import os
import sys
import re
import json
import gzip
from typing import List, Dict, Optional, Set, Tuple, Generator
from dataclasses import dataclass
from datetime import datetime
from collections import Counter, defaultdict
from pathlib import Path


@dataclass
class LogEntry:
    """Entrada de log."""
    timestamp: Optional[str]
    source_ip: Optional[str]
    user: Optional[str]
    action: str
    details: str
    severity: str
    raw: str
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "source_ip": self.source_ip,
            "user": self.user,
            "action": self.action,
            "details": self.details,
            "severity": self.severity
        }


@dataclass
class SecurityAlert:
    """Alerta de segurança."""
    alert_type: str
    severity: str
    description: str
    evidence: List[str]
    count: int
    source_ips: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "alert_type": self.alert_type,
            "severity": self.severity,
            "description": self.description,
            "evidence": self.evidence[:10],
            "count": self.count,
            "source_ips": self.source_ips[:10]
        }


class LogParser:
    """Parser de diferentes formatos de log."""
    
    # Padrões de timestamp
    TIMESTAMP_PATTERNS = [
        r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}',  # ISO
        r'\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}',      # Apache
        r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}',      # Syslog
        r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}',    # Windows
    ]
    
    # Padrão de IP
    IP_PATTERN = re.compile(
        r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    )
    
    # Padrões de log
    APACHE_COMBINED = re.compile(
        r'^(\S+)\s+\S+\s+(\S+)\s+\[([^\]]+)\]\s+"(\S+)\s+(\S+)\s+(\S+)"\s+(\d+)\s+(\d+|-)'
    )
    
    NGINX_COMBINED = re.compile(
        r'^(\S+)\s+-\s+(\S+)\s+\[([^\]]+)\]\s+"(\S+)\s+(\S+)\s+([^"]+)"\s+(\d+)\s+(\d+)'
    )
    
    SYSLOG = re.compile(
        r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+?)(?:\[\d+\])?:\s+(.+)$'
    )
    
    AUTH_LOG = re.compile(
        r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*?(sshd|sudo|su|login).*?(?:from\s+(\S+)|user[=:\s]+(\S+))?'
    )
    
    @classmethod
    def detect_format(cls, line: str) -> str:
        """Detecta formato do log."""
        if cls.APACHE_COMBINED.match(line):
            return "apache"
        elif cls.NGINX_COMBINED.match(line):
            return "nginx"
        elif cls.SYSLOG.match(line):
            return "syslog"
        elif "EventID" in line or "Windows" in line:
            return "windows"
        else:
            return "generic"
    
    @classmethod
    def parse_line(cls, line: str, log_format: str = "auto") -> Optional[LogEntry]:
        """Parse uma linha de log."""
        line = line.strip()
        if not line:
            return None
        
        if log_format == "auto":
            log_format = cls.detect_format(line)
        
        timestamp = None
        source_ip = None
        user = None
        action = ""
        details = line
        severity = "info"
        
        # Extrair timestamp
        for pattern in cls.TIMESTAMP_PATTERNS:
            match = re.search(pattern, line)
            if match:
                timestamp = match.group()
                break
        
        # Extrair IP
        ip_match = cls.IP_PATTERN.search(line)
        if ip_match:
            source_ip = ip_match.group()
        
        # Parse específico por formato
        if log_format == "apache" or log_format == "nginx":
            match = cls.APACHE_COMBINED.match(line) or cls.NGINX_COMBINED.match(line)
            if match:
                source_ip = match.group(1)
                user = match.group(2) if match.group(2) != '-' else None
                action = f"{match.group(4)} {match.group(5)}"
                status_code = int(match.group(7))
                
                if status_code >= 500:
                    severity = "error"
                elif status_code >= 400:
                    severity = "warning"
        
        elif log_format == "syslog":
            match = cls.SYSLOG.match(line)
            if match:
                timestamp = match.group(1)
                action = match.group(3)
                details = match.group(4)
        
        # Detectar severidade por keywords
        lower_line = line.lower()
        if any(w in lower_line for w in ['error', 'fail', 'denied', 'invalid']):
            severity = "error"
        elif any(w in lower_line for w in ['warning', 'warn', 'timeout']):
            severity = "warning"
        elif any(w in lower_line for w in ['critical', 'emergency', 'fatal']):
            severity = "critical"
        
        return LogEntry(
            timestamp=timestamp,
            source_ip=source_ip,
            user=user,
            action=action,
            details=details,
            severity=severity,
            raw=line
        )


class SecurityDetector:
    """Detector de eventos de segurança."""
    
    # Padrões de ataque
    ATTACK_PATTERNS = {
        "sql_injection": [
            r"(?:union\s+select|select.*from|insert\s+into|drop\s+table)",
            r"(?:'\s*or\s+'1'\s*=\s*'1|'\s*or\s+1=1)",
            r"(?:--\s*$|#\s*$|/\*.*\*/)",
        ],
        "xss": [
            r"<script[^>]*>",
            r"javascript:",
            r"on(?:load|error|click|mouse)\s*=",
        ],
        "path_traversal": [
            r"(?:\.\.\/|\.\.\\)",
            r"(?:/etc/passwd|/etc/shadow)",
            r"(?:c:\\windows|c:\\system32)",
        ],
        "command_injection": [
            r"(?:;\s*(?:cat|ls|id|whoami|wget|curl))",
            r"(?:\|\s*(?:cat|ls|id|whoami))",
            r"(?:\$\(|`.*`)",
        ],
        "brute_force": [
            r"(?:failed\s+password|authentication\s+failure|invalid\s+user)",
            r"(?:login\s+failed|access\s+denied)",
        ],
        "port_scan": [
            r"(?:connection\s+refused|no\s+route\s+to\s+host)",
            r"(?:port\s+\d+\s+unreachable)",
        ],
        "web_scanner": [
            r"(?:nikto|nmap|sqlmap|dirbuster|gobuster|wfuzz)",
            r"(?:acunetix|nessus|burp)",
        ],
    }
    
    # User agents suspeitos
    SUSPICIOUS_USER_AGENTS = [
        r"sqlmap", r"nikto", r"nmap", r"masscan",
        r"dirbuster", r"gobuster", r"wfuzz",
        r"python-requests", r"curl", r"wget",
        r"scanner", r"bot", r"crawler",
    ]
    
    def __init__(self):
        self.alerts = []
        self.ip_counts = Counter()
        self.failed_logins = defaultdict(list)
        self.suspicious_requests = []
    
    def analyze_entry(self, entry: LogEntry):
        """Analisa uma entrada de log."""
        if entry.source_ip:
            self.ip_counts[entry.source_ip] += 1
        
        line = entry.raw.lower()
        
        # Verificar padrões de ataque
        for attack_type, patterns in self.ATTACK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.suspicious_requests.append({
                        "type": attack_type,
                        "entry": entry,
                        "pattern": pattern
                    })
                    break
        
        # Detectar falhas de login
        if any(w in line for w in ['failed', 'invalid', 'denied']) and \
           any(w in line for w in ['login', 'password', 'auth']):
            if entry.source_ip:
                self.failed_logins[entry.source_ip].append(entry)
    
    def generate_alerts(self) -> List[SecurityAlert]:
        """Gera alertas baseados na análise."""
        alerts = []
        
        # Brute force (muitas falhas do mesmo IP)
        for ip, failures in self.failed_logins.items():
            if len(failures) >= 5:
                alerts.append(SecurityAlert(
                    alert_type="brute_force",
                    severity="high" if len(failures) >= 10 else "medium",
                    description=f"Possível brute force de {ip}",
                    evidence=[f.raw for f in failures[:5]],
                    count=len(failures),
                    source_ips=[ip]
                ))
        
        # Ataques web agrupados por tipo
        attack_groups = defaultdict(list)
        for req in self.suspicious_requests:
            attack_groups[req["type"]].append(req)
        
        for attack_type, requests in attack_groups.items():
            ips = list(set(r["entry"].source_ip for r in requests if r["entry"].source_ip))
            alerts.append(SecurityAlert(
                alert_type=attack_type,
                severity="high" if len(requests) >= 10 else "medium",
                description=f"Detectado {attack_type}: {len(requests)} ocorrências",
                evidence=[r["entry"].raw for r in requests[:5]],
                count=len(requests),
                source_ips=ips[:10]
            ))
        
        # IPs com muitas requisições (possível DoS)
        for ip, count in self.ip_counts.most_common(10):
            if count >= 1000:
                alerts.append(SecurityAlert(
                    alert_type="dos_attempt",
                    severity="high",
                    description=f"Alto volume de requisições de {ip}",
                    evidence=[f"{count} requisições"],
                    count=count,
                    source_ips=[ip]
                ))
        
        return alerts


class LogAnalyzer:
    """Analisador de logs principal."""
    
    def __init__(self):
        self.parser = LogParser()
        self.detector = SecurityDetector()
    
    def read_log_file(self, file_path: str) -> Generator[str, None, None]:
        """Lê arquivo de log (suporta gzip)."""
        if file_path.endswith('.gz'):
            with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    yield line
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    yield line
    
    def analyze_file(self, file_path: str) -> Dict:
        """Analisa um arquivo de log."""
        if not os.path.exists(file_path):
            return {"error": "Arquivo não encontrado"}
        
        stats = {
            "file": file_path,
            "total_lines": 0,
            "parsed_lines": 0,
            "errors": 0,
            "warnings": 0,
            "unique_ips": set(),
            "status_codes": Counter(),
            "methods": Counter(),
            "top_urls": Counter(),
            "top_ips": Counter(),
        }
        
        self.detector = SecurityDetector()  # Reset
        
        for line in self.read_log_file(file_path):
            stats["total_lines"] += 1
            
            entry = self.parser.parse_line(line)
            if entry:
                stats["parsed_lines"] += 1
                
                if entry.severity == "error":
                    stats["errors"] += 1
                elif entry.severity == "warning":
                    stats["warnings"] += 1
                
                if entry.source_ip:
                    stats["unique_ips"].add(entry.source_ip)
                    stats["top_ips"][entry.source_ip] += 1
                
                if entry.action:
                    parts = entry.action.split()
                    if parts:
                        stats["methods"][parts[0]] += 1
                    if len(parts) > 1:
                        stats["top_urls"][parts[1]] += 1
                
                # Análise de segurança
                self.detector.analyze_entry(entry)
        
        # Gerar alertas
        alerts = self.detector.generate_alerts()
        
        return {
            "file": file_path,
            "total_lines": stats["total_lines"],
            "parsed_lines": stats["parsed_lines"],
            "errors": stats["errors"],
            "warnings": stats["warnings"],
            "unique_ips": len(stats["unique_ips"]),
            "top_ips": dict(stats["top_ips"].most_common(10)),
            "methods": dict(stats["methods"]),
            "top_urls": dict(stats["top_urls"].most_common(10)),
            "security_alerts": [a.to_dict() for a in alerts],
            "alert_summary": {
                "total": len(alerts),
                "high": sum(1 for a in alerts if a.severity == "high"),
                "medium": sum(1 for a in alerts if a.severity == "medium"),
                "low": sum(1 for a in alerts if a.severity == "low"),
            }
        }
    
    def search_logs(self, file_path: str, pattern: str, 
                    is_regex: bool = False) -> List[str]:
        """Busca em logs."""
        results = []
        
        if is_regex:
            regex = re.compile(pattern, re.IGNORECASE)
        
        for line in self.read_log_file(file_path):
            if is_regex:
                if regex.search(line):
                    results.append(line.strip())
            else:
                if pattern.lower() in line.lower():
                    results.append(line.strip())
        
        return results
    
    def extract_ips(self, file_path: str) -> Dict[str, int]:
        """Extrai IPs de um log."""
        ip_counts = Counter()
        
        for line in self.read_log_file(file_path):
            ips = LogParser.IP_PATTERN.findall(line)
            for ip in ips:
                ip_counts[ip] += 1
        
        return dict(ip_counts.most_common())


def interactive_menu():
    """Menu interativo do Log Analyzer."""
    analyzer = LogAnalyzer()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║             📋 LOG ANALYZER - Olho de Deus                   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 📊 Analisar Arquivo de Log                              ║
║  [2] 🔍 Buscar em Logs                                       ║
║  [3] 🔗 Extrair IPs                                          ║
║  [4] 🚨 Detectar Eventos de Segurança                        ║
║  [5] 📈 Estatísticas Rápidas                                 ║
║  [6] 📋 Analisar Múltiplos Arquivos                          ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Analisar Log ===")
            file_path = input("Caminho do arquivo: ").strip()
            
            if not file_path or not os.path.exists(file_path):
                print("❌ Arquivo não encontrado")
                input("Enter para continuar...")
                continue
            
            print(f"\nAnalisando {file_path}...")
            result = analyzer.analyze_file(file_path)
            
            print(f"\n📊 ESTATÍSTICAS:")
            print(f"   Total de linhas: {result['total_lines']:,}")
            print(f"   Linhas parseadas: {result['parsed_lines']:,}")
            print(f"   Erros: {result['errors']:,}")
            print(f"   Warnings: {result['warnings']:,}")
            print(f"   IPs únicos: {result['unique_ips']}")
            
            if result.get('methods'):
                print(f"\n   📋 Métodos HTTP:")
                for method, count in result['methods'].items():
                    print(f"      {method}: {count:,}")
            
            if result.get('top_ips'):
                print(f"\n   🔗 Top IPs:")
                for ip, count in list(result['top_ips'].items())[:5]:
                    print(f"      {ip}: {count:,}")
            
            alerts = result.get('security_alerts', [])
            if alerts:
                summary = result.get('alert_summary', {})
                print(f"\n🚨 ALERTAS DE SEGURANÇA ({summary.get('total', 0)}):")
                print(f"   🔴 Alto: {summary.get('high', 0)}")
                print(f"   🟠 Médio: {summary.get('medium', 0)}")
                print(f"   🟢 Baixo: {summary.get('low', 0)}")
                
                for alert in alerts[:5]:
                    sev = alert['severity']
                    icon = "🔴" if sev == "high" else "🟠" if sev == "medium" else "🟢"
                    print(f"\n   {icon} [{alert['alert_type']}]")
                    print(f"      {alert['description']}")
                    if alert.get('source_ips'):
                        print(f"      IPs: {', '.join(alert['source_ips'][:3])}")
            
            save = input("\nSalvar relatório? (s/n): ").lower()
            if save == 's':
                report_file = f"log_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                print(f"✅ Salvo em {report_file}")
        
        elif escolha == '2':
            print("\n=== Buscar em Logs ===")
            file_path = input("Caminho do arquivo: ").strip()
            pattern = input("Termo de busca: ").strip()
            is_regex = input("Usar regex? (s/n): ").lower() == 's'
            
            if not file_path or not pattern:
                continue
            
            print(f"\nBuscando...")
            results = analyzer.search_logs(file_path, pattern, is_regex)
            
            print(f"\n📝 {len(results)} resultado(s) encontrado(s):")
            for line in results[:20]:
                print(f"   {line[:100]}")
            
            if len(results) > 20:
                print(f"\n   ... e mais {len(results) - 20} resultados")
        
        elif escolha == '3':
            print("\n=== Extrair IPs ===")
            file_path = input("Caminho do arquivo: ").strip()
            
            if not file_path or not os.path.exists(file_path):
                print("❌ Arquivo não encontrado")
                input("Enter para continuar...")
                continue
            
            print(f"\nExtraindo IPs...")
            ips = analyzer.extract_ips(file_path)
            
            print(f"\n🔗 {len(ips)} IPs encontrados:")
            for ip, count in list(ips.items())[:30]:
                print(f"   {ip}: {count:,}")
            
            save = input("\nSalvar lista de IPs? (s/n): ").lower()
            if save == 's':
                with open("extracted_ips.txt", 'w') as f:
                    for ip in ips.keys():
                        f.write(ip + '\n')
                print("✅ Salvo em extracted_ips.txt")
        
        elif escolha == '4':
            print("\n=== Detectar Eventos de Segurança ===")
            file_path = input("Caminho do arquivo: ").strip()
            
            if not file_path or not os.path.exists(file_path):
                print("❌ Arquivo não encontrado")
                input("Enter para continuar...")
                continue
            
            print(f"\nAnalisando eventos de segurança...")
            result = analyzer.analyze_file(file_path)
            
            alerts = result.get('security_alerts', [])
            
            if alerts:
                print(f"\n🚨 {len(alerts)} ALERTAS DETECTADOS:\n")
                
                for alert in alerts:
                    sev = alert['severity']
                    icon = "🔴" if sev == "high" else "🟠" if sev == "medium" else "🟢"
                    
                    print(f"{icon} [{sev.upper()}] {alert['alert_type']}")
                    print(f"   {alert['description']}")
                    print(f"   Ocorrências: {alert['count']}")
                    
                    if alert.get('source_ips'):
                        print(f"   IPs: {', '.join(alert['source_ips'][:5])}")
                    
                    if alert.get('evidence'):
                        print(f"   Evidência:")
                        for ev in alert['evidence'][:2]:
                            print(f"      {ev[:80]}...")
                    print()
            else:
                print("\n✅ Nenhum alerta de segurança detectado")
        
        elif escolha == '5':
            print("\n=== Estatísticas Rápidas ===")
            file_path = input("Caminho do arquivo: ").strip()
            
            if not file_path or not os.path.exists(file_path):
                print("❌ Arquivo não encontrado")
                input("Enter para continuar...")
                continue
            
            print(f"\nCalculando estatísticas...")
            
            line_count = 0
            error_count = 0
            ips = set()
            
            for line in analyzer.read_log_file(file_path):
                line_count += 1
                if 'error' in line.lower() or 'fail' in line.lower():
                    error_count += 1
                ip_matches = LogParser.IP_PATTERN.findall(line)
                ips.update(ip_matches)
            
            file_size = os.path.getsize(file_path)
            
            print(f"\n📈 ESTATÍSTICAS:")
            print(f"   Tamanho: {file_size:,} bytes")
            print(f"   Linhas: {line_count:,}")
            print(f"   Erros/Falhas: {error_count:,}")
            print(f"   IPs únicos: {len(ips)}")
        
        elif escolha == '6':
            print("\n=== Analisar Múltiplos Arquivos ===")
            dir_path = input("Diretório de logs: ").strip()
            pattern = input("Padrão de arquivo (ex: *.log, access*): ").strip() or "*.log"
            
            if not dir_path or not os.path.isdir(dir_path):
                print("❌ Diretório não encontrado")
                input("Enter para continuar...")
                continue
            
            from glob import glob
            files = glob(os.path.join(dir_path, pattern))
            
            if not files:
                print("❌ Nenhum arquivo encontrado")
                input("Enter para continuar...")
                continue
            
            print(f"\nAnalisando {len(files)} arquivos...\n")
            
            all_results = []
            total_alerts = 0
            
            for file_path in files[:10]:
                print(f"Analisando {os.path.basename(file_path)}...", end=" ")
                result = analyzer.analyze_file(file_path)
                alerts = len(result.get('security_alerts', []))
                print(f"{result['total_lines']:,} linhas, {alerts} alertas")
                all_results.append(result)
                total_alerts += alerts
            
            print(f"\n📊 RESUMO:")
            print(f"   Arquivos analisados: {len(all_results)}")
            print(f"   Total de alertas: {total_alerts}")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
