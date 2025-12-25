#!/usr/bin/env python3
"""
Recon Automation - Automação de reconhecimento
Parte do toolkit Olho de Deus
"""

import os
import sys
import json
import socket
import threading
import subprocess
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import time


@dataclass
class ReconTask:
    """Tarefa de reconhecimento."""
    name: str
    task_type: str
    target: str
    options: Dict = field(default_factory=dict)
    status: str = "pending"
    result: Any = None
    error: str = ""
    started_at: str = ""
    completed_at: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "task_type": self.task_type,
            "target": self.target,
            "options": self.options,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


@dataclass
class ReconPipeline:
    """Pipeline de reconhecimento."""
    name: str
    description: str
    tasks: List[ReconTask] = field(default_factory=list)
    created_at: str = ""
    completed_at: str = ""
    status: str = "created"
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "tasks": [t.to_dict() for t in self.tasks],
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "status": self.status
        }


class ReconModules:
    """Módulos de reconhecimento."""
    
    @staticmethod
    def dns_lookup(target: str, options: Dict = None) -> Dict:
        """Lookup DNS básico."""
        result = {"target": target, "records": {}}
        
        try:
            # A record
            try:
                ips = socket.gethostbyname_ex(target)[2]
                result["records"]["A"] = ips
            except:
                pass
            
            # Resolver outros records se dns.resolver disponível
            try:
                import dns.resolver
                
                for rtype in ["MX", "NS", "TXT", "AAAA"]:
                    try:
                        answers = dns.resolver.resolve(target, rtype)
                        result["records"][rtype] = [str(r) for r in answers]
                    except:
                        pass
            except ImportError:
                pass
            
            result["success"] = True
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def port_scan(target: str, options: Dict = None) -> Dict:
        """Port scan básico."""
        options = options or {}
        ports = options.get("ports", [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3389, 8080])
        timeout = options.get("timeout", 1)
        
        result = {
            "target": target,
            "open_ports": [],
            "closed_ports": [],
        }
        
        try:
            ip = socket.gethostbyname(target)
            result["ip"] = ip
            
            for port in ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    conn = sock.connect_ex((ip, port))
                    sock.close()
                    
                    if conn == 0:
                        result["open_ports"].append(port)
                    else:
                        result["closed_ports"].append(port)
                except:
                    result["closed_ports"].append(port)
            
            result["success"] = True
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def whois_lookup(target: str, options: Dict = None) -> Dict:
        """WHOIS lookup."""
        result = {"target": target, "whois": {}}
        
        try:
            import subprocess
            
            proc = subprocess.run(
                ["whois", target],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            result["raw"] = proc.stdout
            
            # Parse básico
            for line in proc.stdout.splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    key = key.strip().lower().replace(" ", "_")
                    value = value.strip()
                    if key and value and len(key) < 30:
                        result["whois"][key] = value
            
            result["success"] = True
        except FileNotFoundError:
            result["success"] = False
            result["error"] = "whois command not found"
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def http_headers(target: str, options: Dict = None) -> Dict:
        """Coleta headers HTTP."""
        result = {"target": target, "headers": {}}
        
        try:
            import urllib.request
            import ssl
            
            url = target if target.startswith("http") else f"https://{target}"
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "Mozilla/5.0")
            
            with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                result["status_code"] = response.status
                result["headers"] = dict(response.headers)
                
                # Security headers check
                security_headers = [
                    "X-Frame-Options",
                    "X-Content-Type-Options",
                    "Content-Security-Policy",
                    "Strict-Transport-Security",
                    "X-XSS-Protection"
                ]
                
                result["security_headers"] = {}
                for h in security_headers:
                    result["security_headers"][h] = h in response.headers
            
            result["success"] = True
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def subdomain_enum(target: str, options: Dict = None) -> Dict:
        """Enumeração de subdomínios."""
        result = {"target": target, "subdomains": []}
        
        common_prefixes = [
            "www", "mail", "ftp", "localhost", "webmail", "smtp", "pop",
            "ns1", "ns2", "ns3", "ns4", "dns", "dns1", "dns2",
            "mx", "mx1", "mx2", "blog", "dev", "staging", "test",
            "api", "app", "admin", "panel", "login", "vpn", "remote",
            "git", "gitlab", "github", "jenkins", "ci", "cd",
            "shop", "store", "support", "help", "docs", "status",
        ]
        
        try:
            for prefix in common_prefixes:
                subdomain = f"{prefix}.{target}"
                try:
                    ip = socket.gethostbyname(subdomain)
                    result["subdomains"].append({
                        "subdomain": subdomain,
                        "ip": ip
                    })
                except socket.gaierror:
                    pass
            
            result["success"] = True
            result["found"] = len(result["subdomains"])
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def tech_detect(target: str, options: Dict = None) -> Dict:
        """Detecção de tecnologias."""
        result = {"target": target, "technologies": []}
        
        try:
            import urllib.request
            import ssl
            
            url = target if target.startswith("http") else f"https://{target}"
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0")
            
            with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                html = response.read().decode('utf-8', errors='ignore').lower()
                headers = dict(response.headers)
                
                # Patterns
                tech_patterns = {
                    "WordPress": ["wp-content", "wp-includes", "wordpress"],
                    "Drupal": ["drupal", "/sites/default/"],
                    "Joomla": ["joomla", "/components/"],
                    "React": ["react", "_next", "reactdom"],
                    "Angular": ["ng-app", "angular", "ng-"],
                    "Vue.js": ["vue.js", "vuejs", "__vue__"],
                    "jQuery": ["jquery"],
                    "Bootstrap": ["bootstrap"],
                    "PHP": [".php"],
                    "ASP.NET": ["asp.net", "__viewstate", "aspnetcore"],
                    "nginx": ["nginx"],
                    "Apache": ["apache"],
                    "Cloudflare": ["cloudflare"],
                }
                
                for tech, patterns in tech_patterns.items():
                    for pattern in patterns:
                        if pattern in html or any(pattern in str(v).lower() for v in headers.values()):
                            if tech not in result["technologies"]:
                                result["technologies"].append(tech)
                            break
                
                # Server header
                if "Server" in headers:
                    result["server"] = headers["Server"]
                    if headers["Server"] not in result["technologies"]:
                        result["technologies"].append(headers["Server"].split("/")[0])
            
            result["success"] = True
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        
        return result


class ReconAutomation:
    """Sistema de automação de reconhecimento."""
    
    MODULES = {
        "dns": ReconModules.dns_lookup,
        "ports": ReconModules.port_scan,
        "whois": ReconModules.whois_lookup,
        "headers": ReconModules.http_headers,
        "subdomains": ReconModules.subdomain_enum,
        "tech": ReconModules.tech_detect,
    }
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.pipelines: List[ReconPipeline] = []
        self.results: Dict[str, Any] = {}
    
    def create_pipeline(self, name: str, description: str = "") -> ReconPipeline:
        """Cria novo pipeline."""
        pipeline = ReconPipeline(
            name=name,
            description=description,
            created_at=datetime.now().isoformat()
        )
        self.pipelines.append(pipeline)
        return pipeline
    
    def add_task(self, pipeline: ReconPipeline, task_type: str, 
                 target: str, options: Dict = None) -> ReconTask:
        """Adiciona tarefa ao pipeline."""
        task = ReconTask(
            name=f"{task_type}_{target}",
            task_type=task_type,
            target=target,
            options=options or {}
        )
        pipeline.tasks.append(task)
        return task
    
    def run_task(self, task: ReconTask) -> ReconTask:
        """Executa uma tarefa."""
        task.started_at = datetime.now().isoformat()
        task.status = "running"
        
        try:
            if task.task_type in self.MODULES:
                module = self.MODULES[task.task_type]
                task.result = module(task.target, task.options)
                task.status = "completed"
            else:
                task.error = f"Módulo desconhecido: {task.task_type}"
                task.status = "failed"
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
        
        task.completed_at = datetime.now().isoformat()
        return task
    
    def run_pipeline(self, pipeline: ReconPipeline, 
                     parallel: bool = True,
                     callback: Callable = None) -> ReconPipeline:
        """Executa pipeline."""
        pipeline.status = "running"
        
        if parallel:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.run_task, task): task 
                          for task in pipeline.tasks}
                
                for future in as_completed(futures):
                    task = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        task.error = str(e)
                        task.status = "failed"
                    
                    if callback:
                        callback(task)
        else:
            for task in pipeline.tasks:
                self.run_task(task)
                if callback:
                    callback(task)
        
        pipeline.completed_at = datetime.now().isoformat()
        
        # Status final
        if all(t.status == "completed" for t in pipeline.tasks):
            pipeline.status = "completed"
        elif any(t.status == "failed" for t in pipeline.tasks):
            pipeline.status = "partial"
        else:
            pipeline.status = "completed"
        
        return pipeline
    
    def quick_recon(self, target: str, modules: List[str] = None) -> Dict:
        """Reconhecimento rápido."""
        modules = modules or ["dns", "ports", "headers", "tech"]
        
        pipeline = self.create_pipeline(
            name=f"Quick Recon - {target}",
            description="Reconhecimento rápido automatizado"
        )
        
        for module in modules:
            if module in self.MODULES:
                self.add_task(pipeline, module, target)
        
        self.run_pipeline(pipeline)
        
        # Consolidar resultados
        results = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "modules": {}
        }
        
        for task in pipeline.tasks:
            results["modules"][task.task_type] = task.result
        
        return results
    
    def full_recon(self, target: str) -> Dict:
        """Reconhecimento completo."""
        return self.quick_recon(target, list(self.MODULES.keys()))
    
    def save_results(self, pipeline: ReconPipeline, filename: str):
        """Salva resultados do pipeline."""
        with open(filename, 'w') as f:
            json.dump(pipeline.to_dict(), f, indent=2, default=str)


def interactive_menu():
    """Menu interativo do Recon Automation."""
    automation = ReconAutomation()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║          🔍 RECON AUTOMATION - Olho de Deus                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] ⚡ Reconhecimento Rápido                                ║
║  [2] 🎯 Reconhecimento Completo                              ║
║  [3] 📋 Criar Pipeline Customizado                           ║
║  [4] 🔧 Executar Módulo Individual                           ║
║  [5] 📊 Ver Módulos Disponíveis                              ║
║  [6] 💾 Ver Pipelines Executados ({len(automation.pipelines)})                        ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Reconhecimento Rápido ===")
            target = input("Alvo (domínio ou IP): ").strip()
            
            if not target:
                continue
            
            print(f"\nExecutando recon rápido em {target}...")
            print("Módulos: dns, ports, headers, tech\n")
            
            results = automation.quick_recon(target)
            
            print("=" * 50)
            print(f"📊 RESULTADOS PARA: {target}")
            print("=" * 50)
            
            for module, data in results.get("modules", {}).items():
                print(f"\n📦 {module.upper()}")
                if data:
                    if data.get("success"):
                        if module == "dns" and data.get("records"):
                            for rtype, values in data["records"].items():
                                print(f"   {rtype}: {', '.join(values[:3])}")
                        
                        elif module == "ports":
                            open_ports = data.get("open_ports", [])
                            print(f"   Portas abertas: {open_ports if open_ports else 'Nenhuma'}")
                        
                        elif module == "headers":
                            print(f"   Status: {data.get('status_code')}")
                            sec = data.get("security_headers", {})
                            missing = [h for h, v in sec.items() if not v]
                            if missing:
                                print(f"   Headers faltando: {', '.join(missing[:3])}")
                        
                        elif module == "tech":
                            techs = data.get("technologies", [])
                            print(f"   Tecnologias: {', '.join(techs) if techs else 'N/A'}")
                    else:
                        print(f"   ❌ Erro: {data.get('error', 'Unknown')}")
            
            save = input("\nSalvar resultados? (s/n): ").lower()
            if save == 's':
                filename = f"recon_{target.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                print(f"✅ Salvo em {filename}")
        
        elif escolha == '2':
            print("\n=== Reconhecimento Completo ===")
            target = input("Alvo (domínio ou IP): ").strip()
            
            if not target:
                continue
            
            print(f"\nExecutando recon completo em {target}...")
            print(f"Módulos: {', '.join(automation.MODULES.keys())}\n")
            
            def progress_callback(task):
                status = "✅" if task.status == "completed" else "❌"
                print(f"  {status} {task.task_type}")
            
            pipeline = automation.create_pipeline(
                name=f"Full Recon - {target}",
                description="Reconhecimento completo"
            )
            
            for module in automation.MODULES:
                automation.add_task(pipeline, module, target)
            
            print("Executando tarefas...")
            automation.run_pipeline(pipeline, callback=progress_callback)
            
            print(f"\n✅ Pipeline {pipeline.status}")
            print(f"   Tarefas: {len(pipeline.tasks)}")
            print(f"   Completas: {sum(1 for t in pipeline.tasks if t.status == 'completed')}")
            
            save = input("\nSalvar resultados? (s/n): ").lower()
            if save == 's':
                filename = f"full_recon_{target.replace('.', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
                automation.save_results(pipeline, filename)
                print(f"✅ Salvo em {filename}")
        
        elif escolha == '3':
            print("\n=== Pipeline Customizado ===")
            name = input("Nome do pipeline: ").strip() or "Custom Pipeline"
            target = input("Alvo: ").strip()
            
            if not target:
                continue
            
            print(f"\nMódulos disponíveis: {', '.join(automation.MODULES.keys())}")
            modules_str = input("Módulos (separados por vírgula): ").strip()
            
            modules = [m.strip() for m in modules_str.split(",") if m.strip()]
            
            if not modules:
                print("❌ Nenhum módulo selecionado")
                input("Enter para continuar...")
                continue
            
            pipeline = automation.create_pipeline(name)
            
            for module in modules:
                if module in automation.MODULES:
                    automation.add_task(pipeline, module, target)
                    print(f"   ✅ {module} adicionado")
                else:
                    print(f"   ❌ {module} não encontrado")
            
            if pipeline.tasks:
                print(f"\nExecutando {len(pipeline.tasks)} tarefas...")
                automation.run_pipeline(pipeline)
                
                for task in pipeline.tasks:
                    status = "✅" if task.status == "completed" else "❌"
                    print(f"   {status} {task.task_type}: {task.status}")
        
        elif escolha == '4':
            print("\n=== Módulo Individual ===")
            print(f"Disponíveis: {', '.join(automation.MODULES.keys())}")
            
            module = input("Módulo: ").strip().lower()
            
            if module not in automation.MODULES:
                print("❌ Módulo não encontrado")
                input("Enter para continuar...")
                continue
            
            target = input("Alvo: ").strip()
            
            if not target:
                continue
            
            print(f"\nExecutando {module} em {target}...")
            
            func = automation.MODULES[module]
            result = func(target)
            
            print(f"\n📊 Resultado:")
            print(json.dumps(result, indent=2, default=str))
        
        elif escolha == '5':
            print("\n=== Módulos Disponíveis ===\n")
            
            descriptions = {
                "dns": "Lookup DNS (A, MX, NS, TXT, AAAA)",
                "ports": "Scan de portas comuns",
                "whois": "Informações WHOIS do domínio",
                "headers": "Headers HTTP e verificação de segurança",
                "subdomains": "Enumeração de subdomínios",
                "tech": "Detecção de tecnologias web",
            }
            
            for name, desc in descriptions.items():
                print(f"   📦 {name}")
                print(f"      {desc}\n")
        
        elif escolha == '6':
            print("\n=== Pipelines Executados ===\n")
            
            if not automation.pipelines:
                print("Nenhum pipeline executado ainda.")
            else:
                for i, pipeline in enumerate(automation.pipelines, 1):
                    status_icon = "✅" if pipeline.status == "completed" else "⚠️"
                    print(f"{i}. {status_icon} {pipeline.name}")
                    print(f"   Status: {pipeline.status}")
                    print(f"   Tarefas: {len(pipeline.tasks)}")
                    print(f"   Criado: {pipeline.created_at}")
                    print()
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
