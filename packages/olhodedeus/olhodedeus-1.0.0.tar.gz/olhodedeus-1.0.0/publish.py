#!/usr/bin/env python3
"""
Script para publicar o Olho de Deus no PyPI.

Uso:
    python publish.py          # Publica no PyPI (produção)
    python publish.py --test   # Publica no TestPyPI primeiro
"""

import subprocess
import sys
import os

def run(cmd: str, check: bool = True):
    """Executa comando e imprime output."""
    print(f"\n🔧 Executando: {cmd}")
    result = subprocess.run(cmd, shell=True, check=check)
    return result.returncode == 0

def main():
    test_mode = '--test' in sys.argv
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║           👁️  OLHO DE DEUS - Publicação PyPI                 ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 1. Limpar builds anteriores
    print("\n📦 Limpando builds anteriores...")
    run("rmdir /s /q dist 2>nul", check=False) if os.name == 'nt' else run("rm -rf dist", check=False)
    run("rmdir /s /q build 2>nul", check=False) if os.name == 'nt' else run("rm -rf build", check=False)
    run("rmdir /s /q *.egg-info 2>nul", check=False) if os.name == 'nt' else run("rm -rf *.egg-info", check=False)
    
    # 2. Instalar/atualizar ferramentas de build
    print("\n🔧 Atualizando ferramentas de build...")
    run(f"{sys.executable} -m pip install --upgrade pip build twine")
    
    # 3. Construir pacote
    print("\n🏗️  Construindo pacote...")
    if not run(f"{sys.executable} -m build"):
        print("❌ Erro ao construir pacote!")
        return 1
    
    # 4. Verificar pacote
    print("\n🔍 Verificando pacote...")
    run(f"{sys.executable} -m twine check dist/*")
    
    # 5. Upload
    if test_mode:
        print("\n🧪 Publicando no TestPyPI...")
        run(f"{sys.executable} -m twine upload --repository testpypi dist/*")
        print("\n✅ Publicado no TestPyPI!")
        print("   Teste com: pip install -i https://test.pypi.org/simple/ olhodedeus")
    else:
        confirm = input("\n⚠️  Publicar no PyPI de PRODUÇÃO? (s/N): ").strip().lower()
        if confirm == 's':
            print("\n🚀 Publicando no PyPI...")
            run(f"{sys.executable} -m twine upload dist/*")
            print("\n✅ Publicado no PyPI!")
            print("   Instale com: pip install olhodedeus")
        else:
            print("\n❌ Publicação cancelada.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
