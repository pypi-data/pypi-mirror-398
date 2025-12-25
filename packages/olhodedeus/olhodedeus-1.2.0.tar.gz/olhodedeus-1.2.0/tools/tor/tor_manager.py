#!/usr/bin/env python3
"""
tor_manager.py

Gerenciador completo do Tor integrado ao Olho de Deus.
Instalação, configuração, verificação e uso.
"""
import os
import sys
import subprocess
import platform
import time
import json
import shutil
import zipfile
import tarfile
import hashlib
import socket
import threading
from typing import Optional, Dict, Tuple
from pathlib import Path

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import socks
    SOCKS_AVAILABLE = True
except ImportError:
    SOCKS_AVAILABLE = False

try:
    from stem import Signal
    from stem.control import Controller
    STEM_AVAILABLE = True
except ImportError:
    STEM_AVAILABLE = False


class TorManager:
    """
    Gerenciador completo do Tor.
    Instalação, configuração e controle.
    """
    
    # URLs de download do Tor Expert Bundle
    TOR_DOWNLOADS = {
        "windows": {
            "url": "https://archive.torproject.org/tor-package-archive/torbrowser/13.0.8/tor-expert-bundle-windows-x86_64-13.0.8.tar.gz",
            "fallback": "https://www.torproject.org/dist/torbrowser/13.0.8/tor-expert-bundle-windows-x86_64-13.0.8.tar.gz"
        },
        "linux": {
            "url": "https://archive.torproject.org/tor-package-archive/torbrowser/13.0.8/tor-expert-bundle-linux-x86_64-13.0.8.tar.gz",
            "fallback": "https://www.torproject.org/dist/torbrowser/13.0.8/tor-expert-bundle-linux-x86_64-13.0.8.tar.gz"
        }
    }
    
    def __init__(self, base_dir: str = None):
        """
        Inicializa o gerenciador do Tor.
        
        Args:
            base_dir: Diretório base do projeto (padrão: detecta automaticamente)
        """
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Detectar diretório base do projeto
            self.base_dir = Path(__file__).parent.parent.parent
        
        self.tor_dir = self.base_dir / "tools" / "tor" / "tor_bundle"
        self.config_file = self.base_dir / "config" / "tor_config.json"
        self.torrc_file = self.tor_dir / "torrc"
        self.data_dir = self.tor_dir / "data"
        
        # Configurações padrão
        self.config = self._load_config()
        
        # Processo do Tor
        self.tor_process: Optional[subprocess.Popen] = None
        self.is_running = False
        
        # Sessão HTTP com Tor
        self._session: Optional[requests.Session] = None
    
    def _load_config(self) -> Dict:
        """Carrega configuração do Tor."""
        default_config = {
            "socks_port": 9050,
            "control_port": 9051,
            "control_password": "olhodedeus",
            "auto_start": False,
            "bridges_enabled": False,
            "bridges": [],
            "exit_nodes": "",  # Ex: {br},{us}
            "exclude_nodes": "",  # Ex: {ru},{cn}
            "installed": False,
            "tor_path": ""
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved = json.load(f)
                    default_config.update(saved)
            except Exception:
                pass
        
        return default_config
    
    def _save_config(self):
        """Salva configuração do Tor."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def check_dependencies(self) -> Dict:
        """Verifica dependências Python necessárias."""
        deps = {
            "requests": REQUESTS_AVAILABLE,
            "PySocks": SOCKS_AVAILABLE,
            "stem": STEM_AVAILABLE
        }
        
        missing = [name for name, available in deps.items() if not available]
        
        return {
            "all_installed": len(missing) == 0,
            "installed": [name for name, available in deps.items() if available],
            "missing": missing,
            "install_cmd": f"pip install {' '.join(missing)}" if missing else None
        }
    
    def install_dependencies(self) -> bool:
        """Instala dependências Python necessárias."""
        deps = self.check_dependencies()
        
        if deps["all_installed"]:
            print("✅ Todas as dependências já estão instaladas!")
            return True
        
        print(f"📦 Instalando dependências: {', '.join(deps['missing'])}")
        
        try:
            # Usar pip do ambiente virtual se existir
            if platform.system() == "Windows":
                pip_path = self.base_dir / ".venv" / "Scripts" / "pip.exe"
            else:
                pip_path = self.base_dir / ".venv" / "bin" / "pip"
            
            if not pip_path.exists():
                pip_path = "pip"
            
            packages = ["requests", "PySocks", "stem", "requests[socks]"]
            cmd = [str(pip_path), "install", "--quiet"] + packages
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Dependências instaladas com sucesso!")
                return True
            else:
                print(f"❌ Erro: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao instalar dependências: {e}")
            return False
    
    def is_tor_installed(self) -> bool:
        """Verifica se o Tor está instalado."""
        # Verificar instalação local
        if platform.system() == "Windows":
            tor_exe = self.tor_dir / "tor" / "tor.exe"
        else:
            tor_exe = self.tor_dir / "tor" / "tor"
        
        if tor_exe.exists():
            self.config["installed"] = True
            self.config["tor_path"] = str(tor_exe)
            self._save_config()
            return True
        
        # Verificar instalação do sistema
        system_tor = shutil.which("tor")
        if system_tor:
            self.config["installed"] = True
            self.config["tor_path"] = system_tor
            self._save_config()
            return True
        
        return False
    
    def download_tor(self) -> bool:
        """Baixa o Tor Expert Bundle."""
        if not REQUESTS_AVAILABLE:
            print("❌ Módulo 'requests' não instalado. Execute primeiro:")
            print("   pip install requests")
            return False
        
        system = "windows" if platform.system() == "Windows" else "linux"
        urls = self.TOR_DOWNLOADS.get(system)
        
        if not urls:
            print(f"❌ Sistema não suportado: {platform.system()}")
            return False
        
        self.tor_dir.mkdir(parents=True, exist_ok=True)
        download_path = self.tor_dir / "tor_bundle.tar.gz"
        
        print(f"📥 Baixando Tor Expert Bundle para {system}...")
        
        for url in [urls["url"], urls["fallback"]]:
            try:
                print(f"   Tentando: {url[:60]}...")
                
                resp = requests.get(url, stream=True, timeout=120)
                resp.raise_for_status()
                
                total_size = int(resp.headers.get('content-length', 0))
                downloaded = 0
                
                with open(download_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            pct = (downloaded / total_size) * 100
                            print(f"\r   Progresso: {pct:.1f}%", end="", flush=True)
                
                print("\n✅ Download concluído!")
                return self._extract_tor(download_path)
                
            except Exception as e:
                print(f"\n   ❌ Falhou: {e}")
                continue
        
        print("❌ Não foi possível baixar o Tor de nenhuma fonte.")
        return False
    
    def _extract_tor(self, archive_path: Path) -> bool:
        """Extrai o arquivo do Tor."""
        print("📦 Extraindo Tor...")
        
        try:
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(self.tor_dir)
            
            # Remover arquivo baixado
            archive_path.unlink()
            
            # Verificar se extraiu corretamente
            if self.is_tor_installed():
                print("✅ Tor instalado com sucesso!")
                return True
            else:
                print("❌ Extração falhou - executável não encontrado")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao extrair: {e}")
            return False
    
    def create_torrc(self) -> str:
        """Cria arquivo de configuração do Tor."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Hash da senha para controle
        # Usar hash simples por enquanto (em produção, usar tor --hash-password)
        hashed_password = f"16:{hashlib.sha256(self.config['control_password'].encode()).hexdigest()}"
        
        torrc_content = f"""# Tor Configuration - Olho de Deus
# Gerado automaticamente

# Porta SOCKS5 para conexões
SocksPort {self.config['socks_port']}

# Porta de controle
ControlPort {self.config['control_port']}

# Senha de controle (hash)
# HashedControlPassword {hashed_password}
# Usando CookieAuthentication por simplicidade
CookieAuthentication 1

# Diretório de dados
DataDirectory {self.data_dir.as_posix()}

# Logs
Log notice file {(self.tor_dir / 'tor.log').as_posix()}

# Performance
NumEntryGuards 3
KeepalivePeriod 60

# Segurança
SafeSocks 1
TestSocks 1

# Circuito
CircuitBuildTimeout 30
LearnCircuitBuildTimeout 1
"""
        
        # Adicionar nós de saída se configurado
        if self.config.get("exit_nodes"):
            torrc_content += f"\n# Nós de saída preferidos\nExitNodes {self.config['exit_nodes']}\n"
        
        if self.config.get("exclude_nodes"):
            torrc_content += f"\n# Nós excluídos\nExcludeNodes {self.config['exclude_nodes']}\n"
        
        # Adicionar bridges se habilitado
        if self.config.get("bridges_enabled") and self.config.get("bridges"):
            torrc_content += "\n# Bridges (para contornar bloqueios)\nUseBridges 1\n"
            for bridge in self.config["bridges"]:
                torrc_content += f"Bridge {bridge}\n"
        
        with open(self.torrc_file, 'w') as f:
            f.write(torrc_content)
        
        return str(self.torrc_file)
    
    def start_tor(self) -> bool:
        """Inicia o processo do Tor."""
        if self.is_running:
            print("⚠️ Tor já está em execução!")
            return True
        
        if not self.is_tor_installed():
            print("❌ Tor não está instalado. Execute install() primeiro.")
            return False
        
        # Criar configuração
        torrc_path = self.create_torrc()
        tor_path = self.config["tor_path"]
        
        print(f"🧅 Iniciando Tor...")
        print(f"   Executável: {tor_path}")
        print(f"   Configuração: {torrc_path}")
        
        try:
            # Iniciar processo do Tor
            if platform.system() == "Windows":
                # No Windows, usar CREATE_NEW_PROCESS_GROUP para não herdar console
                self.tor_process = subprocess.Popen(
                    [tor_path, "-f", torrc_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                self.tor_process = subprocess.Popen(
                    [tor_path, "-f", torrc_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # Aguardar Tor iniciar (máximo 60 segundos)
            print("   Aguardando bootstrap...", end="", flush=True)
            
            for i in range(60):
                time.sleep(1)
                print(".", end="", flush=True)
                
                # Verificar se a porta SOCKS está aberta
                if self._check_port(self.config["socks_port"]):
                    self.is_running = True
                    print(f"\n✅ Tor iniciado! (SOCKS: localhost:{self.config['socks_port']})")
                    return True
                
                # Verificar se processo morreu
                if self.tor_process.poll() is not None:
                    stderr = self.tor_process.stderr.read().decode()
                    print(f"\n❌ Tor encerrou prematuramente: {stderr[:200]}")
                    return False
            
            print("\n❌ Timeout aguardando Tor iniciar")
            self.stop_tor()
            return False
            
        except Exception as e:
            print(f"\n❌ Erro ao iniciar Tor: {e}")
            return False
    
    def stop_tor(self) -> bool:
        """Para o processo do Tor."""
        if self.tor_process:
            print("🛑 Parando Tor...")
            try:
                self.tor_process.terminate()
                self.tor_process.wait(timeout=10)
                self.is_running = False
                print("✅ Tor parado!")
                return True
            except Exception as e:
                print(f"❌ Erro ao parar Tor: {e}")
                try:
                    self.tor_process.kill()
                except Exception:
                    pass
                return False
        return True
    
    def _check_port(self, port: int) -> bool:
        """Verifica se uma porta está aberta."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def get_new_identity(self) -> bool:
        """Solicita nova identidade (novo IP) ao Tor."""
        if not STEM_AVAILABLE:
            print("❌ Módulo 'stem' não instalado")
            return False
        
        try:
            with Controller.from_port(port=self.config["control_port"]) as controller:
                controller.authenticate()
                controller.signal(Signal.NEWNYM)
                print("✅ Nova identidade solicitada! Aguarde ~10 segundos para novo circuito.")
                return True
        except Exception as e:
            print(f"❌ Erro ao solicitar nova identidade: {e}")
            return False
    
    def check_connection(self) -> Dict:
        """Verifica conexão Tor e retorna informações."""
        if not REQUESTS_AVAILABLE or not SOCKS_AVAILABLE:
            return {"connected": False, "error": "Dependências não instaladas"}
        
        try:
            session = self.get_session()
            
            # Verificar no check.torproject.org
            resp = session.get('https://check.torproject.org/api/ip', timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "connected": True,
                    "is_tor": data.get("IsTor", False),
                    "ip": data.get("IP", "Unknown"),
                    "message": "✅ Conectado via Tor!" if data.get("IsTor") else "⚠️ Conectado, mas NÃO via Tor!"
                }
        except Exception as e:
            return {
                "connected": False,
                "is_tor": False,
                "error": str(e),
                "message": f"❌ Erro de conexão: {e}"
            }
        
        return {"connected": False, "message": "❌ Falha na verificação"}
    
    def get_session(self) -> requests.Session:
        """Retorna sessão HTTP configurada para usar Tor."""
        if self._session is None:
            self._session = requests.Session()
            self._session.proxies = {
                'http': f'socks5h://127.0.0.1:{self.config["socks_port"]}',
                'https': f'socks5h://127.0.0.1:{self.config["socks_port"]}'
            }
            self._session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0'
            })
        return self._session
    
    def fetch_onion(self, url: str, timeout: int = 60) -> Optional[requests.Response]:
        """Faz request para um site .onion."""
        if not url.endswith('.onion') and '.onion/' not in url:
            print("⚠️ URL não é um endereço .onion")
        
        try:
            session = self.get_session()
            return session.get(url, timeout=timeout)
        except Exception as e:
            print(f"❌ Erro ao acessar {url}: {e}")
            return None
    
    def install(self) -> bool:
        """Instalação completa do Tor."""
        print("="*60)
        print("🧅 INSTALAÇÃO DO TOR - Olho de Deus")
        print("="*60)
        
        # 1. Verificar/instalar dependências Python
        print("\n[1/3] Verificando dependências Python...")
        if not self.check_dependencies()["all_installed"]:
            if not self.install_dependencies():
                return False
        else:
            print("✅ Dependências OK")
        
        # 2. Verificar/baixar Tor
        print("\n[2/3] Verificando instalação do Tor...")
        if not self.is_tor_installed():
            print("   Tor não encontrado. Baixando...")
            if not self.download_tor():
                return False
        else:
            print(f"✅ Tor encontrado: {self.config['tor_path']}")
        
        # 3. Criar configuração
        print("\n[3/3] Criando configuração...")
        self.create_torrc()
        print(f"✅ Configuração criada: {self.torrc_file}")
        
        print("\n" + "="*60)
        print("✅ INSTALAÇÃO CONCLUÍDA!")
        print("="*60)
        print(f"\nPara iniciar o Tor, use: tor_manager.start_tor()")
        print(f"Porta SOCKS: {self.config['socks_port']}")
        print(f"Porta Control: {self.config['control_port']}")
        
        return True
    
    def get_status(self) -> Dict:
        """Retorna status completo do Tor."""
        deps = self.check_dependencies()
        installed = self.is_tor_installed()
        port_open = self._check_port(self.config["socks_port"])
        
        status = {
            "dependencies": deps,
            "installed": installed,
            "tor_path": self.config.get("tor_path", ""),
            "socks_port": self.config["socks_port"],
            "control_port": self.config["control_port"],
            "port_open": port_open,
            "process_running": self.tor_process is not None and self.tor_process.poll() is None,
            "is_running": self.is_running or port_open
        }
        
        if port_open:
            status["connection"] = self.check_connection()
        
        return status


def interactive_menu():
    """Menu interativo do gerenciador Tor."""
    manager = TorManager()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Verificar status
        status = manager.get_status()
        tor_status = "🟢 ONLINE" if status["is_running"] else "🔴 OFFLINE"
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║              🧅 TOR MANAGER - Olho de Deus                   ║
╠══════════════════════════════════════════════════════════════╣
║  Status: {tor_status}                                          
║  Porta SOCKS: {status['socks_port']}                                         
║  Instalado: {'✅ Sim' if status['installed'] else '❌ Não'}                                          
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ──── ⚙️ INSTALAÇÃO ────                                      ║
║  [1] 📦 Instalar Tor (automático)                            ║
║  [2] 📚 Instalar dependências Python                         ║
║                                                              ║
║  ──── 🔄 CONTROLE ────                                       ║
║  [3] ▶️  Iniciar Tor                                          ║
║  [4] ⏹️  Parar Tor                                            ║
║  [5] 🔄 Nova Identidade (novo IP)                            ║
║                                                              ║
║  ──── 🔍 VERIFICAÇÃO ────                                    ║
║  [6] 🌐 Verificar conexão Tor                                ║
║  [7] 📊 Ver status completo                                  ║
║  [8] 🧅 Testar site .onion                                   ║
║                                                              ║
║  ──── ⚙️ CONFIGURAÇÃO ────                                    ║
║  [9] ⚙️  Configurar portas                                    ║
║  [10] 🌍 Configurar nós de saída                             ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            print("\n")
            manager.install()
            input("\nPressione Enter para continuar...")
        
        elif choice == '2':
            print("\n")
            manager.install_dependencies()
            input("\nPressione Enter para continuar...")
        
        elif choice == '3':
            print("\n")
            manager.start_tor()
            input("\nPressione Enter para continuar...")
        
        elif choice == '4':
            print("\n")
            manager.stop_tor()
            input("\nPressione Enter para continuar...")
        
        elif choice == '5':
            print("\n")
            manager.get_new_identity()
            input("\nPressione Enter para continuar...")
        
        elif choice == '6':
            print("\n🔍 Verificando conexão Tor...\n")
            result = manager.check_connection()
            print(result.get("message", "Erro"))
            if result.get("is_tor"):
                print(f"   IP Tor: {result.get('ip', 'N/A')}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '7':
            print("\n📊 STATUS COMPLETO:\n")
            status = manager.get_status()
            
            print(f"  Dependências Python:")
            for dep in ["requests", "PySocks", "stem"]:
                ok = dep in status["dependencies"]["installed"]
                print(f"    • {dep}: {'✅' if ok else '❌'}")
            
            print(f"\n  Tor:")
            print(f"    • Instalado: {'✅' if status['installed'] else '❌'}")
            print(f"    • Path: {status.get('tor_path', 'N/A')}")
            print(f"    • Porta SOCKS aberta: {'✅' if status['port_open'] else '❌'}")
            print(f"    • Processo ativo: {'✅' if status['process_running'] else '❌'}")
            
            if status.get("connection"):
                conn = status["connection"]
                print(f"\n  Conexão:")
                print(f"    • {conn.get('message', 'N/A')}")
                if conn.get("ip"):
                    print(f"    • IP: {conn['ip']}")
            
            input("\nPressione Enter para continuar...")
        
        elif choice == '8':
            url = input("\n🧅 Digite URL .onion: ").strip()
            if url:
                if not url.startswith("http"):
                    url = "http://" + url
                print(f"\n🔍 Acessando {url}...")
                resp = manager.fetch_onion(url, timeout=60)
                if resp:
                    print(f"✅ Status: {resp.status_code}")
                    print(f"   Tamanho: {len(resp.content)} bytes")
                    
                    show = input("\nMostrar conteúdo? (s/n): ").strip().lower()
                    if show == 's':
                        print("\n" + "="*60)
                        print(resp.text[:2000])
                        if len(resp.text) > 2000:
                            print("\n... [truncado]")
                        print("="*60)
                else:
                    print("❌ Falha ao acessar")
            input("\nPressione Enter para continuar...")
        
        elif choice == '9':
            print("\n⚙️ CONFIGURAR PORTAS\n")
            print(f"  Porta SOCKS atual: {manager.config['socks_port']}")
            print(f"  Porta Control atual: {manager.config['control_port']}")
            
            socks = input("\nNova porta SOCKS (Enter para manter): ").strip()
            if socks.isdigit():
                manager.config['socks_port'] = int(socks)
            
            ctrl = input("Nova porta Control (Enter para manter): ").strip()
            if ctrl.isdigit():
                manager.config['control_port'] = int(ctrl)
            
            manager._save_config()
            print("\n✅ Configuração salva!")
            input("\nPressione Enter para continuar...")
        
        elif choice == '10':
            print("\n🌍 CONFIGURAR NÓS DE SAÍDA\n")
            print("  Use códigos de país entre chaves. Ex: {br},{us},{de}")
            print(f"  Atual: {manager.config.get('exit_nodes', 'Nenhum')}")
            
            nodes = input("\nNós de saída (Enter para limpar): ").strip()
            manager.config['exit_nodes'] = nodes
            
            print(f"\n  Nós excluídos atual: {manager.config.get('exclude_nodes', 'Nenhum')}")
            exclude = input("Nós a excluir (Enter para limpar): ").strip()
            manager.config['exclude_nodes'] = exclude
            
            manager._save_config()
            manager.create_torrc()
            print("\n✅ Configuração salva! Reinicie o Tor para aplicar.")
            input("\nPressione Enter para continuar...")
        
        elif choice == '0':
            # Perguntar se quer parar o Tor ao sair
            if manager.is_running:
                stop = input("\nParar Tor antes de sair? (s/n): ").strip().lower()
                if stop == 's':
                    manager.stop_tor()
            break


# Instância global para fácil acesso
_tor_manager: Optional[TorManager] = None

def get_tor_manager() -> TorManager:
    """Retorna instância global do TorManager."""
    global _tor_manager
    if _tor_manager is None:
        _tor_manager = TorManager()
    return _tor_manager


if __name__ == '__main__':
    interactive_menu()
