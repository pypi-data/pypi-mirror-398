#!/usr/bin/env python3
"""
Ransomware Database - Identificação e informações sobre ransomware
Parte do toolkit Olho de Deus
"""

import os
import sys
import re
import json
import hashlib
import sqlite3
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class RansomwareInfo:
    """Informações sobre ransomware."""
    name: str
    aliases: List[str]
    extensions: List[str]
    ransom_note_names: List[str]
    encryption_type: str
    decryptor_available: bool
    decryptor_url: Optional[str]
    first_seen: str
    description: str
    iocs: Dict[str, List[str]]
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "aliases": self.aliases,
            "extensions": self.extensions,
            "ransom_note_names": self.ransom_note_names,
            "encryption_type": self.encryption_type,
            "decryptor_available": self.decryptor_available,
            "decryptor_url": self.decryptor_url,
            "first_seen": self.first_seen,
            "description": self.description,
            "iocs": self.iocs
        }


class RansomwareDatabase:
    """Database de ransomwares conhecidos."""
    
    # Dados de ransomwares conhecidos (amostra)
    KNOWN_RANSOMWARE = {
        "wannacry": RansomwareInfo(
            name="WannaCry",
            aliases=["WCry", "WanaCrypt0r", "Wanna Decryptor"],
            extensions=[".WNCRY", ".WCRY", ".WNCRYT"],
            ransom_note_names=["@Please_Read_Me@.txt", "@WanaDecryptor@.exe"],
            encryption_type="AES-128 + RSA-2048",
            decryptor_available=True,
            decryptor_url="https://github.com/gentilkiwi/wanakiwi",
            first_seen="2017-05",
            description="Ransomware que explorou EternalBlue (MS17-010). Afetou mais de 200k sistemas.",
            iocs={
                "md5": ["84c82835a5d21bbcf75a61706d8ab549"],
                "domains": ["iuqerfsodp9ifjaposdfjhgosurijfaewrwergwea.com"],
                "mutex": ["Global\\MsWinZonesCacheCounterMutexA"]
            }
        ),
        "lockbit": RansomwareInfo(
            name="LockBit",
            aliases=["ABCD", "LockBit 2.0", "LockBit 3.0"],
            extensions=[".lockbit", ".abcd", ".LockBit"],
            ransom_note_names=["Restore-My-Files.txt", "[id].README.txt"],
            encryption_type="AES + RSA-2048",
            decryptor_available=False,
            decryptor_url=None,
            first_seen="2019-09",
            description="RaaS (Ransomware as a Service) muito ativo. Automatiza propagação lateral.",
            iocs={
                "md5": [],
                "c2": [],
                "registry": ["HKCU\\Software\\LockBit"]
            }
        ),
        "revil": RansomwareInfo(
            name="REvil/Sodinokibi",
            aliases=["Sodinokibi", "Sodin"],
            extensions=[".random_extension"],
            ransom_note_names=["[ext]-readme.txt", "[ext].txt"],
            encryption_type="Salsa20 + Curve25519",
            decryptor_available=True,
            decryptor_url="https://www.nomoreransom.org",
            first_seen="2019-04",
            description="RaaS sofisticado. Ganhou notoriedade com ataques a grandes empresas.",
            iocs={
                "mutex": ["Global\\{random_guid}"],
                "registry": ["HKLM\\SOFTWARE\\BlackLivesMatter"]
            }
        ),
        "conti": RansomwareInfo(
            name="Conti",
            aliases=[],
            extensions=[".CONTI", ".EXTEN"],
            ransom_note_names=["readme.txt", "CONTI_README.txt"],
            encryption_type="AES-256 + RSA-4096",
            decryptor_available=False,
            decryptor_url=None,
            first_seen="2020-05",
            description="Operação RaaS que vazou código fonte. Multithreaded para velocidade.",
            iocs={
                "mutex": ["CONTI"],
                "processes": ["conti.exe"]
            }
        ),
        "ryuk": RansomwareInfo(
            name="Ryuk",
            aliases=[],
            extensions=[".RYK", ".RYUK"],
            ransom_note_names=["RyukReadMe.txt", "RyukReadMe.html"],
            encryption_type="AES-256 + RSA-4096",
            decryptor_available=False,
            decryptor_url=None,
            first_seen="2018-08",
            description="Ransomware direcionado a grandes organizações. Alto valor de resgate.",
            iocs={
                "mutex": ["RyukMutex"],
                "processes": ["ryuk.exe"]
            }
        ),
        "blackcat": RansomwareInfo(
            name="BlackCat/ALPHV",
            aliases=["ALPHV", "Noberus"],
            extensions=[".random"],
            ransom_note_names=["RECOVER-[ext]-FILES.txt"],
            encryption_type="AES + ChaCha20",
            decryptor_available=False,
            decryptor_url=None,
            first_seen="2021-11",
            description="Primeiro ransomware escrito em Rust. Cross-platform (Win/Linux).",
            iocs={
                "behaviors": ["Self-deletes after execution", "Disables recovery options"]
            }
        ),
        "hive": RansomwareInfo(
            name="Hive",
            aliases=[],
            extensions=[".hive", ".key.[hash]"],
            ransom_note_names=["HOW_TO_DECRYPT.txt"],
            encryption_type="Custom + RSA-2048",
            decryptor_available=True,
            decryptor_url="https://www.cisa.gov",
            first_seen="2021-06",
            description="RaaS que foi disrupted pelo FBI em 2023. Decryptor disponível.",
            iocs={
                "c2": [],
                "registry": ["HKCU\\Software\\Hive"]
            }
        ),
        "stop_djvu": RansomwareInfo(
            name="STOP/Djvu",
            aliases=["STOP", "Djvu", "DJVU"],
            extensions=[".stop", ".djvu", ".rumba", ".radman", ".gero", ".noos"],
            ransom_note_names=["_readme.txt", "_openme.txt"],
            encryption_type="Salsa20 + RSA-1024",
            decryptor_available=True,
            decryptor_url="https://www.emsisoft.com/ransomware-decryption-tools/stop-djvu",
            first_seen="2018-12",
            description="Um dos mais prolíficos. Ataca consumidores via software pirata.",
            iocs={
                "processes": ["script.exe", "updatewin.exe"],
                "folders": ["%LocalAppData%\\{random}"]
            }
        ),
        "maze": RansomwareInfo(
            name="Maze",
            aliases=["ChaCha"],
            extensions=[".maze", ".random"],
            ransom_note_names=["DECRYPT-FILES.txt"],
            encryption_type="ChaCha + RSA-2048",
            decryptor_available=False,
            decryptor_url=None,
            first_seen="2019-05",
            description="Pioneiro no modelo de double extortion. Encerrou operações em 2020.",
            iocs={
                "mutex": ["Global\\{GUID}"]
            }
        ),
        "gandcrab": RansomwareInfo(
            name="GandCrab",
            aliases=["Crab"],
            extensions=[".GDCB", ".CRAB", ".KRAB", ".v5+random"],
            ransom_note_names=["GDCB-DECRYPT.txt", "KRAB-DECRYPT.txt"],
            encryption_type="AES-256 + RSA-2048",
            decryptor_available=True,
            decryptor_url="https://www.bitdefender.com/gandcrab-ransomware-decryption",
            first_seen="2018-01",
            description="RaaS muito popular que encerrou em 2019. Múltiplos decryptors.",
            iocs={
                "mutex": ["Global\\pc_group"],
                "registry": ["HKCU\\Software\\keys_data"]
            }
        ),
    }
    
    # Extensões conhecidas de ransomware
    RANSOM_EXTENSIONS = {
        ".encrypted", ".enc", ".locked", ".crypt", ".crypto",
        ".locky", ".cerber", ".zzzzz", ".aaa", ".abc",
        ".ecc", ".ezz", ".exx", ".xyz", ".zzz",
        ".micro", ".mp3", ".wcry", ".wncry", ".wnry",
        ".vvv", ".ccc", ".xxx", ".ttt", ".xxx",
        ".legion", ".1btc", ".hacked", ".pay", ".paymst",
        ".crypted", ".kraken", ".darkness", ".nochance",
        ".oor", ".bleep", ".coverton", ".breaking_bad",
    }
    
    # Nomes comuns de ransom notes
    RANSOM_NOTES = {
        "readme.txt", "_readme.txt", "decrypt.txt",
        "how_to_decrypt.txt", "how-to-decrypt.txt",
        "restore_files.txt", "restore-files.txt",
        "read_me.txt", "decrypt_instruction.txt",
        "decrypt_instructions.txt", "help_decrypt.txt",
        "!!!readme!!!.txt", "@readme@.txt", "read_it.txt",
    }
    
    def __init__(self, db_path: str = "ransomware.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializa database local."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ransomware (
                name TEXT PRIMARY KEY,
                data TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ransomware_name TEXT,
                file_path TEXT,
                indicator_type TEXT,
                indicator_value TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def identify_by_extension(self, extension: str) -> List[RansomwareInfo]:
        """Identifica ransomware pela extensão."""
        results = []
        ext = extension.lower() if extension.startswith('.') else f".{extension.lower()}"
        
        for name, info in self.KNOWN_RANSOMWARE.items():
            for ransom_ext in info.extensions:
                if ext == ransom_ext.lower() or ext in ransom_ext.lower():
                    results.append(info)
                    break
        
        return results
    
    def identify_by_note(self, note_name: str) -> List[RansomwareInfo]:
        """Identifica ransomware pelo nome da ransom note."""
        results = []
        note = note_name.lower()
        
        for name, info in self.KNOWN_RANSOMWARE.items():
            for ransom_note in info.ransom_note_names:
                if note in ransom_note.lower() or ransom_note.lower() in note:
                    results.append(info)
                    break
        
        return results
    
    def search(self, query: str) -> List[RansomwareInfo]:
        """Busca ransomware por nome ou alias."""
        results = []
        query = query.lower()
        
        for name, info in self.KNOWN_RANSOMWARE.items():
            if query in name.lower() or query in info.name.lower():
                results.append(info)
            elif any(query in alias.lower() for alias in info.aliases):
                results.append(info)
        
        return results
    
    def get_all(self) -> List[RansomwareInfo]:
        """Retorna todos os ransomwares conhecidos."""
        return list(self.KNOWN_RANSOMWARE.values())
    
    def get_decryptable(self) -> List[RansomwareInfo]:
        """Retorna ransomwares com decryptor disponível."""
        return [info for info in self.KNOWN_RANSOMWARE.values() 
                if info.decryptor_available]
    
    def get_info(self, name: str) -> Optional[RansomwareInfo]:
        """Retorna informações de um ransomware específico."""
        return self.KNOWN_RANSOMWARE.get(name.lower())


class RansomwareDetector:
    """Detector de indicadores de ransomware."""
    
    def __init__(self):
        self.db = RansomwareDatabase()
    
    def scan_directory(self, path: str) -> Dict:
        """Escaneia diretório por indicadores de ransomware."""
        if not os.path.exists(path):
            return {"error": "Diretório não encontrado"}
        
        results = {
            "path": path,
            "suspicious_files": [],
            "ransom_notes": [],
            "encrypted_files": 0,
            "potential_ransomware": [],
        }
        
        try:
            for root, dirs, files in os.walk(path):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    
                    # Verificar extensão
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in self.db.RANSOM_EXTENSIONS:
                        results["encrypted_files"] += 1
                        results["suspicious_files"].append({
                            "path": file_path,
                            "extension": ext
                        })
                        
                        # Tentar identificar ransomware
                        matches = self.db.identify_by_extension(ext)
                        for match in matches:
                            if match.name not in results["potential_ransomware"]:
                                results["potential_ransomware"].append({
                                    "name": match.name,
                                    "decryptor": match.decryptor_available,
                                    "url": match.decryptor_url
                                })
                    
                    # Verificar ransom notes
                    if filename.lower() in [n.lower() for n in self.db.RANSOM_NOTES]:
                        results["ransom_notes"].append(file_path)
                        
                        # Tentar identificar
                        matches = self.db.identify_by_note(filename)
                        for match in matches:
                            if match.name not in [p["name"] for p in results["potential_ransomware"]]:
                                results["potential_ransomware"].append({
                                    "name": match.name,
                                    "decryptor": match.decryptor_available,
                                    "url": match.decryptor_url
                                })
        except PermissionError:
            pass
        
        return results
    
    def analyze_file(self, file_path: str) -> Dict:
        """Analisa um arquivo específico."""
        if not os.path.exists(file_path):
            return {"error": "Arquivo não encontrado"}
        
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        
        result = {
            "file": file_path,
            "extension": ext,
            "is_suspicious_extension": ext in self.db.RANSOM_EXTENSIONS,
            "is_ransom_note": filename.lower() in [n.lower() for n in self.db.RANSOM_NOTES],
            "matches": []
        }
        
        # Identificar por extensão
        if ext:
            matches = self.db.identify_by_extension(ext)
            for match in matches:
                result["matches"].append(match.to_dict())
        
        # Se for ransom note, tentar ler e identificar
        if result["is_ransom_note"]:
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read(1000)
                    result["note_preview"] = content[:500]
            except:
                pass
        
        return result


def interactive_menu():
    """Menu interativo do Ransomware Database."""
    db = RansomwareDatabase()
    detector = RansomwareDetector()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║           🔐 RANSOMWARE DATABASE - Olho de Deus              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔍 Buscar Ransomware                                    ║
║  [2] 📋 Listar Ransomwares Conhecidos                        ║
║  [3] 🔓 Ransomwares com Decryptor                            ║
║  [4] 📁 Identificar por Extensão                             ║
║  [5] 📄 Identificar por Ransom Note                          ║
║  [6] 🔎 Escanear Diretório                                   ║
║  [7] 📊 Info Detalhada                                       ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Buscar Ransomware ===")
            query = input("Nome ou alias: ").strip()
            
            if not query:
                continue
            
            results = db.search(query)
            
            if results:
                print(f"\n🔍 {len(results)} resultado(s):\n")
                for info in results:
                    status = "🔓 DECRYPTOR" if info.decryptor_available else "🔒 SEM DECRYPTOR"
                    print(f"   {info.name} ({status})")
                    print(f"      Aliases: {', '.join(info.aliases) if info.aliases else 'Nenhum'}")
                    print(f"      Extensões: {', '.join(info.extensions)}")
                    print(f"      First seen: {info.first_seen}")
                    print()
            else:
                print("\n❌ Nenhum resultado encontrado")
        
        elif escolha == '2':
            print("\n=== Ransomwares Conhecidos ===\n")
            
            for info in db.get_all():
                status = "🔓" if info.decryptor_available else "🔒"
                print(f"   {status} {info.name}")
                print(f"      {info.description[:60]}...")
                print()
        
        elif escolha == '3':
            print("\n=== Ransomwares com Decryptor ===\n")
            
            decryptable = db.get_decryptable()
            
            if decryptable:
                for info in decryptable:
                    print(f"   🔓 {info.name}")
                    print(f"      Extensões: {', '.join(info.extensions)}")
                    print(f"      URL: {info.decryptor_url or 'N/A'}")
                    print()
                
                print(f"\n📊 Total: {len(decryptable)} ransomwares com decryptor disponível")
            else:
                print("❌ Nenhum decryptor conhecido no momento")
        
        elif escolha == '4':
            print("\n=== Identificar por Extensão ===")
            ext = input("Extensão (ex: .lockbit, .wcry): ").strip()
            
            if not ext:
                continue
            
            results = db.identify_by_extension(ext)
            
            if results:
                print(f"\n🔍 Possíveis ransomwares:\n")
                for info in results:
                    status = "🔓 DECRYPTOR DISPONÍVEL" if info.decryptor_available else "🔒 SEM DECRYPTOR"
                    print(f"   {info.name}")
                    print(f"      {status}")
                    print(f"      Criptografia: {info.encryption_type}")
                    if info.decryptor_url:
                        print(f"      URL: {info.decryptor_url}")
                    print()
            else:
                print(f"\n❌ Extensão '{ext}' não identificada como ransomware conhecido")
                
                if ext.lower() in db.RANSOM_EXTENSIONS:
                    print("⚠️  Mas é uma extensão suspeita de ransomware!")
        
        elif escolha == '5':
            print("\n=== Identificar por Ransom Note ===")
            note = input("Nome do arquivo (ex: readme.txt): ").strip()
            
            if not note:
                continue
            
            results = db.identify_by_note(note)
            
            if results:
                print(f"\n🔍 Possíveis ransomwares:\n")
                for info in results:
                    status = "🔓" if info.decryptor_available else "🔒"
                    print(f"   {status} {info.name}")
                    print(f"      Ransom notes: {', '.join(info.ransom_note_names)}")
                    print()
            else:
                print(f"\n❌ Ransom note '{note}' não identificada")
                
                if note.lower() in [n.lower() for n in db.RANSOM_NOTES]:
                    print("⚠️  Mas é um nome comum de ransom note!")
        
        elif escolha == '6':
            print("\n=== Escanear Diretório ===")
            path = input("Caminho do diretório: ").strip()
            
            if not path or not os.path.exists(path):
                print("❌ Diretório não encontrado")
                input("Enter para continuar...")
                continue
            
            print(f"\nEscaneando {path}...")
            result = detector.scan_directory(path)
            
            if "error" in result:
                print(f"❌ {result['error']}")
            else:
                print(f"\n📊 RESULTADO DO SCAN:")
                print(f"   Arquivos criptografados: {result['encrypted_files']}")
                print(f"   Ransom notes: {len(result['ransom_notes'])}")
                
                if result['ransom_notes']:
                    print(f"\n   📄 Ransom Notes encontradas:")
                    for note in result['ransom_notes'][:5]:
                        print(f"      {note}")
                
                if result['potential_ransomware']:
                    print(f"\n   🔐 Possível(is) ransomware(s):")
                    for ransm in result['potential_ransomware']:
                        status = "🔓" if ransm['decryptor'] else "🔒"
                        print(f"      {status} {ransm['name']}")
                        if ransm['url']:
                            print(f"         Decryptor: {ransm['url']}")
                
                if result['suspicious_files']:
                    print(f"\n   📁 Primeiros arquivos suspeitos:")
                    for sf in result['suspicious_files'][:5]:
                        print(f"      {sf['path']}")
        
        elif escolha == '7':
            print("\n=== Informação Detalhada ===")
            name = input("Nome do ransomware: ").strip()
            
            if not name:
                continue
            
            info = db.get_info(name)
            
            if info:
                print(f"\n{'='*50}")
                print(f"🔐 {info.name}")
                print(f"{'='*50}")
                print(f"\n📋 Aliases: {', '.join(info.aliases) if info.aliases else 'Nenhum'}")
                print(f"📅 Primeiro avistamento: {info.first_seen}")
                print(f"🔒 Criptografia: {info.encryption_type}")
                print(f"\n📝 Descrição:")
                print(f"   {info.description}")
                print(f"\n📁 Extensões: {', '.join(info.extensions)}")
                print(f"📄 Ransom notes: {', '.join(info.ransom_note_names)}")
                
                if info.decryptor_available:
                    print(f"\n🔓 DECRYPTOR DISPONÍVEL!")
                    print(f"   URL: {info.decryptor_url}")
                else:
                    print(f"\n🔒 Sem decryptor público conhecido")
                
                if info.iocs:
                    print(f"\n🔍 IOCs conhecidos:")
                    for ioc_type, values in info.iocs.items():
                        if values:
                            print(f"   {ioc_type}: {', '.join(values[:3])}")
            else:
                # Tentar busca
                results = db.search(name)
                if results:
                    print(f"\n❌ '{name}' não encontrado. Você quis dizer:")
                    for r in results[:3]:
                        print(f"   - {r.name}")
                else:
                    print(f"\n❌ Ransomware '{name}' não encontrado na base de dados")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
