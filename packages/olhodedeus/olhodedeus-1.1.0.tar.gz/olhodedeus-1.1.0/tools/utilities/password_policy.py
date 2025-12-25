#!/usr/bin/env python3
"""
Password Policy - Análise de força e políticas de senhas
Parte do toolkit Olho de Deus
"""

import os
import sys
import re
import math
import string
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PolicyRule:
    """Regra de política de senha."""
    name: str
    description: str
    check_func: callable
    weight: int = 1
    required: bool = True


@dataclass
class PasswordAnalysis:
    """Resultado da análise de senha."""
    password: str
    length: int
    entropy: float
    score: int  # 0-100
    strength: str  # Muito Fraca, Fraca, Média, Forte, Muito Forte
    passed_rules: List[str]
    failed_rules: List[str]
    suggestions: List[str]
    crack_time_seconds: float
    crack_time_display: str
    
    def to_dict(self) -> Dict:
        return {
            "length": self.length,
            "entropy": self.entropy,
            "score": self.score,
            "strength": self.strength,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "suggestions": self.suggestions,
            "crack_time": self.crack_time_display
        }


class CommonPatterns:
    """Padrões comuns de senhas fracas."""
    
    KEYBOARD_PATTERNS = [
        'qwerty', 'qwertyuiop', 'asdfgh', 'asdfghjkl', 'zxcvbn', 'zxcvbnm',
        '1234567890', '0987654321', 'qwert', 'asdf', 'zxcv',
        '1qaz', '2wsx', '3edc', '4rfv', '5tgb', '6yhn', '7ujm', '8ik,', '9ol.',
        'qazwsx', 'wsxedc', 'edcrfv', 'rfvtgb',
    ]
    
    COMMON_WORDS = [
        'password', 'senha', 'admin', 'administrator', 'root', 'user', 'guest',
        'login', 'welcome', 'master', 'letmein', 'access', 'pass', 'test',
        'hello', 'dragon', 'monkey', 'shadow', 'sunshine', 'princess', 'batman',
        'football', 'baseball', 'soccer', 'hockey', 'superman', 'trustno1',
    ]
    
    COMMON_SUBSTITUTIONS = {
        '4': 'a', '@': 'a', '3': 'e', '1': 'i', '!': 'i', '0': 'o',
        '5': 's', '$': 's', '7': 't', '+': 't'
    }
    
    @classmethod
    def has_keyboard_pattern(cls, password: str) -> bool:
        """Verifica se contém padrão de teclado."""
        lower = password.lower()
        for pattern in cls.KEYBOARD_PATTERNS:
            if pattern in lower or pattern[::-1] in lower:
                return True
        return False
    
    @classmethod
    def has_common_word(cls, password: str) -> bool:
        """Verifica se contém palavra comum."""
        lower = password.lower()
        
        # Desfaz substituições leet
        normalized = lower
        for leet, char in cls.COMMON_SUBSTITUTIONS.items():
            normalized = normalized.replace(leet, char)
        
        for word in cls.COMMON_WORDS:
            if word in lower or word in normalized:
                return True
        
        return False
    
    @classmethod
    def has_repetition(cls, password: str, min_length: int = 3) -> bool:
        """Verifica se contém repetição."""
        for i in range(len(password) - min_length + 1):
            pattern = password[i:i + min_length]
            if password.count(pattern) > 1:
                return True
        return False
    
    @classmethod
    def has_sequential_chars(cls, password: str, min_length: int = 3) -> bool:
        """Verifica se contém sequência de caracteres."""
        for i in range(len(password) - min_length + 1):
            segment = password[i:i + min_length]
            
            # Sequência crescente
            is_sequential = True
            for j in range(1, len(segment)):
                if ord(segment[j]) != ord(segment[j-1]) + 1:
                    is_sequential = False
                    break
            if is_sequential:
                return True
            
            # Sequência decrescente
            is_sequential = True
            for j in range(1, len(segment)):
                if ord(segment[j]) != ord(segment[j-1]) - 1:
                    is_sequential = False
                    break
            if is_sequential:
                return True
        
        return False


class EntropyCalculator:
    """Calculador de entropia de senha."""
    
    @staticmethod
    def calculate_charset_size(password: str) -> int:
        """Calcula o tamanho do conjunto de caracteres."""
        charset_size = 0
        
        if any(c in string.ascii_lowercase for c in password):
            charset_size += 26
        if any(c in string.ascii_uppercase for c in password):
            charset_size += 26
        if any(c in string.digits for c in password):
            charset_size += 10
        if any(c in string.punctuation for c in password):
            charset_size += 32
        if any(c not in string.printable for c in password):
            charset_size += 100  # Unicode
        
        return max(charset_size, 1)
    
    @staticmethod
    def calculate_entropy(password: str) -> float:
        """Calcula a entropia da senha em bits."""
        charset_size = EntropyCalculator.calculate_charset_size(password)
        return len(password) * math.log2(charset_size)
    
    @staticmethod
    def calculate_crack_time(entropy: float, guesses_per_second: float = 1e10) -> float:
        """Calcula tempo estimado para quebrar a senha."""
        # 2^entropy combinações, metade em média para encontrar
        combinations = 2 ** entropy
        seconds = (combinations / 2) / guesses_per_second
        return seconds
    
    @staticmethod
    def format_time(seconds: float) -> str:
        """Formata tempo em unidade legível."""
        if seconds < 1:
            return "instantâneo"
        elif seconds < 60:
            return f"{seconds:.1f} segundos"
        elif seconds < 3600:
            return f"{seconds/60:.1f} minutos"
        elif seconds < 86400:
            return f"{seconds/3600:.1f} horas"
        elif seconds < 2592000:  # 30 dias
            return f"{seconds/86400:.1f} dias"
        elif seconds < 31536000:  # 365 dias
            return f"{seconds/2592000:.1f} meses"
        elif seconds < 31536000 * 100:
            return f"{seconds/31536000:.1f} anos"
        elif seconds < 31536000 * 1000000:
            return f"{seconds/(31536000*1000):.0f} milênios"
        else:
            return "bilhões de anos"


class PasswordPolicy:
    """Política de senha configurável."""
    
    def __init__(self):
        self.min_length = 8
        self.max_length = 128
        self.require_lowercase = True
        self.require_uppercase = True
        self.require_digits = True
        self.require_special = True
        self.min_unique_chars = 4
        self.forbid_common_patterns = True
        self.forbid_keyboard_patterns = True
        self.forbid_repetition = True
        self.forbid_sequential = True
    
    def configure(self, **kwargs):
        """Configura a política."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_rules(self) -> List[PolicyRule]:
        """Retorna as regras da política."""
        rules = []
        
        rules.append(PolicyRule(
            name="min_length",
            description=f"Mínimo de {self.min_length} caracteres",
            check_func=lambda p: len(p) >= self.min_length,
            weight=2,
            required=True
        ))
        
        rules.append(PolicyRule(
            name="max_length",
            description=f"Máximo de {self.max_length} caracteres",
            check_func=lambda p: len(p) <= self.max_length,
            weight=1,
            required=True
        ))
        
        if self.require_lowercase:
            rules.append(PolicyRule(
                name="lowercase",
                description="Contém letra minúscula",
                check_func=lambda p: any(c.islower() for c in p),
                weight=1,
                required=True
            ))
        
        if self.require_uppercase:
            rules.append(PolicyRule(
                name="uppercase",
                description="Contém letra maiúscula",
                check_func=lambda p: any(c.isupper() for c in p),
                weight=1,
                required=True
            ))
        
        if self.require_digits:
            rules.append(PolicyRule(
                name="digits",
                description="Contém número",
                check_func=lambda p: any(c.isdigit() for c in p),
                weight=1,
                required=True
            ))
        
        if self.require_special:
            rules.append(PolicyRule(
                name="special",
                description="Contém caractere especial",
                check_func=lambda p: any(c in string.punctuation for c in p),
                weight=1,
                required=True
            ))
        
        rules.append(PolicyRule(
            name="unique_chars",
            description=f"Mínimo de {self.min_unique_chars} caracteres únicos",
            check_func=lambda p: len(set(p)) >= self.min_unique_chars,
            weight=1,
            required=False
        ))
        
        if self.forbid_common_patterns:
            rules.append(PolicyRule(
                name="no_common",
                description="Não contém palavras comuns",
                check_func=lambda p: not CommonPatterns.has_common_word(p),
                weight=2,
                required=False
            ))
        
        if self.forbid_keyboard_patterns:
            rules.append(PolicyRule(
                name="no_keyboard",
                description="Não contém padrão de teclado",
                check_func=lambda p: not CommonPatterns.has_keyboard_pattern(p),
                weight=1,
                required=False
            ))
        
        if self.forbid_repetition:
            rules.append(PolicyRule(
                name="no_repetition",
                description="Não contém repetição",
                check_func=lambda p: not CommonPatterns.has_repetition(p),
                weight=1,
                required=False
            ))
        
        if self.forbid_sequential:
            rules.append(PolicyRule(
                name="no_sequential",
                description="Não contém sequência",
                check_func=lambda p: not CommonPatterns.has_sequential_chars(p),
                weight=1,
                required=False
            ))
        
        return rules


class PasswordAnalyzer:
    """Analisador de senhas."""
    
    def __init__(self, policy: PasswordPolicy = None):
        self.policy = policy or PasswordPolicy()
        self.entropy_calc = EntropyCalculator()
    
    def analyze(self, password: str) -> PasswordAnalysis:
        """Analisa uma senha completa."""
        # Verifica regras
        rules = self.policy.get_rules()
        passed = []
        failed = []
        total_weight = 0
        passed_weight = 0
        
        for rule in rules:
            total_weight += rule.weight
            try:
                if rule.check_func(password):
                    passed.append(rule.description)
                    passed_weight += rule.weight
                else:
                    failed.append(rule.description)
            except:
                failed.append(rule.description)
        
        # Calcula entropia
        entropy = self.entropy_calc.calculate_entropy(password)
        
        # Calcula score baseado em regras e entropia
        rule_score = (passed_weight / total_weight) * 50 if total_weight > 0 else 0
        
        # Score de entropia (até 50 pontos)
        # 40 bits = fraco, 60 bits = médio, 80 bits = forte, 100+ = muito forte
        entropy_score = min(50, (entropy / 100) * 50)
        
        score = int(rule_score + entropy_score)
        score = max(0, min(100, score))
        
        # Determina força
        if score < 20:
            strength = "Muito Fraca"
        elif score < 40:
            strength = "Fraca"
        elif score < 60:
            strength = "Média"
        elif score < 80:
            strength = "Forte"
        else:
            strength = "Muito Forte"
        
        # Gera sugestões
        suggestions = self._generate_suggestions(password, failed, entropy)
        
        # Calcula tempo de crack
        crack_seconds = self.entropy_calc.calculate_crack_time(entropy)
        crack_display = self.entropy_calc.format_time(crack_seconds)
        
        return PasswordAnalysis(
            password=password,
            length=len(password),
            entropy=entropy,
            score=score,
            strength=strength,
            passed_rules=passed,
            failed_rules=failed,
            suggestions=suggestions,
            crack_time_seconds=crack_seconds,
            crack_time_display=crack_display
        )
    
    def _generate_suggestions(self, password: str, failed: List[str], entropy: float) -> List[str]:
        """Gera sugestões de melhoria."""
        suggestions = []
        
        if len(password) < 12:
            suggestions.append("Aumente para pelo menos 12 caracteres")
        
        if entropy < 60:
            suggestions.append("Adicione mais variedade de caracteres")
        
        if not any(c.isupper() for c in password):
            suggestions.append("Adicione letras maiúsculas")
        
        if not any(c.islower() for c in password):
            suggestions.append("Adicione letras minúsculas")
        
        if not any(c.isdigit() for c in password):
            suggestions.append("Adicione números")
        
        if not any(c in string.punctuation for c in password):
            suggestions.append("Adicione caracteres especiais (!@#$%)")
        
        if CommonPatterns.has_common_word(password):
            suggestions.append("Evite palavras comuns do dicionário")
        
        if CommonPatterns.has_keyboard_pattern(password):
            suggestions.append("Evite padrões de teclado (qwerty, 123)")
        
        if CommonPatterns.has_repetition(password):
            suggestions.append("Evite repetição de caracteres ou padrões")
        
        if len(set(password)) < len(password) * 0.5:
            suggestions.append("Use mais caracteres diferentes")
        
        return suggestions


class PasswordGenerator:
    """Gerador de senhas fortes."""
    
    @staticmethod
    def generate(length: int = 16, 
                 use_lower: bool = True,
                 use_upper: bool = True,
                 use_digits: bool = True,
                 use_special: bool = True,
                 exclude_ambiguous: bool = True) -> str:
        """Gera uma senha forte."""
        import secrets
        
        charset = ""
        required = []
        
        if use_lower:
            chars = string.ascii_lowercase
            if exclude_ambiguous:
                chars = chars.replace('l', '').replace('o', '')
            charset += chars
            required.append(secrets.choice(chars))
        
        if use_upper:
            chars = string.ascii_uppercase
            if exclude_ambiguous:
                chars = chars.replace('I', '').replace('O', '')
            charset += chars
            required.append(secrets.choice(chars))
        
        if use_digits:
            chars = string.digits
            if exclude_ambiguous:
                chars = chars.replace('0', '').replace('1', '')
            charset += chars
            required.append(secrets.choice(chars))
        
        if use_special:
            chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            charset += chars
            required.append(secrets.choice(chars))
        
        if not charset:
            charset = string.ascii_letters + string.digits
        
        # Gera caracteres restantes
        remaining = length - len(required)
        password = list(required)
        password.extend(secrets.choice(charset) for _ in range(remaining))
        
        # Embaralha
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    @staticmethod
    def generate_passphrase(words: int = 4, separator: str = "-") -> str:
        """Gera uma passphrase."""
        import secrets
        
        # Lista de palavras comuns em português
        wordlist = [
            "amor", "casa", "vida", "tempo", "mundo", "olho", "mao", "dia",
            "agua", "terra", "fogo", "vento", "sol", "lua", "mar", "rio",
            "flor", "peixe", "gato", "cao", "lobo", "urso", "leao", "tigre",
            "verde", "azul", "roxo", "preto", "branco", "prata", "ouro", "ferro",
            "norte", "sul", "leste", "oeste", "alto", "baixo", "grande", "forte",
            "rapido", "livre", "novo", "belo", "feliz", "calmo", "sabio", "justo",
            "livro", "porta", "mesa", "cadeira", "janela", "parede", "teto", "piso",
            "chuva", "nuvem", "raio", "neve", "gelo", "pedra", "areia", "folha"
        ]
        
        selected = [secrets.choice(wordlist) for _ in range(words)]
        
        # Capitaliza primeira letra de cada palavra
        selected = [w.capitalize() for w in selected]
        
        # Adiciona número aleatório
        selected.append(str(secrets.randbelow(100)))
        
        return separator.join(selected)


def interactive_menu():
    """Menu interativo do Password Policy."""
    policy = PasswordPolicy()
    analyzer = PasswordAnalyzer(policy)
    generator = PasswordGenerator()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║         🔑 PASSWORD POLICY - Olho de Deus                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔍 Analisar Senha                                       ║
║  [2] ✅ Verificar Política                                   ║
║  [3] 🎲 Gerar Senha Forte                                    ║
║  [4] 📝 Gerar Passphrase                                     ║
║  [5] ⚙️  Configurar Política                                  ║
║  [6] 📊 Análise em Lote                                      ║
║  [7] 📋 Ver Política Atual                                   ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Analisar Senha ===")
            password = input("Senha: ").strip()
            
            if not password:
                continue
            
            result = analyzer.analyze(password)
            
            # Score visual
            bar_filled = '█' * (result.score // 5)
            bar_empty = '░' * (20 - result.score // 5)
            
            if result.score < 40:
                color = "🔴"
            elif result.score < 70:
                color = "🟡"
            else:
                color = "🟢"
            
            print(f"\n{color} Força: {result.strength}")
            print(f"   Score: [{bar_filled}{bar_empty}] {result.score}/100")
            print(f"\n📏 Tamanho: {result.length} caracteres")
            print(f"📊 Entropia: {result.entropy:.1f} bits")
            print(f"⏱️  Tempo para quebrar: {result.crack_time_display}")
            
            if result.passed_rules:
                print(f"\n✅ Regras atendidas ({len(result.passed_rules)}):")
                for rule in result.passed_rules:
                    print(f"   • {rule}")
            
            if result.failed_rules:
                print(f"\n❌ Regras não atendidas ({len(result.failed_rules)}):")
                for rule in result.failed_rules:
                    print(f"   • {rule}")
            
            if result.suggestions:
                print(f"\n💡 Sugestões:")
                for sug in result.suggestions:
                    print(f"   • {sug}")
        
        elif escolha == '2':
            print("\n=== Verificar Política ===")
            password = input("Senha: ").strip()
            
            if not password:
                continue
            
            result = analyzer.analyze(password)
            
            # Verifica apenas regras required
            rules = policy.get_rules()
            required_failed = []
            
            for rule in rules:
                if rule.required:
                    try:
                        if not rule.check_func(password):
                            required_failed.append(rule.description)
                    except:
                        required_failed.append(rule.description)
            
            if not required_failed:
                print("\n✅ Senha atende à política!")
            else:
                print("\n❌ Senha NÃO atende à política:")
                for rule in required_failed:
                    print(f"   • {rule}")
        
        elif escolha == '3':
            print("\n=== Gerar Senha Forte ===")
            length = int(input("Tamanho (padrão 16): ") or "16")
            
            print("\nIncluir (s/n):")
            use_lower = input("  Minúsculas? (s/n): ").lower() != 'n'
            use_upper = input("  Maiúsculas? (s/n): ").lower() != 'n'
            use_digits = input("  Números? (s/n): ").lower() != 'n'
            use_special = input("  Especiais? (s/n): ").lower() != 'n'
            
            password = generator.generate(
                length=length,
                use_lower=use_lower,
                use_upper=use_upper,
                use_digits=use_digits,
                use_special=use_special
            )
            
            print(f"\n🔑 Senha gerada: {password}")
            
            # Analisa a senha gerada
            result = analyzer.analyze(password)
            print(f"   Força: {result.strength} ({result.score}/100)")
            print(f"   Entropia: {result.entropy:.1f} bits")
            print(f"   Tempo para quebrar: {result.crack_time_display}")
        
        elif escolha == '4':
            print("\n=== Gerar Passphrase ===")
            words = int(input("Número de palavras (padrão 4): ") or "4")
            separator = input("Separador (padrão -): ") or "-"
            
            passphrase = generator.generate_passphrase(words, separator)
            
            print(f"\n🔑 Passphrase: {passphrase}")
            
            # Analisa
            result = analyzer.analyze(passphrase)
            print(f"   Força: {result.strength} ({result.score}/100)")
            print(f"   Entropia: {result.entropy:.1f} bits")
            print(f"   Tempo para quebrar: {result.crack_time_display}")
        
        elif escolha == '5':
            print("\n=== Configurar Política ===")
            print("Digite novo valor ou Enter para manter:\n")
            
            new_min = input(f"Tamanho mínimo [{policy.min_length}]: ").strip()
            if new_min:
                policy.min_length = int(new_min)
            
            new_lower = input(f"Exigir minúsculas [{policy.require_lowercase}]: ").strip()
            if new_lower:
                policy.require_lowercase = new_lower.lower() in ['s', 'true', '1']
            
            new_upper = input(f"Exigir maiúsculas [{policy.require_uppercase}]: ").strip()
            if new_upper:
                policy.require_uppercase = new_upper.lower() in ['s', 'true', '1']
            
            new_digits = input(f"Exigir números [{policy.require_digits}]: ").strip()
            if new_digits:
                policy.require_digits = new_digits.lower() in ['s', 'true', '1']
            
            new_special = input(f"Exigir especiais [{policy.require_special}]: ").strip()
            if new_special:
                policy.require_special = new_special.lower() in ['s', 'true', '1']
            
            # Recria analyzer com nova política
            analyzer = PasswordAnalyzer(policy)
            
            print("\n✅ Política atualizada!")
        
        elif escolha == '6':
            print("\n=== Análise em Lote ===")
            print("Digite as senhas (uma por linha, vazio para terminar):\n")
            
            passwords = []
            while True:
                pwd = input()
                if not pwd:
                    break
                passwords.append(pwd)
            
            if not passwords:
                continue
            
            print("\n📊 Resultados:\n")
            
            for pwd in passwords:
                result = analyzer.analyze(pwd)
                masked = pwd[:3] + '*' * (len(pwd) - 3)
                
                if result.score < 40:
                    icon = "🔴"
                elif result.score < 70:
                    icon = "🟡"
                else:
                    icon = "🟢"
                
                print(f"   {icon} {masked:20} | Score: {result.score:3}/100 | {result.strength}")
        
        elif escolha == '7':
            print("\n=== Política Atual ===\n")
            print(f"   📏 Tamanho mínimo: {policy.min_length}")
            print(f"   📏 Tamanho máximo: {policy.max_length}")
            print(f"   🔡 Exigir minúsculas: {'Sim' if policy.require_lowercase else 'Não'}")
            print(f"   🔠 Exigir maiúsculas: {'Sim' if policy.require_uppercase else 'Não'}")
            print(f"   🔢 Exigir números: {'Sim' if policy.require_digits else 'Não'}")
            print(f"   🔣 Exigir especiais: {'Sim' if policy.require_special else 'Não'}")
            print(f"   🔤 Mínimo chars únicos: {policy.min_unique_chars}")
            print(f"   🚫 Proibir padrões comuns: {'Sim' if policy.forbid_common_patterns else 'Não'}")
            print(f"   ⌨️  Proibir padrões teclado: {'Sim' if policy.forbid_keyboard_patterns else 'Não'}")
            print(f"   🔁 Proibir repetição: {'Sim' if policy.forbid_repetition else 'Não'}")
            print(f"   📈 Proibir sequências: {'Sim' if policy.forbid_sequential else 'Não'}")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
