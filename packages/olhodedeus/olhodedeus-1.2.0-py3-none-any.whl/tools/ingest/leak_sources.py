#!/usr/bin/env python3
"""
leak_sources.py

Sistema avançado para buscar dados vazados de múltiplas fontes GRATUITAS.
Inclui Surface Web, APIs públicas e fontes de pesquisa de segurança.

AVISO LEGAL: Use apenas para fins de pesquisa de segurança e verificação
de suas próprias credenciais. O uso indevido é ilegal.
"""
import os
import json
import hashlib
import requests
import time
import re
from datetime import datetime
from typing import Optional, Dict, List, Any
from urllib.parse import quote, urljoin
import base64


class FreeLeakChecker:
    """
    Buscador em fontes 100% GRATUITAS de vazamentos.
    Não requer API keys.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7'
        })
        self.rate_limit = 2.0  # segundos entre requests
    
    # ══════════════════════════════════════════════════════════════
    # 1. HIBP PWNED PASSWORDS - 100% GRATUITO
    # ══════════════════════════════════════════════════════════════
    def check_hibp_password(self, password: str) -> Dict:
        """
        HIBP Pwned Passwords - 100% Gratuito, sem limites.
        Usa k-Anonymity - sua senha NÃO é enviada.
        """
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]
        
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    parts = line.split(':')
                    if len(parts) == 2 and parts[0].upper() == suffix:
                        return {
                            "source": "HIBP Pwned Passwords",
                            "found": True,
                            "count": int(parts[1]),
                            "hash": sha1_hash,
                            "message": f"⚠️ Senha encontrada {int(parts[1]):,}x em vazamentos!"
                        }
                return {
                    "source": "HIBP Pwned Passwords",
                    "found": False,
                    "count": 0,
                    "message": "✅ Senha NÃO encontrada em vazamentos conhecidos"
                }
        except Exception as e:
            return {"source": "HIBP Pwned Passwords", "error": str(e)}
        
        return {"source": "HIBP Pwned Passwords", "found": False}
    
    # ══════════════════════════════════════════════════════════════
    # 2. LEAK-LOOKUP.COM - API GRATUITA
    # ══════════════════════════════════════════════════════════════
    def check_leak_lookup(self, query: str, query_type: str = "email") -> Dict:
        """
        Leak-Lookup - API gratuita para busca de leaks.
        Tipos: email, username, domain, password, hash
        """
        url = "https://leak-lookup.com/api/search"
        
        try:
            time.sleep(self.rate_limit)
            data = {
                "key": "your_key",
                "type": query_type,
                "query": query
            }
            resp = self.session.post(url, data=data, timeout=15)
            
            if resp.status_code == 200:
                result = resp.json()
                if result.get("error") == "false" or not result.get("error"):
                    return {
                        "source": "Leak-Lookup",
                        "found": True,
                        "message": result.get("message", "Dados encontrados"),
                        "data": result
                    }
            return {"source": "Leak-Lookup", "found": False, "message": "Nenhum resultado"}
        except Exception as e:
            return {"source": "Leak-Lookup", "error": str(e)}
    
    # ══════════════════════════════════════════════════════════════
    # 3. BREACHDIRECTORY - API GRATUITA (parcial)
    # ══════════════════════════════════════════════════════════════
    def check_breach_directory(self, email: str) -> Dict:
        """
        BreachDirectory - Mostra em quais breaches o email aparece.
        """
        # Usar RapidAPI endpoint gratuito
        url = f"https://breachdirectory.p.rapidapi.com/?func=auto&term={quote(email)}"
        headers = {
            "X-RapidAPI-Key": "demo",  # Demo key
            "X-RapidAPI-Host": "breachdirectory.p.rapidapi.com"
        }
        
        try:
            time.sleep(self.rate_limit)
            resp = self.session.get(url, headers=headers, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") and data.get("result"):
                    results = data.get("result", [])
                    return {
                        "source": "BreachDirectory",
                        "found": len(results) > 0,
                        "count": len(results),
                        "breaches": results[:20],
                        "message": f"Encontrado em {len(results)} breach(es)"
                    }
            return {"source": "BreachDirectory", "found": False}
        except Exception as e:
            return {"source": "BreachDirectory", "error": str(e)}
    
    # ══════════════════════════════════════════════════════════════
    # 4. EMAILREP.IO - API GRATUITA
    # ══════════════════════════════════════════════════════════════
    def check_emailrep(self, email: str) -> Dict:
        """
        EmailRep.io - Reputação de email gratuita.
        Mostra se email está em breaches, é spam, etc.
        """
        url = f"https://emailrep.io/{quote(email)}"
        
        try:
            time.sleep(self.rate_limit)
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                details = data.get("details", {})
                
                return {
                    "source": "EmailRep.io",
                    "found": True,
                    "email": email,
                    "reputation": data.get("reputation", "unknown"),
                    "suspicious": data.get("suspicious", False),
                    "references": data.get("references", 0),
                    "data_breach": details.get("data_breach", False),
                    "credentials_leaked": details.get("credentials_leaked", False),
                    "malicious_activity": details.get("malicious_activity", False),
                    "spam": details.get("spam", False),
                    "disposable": details.get("disposable", False),
                    "free_provider": details.get("free_provider", False),
                    "profiles": details.get("profiles", []),
                    "message": f"Reputação: {data.get('reputation', 'N/A')}" + 
                              (" ⚠️ DATA BREACH!" if details.get("data_breach") else "")
                }
            elif resp.status_code == 429:
                return {"source": "EmailRep.io", "error": "Rate limit - tente novamente em 1 minuto"}
            return {"source": "EmailRep.io", "found": False}
        except Exception as e:
            return {"source": "EmailRep.io", "error": str(e)}
    
    # ══════════════════════════════════════════════════════════════
    # 5. LEAKCHECK.IO - Endpoint público
    # ══════════════════════════════════════════════════════════════
    def check_leakcheck_free(self, email: str) -> Dict:
        """
        LeakCheck.io - Versão pública gratuita.
        """
        url = f"https://leakcheck.io/api/public?check={quote(email)}"
        
        try:
            time.sleep(self.rate_limit)
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    found = data.get("found", 0)
                    return {
                        "source": "LeakCheck.io (Free)",
                        "found": found > 0,
                        "count": found,
                        "fields": data.get("fields", []),
                        "sources": data.get("sources", [])[:10],
                        "message": f"Encontrado em {found} leak(s)" if found > 0 else "Não encontrado"
                    }
            return {"source": "LeakCheck.io (Free)", "found": False}
        except Exception as e:
            return {"source": "LeakCheck.io (Free)", "error": str(e)}
    
    # ══════════════════════════════════════════════════════════════
    # 6. HASHES.ORG - Lookup de hashes GRATUITO
    # ══════════════════════════════════════════════════════════════
    def check_hashes_org(self, hash_value: str) -> Dict:
        """
        Hashes.org - Lookup gratuito de hashes.
        """
        url = f"https://hashes.org/api.php?key=demo&query={hash_value}"
        
        try:
            time.sleep(self.rate_limit)
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code == 200:
                if ":" in resp.text and len(resp.text) < 500:
                    parts = resp.text.strip().split(":")
                    if len(parts) >= 2:
                        return {
                            "source": "Hashes.org",
                            "found": True,
                            "hash": parts[0],
                            "plaintext": parts[1],
                            "message": f"Hash cracked: {parts[1]}"
                        }
            return {"source": "Hashes.org", "found": False}
        except Exception as e:
            return {"source": "Hashes.org", "error": str(e)}
    
    # ══════════════════════════════════════════════════════════════
    # 7. MD5DECRYPT.NET - Hash lookup GRATUITO
    # ══════════════════════════════════════════════════════════════
    def check_md5decrypt(self, hash_value: str, hash_type: str = "md5") -> Dict:
        """
        MD5Decrypt.net - Lookup de hash gratuito.
        """
        url = f"https://md5decrypt.net/Api/api.php?hash={hash_value}&hash_type={hash_type}&email=test@test.com&code=test"
        
        try:
            time.sleep(self.rate_limit)
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code == 200 and resp.text and resp.text != "":
                plaintext = resp.text.strip()
                if plaintext and not plaintext.startswith("ERROR"):
                    return {
                        "source": "MD5Decrypt.net",
                        "found": True,
                        "hash": hash_value,
                        "plaintext": plaintext,
                        "message": f"Decrypted: {plaintext}"
                    }
            return {"source": "MD5Decrypt.net", "found": False}
        except Exception as e:
            return {"source": "MD5Decrypt.net", "error": str(e)}
    
    # ══════════════════════════════════════════════════════════════
    # 8. CRACK HASH EM TODAS AS FONTES
    # ══════════════════════════════════════════════════════════════
    def crack_hash_all_sources(self, hash_value: str) -> Dict:
        """
        Tenta crackear hash usando todas as fontes gratuitas.
        """
        results = {
            "hash": hash_value,
            "hash_type": self._detect_hash_type(hash_value),
            "sources_checked": [],
            "cracked": False,
            "plaintext": None
        }
        
        print(f"  🔍 Verificando hash em múltiplas fontes...")
        
        sources = [
            ("Hashes.org", lambda: self.check_hashes_org(hash_value)),
            ("MD5Decrypt", lambda: self.check_md5decrypt(hash_value))
        ]
        
        for name, check_func in sources:
            print(f"    • {name}...", end=" ", flush=True)
            result = check_func()
            results["sources_checked"].append(name)
            
            if result.get("found") and result.get("plaintext"):
                results["cracked"] = True
                results["plaintext"] = result["plaintext"]
                results["source"] = name
                print(f"✅ CRACKED: {result['plaintext']}")
                break
            elif result.get("error"):
                print(f"❌ {result['error']}")
            else:
                print("Não encontrado")
        
        return results
    
    def _detect_hash_type(self, hash_value: str) -> str:
        """Detecta tipo de hash pelo tamanho."""
        length = len(hash_value)
        if length == 32:
            return "MD5 ou NTLM"
        elif length == 40:
            return "SHA1"
        elif length == 64:
            return "SHA256"
        elif length == 128:
            return "SHA512"
        else:
            return "Desconhecido"


class LeakAggregator:
    """
    Agregador de múltiplas fontes de vazamentos.
    """
    
    def __init__(self, config_path: str = "config/leak_sources.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.free_checker = FreeLeakChecker()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _load_config(self) -> Dict:
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._default_config()
    
    def _default_config(self) -> Dict:
        return {
            "apis": {
                "hibp": {"enabled": True, "api_key": ""},
                "leakcheck": {"enabled": True, "api_key": ""},
                "dehashed": {"enabled": True, "api_key": "", "email": ""},
                "intelx": {"enabled": True, "api_key": ""},
                "snusbase": {"enabled": True, "api_key": ""},
            },
            "rate_limit_seconds": 2.0
        }
    
    def save_config(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def search_email_free(self, email: str) -> Dict:
        """
        Busca email em TODAS as fontes GRATUITAS.
        """
        results = {
            "query": email,
            "query_type": "email",
            "timestamp": datetime.now().isoformat(),
            "sources_checked": [],
            "sources_with_results": [],
            "total_breaches": 0,
            "data": {},
            "errors": []
        }
        
        print(f"\n🔍 Buscando {email} em fontes GRATUITAS...\n")
        
        # 1. EmailRep.io
        print("  📧 [1/4] EmailRep.io...", end=" ", flush=True)
        er_result = self.free_checker.check_emailrep(email)
        results["data"]["emailrep"] = er_result
        results["sources_checked"].append("EmailRep.io")
        
        if er_result.get("error"):
            results["errors"].append(f"EmailRep: {er_result['error']}")
            print(f"❌ {er_result['error']}")
        else:
            breach_status = "⚠️ BREACH!" if er_result.get("data_breach") else "OK"
            print(f"✅ Rep: {er_result.get('reputation', 'N/A')} {breach_status}")
            if er_result.get("data_breach") or er_result.get("credentials_leaked"):
                results["sources_with_results"].append("EmailRep.io")
                results["total_breaches"] += 1
        
        # 2. LeakCheck Free
        print("  🔐 [2/4] LeakCheck (Free)...", end=" ", flush=True)
        lc_result = self.free_checker.check_leakcheck_free(email)
        results["data"]["leakcheck_free"] = lc_result
        results["sources_checked"].append("LeakCheck (Free)")
        
        if lc_result.get("error"):
            results["errors"].append(f"LeakCheck: {lc_result['error']}")
            print(f"❌")
        elif lc_result.get("found"):
            count = lc_result.get("count", 0)
            results["sources_with_results"].append("LeakCheck")
            results["total_breaches"] += count
            print(f"⚠️ {count} leak(s)!")
        else:
            print("✅ Limpo")
        
        # 3. BreachDirectory
        print("  📂 [3/4] BreachDirectory...", end=" ", flush=True)
        bd_result = self.free_checker.check_breach_directory(email)
        results["data"]["breach_directory"] = bd_result
        results["sources_checked"].append("BreachDirectory")
        
        if bd_result.get("error"):
            results["errors"].append(f"BreachDirectory: {bd_result['error']}")
            print(f"❌")
        elif bd_result.get("found"):
            count = bd_result.get("count", 0)
            results["sources_with_results"].append("BreachDirectory")
            results["total_breaches"] += count
            print(f"⚠️ {count} breach(es)!")
        else:
            print("✅ Limpo")
        
        # 4. Leak-Lookup
        print("  🔎 [4/4] Leak-Lookup...", end=" ", flush=True)
        ll_result = self.free_checker.check_leak_lookup(email, "email")
        results["data"]["leak_lookup"] = ll_result
        results["sources_checked"].append("Leak-Lookup")
        
        if ll_result.get("error"):
            print(f"❌")
        elif ll_result.get("found"):
            results["sources_with_results"].append("Leak-Lookup")
            print(f"⚠️ Dados encontrados!")
        else:
            print("✅ Limpo")
        
        return results
    
    def search_password(self, password: str) -> Dict:
        """Verifica senha no HIBP (100% gratuito)."""
        return self.free_checker.check_hibp_password(password)
    
    def search_hash(self, hash_value: str) -> Dict:
        """Tenta crackear hash em fontes gratuitas."""
        return self.free_checker.crack_hash_all_sources(hash_value)
    
    def search_complete(self, email: str, password: str = None) -> Dict:
        """
        Busca completa: email em todas as fontes + senha se fornecida.
        """
        results = {
            "email": email,
            "timestamp": datetime.now().isoformat(),
            "email_results": {},
            "password_results": {},
            "summary": {}
        }
        
        # Buscar email
        email_results = self.search_email_free(email)
        results["email_results"] = email_results
        
        pwd_result = {}
        # Verificar senha se fornecida
        if password:
            print("\n  🔐 Verificando senha (HIBP)...", end=" ", flush=True)
            pwd_result = self.search_password(password)
            results["password_results"] = pwd_result
            
            if pwd_result.get("found"):
                print(f"⚠️ VAZADA {pwd_result.get('count', 0):,}x!")
            else:
                print("✅ Não encontrada em vazamentos")
        
        # Resumo
        results["summary"] = {
            "email_in_breaches": len(email_results.get("sources_with_results", [])) > 0,
            "breach_sources": email_results.get("sources_with_results", []),
            "total_breaches": email_results.get("total_breaches", 0),
            "password_compromised": pwd_result.get("found", False) if password else None,
            "password_leak_count": pwd_result.get("count", 0) if password else 0
        }
        
        return results
    
    def print_summary(self, results: Dict):
        """Imprime resumo formatado dos resultados."""
        print("\n" + "="*60)
        print("📊 RESUMO DA BUSCA")
        print("="*60)
        
        email_results = results.get("email_results", {})
        
        print(f"Email: {results.get('email', 'N/A')}")
        print(f"Fontes verificadas: {len(email_results.get('sources_checked', []))}")
        print(f"Fontes com resultados: {len(email_results.get('sources_with_results', []))}")
        
        summary = results.get("summary", {})
        
        if summary.get("email_in_breaches"):
            print(f"\n⚠️  EMAIL COMPROMETIDO!")
            print(f"   Encontrado em: {', '.join(summary.get('breach_sources', []))}")
            print(f"   Total de breaches: {summary.get('total_breaches', 0)}")
        else:
            print(f"\n✅ Email não encontrado em vazamentos conhecidos")
        
        if summary.get("password_compromised") is not None:
            if summary["password_compromised"]:
                print(f"\n⚠️  SENHA VAZADA {summary.get('password_leak_count', 0):,}x!")
            else:
                print(f"\n✅ Senha não encontrada em vazamentos")
        
        if email_results.get("errors"):
            print(f"\n⚠️  Erros: {len(email_results['errors'])}")
        
        print("="*60)


class DatabaseDownloader:
    """
    Gerenciador de download de databases e wordlists públicas.
    """
    
    WORDLISTS = {
        "seclists_top100": {
            "name": "SecLists Top 100",
            "url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-100.txt",
            "size": "1KB"
        },
        "seclists_top1000": {
            "name": "SecLists Top 1000",
            "url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000.txt",
            "size": "8KB"
        },
        "seclists_top10000": {
            "name": "SecLists Top 10000",
            "url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-10000.txt",
            "size": "80KB"
        },
        "seclists_top100000": {
            "name": "SecLists Top 100000",
            "url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-100000.txt",
            "size": "800KB"
        },
        "rockyou_75": {
            "name": "RockYou 75",
            "url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Leaked-Databases/rockyou-75.txt",
            "size": "500KB"
        },
        "darkweb_2017": {
            "name": "Darkweb 2017 Top 10k",
            "url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/darkweb2017-top10000.txt",
            "size": "100KB"
        }
    }
    
    def __init__(self, output_dir: str = "raw_data/wordlists"):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        os.makedirs(output_dir, exist_ok=True)
    
    def list_available_seclists(self) -> List[str]:
        """Lista wordlists disponíveis."""
        return list(self.WORDLISTS.keys())
    
    def download_seclist(self, name: str) -> Optional[str]:
        """Baixa uma wordlist específica."""
        if name not in self.WORDLISTS:
            return None
        
        info = self.WORDLISTS[name]
        filename = info["url"].split("/")[-1]
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            print(f"📥 Baixando {info['name']}...")
            resp = self.session.get(info["url"], timeout=60)
            if resp.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(resp.content)
                print(f"✅ Salvo: {filepath}")
                return filepath
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        return None


def interactive_menu():
    """Menu interativo para o agregador de leaks."""
    aggregator = LeakAggregator()
    downloader = DatabaseDownloader()
    free_checker = FreeLeakChecker()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║       🔐 LEAK AGGREGATOR - Busca GRATUITA Multi-Fonte        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ──── 🆓 BUSCA GRATUITA (SEM API KEY) ────                   ║
║  [1] 📧 Buscar EMAIL (EmailRep + LeakCheck + BreachDir)      ║
║  [2] 🔐 Verificar SENHA (HIBP - Ilimitado)                   ║
║  [3] 🔍 Busca COMPLETA (Email + Senha)                       ║
║  [4] #️⃣  Crackear HASH (MD5, SHA1, SHA256, NTLM)              ║
║                                                              ║
║  ──── 🔎 VERIFICAÇÕES ESPECÍFICAS ────                       ║
║  [5] 📊 EmailRep - Reputação detalhada                       ║
║  [6] 📂 BreachDirectory - Ver breaches                       ║
║  [7] 🔐 LeakCheck Free - Verificar leaks                     ║
║                                                              ║
║  ──── 📥 DOWNLOADS ────                                      ║
║  [8] 📥 Baixar Wordlists                                     ║
║  [9] ⚙️  Configurar APIs (premium)                            ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            email = input("\n📧 Digite o email: ").strip()
            if email:
                results = aggregator.search_email_free(email)
                aggregator.print_summary({"email": email, "email_results": results, "summary": {
                    "email_in_breaches": len(results.get("sources_with_results", [])) > 0,
                    "breach_sources": results.get("sources_with_results", []),
                    "total_breaches": results.get("total_breaches", 0)
                }})
            input("\nPressione Enter para continuar...")
        
        elif choice == '2':
            password = input("\n🔐 Digite a senha para verificar: ").strip()
            if password:
                print("\nVerificando senha no HIBP (k-Anonymity)...")
                result = aggregator.search_password(password)
                print(f"\n{result.get('message', 'Erro')}")
                if result.get("found"):
                    print(f"   Hash SHA1: {result.get('hash', 'N/A')}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '3':
            email = input("\n📧 Digite o email: ").strip()
            password = input("🔐 Digite a senha (ou Enter para pular): ").strip() or None
            if email:
                results = aggregator.search_complete(email, password)
                aggregator.print_summary(results)
                
                save = input("\nSalvar resultados? (s/n): ").strip().lower()
                if save == 's':
                    os.makedirs("data/leak_results", exist_ok=True)
                    filename = f"data/leak_results/{email.replace('@', '_at_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
                    print(f"✅ Salvo: {filename}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '4':
            hash_value = input("\n#️⃣ Digite o hash: ").strip()
            if hash_value:
                results = aggregator.search_hash(hash_value)
                print(f"\n📊 Tipo detectado: {results.get('hash_type', 'N/A')}")
                if results.get("cracked"):
                    print(f"✅ CRACKED: {results.get('plaintext')}")
                    print(f"   Fonte: {results.get('source')}")
                else:
                    print("❌ Hash não encontrado nas bases de dados")
            input("\nPressione Enter para continuar...")
        
        elif choice == '5':
            email = input("\n📧 Digite o email: ").strip()
            if email:
                print("\nVerificando reputação no EmailRep.io...")
                result = free_checker.check_emailrep(email)
                if result.get("error"):
                    print(f"❌ Erro: {result['error']}")
                else:
                    print(f"\n📊 REPUTAÇÃO DE {email}:")
                    print(f"   Reputação: {result.get('reputation', 'N/A')}")
                    print(f"   Suspeito: {'Sim' if result.get('suspicious') else 'Não'}")
                    print(f"   Data Breach: {'⚠️ SIM' if result.get('data_breach') else 'Não'}")
                    print(f"   Credenciais Vazadas: {'⚠️ SIM' if result.get('credentials_leaked') else 'Não'}")
                    print(f"   Spam: {'Sim' if result.get('spam') else 'Não'}")
                    print(f"   Email Descartável: {'Sim' if result.get('disposable') else 'Não'}")
                    print(f"   Provedor Gratuito: {'Sim' if result.get('free_provider') else 'Não'}")
                    if result.get("profiles"):
                        print(f"   Perfis encontrados: {', '.join(result['profiles'])}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '6':
            email = input("\n📧 Digite o email: ").strip()
            if email:
                print("\nVerificando no BreachDirectory...")
                result = free_checker.check_breach_directory(email)
                if result.get("error"):
                    print(f"❌ Erro: {result['error']}")
                elif result.get("found"):
                    print(f"\n⚠️ EMAIL ENCONTRADO EM {result.get('count', 0)} BREACH(ES)!")
                    breaches = result.get("breaches", [])
                    for b in breaches[:20]:
                        if isinstance(b, dict):
                            print(f"   • {b.get('name', b)}")
                        else:
                            print(f"   • {b}")
                else:
                    print("✅ Email não encontrado em breaches conhecidos")
            input("\nPressione Enter para continuar...")
        
        elif choice == '7':
            email = input("\n📧 Digite o email: ").strip()
            if email:
                print("\nVerificando no LeakCheck (versão gratuita)...")
                result = free_checker.check_leakcheck_free(email)
                if result.get("error"):
                    print(f"❌ Erro: {result['error']}")
                elif result.get("found"):
                    print(f"\n⚠️ EMAIL ENCONTRADO EM {result.get('count', 0)} LEAK(S)!")
                    if result.get("sources"):
                        print("   Fontes:")
                        for s in result.get("sources", [])[:10]:
                            print(f"   • {s}")
                else:
                    print("✅ Email não encontrado em leaks conhecidos")
            input("\nPressione Enter para continuar...")
        
        elif choice == '8':
            print("\n📥 WORDLISTS DISPONÍVEIS:\n")
            listas = downloader.list_available_seclists()
            for i, nome in enumerate(listas, 1):
                info = downloader.WORDLISTS[nome]
                print(f"  [{i}] {info['name']} ({info['size']})")
            
            print(f"\n  [0] Voltar")
            
            dl_choice = input("\nEscolha: ").strip()
            
            if dl_choice.isdigit() and 1 <= int(dl_choice) <= len(listas):
                lista = listas[int(dl_choice) - 1]
                downloader.download_seclist(lista)
            
            input("\nPressione Enter para continuar...")
        
        elif choice == '9':
            print("\n⚙️ CONFIGURAÇÃO DE APIs PREMIUM\n")
            print("Para resultados mais completos, configure API keys:")
            print("\n  [1] LeakCheck.io - $14.99/mês")
            print("      https://leakcheck.io/")
            print("\n  [2] DeHashed - $5.49/semana")
            print("      https://dehashed.com/")
            print("\n  [3] Snusbase - $29.99/mês")
            print("      https://snusbase.com/")
            print("\n  [4] IntelX - Gratuito limitado")
            print("      https://intelx.io/signup")
            print("\n  [5] HIBP (emails) - $3.95/mês")
            print("      https://haveibeenpwned.com/API/Key")
            
            input("\nPressione Enter para continuar...")
        
        elif choice == '0':
            break


if __name__ == '__main__':
    interactive_menu()
