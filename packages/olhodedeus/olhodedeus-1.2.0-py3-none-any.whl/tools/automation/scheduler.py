#!/usr/bin/env python3
"""
Task Scheduler - Agendador de tarefas de segurança
Parte do toolkit Olho de Deus
"""

import os
import sys
import json
import time
import threading
import schedule
import sqlite3
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from queue import Queue
import subprocess


@dataclass
class ScheduledTask:
    """Tarefa agendada."""
    id: int
    name: str
    task_type: str
    target: str
    schedule_type: str  # once, daily, weekly, hourly
    schedule_time: str  # HH:MM ou dia da semana
    options: Dict = field(default_factory=dict)
    enabled: bool = True
    last_run: str = ""
    next_run: str = ""
    last_result: str = ""
    created_at: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "task_type": self.task_type,
            "target": self.target,
            "schedule_type": self.schedule_type,
            "schedule_time": self.schedule_time,
            "options": self.options,
            "enabled": self.enabled,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "last_result": self.last_result,
            "created_at": self.created_at
        }


@dataclass
class TaskResult:
    """Resultado de execução de tarefa."""
    task_id: int
    task_name: str
    executed_at: str
    success: bool
    output: str
    error: str
    duration: float
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "executed_at": self.executed_at,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration": self.duration
        }


class TaskExecutor:
    """Executor de tarefas."""
    
    @staticmethod
    def execute_ping(target: str, options: Dict = None) -> Dict:
        """Ping simples."""
        try:
            param = "-n" if os.name == "nt" else "-c"
            count = options.get("count", 4) if options else 4
            
            result = subprocess.run(
                ["ping", param, str(count), target],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
    
    @staticmethod
    def execute_port_check(target: str, options: Dict = None) -> Dict:
        """Verifica se porta está aberta."""
        import socket
        
        port = options.get("port", 80) if options else 80
        timeout = options.get("timeout", 5) if options else 5
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((target, port))
            sock.close()
            
            is_open = result == 0
            return {
                "success": True,
                "output": f"Port {port} is {'OPEN' if is_open else 'CLOSED'}",
                "port_open": is_open
            }
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
    
    @staticmethod
    def execute_http_check(target: str, options: Dict = None) -> Dict:
        """Verifica disponibilidade HTTP."""
        import urllib.request
        import ssl
        
        url = target if target.startswith("http") else f"https://{target}"
        timeout = options.get("timeout", 10) if options else 10
        
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "OlhoDeDeus-Monitor/1.0")
            
            start = time.time()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
                status = response.status
                elapsed = time.time() - start
            
            return {
                "success": True,
                "output": f"HTTP {status} - {elapsed:.2f}s",
                "status_code": status,
                "response_time": elapsed
            }
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
    
    @staticmethod
    def execute_dns_check(target: str, options: Dict = None) -> Dict:
        """Verifica resolução DNS."""
        import socket
        
        try:
            start = time.time()
            ip = socket.gethostbyname(target)
            elapsed = time.time() - start
            
            return {
                "success": True,
                "output": f"{target} -> {ip} ({elapsed:.3f}s)",
                "ip": ip,
                "response_time": elapsed
            }
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
    
    @staticmethod
    def execute_script(target: str, options: Dict = None) -> Dict:
        """Executa script personalizado."""
        script_path = target
        
        if not os.path.exists(script_path):
            return {"success": False, "output": "", "error": "Script não encontrado"}
        
        try:
            if script_path.endswith(".py"):
                cmd = ["python", script_path]
            elif script_path.endswith(".sh"):
                cmd = ["bash", script_path]
            elif script_path.endswith(".bat"):
                cmd = [script_path]
            else:
                cmd = [script_path]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}


class TaskStore:
    """Armazenamento de tarefas."""
    
    def __init__(self, db_path: str = "scheduler.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializa banco de dados."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                target TEXT NOT NULL,
                schedule_type TEXT NOT NULL,
                schedule_time TEXT,
                options TEXT,
                enabled INTEGER DEFAULT 1,
                last_run TEXT,
                next_run TEXT,
                last_result TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                task_name TEXT,
                executed_at TEXT,
                success INTEGER,
                output TEXT,
                error TEXT,
                duration REAL,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_task(self, task: ScheduledTask) -> int:
        """Adiciona tarefa."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (name, task_type, target, schedule_type, schedule_time, options, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.name,
            task.task_type,
            task.target,
            task.schedule_type,
            task.schedule_time,
            json.dumps(task.options),
            1 if task.enabled else 0
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return task_id
    
    def get_task(self, task_id: int) -> Optional[ScheduledTask]:
        """Obtém tarefa por ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return ScheduledTask(
                id=row[0],
                name=row[1],
                task_type=row[2],
                target=row[3],
                schedule_type=row[4],
                schedule_time=row[5],
                options=json.loads(row[6]) if row[6] else {},
                enabled=bool(row[7]),
                last_run=row[8] or "",
                next_run=row[9] or "",
                last_result=row[10] or "",
                created_at=row[11]
            )
        
        return None
    
    def get_all_tasks(self, enabled_only: bool = False) -> List[ScheduledTask]:
        """Lista todas as tarefas."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if enabled_only:
            cursor.execute('SELECT * FROM tasks WHERE enabled = 1')
        else:
            cursor.execute('SELECT * FROM tasks')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            ScheduledTask(
                id=row[0],
                name=row[1],
                task_type=row[2],
                target=row[3],
                schedule_type=row[4],
                schedule_time=row[5],
                options=json.loads(row[6]) if row[6] else {},
                enabled=bool(row[7]),
                last_run=row[8] or "",
                next_run=row[9] or "",
                last_result=row[10] or "",
                created_at=row[11]
            )
            for row in rows
        ]
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        """Atualiza tarefa."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        for field in ['name', 'task_type', 'target', 'schedule_type', 'schedule_time', 'last_run', 'next_run', 'last_result']:
            if field in kwargs:
                updates.append(f'{field} = ?')
                values.append(kwargs[field])
        
        if 'enabled' in kwargs:
            updates.append('enabled = ?')
            values.append(1 if kwargs['enabled'] else 0)
        
        if 'options' in kwargs:
            updates.append('options = ?')
            values.append(json.dumps(kwargs['options']))
        
        if not updates:
            conn.close()
            return False
        
        values.append(task_id)
        
        cursor.execute(f'UPDATE tasks SET {", ".join(updates)} WHERE id = ?', values)
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success
    
    def delete_task(self, task_id: int) -> bool:
        """Remove tarefa."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        success = cursor.rowcount > 0
        
        cursor.execute('DELETE FROM task_history WHERE task_id = ?', (task_id,))
        
        conn.commit()
        conn.close()
        
        return success
    
    def add_history(self, result: TaskResult):
        """Adiciona resultado ao histórico."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO task_history (task_id, task_name, executed_at, success, output, error, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            result.task_id,
            result.task_name,
            result.executed_at,
            1 if result.success else 0,
            result.output[:1000],
            result.error[:500],
            result.duration
        ))
        
        conn.commit()
        conn.close()
    
    def get_history(self, task_id: int = None, limit: int = 50) -> List[TaskResult]:
        """Obtém histórico de execuções."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if task_id:
            cursor.execute('''
                SELECT * FROM task_history WHERE task_id = ? 
                ORDER BY executed_at DESC LIMIT ?
            ''', (task_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM task_history ORDER BY executed_at DESC LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            TaskResult(
                task_id=row[1],
                task_name=row[2],
                executed_at=row[3],
                success=bool(row[4]),
                output=row[5],
                error=row[6],
                duration=row[7]
            )
            for row in rows
        ]


class TaskScheduler:
    """Agendador de tarefas."""
    
    TASK_TYPES = {
        "ping": TaskExecutor.execute_ping,
        "port_check": TaskExecutor.execute_port_check,
        "http_check": TaskExecutor.execute_http_check,
        "dns_check": TaskExecutor.execute_dns_check,
        "script": TaskExecutor.execute_script,
    }
    
    def __init__(self):
        self.store = TaskStore()
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def execute_task(self, task: ScheduledTask) -> TaskResult:
        """Executa uma tarefa."""
        start_time = time.time()
        
        try:
            if task.task_type in self.TASK_TYPES:
                executor = self.TASK_TYPES[task.task_type]
                result_data = executor(task.target, task.options)
            else:
                result_data = {
                    "success": False,
                    "output": "",
                    "error": f"Tipo de tarefa desconhecido: {task.task_type}"
                }
        except Exception as e:
            result_data = {
                "success": False,
                "output": "",
                "error": str(e)
            }
        
        duration = time.time() - start_time
        executed_at = datetime.now().isoformat()
        
        result = TaskResult(
            task_id=task.id,
            task_name=task.name,
            executed_at=executed_at,
            success=result_data.get("success", False),
            output=result_data.get("output", ""),
            error=result_data.get("error", ""),
            duration=duration
        )
        
        # Atualizar task
        self.store.update_task(
            task.id,
            last_run=executed_at,
            last_result="success" if result.success else "failed"
        )
        
        # Salvar histórico
        self.store.add_history(result)
        
        return result
    
    def run_now(self, task_id: int) -> Optional[TaskResult]:
        """Executa tarefa imediatamente."""
        task = self.store.get_task(task_id)
        if task:
            return self.execute_task(task)
        return None


def interactive_menu():
    """Menu interativo do Task Scheduler."""
    scheduler = TaskScheduler()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        tasks = scheduler.store.get_all_tasks()
        enabled = sum(1 for t in tasks if t.enabled)
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║           ⏰ TASK SCHEDULER - Olho de Deus                   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Tarefas: {len(tasks):<3} (Ativas: {enabled})                                 ║
║                                                              ║
║  [1] ➕ Criar Tarefa                                         ║
║  [2] 📋 Listar Tarefas                                       ║
║  [3] ▶️  Executar Agora                                       ║
║  [4] ⏸️  Ativar/Desativar Tarefa                              ║
║  [5] 🗑️  Remover Tarefa                                       ║
║  [6] 📊 Ver Histórico                                        ║
║  [7] 🔧 Tipos de Tarefa                                      ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Criar Tarefa ===")
            
            name = input("Nome da tarefa: ").strip()
            if not name:
                continue
            
            print("\nTipos: ping, port_check, http_check, dns_check, script")
            task_type = input("Tipo: ").strip().lower()
            
            if task_type not in scheduler.TASK_TYPES:
                print("❌ Tipo inválido!")
                input("Enter para continuar...")
                continue
            
            target = input("Alvo (host/URL/caminho): ").strip()
            
            options = {}
            if task_type == "port_check":
                port = input("Porta (80): ").strip()
                options["port"] = int(port) if port else 80
            
            print("\nAgendamento: once, hourly, daily, weekly")
            schedule_type = input("Tipo: ").strip().lower() or "once"
            
            schedule_time = ""
            if schedule_type in ["daily", "weekly"]:
                schedule_time = input("Horário (HH:MM): ").strip() or "00:00"
            
            task = ScheduledTask(
                id=0,
                name=name,
                task_type=task_type,
                target=target,
                schedule_type=schedule_type,
                schedule_time=schedule_time,
                options=options,
                created_at=datetime.now().isoformat()
            )
            
            task_id = scheduler.store.add_task(task)
            print(f"\n✅ Tarefa #{task_id} criada!")
        
        elif escolha == '2':
            print("\n=== Tarefas ===\n")
            
            tasks = scheduler.store.get_all_tasks()
            
            if not tasks:
                print("Nenhuma tarefa cadastrada.")
            else:
                for task in tasks:
                    status = "✅" if task.enabled else "⏸️"
                    last = task.last_run[:16] if task.last_run else "Nunca"
                    result = "✓" if task.last_result == "success" else "✗" if task.last_result else "-"
                    
                    print(f"{status} [{task.id}] {task.name}")
                    print(f"      Tipo: {task.task_type} | Alvo: {task.target}")
                    print(f"      Agenda: {task.schedule_type} {task.schedule_time}")
                    print(f"      Última: {last} ({result})")
                    print()
        
        elif escolha == '3':
            print("\n=== Executar Agora ===")
            
            tasks = scheduler.store.get_all_tasks()
            if not tasks:
                print("Nenhuma tarefa cadastrada.")
                input("Enter para continuar...")
                continue
            
            print("Tarefas disponíveis:")
            for task in tasks:
                print(f"   [{task.id}] {task.name}")
            
            try:
                task_id = int(input("\nID da tarefa: ").strip())
                
                print(f"\nExecutando tarefa #{task_id}...")
                result = scheduler.run_now(task_id)
                
                if result:
                    status = "✅ Sucesso" if result.success else "❌ Falha"
                    print(f"\n{status} ({result.duration:.2f}s)")
                    
                    if result.output:
                        print(f"\nOutput:")
                        print(result.output[:500])
                    
                    if result.error:
                        print(f"\nErro: {result.error}")
                else:
                    print("❌ Tarefa não encontrada")
            except ValueError:
                print("❌ ID inválido")
        
        elif escolha == '4':
            print("\n=== Ativar/Desativar ===")
            
            try:
                task_id = int(input("ID da tarefa: ").strip())
                task = scheduler.store.get_task(task_id)
                
                if task:
                    new_state = not task.enabled
                    scheduler.store.update_task(task_id, enabled=new_state)
                    state_str = "ativada" if new_state else "desativada"
                    print(f"✅ Tarefa {state_str}!")
                else:
                    print("❌ Tarefa não encontrada")
            except ValueError:
                print("❌ ID inválido")
        
        elif escolha == '5':
            print("\n=== Remover Tarefa ===")
            
            try:
                task_id = int(input("ID da tarefa: ").strip())
                task = scheduler.store.get_task(task_id)
                
                if task:
                    confirm = input(f"Remover '{task.name}'? (s/n): ").lower()
                    if confirm == 's':
                        scheduler.store.delete_task(task_id)
                        print("✅ Tarefa removida!")
                else:
                    print("❌ Tarefa não encontrada")
            except ValueError:
                print("❌ ID inválido")
        
        elif escolha == '6':
            print("\n=== Histórico de Execuções ===\n")
            
            task_id_str = input("ID da tarefa (Enter para todas): ").strip()
            task_id = int(task_id_str) if task_id_str else None
            
            history = scheduler.store.get_history(task_id, limit=20)
            
            if not history:
                print("Nenhum registro no histórico.")
            else:
                for entry in history:
                    status = "✅" if entry.success else "❌"
                    print(f"{status} [{entry.task_name}]")
                    print(f"   Executado: {entry.executed_at[:19]}")
                    print(f"   Duração: {entry.duration:.2f}s")
                    if entry.error:
                        print(f"   Erro: {entry.error[:50]}")
                    print()
        
        elif escolha == '7':
            print("\n=== Tipos de Tarefa ===\n")
            
            types_info = {
                "ping": "Ping ICMP para verificar conectividade",
                "port_check": "Verifica se uma porta específica está aberta",
                "http_check": "Verifica disponibilidade de endpoint HTTP/HTTPS",
                "dns_check": "Verifica resolução DNS de um domínio",
                "script": "Executa um script personalizado (Python, Bash, Bat)",
            }
            
            for name, desc in types_info.items():
                print(f"   📦 {name}")
                print(f"      {desc}\n")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
