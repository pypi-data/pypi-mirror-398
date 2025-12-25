#!/usr/bin/env python3
"""
Cookie Analyzer - Análise de segurança de cookies e sessões
Parte do toolkit Olho de Deus
"""

import os
import sys
import re
import json
import base64
import hashlib
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    requests = None


@dataclass
class CookieInfo:
    """Informações de um cookie."""
    name: str
    value: str
    domain: Optional[str]
    path: Optional[str]
    expires: Optional[str]
    secure: bool
    httponly: bool
    samesite: Optional[str]
    size: int
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "value": self.value,
            "domain": self.domain,
            "path": self.path,
            "expires": self.expires,
            "secure": self.secure,
            "httponly": self.httponly,
            "samesite": self.samesite,
            "size": self.size
        }


@dataclass 
class CookieVulnerability:
    """Vulnerabilidade de cookie."""
    cookie_name: str
    issue: str
    severity: str
    description: str
    recommendation: str
    
    def to_dict(self) -> Dict:
        return {
            "cookie_name": self.cookie_name,
            "issue": self.issue,
            "severity": self.severity,
            "description": self.description,
            "recommendation": self.recommendation
        }


class SessionTokenAnalyzer:
    """Analisador de tokens de sessão."""
    
    # Padrões de session tokens
    SESSION_PATTERNS = {
        "php_sessid": r'^[a-f0-9]{26,32}$',
        "asp_net_sessionid": r'^[a-z0-9]{24}$',
        "jsessionid": r'^[A-F0-9]{32}$',
        "cfid": r'^\d+$',
        "jwt": r'^eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$',
        "base64": r'^[A-Za-z0-9+/=]+$',
        "uuid": r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    }
    
    # Algoritmos de hash por comprimento
    HASH_LENGTHS = {
        32: "MD5",
        40: "SHA-1",
        64: "SHA-256",
        128: "SHA-512",
    }
    
    def analyze(self, token: str) -> Dict:
        """Analisa um token de sessão."""
        result = {
            "token": token[:50] + "..." if len(token) > 50 else token,
            "length": len(token),
            "type": "unknown",
            "entropy": self._calculate_entropy(token),
            "issues": [],
            "decoded": None
        }
        
        # Identificar tipo
        for name, pattern in self.SESSION_PATTERNS.items():
            if re.match(pattern, token, re.IGNORECASE):
                result["type"] = name
                break
        
        # Verificar se é hash
        if len(token) in self.HASH_LENGTHS and re.match(r'^[a-fA-F0-9]+$', token):
            result["type"] = f"hash_{self.HASH_LENGTHS[len(token)]}"
        
        # Tentar decodificar JWT
        if token.startswith("eyJ"):
            result["decoded"] = self._decode_jwt(token)
            result["type"] = "jwt"
        
        # Tentar decodificar Base64
        elif result["type"] == "base64":
            try:
                decoded = base64.b64decode(token).decode('utf-8', errors='ignore')
                if decoded.isprintable():
                    result["decoded"] = decoded
            except Exception:
                pass
        
        # Verificar problemas
        if result["entropy"] < 3.0:
            result["issues"].append({
                "issue": "low_entropy",
                "severity": "high",
                "description": "Token com entropia baixa, pode ser previsível"
            })
        
        if len(token) < 16:
            result["issues"].append({
                "issue": "short_token",
                "severity": "medium", 
                "description": "Token muito curto para ser seguro"
            })
        
        # Verificar padrões sequenciais
        if self._is_sequential(token):
            result["issues"].append({
                "issue": "sequential_pattern",
                "severity": "critical",
                "description": "Token contém padrões sequenciais previsíveis"
            })
        
        return result
    
    def _calculate_entropy(self, text: str) -> float:
        """Calcula entropia de Shannon."""
        from collections import Counter
        import math
        
        if not text:
            return 0.0
        
        counter = Counter(text)
        length = len(text)
        
        entropy = 0.0
        for count in counter.values():
            prob = count / length
            if prob > 0:
                entropy -= prob * math.log2(prob)
        
        return round(entropy, 2)
    
    def _decode_jwt(self, token: str) -> Optional[Dict]:
        """Decodifica um JWT."""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            # Header
            header = base64.urlsafe_b64decode(parts[0] + '==').decode('utf-8')
            header = json.loads(header)
            
            # Payload
            payload = base64.urlsafe_b64decode(parts[1] + '==').decode('utf-8')
            payload = json.loads(payload)
            
            return {
                "header": header,
                "payload": payload,
                "signature_present": bool(parts[2])
            }
        except Exception:
            return None
    
    def _is_sequential(self, token: str) -> bool:
        """Verifica se o token tem padrões sequenciais."""
        # Números sequenciais
        if token.isdigit():
            for i in range(len(token) - 3):
                if int(token[i]) + 1 == int(token[i+1]) == int(token[i+2]) - 1:
                    return True
        
        # Padrões repetidos
        if len(set(token)) < len(token) / 4:
            return True
        
        return False


class CookieAnalyzer:
    """Analisador de cookies."""
    
    # Cookies sensíveis conhecidos
    SENSITIVE_COOKIES = [
        "sessionid", "session_id", "sid", "ssid", "phpsessid", "jsessionid",
        "asp.net_sessionid", "cfid", "cftoken", "auth", "authentication",
        "token", "access_token", "refresh_token", "jwt", "api_key", "apikey",
        "password", "passwd", "secret", "private", "credential"
    ]
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session() if requests else None
        self.token_analyzer = SessionTokenAnalyzer()
    
    def analyze_url(self, url: str) -> Dict:
        """Analisa cookies de uma URL."""
        if not self.session:
            return {"error": "requests não instalado"}
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        result = {
            "url": url,
            "cookies": [],
            "vulnerabilities": [],
            "summary": {
                "total": 0,
                "secure": 0,
                "httponly": 0,
                "samesite": 0,
                "sensitive": 0
            }
        }
        
        try:
            # Fazer requisição
            response = self.session.get(url, timeout=self.timeout, verify=False)
            
            # Analisar cookies
            for cookie in self.session.cookies:
                cookie_info = self._parse_cookie(cookie, response.headers)
                result["cookies"].append(cookie_info.to_dict())
                
                # Atualizar sumário
                result["summary"]["total"] += 1
                if cookie_info.secure:
                    result["summary"]["secure"] += 1
                if cookie_info.httponly:
                    result["summary"]["httponly"] += 1
                if cookie_info.samesite:
                    result["summary"]["samesite"] += 1
                
                # Verificar se é sensível
                is_sensitive = any(
                    s in cookie_info.name.lower() 
                    for s in self.SENSITIVE_COOKIES
                )
                if is_sensitive:
                    result["summary"]["sensitive"] += 1
                
                # Detectar vulnerabilidades
                vulns = self._check_vulnerabilities(cookie_info, is_sensitive, url)
                result["vulnerabilities"].extend([v.to_dict() for v in vulns])
        
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _parse_cookie(self, cookie, headers) -> CookieInfo:
        """Parseia um cookie."""
        # Verificar SameSite no header Set-Cookie
        samesite = None
        for header_value in headers.get_all('Set-Cookie', []) or []:
            if cookie.name in header_value:
                if 'samesite=strict' in header_value.lower():
                    samesite = "Strict"
                elif 'samesite=lax' in header_value.lower():
                    samesite = "Lax"
                elif 'samesite=none' in header_value.lower():
                    samesite = "None"
        
        return CookieInfo(
            name=cookie.name,
            value=cookie.value,
            domain=cookie.domain,
            path=cookie.path,
            expires=str(cookie.expires) if cookie.expires else None,
            secure=cookie.secure,
            httponly=cookie.has_nonstandard_attr('httponly') if hasattr(cookie, 'has_nonstandard_attr') else False,
            samesite=samesite,
            size=len(cookie.value)
        )
    
    def _check_vulnerabilities(self, cookie: CookieInfo, is_sensitive: bool, url: str) -> List[CookieVulnerability]:
        """Verifica vulnerabilidades em um cookie."""
        vulns = []
        is_https = url.startswith('https://')
        
        # Cookie sensível sem Secure flag
        if is_sensitive and not cookie.secure:
            vulns.append(CookieVulnerability(
                cookie_name=cookie.name,
                issue="missing_secure_flag",
                severity="high" if is_https else "critical",
                description="Cookie sensível sem flag Secure",
                recommendation="Adicionar flag Secure ao cookie"
            ))
        
        # Cookie sensível sem HttpOnly
        if is_sensitive and not cookie.httponly:
            vulns.append(CookieVulnerability(
                cookie_name=cookie.name,
                issue="missing_httponly_flag",
                severity="high",
                description="Cookie sensível sem flag HttpOnly (vulnerável a XSS)",
                recommendation="Adicionar flag HttpOnly ao cookie"
            ))
        
        # Sem SameSite (vulnerável a CSRF)
        if is_sensitive and not cookie.samesite:
            vulns.append(CookieVulnerability(
                cookie_name=cookie.name,
                issue="missing_samesite",
                severity="medium",
                description="Cookie sem atributo SameSite (pode ser vulnerável a CSRF)",
                recommendation="Adicionar SameSite=Strict ou SameSite=Lax"
            ))
        
        # SameSite=None sem Secure
        if cookie.samesite == "None" and not cookie.secure:
            vulns.append(CookieVulnerability(
                cookie_name=cookie.name,
                issue="samesite_none_without_secure",
                severity="high",
                description="SameSite=None requer flag Secure",
                recommendation="Adicionar flag Secure quando usar SameSite=None"
            ))
        
        # Cookie muito grande
        if cookie.size > 4096:
            vulns.append(CookieVulnerability(
                cookie_name=cookie.name,
                issue="cookie_too_large",
                severity="low",
                description=f"Cookie muito grande ({cookie.size} bytes)",
                recommendation="Reduzir tamanho do cookie ou usar armazenamento server-side"
            ))
        
        # Token analysis
        if is_sensitive and len(cookie.value) > 8:
            token_analysis = self.token_analyzer.analyze(cookie.value)
            for issue in token_analysis.get("issues", []):
                vulns.append(CookieVulnerability(
                    cookie_name=cookie.name,
                    issue=issue["issue"],
                    severity=issue["severity"],
                    description=issue["description"],
                    recommendation="Usar gerador de tokens criptograficamente seguro"
                ))
        
        return vulns
    
    def analyze_token(self, token: str) -> Dict:
        """Analisa um token de sessão."""
        return self.token_analyzer.analyze(token)
    
    def compare_sessions(self, url: str, iterations: int = 5) -> Dict:
        """Compara sessões para verificar randomização."""
        result = {
            "url": url,
            "sessions": [],
            "analysis": {
                "tokens_unique": True,
                "pattern_detected": False,
                "issues": []
            }
        }
        
        try:
            for i in range(iterations):
                # Nova sessão
                temp_session = requests.Session()
                temp_session.get(url, timeout=self.timeout, verify=False)
                
                session_cookies = {}
                for cookie in temp_session.cookies:
                    session_cookies[cookie.name] = cookie.value
                
                result["sessions"].append(session_cookies)
            
            # Analisar tokens
            for cookie_name in result["sessions"][0].keys():
                values = [s.get(cookie_name, "") for s in result["sessions"]]
                
                # Verificar unicidade
                if len(set(values)) != len(values):
                    result["analysis"]["tokens_unique"] = False
                    result["analysis"]["issues"].append({
                        "cookie": cookie_name,
                        "issue": "duplicate_tokens",
                        "severity": "critical"
                    })
                
                # Verificar padrões
                for i in range(len(values) - 1):
                    if self._tokens_similar(values[i], values[i+1]):
                        result["analysis"]["pattern_detected"] = True
                        result["analysis"]["issues"].append({
                            "cookie": cookie_name,
                            "issue": "predictable_pattern",
                            "severity": "high"
                        })
                        break
        
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _tokens_similar(self, t1: str, t2: str) -> bool:
        """Verifica se dois tokens são muito similares."""
        if len(t1) != len(t2):
            return False
        
        differences = sum(1 for a, b in zip(t1, t2) if a != b)
        return differences < len(t1) / 4


def interactive_menu():
    """Menu interativo do Cookie Analyzer."""
    if not requests:
        print("❌ Módulo requests não encontrado. Instale com: pip install requests")
        input("Pressione Enter...")
        return
    
    analyzer = CookieAnalyzer()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║            🍪 COOKIE ANALYZER - Olho de Deus                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔍 Analisar Cookies de URL                              ║
║  [2] 🎫 Analisar Token/Session ID                            ║
║  [3] 🔄 Comparar Múltiplas Sessões                           ║
║  [4] 🔓 Decodificar JWT                                      ║
║  [5] 📊 Verificar Entropia de Token                          ║
║  [6] 🌐 Scan Múltiplas URLs                                  ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Analisar Cookies ===")
            url = input("URL: ").strip()
            
            if not url:
                continue
            
            print(f"\nAnalisando {url}...")
            result = analyzer.analyze_url(url)
            
            if result.get("error"):
                print(f"❌ Erro: {result['error']}")
                input("Enter para continuar...")
                continue
            
            print(f"\n📊 SUMÁRIO:")
            summary = result["summary"]
            print(f"   Total de cookies: {summary['total']}")
            print(f"   Com Secure: {summary['secure']}/{summary['total']}")
            print(f"   Com HttpOnly: {summary['httponly']}/{summary['total']}")
            print(f"   Com SameSite: {summary['samesite']}/{summary['total']}")
            print(f"   Sensíveis: {summary['sensitive']}")
            
            print(f"\n🍪 COOKIES:")
            for cookie in result["cookies"]:
                secure_icon = "🔒" if cookie["secure"] else "⚠️"
                http_icon = "🛡️" if cookie["httponly"] else "⚠️"
                same_icon = "✅" if cookie["samesite"] else "⚠️"
                
                print(f"\n   {cookie['name']}:")
                print(f"      Valor: {cookie['value'][:30]}..." if len(cookie['value']) > 30 else f"      Valor: {cookie['value']}")
                print(f"      {secure_icon} Secure | {http_icon} HttpOnly | {same_icon} SameSite: {cookie['samesite'] or 'Não definido'}")
            
            if result["vulnerabilities"]:
                print(f"\n⚠️ VULNERABILIDADES ({len(result['vulnerabilities'])}):")
                for vuln in result["vulnerabilities"]:
                    sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(vuln["severity"], "⚪")
                    print(f"\n   {sev_icon} [{vuln['severity'].upper()}] {vuln['issue']}")
                    print(f"      Cookie: {vuln['cookie_name']}")
                    print(f"      {vuln['description']}")
                    print(f"      💡 {vuln['recommendation']}")
            else:
                print("\n✅ Nenhuma vulnerabilidade crítica detectada")
            
            save = input("\nSalvar resultados? (s/n): ").lower()
            if save == 's':
                with open(f"cookie_analysis.json", 'w') as f:
                    json.dump(result, f, indent=2)
                print("✅ Salvo em cookie_analysis.json")
        
        elif escolha == '2':
            print("\n=== Analisar Token ===")
            token = input("Token/Session ID: ").strip()
            
            if not token:
                continue
            
            result = analyzer.analyze_token(token)
            
            print(f"\n🎫 ANÁLISE DO TOKEN:")
            print(f"   Tipo: {result['type']}")
            print(f"   Tamanho: {result['length']} caracteres")
            print(f"   Entropia: {result['entropy']} bits/char")
            
            if result.get("decoded"):
                print(f"\n   📄 Conteúdo decodificado:")
                if isinstance(result["decoded"], dict):
                    for key, value in result["decoded"].items():
                        print(f"      {key}: {json.dumps(value, indent=8)}")
                else:
                    print(f"      {result['decoded']}")
            
            if result["issues"]:
                print(f"\n   ⚠️ Issues:")
                for issue in result["issues"]:
                    print(f"      [{issue['severity'].upper()}] {issue['description']}")
            else:
                print(f"\n   ✅ Token parece seguro")
        
        elif escolha == '3':
            print("\n=== Comparar Sessões ===")
            url = input("URL: ").strip()
            count = input("Número de sessões (default: 5): ").strip()
            count = int(count) if count.isdigit() else 5
            
            if not url:
                continue
            
            print(f"\nGerando {count} sessões...")
            result = analyzer.compare_sessions(url, count)
            
            if result.get("error"):
                print(f"❌ Erro: {result['error']}")
                input("Enter para continuar...")
                continue
            
            print(f"\n📊 RESULTADO:")
            print(f"   Tokens únicos: {'✅ Sim' if result['analysis']['tokens_unique'] else '❌ Não'}")
            print(f"   Padrão detectado: {'❌ Sim' if result['analysis']['pattern_detected'] else '✅ Não'}")
            
            if result['analysis']['issues']:
                print(f"\n   ⚠️ Issues:")
                for issue in result['analysis']['issues']:
                    print(f"      [{issue['severity'].upper()}] {issue['issue']} em {issue['cookie']}")
            else:
                print(f"\n   ✅ Geração de sessão parece segura")
        
        elif escolha == '4':
            print("\n=== Decodificar JWT ===")
            jwt = input("JWT Token: ").strip()
            
            if not jwt:
                continue
            
            token_analyzer = SessionTokenAnalyzer()
            decoded = token_analyzer._decode_jwt(jwt)
            
            if decoded:
                print(f"\n📜 JWT Decodificado:")
                
                print(f"\n   HEADER:")
                for key, value in decoded.get("header", {}).items():
                    print(f"      {key}: {value}")
                
                print(f"\n   PAYLOAD:")
                payload = decoded.get("payload", {})
                for key, value in payload.items():
                    # Converter timestamps
                    if key in ["exp", "iat", "nbf"] and isinstance(value, int):
                        dt = datetime.fromtimestamp(value)
                        print(f"      {key}: {value} ({dt.isoformat()})")
                    else:
                        print(f"      {key}: {value}")
                
                # Verificar expiração
                if "exp" in payload:
                    exp = datetime.fromtimestamp(payload["exp"])
                    if exp < datetime.now():
                        print(f"\n   ⚠️ TOKEN EXPIRADO!")
                    else:
                        remaining = (exp - datetime.now()).total_seconds()
                        print(f"\n   ⏰ Expira em: {remaining/3600:.1f} horas")
                
                print(f"\n   Assinatura presente: {'Sim' if decoded['signature_present'] else 'Não'}")
            else:
                print("❌ Não foi possível decodificar o JWT")
        
        elif escolha == '5':
            print("\n=== Verificar Entropia ===")
            token = input("Token: ").strip()
            
            if not token:
                continue
            
            token_analyzer = SessionTokenAnalyzer()
            entropy = token_analyzer._calculate_entropy(token)
            
            print(f"\n📊 Entropia: {entropy} bits/caractere")
            print(f"   Entropia total: {entropy * len(token):.0f} bits")
            
            if entropy < 2.0:
                print(f"   🔴 MUITO BAIXA - Token altamente previsível")
            elif entropy < 3.0:
                print(f"   🟠 BAIXA - Token potencialmente previsível")
            elif entropy < 4.0:
                print(f"   🟡 MÉDIA - Token aceitável")
            else:
                print(f"   🟢 ALTA - Token parece seguro")
            
            # Calcular bits de segurança estimados
            charset_size = len(set(token))
            bits_security = len(token) * (entropy / 8) * 8
            print(f"\n   Caracteres únicos: {charset_size}")
            print(f"   Bits de segurança: ~{bits_security:.0f}")
        
        elif escolha == '6':
            print("\n=== Scan Múltiplas URLs ===")
            print("Digite as URLs (uma por linha, linha vazia para terminar):")
            
            urls = []
            while True:
                u = input("  > ").strip()
                if not u:
                    break
                urls.append(u)
            
            if not urls:
                continue
            
            print(f"\nAnalisando {len(urls)} URLs...\n")
            
            all_results = []
            for url in urls:
                print(f"Analisando {url}...", end=" ")
                result = analyzer.analyze_url(url)
                
                if result.get("error"):
                    print(f"Erro: {result['error']}")
                else:
                    vuln_count = len(result["vulnerabilities"])
                    cookie_count = result["summary"]["total"]
                    print(f"{cookie_count} cookies, {vuln_count} vulnerabilidades")
                    all_results.append(result)
            
            save = input("\nSalvar resultados? (s/n): ").lower()
            if save == 's':
                with open("cookies_scan_results.json", 'w') as f:
                    json.dump(all_results, f, indent=2)
                print("✅ Salvo em cookies_scan_results.json")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
