#!/usr/bin/env python3
"""
breach_sources.py

Sistema avançado para buscar e acessar dados vazados de múltiplas fontes.
Inclui integração com APIs públicas e privadas de verificação de breaches.

AVISO LEGAL: Use apenas para fins de pesquisa de segurança e verificação
de suas próprias credenciais. O uso indevido é ilegal.
"""
import os
import json
import hashlib
import requests
import time
from datetime import datetime
from typing import Optional, Dict, List, Any


class BreachChecker:
    """Verifica se emails/senhas aparecem em vazamentos conhecidos."""
    
    def __init__(self, config_path: str = "config/breach_apis.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OlhoDeDeus-SecurityResearch/1.0'
        })
    
    def _load_config(self) -> Dict:
        """Carrega configuração de APIs."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {
            "hibp_api_key": "",
            "dehashed_api_key": "",
            "dehashed_email": "",
            "leakcheck_api_key": "",
            "intelx_api_key": "",
            "proxynova_enabled": True,
            "rate_limit_seconds": 1.5
        }
    
    def save_config(self):
        """Salva configuração."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    # ══════════════════════════════════════════════════════════════
    # HAVE I BEEN PWNED (HIBP)
    # ══════════════════════════════════════════════════════════════
    
    def check_hibp_email(self, email: str) -> Dict:
        """
        Verifica se um email aparece em breaches conhecidos via HIBP.
        Requer API key (https://haveibeenpwned.com/API/Key)
        """
        api_key = self.config.get("hibp_api_key", "")
        if not api_key:
            return {"error": "HIBP API key não configurada", "breaches": []}
        
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        headers = {
            "hibp-api-key": api_key,
            "User-Agent": "OlhoDeDeus-SecurityResearch"
        }
        
        try:
            time.sleep(self.config.get("rate_limit_seconds", 1.5))
            resp = self.session.get(url, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                breaches = resp.json()
                return {
                    "email": email,
                    "found": True,
                    "breach_count": len(breaches),
                    "breaches": [b.get("Name", "Unknown") for b in breaches],
                    "details": breaches
                }
            elif resp.status_code == 404:
                return {"email": email, "found": False, "breaches": []}
            elif resp.status_code == 401:
                return {"error": "API key inválida", "breaches": []}
            elif resp.status_code == 429:
                return {"error": "Rate limit excedido, aguarde", "breaches": []}
            else:
                return {"error": f"Erro HTTP {resp.status_code}", "breaches": []}
        except Exception as e:
            return {"error": str(e), "breaches": []}
    
    def check_hibp_password(self, password: str) -> Dict:
        """
        Verifica se uma senha aparece em vazamentos via HIBP Pwned Passwords.
        Usa k-Anonymity (não envia a senha completa).
        GRATUITO - não requer API key.
        """
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]
        
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                hashes = resp.text.splitlines()
                for line in hashes:
                    parts = line.split(':')
                    if len(parts) == 2:
                        hash_suffix, count = parts
                        if hash_suffix.upper() == suffix:
                            return {
                                "password_hash": sha1_hash,
                                "found": True,
                                "count": int(count),
                                "message": f"Senha encontrada {count}x em vazamentos!"
                            }
                return {"found": False, "count": 0, "message": "Senha não encontrada em vazamentos conhecidos"}
            else:
                return {"error": f"Erro HTTP {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    # ══════════════════════════════════════════════════════════════
    # DEHASHED API
    # ══════════════════════════════════════════════════════════════
    
    def search_dehashed(self, query: str, query_type: str = "email") -> Dict:
        """
        Busca em DeHashed (requer API key paga).
        query_type: email, username, ip_address, name, address, phone, vin, password
        """
        api_key = self.config.get("dehashed_api_key", "")
        email = self.config.get("dehashed_email", "")
        
        if not api_key or not email:
            return {"error": "DeHashed API não configurada", "entries": []}
        
        url = f"https://api.dehashed.com/search?query={query_type}:{query}"
        
        try:
            time.sleep(self.config.get("rate_limit_seconds", 1.5))
            resp = self.session.get(url, auth=(email, api_key), timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "query": query,
                    "type": query_type,
                    "total": data.get("total", 0),
                    "entries": data.get("entries", [])[:100]  # Limita a 100
                }
            elif resp.status_code == 401:
                return {"error": "Credenciais DeHashed inválidas", "entries": []}
            else:
                return {"error": f"Erro HTTP {resp.status_code}", "entries": []}
        except Exception as e:
            return {"error": str(e), "entries": []}
    
    # ══════════════════════════════════════════════════════════════
    # LEAKCHECK API
    # ══════════════════════════════════════════════════════════════
    
    def search_leakcheck(self, query: str, query_type: str = "email") -> Dict:
        """
        Busca em LeakCheck.io (tem plano gratuito limitado).
        query_type: email, username, phone, hash, domain
        """
        api_key = self.config.get("leakcheck_api_key", "")
        
        if not api_key:
            return {"error": "LeakCheck API não configurada", "sources": []}
        
        url = f"https://leakcheck.io/api/public?key={api_key}&check={query}&type={query_type}"
        
        try:
            time.sleep(self.config.get("rate_limit_seconds", 1.5))
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    return {
                        "query": query,
                        "found": data.get("found", 0),
                        "sources": data.get("sources", []),
                        "fields": data.get("fields", [])
                    }
                else:
                    return {"error": data.get("error", "Unknown error"), "sources": []}
            else:
                return {"error": f"Erro HTTP {resp.status_code}", "sources": []}
        except Exception as e:
            return {"error": str(e), "sources": []}
    
    # ══════════════════════════════════════════════════════════════
    # FONTES GRATUITAS / PÚBLICAS
    # ══════════════════════════════════════════════════════════════
    
    def check_firefox_monitor(self, email: str) -> Dict:
        """
        Verifica via Firefox Monitor (usa HIBP por baixo, mas é gratuito).
        """
        # Firefox Monitor usa HIBP internamente
        # Podemos fazer uma verificação básica via web scraping
        return self.check_hibp_password_only(email)
    
    def check_breach_directory(self, email: str) -> Dict:
        """
        Verifica em BreachDirectory.org (gratuito, mas limitado).
        """
        url = "https://breachdirectory.org/api/v1/check"
        
        try:
            time.sleep(2)  # Rate limit mais conservador
            resp = self.session.post(url, json={"email": email}, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "email": email,
                    "found": data.get("found", False),
                    "sources": data.get("sources", [])
                }
            else:
                return {"error": f"Erro HTTP {resp.status_code}", "sources": []}
        except Exception as e:
            return {"error": str(e), "sources": []}
    
    # ══════════════════════════════════════════════════════════════
    # BUSCA CONSOLIDADA
    # ══════════════════════════════════════════════════════════════
    
    def full_check(self, email: str, check_password: str = None) -> Dict:
        """
        Executa verificação completa em todas as fontes disponíveis.
        """
        results = {
            "email": email,
            "timestamp": datetime.now().isoformat(),
            "sources_checked": [],
            "total_breaches": 0,
            "breaches": [],
            "password_compromised": None,
            "errors": []
        }
        
        # HIBP Email (se API key configurada)
        if self.config.get("hibp_api_key"):
            hibp_result = self.check_hibp_email(email)
            results["sources_checked"].append("HIBP")
            if "error" not in hibp_result:
                results["breaches"].extend(hibp_result.get("breaches", []))
                results["total_breaches"] += hibp_result.get("breach_count", 0)
            else:
                results["errors"].append(f"HIBP: {hibp_result['error']}")
        
        # HIBP Password (sempre gratuito)
        if check_password:
            pwd_result = self.check_hibp_password(check_password)
            results["sources_checked"].append("HIBP-Passwords")
            results["password_compromised"] = pwd_result.get("found", False)
            if pwd_result.get("found"):
                results["password_leak_count"] = pwd_result.get("count", 0)
        
        # DeHashed (se configurado)
        if self.config.get("dehashed_api_key"):
            dh_result = self.search_dehashed(email, "email")
            results["sources_checked"].append("DeHashed")
            if "error" not in dh_result:
                results["dehashed_total"] = dh_result.get("total", 0)
            else:
                results["errors"].append(f"DeHashed: {dh_result['error']}")
        
        # LeakCheck (se configurado)
        if self.config.get("leakcheck_api_key"):
            lc_result = self.search_leakcheck(email, "email")
            results["sources_checked"].append("LeakCheck")
            if "error" not in lc_result:
                results["leakcheck_found"] = lc_result.get("found", 0)
            else:
                results["errors"].append(f"LeakCheck: {lc_result['error']}")
        
        # Remove duplicatas de breaches
        results["breaches"] = list(set(results["breaches"]))
        
        return results


class BreachDownloader:
    """Baixa e processa arquivos de vazamentos de fontes configuradas."""
    
    # Fontes públicas conhecidas (apenas para referência de pesquisa)
    KNOWN_SOURCES = {
        "hibp_passwords": {
            "url": "https://haveibeenpwned.com/Passwords",
            "description": "HIBP Pwned Passwords (SHA1 hashes, legal)",
            "format": "sha1:count"
        },
        "seclist_passwords": {
            "url": "https://github.com/danielmiessler/SecLists/tree/master/Passwords",
            "description": "SecLists Password Lists (wordlists comuns)",
            "format": "plaintext"
        },
        "weakpass": {
            "url": "https://weakpass.com/",
            "description": "Weakpass wordlists (para pesquisa)",
            "format": "plaintext"
        },
        "crackstation": {
            "url": "https://crackstation.net/crackstation-wordlist-password-cracking-dictionary.htm",
            "description": "CrackStation wordlist (1.5GB)",
            "format": "plaintext"
        }
    }
    
    def __init__(self, output_dir: str = "raw_data/breaches"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_hibp_passwords(self, output_file: str = None) -> str:
        """
        Instruções para baixar HIBP Pwned Passwords.
        O arquivo é muito grande (~30GB) para download direto.
        """
        print("""
╔══════════════════════════════════════════════════════════════╗
║  HIBP Pwned Passwords - Instruções de Download               ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  O arquivo completo tem ~30GB (SHA1 hashes + contagens).     ║
║                                                              ║
║  Opções de download:                                         ║
║                                                              ║
║  1. Via Torrent (recomendado):                               ║
║     https://haveibeenpwned.com/Passwords                     ║
║                                                              ║
║  2. Via API (verificação individual):                        ║
║     Use check_hibp_password() para verificar senhas          ║
║     individualmente sem baixar o arquivo completo.           ║
║                                                              ║
║  3. Cloudflare Range API (k-Anonymity):                      ║
║     https://api.pwnedpasswords.com/range/{5-char-prefix}     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        return "Veja instruções acima"
    
    def download_seclist(self, list_name: str = "10-million-password-list-top-100000.txt") -> str:
        """
        Baixa uma wordlist do SecLists (GitHub).
        """
        base_url = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords"
        url = f"{base_url}/{list_name}"
        
        output_file = os.path.join(self.output_dir, list_name)
        
        print(f"Baixando {list_name}...")
        try:
            resp = self.session.get(url, stream=True, timeout=60)
            if resp.status_code == 200:
                with open(output_file, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Salvo em: {output_file}")
                return output_file
            else:
                print(f"Erro: HTTP {resp.status_code}")
                return None
        except Exception as e:
            print(f"Erro: {e}")
            return None
    
    def list_available_seclists(self) -> List[str]:
        """Lista wordlists populares do SecLists com URLs funcionais."""
        return [
            "Common-Credentials/10-million-password-list-top-100.txt",
            "Common-Credentials/10-million-password-list-top-1000.txt",
            "Common-Credentials/10-million-password-list-top-10000.txt",
            "Common-Credentials/10-million-password-list-top-100000.txt",
            "Common-Credentials/10-million-password-list-top-1000000.txt",
            "Common-Credentials/10k-most-common.txt",
            "Common-Credentials/100k-most-used-passwords-NCSC.txt",
            "darkweb2017-top10000.txt",
            "xato-net-10-million-passwords.txt",
            "Leaked-Databases/rockyou-75.txt"
        ]


def interactive_menu():
    """Menu interativo para o módulo de breach sources."""
    checker = BreachChecker()
    downloader = BreachDownloader()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║        🔐 BREACH CHECKER - Verificador de Vazamentos         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] Verificar email em vazamentos (HIBP)                    ║
║  [2] Verificar senha em vazamentos (HIBP - Gratuito)         ║
║  [3] Busca completa (todas as fontes)                        ║
║  [4] Baixar wordlists (SecLists)                             ║
║  [5] Configurar API keys                                     ║
║  [6] Ver fontes disponíveis                                  ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            email = input("\nDigite o email para verificar: ").strip()
            if email:
                print("\nVerificando...")
                result = checker.check_hibp_email(email)
                print(f"\nResultado: {json.dumps(result, indent=2)}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '2':
            password = input("\nDigite a senha para verificar: ").strip()
            if password:
                print("\nVerificando (usa k-Anonymity, seguro)...")
                result = checker.check_hibp_password(password)
                print(f"\nResultado: {json.dumps(result, indent=2)}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '3':
            email = input("\nDigite o email: ").strip()
            password = input("Digite a senha (ou Enter para pular): ").strip() or None
            if email:
                print("\nExecutando busca completa...")
                result = checker.full_check(email, password)
                print(f"\nResultado: {json.dumps(result, indent=2)}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '4':
            print("\nWordlists disponíveis:")
            for i, name in enumerate(downloader.list_available_seclists(), 1):
                print(f"  [{i}] {name}")
            sel = input("\nEscolha o número ou Enter para a padrão (top-100000): ").strip()
            lists = downloader.list_available_seclists()
            if sel.isdigit() and 1 <= int(sel) <= len(lists):
                downloader.download_seclist(lists[int(sel)-1])
            else:
                downloader.download_seclist()
            input("\nPressione Enter para continuar...")
        
        elif choice == '5':
            print("\n=== Configuração de APIs ===")
            print(f"Atual: {json.dumps(checker.config, indent=2)}")
            print("\nQual API configurar?")
            print("  [1] HIBP API Key (https://haveibeenpwned.com/API/Key)")
            print("  [2] DeHashed (email + API key)")
            print("  [3] LeakCheck API Key")
            api_choice = input("Opção: ").strip()
            
            if api_choice == '1':
                key = input("HIBP API Key: ").strip()
                if key:
                    checker.config["hibp_api_key"] = key
                    checker.save_config()
                    print("Salvo!")
            elif api_choice == '2':
                email = input("DeHashed Email: ").strip()
                key = input("DeHashed API Key: ").strip()
                if email and key:
                    checker.config["dehashed_email"] = email
                    checker.config["dehashed_api_key"] = key
                    checker.save_config()
                    print("Salvo!")
            elif api_choice == '3':
                key = input("LeakCheck API Key: ").strip()
                if key:
                    checker.config["leakcheck_api_key"] = key
                    checker.save_config()
                    print("Salvo!")
            input("\nPressione Enter para continuar...")
        
        elif choice == '6':
            print("\n=== Fontes de Dados Disponíveis ===\n")
            for name, info in downloader.KNOWN_SOURCES.items():
                print(f"  📁 {name}")
                print(f"     URL: {info['url']}")
                print(f"     Descrição: {info['description']}")
                print(f"     Formato: {info['format']}")
                print()
            downloader.download_hibp_passwords()
            input("\nPressione Enter para continuar...")
        
        elif choice == '0':
            break


if __name__ == '__main__':
    interactive_menu()
