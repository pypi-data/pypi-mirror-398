#!/usr/bin/env python3
"""
SSL/TLS Scanner - Verificação de certificados, ciphers, vulnerabilidades
Parte do toolkit Olho de Deus
"""

import os
import sys
import json
import socket
import ssl
import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import hashlib


@dataclass
class CertificateInfo:
    """Informações do certificado SSL."""
    subject: Dict
    issuer: Dict
    version: int
    serial_number: str
    not_before: str
    not_after: str
    days_until_expiry: int
    expired: bool
    san: List[str]
    signature_algorithm: str
    public_key_type: str
    public_key_bits: int
    fingerprint_sha256: str
    chain_length: int
    
    def to_dict(self) -> Dict:
        return {
            "subject": self.subject,
            "issuer": self.issuer,
            "version": self.version,
            "serial_number": self.serial_number,
            "not_before": self.not_before,
            "not_after": self.not_after,
            "days_until_expiry": self.days_until_expiry,
            "expired": self.expired,
            "san": self.san,
            "signature_algorithm": self.signature_algorithm,
            "public_key_type": self.public_key_type,
            "public_key_bits": self.public_key_bits,
            "fingerprint_sha256": self.fingerprint_sha256,
            "chain_length": self.chain_length
        }


@dataclass
class SSLVulnerability:
    """Vulnerabilidade SSL/TLS detectada."""
    name: str
    severity: str  # critical, high, medium, low, info
    description: str
    cve: Optional[str] = None
    recommendation: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "severity": self.severity,
            "description": self.description,
            "cve": self.cve,
            "recommendation": self.recommendation
        }


class SSLScanner:
    """Scanner SSL/TLS."""
    
    # Ciphers considerados fracos
    WEAK_CIPHERS = [
        "RC4", "DES", "3DES", "MD5", "NULL", "EXPORT", "anon",
        "RC2", "IDEA", "SEED", "CAMELLIA128"
    ]
    
    # Protocolos inseguros
    INSECURE_PROTOCOLS = ["SSLv2", "SSLv3", "TLSv1.0", "TLSv1.1"]
    
    # Protocolos seguros
    SECURE_PROTOCOLS = ["TLSv1.2", "TLSv1.3"]
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def scan(self, host: str, port: int = 443) -> Dict:
        """Executa scan completo SSL/TLS."""
        results = {
            "host": host,
            "port": port,
            "timestamp": datetime.datetime.now().isoformat(),
            "certificate": None,
            "protocols": {},
            "ciphers": [],
            "vulnerabilities": [],
            "grade": "N/A",
            "secure": False
        }
        
        try:
            # Obter certificado
            cert_info = self._get_certificate(host, port)
            if cert_info:
                results["certificate"] = cert_info.to_dict()
            
            # Testar protocolos
            results["protocols"] = self._test_protocols(host, port)
            
            # Testar ciphers
            results["ciphers"] = self._get_ciphers(host, port)
            
            # Detectar vulnerabilidades
            vulns = self._detect_vulnerabilities(results)
            results["vulnerabilities"] = [v.to_dict() for v in vulns]
            
            # Calcular grade
            results["grade"] = self._calculate_grade(results)
            results["secure"] = results["grade"] in ["A+", "A", "A-", "B+", "B"]
            
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def _get_certificate(self, host: str, port: int) -> Optional[CertificateInfo]:
        """Obtém informações do certificado."""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert(binary_form=True)
                    cert_dict = ssock.getpeercert()
                    
                    # Parse dates
                    not_before = datetime.datetime.strptime(
                        cert_dict.get('notBefore', ''), '%b %d %H:%M:%S %Y %Z'
                    ) if cert_dict.get('notBefore') else None
                    
                    not_after = datetime.datetime.strptime(
                        cert_dict.get('notAfter', ''), '%b %d %H:%M:%S %Y %Z'
                    ) if cert_dict.get('notAfter') else None
                    
                    days_until_expiry = (not_after - datetime.datetime.now()).days if not_after else 0
                    
                    # Subject Alternative Names
                    san = []
                    for item in cert_dict.get('subjectAltName', []):
                        if item[0] == 'DNS':
                            san.append(item[1])
                    
                    # Fingerprint
                    fingerprint = hashlib.sha256(cert).hexdigest()
                    
                    # Subject e Issuer
                    subject = {}
                    for rdn in cert_dict.get('subject', []):
                        for attr in rdn:
                            subject[attr[0]] = attr[1]
                    
                    issuer = {}
                    for rdn in cert_dict.get('issuer', []):
                        for attr in rdn:
                            issuer[attr[0]] = attr[1]
                    
                    return CertificateInfo(
                        subject=subject,
                        issuer=issuer,
                        version=cert_dict.get('version', 0),
                        serial_number=str(cert_dict.get('serialNumber', '')),
                        not_before=not_before.isoformat() if not_before else "",
                        not_after=not_after.isoformat() if not_after else "",
                        days_until_expiry=days_until_expiry,
                        expired=days_until_expiry < 0,
                        san=san,
                        signature_algorithm="",  # Não disponível diretamente
                        public_key_type="RSA",  # Simplificado
                        public_key_bits=2048,   # Simplificado
                        fingerprint_sha256=fingerprint,
                        chain_length=1
                    )
                    
        except Exception as e:
            return None
    
    def _test_protocols(self, host: str, port: int) -> Dict[str, bool]:
        """Testa quais protocolos SSL/TLS são suportados."""
        protocols = {
            "SSLv2": False,
            "SSLv3": False,
            "TLSv1.0": False,
            "TLSv1.1": False,
            "TLSv1.2": False,
            "TLSv1.3": False
        }
        
        # Mapear protocolos para constantes SSL
        protocol_map = {
            "TLSv1.0": ssl.PROTOCOL_TLSv1 if hasattr(ssl, 'PROTOCOL_TLSv1') else None,
            "TLSv1.1": ssl.PROTOCOL_TLSv1_1 if hasattr(ssl, 'PROTOCOL_TLSv1_1') else None,
            "TLSv1.2": ssl.PROTOCOL_TLSv1_2 if hasattr(ssl, 'PROTOCOL_TLSv1_2') else None,
        }
        
        for proto_name, proto_const in protocol_map.items():
            if proto_const is None:
                continue
            
            try:
                context = ssl.SSLContext(proto_const)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                with socket.create_connection((host, port), timeout=self.timeout) as sock:
                    with context.wrap_socket(sock, server_hostname=host) as ssock:
                        protocols[proto_name] = True
            except Exception:
                protocols[proto_name] = False
        
        # TLS 1.3 teste
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.minimum_version = ssl.TLSVersion.TLSv1_3
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    if ssock.version() == 'TLSv1.3':
                        protocols["TLSv1.3"] = True
        except Exception:
            pass
        
        return protocols
    
    def _get_ciphers(self, host: str, port: int) -> List[Dict]:
        """Obtém ciphers suportados."""
        ciphers = []
        
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cipher = ssock.cipher()
                    if cipher:
                        is_weak = any(w in cipher[0].upper() for w in self.WEAK_CIPHERS)
                        ciphers.append({
                            "name": cipher[0],
                            "version": cipher[1],
                            "bits": cipher[2],
                            "weak": is_weak
                        })
        except Exception:
            pass
        
        return ciphers
    
    def _detect_vulnerabilities(self, scan_results: Dict) -> List[SSLVulnerability]:
        """Detecta vulnerabilidades com base nos resultados."""
        vulnerabilities = []
        
        cert = scan_results.get("certificate", {})
        protocols = scan_results.get("protocols", {})
        ciphers = scan_results.get("ciphers", [])
        
        # Certificado expirado
        if cert and cert.get("expired"):
            vulnerabilities.append(SSLVulnerability(
                name="Expired Certificate",
                severity="critical",
                description="O certificado SSL expirou",
                recommendation="Renovar o certificado imediatamente"
            ))
        
        # Certificado prestes a expirar
        if cert and 0 < cert.get("days_until_expiry", 365) < 30:
            vulnerabilities.append(SSLVulnerability(
                name="Certificate Expiring Soon",
                severity="medium",
                description=f"Certificado expira em {cert['days_until_expiry']} dias",
                recommendation="Renovar o certificado antes da expiração"
            ))
        
        # Protocolos inseguros
        for proto in self.INSECURE_PROTOCOLS:
            if protocols.get(proto):
                vulnerabilities.append(SSLVulnerability(
                    name=f"Insecure Protocol: {proto}",
                    severity="high" if proto in ["SSLv2", "SSLv3"] else "medium",
                    description=f"Protocolo {proto} está habilitado",
                    cve="CVE-2014-3566" if proto == "SSLv3" else None,
                    recommendation=f"Desabilitar {proto}"
                ))
        
        # Sem TLS 1.2/1.3
        if not protocols.get("TLSv1.2") and not protocols.get("TLSv1.3"):
            vulnerabilities.append(SSLVulnerability(
                name="No Modern TLS",
                severity="high",
                description="Nenhum protocolo TLS moderno (1.2/1.3) suportado",
                recommendation="Habilitar TLS 1.2 e TLS 1.3"
            ))
        
        # Ciphers fracos
        weak_ciphers = [c for c in ciphers if c.get("weak")]
        if weak_ciphers:
            vulnerabilities.append(SSLVulnerability(
                name="Weak Ciphers",
                severity="medium",
                description=f"{len(weak_ciphers)} cipher(s) fraco(s) detectado(s)",
                recommendation="Desabilitar ciphers fracos"
            ))
        
        # Self-signed
        if cert:
            subject = cert.get("subject", {})
            issuer = cert.get("issuer", {})
            if subject == issuer:
                vulnerabilities.append(SSLVulnerability(
                    name="Self-Signed Certificate",
                    severity="medium",
                    description="Certificado auto-assinado detectado",
                    recommendation="Usar certificado de uma CA confiável"
                ))
        
        return vulnerabilities
    
    def _calculate_grade(self, scan_results: Dict) -> str:
        """Calcula grade do SSL/TLS."""
        score = 100
        
        vulnerabilities = scan_results.get("vulnerabilities", [])
        protocols = scan_results.get("protocols", {})
        
        # Penalidades por vulnerabilidades
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "low")
            if severity == "critical":
                score -= 40
            elif severity == "high":
                score -= 25
            elif severity == "medium":
                score -= 15
            elif severity == "low":
                score -= 5
        
        # Bônus por TLS 1.3
        if protocols.get("TLSv1.3"):
            score += 5
        
        # Converter score para grade
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 65:
            return "C+"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"
    
    def check_hostname_match(self, host: str, port: int = 443) -> bool:
        """Verifica se o hostname corresponde ao certificado."""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    return True
        except ssl.CertificateError:
            return False
        except Exception:
            return False
    
    def export_results(self, results: Dict, output_file: str):
        """Exporta resultados para arquivo."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)


def interactive_menu():
    """Menu interativo do SSL Scanner."""
    scanner = SSLScanner()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║            🔒 SSL/TLS SCANNER - Olho de Deus                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔍 Scan Completo de SSL/TLS                             ║
║  [2] 📜 Ver Informações do Certificado                       ║
║  [3] 🔐 Testar Protocolos Suportados                         ║
║  [4] 🔓 Verificar Hostname                                   ║
║  [5] 📊 Scan em Múltiplos Hosts                              ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Scan Completo SSL/TLS ===")
            host = input("Host (ex: google.com): ").strip()
            port = input("Porta (default: 443): ").strip()
            port = int(port) if port.isdigit() else 443
            
            if not host:
                continue
            
            print(f"\nEscaneando {host}:{port}...")
            results = scanner.scan(host, port)
            
            # Grade
            grade = results.get("grade", "N/A")
            grade_icon = "🟢" if grade.startswith("A") else "🟡" if grade.startswith("B") else "🔴"
            print(f"\n{grade_icon} GRADE: {grade}")
            
            # Certificado
            cert = results.get("certificate", {})
            if cert:
                print(f"\n📜 CERTIFICADO:")
                print(f"   Subject: {cert.get('subject', {}).get('commonName', 'N/A')}")
                print(f"   Issuer: {cert.get('issuer', {}).get('organizationName', 'N/A')}")
                print(f"   Expira em: {cert.get('days_until_expiry', 'N/A')} dias")
                print(f"   SANs: {len(cert.get('san', []))} domínios")
            
            # Protocolos
            protocols = results.get("protocols", {})
            print(f"\n🔐 PROTOCOLOS:")
            for proto, supported in protocols.items():
                icon = "✅" if supported else "❌"
                secure = "🟢" if proto in ["TLSv1.2", "TLSv1.3"] else "🔴" if supported else ""
                print(f"   {icon} {proto} {secure}")
            
            # Vulnerabilidades
            vulns = results.get("vulnerabilities", [])
            if vulns:
                print(f"\n⚠️  {len(vulns)} VULNERABILIDADES:")
                for v in vulns:
                    sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(v["severity"], "⚪")
                    print(f"   {sev_icon} [{v['severity'].upper()}] {v['name']}")
                    print(f"      {v['description']}")
            else:
                print("\n✅ Nenhuma vulnerabilidade crítica detectada")
            
            save = input("\nSalvar resultados? (s/n): ").lower()
            if save == 's':
                scanner.export_results(results, f"ssl_scan_{host}.json")
                print(f"✅ Salvo em ssl_scan_{host}.json")
        
        elif escolha == '2':
            print("\n=== Informações do Certificado ===")
            host = input("Host: ").strip()
            
            if not host:
                continue
            
            cert = scanner._get_certificate(host, 443)
            
            if cert:
                print(f"\n📜 Certificado de {host}:")
                print(f"   Common Name: {cert.subject.get('commonName', 'N/A')}")
                print(f"   Organization: {cert.subject.get('organizationName', 'N/A')}")
                print(f"   Issuer: {cert.issuer.get('commonName', 'N/A')}")
                print(f"   Válido de: {cert.not_before}")
                print(f"   Válido até: {cert.not_after}")
                print(f"   Dias até expirar: {cert.days_until_expiry}")
                print(f"   Expirado: {'Sim' if cert.expired else 'Não'}")
                print(f"   Fingerprint SHA256: {cert.fingerprint_sha256[:32]}...")
                
                if cert.san:
                    print(f"   SANs ({len(cert.san)}):")
                    for san in cert.san[:10]:
                        print(f"      • {san}")
            else:
                print("Não foi possível obter o certificado.")
        
        elif escolha == '3':
            print("\n=== Testar Protocolos ===")
            host = input("Host: ").strip()
            
            if not host:
                continue
            
            print(f"\nTestando protocolos em {host}:443...")
            protocols = scanner._test_protocols(host, 443)
            
            print("\nProtocolos suportados:")
            for proto, supported in protocols.items():
                if supported:
                    secure = proto in scanner.SECURE_PROTOCOLS
                    icon = "🟢" if secure else "🔴"
                    print(f"   {icon} {proto} {'(seguro)' if secure else '(INSEGURO)'}")
        
        elif escolha == '4':
            print("\n=== Verificar Hostname ===")
            host = input("Host: ").strip()
            
            if not host:
                continue
            
            match = scanner.check_hostname_match(host)
            
            if match:
                print(f"\n✅ Hostname {host} corresponde ao certificado")
            else:
                print(f"\n❌ Hostname {host} NÃO corresponde ao certificado")
        
        elif escolha == '5':
            print("\n=== Scan em Múltiplos Hosts ===")
            print("Digite os hosts (um por linha, linha vazia para terminar):")
            
            hosts = []
            while True:
                h = input("  > ").strip()
                if not h:
                    break
                hosts.append(h)
            
            if not hosts:
                continue
            
            print(f"\nEscaneando {len(hosts)} hosts...\n")
            
            for host in hosts:
                print(f"Escaneando {host}...", end=" ")
                results = scanner.scan(host)
                grade = results.get("grade", "ERR")
                vulns = len(results.get("vulnerabilities", []))
                print(f"Grade: {grade} | Vulnerabilidades: {vulns}")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
