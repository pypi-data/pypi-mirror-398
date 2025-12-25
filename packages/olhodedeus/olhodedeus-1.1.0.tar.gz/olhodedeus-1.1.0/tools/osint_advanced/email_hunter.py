#!/usr/bin/env python3
"""
Email Hunter - Descoberta e validação de emails
Parte do toolkit Olho de Deus
"""

import os
import sys
import re
import json
import socket
import smtplib
import dns.resolver
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin
import hashlib

try:
    import requests
except ImportError:
    requests = None


@dataclass
class EmailInfo:
    """Informações de um email."""
    email: str
    domain: str
    valid: bool
    mx_exists: bool
    smtp_valid: Optional[bool]
    source: str
    first_name: Optional[str]
    last_name: Optional[str]
    
    def to_dict(self) -> Dict:
        return {
            "email": self.email,
            "domain": self.domain,
            "valid": self.valid,
            "mx_exists": self.mx_exists,
            "smtp_valid": self.smtp_valid,
            "source": self.source,
            "first_name": self.first_name,
            "last_name": self.last_name
        }


class EmailGenerator:
    """Gerador de padrões de email."""
    
    # Padrões comuns de email corporativo
    PATTERNS = [
        "{first}.{last}",           # john.doe
        "{first}{last}",            # johndoe
        "{f}{last}",                # jdoe
        "{first}.{l}",              # john.d
        "{first}_{last}",           # john_doe
        "{last}.{first}",           # doe.john
        "{last}{first}",            # doejohn
        "{first}",                  # john
        "{last}",                   # doe
        "{f}.{last}",               # j.doe
        "{first}{l}",               # johnd
        "{l}{first}",               # djohn
        "{first}-{last}",           # john-doe
    ]
    
    @classmethod
    def generate(cls, first_name: str, last_name: str, domain: str) -> List[str]:
        """Gera variações de email."""
        first = first_name.lower().strip()
        last = last_name.lower().strip()
        f = first[0] if first else ""
        l = last[0] if last else ""
        
        emails = []
        for pattern in cls.PATTERNS:
            try:
                email_local = pattern.format(
                    first=first,
                    last=last,
                    f=f,
                    l=l
                )
                email = f"{email_local}@{domain}"
                emails.append(email)
            except Exception:
                pass
        
        return list(set(emails))


class EmailValidator:
    """Validador de emails."""
    
    # Regex para validação básica
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Provedores gratuitos comuns
    FREE_PROVIDERS = [
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
        "live.com", "aol.com", "protonmail.com", "icloud.com",
        "mail.com", "zoho.com", "yandex.com"
    ]
    
    # Domínios descartáveis conhecidos
    DISPOSABLE_DOMAINS = [
        "tempmail.com", "guerrillamail.com", "10minutemail.com",
        "mailinator.com", "throwaway.email", "fakeinbox.com",
        "temp-mail.org", "trashmail.com", "maildrop.cc"
    ]
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self._mx_cache = {}
    
    def validate_format(self, email: str) -> bool:
        """Valida formato do email."""
        return bool(self.EMAIL_REGEX.match(email))
    
    def check_mx(self, domain: str) -> List[str]:
        """Verifica registros MX do domínio."""
        if domain in self._mx_cache:
            return self._mx_cache[domain]
        
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            servers = [str(r.exchange).rstrip('.') for r in mx_records]
            self._mx_cache[domain] = servers
            return servers
        except Exception:
            self._mx_cache[domain] = []
            return []
    
    def verify_smtp(self, email: str) -> Optional[bool]:
        """Verifica email via SMTP (pode ser bloqueado)."""
        domain = email.split('@')[1]
        mx_servers = self.check_mx(domain)
        
        if not mx_servers:
            return None
        
        for mx in mx_servers[:2]:  # Tentar primeiros 2 MX
            try:
                smtp = smtplib.SMTP(timeout=self.timeout)
                smtp.connect(mx)
                smtp.helo('check.local')
                smtp.mail('test@check.local')
                code, _ = smtp.rcpt(email)
                smtp.quit()
                
                # 250 = OK, 251 = User not local
                return code == 250 or code == 251
            except Exception:
                continue
        
        return None
    
    def is_free_provider(self, email: str) -> bool:
        """Verifica se é provedor gratuito."""
        domain = email.split('@')[1].lower()
        return domain in self.FREE_PROVIDERS
    
    def is_disposable(self, email: str) -> bool:
        """Verifica se é email descartável."""
        domain = email.split('@')[1].lower()
        return domain in self.DISPOSABLE_DOMAINS
    
    def get_gravatar(self, email: str) -> Optional[str]:
        """Retorna URL do Gravatar se existir."""
        email_hash = hashlib.md5(email.lower().encode()).hexdigest()
        gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
        
        if requests:
            try:
                r = requests.head(gravatar_url, timeout=5)
                if r.status_code == 200:
                    return gravatar_url
            except Exception:
                pass
        
        return None
    
    def full_validate(self, email: str) -> Dict:
        """Validação completa de email."""
        result = {
            "email": email,
            "valid_format": False,
            "domain": None,
            "mx_exists": False,
            "mx_servers": [],
            "smtp_valid": None,
            "is_free": False,
            "is_disposable": False,
            "has_gravatar": False,
            "score": 0
        }
        
        # Formato
        if not self.validate_format(email):
            return result
        
        result["valid_format"] = True
        result["domain"] = email.split('@')[1]
        result["score"] += 20
        
        # MX
        mx_servers = self.check_mx(result["domain"])
        result["mx_exists"] = bool(mx_servers)
        result["mx_servers"] = mx_servers
        if result["mx_exists"]:
            result["score"] += 30
        
        # SMTP
        result["smtp_valid"] = self.verify_smtp(email)
        if result["smtp_valid"]:
            result["score"] += 30
        elif result["smtp_valid"] is False:
            result["score"] -= 50
        
        # Tipo
        result["is_free"] = self.is_free_provider(email)
        result["is_disposable"] = self.is_disposable(email)
        
        if result["is_disposable"]:
            result["score"] -= 30
        
        # Gravatar
        gravatar = self.get_gravatar(email)
        result["has_gravatar"] = bool(gravatar)
        if result["has_gravatar"]:
            result["score"] += 20
        
        return result


class EmailHarvester:
    """Coleta emails de fontes públicas."""
    
    # Regex para extrair emails
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session() if requests else None
        if self.session:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
    
    def scrape_website(self, url: str) -> Set[str]:
        """Extrai emails de um website."""
        emails = set()
        
        if not self.session:
            return emails
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            response = self.session.get(url, timeout=self.timeout, verify=False)
            found = self.EMAIL_PATTERN.findall(response.text)
            
            for email in found:
                email = email.lower()
                # Filtrar emails de imagem/css
                if not any(ext in email for ext in ['.png', '.jpg', '.gif', '.css', '.js']):
                    emails.add(email)
        except Exception:
            pass
        
        return emails
    
    def search_google(self, domain: str, max_results: int = 50) -> Set[str]:
        """Busca emails relacionados a um domínio no Google."""
        emails = set()
        
        # Nota: Em produção, usar Google Custom Search API
        # Esta é uma implementação simplificada
        
        queries = [
            f'site:{domain} email',
            f'"@{domain}"',
            f'"{domain}" contact email',
        ]
        
        # Implementação básica - em produção usar API
        for query in queries:
            search_url = f"https://www.google.com/search?q={query}&num=100"
            try:
                response = self.session.get(search_url, timeout=self.timeout)
                found = self.EMAIL_PATTERN.findall(response.text)
                for email in found:
                    if domain in email.lower():
                        emails.add(email.lower())
            except Exception:
                pass
        
        return emails
    
    def scrape_linkedin_pattern(self, company_name: str, domain: str) -> Dict:
        """Identifica padrão de emails de uma empresa."""
        # Em produção, usar LinkedIn API ou scraping avançado
        
        return {
            "company": company_name,
            "domain": domain,
            "likely_patterns": [
                f"{{first}}.{{last}}@{domain}",
                f"{{first}}{{last}}@{domain}",
                f"{{f}}{{last}}@{domain}",
            ],
            "note": "Use ferramentas especializadas para descoberta real"
        }


class EmailHunter:
    """Interface principal do Email Hunter."""
    
    def __init__(self):
        self.generator = EmailGenerator()
        self.validator = EmailValidator()
        self.harvester = EmailHarvester()
    
    def find_person_email(self, first_name: str, last_name: str, 
                          domain: str, verify: bool = True) -> List[EmailInfo]:
        """Encontra possíveis emails de uma pessoa."""
        results = []
        
        # Gerar variações
        emails = self.generator.generate(first_name, last_name, domain)
        
        # Verificar MX primeiro
        mx_exists = bool(self.validator.check_mx(domain))
        
        for email in emails:
            smtp_valid = None
            if verify:
                smtp_valid = self.validator.verify_smtp(email)
            
            results.append(EmailInfo(
                email=email,
                domain=domain,
                valid=mx_exists,
                mx_exists=mx_exists,
                smtp_valid=smtp_valid,
                source="generated",
                first_name=first_name,
                last_name=last_name
            ))
        
        # Ordenar por probabilidade (verificados primeiro)
        results.sort(key=lambda x: (x.smtp_valid is True, x.smtp_valid is not False), reverse=True)
        
        return results
    
    def harvest_domain(self, domain: str) -> Dict:
        """Coleta todos os emails de um domínio."""
        results = {
            "domain": domain,
            "mx_servers": self.validator.check_mx(domain),
            "emails_found": [],
            "sources": []
        }
        
        all_emails = set()
        
        # Scrape website principal
        website_emails = self.harvester.scrape_website(f"https://{domain}")
        if website_emails:
            all_emails.update(website_emails)
            results["sources"].append("website")
        
        # Páginas comuns
        common_pages = ["/contact", "/about", "/team", "/about-us", "/kontakt"]
        for page in common_pages:
            page_emails = self.harvester.scrape_website(f"https://{domain}{page}")
            if page_emails:
                all_emails.update(page_emails)
        
        # Filtrar apenas emails do domínio
        domain_emails = [e for e in all_emails if domain in e]
        results["emails_found"] = list(domain_emails)
        
        return results


def interactive_menu():
    """Menu interativo do Email Hunter."""
    hunter = EmailHunter()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║             📧 EMAIL HUNTER - Olho de Deus                   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔍 Encontrar Email de Pessoa                            ║
║  [2] ✅ Validar Email                                        ║
║  [3] 🌐 Coletar Emails de Domínio                            ║
║  [4] 📊 Validar Lista de Emails                              ║
║  [5] 🔑 Gerar Padrões de Email                               ║
║  [6] 📋 Verificar MX de Domínio                              ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Encontrar Email de Pessoa ===")
            first = input("Primeiro nome: ").strip()
            last = input("Sobrenome: ").strip()
            domain = input("Domínio (ex: empresa.com): ").strip()
            verify = input("Verificar via SMTP? (s/n, pode ser lento): ").lower() == 's'
            
            if not first or not last or not domain:
                continue
            
            print(f"\nGerando e verificando emails...")
            results = hunter.find_person_email(first, last, domain, verify)
            
            print(f"\n📧 Possíveis emails para {first} {last}:")
            for r in results[:10]:
                status = ""
                if r.smtp_valid is True:
                    status = "✅ VERIFICADO"
                elif r.smtp_valid is False:
                    status = "❌ INVÁLIDO"
                else:
                    status = "❓ NÃO VERIFICADO"
                
                print(f"   {r.email} {status}")
        
        elif escolha == '2':
            print("\n=== Validar Email ===")
            email = input("Email: ").strip()
            
            if not email:
                continue
            
            print(f"\nValidando {email}...")
            result = hunter.validator.full_validate(email)
            
            print(f"\n📊 Resultado:")
            print(f"   Formato válido: {'✅' if result['valid_format'] else '❌'}")
            print(f"   Domínio: {result['domain']}")
            print(f"   MX existe: {'✅' if result['mx_exists'] else '❌'}")
            
            if result['mx_servers']:
                print(f"   Servidores MX: {', '.join(result['mx_servers'][:3])}")
            
            if result['smtp_valid'] is True:
                print(f"   SMTP verificado: ✅ VÁLIDO")
            elif result['smtp_valid'] is False:
                print(f"   SMTP verificado: ❌ INVÁLIDO")
            else:
                print(f"   SMTP verificado: ❓ Não testável")
            
            print(f"   Provedor gratuito: {'Sim' if result['is_free'] else 'Não'}")
            print(f"   Email descartável: {'⚠️ SIM' if result['is_disposable'] else 'Não'}")
            print(f"   Gravatar: {'Sim' if result['has_gravatar'] else 'Não'}")
            print(f"\n   Score: {result['score']}/100")
        
        elif escolha == '3':
            print("\n=== Coletar Emails de Domínio ===")
            domain = input("Domínio: ").strip()
            
            if not domain:
                continue
            
            print(f"\nColetando emails de {domain}...")
            result = hunter.harvest_domain(domain)
            
            print(f"\n📧 Resultados para {domain}:")
            
            if result['mx_servers']:
                print(f"   MX: {', '.join(result['mx_servers'][:3])}")
            
            if result['emails_found']:
                print(f"\n   📬 {len(result['emails_found'])} emails encontrados:")
                for email in result['emails_found'][:20]:
                    print(f"      • {email}")
            else:
                print(f"\n   Nenhum email encontrado publicamente")
            
            save = input("\nSalvar resultados? (s/n): ").lower()
            if save == 's':
                with open(f"emails_{domain.replace('.', '_')}.json", 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"✅ Salvo em emails_{domain.replace('.', '_')}.json")
        
        elif escolha == '4':
            print("\n=== Validar Lista de Emails ===")
            print("Cole os emails (um por linha, linha vazia para terminar):")
            
            emails = []
            while True:
                e = input("  > ").strip()
                if not e:
                    break
                emails.append(e)
            
            if not emails:
                continue
            
            print(f"\nValidando {len(emails)} emails...\n")
            
            valid = []
            invalid = []
            unknown = []
            
            for email in emails:
                result = hunter.validator.full_validate(email)
                
                if not result['valid_format'] or not result['mx_exists']:
                    invalid.append(email)
                elif result['smtp_valid'] is True:
                    valid.append(email)
                elif result['smtp_valid'] is False:
                    invalid.append(email)
                else:
                    unknown.append(email)
                
                status = "✅" if result['mx_exists'] else "❌"
                print(f"   {status} {email}")
            
            print(f"\n📊 Resumo:")
            print(f"   ✅ Válidos: {len(valid)}")
            print(f"   ❌ Inválidos: {len(invalid)}")
            print(f"   ❓ Incertos: {len(unknown)}")
        
        elif escolha == '5':
            print("\n=== Gerar Padrões de Email ===")
            first = input("Primeiro nome: ").strip()
            last = input("Sobrenome: ").strip()
            domain = input("Domínio: ").strip()
            
            if not first or not last or not domain:
                continue
            
            emails = hunter.generator.generate(first, last, domain)
            
            print(f"\n📧 Padrões gerados para {first} {last}:")
            for email in emails:
                print(f"   • {email}")
        
        elif escolha == '6':
            print("\n=== Verificar MX ===")
            domain = input("Domínio: ").strip()
            
            if not domain:
                continue
            
            mx_servers = hunter.validator.check_mx(domain)
            
            if mx_servers:
                print(f"\n📬 Servidores MX de {domain}:")
                for i, mx in enumerate(mx_servers, 1):
                    print(f"   {i}. {mx}")
            else:
                print(f"\n❌ Nenhum registro MX encontrado para {domain}")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
