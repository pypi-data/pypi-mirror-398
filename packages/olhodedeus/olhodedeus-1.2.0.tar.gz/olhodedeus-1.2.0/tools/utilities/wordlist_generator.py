#!/usr/bin/env python3
"""
Wordlist Generator - Gerador de wordlists personalizadas
Parte do toolkit Olho de Deus
"""

import os
import sys
import itertools
import random
import string
from typing import List, Dict, Set, Optional, Generator
from dataclasses import dataclass


@dataclass
class WordlistConfig:
    """Configuração para geração de wordlist."""
    min_length: int = 4
    max_length: int = 12
    include_lowercase: bool = True
    include_uppercase: bool = False
    include_numbers: bool = True
    include_special: bool = False
    custom_chars: str = ""
    
    def get_charset(self) -> str:
        charset = ""
        if self.include_lowercase:
            charset += string.ascii_lowercase
        if self.include_uppercase:
            charset += string.ascii_uppercase
        if self.include_numbers:
            charset += string.digits
        if self.include_special:
            charset += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if self.custom_chars:
            charset += self.custom_chars
        return charset


class LeetSpeakConverter:
    """Conversor para Leet Speak."""
    
    LEET_MAP = {
        'a': ['4', '@', 'A', 'a'],
        'b': ['8', 'B', 'b'],
        'c': ['(', 'C', 'c'],
        'd': ['D', 'd'],
        'e': ['3', 'E', 'e'],
        'f': ['F', 'f'],
        'g': ['9', '6', 'G', 'g'],
        'h': ['#', 'H', 'h'],
        'i': ['1', '!', 'I', 'i'],
        'j': ['J', 'j'],
        'k': ['K', 'k'],
        'l': ['1', 'L', 'l'],
        'm': ['M', 'm'],
        'n': ['N', 'n'],
        'o': ['0', 'O', 'o'],
        'p': ['P', 'p'],
        'q': ['Q', 'q'],
        'r': ['R', 'r'],
        's': ['5', '$', 'S', 's'],
        't': ['7', '+', 'T', 't'],
        'u': ['U', 'u'],
        'v': ['V', 'v'],
        'w': ['W', 'w'],
        'x': ['X', 'x'],
        'y': ['Y', 'y'],
        'z': ['2', 'Z', 'z'],
    }
    
    SIMPLE_LEET = {
        'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7',
        'A': '4', 'E': '3', 'I': '1', 'O': '0', 'S': '5', 'T': '7'
    }
    
    @classmethod
    def simple_leet(cls, text: str) -> str:
        """Converte para leet speak simples."""
        return ''.join(cls.SIMPLE_LEET.get(c, c) for c in text)
    
    @classmethod
    def generate_variations(cls, word: str, max_variations: int = 100) -> List[str]:
        """Gera variações leet de uma palavra."""
        word = word.lower()
        
        # Gera todas as combinações possíveis (limitado)
        positions = []
        for i, char in enumerate(word):
            if char in cls.LEET_MAP:
                positions.append((i, cls.LEET_MAP[char]))
            else:
                positions.append((i, [char]))
        
        # Limita combinações
        total = 1
        for _, options in positions:
            total *= len(options)
            if total > max_variations * 10:
                break
        
        variations = set()
        
        if total <= max_variations:
            # Gera todas as combinações
            for combo in itertools.product(*[options for _, options in positions]):
                variations.add(''.join(combo))
        else:
            # Gera aleatoriamente
            for _ in range(max_variations):
                result = ''.join(random.choice(options) for _, options in positions)
                variations.add(result)
        
        return list(variations)[:max_variations]


class CasePermutator:
    """Gerador de permutações de case."""
    
    @staticmethod
    def all_cases(word: str, max_results: int = 1000) -> List[str]:
        """Gera todas as combinações de case."""
        if len(word) > 10:  # Limita para evitar explosão combinatória
            return CasePermutator.common_cases(word)
        
        results = []
        for combo in itertools.product(*[(c.lower(), c.upper()) for c in word]):
            results.append(''.join(combo))
            if len(results) >= max_results:
                break
        
        return results
    
    @staticmethod
    def common_cases(word: str) -> List[str]:
        """Gera casos comuns apenas."""
        cases = set()
        cases.add(word.lower())
        cases.add(word.upper())
        cases.add(word.capitalize())
        cases.add(word.title())
        cases.add(word.lower().capitalize())
        
        # Alternar
        cases.add(''.join(c.upper() if i % 2 == 0 else c.lower() 
                         for i, c in enumerate(word)))
        cases.add(''.join(c.lower() if i % 2 == 0 else c.upper() 
                         for i, c in enumerate(word)))
        
        return list(cases)


class SuffixAppender:
    """Gerador de sufixos comuns."""
    
    COMMON_SUFFIXES = [
        # Anos
        *[str(y) for y in range(1990, 2026)],
        *[str(y)[2:] for y in range(1990, 2026)],
        
        # Números simples
        '1', '12', '123', '1234', '12345', '123456',
        '0', '00', '000', '01', '02', '03', '04', '05',
        '69', '666', '007', '13', '7', '77', '777',
        
        # Símbolos
        '!', '!!', '@', '#', '$', '*',
        '!@#', '!1', '@1', '#1', '!@#$',
        
        # Padrões
        '!', '!!', '!!!', '@!', '!@', '1!', '!1',
        '123!', '!123', 'abc', 'xyz',
        
        # Combinações teclado
        'qwerty', 'asdf', 'zxcv', '1qaz', '2wsx',
    ]
    
    @classmethod
    def append_suffixes(cls, word: str, suffixes: List[str] = None) -> List[str]:
        """Adiciona sufixos a uma palavra."""
        if suffixes is None:
            suffixes = cls.COMMON_SUFFIXES
        
        results = [word]
        for suffix in suffixes:
            results.append(word + suffix)
        
        return results
    
    @classmethod
    def prepend_prefixes(cls, word: str, prefixes: List[str] = None) -> List[str]:
        """Adiciona prefixos a uma palavra."""
        if prefixes is None:
            prefixes = ['the', 'my', 'i', 'a', '123', '1', '@']
        
        results = [word]
        for prefix in prefixes:
            results.append(prefix + word)
        
        return results


class PatternGenerator:
    """Gerador baseado em padrões."""
    
    PATTERNS = {
        "?l": string.ascii_lowercase,
        "?u": string.ascii_uppercase,
        "?d": string.digits,
        "?s": "!@#$%^&*()_+-=",
        "?a": string.ascii_letters + string.digits + "!@#$%^&*()_+-=",
    }
    
    @classmethod
    def generate_from_pattern(cls, pattern: str, max_results: int = 10000) -> Generator[str, None, None]:
        """Gera palavras baseadas em um padrão."""
        # Analisa o padrão
        parts = []
        i = 0
        while i < len(pattern):
            if i < len(pattern) - 1 and pattern[i] == '?':
                code = pattern[i:i+2]
                if code in cls.PATTERNS:
                    parts.append(cls.PATTERNS[code])
                    i += 2
                    continue
            parts.append(pattern[i])
            i += 1
        
        # Gera combinações
        count = 0
        for combo in itertools.product(*parts):
            yield ''.join(combo)
            count += 1
            if count >= max_results:
                return
    
    @classmethod
    def estimate_combinations(cls, pattern: str) -> int:
        """Estima o número de combinações possíveis."""
        total = 1
        i = 0
        while i < len(pattern):
            if i < len(pattern) - 1 and pattern[i] == '?':
                code = pattern[i:i+2]
                if code in cls.PATTERNS:
                    total *= len(cls.PATTERNS[code])
                    i += 2
                    continue
            i += 1
        return total


class CombinationGenerator:
    """Gerador de combinações de palavras."""
    
    @staticmethod
    def combine_words(words: List[str], separators: List[str] = None) -> List[str]:
        """Combina palavras com separadores."""
        if separators is None:
            separators = ['', '_', '-', '.', '@', '!']
        
        results = []
        
        # Todas as permutações de pares
        for i, w1 in enumerate(words):
            for j, w2 in enumerate(words):
                if i != j:
                    for sep in separators:
                        results.append(w1 + sep + w2)
        
        return results
    
    @staticmethod
    def combine_with_numbers(words: List[str], numbers: List[str] = None) -> List[str]:
        """Combina palavras com números."""
        if numbers is None:
            numbers = ['1', '12', '123', '1234', '2020', '2021', '2022', '2023', '2024', '2025']
        
        results = []
        for word in words:
            for num in numbers:
                results.append(word + num)
                results.append(num + word)
        
        return results


class WordlistGenerator:
    """Gerador principal de wordlists."""
    
    def __init__(self):
        self.leet = LeetSpeakConverter()
        self.case = CasePermutator()
        self.suffix = SuffixAppender()
        self.pattern = PatternGenerator()
        self.combiner = CombinationGenerator()
    
    def from_base_words(self, words: List[str], 
                        use_leet: bool = True,
                        use_case: bool = True,
                        use_suffix: bool = True) -> Set[str]:
        """Gera wordlist a partir de palavras base."""
        results = set()
        
        for word in words:
            # Palavra original
            results.add(word)
            
            # Variações de case
            if use_case:
                for case_var in self.case.common_cases(word):
                    results.add(case_var)
            
            # Variações leet
            if use_leet:
                for leet_var in self.leet.generate_variations(word, 20):
                    results.add(leet_var)
            
            # Sufixos
            if use_suffix:
                for suffix_var in self.suffix.append_suffixes(word):
                    results.add(suffix_var)
                
                # Leet + sufixos
                if use_leet:
                    leet_word = self.leet.simple_leet(word)
                    for suffix_var in self.suffix.append_suffixes(leet_word):
                        results.add(suffix_var)
        
        return results
    
    def from_pattern(self, pattern: str, max_results: int = 10000) -> List[str]:
        """Gera wordlist a partir de um padrão."""
        return list(self.pattern.generate_from_pattern(pattern, max_results))
    
    def from_profile(self, profile: Dict) -> Set[str]:
        """Gera wordlist a partir de um perfil de usuário."""
        words = set()
        
        # Nome
        if profile.get("first_name"):
            words.add(profile["first_name"])
        if profile.get("last_name"):
            words.add(profile["last_name"])
        if profile.get("nickname"):
            words.add(profile["nickname"])
        
        # Datas
        if profile.get("birthdate"):
            bd = profile["birthdate"]
            words.add(bd.replace("-", "").replace("/", ""))
            parts = bd.replace("/", "-").split("-")
            if len(parts) >= 3:
                words.add(parts[2])  # Ano
                words.add(parts[1] + parts[2])  # MMYYYY
                words.add(parts[0] + parts[1])  # DDMM
        
        # Outros
        if profile.get("pet_name"):
            words.add(profile["pet_name"])
        if profile.get("company"):
            words.add(profile["company"])
        if profile.get("keywords"):
            words.update(profile["keywords"])
        
        return self.from_base_words(list(words))
    
    def save_wordlist(self, words: Set[str], filepath: str):
        """Salva wordlist em arquivo."""
        with open(filepath, 'w', encoding='utf-8') as f:
            for word in sorted(words):
                f.write(word + '\n')
    
    def load_wordlist(self, filepath: str) -> Set[str]:
        """Carrega wordlist de arquivo."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    
    def merge_wordlists(self, *filepaths: str) -> Set[str]:
        """Mescla múltiplas wordlists."""
        result = set()
        for filepath in filepaths:
            if os.path.isfile(filepath):
                result.update(self.load_wordlist(filepath))
        return result


def interactive_menu():
    """Menu interativo do Wordlist Generator."""
    generator = WordlistGenerator()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║        📝 WORDLIST GENERATOR - Olho de Deus                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 📋 Gerar de Palavras Base                               ║
║  [2] 🔣 Gerar de Padrão                                      ║
║  [3] 👤 Gerar de Perfil (CUPP-like)                          ║
║  [4] 🔄 Converter para Leet Speak                            ║
║  [5] 📎 Combinar Palavras                                    ║
║  [6] 📁 Mesclar Wordlists                                    ║
║  [7] 📊 Analisar Wordlist                                    ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Gerar de Palavras Base ===")
            print("Digite as palavras base (separadas por vírgula):")
            words_input = input("> ").strip()
            
            if not words_input:
                continue
            
            words = [w.strip() for w in words_input.split(",")]
            
            print("\nOpções:")
            use_leet = input("Incluir variações leet? (s/n): ").lower() == 's'
            use_case = input("Incluir variações de case? (s/n): ").lower() == 's'
            use_suffix = input("Incluir sufixos comuns? (s/n): ").lower() == 's'
            
            print("\nGerando...")
            result = generator.from_base_words(words, use_leet, use_case, use_suffix)
            
            print(f"\n✅ {len(result)} palavras geradas")
            print("\nPrimeiras 20:")
            for word in list(result)[:20]:
                print(f"   {word}")
            
            save = input("\nSalvar em arquivo? (s/n): ").lower()
            if save == 's':
                filepath = input("Caminho do arquivo: ").strip()
                if filepath:
                    generator.save_wordlist(result, filepath)
                    print(f"✅ Salvo em {filepath}")
        
        elif escolha == '2':
            print("\n=== Gerar de Padrão ===")
            print("Padrões disponíveis:")
            print("  ?l = letra minúscula")
            print("  ?u = letra maiúscula")
            print("  ?d = dígito")
            print("  ?s = caractere especial")
            print("  ?a = todos")
            print("\nExemplo: senha?d?d?d (senha + 3 dígitos)")
            
            pattern = input("\nPadrão: ").strip()
            
            if not pattern:
                continue
            
            # Estima combinações
            estimate = PatternGenerator.estimate_combinations(pattern)
            print(f"\nEstimativa: {estimate:,} combinações")
            
            if estimate > 100000:
                print("⚠️  Muitas combinações! Limitando a 100.000")
                max_results = 100000
            else:
                max_results = min(estimate, 100000)
            
            confirm = input("Continuar? (s/n): ").lower()
            if confirm != 's':
                continue
            
            print("Gerando...")
            result = set(generator.from_pattern(pattern, max_results))
            
            print(f"\n✅ {len(result)} palavras geradas")
            print("\nPrimeiras 20:")
            for word in list(result)[:20]:
                print(f"   {word}")
            
            save = input("\nSalvar em arquivo? (s/n): ").lower()
            if save == 's':
                filepath = input("Caminho do arquivo: ").strip()
                if filepath:
                    generator.save_wordlist(result, filepath)
                    print(f"✅ Salvo em {filepath}")
        
        elif escolha == '3':
            print("\n=== Gerar de Perfil ===")
            print("Responda as perguntas (Enter para pular):\n")
            
            profile = {}
            profile["first_name"] = input("Primeiro nome: ").strip() or None
            profile["last_name"] = input("Sobrenome: ").strip() or None
            profile["nickname"] = input("Apelido: ").strip() or None
            profile["birthdate"] = input("Data de nascimento (DD/MM/AAAA): ").strip() or None
            profile["pet_name"] = input("Nome do pet: ").strip() or None
            profile["company"] = input("Empresa: ").strip() or None
            
            keywords_input = input("Palavras-chave (vírgula): ").strip()
            if keywords_input:
                profile["keywords"] = [k.strip() for k in keywords_input.split(",")]
            
            if not any(profile.values()):
                print("\n❌ Nenhum dado informado")
                input("\nPressione Enter para continuar...")
                continue
            
            print("\nGerando...")
            result = generator.from_profile(profile)
            
            print(f"\n✅ {len(result)} palavras geradas")
            print("\nPrimeiras 30:")
            for word in list(result)[:30]:
                print(f"   {word}")
            
            save = input("\nSalvar em arquivo? (s/n): ").lower()
            if save == 's':
                filepath = input("Caminho do arquivo: ").strip()
                if filepath:
                    generator.save_wordlist(result, filepath)
                    print(f"✅ Salvo em {filepath}")
        
        elif escolha == '4':
            print("\n=== Converter para Leet Speak ===")
            word = input("Palavra: ").strip()
            
            if not word:
                continue
            
            print("\n1. Conversão simples")
            print("2. Gerar variações")
            op = input("Opção: ").strip()
            
            if op == '1':
                result = LeetSpeakConverter.simple_leet(word)
                print(f"\n✅ Resultado: {result}")
            else:
                max_var = int(input("Máximo de variações (padrão 50): ") or "50")
                variations = LeetSpeakConverter.generate_variations(word, max_var)
                
                print(f"\n✅ {len(variations)} variações:")
                for var in variations[:30]:
                    print(f"   {var}")
                
                if len(variations) > 30:
                    print(f"   ... e mais {len(variations) - 30}")
        
        elif escolha == '5':
            print("\n=== Combinar Palavras ===")
            words_input = input("Palavras (vírgula): ").strip()
            
            if not words_input:
                continue
            
            words = [w.strip() for w in words_input.split(",")]
            
            print("\n1. Combinar entre si")
            print("2. Combinar com números")
            print("3. Ambos")
            op = input("Opção: ").strip()
            
            result = set()
            
            if op in ['1', '3']:
                result.update(CombinationGenerator.combine_words(words))
            
            if op in ['2', '3']:
                result.update(CombinationGenerator.combine_with_numbers(words))
            
            print(f"\n✅ {len(result)} combinações:")
            for combo in list(result)[:30]:
                print(f"   {combo}")
        
        elif escolha == '6':
            print("\n=== Mesclar Wordlists ===")
            print("Digite os caminhos dos arquivos (um por linha, vazio para terminar):")
            
            paths = []
            while True:
                path = input("> ").strip()
                if not path:
                    break
                if os.path.isfile(path):
                    paths.append(path)
                else:
                    print(f"   ⚠️  Arquivo não encontrado: {path}")
            
            if not paths:
                continue
            
            result = generator.merge_wordlists(*paths)
            
            print(f"\n✅ {len(result)} palavras únicas")
            
            save = input("\nSalvar resultado? (s/n): ").lower()
            if save == 's':
                filepath = input("Caminho do arquivo: ").strip()
                if filepath:
                    generator.save_wordlist(result, filepath)
                    print(f"✅ Salvo em {filepath}")
        
        elif escolha == '7':
            print("\n=== Analisar Wordlist ===")
            filepath = input("Caminho do arquivo: ").strip()
            
            if not filepath or not os.path.isfile(filepath):
                print("❌ Arquivo não encontrado")
                input("\nPressione Enter para continuar...")
                continue
            
            words = generator.load_wordlist(filepath)
            
            # Estatísticas
            lengths = [len(w) for w in words]
            
            print(f"\n📊 Análise:")
            print(f"   Total de palavras: {len(words):,}")
            print(f"   Palavras únicas: {len(set(words)):,}")
            print(f"   Tamanho mínimo: {min(lengths)}")
            print(f"   Tamanho máximo: {max(lengths)}")
            print(f"   Tamanho médio: {sum(lengths) / len(lengths):.1f}")
            
            # Distribuição de tamanhos
            print("\n   Distribuição por tamanho:")
            from collections import Counter
            size_dist = Counter(lengths)
            for size in sorted(size_dist.keys())[:10]:
                count = size_dist[size]
                bar = '█' * min(count // 100, 30)
                print(f"     {size:2d} chars: {count:6,} {bar}")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
