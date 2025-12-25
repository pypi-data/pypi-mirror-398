#!/usr/bin/env python3
"""
SSL/TLS Analyzer - Olho de Deus
Análise profunda de configurações SSL/TLS
"""

import socket
import ssl
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class CertInfo:
    """Informações do certificado"""
    subject: Dict[str, str] = field(default_factory=dict)
    issuer: Dict[str, str] = field(default_factory=dict)
    version: int = 0
    serial: str = ""
    not_before: str = ""
    not_after: str = ""
    days_remaining: int = 0
    expired: bool = False
    self_signed: bool = False
    san: List[str] = field(default_factory=list)
    fingerprint_sha256: str = ""
    signature_algorithm: str = ""
    key_size: int = 0
    key_type: str = ""


@dataclass
class SSLAnalysisResult:
    """Resultado da análise SSL"""
    host: str
    port: int
    ssl_version: str = ""
    cipher_suite: str = ""
    cipher_bits: int = 0
    certificate: Optional[CertInfo] = None
    supported_protocols: List[str] = field(default_factory=list)
    supported_ciphers: List[str] = field(default_factory=list)
    vulnerabilities: List[Dict] = field(default_factory=list)
    score: str = "F"
    recommendations: List[str] = field(default_factory=list)


class SSLAnalyzer:
    """Analisador SSL/TLS avançado"""
    
    # Protocolos a testar
    PROTOCOLS = {
        'SSLv2': getattr(ssl, 'PROTOCOL_SSLv2', None),
        'SSLv3': getattr(ssl, 'PROTOCOL_SSLv3', None),
        'TLSv1.0': getattr(ssl, 'PROTOCOL_TLSv1', None),
        'TLSv1.1': getattr(ssl, 'PROTOCOL_TLSv1_1', None),
        'TLSv1.2': getattr(ssl, 'PROTOCOL_TLSv1_2', None),
        'TLSv1.3': getattr(ssl, 'PROTOCOL_TLS', None),
    }
    
    # Ciphers fracos
    WEAK_CIPHERS = [
        'NULL', 'EXPORT', 'DES', '3DES', 'RC4', 'RC2', 'MD5',
        'anon', 'ADH', 'AECDH', 'PSK', 'SRP', 'CAMELLIA'
    ]
    
    # Vulnerabilidades conhecidas
    VULNERABILITIES = {
        'SSLv2': {'name': 'DROWN', 'severity': 'critical', 'cve': 'CVE-2016-0800'},
        'SSLv3': {'name': 'POODLE', 'severity': 'high', 'cve': 'CVE-2014-3566'},
        'TLSv1.0': {'name': 'BEAST', 'severity': 'medium', 'cve': 'CVE-2011-3389'},
        'TLSv1.1': {'name': 'Deprecated', 'severity': 'low', 'cve': None},
    }
    
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
    
    def analyze(self, host: str, port: int = 443) -> SSLAnalysisResult:
        """Análise completa de SSL/TLS"""
        print(f"\n🔐 Analisando SSL/TLS: {host}:{port}")
        print("=" * 50)
        
        result = SSLAnalysisResult(host=host, port=port)
        
        # Obter certificado
        cert_info = self._get_certificate(host, port)
        if cert_info:
            result.certificate = cert_info
            print(f"\n📜 Certificado:")
            print(f"   Subject: {cert_info.subject.get('CN', 'N/A')}")
            print(f"   Issuer: {cert_info.issuer.get('CN', 'N/A')}")
            print(f"   Válido até: {cert_info.not_after}")
            print(f"   Dias restantes: {cert_info.days_remaining}")
            print(f"   Auto-assinado: {'Sim' if cert_info.self_signed else 'Não'}")
            print(f"   Chave: {cert_info.key_type} {cert_info.key_size} bits")
        
        # Testar protocolos
        result.supported_protocols = self._test_protocols(host, port)
        print(f"\n🔒 Protocolos suportados:")
        for proto in result.supported_protocols:
            status = "✅" if proto in ['TLSv1.2', 'TLSv1.3'] else "⚠️"
            print(f"   {status} {proto}")
        
        # Verificar vulnerabilidades
        result.vulnerabilities = self._check_vulnerabilities(result.supported_protocols)
        if result.vulnerabilities:
            print(f"\n🚨 Vulnerabilidades:")
            for vuln in result.vulnerabilities:
                print(f"   ❌ {vuln['name']} ({vuln['severity']})")
        
        # Testar ciphers
        result.supported_ciphers = self._get_ciphers(host, port)
        weak = [c for c in result.supported_ciphers if self._is_weak_cipher(c)]
        print(f"\n🔑 Ciphers: {len(result.supported_ciphers)} total, {len(weak)} fracos")
        
        # Calcular score
        result.score = self._calculate_score(result)
        result.recommendations = self._get_recommendations(result)
        
        print(f"\n📊 Score: {result.score}")
        
        return result
    
    def _get_certificate(self, host: str, port: int) -> Optional[CertInfo]:
        """Obtém informações do certificado"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert(binary_form=True)
                    cert_dict = ssock.getpeercert()
                    cipher = ssock.cipher()
                    
                    if not cert_dict:
                        # Parse do certificado binário
                        import ssl
                        cert_dict = ssl._ssl._test_decode_cert(cert) if hasattr(ssl._ssl, '_test_decode_cert') else {}
                    
                    info = CertInfo()
                    
                    # Subject
                    if 'subject' in cert_dict:
                        for item in cert_dict['subject']:
                            for key, value in item:
                                info.subject[key] = value
                    
                    # Issuer
                    if 'issuer' in cert_dict:
                        for item in cert_dict['issuer']:
                            for key, value in item:
                                info.issuer[key] = value
                    
                    # Datas
                    info.not_before = cert_dict.get('notBefore', '')
                    info.not_after = cert_dict.get('notAfter', '')
                    
                    # Calcular dias restantes
                    if info.not_after:
                        try:
                            exp_date = datetime.strptime(info.not_after, '%b %d %H:%M:%S %Y %Z')
                            info.days_remaining = (exp_date - datetime.now()).days
                            info.expired = info.days_remaining < 0
                        except:
                            pass
                    
                    # SAN
                    if 'subjectAltName' in cert_dict:
                        info.san = [v for t, v in cert_dict['subjectAltName'] if t == 'DNS']
                    
                    # Fingerprint
                    info.fingerprint_sha256 = hashlib.sha256(cert).hexdigest().upper()
                    
                    # Self-signed check
                    info.self_signed = info.subject == info.issuer
                    
                    # Key info from cipher
                    if cipher:
                        info.key_size = cipher[2] if len(cipher) > 2 else 0
                    
                    return info
                    
        except Exception as e:
            print(f"   ⚠️ Erro ao obter certificado: {e}")
            return None
    
    def _test_protocols(self, host: str, port: int) -> List[str]:
        """Testa quais protocolos são suportados"""
        supported = []
        
        for name, protocol in self.PROTOCOLS.items():
            if protocol is None:
                continue
            
            try:
                context = ssl.SSLContext(protocol)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                with socket.create_connection((host, port), timeout=self.timeout) as sock:
                    with context.wrap_socket(sock, server_hostname=host) as ssock:
                        supported.append(name)
            except:
                pass
        
        return supported
    
    def _get_ciphers(self, host: str, port: int) -> List[str]:
        """Obtém lista de ciphers suportados"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cipher = ssock.cipher()
                    return [cipher[0]] if cipher else []
        except:
            return []
    
    def _is_weak_cipher(self, cipher: str) -> bool:
        """Verifica se o cipher é fraco"""
        return any(weak in cipher.upper() for weak in self.WEAK_CIPHERS)
    
    def _check_vulnerabilities(self, protocols: List[str]) -> List[Dict]:
        """Verifica vulnerabilidades baseado nos protocolos"""
        vulns = []
        for proto in protocols:
            if proto in self.VULNERABILITIES:
                vulns.append(self.VULNERABILITIES[proto])
        return vulns
    
    def _calculate_score(self, result: SSLAnalysisResult) -> str:
        """Calcula score de segurança"""
        score = 100
        
        # Penalidades por protocolo
        if 'SSLv2' in result.supported_protocols:
            score -= 50
        if 'SSLv3' in result.supported_protocols:
            score -= 40
        if 'TLSv1.0' in result.supported_protocols:
            score -= 20
        if 'TLSv1.1' in result.supported_protocols:
            score -= 10
        
        # Bonus por TLS moderno
        if 'TLSv1.3' in result.supported_protocols:
            score += 10
        
        # Penalidade por certificado
        if result.certificate:
            if result.certificate.expired:
                score -= 50
            if result.certificate.self_signed:
                score -= 20
            if result.certificate.days_remaining < 30:
                score -= 10
        
        # Penalidade por vulnerabilidades
        score -= len(result.vulnerabilities) * 15
        
        # Converter para letra
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"
    
    def _get_recommendations(self, result: SSLAnalysisResult) -> List[str]:
        """Gera recomendações de segurança"""
        recs = []
        
        if 'SSLv2' in result.supported_protocols:
            recs.append("Desabilitar SSLv2 imediatamente")
        if 'SSLv3' in result.supported_protocols:
            recs.append("Desabilitar SSLv3")
        if 'TLSv1.0' in result.supported_protocols:
            recs.append("Desabilitar TLS 1.0")
        if 'TLSv1.1' in result.supported_protocols:
            recs.append("Considerar desabilitar TLS 1.1")
        if 'TLSv1.3' not in result.supported_protocols:
            recs.append("Habilitar TLS 1.3")
        
        if result.certificate:
            if result.certificate.expired:
                recs.append("Renovar certificado expirado")
            elif result.certificate.days_remaining < 30:
                recs.append(f"Renovar certificado em breve ({result.certificate.days_remaining} dias)")
            if result.certificate.self_signed:
                recs.append("Usar certificado de CA confiável")
            if result.certificate.key_size < 2048:
                recs.append("Usar chave de pelo menos 2048 bits")
        
        return recs
    
    def quick_check(self, host: str, port: int = 443) -> Dict:
        """Verificação rápida de SSL"""
        result = {
            'host': host,
            'port': port,
            'ssl_enabled': False,
            'valid_cert': False,
            'expires_soon': False
        }
        
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    result['ssl_enabled'] = True
                    result['valid_cert'] = True
                    cert = ssock.getpeercert()
                    if cert and 'notAfter' in cert:
                        exp = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        result['expires_soon'] = (exp - datetime.now()).days < 30
        except ssl.SSLCertVerificationError:
            result['ssl_enabled'] = True
            result['valid_cert'] = False
        except:
            pass
        
        return result
    
    def export_report(self, result: SSLAnalysisResult, filepath: str):
        """Exporta relatório para JSON"""
        report = {
            'host': result.host,
            'port': result.port,
            'score': result.score,
            'protocols': result.supported_protocols,
            'vulnerabilities': result.vulnerabilities,
            'recommendations': result.recommendations,
            'timestamp': datetime.now().isoformat()
        }
        
        if result.certificate:
            report['certificate'] = {
                'subject': result.certificate.subject,
                'issuer': result.certificate.issuer,
                'expires': result.certificate.not_after,
                'days_remaining': result.certificate.days_remaining,
                'expired': result.certificate.expired,
                'self_signed': result.certificate.self_signed
            }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Relatório salvo: {filepath}")


def main():
    """Função principal"""
    import sys
    
    print("\n" + "=" * 50)
    print("🔐 SSL/TLS Analyzer - Olho de Deus")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        host = input("\n🌐 Host para analisar: ").strip()
    else:
        host = sys.argv[1]
    
    port = 443
    if ':' in host:
        host, port = host.rsplit(':', 1)
        port = int(port)
    
    analyzer = SSLAnalyzer()
    result = analyzer.analyze(host, port)
    
    print("\n" + "=" * 50)
    print("📋 Recomendações:")
    for rec in result.recommendations:
        print(f"   • {rec}")
    
    print("\n✅ Análise concluída!")


if __name__ == "__main__":
    main()
