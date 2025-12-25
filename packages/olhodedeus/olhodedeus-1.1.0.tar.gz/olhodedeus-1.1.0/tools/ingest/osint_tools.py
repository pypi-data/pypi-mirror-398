#!/usr/bin/env python3
"""
osint_tools.py

Ferramentas OSINT integradas para busca de informações.
Integra com ferramentas externas e APIs públicas.

AVISO LEGAL: Use apenas para fins de pesquisa de segurança e verificação
de suas próprias informações. O uso indevido é ilegal.
"""
import os
import sys
import json
import subprocess
import platform
import hashlib
import re
import time
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime


def get_python_cmd() -> str:
    """Retorna o comando Python correto para o sistema."""
    if platform.system() == 'Windows':
        venv_python = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.venv', 'Scripts', 'python.exe')
        if os.path.exists(venv_python):
            return venv_python
        return 'python'
    return 'python3'


class HoleheTool:
    """
    Wrapper para holehe - verifica em quais sites um email está registrado.
    GitHub: https://github.com/megadose/holehe
    """
    
    def __init__(self):
        self.installed = self._check_installed()
    
    def _check_installed(self) -> bool:
        try:
            result = subprocess.run([get_python_cmd(), '-m', 'holehe', '--help'],
                                   capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def install(self) -> bool:
        """Instala o holehe via pip."""
        try:
            print("📦 Instalando holehe...")
            result = subprocess.run([get_python_cmd(), '-m', 'pip', 'install', 'holehe'],
                                   capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                self.installed = True
                print("✅ holehe instalado!")
                return True
            else:
                print(f"❌ Erro: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
    
    def check_email(self, email: str) -> Dict:
        """Verifica em quais sites o email está registrado."""
        if not self.installed:
            return {"error": "holehe não instalado. Use install() primeiro."}
        
        try:
            print(f"🔍 Verificando {email} com holehe...")
            result = subprocess.run(
                [get_python_cmd(), '-m', 'holehe', email, '--only-used', '-NP'],
                capture_output=True, text=True, timeout=120
            )
            
            # Parse output
            lines = result.stdout.strip().split('\n')
            services_found = []
            
            for line in lines:
                if '[+]' in line:
                    # Extrair nome do serviço
                    match = re.search(r'\[\+\]\s+(\w+)', line)
                    if match:
                        services_found.append(match.group(1))
            
            return {
                "email": email,
                "services_found": services_found,
                "count": len(services_found),
                "raw_output": result.stdout
            }
        except subprocess.TimeoutExpired:
            return {"error": "Timeout - busca demorou muito"}
        except Exception as e:
            return {"error": str(e)}


class SherlockTool:
    """
    Wrapper para sherlock - busca username em redes sociais.
    GitHub: https://github.com/sherlock-project/sherlock
    """
    
    def __init__(self):
        self.installed = self._check_installed()
    
    def _check_installed(self) -> bool:
        try:
            result = subprocess.run([get_python_cmd(), '-m', 'sherlock_project', '--help'],
                                   capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            try:
                result = subprocess.run(['sherlock', '--help'],
                                       capture_output=True, text=True, timeout=10)
                return result.returncode == 0
            except:
                return False
    
    def install(self) -> bool:
        """Instala o sherlock via pip."""
        try:
            print("📦 Instalando sherlock...")
            result = subprocess.run([get_python_cmd(), '-m', 'pip', 'install', 'sherlock-project'],
                                   capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                self.installed = True
                print("✅ sherlock instalado!")
                return True
            else:
                print(f"❌ Erro: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
    
    def search_username(self, username: str, output_dir: str = None) -> Dict:
        """Busca username em múltiplas plataformas."""
        if not self.installed:
            return {"error": "sherlock não instalado. Use install() primeiro."}
        
        cmd = [get_python_cmd(), '-m', 'sherlock_project', username, '--print-found']
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            cmd.extend(['--output', os.path.join(output_dir, f'{username}.txt')])
        
        try:
            print(f"🔍 Buscando {username} com sherlock...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Parse output
            lines = result.stdout.strip().split('\n')
            sites_found = []
            
            for line in lines:
                if 'http' in line and '[+]' in line:
                    # Extrair URL
                    match = re.search(r'(https?://\S+)', line)
                    if match:
                        sites_found.append(match.group(1))
            
            return {
                "username": username,
                "sites_found": sites_found,
                "count": len(sites_found),
                "raw_output": result.stdout
            }
        except subprocess.TimeoutExpired:
            return {"error": "Timeout - busca demorou muito"}
        except Exception as e:
            return {"error": str(e)}


class PhoneInfogaTool:
    """
    Wrapper para PhoneInfoga - OSINT de números de telefone.
    GitHub: https://github.com/sundowndev/phoneinfoga
    """
    
    def __init__(self):
        self.installed = self._check_installed()
    
    def _check_installed(self) -> bool:
        try:
            result = subprocess.run(['phoneinfoga', 'version'],
                                   capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def scan_number(self, phone: str) -> Dict:
        """Escaneia número de telefone."""
        if not self.installed:
            return {"error": "phoneinfoga não instalado. Baixe em https://github.com/sundowndev/phoneinfoga"}
        
        try:
            print(f"🔍 Escaneando {phone} com phoneinfoga...")
            result = subprocess.run(
                ['phoneinfoga', 'scan', '-n', phone],
                capture_output=True, text=True, timeout=60
            )
            
            return {
                "phone": phone,
                "raw_output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {"error": str(e)}


class EmailRepChecker:
    """
    Verificação de reputação de email usando emailrep.io (gratuito limitado).
    """
    
    def __init__(self):
        self.base_url = "https://emailrep.io"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def check_email(self, email: str) -> Dict:
        """Verifica reputação do email."""
        url = f"{self.base_url}/{email}"
        
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "email": email,
                    "reputation": data.get("reputation", "unknown"),
                    "suspicious": data.get("suspicious", False),
                    "references": data.get("references", 0),
                    "blacklisted": data.get("details", {}).get("blacklisted", False),
                    "malicious_activity": data.get("details", {}).get("malicious_activity", False),
                    "data_breach": data.get("details", {}).get("data_breach", False),
                    "credentials_leaked": data.get("details", {}).get("credentials_leaked", False),
                    "spoofable": data.get("details", {}).get("spoofable", False),
                    "spam": data.get("details", {}).get("spam", False),
                    "free_provider": data.get("details", {}).get("free_provider", False),
                    "disposable": data.get("details", {}).get("disposable", False),
                    "deliverable": data.get("details", {}).get("deliverable", True),
                    "accept_all": data.get("details", {}).get("accept_all", False),
                    "valid_mx": data.get("details", {}).get("valid_mx", True),
                    "profiles": data.get("details", {}).get("profiles", []),
                    "domain_exists": data.get("details", {}).get("domain_exists", True),
                    "domain_reputation": data.get("details", {}).get("domain_reputation", "unknown"),
                    "new_domain": data.get("details", {}).get("new_domain", False),
                    "days_since_domain_creation": data.get("details", {}).get("days_since_domain_creation", -1),
                    "last_seen": data.get("details", {}).get("last_seen", "never")
                }
            elif resp.status_code == 429:
                return {"error": "Rate limit atingido. Tente novamente mais tarde."}
            else:
                return {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}


class DNSDumpsterTool:
    """
    Busca DNS usando DNSDumpster (gratuito).
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def lookup_domain(self, domain: str) -> Dict:
        """Busca informações DNS do domínio."""
        # DNSDumpster precisa de token CSRF
        try:
            # Primeira request para pegar o token
            resp = self.session.get("https://dnsdumpster.com/", timeout=15)
            
            # Extrair CSRF token
            match = re.search(r'csrfmiddlewaretoken.*?value="([^"]+)"', resp.text)
            if not match:
                return {"error": "Não foi possível obter CSRF token"}
            
            csrf_token = match.group(1)
            
            # Fazer a busca
            resp = self.session.post(
                "https://dnsdumpster.com/",
                data={
                    'csrfmiddlewaretoken': csrf_token,
                    'targetip': domain
                },
                headers={'Referer': 'https://dnsdumpster.com/'},
                timeout=30
            )
            
            if resp.status_code == 200:
                # Parse básico - extrair IPs e subdomínios
                ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', resp.text)
                subdomains = re.findall(rf'([a-zA-Z0-9\-]+\.{re.escape(domain)})', resp.text)
                
                return {
                    "domain": domain,
                    "ips_found": list(set(ips)),
                    "subdomains": list(set(subdomains)),
                    "success": True
                }
            else:
                return {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}


class LeakedDatabaseSearch:
    """
    Busca em fontes públicas de pesquisa de segurança.
    """
    
    # APIs e fontes públicas conhecidas
    PUBLIC_APIS = {
        "hibp_password": {
            "name": "HIBP Pwned Passwords",
            "url": "https://api.pwnedpasswords.com/range/",
            "free": True,
            "description": "Verificação de senhas com k-Anonymity"
        },
        "emailrep": {
            "name": "EmailRep.io",
            "url": "https://emailrep.io/",
            "free": True,
            "description": "Reputação de email"
        },
        "hunter": {
            "name": "Hunter.io",
            "url": "https://hunter.io/",
            "free": False,
            "description": "Busca de emails por domínio"
        }
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def check_password_hibp(self, password: str) -> Dict:
        """Verifica senha no HIBP usando k-Anonymity."""
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
                            "found": True,
                            "count": int(parts[1]),
                            "sha1": sha1_hash,
                            "password_truncated": password[:3] + "***"
                        }
                return {"found": False, "sha1": sha1_hash}
        except Exception as e:
            return {"error": str(e)}
        
        return {"found": False}
    
    def search_pastebin_google(self, query: str) -> List[str]:
        """Busca pastes via Google (dork)."""
        # Isso é apenas uma sugestão de dork, não executa automaticamente
        dorks = [
            f'site:pastebin.com "{query}"',
            f'site:ghostbin.com "{query}"',
            f'site:hastebin.com "{query}"',
            f'site:paste.ee "{query}"',
        ]
        return dorks


class OSINTAggregator:
    """
    Agregador de todas as ferramentas OSINT.
    """
    
    def __init__(self):
        self.holehe = HoleheTool()
        self.sherlock = SherlockTool()
        self.phoneinfoga = PhoneInfogaTool()
        self.emailrep = EmailRepChecker()
        self.dnsdumpster = DNSDumpsterTool()
        self.leakdb = LeakedDatabaseSearch()
    
    def full_email_scan(self, email: str, password: str = None) -> Dict:
        """Scan completo de email usando todas as ferramentas."""
        results = {
            "email": email,
            "timestamp": datetime.now().isoformat(),
            "scans": {}
        }
        
        print("\n" + "="*60)
        print(f"🔍 SCAN COMPLETO DE EMAIL: {email}")
        print("="*60 + "\n")
        
        # 1. EmailRep
        print("📧 [1/4] Verificando reputação (EmailRep)...")
        results["scans"]["emailrep"] = self.emailrep.check_email(email)
        
        if results["scans"]["emailrep"].get("error"):
            print(f"   ❌ Erro: {results['scans']['emailrep']['error']}")
        else:
            rep = results["scans"]["emailrep"]
            print(f"   Reputação: {rep.get('reputation', 'N/A')}")
            if rep.get("data_breach"):
                print("   ⚠️  Email aparece em data breaches!")
            if rep.get("credentials_leaked"):
                print("   ⚠️  Credenciais vazadas!")
        
        # 2. HIBP Password (se fornecida)
        if password:
            print("\n🔐 [2/4] Verificando senha (HIBP)...")
            results["scans"]["hibp_password"] = self.leakdb.check_password_hibp(password)
            
            if results["scans"]["hibp_password"].get("found"):
                count = results["scans"]["hibp_password"]["count"]
                print(f"   ⚠️  SENHA VAZADA! Encontrada {count:,}x em breaches!")
            elif results["scans"]["hibp_password"].get("error"):
                print(f"   ❌ Erro: {results['scans']['hibp_password']['error']}")
            else:
                print("   ✅ Senha não encontrada em breaches")
        else:
            print("\n🔐 [2/4] Senha não fornecida - pulando verificação HIBP")
        
        # 3. Holehe (se instalado)
        print("\n🌐 [3/4] Verificando serviços registrados (Holehe)...")
        if self.holehe.installed:
            results["scans"]["holehe"] = self.holehe.check_email(email)
            if results["scans"]["holehe"].get("services_found"):
                count = len(results["scans"]["holehe"]["services_found"])
                print(f"   Encontrado em {count} serviços")
                for svc in results["scans"]["holehe"]["services_found"][:10]:
                    print(f"     • {svc}")
                if count > 10:
                    print(f"     ... e mais {count - 10}")
            elif results["scans"]["holehe"].get("error"):
                print(f"   ❌ Erro: {results['scans']['holehe']['error']}")
            else:
                print("   Nenhum serviço encontrado")
        else:
            print("   ⚠️  holehe não instalado. Use 'pip install holehe'")
            results["scans"]["holehe"] = {"error": "Não instalado"}
        
        # 4. Extrair domínio e verificar
        domain = email.split('@')[-1]
        print(f"\n🌍 [4/4] Verificando domínio: {domain}...")
        results["scans"]["domain"] = self.dnsdumpster.lookup_domain(domain)
        
        if results["scans"]["domain"].get("subdomains"):
            print(f"   Subdomínios encontrados: {len(results['scans']['domain']['subdomains'])}")
        
        print("\n" + "="*60)
        print("✅ SCAN COMPLETO")
        print("="*60)
        
        return results
    
    def full_username_scan(self, username: str) -> Dict:
        """Scan completo de username."""
        results = {
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "scans": {}
        }
        
        print("\n" + "="*60)
        print(f"🔍 SCAN DE USERNAME: {username}")
        print("="*60 + "\n")
        
        # Sherlock
        print("🕵️ Verificando redes sociais (Sherlock)...")
        if self.sherlock.installed:
            results["scans"]["sherlock"] = self.sherlock.search_username(username)
            if results["scans"]["sherlock"].get("sites_found"):
                count = len(results["scans"]["sherlock"]["sites_found"])
                print(f"   Encontrado em {count} sites:")
                for site in results["scans"]["sherlock"]["sites_found"][:15]:
                    print(f"     • {site}")
                if count > 15:
                    print(f"     ... e mais {count - 15}")
        else:
            print("   ⚠️  sherlock não instalado. Use 'pip install sherlock-project'")
            results["scans"]["sherlock"] = {"error": "Não instalado"}
        
        return results
    
    def quick_password_check(self, password: str) -> Dict:
        """Verificação rápida de senha no HIBP."""
        return self.leakdb.check_password_hibp(password)


def interactive_menu():
    """Menu interativo para OSINT."""
    osint = OSINTAggregator()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║       🕵️ OSINT TOOLKIT - Ferramentas de Investigação        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 📧 Scan completo de EMAIL                               ║
║  [2] 👤 Scan de USERNAME (redes sociais)                     ║
║  [3] 🔐 Verificar SENHA (HIBP)                               ║
║  [4] 📱 Verificar reputação de EMAIL (EmailRep)              ║
║  [5] 🌍 Lookup de DOMÍNIO                                    ║
║                                                              ║
║  [6] 📦 Instalar ferramentas OSINT                           ║
║  [7] 📋 Ver status das ferramentas                           ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            email = input("\nEmail: ").strip()
            password = input("Senha (Enter para pular): ").strip() or None
            if email:
                results = osint.full_email_scan(email, password)
                
                save = input("\nSalvar resultados? (s/n): ").strip().lower()
                if save == 's':
                    os.makedirs("data/osint_results", exist_ok=True)
                    filename = f"data/osint_results/email_{email.replace('@', '_at_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
                    print(f"✅ Salvo: {filename}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '2':
            username = input("\nUsername: ").strip()
            if username:
                results = osint.full_username_scan(username)
            input("\nPressione Enter para continuar...")
        
        elif choice == '3':
            password = input("\nSenha para verificar: ").strip()
            if password:
                result = osint.quick_password_check(password)
                if result.get("found"):
                    print(f"\n⚠️  SENHA VAZADA!")
                    print(f"   Encontrada {result['count']:,}x em breaches")
                    print(f"   SHA1: {result['sha1']}")
                elif result.get("error"):
                    print(f"\n❌ Erro: {result['error']}")
                else:
                    print("\n✅ Senha NÃO encontrada em breaches conhecidos")
            input("\nPressione Enter para continuar...")
        
        elif choice == '4':
            email = input("\nEmail: ").strip()
            if email:
                result = osint.emailrep.check_email(email)
                if result.get("error"):
                    print(f"\n❌ Erro: {result['error']}")
                else:
                    print(f"\n📧 Reputação de {email}:")
                    print(f"   Reputação: {result.get('reputation', 'N/A')}")
                    print(f"   Suspeito: {'Sim' if result.get('suspicious') else 'Não'}")
                    print(f"   Data Breach: {'Sim ⚠️' if result.get('data_breach') else 'Não'}")
                    print(f"   Credenciais Vazadas: {'Sim ⚠️' if result.get('credentials_leaked') else 'Não'}")
                    print(f"   Spam: {'Sim' if result.get('spam') else 'Não'}")
                    print(f"   Descartável: {'Sim' if result.get('disposable') else 'Não'}")
                    print(f"   Provedor Gratuito: {'Sim' if result.get('free_provider') else 'Não'}")
                    if result.get("profiles"):
                        print(f"   Perfis: {', '.join(result['profiles'])}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '5':
            domain = input("\nDomínio (ex: empresa.com): ").strip()
            if domain:
                print(f"\n🔍 Buscando informações de {domain}...")
                result = osint.dnsdumpster.lookup_domain(domain)
                if result.get("error"):
                    print(f"\n❌ Erro: {result['error']}")
                else:
                    if result.get("subdomains"):
                        print(f"\n📌 Subdomínios encontrados ({len(result['subdomains'])}):")
                        for sub in result['subdomains'][:20]:
                            print(f"   • {sub}")
                    if result.get("ips_found"):
                        print(f"\n🌐 IPs encontrados ({len(result['ips_found'])}):")
                        for ip in list(set(result['ips_found']))[:20]:
                            print(f"   • {ip}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '6':
            print("\n📦 Instalação de Ferramentas OSINT\n")
            print("  [1] holehe - Verificar serviços por email")
            print("  [2] sherlock - Buscar username em redes sociais")
            print("  [3] maigret - Fork do sherlock com mais sites")
            print("  [4] h8mail - Email OSINT")
            print("  [5] Todas as acima")
            print("  [0] Voltar")
            
            inst_choice = input("\nOpção: ").strip()
            
            if inst_choice == '1':
                osint.holehe.install()
            elif inst_choice == '2':
                osint.sherlock.install()
            elif inst_choice == '3':
                print("Instalando maigret...")
                subprocess.run([get_python_cmd(), '-m', 'pip', 'install', 'maigret'])
            elif inst_choice == '4':
                print("Instalando h8mail...")
                subprocess.run([get_python_cmd(), '-m', 'pip', 'install', 'h8mail'])
            elif inst_choice == '5':
                osint.holehe.install()
                osint.sherlock.install()
                subprocess.run([get_python_cmd(), '-m', 'pip', 'install', 'maigret', 'h8mail'])
            
            input("\nPressione Enter para continuar...")
        
        elif choice == '7':
            print("\n📋 Status das Ferramentas:\n")
            print(f"  holehe:     {'✅ Instalado' if osint.holehe.installed else '❌ Não instalado'}")
            print(f"  sherlock:   {'✅ Instalado' if osint.sherlock.installed else '❌ Não instalado'}")
            print(f"  phoneinfoga: {'✅ Instalado' if osint.phoneinfoga.installed else '❌ Não instalado'}")
            print(f"\n  EmailRep:   ✅ API Online (gratuito limitado)")
            print(f"  HIBP:       ✅ API Online (gratuito)")
            print(f"  DNSDumpster: ✅ Online (gratuito)")
            
            input("\nPressione Enter para continuar...")
        
        elif choice == '0':
            break


if __name__ == '__main__':
    interactive_menu()
