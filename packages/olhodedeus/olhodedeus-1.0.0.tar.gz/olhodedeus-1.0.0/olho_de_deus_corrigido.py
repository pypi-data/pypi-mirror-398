"""
Backup wrapper: olho_de_deus_corrigido.py

Este arquivo é uma cópia de segurança da versão corrigida.
O ponto de entrada principal do projeto é `app/main.py`.

Uso recomendado a partir do diretório do projeto:
  - Executar a aplicação: python -m app.main
  - Ou executar este wrapper explicitamente: python olho_de_deus_corrigido.py --run

Se chamado com --run, este wrapper importa e executa app.main.main().
Caso contrário, apenas imprime esta mensagem e sai.
"""

import sys


def _print_info():
    print("olho_de_deus_corrigido.py is a backup wrapper for the project.")
    print("Recommended entrypoint: python -m app.main")
    print("To run the app using this file: python olho_de_deus_corrigido.py --run")


def _run_app():
    try:
        from importlib import import_module
        mod = import_module('app.main')
        if hasattr(mod, 'main'):
            mod.main()
        else:
            print('app.main does not expose main()')
    except Exception as e:
        print('Erro ao iniciar a aplicação via wrapper:', e)


if __name__ == '__main__':
    if '--run' in sys.argv:
        _run_app()
    else:
        _print_info()

⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⢶⠼⢻⣷⣦⡀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡈⢃⠐⣏⣟⣸⢣⡆⠀⠀⠀⠐⠳⠃⠉⣥⣆⣠⣠⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⡷⠤⣬⠍⠉⠁⠆⠀⠀⠀⠨⢼⡄⠜⢿⣭⡼⠋⡦⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠋⠲⠆⠘⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣼⣿⣼⣿⣿⣤⣤⣀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⠶⠖⠶⣶⣄⣄⡀⠀⠀⢺⡿⠟⠛⠋⠉⡻⣿⣿⣿⣿⡆
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢴⣿⡯⠿⠽⢆⠠⡀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡾⠃⢰⣿⣷⠌⡿⢻⡃⠀⠀⢋⠀⠀⠀⠀⢰⣼⣤⣽⣿⡯⡇
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣟⢠⢾⣶⡄⢹⠼⢦⠀⠀⠀⠀⠀⠀⠀⠿⠒⡓⠊⠉⠁⡀⣴⡛⠋⠀⢀⠆⠀⠀⠀⠀⢸⣿⣿⣿⣛⣡⣧
⠀⠀⠀⠀⢀⢠⣠⣠⠀⡀⠀⠀⠀⢻⣌⠋⠛⠚⢁⡡⠊⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠙⠓⠋⠁⠁⠀⠀⠀⠠⣞⠠⣀⠀⠀⠀⠙⢿⣿⣿⣿⡇
⠀⢠⡴⣿⣿⡿⡄⠹⡑⡕⠀⠀⠀⠀⠛⠛⠒⠋⢉⣦⣦⣞⡢⢄⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠙⡇⠂⠠⠀⡤⠒⠂⠒⠂⠘
⠈⢭⡣⠳⢯⡵⠃⢠⠱⠼⠀⠀⠀⠀⠀⠀⠀⢠⡿⢹⣝⣻⠇⢸⢱⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠀⠀⠀
⠀⠀⠉⠳⠜⠆⠁⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠚⠪⠅⠤⠘⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡠⠝⢉⣡⣬⡐⠺⡂
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣤⠀⠠⠄⠤⢦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠛⣕⣀⢺⣟⣛⣷⣴⠈
⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠛⠬⠀⢠⣾⡯⣷⠀⡳⡔⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠛⠛⠉⠈⠀⠀
⠀⠀⠀⠾⣷⣾⠿⣛⣶⣟⡷⠦⣄⣠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠺⣻⣛⠛⠍⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠰⠰⣅⠀⣼⣟⣿⣿⠿⡆⠈⡹⣷⡞⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣥⣈⠁⠙⢬⣌⣭⡾⠃⠀⢹⣦⠷⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣤⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠧⠉⠛⠢⣄⣤⣠⡀⣠⣤⠤⠒⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣬⠿⠛⢉⣉⣛⡻⢮⣄⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠘⠛⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠾⢷⡁⠀⢰⡿⢫⣿⣿⡆⠈⢻⣷⡄⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⣀⡀⠀⣄⢠⡀⡀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠑⠀⡉⠂⠘⢯⣼⣷⡿⠃⢀⠞⡙⠁⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣿⣦⣼⡖⠓⣼⣼⢠⣤⡄⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⣵⣤⢠⠀⠀⢠⣤⠚⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣬⣿⠅⠀⠀⢀⠔⠚⣶⣾⡽⣞⣤⠠⡀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠛⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠁⠀⠀⠀⣼⡿⣷⣾⣷⣆⠰⣿⡷⡀⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠄⠀⠀⢹⡥⣌⠟⠛⠁⡜⣿⠀⢰⢎⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠆⠀⠀⠀⠙⠾⣦⠶⣦⢞⡁⠀⠈⠸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                   
 ░██████        ░██████   ░██ ░██                             ░██               ░███████                                    
 ░██   ░██      ░██   ░██  ░██ ░██                             ░██               ░██   ░██                                   
░██     ░██    ░██     ░██ ░██ ░████████   ░███████      ░████████  ░███████     ░██    ░██  ░███████  ░██    ░██  ░███████  
░██     ░██    ░██     ░██ ░██ ░██    ░██ ░██    ░██    ░██    ░██ ░██    ░██    ░██    ░██ ░██    ░██ ░██    ░██ ░██        
░██     ░██    ░██     ░██ ░██ ░██    ░██ ░██    ░██    ░██    ░██ ░█████████    ░██    ░██ ░█████████ ░██    ░██  ░███████  
 ░██   ░██      ░██   ░██  ░██ ░██    ░██ ░██    ░██    ░██   ░███ ░██           ░██   ░██  ░██        ░██   ░███        ░██ 
  ░██████        ░██████   ░██ ░██    ░██  ░███████      ░█████░██  ░███████     ░███████    ░███████   ░█████░██  ░███████  
                                                                                                                             
                                                                              
                   ▄▄▄          ▄ 
                 ▄██▀▀▀       ▄██ 
                 ██ ▄▀█▄    ▄█▀██                        
          ▀█▄ ██▀██   ██    ▀  ██ 
           ██▄██ ██  ▄██       ██ 
            ▀█▀   ▀███▀   ██   ██ 
                        
                                                                                            
                                                                                                                             

                      
''')  # noqa: W605
    print("\n════════════════════════════════════════")
    print("    MENU PRINCIPAL")
    print("════════════════════════════════════════")
    print("  [1] Gestor de Senhas")
    print("  [2] Scraping de Dados (Auth Required)")
    print("  [3] Gerenciador de Programas")
    print("  [4] Bancos de Dados e Busca")
    print("  [5] Gen and Checkers")
    print("  [8] Sincronizar com Nuvem (Git)")
    print("  [9] Atualizar da Nuvem (Git)")
    print("  [0] Sair")
    print("════════════════════════════════════════")


def autenticar_usuario():
    """Autentica o usuário ou cria um novo."""
    from app.main import usuarios, config
    if not usuarios:
        print("Nenhum usuário cadastrado. Criar novo usuário?\n")
        print("[1] Criar novo usuário")
        print("[0] Sair")
        escolha = input("\nOpção: ")
        if escolha == '1':
            nome = input("Nome de usuário: ").strip()
            if nome in usuarios:
                print("Usuário já existe!")
                input("Pressione Enter para sair...")
                return None
            senha = input("Senha: ").strip()
            usuarios[nome] = hash_senha(senha)
            config["users"] = usuarios
            salvar_auth_config(config)
            print("Usuário criado com sucesso!")
            input("Pressione Enter para continuar...")
            return nome
        else:
            return None

    for tentativa in range(3):
        nome = input(f"Usuário ({3-tentativa} tentativas): ").strip()
        if nome not in usuarios:
            print("Usuário não encontrado!")
            continue

        senha = input("Senha: ").strip()
        if hash_senha(senha) == usuarios[nome]:
            print("Autenticado com sucesso!")
            input("Pressione Enter para continuar...")
            return nome
        else:
            print(f"Senha incorreta! ({3-tentativa-1} tentativas restantes)")

    print("Falha na autenticação. Encerrando...")
    input("Pressione Enter para sair...")
    return None


def limpar_tela():
    """Limpa o terminal para Windows ou Linux/Mac."""
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


def exibir_menu_principal():
    """Mostra o menu principal do programa."""
    limpar_tela()
    print(r''' 

⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⢶⠼⢻⣷⣦⡀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡈⢃⠐⣏⣟⣸⢣⡆⠀⠀⠀⠐⠳⠃⠉⣥⣆⣠⣠⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⡷⠤⣬⠍⠉⠁⠆⠀⠀⠀⠨⢼⡄⠜⢿⣭⡼⠋⡦⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠋⠲⠆⠘⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣼⣿⣼⣿⣿⣤⣤⣀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⠶⠖⠶⣶⣄⣄⡀⠀⠀⢺⡿⠟⠛⠋⠉⡻⣿⣿⣿⣿⡆
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢴⣿⡯⠿⠽⢆⠠⡀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡾⠃⢰⣿⣷⠌⡿⢻⡃⠀⠀⢋⠀⠀⠀⠀⢰⣼⣤⣽⣿⡯⡇
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣟⢠⢾⣶⡄⢹⠼⢦⠀⠀⠀⠀⠀⠀⠀⠿⠒⡓⠊⠉⠁⡀⣴⡛⠋⠀⢀⠆⠀⠀⠀⠀⢸⣿⣿⣿⣛⣡⣧
⠀⠀⠀⠀⢀⢠⣠⣠⠀⡀⠀⠀⠀⢻⣌⠋⠛⠚⢁⡡⠊⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠙⠓⠋⠁⠁⠀⠀⠀⠠⣞⠠⣀⠀⠀⠀⠙⢿⣿⣿⣿⡇
⠀⢠⡴⣿⣿⡿⡄⠹⡑⡕⠀⠀⠀⠀⠛⠛⠒⠋⢉⣦⣦⣞⡢⢄⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠙⡇⠂⠠⠀⡤⠒⠂⠒⠂⠘
⠈⢭⡣⠳⢯⡵⠃⢠⠱⠼⠀⠀⠀⠀⠀⠀⠀⢠⡿⢹⣝⣻⠇⢸⢱⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠀⠀⠀
⠀⠀⠉⠳⠜⠆⠁⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠚⠪⠅⠤⠘⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡠⠝⢉⣡⣬⡐⠺⡂
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣤⠀⠠⠄⠤⢦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠛⣕⣀⢺⣟⣛⣷⣴⠈
⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠛⠬⠀⢠⣾⡯⣷⠀⡳⡔⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠛⠛⠉⠈⠀⠀
⠀⠀⠀⠾⣷⣾⠿⣛⣶⣟⡷⠦⣄⣠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠺⣻⣛⠛⠍⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠰⠰⣅⠀⣼⣟⣿⣿⠿⡆⠈⡹⣷⡞⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣥⣈⠁⠙⢬⣌⣭⡾⠃⠀⢹⣦⠷⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣤⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠧⠉⠛⠢⣄⣤⣠⡀⣠⣤⠤⠒⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣬⠿⠛⢉⣉⣛⡻⢮⣄⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠘⠛⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠾⢷⡁⠀⢰⡿⢫⣿⣿⡆⠈⢻⣷⡄⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⣀⡀⠀⣄⢠⡀⡀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠑⠀⡉⠂⠘⢯⣼⣷⡿⠃⢀⠞⡙⠁⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣿⣦⣼⡖⠓⣼⣼⢠⣤⡄⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⣵⣤⢠⠀⠀⢠⣤⠚⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣬⣿⠅⠀⠀⢀⠔⠚⣶⣾⡽⣞⣤⠠⡀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠛⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠁⠀⠀⠀⣼⡿⣷⣾⣷⣆⠰⣿⡷⡀⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠄⠀⠀⢹⡥⣌⠟⠛⠁⡜⣿⠀⢰⢎⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠆⠀⠀⠀⠙⠾⣦⠶⣦⢞⡁⠀⠈⠸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                   
 ░██████        ░██████   ░██ ░██                             ░██               ░███████                                    
 ░██   ░██      ░██   ░██  ░██ ░██                             ░██               ░██   ░██                                   
░██     ░██    ░██     ░██ ░██ ░████████   ░███████      ░████████  ░███████     ░██    ░██  ░███████  ░██    ░██  ░███████  
░██     ░██    ░██     ░██ ░██ ░██    ░██ ░██    ░██    ░██    ░██ ░██    ░██    ░██    ░██ ░██    ░██ ░██    ░██ ░██        
░██     ░██    ░██     ░██ ░██ ░██    ░██ ░██    ░██    ░██    ░██ ░█████████    ░██    ░██ ░█████████ ░██    ░██  ░███████  
 ░██   ░██      ░██   ░██  ░██ ░██    ░██ ░██    ░██    ░██   ░███ ░██           ░██   ░██  ░██        ░██   ░███        ░██ 
  ░██████        ░██████   ░██ ░██    ░██  ░███████      ░█████░██  ░███████     ░███████    ░███████   ░█████░██  ░███████  
                                                                                                                             
                                                                              
                   ▄▄▄          ▄ 
                 ▄██▀▀▀       ▄██ 
                 ██ ▄▀█▄    ▄█▀██                        
          ▀█▄ ██▀██   ██    ▀  ██ 
           ██▄██ ██  ▄██       ██ 
            ▀█▀   ▀███▀   ██   ██ 
                        
                                                                                            
                                                                                                                             

                      
''')  # noqa: W605
    print("\n════════════════════════════════════════")
    print("    MENU PRINCIPAL")
    print("════════════════════════════════════════")
    print("  [1] Gestor de Senhas")
    print("  [2] Scraping de Dados (Auth Required)")
    print("  [3] Gerenciador de Programas")
    print("  [4] Bancos de Dados e Busca")
    print("  [5] Gen and Checkers")
    print("  [8] Sincronizar com Nuvem (Git)")
    print("  [9] Atualizar da Nuvem (Git)")
    print("  [0] Sair")
    print("════════════════════════════════════════")


def menu_senhas():
    """Gerencia a seção de senhas."""
    while True:
        limpar_tela()
        print("--- Gestor de Senhas ---")
        print("  [1] Acessar Cofre de Senhas (KeePass)")
        print("  [0] Voltar ao Menu Principal")
        print("--------------------------")
        escolha = input("Selecione a Opção necessária: ")
        if escolha == '1':
            acessar_cofre_senhas()
        elif escolha == '0':
            break
        else:
            input("Opção inválida. Pressione Enter para tentar novamente...")


def menu_hacking():
    """Gerencia a seção de ferramentas de hacking."""
    while True:
        limpar_tela()
        print("--- Ferramentas de Hacking (Private by Nin, Auth Necessária ou token de visitante único) ---")
        print("  [1] Bypass Tools (Não implementado)")
        print("  [2] Spoofer Tools (Não implementado)")
        print("  [3] Gerenciador de VPN (Não implementado)")
        print("  [0] Voltar ao Menu Principal")
        print("--------------------------------")
        escolha = input("Opção: ")
        if escolha == '0':
            break
        else:
            input("Função não implementada. Pressione Enter para voltar...")


def menu_programas():
    """Gerencia a seção de programas."""
    while True:
        limpar_tela()
        print("--- Gerenciador de Programas ---")
        print("  [1] Baixar e Instalar Programa (Não implementado)")
        print("  [2] Listar Programas Instalados (Não implementado)")
        print("  [0] Voltar ao Menu Principal")
        print("----------------------------------")
        escolha = input("Opção: ")
        if escolha == '0':
            break
        else:
            input("Função não implementada. Pressione Enter para voltar...")


def menu_bancos_de_dados():
    """Gerencia a seção de bancos de dados e arquivos."""
    while True:
        limpar_tela()
        print("--- Bancos de Dados e Arquivos ---")
        print("  [1] Pesquisar em Bancos de Dados Vazados")
        print("  [2] Gerenciar Arquivos Locais (Não implementado)")
        print("  [0] Voltar ao Menu Principal")
        print("--------------------------------------")
        escolha = input("Opção: ")
        if escolha == '1':
            menu_search_db()
        elif escolha == '0':
            break
        else:
            input("Função não implementada. Pressione Enter para voltar...")

def menu_gen_and_checkers():
    """Executa o script de Gen and Checkers."""
    limpar_tela()
    print("--- Gen and Checkers ---")
    try:
        cmd = ['python3', 'tools/Gen_And_Checkers.py']
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Erro ao executar o script: {e}")
    input("Pressione Enter para voltar ao menu principal...")

def menu_gen_and_checkers():
    """Executa o script de Gen and Checkers."""
    limpar_tela()
    print("--- Gen and Checkers ---")
    try:
        cmd = ['python3', 'tools/Gen_And_Checkers.py']
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Erro ao executar o script: {e}")
    input("Pressione Enter para voltar ao menu principal...")

def menu_search_db():
    """Menu para buscar no DB de vazamentos."""
    while True:
        limpar_tela()
        print("--- Buscar em Bancos de Dados ---")
        print("  [1] Buscar por Categoria (Netflix, Gmail, etc)")
        print("  [2] Buscar por Serviço/Domínio")
        print("  [3] Ver Estatísticas do DB")
        print("  [0] Voltar")
        print("---------------------------------")
        escolha = input("Opção: ")

        if escolha == '1':
            categoria = input("Digite a categoria para buscar (ex: netflix): ").strip()
            limite = input("Limite de resultados (padrão 20): ").strip() or "20"
            cmd = ['python3', 'tools/ingest/decrypt_and_search.py', '--db-gpg', DB_PATH + '.gpg', '--category',
                   categoria, '--limit', limite]
            try:
                subprocess.run(cmd, check=True)
            except Exception as e:
                print(f"Erro na busca: {e}")
            input("Pressione Enter para continuar...")

        elif escolha == '2':
            servico = input("Digite o serviço/domínio (ex: gmail.com): ").strip()
            limite = input("Limite de resultados (padrão 20): ").strip() or "20"
            cmd = ['python3', 'tools/ingest/decrypt_and_search.py', '--db-gpg', DB_PATH + '.gpg', '--service',
                   servico, '--limit', limite]
            try:
                subprocess.run(cmd, check=True)
            except Exception as e:
                print(f"Erro na busca: {e}")
            input("Pressione Enter para continuar...")

        elif escolha == '3':
            cmd = ['python3', 'tools/ingest/decrypt_and_search.py', '--db-gpg', DB_PATH + '.gpg', '--limit', '1']
            try:
                subprocess.run(cmd, check=True)
            except Exception as e:
                print(f"Erro ao exibir estatísticas: {e}")
            input("Pressione Enter para continuar...")

        elif escolha == '0':
            break
        else:
            input("Opção inválida. Pressione Enter para tentar novamente...")


def menu_scraping():
    """Gerencia a seção de scraping de dados."""
    while True:
        limpar_tela()
        print("--- Scraping de Bancos de Dados (Auth Required) ---")
        print("  [1] Scraping Automático (URLs Permitidas)")
        print("  [2] Scraping Manual (Adicionar URL)")
        print("  [3] Ingerir Arquivo Local")
        print("  [4] Ver Arquivos Processados")
        print("  [0] Voltar ao Menu Principal")
        print("--------------------------------------------------")
        escolha = input("Opção: ")

        if escolha == '1':
            scraping_automatico()
        elif escolha == '2':
            scraping_manual()
        elif escolha == '3':
            ingestao_local()
        elif escolha == '4':
            listar_processados()
        elif escolha == '0':
            break
        else:
            input("Opção inválida. Pressione Enter para tentar novamente...")

def scraping_automatico():
    """Executa scraping automático de URLs permitidas."""
    limpar_tela()
    print("--- Scraping Automático ---\n")

    if not os.path.exists(ALLOWED_SOURCES_CONFIG):
        print(f"Config não encontrada: {ALLOWED_SOURCES_CONFIG}")
        print("Execute este comando para criar:")
        print(f"  echo '{{\"urls\": []}}' > {ALLOWED_SOURCES_CONFIG}")
        input("Pressione Enter para voltar...")
        return

    with open(ALLOWED_SOURCES_CONFIG, 'r') as f:
        config = json.load(f)

    urls = config.get('urls', [])
    if not urls:
        print("Nenhuma URL configurada em allowed_sources.json")
        print("\nAdicione URLs ao arquivo da seguinte forma:")
        print('{')
        print('  "urls": [')
        print('    "https://exemplo.com/leak.csv",')
        print('    "file:///caminho/local/arquivo.csv"')
        print('  ]')
        print('}')
        input("Pressione Enter para voltar...")
        return

    print(f"URLs configuradas: {len(urls)}")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}")

    confirma = input("\nIniciar download? (s/n): ").lower()
    if confirma != 's':
        return

    try:
        cmd = ['python3', 'tools/ingest/scraper.py', '--config', ALLOWED_SOURCES_CONFIG]
        subprocess.run(cmd, check=True)
        print("\nScraping concluído! Arquivos salvos em raw_data/")
    except Exception as e:
        print(f"Erro durante scraping: {e}")

    input("Pressione Enter para voltar...")


def scraping_manual():
    """Permite adicionar URLs manualmente para scraping."""
    limpar_tela()
    print("--- Scraping Manual ---\n")

    url = input("Digite a URL para download (ex: https://exemplo.com/leak.csv): ").strip()
    if not url:
        print("URL vazia!")
        input("Pressione Enter para voltar...")
        return

    # Valida URL mínima
    if not url.startswith('http://') and not url.startswith('https://') and not url.startswith('file://'):
        print("URL deve começar com http://, https:// ou file://")
        input("Pressione Enter para voltar...")
        return

    max_bytes = input("Tamanho máximo em MB (padrão 50): ").strip() or "50"
    try:
        max_bytes = int(max_bytes) * 1_000_000
    except ValueError:
        max_bytes = 50_000_000

    print(f"\nTamanho máximo: {max_bytes / 1_000_000:.1f} MB")

    os.makedirs('raw_data', exist_ok=True)

    # Nome de arquivo baseado na URL
    import hashlib
    fname = hashlib.sha1(url.encode()).hexdigest()[:16]
    dest = f'raw_data/manual_{fname}.csv'

    try:
        if url.startswith('file://'):
            # Arquivo local
            local_path = url[7:]  # remove file://
            import shutil
            shutil.copy(local_path, dest)
            print(f"Arquivo copiado: {dest}")
        else:
            # Download remoto
            from tools.ingest.utils import safe_download
            safe_download(url, dest, max_bytes=max_bytes)
            print(f"Arquivo baixado: {dest}")

        # Extrair dados
        print("\nExtraindo dados...")
        from tools.ingest.extractors import extract_from_text
        with open(dest, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        items = extract_from_text(text)
        print(f"Extraídos {len(items)} itens")

        # Salvar CSV
        import csv
        csv_path = dest.replace('.csv', '_extracted.csv')
        with open(csv_path, 'w', encoding='utf-8', newline='') as csvf:
            writer = csv.DictWriter(csvf, fieldnames=['email', 'password', 'cpf', 'name', 'raw'])
            writer.writeheader()
            for it in items:
                writer.writerow({k: it.get(k, '') for k in ['email', 'password', 'cpf', 'name', 'raw']})
        print(f"CSV salvo: {csv_path}")

        # Perguntar se quer ingerir agora
        ingerir = input("\nIngerir dados agora? (s/n): ").lower()
        if ingerir == 's':
            ingestao_arquivo(csv_path)

    except Exception as e:
        print(f"Erro: {e}")

    input("Pressione Enter para voltar...")


def ingestao_local():
    """Ingesta de arquivo local."""
    limpar_tela()
    print("--- Ingestão de Arquivo Local ---\n")

    arquivo = input("Caminho para o arquivo CSV (ex: raw_data/leak.csv): ").strip()
    if not os.path.exists(arquivo):
        print(f"Arquivo não encontrado: {arquivo}")
        input("Pressione Enter para voltar...")
        return

    ingestao_arquivo(arquivo)

def ingestao_arquivo(arquivo):
    """Realiza ingestão de um arquivo específico."""
    print(f"\nIngerindo {arquivo}...")

    categoria = input("Categoria (deixe em branco para auto-detectar): ").strip() or None
    salt = HASH_SALT

    encrypt = input("Encriptar DB após ingestão? (s/n): ").lower() == 's'

    cmd = ['python3', 'tools/ingest/pipeline.py', '--source', arquivo, '--db', DB_PATH, '--hash-salt', salt]
    if encrypt:
        cmd.append('--encrypt')
    if categoria:
        cmd.extend(['--category', categoria])

    try:
        subprocess.run(cmd, check=True)
        print("\nIngestão concluída com sucesso!")
    except Exception as e:
        print(f"Erro durante ingestão: {e}")

    input("Pressione Enter para voltar...")

def listar_processados():
    """Lista arquivos já processados."""
    limpar_tela()
    print("--- Arquivos Processados ---\n")

    processed_dir = 'raw_data/processed'
    if not os.path.exists(processed_dir):
        print("Nenhum arquivo processado ainda")
        input("Pressione Enter para voltar...")
        return

    arquivos = os.listdir(processed_dir)
    if not arquivos:
        print("Pasta vazia")
        input("Pressione Enter para voltar...")
        return

    for i, arquivo in enumerate(arquivos, 1):
        path = os.path.join(processed_dir, arquivo)
        size = os.path.getsize(path) / 1024
        print(f"{i}. {arquivo} ({size:.1f} KB)")

    input("\nPressione Enter para voltar...")

def acessar_cofre_senhas():
    """Descriptografa e abre o banco de dados do KeePass."""
    print("Acessando o cofre de senhas...")

    # Comando para descriptografar o arquivo GPG
    # Ele vai pedir sua senha mestra no próprio terminal
    comando_gpg = f"gpg --output {KEEPASS_DB_PATH_DECRYPTED} --decrypt {KEEPASS_DB_PATH_ENCRYPTED}"

    try:
        # Executa o comando GPG. `subprocess.run` é mais moderno e seguro.
        resultado = subprocess.run(comando_gpg, shell=True, check=True)

        print(f"Cofre '{KEEPASS_DB_PATH_DECRYPTED}' descriptografado com sucesso.")
        print("Abrindo o KeePass... Feche o KeePass para continuar.")

        # Tenta abrir o KeePass com o banco de dados.
        # Você precisa ter o KeePass.exe no seu PATH ou especificar o caminho completo.
        # Exemplo de caminho: "C:/Program Files/KeePassXC/KeePassXC.exe"
        comando_keepass = f"KeePassXC.exe {KEEPASS_DB_PATH_DECRYPTED}"
        subprocess.run(comando_keepass, shell=True)

    except subprocess.CalledProcessError:
        print("\nERRO: Falha ao descriptografar. A senha mestra estava correta?")
        print("O arquivo de senhas de origem existe?")

    finally:
        # APAGA o arquivo descriptografado por segurança após o uso.
        if os.path.exists(KEEPASS_DB_PATH_DECRYPTED):
            print(f"Removendo arquivo descriptografado '{KEEPASS_DB_PATH_DECRYPTED}' por segurança.")
            os.remove(KEEPASS_DB_PATH_DECRYPTED)

    input("\nPressione Enter para voltar ao menu...")

def sincronizar_nuvem():
    """Envia as alterações locais para o repositório Git remoto."""
    print("Sincronizando com a nuvem...")
    try:
        # Adiciona todos os arquivos modificados (incluindo novos arquivos .gpg)
        subprocess.run("git add .", shell=True, check=True)

        # Faz o commit com uma mensagem padrão
        mensagem_commit = "sincronizacao automatica via OlhoDeDeus"
        subprocess.run(f'git commit -m "{mensagem_commit}"', shell=True)  # O commit pode falhar se não houver nada para comitar

        # Envia para o repositório remoto
        print("Enviando para a nuvem...")
        subprocess.run("git push", shell=True, check=True)
        print("\nArquivos enviados com sucesso!")

    except subprocess.CalledProcessError as e:
        print(f"\nERRO durante a sincronização: {e}")
        print("Pode ser que não havia nada para salvar ou ocorreu um erro de conexão.")

    input("Pressione Enter para voltar ao menu...")

def puxar_da_nuvem():
    """Baixa as alterações do repositório Git remoto."""
    print("Atualizando a partir da nuvem...")
    try:
        subprocess.run("git pull", shell=True, check=True)
        print("\nArquivos atualizados com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"\nERRO ao atualizar: {e}")

    input("Pressione Enter para voltar ao menu...")

def main():
    """Função principal que gerencia o loop do menu."""
    # Autentica usuário primeiro
    usuario = autenticar_usuario()
    if not usuario:
        return

    while True:
        exibir_menu_principal()
        print(f"\nAutenticado como: {usuario}\n")
        escolha = input("Opção: ")

        if escolha == '1':
            menu_senhas()
        elif escolha == '2':
            menu_scraping()  # Novo menu de scraping
        elif escolha == '3':
            menu_programas()
        elif escolha == '4':
            menu_bancos_de_dados()
        elif escolha == '5':
            menu_gen_and_checkers()
        elif escolha == '8':
            sincronizar_nuvem()
        elif escolha == '9':
            puxar_da_nuvem()
        elif escolha == '0':
            print("Saindo. Até a próxima.")
            break
        else:
            input("Opção inválida. Pressione Enter para tentar novamente...")


if __name__ == "__main__":
    main()
