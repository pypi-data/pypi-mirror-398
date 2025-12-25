#!/usr/bin/env python3
"""
Regex Builder - Construtor e testador de expressões regulares
Parte do toolkit Olho de Deus
"""

import os
import sys
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass 
class RegexMatch:
    """Resultado de um match de regex."""
    pattern: str
    text: str
    match: str
    start: int
    end: int
    groups: Tuple
    group_dict: Dict
    
    def to_dict(self) -> Dict:
        return {
            "match": self.match,
            "start": self.start,
            "end": self.end,
            "groups": self.groups,
            "named_groups": self.group_dict
        }


@dataclass
class RegexTest:
    """Resultado de teste de regex."""
    pattern: str
    text: str
    matches: List[RegexMatch]
    is_valid: bool
    error: str = ""


class RegexPatternLibrary:
    """Biblioteca de padrões regex comuns para segurança."""
    
    PATTERNS = {
        # Rede e Internet
        "ipv4": {
            "pattern": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
            "description": "Endereço IPv4",
            "example": "192.168.1.1"
        },
        "ipv6": {
            "pattern": r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b",
            "description": "Endereço IPv6 (formato completo)",
            "example": "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        },
        "mac_address": {
            "pattern": r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b",
            "description": "Endereço MAC",
            "example": "00:1A:2B:3C:4D:5E"
        },
        "url": {
            "pattern": r"https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_+.~#?&/=]*)",
            "description": "URL HTTP/HTTPS",
            "example": "https://example.com/path?query=value"
        },
        "domain": {
            "pattern": r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b",
            "description": "Nome de domínio",
            "example": "subdomain.example.com"
        },
        "email": {
            "pattern": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
            "description": "Endereço de email",
            "example": "user@example.com"
        },
        "port": {
            "pattern": r"\b(?:6553[0-5]|655[0-2][0-9]|65[0-4][0-9]{2}|6[0-4][0-9]{3}|[1-5][0-9]{4}|[1-9][0-9]{0,3})\b",
            "description": "Número de porta (1-65535)",
            "example": "8080"
        },
        
        # Credenciais e Segurança
        "jwt": {
            "pattern": r"\beyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\b",
            "description": "JSON Web Token (JWT)",
            "example": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        },
        "api_key": {
            "pattern": r"\b[a-zA-Z0-9]{32,64}\b",
            "description": "API Key (32-64 caracteres alfanuméricos)",
            "example": "sk_live_abcdefghijklmnopqrstuvwxyz123456"
        },
        "aws_access_key": {
            "pattern": r"\bAKIA[0-9A-Z]{16}\b",
            "description": "AWS Access Key ID",
            "example": "AKIAIOSFODNN7EXAMPLE"
        },
        "aws_secret_key": {
            "pattern": r"\b[a-zA-Z0-9/+=]{40}\b",
            "description": "AWS Secret Access Key",
            "example": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        },
        "github_token": {
            "pattern": r"\bghp_[a-zA-Z0-9]{36}\b",
            "description": "GitHub Personal Access Token",
            "example": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        },
        "private_key": {
            "pattern": r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----",
            "description": "Início de chave privada",
            "example": "-----BEGIN RSA PRIVATE KEY-----"
        },
        
        # Hashes
        "md5": {
            "pattern": r"\b[a-fA-F0-9]{32}\b",
            "description": "Hash MD5",
            "example": "d41d8cd98f00b204e9800998ecf8427e"
        },
        "sha1": {
            "pattern": r"\b[a-fA-F0-9]{40}\b",
            "description": "Hash SHA-1",
            "example": "da39a3ee5e6b4b0d3255bfef95601890afd80709"
        },
        "sha256": {
            "pattern": r"\b[a-fA-F0-9]{64}\b",
            "description": "Hash SHA-256",
            "example": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        },
        
        # Arquivos e Sistema
        "windows_path": {
            "pattern": r'[A-Z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*',
            "description": "Caminho Windows",
            "example": "C:\\Users\\Admin\\file.txt"
        },
        "unix_path": {
            "pattern": r"/(?:[^/\0]+/)*[^/\0]*",
            "description": "Caminho Unix/Linux",
            "example": "/home/user/file.txt"
        },
        "file_extension": {
            "pattern": r"\.[a-zA-Z0-9]{1,10}$",
            "description": "Extensão de arquivo",
            "example": ".txt"
        },
        
        # Dados Pessoais (PII)
        "phone_br": {
            "pattern": r"\+?55\s?(?:\([1-9]{2}\)|[1-9]{2})\s?9?\d{4}[-\s]?\d{4}",
            "description": "Telefone brasileiro",
            "example": "+55 (11) 99999-9999"
        },
        "cpf": {
            "pattern": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
            "description": "CPF brasileiro",
            "example": "123.456.789-00"
        },
        "cnpj": {
            "pattern": r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b",
            "description": "CNPJ brasileiro",
            "example": "12.345.678/0001-90"
        },
        "credit_card": {
            "pattern": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
            "description": "Número de cartão de crédito",
            "example": "4111-1111-1111-1111"
        },
        "ssn": {
            "pattern": r"\b\d{3}-\d{2}-\d{4}\b",
            "description": "Social Security Number (SSN)",
            "example": "123-45-6789"
        },
        
        # Logs e Segurança
        "log_level": {
            "pattern": r"\b(?:DEBUG|INFO|WARNING|ERROR|CRITICAL|FATAL|TRACE)\b",
            "description": "Nível de log",
            "example": "ERROR"
        },
        "http_status": {
            "pattern": r"\b[1-5][0-9]{2}\b",
            "description": "Código de status HTTP",
            "example": "404"
        },
        "user_agent": {
            "pattern": r"Mozilla/[^\s]+\s+\([^)]+\)",
            "description": "User-Agent (início)",
            "example": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        },
        
        # Código
        "sql_injection": {
            "pattern": r"(?:'|\"|;|--|\bOR\b|\bAND\b|\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b).*(?:=|<|>|\bLIKE\b)",
            "description": "Padrão de SQL Injection",
            "example": "' OR '1'='1"
        },
        "xss_pattern": {
            "pattern": r"<\s*script[^>]*>|javascript:|on\w+\s*=",
            "description": "Padrão de XSS",
            "example": "<script>alert(1)</script>"
        },
        "base64": {
            "pattern": r"\b[A-Za-z0-9+/]{20,}={0,2}\b",
            "description": "String Base64",
            "example": "SGVsbG8gV29ybGQh"
        },
    }
    
    @classmethod
    def get_pattern(cls, name: str) -> Optional[Dict]:
        """Retorna um padrão específico."""
        return cls.PATTERNS.get(name)
    
    @classmethod
    def get_all(cls) -> Dict:
        """Retorna todos os padrões."""
        return cls.PATTERNS
    
    @classmethod
    def search(cls, keyword: str) -> Dict:
        """Busca padrões por palavra-chave."""
        keyword = keyword.lower()
        results = {}
        for name, pattern in cls.PATTERNS.items():
            if keyword in name.lower() or keyword in pattern["description"].lower():
                results[name] = pattern
        return results


class RegexBuilder:
    """Construtor de expressões regulares."""
    
    def __init__(self):
        self.pattern_parts = []
        self.flags = 0
    
    def clear(self):
        """Limpa o padrão atual."""
        self.pattern_parts = []
        self.flags = 0
        return self
    
    def add(self, part: str) -> 'RegexBuilder':
        """Adiciona parte ao padrão."""
        self.pattern_parts.append(part)
        return self
    
    def literal(self, text: str) -> 'RegexBuilder':
        """Adiciona texto literal (escapado)."""
        self.pattern_parts.append(re.escape(text))
        return self
    
    def any_char(self) -> 'RegexBuilder':
        """Qualquer caractere (.)."""
        self.pattern_parts.append(".")
        return self
    
    def digit(self) -> 'RegexBuilder':
        """Dígito (\\d)."""
        self.pattern_parts.append(r"\d")
        return self
    
    def digits(self, min_count: int = 1, max_count: int = None) -> 'RegexBuilder':
        """Dígitos com quantidade."""
        if max_count:
            self.pattern_parts.append(rf"\d{{{min_count},{max_count}}}")
        else:
            self.pattern_parts.append(rf"\d{{{min_count},}}")
        return self
    
    def word(self) -> 'RegexBuilder':
        """Caractere de palavra (\\w)."""
        self.pattern_parts.append(r"\w")
        return self
    
    def words(self, min_count: int = 1, max_count: int = None) -> 'RegexBuilder':
        """Caracteres de palavra com quantidade."""
        if max_count:
            self.pattern_parts.append(rf"\w{{{min_count},{max_count}}}")
        else:
            self.pattern_parts.append(rf"\w{{{min_count},}}")
        return self
    
    def whitespace(self) -> 'RegexBuilder':
        """Espaço em branco (\\s)."""
        self.pattern_parts.append(r"\s")
        return self
    
    def optional(self, part: str) -> 'RegexBuilder':
        """Parte opcional (?)."""
        self.pattern_parts.append(f"(?:{part})?")
        return self
    
    def group(self, part: str, name: str = None) -> 'RegexBuilder':
        """Grupo de captura."""
        if name:
            self.pattern_parts.append(f"(?P<{name}>{part})")
        else:
            self.pattern_parts.append(f"({part})")
        return self
    
    def either(self, *options: str) -> 'RegexBuilder':
        """Alternativas (|)."""
        self.pattern_parts.append(f"(?:{'|'.join(options)})")
        return self
    
    def start_of_line(self) -> 'RegexBuilder':
        """Início da linha (^)."""
        self.pattern_parts.append("^")
        return self
    
    def end_of_line(self) -> 'RegexBuilder':
        """Fim da linha ($)."""
        self.pattern_parts.append("$")
        return self
    
    def word_boundary(self) -> 'RegexBuilder':
        """Limite de palavra (\\b)."""
        self.pattern_parts.append(r"\b")
        return self
    
    def repeat(self, part: str, min_count: int, max_count: int = None) -> 'RegexBuilder':
        """Repetição com quantidade."""
        if max_count is None:
            self.pattern_parts.append(f"(?:{part}){{{min_count},}}")
        elif min_count == max_count:
            self.pattern_parts.append(f"(?:{part}){{{min_count}}}")
        else:
            self.pattern_parts.append(f"(?:{part}){{{min_count},{max_count}}}")
        return self
    
    def zero_or_more(self, part: str) -> 'RegexBuilder':
        """Zero ou mais (*)."""
        self.pattern_parts.append(f"(?:{part})*")
        return self
    
    def one_or_more(self, part: str) -> 'RegexBuilder':
        """Um ou mais (+)."""
        self.pattern_parts.append(f"(?:{part})+")
        return self
    
    def char_class(self, chars: str) -> 'RegexBuilder':
        """Classe de caracteres [...]."""
        self.pattern_parts.append(f"[{chars}]")
        return self
    
    def not_char_class(self, chars: str) -> 'RegexBuilder':
        """Classe de caracteres negada [^...]."""
        self.pattern_parts.append(f"[^{chars}]")
        return self
    
    def case_insensitive(self) -> 'RegexBuilder':
        """Adiciona flag case insensitive."""
        self.flags |= re.IGNORECASE
        return self
    
    def multiline(self) -> 'RegexBuilder':
        """Adiciona flag multiline."""
        self.flags |= re.MULTILINE
        return self
    
    def dotall(self) -> 'RegexBuilder':
        """Adiciona flag dotall."""
        self.flags |= re.DOTALL
        return self
    
    def build(self) -> str:
        """Constrói o padrão final."""
        return "".join(self.pattern_parts)
    
    def compile(self) -> re.Pattern:
        """Compila o padrão."""
        return re.compile(self.build(), self.flags)


class RegexTester:
    """Testador de expressões regulares."""
    
    @staticmethod
    def validate_pattern(pattern: str) -> Tuple[bool, str]:
        """Valida se um padrão regex é válido."""
        try:
            re.compile(pattern)
            return True, ""
        except re.error as e:
            return False, str(e)
    
    @staticmethod
    def test(pattern: str, text: str, flags: int = 0) -> RegexTest:
        """Testa um padrão contra um texto."""
        is_valid, error = RegexTester.validate_pattern(pattern)
        
        if not is_valid:
            return RegexTest(
                pattern=pattern,
                text=text,
                matches=[],
                is_valid=False,
                error=error
            )
        
        try:
            compiled = re.compile(pattern, flags)
            matches = []
            
            for match in compiled.finditer(text):
                matches.append(RegexMatch(
                    pattern=pattern,
                    text=text,
                    match=match.group(),
                    start=match.start(),
                    end=match.end(),
                    groups=match.groups(),
                    group_dict=match.groupdict()
                ))
            
            return RegexTest(
                pattern=pattern,
                text=text,
                matches=matches,
                is_valid=True
            )
        except Exception as e:
            return RegexTest(
                pattern=pattern,
                text=text,
                matches=[],
                is_valid=False,
                error=str(e)
            )
    
    @staticmethod
    def replace(pattern: str, text: str, replacement: str, flags: int = 0) -> str:
        """Substitui matches de um padrão."""
        return re.sub(pattern, replacement, text, flags=flags)
    
    @staticmethod
    def split(pattern: str, text: str, flags: int = 0) -> List[str]:
        """Divide texto por um padrão."""
        return re.split(pattern, text, flags=flags)
    
    @staticmethod
    def explain_pattern(pattern: str) -> List[str]:
        """Explica um padrão regex (simplificado)."""
        explanations = {
            r"\d": "Dígito (0-9)",
            r"\D": "Não-dígito",
            r"\w": "Caractere de palavra (a-z, A-Z, 0-9, _)",
            r"\W": "Não-caractere de palavra",
            r"\s": "Espaço em branco",
            r"\S": "Não-espaço em branco",
            r"\b": "Limite de palavra",
            r"\B": "Não-limite de palavra",
            r"^": "Início da linha/string",
            r"$": "Fim da linha/string",
            r".": "Qualquer caractere (exceto newline)",
            r"*": "Zero ou mais do anterior",
            r"+": "Um ou mais do anterior",
            r"?": "Zero ou um do anterior (opcional)",
            r"|": "OU (alternativa)",
            r"[": "Início de classe de caracteres",
            r"]": "Fim de classe de caracteres",
            r"(": "Início de grupo de captura",
            r")": "Fim de grupo de captura",
            r"{": "Início de quantificador",
            r"}": "Fim de quantificador",
        }
        
        result = []
        for token, explanation in explanations.items():
            if token in pattern:
                result.append(f"{token} → {explanation}")
        
        return result


def interactive_menu():
    """Menu interativo do Regex Builder."""
    library = RegexPatternLibrary()
    tester = RegexTester()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║          🔍 REGEX BUILDER - Olho de Deus                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🧪 Testar Regex                                         ║
║  [2] 🏗️  Construir Regex (Assistido)                          ║
║  [3] 📚 Biblioteca de Padrões                                ║
║  [4] 🔄 Substituir com Regex                                 ║
║  [5] ✂️  Dividir com Regex                                    ║
║  [6] 📖 Explicar Padrão                                      ║
║  [7] ✅ Validar Padrão                                       ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Testar Regex ===")
            pattern = input("Padrão regex: ").strip()
            
            if not pattern:
                continue
            
            print("\nDigite o texto (linha vazia para terminar):")
            lines = []
            while True:
                line = input()
                if not line:
                    break
                lines.append(line)
            
            text = "\n".join(lines)
            
            if not text:
                continue
            
            result = tester.test(pattern, text)
            
            if not result.is_valid:
                print(f"\n❌ Padrão inválido: {result.error}")
            elif result.matches:
                print(f"\n✅ {len(result.matches)} match(es) encontrado(s):\n")
                
                for i, match in enumerate(result.matches, 1):
                    print(f"   {i}. \"{match.match}\"")
                    print(f"      Posição: {match.start}-{match.end}")
                    if match.groups:
                        print(f"      Grupos: {match.groups}")
                    if match.group_dict:
                        print(f"      Grupos nomeados: {match.group_dict}")
            else:
                print("\n⚠️  Nenhum match encontrado")
        
        elif escolha == '2':
            print("\n=== Construir Regex ===")
            print("Use os comandos para construir seu padrão:\n")
            print("  literal <texto>  - Texto literal")
            print("  digit            - Um dígito (\\d)")
            print("  digits N [M]     - N a M dígitos")
            print("  word             - Caractere palavra (\\w)")
            print("  words N [M]      - N a M caracteres palavra")
            print("  any              - Qualquer caractere (.)")
            print("  space            - Espaço (\\s)")
            print("  start            - Início (^)")
            print("  end              - Fim ($)")
            print("  boundary         - Limite palavra (\\b)")
            print("  optional <regex> - Opcional (?)")
            print("  group <regex>    - Grupo de captura")
            print("  either A|B|C     - Alternativas")
            print("  chars [abc]      - Classe de caracteres")
            print("  show             - Mostra padrão atual")
            print("  clear            - Limpa padrão")
            print("  done             - Finaliza\n")
            
            builder = RegexBuilder()
            
            while True:
                cmd = input("Builder> ").strip()
                
                if cmd == "done":
                    break
                elif cmd == "show":
                    print(f"   Padrão: {builder.build()}")
                elif cmd == "clear":
                    builder.clear()
                    print("   ✓ Padrão limpo")
                elif cmd.startswith("literal "):
                    builder.literal(cmd[8:])
                    print(f"   ✓ Adicionado literal")
                elif cmd == "digit":
                    builder.digit()
                    print("   ✓ Adicionado \\d")
                elif cmd.startswith("digits "):
                    parts = cmd[7:].split()
                    min_c = int(parts[0])
                    max_c = int(parts[1]) if len(parts) > 1 else None
                    builder.digits(min_c, max_c)
                    print("   ✓ Adicionado dígitos")
                elif cmd == "word":
                    builder.word()
                    print("   ✓ Adicionado \\w")
                elif cmd.startswith("words "):
                    parts = cmd[6:].split()
                    min_c = int(parts[0])
                    max_c = int(parts[1]) if len(parts) > 1 else None
                    builder.words(min_c, max_c)
                    print("   ✓ Adicionado palavras")
                elif cmd == "any":
                    builder.any_char()
                    print("   ✓ Adicionado .")
                elif cmd == "space":
                    builder.whitespace()
                    print("   ✓ Adicionado \\s")
                elif cmd == "start":
                    builder.start_of_line()
                    print("   ✓ Adicionado ^")
                elif cmd == "end":
                    builder.end_of_line()
                    print("   ✓ Adicionado $")
                elif cmd == "boundary":
                    builder.word_boundary()
                    print("   ✓ Adicionado \\b")
                elif cmd.startswith("optional "):
                    builder.optional(cmd[9:])
                    print("   ✓ Adicionado opcional")
                elif cmd.startswith("group "):
                    builder.group(cmd[6:])
                    print("   ✓ Adicionado grupo")
                elif cmd.startswith("either "):
                    options = cmd[7:].split("|")
                    builder.either(*options)
                    print("   ✓ Adicionado alternativas")
                elif cmd.startswith("chars "):
                    builder.char_class(cmd[6:])
                    print("   ✓ Adicionado classe")
                else:
                    print("   ❌ Comando não reconhecido")
            
            final_pattern = builder.build()
            print(f"\n✅ Padrão final: {final_pattern}")
        
        elif escolha == '3':
            print("\n=== Biblioteca de Padrões ===")
            print("1. Listar todos")
            print("2. Buscar por palavra-chave")
            print("3. Ver detalhes de um padrão")
            
            op = input("\nOpção: ").strip()
            
            if op == '1':
                patterns = library.get_all()
                print("\n📚 Padrões disponíveis:\n")
                
                for name in sorted(patterns.keys()):
                    desc = patterns[name]["description"]
                    print(f"   • {name}: {desc}")
            
            elif op == '2':
                keyword = input("Buscar: ").strip()
                results = library.search(keyword)
                
                if results:
                    print(f"\n🔍 {len(results)} resultado(s):\n")
                    for name, pattern in results.items():
                        print(f"   • {name}: {pattern['description']}")
                else:
                    print("\n⚠️  Nenhum resultado encontrado")
            
            elif op == '3':
                name = input("Nome do padrão: ").strip()
                pattern = library.get_pattern(name)
                
                if pattern:
                    print(f"\n📌 {name}:")
                    print(f"   Descrição: {pattern['description']}")
                    print(f"   Padrão: {pattern['pattern']}")
                    print(f"   Exemplo: {pattern['example']}")
                else:
                    print("\n❌ Padrão não encontrado")
        
        elif escolha == '4':
            print("\n=== Substituir com Regex ===")
            pattern = input("Padrão: ").strip()
            replacement = input("Substituição: ").strip()
            text = input("Texto: ").strip()
            
            if not all([pattern, replacement, text]):
                continue
            
            try:
                result = tester.replace(pattern, text, replacement)
                print(f"\n✅ Resultado:")
                print(result)
            except Exception as e:
                print(f"\n❌ Erro: {e}")
        
        elif escolha == '5':
            print("\n=== Dividir com Regex ===")
            pattern = input("Padrão separador: ").strip()
            text = input("Texto: ").strip()
            
            if not pattern or not text:
                continue
            
            try:
                parts = tester.split(pattern, text)
                print(f"\n✅ {len(parts)} partes:")
                for i, part in enumerate(parts, 1):
                    print(f"   {i}. \"{part}\"")
            except Exception as e:
                print(f"\n❌ Erro: {e}")
        
        elif escolha == '6':
            print("\n=== Explicar Padrão ===")
            pattern = input("Padrão: ").strip()
            
            if not pattern:
                continue
            
            explanations = tester.explain_pattern(pattern)
            
            if explanations:
                print("\n📖 Componentes encontrados:\n")
                for exp in explanations:
                    print(f"   {exp}")
            else:
                print("\n⚠️  Nenhum componente especial encontrado")
        
        elif escolha == '7':
            print("\n=== Validar Padrão ===")
            pattern = input("Padrão: ").strip()
            
            if not pattern:
                continue
            
            is_valid, error = tester.validate_pattern(pattern)
            
            if is_valid:
                print("\n✅ Padrão válido!")
            else:
                print(f"\n❌ Padrão inválido: {error}")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
