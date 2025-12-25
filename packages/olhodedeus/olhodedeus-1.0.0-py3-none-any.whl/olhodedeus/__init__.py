"""
Olho de Deus - Ferramenta OSINT e Análise de Segurança
======================================================

Instalação:
    pip install olhodedeus

Uso via terminal:
    olhodedeus          # Menu interativo
    olhodedeus --help   # Ver comandos
    odd                 # Atalho rápido
    olho                # Outro atalho

Uso como biblioteca:
    from olhodedeus import OlhoDeDeus
    
    odd = OlhoDeDeus()
    odd.check_leak("email@example.com")
"""

import sys
import os

# Adiciona path do projeto para imports
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_PATH not in sys.path:
    sys.path.insert(0, BASE_PATH)

__version__ = "1.0.0"
__author__ = "Olho de Deus Team"
__license__ = "MIT"

from olhodedeus.core import OlhoDeDeus

__all__ = ["OlhoDeDeus", "__version__"]
