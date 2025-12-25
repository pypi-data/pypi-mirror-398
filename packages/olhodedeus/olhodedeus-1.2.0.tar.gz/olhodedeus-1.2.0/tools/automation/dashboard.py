#!/usr/bin/env python3
"""
Security Dashboard - Painel de controle de segurança
Parte do toolkit Olho de Deus
"""

import os
import sys
import json
import sqlite3
import socket
import platform
import subprocess
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class SystemInfo:
    """Informações do sistema."""
    hostname: str
    os_name: str
    os_version: str
    architecture: str
    python_version: str
    uptime: str
    ip_addresses: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "hostname": self.hostname,
            "os_name": self.os_name,
            "os_version": self.os_version,
            "architecture": self.architecture,
            "python_version": self.python_version,
            "uptime": self.uptime,
            "ip_addresses": self.ip_addresses
        }


@dataclass
class SecurityMetric:
    """Métrica de segurança."""
    name: str
    value: Any
    status: str  # good, warning, critical
    description: str
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "value": self.value,
            "status": self.status,
            "description": self.description
        }


class SystemCollector:
    """Coletor de informações do sistema."""
    
    @staticmethod
    def get_system_info() -> SystemInfo:
        """Coleta informações do sistema."""
        hostname = socket.gethostname()
        os_name = platform.system()
        os_version = platform.release()
        architecture = platform.machine()
        python_version = platform.python_version()
        
        # IPs
        ip_addresses = []
        try:
            hostname_info = socket.gethostbyname_ex(hostname)
            ip_addresses = hostname_info[2]
        except:
            ip_addresses = ["127.0.0.1"]
        
        # Uptime
        uptime = "N/A"
        try:
            if os_name == "Windows":
                result = subprocess.run(
                    ["net", "stats", "srv"],
                    capture_output=True,
                    text=True
                )
                for line in result.stdout.splitlines():
                    if "Statistics since" in line:
                        uptime = line.split("since")[1].strip()
                        break
            else:
                result = subprocess.run(
                    ["uptime", "-p"],
                    capture_output=True,
                    text=True
                )
                uptime = result.stdout.strip()
        except:
            pass
        
        return SystemInfo(
            hostname=hostname,
            os_name=os_name,
            os_version=os_version,
            architecture=architecture,
            python_version=python_version,
            uptime=uptime,
            ip_addresses=ip_addresses
        )
    
    @staticmethod
    def get_open_ports() -> List[Dict]:
        """Lista portas abertas."""
        ports = []
        
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["netstat", "-an"],
                    capture_output=True,
                    text=True
                )
            else:
                result = subprocess.run(
                    ["netstat", "-tuln"],
                    capture_output=True,
                    text=True
                )
            
            for line in result.stdout.splitlines():
                if "LISTEN" in line or "LISTENING" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        local = parts[1] if platform.system() != "Windows" else parts[1]
                        if ":" in local:
                            port = local.rsplit(":", 1)[-1]
                            try:
                                ports.append({
                                    "port": int(port),
                                    "address": local
                                })
                            except ValueError:
                                pass
        except:
            pass
        
        return ports
    
    @staticmethod
    def get_running_processes() -> List[Dict]:
        """Lista processos em execução."""
        processes = []
        
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["tasklist", "/FO", "CSV"],
                    capture_output=True,
                    text=True
                )
                lines = result.stdout.splitlines()[1:]  # Skip header
                for line in lines[:50]:  # Limit
                    parts = line.replace('"', '').split(',')
                    if len(parts) >= 2:
                        processes.append({
                            "name": parts[0],
                            "pid": parts[1]
                        })
            else:
                result = subprocess.run(
                    ["ps", "aux", "--sort=-rss"],
                    capture_output=True,
                    text=True
                )
                lines = result.stdout.splitlines()[1:51]
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 11:
                        processes.append({
                            "user": parts[0],
                            "pid": parts[1],
                            "cpu": parts[2],
                            "mem": parts[3],
                            "name": " ".join(parts[10:])
                        })
        except:
            pass
        
        return processes


class SecurityChecker:
    """Verificador de segurança."""
    
    DANGEROUS_PORTS = [21, 23, 135, 137, 138, 139, 445, 3389, 5900]
    
    @classmethod
    def check_open_ports(cls) -> SecurityMetric:
        """Verifica portas abertas perigosas."""
        ports = SystemCollector.get_open_ports()
        dangerous = [p for p in ports if p["port"] in cls.DANGEROUS_PORTS]
        
        if len(dangerous) > 3:
            status = "critical"
        elif len(dangerous) > 0:
            status = "warning"
        else:
            status = "good"
        
        return SecurityMetric(
            name="Portas Perigosas",
            value=len(dangerous),
            status=status,
            description=f"{len(dangerous)} portas potencialmente perigosas abertas"
        )
    
    @classmethod
    def check_firewall(cls) -> SecurityMetric:
        """Verifica status do firewall."""
        enabled = False
        
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["netsh", "advfirewall", "show", "allprofiles", "state"],
                    capture_output=True,
                    text=True
                )
                enabled = "ON" in result.stdout
            else:
                result = subprocess.run(
                    ["ufw", "status"],
                    capture_output=True,
                    text=True
                )
                enabled = "active" in result.stdout.lower()
        except:
            pass
        
        return SecurityMetric(
            name="Firewall",
            value="Ativo" if enabled else "Inativo",
            status="good" if enabled else "critical",
            description="Status do firewall do sistema"
        )
    
    @classmethod
    def check_updates(cls) -> SecurityMetric:
        """Verifica atualizações pendentes."""
        pending = 0
        
        try:
            if platform.system() == "Windows":
                # Simplificado - Windows Update é complexo
                status = "warning"
                description = "Verifique Windows Update manualmente"
            else:
                result = subprocess.run(
                    ["apt", "list", "--upgradable"],
                    capture_output=True,
                    text=True
                )
                pending = len(result.stdout.splitlines()) - 1
                
                if pending > 20:
                    status = "critical"
                elif pending > 0:
                    status = "warning"
                else:
                    status = "good"
                    
                description = f"{pending} atualizações disponíveis"
        except:
            status = "warning"
            description = "Não foi possível verificar atualizações"
        
        return SecurityMetric(
            name="Atualizações",
            value=pending,
            status=status,
            description=description
        )
    
    @classmethod
    def get_all_metrics(cls) -> List[SecurityMetric]:
        """Retorna todas as métricas de segurança."""
        return [
            cls.check_open_ports(),
            cls.check_firewall(),
            cls.check_updates(),
        ]


class ActivityLogger:
    """Logger de atividades."""
    
    def __init__(self, db_path: str = "dashboard.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializa banco de dados."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                category TEXT,
                action TEXT,
                details TEXT,
                severity TEXT DEFAULT 'info'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                metric_name TEXT,
                metric_value TEXT,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_activity(self, category: str, action: str, 
                     details: str = "", severity: str = "info"):
        """Registra atividade."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO activity_log (category, action, details, severity)
            VALUES (?, ?, ?, ?)
        ''', (category, action, details, severity))
        
        conn.commit()
        conn.close()
    
    def get_recent_activity(self, limit: int = 50) -> List[Dict]:
        """Obtém atividades recentes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, category, action, details, severity
            FROM activity_log
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "timestamp": row[0],
                "category": row[1],
                "action": row[2],
                "details": row[3],
                "severity": row[4]
            }
            for row in rows
        ]
    
    def save_metrics(self, metrics: List[SecurityMetric]):
        """Salva métricas para histórico."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for metric in metrics:
            cursor.execute('''
                INSERT INTO metrics_history (metric_name, metric_value, status)
                VALUES (?, ?, ?)
            ''', (metric.name, str(metric.value), metric.status))
        
        conn.commit()
        conn.close()


class Dashboard:
    """Painel de controle principal."""
    
    def __init__(self):
        self.logger = ActivityLogger()
        self.system_info = None
        self.metrics = []
    
    def refresh(self):
        """Atualiza dados do dashboard."""
        self.system_info = SystemCollector.get_system_info()
        self.metrics = SecurityChecker.get_all_metrics()
        self.logger.save_metrics(self.metrics)
        self.logger.log_activity("dashboard", "refresh", "Dashboard atualizado")
    
    def get_summary(self) -> Dict:
        """Retorna resumo do dashboard."""
        if not self.system_info:
            self.refresh()
        
        critical = sum(1 for m in self.metrics if m.status == "critical")
        warning = sum(1 for m in self.metrics if m.status == "warning")
        good = sum(1 for m in self.metrics if m.status == "good")
        
        return {
            "system": self.system_info.to_dict(),
            "security_score": max(0, 100 - (critical * 30) - (warning * 10)),
            "metrics": {
                "critical": critical,
                "warning": warning,
                "good": good
            },
            "last_refresh": datetime.now().isoformat()
        }


def interactive_menu():
    """Menu interativo do Dashboard."""
    dashboard = Dashboard()
    dashboard.refresh()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        summary = dashboard.get_summary()
        score = summary["security_score"]
        
        if score >= 80:
            score_color = "🟢"
        elif score >= 50:
            score_color = "🟡"
        else:
            score_color = "🔴"
        
        system = summary["system"]
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║          📊 SECURITY DASHBOARD - Olho de Deus                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Sistema: {system['hostname'][:20]:<20} {system['os_name']} {system['os_version'][:10]:<10} ║
║  IP: {system['ip_addresses'][0] if system['ip_addresses'] else 'N/A':<25}                          ║
║                                                              ║
║  {score_color} Security Score: {score}/100                                    ║
║                                                              ║
║  Métricas: 🔴 {summary['metrics']['critical']} críticas | 🟡 {summary['metrics']['warning']} alertas | 🟢 {summary['metrics']['good']} OK      ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔄 Atualizar Dashboard                                  ║
║  [2] 📋 Ver Métricas Detalhadas                              ║
║  [3] 🔌 Portas Abertas                                       ║
║  [4] 📝 Processos em Execução                                ║
║  [5] 📊 Informações do Sistema                               ║
║  [6] 📜 Log de Atividades                                    ║
║  [7] 💾 Exportar Relatório                                   ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n🔄 Atualizando dashboard...")
            dashboard.refresh()
            print("✅ Dashboard atualizado!")
            input("Enter para continuar...")
        
        elif escolha == '2':
            print("\n=== Métricas de Segurança ===\n")
            
            for metric in dashboard.metrics:
                if metric.status == "critical":
                    icon = "🔴"
                elif metric.status == "warning":
                    icon = "🟡"
                else:
                    icon = "🟢"
                
                print(f"{icon} {metric.name}")
                print(f"   Valor: {metric.value}")
                print(f"   {metric.description}")
                print()
        
        elif escolha == '3':
            print("\n=== Portas Abertas ===\n")
            
            ports = SystemCollector.get_open_ports()
            
            dangerous_ports = [21, 23, 135, 137, 138, 139, 445, 3389, 5900]
            
            if not ports:
                print("Não foi possível listar portas ou nenhuma porta encontrada.")
            else:
                for p in sorted(ports, key=lambda x: x["port"])[:30]:
                    is_dangerous = p["port"] in dangerous_ports
                    icon = "⚠️" if is_dangerous else "🔌"
                    print(f"   {icon} {p['port']:<6} {p['address']}")
                
                dangerous_open = [p for p in ports if p["port"] in dangerous_ports]
                if dangerous_open:
                    print(f"\n⚠️  {len(dangerous_open)} porta(s) potencialmente perigosa(s) detectada(s)!")
        
        elif escolha == '4':
            print("\n=== Processos em Execução ===\n")
            
            processes = SystemCollector.get_running_processes()
            
            if not processes:
                print("Não foi possível listar processos.")
            else:
                if platform.system() == "Windows":
                    print(f"{'Nome':<40} {'PID':<10}")
                    print("-" * 50)
                    for p in processes[:30]:
                        print(f"{p['name'][:39]:<40} {p['pid']:<10}")
                else:
                    print(f"{'Usuário':<10} {'PID':<8} {'CPU%':<6} {'MEM%':<6} {'Nome':<30}")
                    print("-" * 65)
                    for p in processes[:30]:
                        print(f"{p['user'][:9]:<10} {p['pid']:<8} {p['cpu']:<6} {p['mem']:<6} {p['name'][:29]:<30}")
        
        elif escolha == '5':
            print("\n=== Informações do Sistema ===\n")
            
            info = dashboard.system_info
            
            print(f"   Hostname: {info.hostname}")
            print(f"   Sistema: {info.os_name} {info.os_version}")
            print(f"   Arquitetura: {info.architecture}")
            print(f"   Python: {info.python_version}")
            print(f"   Uptime: {info.uptime}")
            print(f"   IPs: {', '.join(info.ip_addresses)}")
        
        elif escolha == '6':
            print("\n=== Log de Atividades ===\n")
            
            activities = dashboard.logger.get_recent_activity(20)
            
            if not activities:
                print("Nenhuma atividade registrada.")
            else:
                for act in activities:
                    sev = act['severity']
                    icon = "🔴" if sev == "critical" else "🟡" if sev == "warning" else "🔵"
                    timestamp = act['timestamp'][:16] if act['timestamp'] else "N/A"
                    print(f"{icon} [{timestamp}] {act['category']}: {act['action']}")
        
        elif escolha == '7':
            print("\n=== Exportar Relatório ===")
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "system": dashboard.system_info.to_dict(),
                "metrics": [m.to_dict() for m in dashboard.metrics],
                "security_score": summary["security_score"],
                "open_ports": SystemCollector.get_open_ports()[:50],
            }
            
            filename = f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"✅ Relatório salvo em {filename}")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
