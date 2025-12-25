#!/usr/bin/env python3
"""
Header Analyzer - Olho de Deus
Análise de headers HTTP para segurança
"""

import requests
import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse


@dataclass
class SecurityHeader:
    """Header de segurança"""
    name: str
    value: str
    present: bool
    secure: bool
    severity: str  # critical, high, medium, low, info
    recommendation: str = ""


@dataclass
class HeaderAnalysisResult:
    """Resultado da análise"""
    url: str
    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    security_headers: List[SecurityHeader] = field(default_factory=list)
    server_info: Dict[str, str] = field(default_factory=dict)
    cookies: List[Dict] = field(default_factory=list)
    score: int = 0
    grade: str = "F"
    issues: List[str] = field(default_factory=list)


class HeaderAnalyzer:
    """Analisador de headers HTTP"""
    
    # Headers de segurança esperados
    SECURITY_HEADERS = {
        'Strict-Transport-Security': {
            'description': 'HSTS - Força conexões HTTPS',
            'severity': 'high',
            'recommendation': 'Adicionar: Strict-Transport-Security: max-age=31536000; includeSubDomains'
        },
        'Content-Security-Policy': {
            'description': 'CSP - Previne XSS e injeção de código',
            'severity': 'high',
            'recommendation': 'Configurar CSP adequado para o site'
        },
        'X-Content-Type-Options': {
            'description': 'Previne MIME-type sniffing',
            'severity': 'medium',
            'recommendation': 'Adicionar: X-Content-Type-Options: nosniff'
        },
        'X-Frame-Options': {
            'description': 'Previne clickjacking',
            'severity': 'medium',
            'recommendation': 'Adicionar: X-Frame-Options: DENY ou SAMEORIGIN'
        },
        'X-XSS-Protection': {
            'description': 'Filtro XSS do navegador (legacy)',
            'severity': 'low',
            'recommendation': 'Adicionar: X-XSS-Protection: 1; mode=block'
        },
        'Referrer-Policy': {
            'description': 'Controla informações de referrer',
            'severity': 'low',
            'recommendation': 'Adicionar: Referrer-Policy: strict-origin-when-cross-origin'
        },
        'Permissions-Policy': {
            'description': 'Controla features do navegador',
            'severity': 'low',
            'recommendation': 'Configurar Permissions-Policy adequado'
        },
        'X-Permitted-Cross-Domain-Policies': {
            'description': 'Políticas cross-domain para Flash/PDF',
            'severity': 'low',
            'recommendation': 'Adicionar: X-Permitted-Cross-Domain-Policies: none'
        },
    }
    
    # Headers que revelam informações sensíveis
    INFO_DISCLOSURE_HEADERS = [
        'Server', 'X-Powered-By', 'X-AspNet-Version', 'X-AspNetMvc-Version',
        'X-Generator', 'X-Drupal-Cache', 'X-Drupal-Dynamic-Cache',
        'X-Varnish', 'Via', 'X-Backend-Server', 'X-Debug'
    ]
    
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def analyze(self, url: str) -> HeaderAnalysisResult:
        """Analisa headers de uma URL"""
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        print(f"\n🔍 Analisando Headers: {url}")
        print("=" * 50)
        
        result = HeaderAnalysisResult(url=url, status_code=0)
        
        try:
            resp = self.session.get(url, timeout=self.timeout, verify=False, allow_redirects=True)
            result.status_code = resp.status_code
            result.headers = dict(resp.headers)
            
        except Exception as e:
            result.issues.append(f"Erro de conexão: {str(e)}")
            return result
        
        # Analisar headers de segurança
        self._analyze_security_headers(result)
        
        # Analisar disclosure de informações
        self._analyze_info_disclosure(result)
        
        # Analisar cookies
        self._analyze_cookies(result, resp.cookies)
        
        # Calcular score
        self._calculate_score(result)
        
        # Imprimir resultados
        self._print_results(result)
        
        return result
    
    def _analyze_security_headers(self, result: HeaderAnalysisResult):
        """Analisa headers de segurança"""
        for header_name, info in self.SECURITY_HEADERS.items():
            value = result.headers.get(header_name, '')
            present = bool(value)
            
            sec_header = SecurityHeader(
                name=header_name,
                value=value,
                present=present,
                secure=present,
                severity=info['severity'],
                recommendation=info['recommendation'] if not present else ""
            )
            
            # Validar valor se presente
            if present:
                sec_header.secure = self._validate_header_value(header_name, value)
            
            result.security_headers.append(sec_header)
    
    def _validate_header_value(self, name: str, value: str) -> bool:
        """Valida valor de header de segurança"""
        validations = {
            'Strict-Transport-Security': lambda v: 'max-age=' in v.lower() and int(re.search(r'max-age=(\d+)', v.lower()).group(1)) >= 31536000 if re.search(r'max-age=(\d+)', v.lower()) else False,
            'X-Content-Type-Options': lambda v: v.lower() == 'nosniff',
            'X-Frame-Options': lambda v: v.upper() in ['DENY', 'SAMEORIGIN'],
            'X-XSS-Protection': lambda v: '1' in v,
            'Referrer-Policy': lambda v: v.lower() in ['no-referrer', 'strict-origin', 'strict-origin-when-cross-origin'],
        }
        
        validator = validations.get(name)
        if validator:
            try:
                return validator(value)
            except:
                return False
        return True
    
    def _analyze_info_disclosure(self, result: HeaderAnalysisResult):
        """Analisa headers que revelam informações"""
        for header in self.INFO_DISCLOSURE_HEADERS:
            value = result.headers.get(header, '')
            if value:
                result.server_info[header] = value
                result.issues.append(f"Information disclosure: {header}: {value}")
    
    def _analyze_cookies(self, result: HeaderAnalysisResult, cookies):
        """Analisa segurança dos cookies"""
        set_cookie_headers = result.headers.get('Set-Cookie', '')
        
        for cookie in cookies:
            cookie_info = {
                'name': cookie.name,
                'secure': cookie.secure,
                'httponly': 'httponly' in str(cookie).lower(),
                'samesite': 'none',
                'issues': []
            }
            
            # Verificar flags
            if not cookie.secure:
                cookie_info['issues'].append('Missing Secure flag')
            
            if not cookie_info['httponly']:
                cookie_info['issues'].append('Missing HttpOnly flag')
            
            # Check SameSite
            cookie_str = str(cookie).lower()
            if 'samesite=strict' in cookie_str:
                cookie_info['samesite'] = 'strict'
            elif 'samesite=lax' in cookie_str:
                cookie_info['samesite'] = 'lax'
            elif 'samesite=none' in cookie_str:
                cookie_info['samesite'] = 'none'
                cookie_info['issues'].append('SameSite=None may be insecure')
            else:
                cookie_info['issues'].append('Missing SameSite attribute')
            
            result.cookies.append(cookie_info)
    
    def _calculate_score(self, result: HeaderAnalysisResult):
        """Calcula score de segurança"""
        score = 100
        
        # Penalidades por headers faltantes
        severity_penalties = {
            'critical': 25,
            'high': 15,
            'medium': 10,
            'low': 5,
        }
        
        for sh in result.security_headers:
            if not sh.present:
                score -= severity_penalties.get(sh.severity, 5)
            elif not sh.secure:
                score -= severity_penalties.get(sh.severity, 5) // 2
        
        # Penalidade por information disclosure
        score -= len(result.server_info) * 3
        
        # Penalidade por cookies inseguros
        for cookie in result.cookies:
            score -= len(cookie['issues']) * 2
        
        result.score = max(0, min(100, score))
        
        # Grade
        if result.score >= 90:
            result.grade = 'A'
        elif result.score >= 80:
            result.grade = 'B'
        elif result.score >= 70:
            result.grade = 'C'
        elif result.score >= 60:
            result.grade = 'D'
        else:
            result.grade = 'F'
    
    def _print_results(self, result: HeaderAnalysisResult):
        """Imprime resultados da análise"""
        
        print(f"\n📋 Status: {result.status_code}")
        
        # Security headers
        print(f"\n🔒 Headers de Segurança:")
        for sh in result.security_headers:
            if sh.present:
                status = "✅" if sh.secure else "⚠️"
                print(f"   {status} {sh.name}: {sh.value[:60]}...")
            else:
                print(f"   ❌ {sh.name}: AUSENTE")
        
        # Server info
        if result.server_info:
            print(f"\n⚠️ Information Disclosure:")
            for header, value in result.server_info.items():
                print(f"   📢 {header}: {value}")
        
        # Cookies
        if result.cookies:
            print(f"\n🍪 Cookies ({len(result.cookies)}):")
            for cookie in result.cookies:
                issues = ", ".join(cookie['issues']) if cookie['issues'] else "OK"
                status = "✅" if not cookie['issues'] else "⚠️"
                print(f"   {status} {cookie['name']}: {issues}")
        
        # Score
        print(f"\n📊 Score: {result.score}/100 (Grade: {result.grade})")
    
    def get_recommendations(self, result: HeaderAnalysisResult) -> List[str]:
        """Retorna recomendações de segurança"""
        recs = []
        
        for sh in result.security_headers:
            if not sh.present and sh.recommendation:
                recs.append(sh.recommendation)
        
        if result.server_info:
            recs.append("Remover headers que revelam informações do servidor")
        
        for cookie in result.cookies:
            if cookie['issues']:
                recs.append(f"Cookie '{cookie['name']}': {', '.join(cookie['issues'])}")
        
        return recs
    
    def compare_urls(self, urls: List[str]) -> Dict[str, HeaderAnalysisResult]:
        """Compara headers de múltiplas URLs"""
        results = {}
        
        for url in urls:
            print(f"\n{'='*50}")
            results[url] = self.analyze(url)
        
        # Comparação
        print(f"\n{'='*50}")
        print("📊 Comparação:")
        print("-" * 50)
        
        for url, result in results.items():
            domain = urlparse(url).netloc
            print(f"   {domain}: {result.grade} ({result.score}/100)")
        
        return results
    
    def export_report(self, result: HeaderAnalysisResult, filepath: str):
        """Exporta relatório para JSON"""
        report = {
            'url': result.url,
            'status_code': result.status_code,
            'score': result.score,
            'grade': result.grade,
            'headers': result.headers,
            'security_headers': [
                {
                    'name': sh.name,
                    'value': sh.value,
                    'present': sh.present,
                    'secure': sh.secure,
                    'severity': sh.severity
                }
                for sh in result.security_headers
            ],
            'server_info': result.server_info,
            'cookies': result.cookies,
            'issues': result.issues,
            'recommendations': self.get_recommendations(result),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Relatório salvo: {filepath}")


# Suprimir warnings de SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    """Função principal"""
    import sys
    
    print("\n" + "=" * 50)
    print("🔍 Header Analyzer - Olho de Deus")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        url = input("\n🌐 URL para analisar: ").strip()
    else:
        url = sys.argv[1]
    
    analyzer = HeaderAnalyzer()
    result = analyzer.analyze(url)
    
    # Recomendações
    recs = analyzer.get_recommendations(result)
    if recs:
        print(f"\n💡 Recomendações:")
        for rec in recs:
            print(f"   • {rec}")
    
    print("\n✅ Análise concluída!")


if __name__ == "__main__":
    main()
