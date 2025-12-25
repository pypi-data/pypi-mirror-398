"""
Olho de Deus - Módulo de Autenticação
=====================================

Sistema centralizado de autenticação para:
- CLI local (login interativo)
- API REST (tokens/API keys)
- Acesso remoto (sessões)
"""

import os
import sys
import json
import hashlib
import secrets
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from functools import wraps

# Adiciona path do projeto
BASE_PATH = Path(__file__).parent.parent
if str(BASE_PATH) not in sys.path:
    sys.path.insert(0, str(BASE_PATH))


# ═══════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════════

AUTH_CONFIG_PATH = BASE_PATH / "config" / "auth.json"
SESSIONS_PATH = BASE_PATH / "config" / "sessions.json"
HASH_SALT = "olhodedeus-v1-secure-salt"  # Salt para hashing
TOKEN_EXPIRY_HOURS = 24  # Tokens expiram em 24h
MAX_LOGIN_ATTEMPTS = 3


# ═══════════════════════════════════════════════════════════════
# CLASSE PRINCIPAL DE AUTENTICAÇÃO
# ═══════════════════════════════════════════════════════════════

class AuthManager:
    """
    Gerenciador de autenticação do Olho de Deus.
    
    Uso:
        auth = AuthManager()
        
        # Criar usuário
        auth.create_user("admin", "senha123")
        
        # Autenticar
        if auth.authenticate("admin", "senha123"):
            token = auth.generate_token("admin")
            
        # Validar token
        user = auth.validate_token(token)
    """
    
    def __init__(self, config_path: Path = None):
        self.config_path = config_path or AUTH_CONFIG_PATH
        self.sessions_path = SESSIONS_PATH
        self.config = self._load_config()
        self.sessions = self._load_sessions()
        self._current_user = None
        self._current_token = None
    
    # === Propriedades ===
    
    @property
    def current_user(self) -> Optional[str]:
        """Usuário atualmente autenticado."""
        return self._current_user
    
    @property
    def is_authenticated(self) -> bool:
        """Verifica se há um usuário autenticado."""
        return self._current_user is not None
    
    @property
    def users(self) -> Dict[str, str]:
        """Dicionário de usuários (username: password_hash)."""
        return self.config.get("users", {})
    
    @property
    def api_keys(self) -> Dict[str, Dict]:
        """Dicionário de API keys (key: {user, permissions, created})."""
        return self.config.get("api_keys", {})
    
    # === Carregamento/Salvamento ===
    
    def _load_config(self) -> Dict:
        """Carrega configuração de autenticação."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {"users": {}, "api_keys": {}, "settings": {}}
    
    def _save_config(self):
        """Salva configuração de autenticação."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _load_sessions(self) -> Dict:
        """Carrega sessões ativas."""
        if self.sessions_path.exists():
            try:
                with open(self.sessions_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"tokens": {}}
    
    def _save_sessions(self):
        """Salva sessões ativas."""
        self.sessions_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.sessions_path, 'w') as f:
            json.dump(self.sessions, f, indent=2)
    
    # === Hashing ===
    
    def _hash_password(self, password: str) -> str:
        """Gera hash SHA256 da senha com salt."""
        salted = f"{HASH_SALT}{password}{HASH_SALT}"
        return hashlib.sha256(salted.encode()).hexdigest()
    
    def _hash_password_legacy(self, password: str) -> str:
        """Hash legado (sem salt) para compatibilidade."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    # === Gerenciamento de Usuários ===
    
    def create_user(self, username: str, password: str, role: str = "user") -> bool:
        """
        Cria um novo usuário.
        
        Args:
            username: Nome de usuário
            password: Senha
            role: Papel (admin, user)
            
        Returns:
            True se criado com sucesso
        """
        if username in self.users:
            return False
        
        if "users" not in self.config:
            self.config["users"] = {}
        
        self.config["users"][username] = {
            "password": self._hash_password(password),
            "role": role,
            "created": datetime.now().isoformat(),
        }
        self._save_config()
        return True
    
    def delete_user(self, username: str) -> bool:
        """Remove um usuário."""
        if username not in self.users:
            return False
        
        del self.config["users"][username]
        self._save_config()
        return True
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Altera a senha de um usuário."""
        if not self.authenticate(username, old_password):
            return False
        
        if isinstance(self.config["users"][username], dict):
            self.config["users"][username]["password"] = self._hash_password(new_password)
        else:
            self.config["users"][username] = {
                "password": self._hash_password(new_password),
                "role": "user",
                "created": datetime.now().isoformat(),
            }
        self._save_config()
        return True
    
    def list_users(self) -> list:
        """Lista todos os usuários."""
        users_list = []
        for username, data in self.users.items():
            if isinstance(data, dict):
                users_list.append({
                    "username": username,
                    "role": data.get("role", "user"),
                    "created": data.get("created", "unknown"),
                })
            else:
                # Formato legado (só hash)
                users_list.append({
                    "username": username,
                    "role": "user",
                    "created": "legacy",
                })
        return users_list
    
    # === Autenticação ===
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Autentica um usuário.
        
        Args:
            username: Nome de usuário
            password: Senha
            
        Returns:
            True se autenticado com sucesso
        """
        if username not in self.users:
            return False
        
        user_data = self.users[username]
        
        # Suporta formato novo (dict) e legado (string)
        if isinstance(user_data, dict):
            stored_hash = user_data.get("password", "")
        else:
            stored_hash = user_data
        
        # Tenta hash novo primeiro, depois legado
        if self._hash_password(password) == stored_hash:
            self._current_user = username
            return True
        
        # Compatibilidade com hash legado
        if self._hash_password_legacy(password) == stored_hash:
            self._current_user = username
            # Migra para novo formato
            self._migrate_user_format(username, password)
            return True
        
        return False
    
    def _migrate_user_format(self, username: str, password: str):
        """Migra usuário do formato legado para o novo."""
        self.config["users"][username] = {
            "password": self._hash_password(password),
            "role": "user",
            "created": datetime.now().isoformat(),
            "migrated": True,
        }
        self._save_config()
    
    def logout(self):
        """Faz logout do usuário atual."""
        if self._current_token:
            self.revoke_token(self._current_token)
        self._current_user = None
        self._current_token = None
    
    # === Tokens de Sessão ===
    
    def generate_token(self, username: str, expiry_hours: int = None) -> str:
        """
        Gera um token de sessão para o usuário.
        
        Args:
            username: Nome do usuário
            expiry_hours: Horas até expirar (default: 24)
            
        Returns:
            Token de sessão
        """
        expiry_hours = expiry_hours or TOKEN_EXPIRY_HOURS
        token = secrets.token_urlsafe(32)
        
        expiry = datetime.now() + timedelta(hours=expiry_hours)
        
        self.sessions["tokens"][token] = {
            "user": username,
            "created": datetime.now().isoformat(),
            "expires": expiry.isoformat(),
        }
        self._save_sessions()
        
        self._current_token = token
        return token
    
    def validate_token(self, token: str) -> Optional[str]:
        """
        Valida um token de sessão.
        
        Args:
            token: Token a validar
            
        Returns:
            Username se válido, None se inválido
        """
        if token not in self.sessions.get("tokens", {}):
            return None
        
        token_data = self.sessions["tokens"][token]
        expiry = datetime.fromisoformat(token_data["expires"])
        
        if datetime.now() > expiry:
            # Token expirado
            self.revoke_token(token)
            return None
        
        return token_data["user"]
    
    def revoke_token(self, token: str) -> bool:
        """Revoga um token de sessão."""
        if token in self.sessions.get("tokens", {}):
            del self.sessions["tokens"][token]
            self._save_sessions()
            return True
        return False
    
    def cleanup_expired_tokens(self):
        """Remove tokens expirados."""
        now = datetime.now()
        expired = []
        
        for token, data in self.sessions.get("tokens", {}).items():
            expiry = datetime.fromisoformat(data["expires"])
            if now > expiry:
                expired.append(token)
        
        for token in expired:
            del self.sessions["tokens"][token]
        
        if expired:
            self._save_sessions()
        
        return len(expired)
    
    # === API Keys ===
    
    def create_api_key(self, username: str, name: str = "default", permissions: list = None) -> str:
        """
        Cria uma API key para acesso remoto.
        
        Args:
            username: Usuário dono da key
            name: Nome descritivo
            permissions: Lista de permissões (default: todas)
            
        Returns:
            API key gerada
        """
        api_key = f"odd_{secrets.token_urlsafe(32)}"
        
        if "api_keys" not in self.config:
            self.config["api_keys"] = {}
        
        self.config["api_keys"][api_key] = {
            "user": username,
            "name": name,
            "permissions": permissions or ["*"],
            "created": datetime.now().isoformat(),
            "last_used": None,
        }
        self._save_config()
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """
        Valida uma API key.
        
        Args:
            api_key: Key a validar
            
        Returns:
            Dict com dados da key se válida, None se inválida
        """
        if api_key not in self.api_keys:
            return None
        
        key_data = self.api_keys[api_key]
        
        # Atualiza último uso
        self.config["api_keys"][api_key]["last_used"] = datetime.now().isoformat()
        self._save_config()
        
        return key_data
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoga uma API key."""
        if api_key in self.api_keys:
            del self.config["api_keys"][api_key]
            self._save_config()
            return True
        return False
    
    def list_api_keys(self, username: str = None) -> list:
        """Lista API keys (opcionalmente filtradas por usuário)."""
        keys = []
        for key, data in self.api_keys.items():
            if username and data.get("user") != username:
                continue
            keys.append({
                "key": key[:12] + "..." + key[-4:],  # Mascara a key
                "name": data.get("name", "default"),
                "user": data.get("user"),
                "created": data.get("created"),
                "last_used": data.get("last_used"),
            })
        return keys
    
    # === Login Interativo ===
    
    def interactive_login(self, clear_screen_func=None) -> Optional[str]:
        """
        Login interativo via terminal.
        
        Args:
            clear_screen_func: Função para limpar tela (opcional)
            
        Returns:
            Username se autenticado, None se falhou
        """
        if clear_screen_func:
            clear_screen_func()
        
        print("\n" + "═" * 50)
        print("      👁️  OLHO DE DEUS - AUTENTICAÇÃO")
        print("═" * 50 + "\n")
        
        # Se não há usuários, oferece criar
        if not self.users:
            print("⚠️  Nenhum usuário cadastrado.\n")
            print("[1] Criar novo usuário")
            print("[0] Sair\n")
            
            choice = input("Opção: ").strip()
            
            if choice == '1':
                return self._interactive_create_user()
            return None
        
        # Login normal
        for attempt in range(MAX_LOGIN_ATTEMPTS):
            remaining = MAX_LOGIN_ATTEMPTS - attempt
            
            username = input(f"Usuário ({remaining} tentativas): ").strip()
            
            if not username:
                continue
            
            if username not in self.users:
                print("❌ Usuário não encontrado!\n")
                continue
            
            # Esconde senha (se disponível)
            try:
                import getpass
                password = getpass.getpass("Senha: ")
            except:
                password = input("Senha: ").strip()
            
            if self.authenticate(username, password):
                print("\n✅ Autenticado com sucesso!")
                token = self.generate_token(username)
                input("\nPressione Enter para continuar...")
                return username
            else:
                print(f"❌ Senha incorreta! ({remaining - 1} tentativas restantes)\n")
        
        print("\n❌ Falha na autenticação. Encerrando...")
        input("Pressione Enter para sair...")
        return None
    
    def _interactive_create_user(self) -> Optional[str]:
        """Cria usuário interativamente."""
        print("\n📝 CRIAR NOVO USUÁRIO\n")
        
        username = input("Nome de usuário: ").strip()
        if not username:
            print("❌ Nome inválido!")
            return None
        
        if username in self.users:
            print("❌ Usuário já existe!")
            return None
        
        try:
            import getpass
            password = getpass.getpass("Senha: ")
            password2 = getpass.getpass("Confirme a senha: ")
        except:
            password = input("Senha: ").strip()
            password2 = input("Confirme a senha: ").strip()
        
        if password != password2:
            print("❌ Senhas não conferem!")
            return None
        
        if len(password) < 4:
            print("❌ Senha muito curta (mínimo 4 caracteres)!")
            return None
        
        # Primeiro usuário é admin
        role = "admin" if not self.users else "user"
        
        if self.create_user(username, password, role):
            print(f"\n✅ Usuário '{username}' criado com sucesso!")
            if role == "admin":
                print("   (Definido como administrador)")
            
            self._current_user = username
            self.generate_token(username)
            input("\nPressione Enter para continuar...")
            return username
        else:
            print("❌ Erro ao criar usuário!")
            return None


# ═══════════════════════════════════════════════════════════════
# DECORADORES PARA PROTEÇÃO DE FUNÇÕES
# ═══════════════════════════════════════════════════════════════

def require_auth(func):
    """
    Decorador que exige autenticação para executar uma função.
    
    Uso:
        @require_auth
        def funcao_protegida():
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth = AuthManager()
        if not auth.is_authenticated:
            print("❌ Autenticação necessária!")
            return None
        return func(*args, **kwargs)
    return wrapper


def require_role(role: str):
    """
    Decorador que exige um papel específico.
    
    Uso:
        @require_role("admin")
        def funcao_admin():
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth = AuthManager()
            if not auth.is_authenticated:
                print("❌ Autenticação necessária!")
                return None
            
            user_data = auth.users.get(auth.current_user, {})
            user_role = user_data.get("role", "user") if isinstance(user_data, dict) else "user"
            
            if user_role != role and user_role != "admin":
                print(f"❌ Permissão negada! Requer papel: {role}")
                return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════
# INSTÂNCIA GLOBAL
# ═══════════════════════════════════════════════════════════════

# Instância global para uso simplificado
_auth_instance = None

def get_auth() -> AuthManager:
    """Retorna instância global do AuthManager."""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = AuthManager()
    return _auth_instance


# ═══════════════════════════════════════════════════════════════
# FUNÇÕES DE COMPATIBILIDADE (para app/main.py)
# ═══════════════════════════════════════════════════════════════

def autenticar_usuario():
    """Função de compatibilidade com app/main.py."""
    auth = get_auth()
    return auth.interactive_login()


def hash_senha(senha: str) -> str:
    """Função de compatibilidade com app/main.py."""
    return hashlib.sha256(senha.encode()).hexdigest()


def carregar_auth_config() -> Dict:
    """Função de compatibilidade com app/main.py."""
    auth = get_auth()
    return auth.config


def salvar_auth_config(config: Dict):
    """Função de compatibilidade com app/main.py."""
    auth = get_auth()
    auth.config = config
    auth._save_config()


# ═══════════════════════════════════════════════════════════════
# CLI DE GERENCIAMENTO
# ═══════════════════════════════════════════════════════════════

def interactive_user_management():
    """Menu interativo para gerenciamento de usuários."""
    auth = get_auth()
    
    while True:
        print("\n" + "═" * 50)
        print("      👥 GERENCIAMENTO DE USUÁRIOS")
        print("═" * 50)
        print("""
[1] Listar usuários
[2] Criar usuário
[3] Alterar senha
[4] Excluir usuário
[5] Gerar API Key
[6] Listar API Keys
[7] Revogar API Key

[0] Voltar
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '0':
            break
        
        elif choice == '1':
            users = auth.list_users()
            print("\n👥 USUÁRIOS CADASTRADOS:\n")
            for user in users:
                print(f"  • {user['username']} ({user['role']})")
            input("\nPressione Enter...")
        
        elif choice == '2':
            auth._interactive_create_user()
        
        elif choice == '3':
            username = input("\nUsuário: ").strip()
            old_pass = input("Senha atual: ").strip()
            new_pass = input("Nova senha: ").strip()
            if auth.change_password(username, old_pass, new_pass):
                print("✅ Senha alterada!")
            else:
                print("❌ Falha ao alterar senha!")
            input("\nPressione Enter...")
        
        elif choice == '4':
            username = input("\nUsuário a excluir: ").strip()
            confirm = input(f"Confirma exclusão de '{username}'? (s/N): ").strip().lower()
            if confirm == 's':
                if auth.delete_user(username):
                    print("✅ Usuário excluído!")
                else:
                    print("❌ Usuário não encontrado!")
            input("\nPressione Enter...")
        
        elif choice == '5':
            username = input("\nUsuário para a API Key: ").strip()
            name = input("Nome da key (ex: 'meu-pc'): ").strip() or "default"
            if username in auth.users:
                key = auth.create_api_key(username, name)
                print(f"\n✅ API Key criada:")
                print(f"\n   {key}\n")
                print("   ⚠️  Guarde esta chave! Ela não será mostrada novamente.")
            else:
                print("❌ Usuário não encontrado!")
            input("\nPressione Enter...")
        
        elif choice == '6':
            keys = auth.list_api_keys()
            print("\n🔑 API KEYS:\n")
            for k in keys:
                print(f"  • {k['key']} ({k['name']}) - Usuário: {k['user']}")
            input("\nPressione Enter...")
        
        elif choice == '7':
            key = input("\nAPI Key completa para revogar: ").strip()
            if auth.revoke_api_key(key):
                print("✅ API Key revogada!")
            else:
                print("❌ API Key não encontrada!")
            input("\nPressione Enter...")


if __name__ == '__main__':
    # Teste rápido
    auth = AuthManager()
    user = auth.interactive_login()
    if user:
        print(f"\nLogado como: {user}")
        interactive_user_management()
