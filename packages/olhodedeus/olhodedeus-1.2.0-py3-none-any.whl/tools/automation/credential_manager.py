#!/usr/bin/env python3
"""
Credential Manager - Gerenciador seguro de credenciais
Parte do toolkit Olho de Deus
"""

import os
import sys
import json
import base64
import hashlib
import secrets
import sqlite3
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from getpass import getpass
from pathlib import Path


@dataclass
class Credential:
    """Credencial armazenada."""
    id: int
    name: str
    username: str
    password_hash: str  # Armazenado criptografado
    url: str
    category: str
    notes: str
    created_at: str
    updated_at: str
    
    def to_dict(self, include_password: bool = False) -> Dict:
        result = {
            "id": self.id,
            "name": self.name,
            "username": self.username,
            "url": self.url,
            "category": self.category,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        if include_password:
            result["password"] = self.password_hash
        return result


class SimpleCrypto:
    """Criptografia simples para credenciais."""
    
    @staticmethod
    def derive_key(master_password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """Deriva chave do master password."""
        if salt is None:
            salt = secrets.token_bytes(16)
        
        # PBKDF2-like derivation
        key = hashlib.pbkdf2_hmac(
            'sha256',
            master_password.encode(),
            salt,
            100000
        )
        
        return key, salt
    
    @staticmethod
    def encrypt(data: str, key: bytes) -> str:
        """Criptografa dados (XOR simples - para produção usar AES)."""
        data_bytes = data.encode()
        
        # Extend key to match data length
        extended_key = (key * (len(data_bytes) // len(key) + 1))[:len(data_bytes)]
        
        # XOR encryption
        encrypted = bytes(a ^ b for a, b in zip(data_bytes, extended_key))
        
        return base64.b64encode(encrypted).decode()
    
    @staticmethod
    def decrypt(encrypted_data: str, key: bytes) -> str:
        """Descriptografa dados."""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Extend key to match data length
            extended_key = (key * (len(encrypted_bytes) // len(key) + 1))[:len(encrypted_bytes)]
            
            # XOR decryption
            decrypted = bytes(a ^ b for a, b in zip(encrypted_bytes, extended_key))
            
            return decrypted.decode()
        except Exception:
            return ""


class CredentialStore:
    """Armazenamento de credenciais."""
    
    def __init__(self, db_path: str = "credentials.db"):
        self.db_path = db_path
        self.key: Optional[bytes] = None
        self.salt: Optional[bytes] = None
        self.unlocked = False
        self._init_db()
    
    def _init_db(self):
        """Inicializa banco de dados."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de metadados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Tabela de credenciais
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT,
                password_enc TEXT,
                url TEXT,
                category TEXT DEFAULT 'Geral',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de categorias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Inserir categorias padrão
        default_categories = ['Geral', 'Web', 'SSH', 'API', 'Database', 'Email', 'VPN']
        for cat in default_categories:
            try:
                cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (cat,))
            except:
                pass
        
        conn.commit()
        conn.close()
    
    def setup_master_password(self, master_password: str) -> bool:
        """Configura master password."""
        key, salt = SimpleCrypto.derive_key(master_password)
        
        # Criar verificador
        verifier = SimpleCrypto.encrypt("OLHODEDEUS_VERIFY", key)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)',
                      ('salt', base64.b64encode(salt).decode()))
        cursor.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)',
                      ('verifier', verifier))
        
        conn.commit()
        conn.close()
        
        self.key = key
        self.salt = salt
        self.unlocked = True
        
        return True
    
    def unlock(self, master_password: str) -> bool:
        """Desbloqueia o vault."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM metadata WHERE key = ?', ('salt',))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return False
        
        self.salt = base64.b64decode(row[0])
        self.key, _ = SimpleCrypto.derive_key(master_password, self.salt)
        
        # Verificar
        cursor.execute('SELECT value FROM metadata WHERE key = ?', ('verifier',))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            decrypted = SimpleCrypto.decrypt(row[0], self.key)
            if decrypted == "OLHODEDEUS_VERIFY":
                self.unlocked = True
                return True
        
        self.key = None
        return False
    
    def is_initialized(self) -> bool:
        """Verifica se vault foi inicializado."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM metadata WHERE key = ?', ('salt',))
        row = cursor.fetchone()
        conn.close()
        return row is not None
    
    def add_credential(self, name: str, username: str, password: str,
                       url: str = "", category: str = "Geral", 
                       notes: str = "") -> int:
        """Adiciona credencial."""
        if not self.unlocked:
            raise ValueError("Vault não desbloqueado")
        
        encrypted_password = SimpleCrypto.encrypt(password, self.key)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO credentials (name, username, password_enc, url, category, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, username, encrypted_password, url, category, notes))
        
        cred_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return cred_id
    
    def get_credential(self, cred_id: int) -> Optional[Dict]:
        """Obtém credencial por ID."""
        if not self.unlocked:
            raise ValueError("Vault não desbloqueado")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM credentials WHERE id = ?', (cred_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            password = SimpleCrypto.decrypt(row[3], self.key)
            return {
                "id": row[0],
                "name": row[1],
                "username": row[2],
                "password": password,
                "url": row[4],
                "category": row[5],
                "notes": row[6],
                "created_at": row[7],
                "updated_at": row[8]
            }
        
        return None
    
    def list_credentials(self, category: str = None) -> List[Dict]:
        """Lista credenciais (sem passwords)."""
        if not self.unlocked:
            raise ValueError("Vault não desbloqueado")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute('SELECT id, name, username, url, category, created_at FROM credentials WHERE category = ?', (category,))
        else:
            cursor.execute('SELECT id, name, username, url, category, created_at FROM credentials')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "name": row[1],
                "username": row[2],
                "url": row[3],
                "category": row[4],
                "created_at": row[5]
            }
            for row in rows
        ]
    
    def search_credentials(self, query: str) -> List[Dict]:
        """Busca credenciais."""
        if not self.unlocked:
            raise ValueError("Vault não desbloqueado")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, username, url, category, created_at 
            FROM credentials 
            WHERE name LIKE ? OR username LIKE ? OR url LIKE ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "name": row[1],
                "username": row[2],
                "url": row[3],
                "category": row[4],
                "created_at": row[5]
            }
            for row in rows
        ]
    
    def update_credential(self, cred_id: int, **kwargs) -> bool:
        """Atualiza credencial."""
        if not self.unlocked:
            raise ValueError("Vault não desbloqueado")
        
        updates = []
        values = []
        
        for field in ['name', 'username', 'url', 'category', 'notes']:
            if field in kwargs:
                updates.append(f'{field} = ?')
                values.append(kwargs[field])
        
        if 'password' in kwargs:
            updates.append('password_enc = ?')
            values.append(SimpleCrypto.encrypt(kwargs['password'], self.key))
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(cred_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            UPDATE credentials SET {', '.join(updates)} WHERE id = ?
        ''', values)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_credential(self, cred_id: int) -> bool:
        """Remove credencial."""
        if not self.unlocked:
            raise ValueError("Vault não desbloqueado")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM credentials WHERE id = ?', (cred_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success
    
    def get_categories(self) -> List[str]:
        """Lista categorias."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT name FROM categories ORDER BY name')
        categories = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return categories
    
    def export_to_json(self, include_passwords: bool = False) -> str:
        """Exporta credenciais para JSON."""
        if not self.unlocked:
            raise ValueError("Vault não desbloqueado")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM credentials')
        rows = cursor.fetchall()
        conn.close()
        
        credentials = []
        for row in rows:
            cred = {
                "name": row[1],
                "username": row[2],
                "url": row[4],
                "category": row[5],
                "notes": row[6]
            }
            if include_passwords:
                cred["password"] = SimpleCrypto.decrypt(row[3], self.key)
            credentials.append(cred)
        
        return json.dumps(credentials, indent=2)


class PasswordGenerator:
    """Gerador de senhas seguras."""
    
    LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
    UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    DIGITS = "0123456789"
    SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    @classmethod
    def generate(cls, length: int = 16, 
                 use_upper: bool = True,
                 use_digits: bool = True,
                 use_symbols: bool = True,
                 exclude_ambiguous: bool = False) -> str:
        """Gera senha segura."""
        charset = cls.LOWERCASE
        
        if use_upper:
            charset += cls.UPPERCASE
        if use_digits:
            charset += cls.DIGITS
        if use_symbols:
            charset += cls.SYMBOLS
        
        if exclude_ambiguous:
            charset = charset.translate(str.maketrans('', '', 'l1I0O'))
        
        password = ''.join(secrets.choice(charset) for _ in range(length))
        
        return password
    
    @classmethod
    def generate_passphrase(cls, words: int = 4) -> str:
        """Gera passphrase."""
        wordlist = [
            "correct", "horse", "battery", "staple", "cloud", "river",
            "mountain", "forest", "ocean", "thunder", "crystal", "diamond",
            "phoenix", "dragon", "shadow", "light", "storm", "fire",
            "water", "earth", "wind", "spirit", "cosmic", "stellar"
        ]
        
        return "-".join(secrets.choice(wordlist) for _ in range(words))


def interactive_menu():
    """Menu interativo do Credential Manager."""
    store = CredentialStore()
    
    # Setup inicial ou login
    if not store.is_initialized():
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║        🔐 CREDENTIAL MANAGER - Primeiro Acesso               ║
╚══════════════════════════════════════════════════════════════╝
        """)
        print("Configure uma senha mestra para proteger suas credenciais.")
        print("⚠️  Esta senha NÃO pode ser recuperada se perdida!\n")
        
        while True:
            master = getpass("Senha mestra: ")
            confirm = getpass("Confirme a senha: ")
            
            if master != confirm:
                print("❌ Senhas não coincidem!")
                continue
            
            if len(master) < 8:
                print("❌ Senha deve ter no mínimo 8 caracteres!")
                continue
            
            store.setup_master_password(master)
            print("\n✅ Vault configurado com sucesso!")
            input("Enter para continuar...")
            break
    else:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║            🔐 CREDENTIAL MANAGER - Login                     ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        attempts = 3
        while attempts > 0:
            master = getpass("Senha mestra: ")
            
            if store.unlock(master):
                print("✅ Vault desbloqueado!")
                break
            else:
                attempts -= 1
                print(f"❌ Senha incorreta! ({attempts} tentativas restantes)")
        
        if not store.unlocked:
            print("❌ Muitas tentativas. Saindo...")
            return
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        cred_count = len(store.list_credentials())
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║          🔐 CREDENTIAL MANAGER - Olho de Deus                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Credenciais armazenadas: {cred_count:<5}                            ║
║                                                              ║
║  [1] ➕ Adicionar Credencial                                 ║
║  [2] 📋 Listar Credenciais                                   ║
║  [3] 🔍 Buscar Credencial                                    ║
║  [4] 👁️  Ver Credencial                                       ║
║  [5] ✏️  Editar Credencial                                    ║
║  [6] 🗑️  Remover Credencial                                   ║
║  [7] 🔑 Gerar Senha                                          ║
║  [8] 💾 Exportar (JSON)                                      ║
║                                                              ║
║  [0] Bloquear e Sair                                         ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            store.key = None
            store.unlocked = False
            print("🔒 Vault bloqueado!")
            break
        
        elif escolha == '1':
            print("\n=== Adicionar Credencial ===")
            
            name = input("Nome/Título: ").strip()
            if not name:
                continue
            
            username = input("Usuário: ").strip()
            
            print("\nSenha: [1] Digitar  [2] Gerar automaticamente")
            pwd_choice = input("Opção: ").strip()
            
            if pwd_choice == '2':
                length = int(input("Tamanho (16): ").strip() or "16")
                password = PasswordGenerator.generate(length)
                print(f"   Senha gerada: {password}")
            else:
                password = getpass("Senha: ")
            
            url = input("URL (opcional): ").strip()
            
            categories = store.get_categories()
            print(f"\nCategorias: {', '.join(categories)}")
            category = input("Categoria: ").strip() or "Geral"
            
            notes = input("Notas (opcional): ").strip()
            
            cred_id = store.add_credential(
                name=name,
                username=username,
                password=password,
                url=url,
                category=category,
                notes=notes
            )
            
            print(f"\n✅ Credencial #{cred_id} adicionada!")
        
        elif escolha == '2':
            print("\n=== Credenciais ===")
            
            categories = store.get_categories()
            print(f"Filtrar por categoria? ({', '.join(categories)})")
            cat_filter = input("Categoria (Enter para todas): ").strip()
            
            creds = store.list_credentials(cat_filter if cat_filter else None)
            
            if not creds:
                print("\nNenhuma credencial encontrada.")
            else:
                print(f"\n{'ID':<5} {'Nome':<20} {'Usuário':<20} {'Categoria':<10}")
                print("-" * 60)
                for c in creds:
                    print(f"{c['id']:<5} {c['name'][:19]:<20} {c['username'][:19]:<20} {c['category']:<10}")
        
        elif escolha == '3':
            print("\n=== Buscar Credencial ===")
            query = input("Buscar: ").strip()
            
            if not query:
                continue
            
            results = store.search_credentials(query)
            
            if not results:
                print("\nNenhum resultado encontrado.")
            else:
                print(f"\n{len(results)} resultado(s):\n")
                for c in results:
                    print(f"   [{c['id']}] {c['name']} ({c['username']})")
        
        elif escolha == '4':
            print("\n=== Ver Credencial ===")
            try:
                cred_id = int(input("ID da credencial: ").strip())
                cred = store.get_credential(cred_id)
                
                if cred:
                    print(f"\n{'='*40}")
                    print(f"📝 {cred['name']}")
                    print(f"{'='*40}")
                    print(f"   Usuário: {cred['username']}")
                    print(f"   Senha: {'*' * 8} (pressione 's' para revelar)")
                    print(f"   URL: {cred['url'] or 'N/A'}")
                    print(f"   Categoria: {cred['category']}")
                    if cred['notes']:
                        print(f"   Notas: {cred['notes']}")
                    
                    show = input("\nRevelar senha? (s/n): ").lower()
                    if show == 's':
                        print(f"\n   🔑 Senha: {cred['password']}")
                else:
                    print("❌ Credencial não encontrada")
            except ValueError:
                print("❌ ID inválido")
        
        elif escolha == '5':
            print("\n=== Editar Credencial ===")
            try:
                cred_id = int(input("ID da credencial: ").strip())
                cred = store.get_credential(cred_id)
                
                if cred:
                    print(f"\nEditando: {cred['name']}")
                    print("(Enter para manter valor atual)\n")
                    
                    name = input(f"Nome [{cred['name']}]: ").strip()
                    username = input(f"Usuário [{cred['username']}]: ").strip()
                    
                    change_pwd = input("Alterar senha? (s/n): ").lower()
                    password = None
                    if change_pwd == 's':
                        password = getpass("Nova senha: ")
                    
                    url = input(f"URL [{cred['url']}]: ").strip()
                    category = input(f"Categoria [{cred['category']}]: ").strip()
                    
                    updates = {}
                    if name:
                        updates['name'] = name
                    if username:
                        updates['username'] = username
                    if password:
                        updates['password'] = password
                    if url:
                        updates['url'] = url
                    if category:
                        updates['category'] = category
                    
                    if updates:
                        store.update_credential(cred_id, **updates)
                        print("✅ Credencial atualizada!")
                    else:
                        print("Nenhuma alteração feita.")
                else:
                    print("❌ Credencial não encontrada")
            except ValueError:
                print("❌ ID inválido")
        
        elif escolha == '6':
            print("\n=== Remover Credencial ===")
            try:
                cred_id = int(input("ID da credencial: ").strip())
                cred = store.get_credential(cred_id)
                
                if cred:
                    confirm = input(f"Remover '{cred['name']}'? (s/n): ").lower()
                    if confirm == 's':
                        store.delete_credential(cred_id)
                        print("✅ Credencial removida!")
                else:
                    print("❌ Credencial não encontrada")
            except ValueError:
                print("❌ ID inválido")
        
        elif escolha == '7':
            print("\n=== Gerador de Senhas ===")
            
            length = int(input("Tamanho (16): ").strip() or "16")
            use_upper = input("Maiúsculas? (S/n): ").lower() != 'n'
            use_digits = input("Números? (S/n): ").lower() != 'n'
            use_symbols = input("Símbolos? (S/n): ").lower() != 'n'
            
            print("\n📋 Senhas geradas:")
            for i in range(5):
                pwd = PasswordGenerator.generate(length, use_upper, use_digits, use_symbols)
                print(f"   {i+1}. {pwd}")
            
            print("\n🔤 Passphrases:")
            for i in range(3):
                phrase = PasswordGenerator.generate_passphrase(4)
                print(f"   {i+1}. {phrase}")
        
        elif escolha == '8':
            print("\n=== Exportar Credenciais ===")
            print("⚠️  ATENÇÃO: Exportar senhas em texto plano é um risco de segurança!")
            
            include_pwd = input("Incluir senhas? (s/n): ").lower() == 's'
            
            json_data = store.export_to_json(include_pwd)
            
            filename = f"credentials_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w') as f:
                f.write(json_data)
            
            print(f"✅ Exportado para {filename}")
            
            if include_pwd:
                print("⚠️  Arquivo contém senhas! Guarde com segurança!")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
