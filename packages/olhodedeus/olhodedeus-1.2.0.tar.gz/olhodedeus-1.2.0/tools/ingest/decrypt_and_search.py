#!/usr/bin/env python3
"""
decrypt_and_search.py

Decrypt a GPG-encrypted DB to a temporary file, run `search.py` against it,
then remove the temporary file. This avoids keeping plaintext DB on disk.

Também suporta busca direta em DB não criptografado.
"""
import argparse
import subprocess
import tempfile
import os
import sys
import platform


def get_python_cmd():
    """Retorna o comando Python correto para o sistema."""
    if platform.system() == 'Windows':
        # Tentar venv primeiro
        venv_python = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                    '.venv', 'Scripts', 'python.exe')
        if os.path.exists(venv_python):
            return venv_python
        return 'python'
    else:
        return 'python3'


def check_gpg_available():
    """Verifica se GPG está disponível."""
    try:
        subprocess.run(['gpg', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def decrypt_and_search(db_gpg: str, search_args: list):
    """Descriptografa DB e executa busca."""
    
    if not os.path.exists(db_gpg):
        print(f'❌ Arquivo não encontrado: {db_gpg}')
        return False
    
    if not check_gpg_available():
        print('❌ GPG não está instalado ou não está no PATH.')
        print('   Instale GPG: https://gnupg.org/download/')
        return False

    with tempfile.NamedTemporaryFile(prefix='leaks-', suffix='.db', delete=False) as tmp:
        tmpname = tmp.name
    
    try:
        print(f'🔓 Descriptografando {db_gpg}...')
        result = subprocess.run(
            ['gpg', '--batch', '--yes', '-o', tmpname, '-d', db_gpg], 
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f'❌ Erro ao descriptografar: {result.stderr}')
            return False
        
        print('✅ Descriptografado com sucesso!')
        
        # Executar busca
        python_cmd = get_python_cmd()
        search_script = os.path.join(os.path.dirname(__file__), 'search.py')
        
        cmd = [python_cmd, search_script, '--db', tmpname] + search_args
        subprocess.run(cmd)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f'❌ Erro: {e}')
        return False
    finally:
        # Limpar arquivo temporário
        try:
            if os.path.exists(tmpname):
                os.remove(tmpname)
                print('🧹 Arquivo temporário removido.')
        except Exception:
            pass


def search_direct(db_path: str, search_args: list):
    """Busca diretamente em DB não criptografado."""
    
    if not os.path.exists(db_path):
        print(f'❌ DB não encontrado: {db_path}')
        return False
    
    python_cmd = get_python_cmd()
    search_script = os.path.join(os.path.dirname(__file__), 'search.py')
    
    cmd = [python_cmd, search_script, '--db', db_path] + search_args
    subprocess.run(cmd)
    return True


def main():
    p = argparse.ArgumentParser(
        description='Decrypt DB.gpg and run search, or search directly',
        epilog='''
Exemplos:
  python decrypt_and_search.py --db-gpg data/leaks.db.gpg --email user@gmail.com
  python decrypt_and_search.py --db data/leaks.db --service netflix
  python decrypt_and_search.py --interactive
        '''
    )
    p.add_argument('--db-gpg', help='Caminho para DB criptografado (.gpg)')
    p.add_argument('--db', help='Caminho para DB não criptografado')
    p.add_argument('--interactive', '-i', action='store_true', help='Modo interativo')
    
    # Parse known args, remaining go to search.py
    args, remaining = p.parse_known_args()

    # Modo interativo
    if args.interactive or '--interactive' in remaining or '-i' in remaining:
        python_cmd = get_python_cmd()
        search_script = os.path.join(os.path.dirname(__file__), 'search.py')
        subprocess.run([python_cmd, search_script, '--interactive'])
        return

    # Prioridade: DB direto > DB criptografado > padrão
    if args.db:
        search_direct(args.db, remaining)
    elif args.db_gpg:
        decrypt_and_search(args.db_gpg, remaining)
    else:
        # Tentar encontrar automaticamente
        default_db = 'data/leaks.db'
        default_gpg = 'data/leaks.db.gpg'
        
        if os.path.exists(default_db):
            print(f'📁 Usando DB: {default_db}')
            search_direct(default_db, remaining)
        elif os.path.exists(default_gpg):
            print(f'🔐 Usando DB criptografado: {default_gpg}')
            decrypt_and_search(default_gpg, remaining)
        else:
            print('❌ Nenhum banco de dados encontrado.')
            print('   Use --db ou --db-gpg para especificar o caminho.')
            print('   Ou execute o ingest para criar o banco de dados.')


if __name__ == '__main__':
    main()
