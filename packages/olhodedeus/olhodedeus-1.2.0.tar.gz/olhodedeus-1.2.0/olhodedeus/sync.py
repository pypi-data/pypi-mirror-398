"""
Olho de Deus - Sincronização de Auth via GitHub
================================================

Sincroniza autenticação entre múltiplos PCs usando GitHub Gist privado.
Assim você pode usar a ferramenta em qualquer lugar com a mesma conta.
"""

import os
import sys
import json
import base64
import hashlib
import requests
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Paths
BASE_PATH = Path(__file__).parent.parent
CONFIG_PATH = BASE_PATH / "config"
AUTH_FILE = CONFIG_PATH / "auth.json"
SYNC_CONFIG_FILE = CONFIG_PATH / "sync_config.json"


class GitHubSync:
    """
    Sincroniza autenticação via GitHub Gist privado.
    
    Os dados são criptografados antes de enviar ao GitHub,
    então nem o GitHub pode ver suas credenciais.
    
    Uso:
        sync = GitHubSync()
        sync.setup("seu_github_token", "sua_senha_mestra")
        
        # Em outro PC
        sync.pull()  # Baixa e descriptografa auth
        
        # Após mudanças
        sync.push()  # Envia auth atualizado
    """
    
    GIST_FILENAME = "olhodedeus_auth.encrypted"
    
    def __init__(self):
        self.config = self._load_sync_config()
        self._fernet = None
    
    # === Configuração ===
    
    def _load_sync_config(self) -> Dict:
        """Carrega config de sincronização."""
        if SYNC_CONFIG_FILE.exists():
            with open(SYNC_CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_sync_config(self):
        """Salva config de sincronização."""
        CONFIG_PATH.mkdir(parents=True, exist_ok=True)
        with open(SYNC_CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _derive_key(self, master_password: str, salt: bytes = None) -> tuple:
        """Deriva chave de criptografia da senha mestra."""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        return key, salt
    
    def _get_fernet(self, master_password: str = None) -> Fernet:
        """Obtém instância Fernet para criptografia."""
        if self._fernet:
            return self._fernet
        
        if not master_password:
            raise ValueError("Senha mestra necessária!")
        
        salt = self.config.get("salt")
        if salt:
            salt = base64.b64decode(salt)
            key, _ = self._derive_key(master_password, salt)
        else:
            key, salt = self._derive_key(master_password)
            self.config["salt"] = base64.b64encode(salt).decode()
            self._save_sync_config()
        
        self._fernet = Fernet(key)
        return self._fernet
    
    # === Setup ===
    
    def is_configured(self) -> bool:
        """Verifica se sync está configurado."""
        return bool(self.config.get("github_token") and self.config.get("gist_id"))
    
    def setup(self, github_token: str, master_password: str) -> bool:
        """
        Configura sincronização.
        
        Args:
            github_token: Token pessoal do GitHub (com permissão de gist)
            master_password: Senha mestra para criptografia
            
        Returns:
            True se configurado com sucesso
        """
        # Valida token
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        r = requests.get("https://api.github.com/user", headers=headers)
        if r.status_code != 200:
            print("❌ Token do GitHub inválido!")
            return False
        
        user = r.json()
        print(f"✅ Autenticado como: {user.get('login')}")
        
        # Salva token (ofuscado)
        self.config["github_token"] = self._obfuscate_token(github_token)
        self.config["github_user"] = user.get("login")
        
        # Inicializa criptografia
        self._get_fernet(master_password)
        
        # Verifica se já existe gist
        gist_id = self._find_existing_gist(github_token)
        
        if gist_id:
            print(f"✅ Gist existente encontrado: {gist_id[:8]}...")
            self.config["gist_id"] = gist_id
        else:
            # Cria novo gist
            gist_id = self._create_gist(github_token)
            if gist_id:
                print(f"✅ Novo Gist criado: {gist_id[:8]}...")
                self.config["gist_id"] = gist_id
            else:
                print("❌ Erro ao criar Gist!")
                return False
        
        self._save_sync_config()
        
        # Push inicial
        if AUTH_FILE.exists():
            self.push(master_password)
        
        return True
    
    def _obfuscate_token(self, token: str) -> str:
        """Ofusca token para não ficar em texto plano."""
        # Simples XOR com chave fixa + base64
        key = b"olhodedeus2025!@#"
        obfuscated = bytes([token.encode()[i] ^ key[i % len(key)] for i in range(len(token))])
        return base64.b64encode(obfuscated).decode()
    
    def _deobfuscate_token(self, obfuscated: str) -> str:
        """Deofusca token."""
        key = b"olhodedeus2025!@#"
        decoded = base64.b64decode(obfuscated)
        original = bytes([decoded[i] ^ key[i % len(key)] for i in range(len(decoded))])
        return original.decode()
    
    def _get_token(self) -> str:
        """Obtém token do GitHub."""
        obfuscated = self.config.get("github_token", "")
        if not obfuscated:
            raise ValueError("Token não configurado!")
        return self._deobfuscate_token(obfuscated)
    
    def _find_existing_gist(self, token: str) -> Optional[str]:
        """Procura gist existente."""
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        r = requests.get("https://api.github.com/gists", headers=headers)
        if r.status_code != 200:
            return None
        
        for gist in r.json():
            if self.GIST_FILENAME in gist.get("files", {}):
                return gist["id"]
        
        return None
    
    def _create_gist(self, token: str) -> Optional[str]:
        """Cria novo gist privado."""
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "description": "Olho de Deus - Auth Sync (encrypted)",
            "public": False,
            "files": {
                self.GIST_FILENAME: {
                    "content": "# Encrypted auth data"
                }
            }
        }
        
        r = requests.post("https://api.github.com/gists", headers=headers, json=data)
        if r.status_code == 201:
            return r.json()["id"]
        return None
    
    # === Sync ===
    
    def push(self, master_password: str = None) -> bool:
        """
        Envia auth local para GitHub.
        
        Args:
            master_password: Senha mestra (se não fornecida, usa cache)
        """
        if not self.is_configured():
            print("❌ Sync não configurado! Use: olhodedeus sync --setup")
            return False
        
        if not AUTH_FILE.exists():
            print("❌ Arquivo auth.json não encontrado!")
            return False
        
        try:
            token = self._get_token()
            fernet = self._get_fernet(master_password)
            
            # Lê e criptografa auth
            with open(AUTH_FILE, 'r') as f:
                auth_data = f.read()
            
            encrypted = fernet.encrypt(auth_data.encode())
            
            # Adiciona metadados
            payload = {
                "data": encrypted.decode(),
                "timestamp": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # Atualiza gist
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {
                "files": {
                    self.GIST_FILENAME: {
                        "content": json.dumps(payload)
                    }
                }
            }
            
            gist_id = self.config["gist_id"]
            r = requests.patch(f"https://api.github.com/gists/{gist_id}", headers=headers, json=data)
            
            if r.status_code == 200:
                print("✅ Auth sincronizado com GitHub!")
                self.config["last_push"] = datetime.now().isoformat()
                self._save_sync_config()
                return True
            else:
                print(f"❌ Erro ao sincronizar: {r.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
    
    def pull(self, master_password: str = None) -> bool:
        """
        Baixa auth do GitHub.
        
        Args:
            master_password: Senha mestra para descriptografar
        """
        if not self.is_configured():
            print("❌ Sync não configurado! Use: olhodedeus sync --setup")
            return False
        
        try:
            token = self._get_token()
            fernet = self._get_fernet(master_password)
            
            # Busca gist
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            gist_id = self.config["gist_id"]
            r = requests.get(f"https://api.github.com/gists/{gist_id}", headers=headers)
            
            if r.status_code != 200:
                print(f"❌ Erro ao buscar Gist: {r.status_code}")
                return False
            
            gist = r.json()
            content = gist["files"][self.GIST_FILENAME]["content"]
            
            # Parse e descriptografa
            payload = json.loads(content)
            encrypted = payload["data"].encode()
            
            decrypted = fernet.decrypt(encrypted).decode()
            
            # Salva localmente
            CONFIG_PATH.mkdir(parents=True, exist_ok=True)
            with open(AUTH_FILE, 'w') as f:
                f.write(decrypted)
            
            print("✅ Auth baixado do GitHub!")
            print(f"   Última atualização: {payload.get('timestamp', 'desconhecido')}")
            self.config["last_pull"] = datetime.now().isoformat()
            self._save_sync_config()
            return True
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
    
    def status(self):
        """Mostra status da sincronização."""
        print("\n" + "=" * 50)
        print("  📡 STATUS DE SINCRONIZAÇÃO")
        print("=" * 50)
        
        if not self.is_configured():
            print("\n  ⚠️  Não configurado")
            print("  Use: olhodedeus sync --setup")
        else:
            print(f"\n  GitHub User: {self.config.get('github_user', '?')}")
            print(f"  Gist ID: {self.config.get('gist_id', '?')[:12]}...")
            print(f"  Último Push: {self.config.get('last_push', 'nunca')}")
            print(f"  Último Pull: {self.config.get('last_pull', 'nunca')}")
        
        print("\n" + "=" * 50)


# === CLI ===

def interactive_setup():
    """Setup interativo."""
    print("\n" + "=" * 60)
    print("  🔄 CONFIGURAÇÃO DE SINCRONIZAÇÃO")
    print("=" * 60)
    
    print("""
Para sincronizar sua autenticação entre PCs, você precisa:

1. Um token do GitHub com permissão de 'gist'
   Crie em: https://github.com/settings/tokens/new
   Marque apenas: ☑️ gist

2. Uma senha mestra (para criptografar os dados)
   Essa senha será usada em todos os PCs
    """)
    
    token = input("GitHub Token: ").strip()
    if not token:
        print("❌ Token obrigatório!")
        return
    
    import getpass
    try:
        password = getpass.getpass("Senha Mestra: ")
        password2 = getpass.getpass("Confirme Senha: ")
    except:
        password = input("Senha Mestra: ").strip()
        password2 = input("Confirme Senha: ").strip()
    
    if password != password2:
        print("❌ Senhas não conferem!")
        return
    
    if len(password) < 8:
        print("❌ Senha mestra deve ter pelo menos 8 caracteres!")
        return
    
    sync = GitHubSync()
    if sync.setup(token, password):
        print("\n✅ Sincronização configurada com sucesso!")
        print("\nAgora você pode usar em outro PC:")
        print("  1. pip install olhodedeus")
        print("  2. olhodedeus sync --pull")
        print("  3. Digite sua senha mestra")


def cmd_sync(action: str = None, master_password: str = None):
    """Comando de sincronização."""
    sync = GitHubSync()
    
    if action == "setup":
        interactive_setup()
    elif action == "push":
        if not master_password:
            import getpass
            try:
                master_password = getpass.getpass("Senha Mestra: ")
            except:
                master_password = input("Senha Mestra: ").strip()
        sync.push(master_password)
    elif action == "pull":
        if not master_password:
            import getpass
            try:
                master_password = getpass.getpass("Senha Mestra: ")
            except:
                master_password = input("Senha Mestra: ").strip()
        sync.pull(master_password)
    elif action == "status":
        sync.status()
    else:
        sync.status()
        print("""
Comandos disponíveis:
  olhodedeus sync --setup   # Configurar sincronização
  olhodedeus sync --push    # Enviar auth para GitHub
  olhodedeus sync --pull    # Baixar auth do GitHub
  olhodedeus sync --status  # Ver status
        """)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--setup', action='store_true')
    parser.add_argument('--push', action='store_true')
    parser.add_argument('--pull', action='store_true')
    parser.add_argument('--status', action='store_true')
    args = parser.parse_args()
    
    if args.setup:
        cmd_sync("setup")
    elif args.push:
        cmd_sync("push")
    elif args.pull:
        cmd_sync("pull")
    else:
        cmd_sync("status")
