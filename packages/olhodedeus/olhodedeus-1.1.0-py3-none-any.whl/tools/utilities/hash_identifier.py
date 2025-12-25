#!/usr/bin/env python3
"""
Hash Identifier - Identificação e análise de hashes
Parte do toolkit Olho de Deus
"""

import os
import sys
import hashlib
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class HashInfo:
    """Informações sobre um tipo de hash."""
    name: str
    length: int
    regex: str
    description: str
    category: str
    example: str


@dataclass
class HashMatch:
    """Resultado de identificação de hash."""
    hash_value: str
    possible_types: List[HashInfo]
    confidence: float
    
    def to_dict(self) -> Dict:
        return {
            "hash": self.hash_value,
            "types": [h.name for h in self.possible_types],
            "confidence": self.confidence
        }


class HashDatabase:
    """Banco de dados de tipos de hash."""
    
    HASH_TYPES = [
        # MD Family
        HashInfo("MD5", 32, r"^[a-f0-9]{32}$", "Message Digest 5", "MD", 
                "d41d8cd98f00b204e9800998ecf8427e"),
        HashInfo("MD4", 32, r"^[a-f0-9]{32}$", "Message Digest 4", "MD",
                "31d6cfe0d16ae931b73c59d7e0c089c0"),
        HashInfo("MD2", 32, r"^[a-f0-9]{32}$", "Message Digest 2", "MD",
                "8350e5a3e24c153df2275c9f80692773"),
        
        # SHA-1
        HashInfo("SHA-1", 40, r"^[a-f0-9]{40}$", "Secure Hash Algorithm 1", "SHA",
                "da39a3ee5e6b4b0d3255bfef95601890afd80709"),
        
        # SHA-2 Family
        HashInfo("SHA-224", 56, r"^[a-f0-9]{56}$", "SHA-2 224 bits", "SHA-2",
                "d14a028c2a3a2bc9476102bb288234c415a2b01f828ea62ac5b3e42f"),
        HashInfo("SHA-256", 64, r"^[a-f0-9]{64}$", "SHA-2 256 bits", "SHA-2",
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
        HashInfo("SHA-384", 96, r"^[a-f0-9]{96}$", "SHA-2 384 bits", "SHA-2",
                "38b060a751ac96384cd9327eb1b1e36a21fdb71114be07434c0cc7bf63f6e1da274edebfe76f65fbd51ad2f14898b95b"),
        HashInfo("SHA-512", 128, r"^[a-f0-9]{128}$", "SHA-2 512 bits", "SHA-2",
                "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"),
        
        # SHA-3 Family
        HashInfo("SHA3-224", 56, r"^[a-f0-9]{56}$", "SHA-3 224 bits", "SHA-3",
                "6b4e03423667dbb73b6e15454f0eb1abd4597f9a1b078e3f5b5a6bc7"),
        HashInfo("SHA3-256", 64, r"^[a-f0-9]{64}$", "SHA-3 256 bits", "SHA-3",
                "a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a"),
        HashInfo("SHA3-384", 96, r"^[a-f0-9]{96}$", "SHA-3 384 bits", "SHA-3",
                "0c63a75b845e4f7d01107d852e4c2485c51a50aaaa94fc61995e71bbee983a2ac3713831264adb47fb6bd1e058d5f004"),
        HashInfo("SHA3-512", 128, r"^[a-f0-9]{128}$", "SHA-3 512 bits", "SHA-3",
                "a69f73cca23a9ac5c8b567dc185a756e97c982164fe25859e0d1dcc1475c80a615b2123af1f5f94c11e3e9402c3ac558f500199d95b6d3e301758586281dcd26"),
        
        # BLAKE
        HashInfo("BLAKE2b-256", 64, r"^[a-f0-9]{64}$", "BLAKE2b 256 bits", "BLAKE",
                "0e5751c026e543b2e8ab2eb06099daa1d1e5df47778f7787faab45cdf12fe3a8"),
        HashInfo("BLAKE2b-512", 128, r"^[a-f0-9]{128}$", "BLAKE2b 512 bits", "BLAKE",
                "786a02f742015903c6c6fd852552d272912f4740e15847618a86e217f71f5419d25e1031afee585313896444934eb04b903a685b1448b755d56f701afe9be2ce"),
        HashInfo("BLAKE2s-256", 64, r"^[a-f0-9]{64}$", "BLAKE2s 256 bits", "BLAKE",
                "69217a3079908094e11121d042354a7c1f55b6482ca1a51e1b250dfd1ed0eef9"),
        
        # RIPEMD
        HashInfo("RIPEMD-128", 32, r"^[a-f0-9]{32}$", "RIPEMD 128 bits", "RIPEMD",
                "cdf26213a150dc3ecb610f18f6b38b46"),
        HashInfo("RIPEMD-160", 40, r"^[a-f0-9]{40}$", "RIPEMD 160 bits", "RIPEMD",
                "9c1185a5c5e9fc54612808977ee8f548b2258d31"),
        HashInfo("RIPEMD-256", 64, r"^[a-f0-9]{64}$", "RIPEMD 256 bits", "RIPEMD",
                "02ba4c4e5f8ecd1877fc52d64d30e37a2d9774fb1e5d026380ae0168e3c5522d"),
        HashInfo("RIPEMD-320", 80, r"^[a-f0-9]{80}$", "RIPEMD 320 bits", "RIPEMD",
                "22d65d5661536cdc75c1fdf5c6de7b41b9f27325ebc61e8557177d705a0ec880151c3a32a00899b8"),
        
        # NTLM/LM
        HashInfo("NTLM", 32, r"^[a-f0-9]{32}$", "Windows NT LAN Manager", "Windows",
                "31d6cfe0d16ae931b73c59d7e0c089c0"),
        HashInfo("LM", 32, r"^[a-f0-9]{32}$", "LAN Manager (legacy)", "Windows",
                "aad3b435b51404eeaad3b435b51404ee"),
        
        # MySQL
        HashInfo("MySQL323", 16, r"^[a-f0-9]{16}$", "MySQL 3.x-4.x", "Database",
                "5d2e19393cc5ef67"),
        HashInfo("MySQL5", 40, r"^\*[A-F0-9]{40}$", "MySQL 5.x+", "Database",
                "*2470C0C06DEE42FD1618BB99005ADCA2EC9D1E19"),
        
        # PostgreSQL
        HashInfo("PostgreSQL MD5", 35, r"^md5[a-f0-9]{32}$", "PostgreSQL MD5", "Database",
                "md5ed6c7796eeab4d5c47eec0e73db5e26d"),
        
        # Bcrypt
        HashInfo("Bcrypt", 60, r"^\$2[aby]?\$\d{2}\$[./A-Za-z0-9]{53}$", 
                "Bcrypt (Blowfish)", "Modern",
                "$2a$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW"),
        
        # Scrypt
        HashInfo("Scrypt", 0, r"^\$s0\$", "Scrypt", "Modern",
                "$s0$e0801$epIxT/h6HbbwHaehFnh/bw==$7H0vsXlY8UxxyW/BWx/9GuY7jEvGjT71GFd6O4SZND0="),
        
        # Argon2
        HashInfo("Argon2", 0, r"^\$argon2(i|d|id)\$", "Argon2 (i, d, id)", "Modern",
                "$argon2id$v=19$m=65536,t=3,p=4$c2FsdA$Y3JhY2tpbmc="),
        
        # PBKDF2
        HashInfo("PBKDF2-SHA256", 0, r"^\$pbkdf2-sha256\$", "PBKDF2 SHA-256", "Modern",
                "$pbkdf2-sha256$29000$9t7be09LyXlPaU3JGQMgZA$kGBL5GfEtIaV6M5ZRWF2"),
        
        # PHPass
        HashInfo("PHPass", 34, r"^\$P\$[a-zA-Z0-9./]{31}$", "PHPass (WordPress, Joomla)", "CMS",
                "$P$984478476IagS59wHZvyQMArzfx58u."),
        
        # Django
        HashInfo("Django PBKDF2", 0, r"^pbkdf2_sha256\$", "Django PBKDF2-SHA256", "Framework",
                "pbkdf2_sha256$10000$salt$hash"),
        
        # Unix/Linux
        HashInfo("DES Crypt", 13, r"^[./0-9A-Za-z]{13}$", "Traditional DES Crypt", "Unix",
                "IvS7aeT4NzQPM"),
        HashInfo("MD5 Crypt", 0, r"^\$1\$[a-zA-Z0-9./]{8}\$[a-zA-Z0-9./]{22}$", 
                "MD5 Crypt ($1$)", "Unix",
                "$1$12345678$jSmBvLhxmNRtIvJSEqXRj1"),
        HashInfo("SHA-256 Crypt", 0, r"^\$5\$", "SHA-256 Crypt ($5$)", "Unix",
                "$5$rounds=5000$salt$hash"),
        HashInfo("SHA-512 Crypt", 0, r"^\$6\$", "SHA-512 Crypt ($6$)", "Unix",
                "$6$rounds=5000$salt$hash"),
        
        # CRC
        HashInfo("CRC32", 8, r"^[a-f0-9]{8}$", "CRC32 Checksum", "Checksum",
                "3d4b8c2e"),
        HashInfo("CRC32B", 8, r"^[a-f0-9]{8}$", "CRC32B Checksum", "Checksum",
                "b4c2d7e1"),
        
        # Adler
        HashInfo("Adler32", 8, r"^[a-f0-9]{8}$", "Adler-32 Checksum", "Checksum",
                "03da0195"),
        
        # Whirlpool
        HashInfo("Whirlpool", 128, r"^[a-f0-9]{128}$", "Whirlpool 512 bits", "Legacy",
                "19fa61d75522a4669b44e39c1d2e1726c530232130d407f89afee0964997f7a73e83be698b288febcf88e3e03c4f0757ea8964e59b63d93708b138cc42a66eb3"),
        
        # Tiger
        HashInfo("Tiger-192", 48, r"^[a-f0-9]{48}$", "Tiger 192 bits", "Legacy",
                "24f0130c63ac933216166e76b1bb925ff373de2d49584e7a"),
        
        # Snefru
        HashInfo("Snefru-256", 64, r"^[a-f0-9]{64}$", "Snefru 256 bits", "Legacy",
                "8617f366566a011837f4fb4ba5bedea2b892f3ed8b894023d16ae344b2be5881"),
    ]
    
    @classmethod
    def get_by_length(cls, length: int) -> List[HashInfo]:
        """Retorna hashes com um tamanho específico."""
        return [h for h in cls.HASH_TYPES if h.length == length]
    
    @classmethod
    def get_by_category(cls, category: str) -> List[HashInfo]:
        """Retorna hashes de uma categoria específica."""
        return [h for h in cls.HASH_TYPES if h.category.lower() == category.lower()]
    
    @classmethod
    def get_all(cls) -> List[HashInfo]:
        """Retorna todos os tipos de hash."""
        return cls.HASH_TYPES


class HashIdentifier:
    """Identificador de tipos de hash."""
    
    def __init__(self):
        self.db = HashDatabase()
    
    def identify(self, hash_value: str) -> HashMatch:
        """Identifica possíveis tipos de um hash."""
        hash_value = hash_value.strip().lower()
        matches = []
        
        for hash_type in self.db.get_all():
            if re.match(hash_type.regex, hash_value, re.IGNORECASE):
                # Verifica comprimento se definido
                if hash_type.length == 0 or len(hash_value) == hash_type.length:
                    matches.append(hash_type)
        
        # Calcula confiança baseada no número de matches
        if len(matches) == 1:
            confidence = 1.0
        elif len(matches) <= 3:
            confidence = 0.7
        else:
            confidence = 0.5
        
        return HashMatch(
            hash_value=hash_value,
            possible_types=matches,
            confidence=confidence
        )
    
    def identify_multiple(self, hashes: List[str]) -> List[HashMatch]:
        """Identifica múltiplos hashes."""
        return [self.identify(h) for h in hashes]


class HashGenerator:
    """Gerador de hashes."""
    
    ALGORITHMS = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha224": hashlib.sha224,
        "sha256": hashlib.sha256,
        "sha384": hashlib.sha384,
        "sha512": hashlib.sha512,
        "sha3_224": hashlib.sha3_224,
        "sha3_256": hashlib.sha3_256,
        "sha3_384": hashlib.sha3_384,
        "sha3_512": hashlib.sha3_512,
        "blake2b": hashlib.blake2b,
        "blake2s": hashlib.blake2s,
    }
    
    @classmethod
    def generate(cls, text: str, algorithm: str) -> str:
        """Gera hash de um texto."""
        algorithm = algorithm.lower().replace("-", "_")
        
        if algorithm not in cls.ALGORITHMS:
            raise ValueError(f"Algoritmo '{algorithm}' não suportado")
        
        hasher = cls.ALGORITHMS[algorithm]()
        hasher.update(text.encode())
        return hasher.hexdigest()
    
    @classmethod
    def generate_all(cls, text: str) -> Dict[str, str]:
        """Gera todos os hashes suportados."""
        result = {}
        for algo in cls.ALGORITHMS:
            try:
                result[algo] = cls.generate(text, algo)
            except:
                pass
        return result
    
    @classmethod
    def hash_file(cls, filepath: str, algorithm: str = "sha256") -> str:
        """Calcula hash de um arquivo."""
        algorithm = algorithm.lower().replace("-", "_")
        
        if algorithm not in cls.ALGORITHMS:
            raise ValueError(f"Algoritmo '{algorithm}' não suportado")
        
        hasher = cls.ALGORITHMS[algorithm]()
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        
        return hasher.hexdigest()


class HashAnalyzer:
    """Analisador de hashes."""
    
    @staticmethod
    def get_entropy(hash_value: str) -> float:
        """Calcula entropia do hash."""
        from collections import Counter
        import math
        
        counter = Counter(hash_value.lower())
        length = len(hash_value)
        
        entropy = 0.0
        for count in counter.values():
            probability = count / length
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    @staticmethod
    def analyze_patterns(hash_value: str) -> Dict:
        """Analisa padrões no hash."""
        analysis = {
            "length": len(hash_value),
            "charset": set(hash_value.lower()),
            "unique_chars": len(set(hash_value.lower())),
            "has_prefix": False,
            "prefix": "",
            "is_uppercase": hash_value.isupper(),
            "is_lowercase": hash_value.islower(),
            "is_mixed": not hash_value.isupper() and not hash_value.islower(),
        }
        
        # Detecta prefixos comuns
        prefixes = ['$1$', '$2a$', '$2b$', '$5$', '$6$', '$P$', '$H$', 
                    '$argon2', '$pbkdf2', 'md5', '*']
        for prefix in prefixes:
            if hash_value.lower().startswith(prefix.lower()):
                analysis["has_prefix"] = True
                analysis["prefix"] = prefix
                break
        
        return analysis


def interactive_menu():
    """Menu interativo do Hash Identifier."""
    identifier = HashIdentifier()
    generator = HashGenerator()
    analyzer = HashAnalyzer()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║          🔐 HASH IDENTIFIER - Olho de Deus                   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔍 Identificar Hash                                     ║
║  [2] 📝 Gerar Hash                                           ║
║  [3] 📁 Hash de Arquivo                                      ║
║  [4] 📊 Analisar Hash                                        ║
║  [5] 📋 Gerar Todos os Hashes                                ║
║  [6] 📚 Listar Tipos de Hash                                 ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Identificar Hash ===")
            hash_value = input("Hash: ").strip()
            
            if not hash_value:
                continue
            
            result = identifier.identify(hash_value)
            
            if result.possible_types:
                print(f"\n🔍 Possíveis tipos (confiança: {result.confidence:.0%}):\n")
                
                for hash_type in result.possible_types:
                    print(f"   📌 {hash_type.name}")
                    print(f"      Categoria: {hash_type.category}")
                    print(f"      Descrição: {hash_type.description}")
                    print(f"      Tamanho: {hash_type.length} caracteres")
                    print()
            else:
                print("\n❌ Tipo de hash não identificado")
                
                # Análise adicional
                analysis = analyzer.analyze_patterns(hash_value)
                print(f"\n📊 Análise:")
                print(f"   Tamanho: {analysis['length']}")
                print(f"   Caracteres únicos: {analysis['unique_chars']}")
        
        elif escolha == '2':
            print("\n=== Gerar Hash ===")
            print(f"Algoritmos: {', '.join(generator.ALGORITHMS.keys())}")
            
            algorithm = input("\nAlgoritmo: ").strip().lower()
            text = input("Texto: ").strip()
            
            if not text:
                continue
            
            try:
                hash_result = generator.generate(text, algorithm)
                print(f"\n✅ {algorithm.upper()}:")
                print(hash_result)
            except ValueError as e:
                print(f"\n❌ Erro: {e}")
        
        elif escolha == '3':
            print("\n=== Hash de Arquivo ===")
            filepath = input("Caminho do arquivo: ").strip()
            
            if not filepath or not os.path.isfile(filepath):
                print("\n❌ Arquivo não encontrado")
                input("\nPressione Enter para continuar...")
                continue
            
            print(f"\nAlgoritmos: {', '.join(generator.ALGORITHMS.keys())}")
            algorithm = input("Algoritmo (padrão: sha256): ").strip() or "sha256"
            
            try:
                hash_result = generator.hash_file(filepath, algorithm)
                print(f"\n✅ {algorithm.upper()}:")
                print(hash_result)
            except Exception as e:
                print(f"\n❌ Erro: {e}")
        
        elif escolha == '4':
            print("\n=== Analisar Hash ===")
            hash_value = input("Hash: ").strip()
            
            if not hash_value:
                continue
            
            # Identificação
            result = identifier.identify(hash_value)
            
            # Análise de padrões
            patterns = analyzer.analyze_patterns(hash_value)
            
            # Entropia
            entropy = analyzer.get_entropy(hash_value)
            
            print("\n📊 Análise Completa:\n")
            print(f"   📏 Tamanho: {patterns['length']} caracteres")
            print(f"   🔤 Caracteres únicos: {patterns['unique_chars']}")
            print(f"   📈 Entropia: {entropy:.2f} bits")
            
            if patterns["has_prefix"]:
                print(f"   🏷️  Prefixo: {patterns['prefix']}")
            
            if patterns["is_uppercase"]:
                print("   🔠 Case: Maiúsculas")
            elif patterns["is_lowercase"]:
                print("   🔡 Case: Minúsculas")
            else:
                print("   🔠🔡 Case: Misto")
            
            if result.possible_types:
                print(f"\n   🔍 Tipos possíveis: {', '.join(h.name for h in result.possible_types)}")
        
        elif escolha == '5':
            print("\n=== Gerar Todos os Hashes ===")
            text = input("Texto: ").strip()
            
            if not text:
                continue
            
            hashes = generator.generate_all(text)
            
            print("\n📋 Hashes gerados:\n")
            for algo, hash_value in hashes.items():
                print(f"   {algo.upper():12}: {hash_value}")
        
        elif escolha == '6':
            print("\n=== Tipos de Hash Suportados ===\n")
            
            # Agrupa por categoria
            categories = {}
            for hash_type in HashDatabase.get_all():
                if hash_type.category not in categories:
                    categories[hash_type.category] = []
                categories[hash_type.category].append(hash_type)
            
            for category, types in categories.items():
                print(f"\n📁 {category}:")
                for t in types:
                    size_info = f"{t.length} chars" if t.length else "variável"
                    print(f"   • {t.name} ({size_info})")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
