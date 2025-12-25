import os
import platform
import subprocess
import requests
import sys
from shutil import which

# --- Ferramentas necessárias ---
# URL do instalador para Windows. Pode precisar ser atualizado no futuro.
NMAP_WINDOWS_URL = "https://nmap.org/dist/nmap-7.95-setup.exe"

REQUIRED_TOOLS = {
    'nmap': {
        'linux_install': 'sudo apt update && sudo apt install nmap',
        'windows_install': 'winget install nmap',
        'windows_download_url': NMAP_WINDOWS_URL
    },
    'git': {
        'linux_install': 'sudo apt install git',
        'windows_install': 'winget install git'
    },
    'nikto': {
        'linux_install': 'sudo apt install nikto'
    },
    'sqlmap': {
        'linux_install': 'sudo apt install sqlmap'
    },
    'hydra': {
        'linux_install': 'sudo apt install hydra-gtk' # hydra-gtk includes the command-line tool
    },
    'john': {
        'linux_install': 'sudo apt install john'
    }
}

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """Imprime uma barra de progresso no terminal."""
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()

def download_file(url, filename):
    """Baixa um arquivo de uma URL com barra de progresso."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte

        print(f"Baixando: {filename} (Tamanho: {total_size / 1024 / 1024:.2f} MB)")
        with open(filename, 'wb') as f:
            downloaded_size = 0
            for data in response.iter_content(block_size):
                downloaded_size += len(data)
                f.write(data)
                print_progress_bar(downloaded_size, total_size, prefix='Progresso:', suffix='Completo', length=50)
        sys.stdout.write('\n')
        print(f"  [✓] Download de {filename} concluído com sucesso.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"\n  [✗] Erro ao baixar o arquivo: {e}")
        return False

def is_tool_installed(name):
    """Verifica se uma ferramenta está instalada e no PATH."""
    return which(name) is not None

def check_dependencies():
    """Verifica e oferece instalação de dependências."""
    print("Verificando dependências de ferramentas...")
    all_good = True
    system = platform.system()

    for tool, instructions in REQUIRED_TOOLS.items():
        if is_tool_installed(tool):
            print(f"  [✓] {tool} já está instalado.")
            continue

        all_good = False
        print(f"  [✗] {tool} não encontrado.")
        
        if system == "Windows" and 'windows_download_url' in instructions:
            print(f"      Deseja baixar e executar o instalador para '{tool}'?")
            choice = input("      (s/n): ").lower().strip()
            
            if choice == 's':
                installer_url = instructions['windows_download_url']
                installer_name = os.path.basename(installer_url)
                
                if download_file(installer_url, installer_name):
                    print(f"\n      Executando o instalador '{installer_name}'...")
                    print("      >>> Siga as instruções na tela. IMPORTANTE: Marque a opção para adicionar ao PATH do sistema, se houver. <<<")
                    try:
                        # Executa o instalador e espera ele terminar.
                        subprocess.run([installer_name], check=True)
                        print(f"      Instalador de '{tool}' finalizado. Por favor, reinicie o terminal e rode o setup novamente para verificar.")
                    except FileNotFoundError:
                        # Em alguns casos, pode ser necessário especificar o caminho
                        subprocess.run([os.path.join(os.getcwd(), installer_name)], check=True)
                    except Exception as e:
                        print(f"      [✗] Erro ao executar o instalador: {e}")
                    
                    # Sugere rodar de novo para verificar se a instalação (e o PATH) funcionou
                    print("\n      É recomendado reiniciar seu terminal e rodar este script de setup novamente para confirmar a instalação.")

            else:
                print(f"      Instalação pulada. Você pode instalar '{tool}' manualmente com:")
                print(f"      {instructions['windows_install']}")

        elif system == "Linux":
            print(f"      Para instalar, rode no seu terminal:")
            print(f"      {instructions['linux_install']}\n")
        else: # macOS ou outros
            print(f"      Por favor, instale '{tool}' manualmente para o seu sistema: {system}\n")
            
    if all_good:
        print("\nTodas as ferramentas necessárias foram encontradas!")
    else:
        print("\nAlgumas ferramentas não foram instaladas. Execute o setup novamente após a instalação manual se necessário.")
        
    return all_good

def setup_python_dependencies():
    """Instala dependências de Python de requirements.txt."""
    print("\nVerificando dependências de Python (requirements.txt)...")
    if os.path.exists('requirements.txt'):
        print("Arquivo requirements.txt encontrado. Instalando pacotes...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
            print("  [✓] Pacotes Python instalados com sucesso.")
        except subprocess.CalledProcessError as e:
            print(f"  [✗] Erro ao instalar pacotes Python: {e}")
            print("      Tente instalar manualmente com: pip install -r requirements.txt")
        except FileNotFoundError:
            print("  [✗] O comando 'pip' não foi encontrado.")
            print("      Verifique se o Python e o pip estão instalados e no PATH do sistema.")
    else:
        print("  (i) Nenhum arquivo requirements.txt encontrado. Pulando esta etapa.")

if __name__ == "__main__":
    setup_python_dependencies()
    check_dependencies()
    print("\nSetup finalizado.")
    input("Pressione Enter para sair.")