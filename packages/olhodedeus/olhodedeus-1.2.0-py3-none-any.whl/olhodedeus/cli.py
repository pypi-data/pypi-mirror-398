#!/usr/bin/env python3
"""
Olho de Deus - Command Line Interface
=====================================

Uso:
    olhodedeus              # Menu interativo completo
    olhodedeus leak EMAIL   # Verificar vazamento de email
    olhodedeus ip IP        # Geolocalização de IP  
    olhodedeus user USER    # OSINT de username
    olhodedeus scan HOST    # Port scan
    olhodedeus api          # Iniciar servidor API
    
Atalhos:
    odd                     # Igual a olhodedeus
    olho                    # Igual a olhodedeus
"""

import sys
import os
import argparse
from typing import Optional

# Adiciona path do projeto para imports
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_PATH not in sys.path:
    sys.path.insert(0, BASE_PATH)

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    import colorama
    colorama.init()
except ImportError:
    pass


# ═══════════════════════════════════════════════════════════════
# CONSTANTES E CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════

VERSION = "1.0.0"

BANNER = r"""
\033[91m
   ██████╗ ██╗     ██╗  ██╗ ██████╗     ██████╗ ███████╗    ██████╗ ███████╗██╗   ██╗███████╗
  ██╔═══██╗██║     ██║  ██║██╔═══██╗    ██╔══██╗██╔════╝    ██╔══██╗██╔════╝██║   ██║██╔════╝
  ██║   ██║██║     ███████║██║   ██║    ██║  ██║█████╗      ██║  ██║█████╗  ██║   ██║███████╗
  ██║   ██║██║     ██╔══██║██║   ██║    ██║  ██║██╔══╝      ██║  ██║██╔══╝  ██║   ██║╚════██║
  ╚██████╔╝███████╗██║  ██║╚██████╔╝    ██████╔╝███████╗    ██████╔╝███████╗╚██████╔╝███████║
   ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝     ╚═════╝ ╚══════╝    ╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝
\033[0m
\033[93m                        👁️  OSINT & Security Analysis Tool v{version}
                             Acessível de qualquer lugar via terminal\033[0m
""".format(version=VERSION)


# ═══════════════════════════════════════════════════════════════
# FUNÇÕES UTILITÁRIAS
# ═══════════════════════════════════════════════════════════════

def clear_screen():
    """Limpa a tela do terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Exibe o banner do programa."""
    print(BANNER)


def print_success(msg: str):
    """Mensagem de sucesso."""
    print(f"\033[92m✓ {msg}\033[0m")


def print_error(msg: str):
    """Mensagem de erro."""
    print(f"\033[91m✗ {msg}\033[0m")


def print_info(msg: str):
    """Mensagem informativa."""
    print(f"\033[94mℹ {msg}\033[0m")


def print_warning(msg: str):
    """Mensagem de aviso."""
    print(f"\033[93m⚠ {msg}\033[0m")


def print_result_table(title: str, data: dict):
    """Exibe resultado em formato de tabela."""
    if RICH_AVAILABLE:
        console = Console()
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("Campo", style="dim")
        table.add_column("Valor")
        
        for key, value in data.items():
            if isinstance(value, dict):
                value = str(value)
            table.add_row(str(key), str(value))
        
        console.print(table)
    else:
        print(f"\n{'═' * 50}")
        print(f"  {title}")
        print(f"{'═' * 50}")
        for key, value in data.items():
            print(f"  {key}: {value}")
        print(f"{'═' * 50}\n")


# ═══════════════════════════════════════════════════════════════
# COMANDOS CLI
# ═══════════════════════════════════════════════════════════════

def cmd_interactive():
    """Inicia o menu interativo completo."""
    try:
        # Tenta usar o menu completo do app/main.py
        from app.main import main as app_main
        
        clear_screen()
        # app_main já tem autenticação e menu
        app_main()
    except ImportError as e:
        print_warning(f"Módulo principal não disponível: {e}")
        print_info("Iniciando versão lite...")
        interactive_menu_lite()


def cmd_leak_check(email: str):
    """Verifica vazamento de email."""
    print_info(f"Verificando vazamentos para: {email}")
    
    try:
        from olhodedeus.core import OlhoDeDeus
        odd = OlhoDeDeus()
        result = odd.check_leak(email)
        
        if "error" in result:
            print_error(result["error"])
        else:
            print_result_table(f"Resultado para {email}", result)
    except Exception as e:
        print_error(f"Erro: {e}")


def cmd_ip_lookup(ip: str):
    """Geolocalização de IP."""
    print_info(f"Consultando geolocalização de: {ip}")
    
    try:
        from olhodedeus.core import OlhoDeDeus
        odd = OlhoDeDeus()
        result = odd.ip_lookup(ip)
        
        if "error" in result:
            print_error(result["error"])
        else:
            print_result_table(f"Geolocalização de {ip}", result)
    except Exception as e:
        print_error(f"Erro: {e}")


def cmd_username_osint(username: str):
    """OSINT de username em redes sociais."""
    print_info(f"Verificando username: {username}")
    
    try:
        from olhodedeus.core import OlhoDeDeus
        odd = OlhoDeDeus()
        result = odd.username_osint(username)
        
        print(f"\n\033[1mResultados para @{username}:\033[0m\n")
        
        for platform, data in result.get("platforms", {}).items():
            if data.get("found"):
                print_success(f"{platform}: Encontrado - {data['url']}")
            elif data.get("found") is False:
                print_error(f"{platform}: Não encontrado")
            else:
                print_warning(f"{platform}: Erro na verificação")
                
    except Exception as e:
        print_error(f"Erro: {e}")


def cmd_port_scan(target: str, ports: str = "1-1000"):
    """Realiza port scan."""
    print_info(f"Escaneando {target} (portas: {ports})")
    print_warning("Certifique-se de ter autorização para escanear este alvo!")
    
    try:
        from olhodedeus.core import OlhoDeDeus
        odd = OlhoDeDeus()
        result = odd.port_scan(target, ports)
        
        if "error" in result:
            print_error(result["error"])
        else:
            print_result_table(f"Port Scan - {target}", result)
    except Exception as e:
        print_error(f"Erro: {e}")


def cmd_subdomain(domain: str):
    """Enumera subdomínios."""
    print_info(f"Enumerando subdomínios de: {domain}")
    
    try:
        from olhodedeus.core import OlhoDeDeus
        odd = OlhoDeDeus()
        result = odd.subdomain_enum(domain)
        
        if "error" in result:
            print_error(result["error"])
        else:
            subdomains = result.get("subdomains", [])
            print_success(f"Encontrados {len(subdomains)} subdomínios:")
            for sub in subdomains:
                print(f"  • {sub}")
    except Exception as e:
        print_error(f"Erro: {e}")


def cmd_api(host: str = "0.0.0.0", port: int = 8080, api_key: str = None):
    """Inicia o servidor API."""
    print_info(f"Iniciando API em {host}:{port}")
    
    if not api_key:
        print_warning("API iniciada SEM autenticação! Use --api-key para segurança.")
    
    try:
        from olhodedeus.core import OlhoDeDeus
        odd = OlhoDeDeus()
        odd.start_api(host=host, port=port, api_key=api_key)
    except Exception as e:
        print_error(f"Erro ao iniciar API: {e}")


def cmd_login():
    """Login interativo."""
    from olhodedeus.auth import AuthManager
    auth = AuthManager()
    user = auth.interactive_login(clear_screen)
    if user:
        print_success(f"Logado como: {user}")
        token = auth._current_token
        print_info(f"Token de sessão: {token[:20]}...")
        return user
    return None


def cmd_users():
    """Gerenciamento de usuários."""
    from olhodedeus.auth import interactive_user_management
    interactive_user_management()


def cmd_generate_key(username: str = None):
    """Gera uma API key para acesso remoto."""
    from olhodedeus.auth import AuthManager
    auth = AuthManager()
    
    if not username:
        # Lista usuários disponíveis
        users = auth.list_users()
        if not users:
            print_error("Nenhum usuário cadastrado! Crie um primeiro com: olhodedeus login")
            return
        
        print("\nUsuários disponíveis:")
        for u in users:
            print(f"  • {u['username']} ({u['role']})")
        
        username = input("\nUsuário para a API Key: ").strip()
    
    if username not in auth.users:
        print_error(f"Usuário '{username}' não encontrado!")
        return
    
    name = input("Nome da key (ex: 'meu-notebook'): ").strip() or "cli-generated"
    
    key = auth.create_api_key(username, name)
    
    print_success("API Key criada com sucesso!")
    print(f"\n  🔑 {key}\n")
    print_warning("Guarde esta chave! Ela não será mostrada novamente.")
    print_info("Use com: olhodedeus api --api-key SUA_CHAVE")
    print_info("Ou via curl: curl -H 'X-API-Key: SUA_CHAVE' http://host:porta/api/...")


def cmd_sync(action: str = None):
    """Sincroniza auth entre PCs via GitHub."""
    from olhodedeus.sync import cmd_sync as sync_cmd
    sync_cmd(action)


def interactive_menu_lite():
    """Menu interativo simplificado (fallback)."""
    from olhodedeus.auth import AuthManager
    
    # Autenticação primeiro
    clear_screen()
    print_banner()
    
    auth = AuthManager()
    usuario = auth.interactive_login(clear_screen)
    
    if not usuario:
        print_error("Autenticação necessária!")
        return
    
    while True:
        clear_screen()
        print_banner()
        
        print("""
\033[96m╔══════════════════════════════════════════════════════════════╗
║                     MENU PRINCIPAL                           ║
╠══════════════════════════════════════════════════════════════╣\033[0m
║                                                              ║
║  \033[93m[1]\033[0m 📧 Verificar vazamento de email                       ║
║  \033[93m[2]\033[0m 🌍 Geolocalização de IP                                ║
║  \033[93m[3]\033[0m 👤 OSINT de username                                   ║
║  \033[93m[4]\033[0m 🔌 Port Scan                                           ║
║  \033[93m[5]\033[0m 🌐 Enumerar subdomínios                                ║
║  \033[93m[6]\033[0m 🚀 Iniciar servidor API                                ║
║                                                              ║
║  \033[91m[0]\033[0m Sair                                                   ║
\033[96m╚══════════════════════════════════════════════════════════════╝\033[0m
        """)
        
        choice = input("\033[92mOpção: \033[0m").strip()
        
        if choice == '0':
            print_info("Até logo!")
            break
        elif choice == '1':
            email = input("\nEmail para verificar: ").strip()
            if email:
                cmd_leak_check(email)
            input("\nPressione Enter...")
        elif choice == '2':
            ip = input("\nIP para consultar: ").strip()
            if ip:
                cmd_ip_lookup(ip)
            input("\nPressione Enter...")
        elif choice == '3':
            username = input("\nUsername para verificar: ").strip()
            if username:
                cmd_username_osint(username)
            input("\nPressione Enter...")
        elif choice == '4':
            target = input("\nAlvo (IP/hostname): ").strip()
            ports = input("Portas [1-1000]: ").strip() or "1-1000"
            if target:
                cmd_port_scan(target, ports)
            input("\nPressione Enter...")
        elif choice == '5':
            domain = input("\nDomínio: ").strip()
            if domain:
                cmd_subdomain(domain)
            input("\nPressione Enter...")
        elif choice == '6':
            host = input("\nHost [0.0.0.0]: ").strip() or "0.0.0.0"
            port = input("Porta [8080]: ").strip() or "8080"
            api_key = input("API Key (Enter para nenhuma): ").strip()
            cmd_api(host, int(port), api_key if api_key else None)


# ═══════════════════════════════════════════════════════════════
# PARSER DE ARGUMENTOS
# ═══════════════════════════════════════════════════════════════

def create_parser():
    """Cria o parser de argumentos CLI."""
    parser = argparse.ArgumentParser(
        prog='olhodedeus',
        description='👁️ Olho de Deus - Ferramenta OSINT e Análise de Segurança',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  olhodedeus                        # Menu interativo
  olhodedeus leak email@teste.com   # Verificar vazamento
  olhodedeus ip 8.8.8.8             # Geolocalização
  olhodedeus user johndoe           # OSINT de username
  olhodedeus scan 192.168.1.1       # Port scan
  olhodedeus sub exemplo.com        # Enumerar subdomínios
  olhodedeus api --port 9000        # Iniciar API

Atalhos disponíveis: odd, olho
        """
    )
    
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {VERSION}')
    parser.add_argument('-q', '--quiet', action='store_true', help='Modo silencioso (sem banner)')
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Comando: leak
    leak_parser = subparsers.add_parser('leak', help='Verificar vazamento de email')
    leak_parser.add_argument('email', help='Email para verificar')
    
    # Comando: ip
    ip_parser = subparsers.add_parser('ip', help='Geolocalização de IP')
    ip_parser.add_argument('address', help='Endereço IP')
    
    # Comando: user
    user_parser = subparsers.add_parser('user', help='OSINT de username')
    user_parser.add_argument('username', help='Username para verificar')
    user_parser.add_argument('-p', '--platforms', nargs='+', help='Plataformas específicas')
    
    # Comando: scan
    scan_parser = subparsers.add_parser('scan', help='Port scan')
    scan_parser.add_argument('target', help='IP ou hostname alvo')
    scan_parser.add_argument('-p', '--ports', default='1-1000', help='Range de portas (ex: 1-1000, 80,443)')
    
    # Comando: sub
    sub_parser = subparsers.add_parser('sub', help='Enumerar subdomínios')
    sub_parser.add_argument('domain', help='Domínio alvo')
    
    # Comando: api
    api_parser = subparsers.add_parser('api', help='Iniciar servidor API REST')
    api_parser.add_argument('--host', default='0.0.0.0', help='Host para bind (default: 0.0.0.0)')
    api_parser.add_argument('--port', type=int, default=8080, help='Porta (default: 8080)')
    api_parser.add_argument('--api-key', help='API Key para autenticação')
    
    # Comando: login
    login_parser = subparsers.add_parser('login', help='Fazer login / criar usuário')
    
    # Comando: users
    users_parser = subparsers.add_parser('users', help='Gerenciar usuários e API keys')
    
    # Comando: genkey
    genkey_parser = subparsers.add_parser('genkey', help='Gerar API key para acesso remoto')
    genkey_parser.add_argument('--user', help='Usuário para a API key')
    
    # Comando: sync
    sync_parser = subparsers.add_parser('sync', help='Sincronizar auth entre PCs via GitHub')
    sync_parser.add_argument('--setup', action='store_true', help='Configurar sincronização')
    sync_parser.add_argument('--push', action='store_true', help='Enviar auth para GitHub')
    sync_parser.add_argument('--pull', action='store_true', help='Baixar auth do GitHub')
    sync_parser.add_argument('--status', action='store_true', help='Ver status da sync')
    
    return parser


# ═══════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def main():
    """Entry point principal do CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Se não houver comando, inicia modo interativo
    if not args.command:
        if not args.quiet:
            clear_screen()
            print_banner()
        cmd_interactive()
        return
    
    # Executa comando específico
    if not args.quiet:
        print_banner()
    
    if args.command == 'leak':
        cmd_leak_check(args.email)
    
    elif args.command == 'ip':
        cmd_ip_lookup(args.address)
    
    elif args.command == 'user':
        cmd_username_osint(args.username)
    
    elif args.command == 'scan':
        cmd_port_scan(args.target, args.ports)
    
    elif args.command == 'sub':
        cmd_subdomain(args.domain)
    
    elif args.command == 'api':
        cmd_api(args.host, args.port, args.api_key)
    
    elif args.command == 'login':
        cmd_login()
    
    elif args.command == 'users':
        cmd_users()
    
    elif args.command == 'genkey':
        cmd_generate_key(args.user)
    
    elif args.command == 'sync':
        if args.setup:
            cmd_sync("setup")
        elif args.push:
            cmd_sync("push")
        elif args.pull:
            cmd_sync("pull")
        else:
            cmd_sync("status")


if __name__ == '__main__':
    main()
