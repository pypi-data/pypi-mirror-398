#!/usr/bin/env python3
"""
API Tester - Teste de segurança de APIs REST/GraphQL
Parte do toolkit Olho de Deus
"""

import os
import sys
import re
import json
import time
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except ImportError:
    requests = None


@dataclass
class APIEndpoint:
    """Endpoint de API descoberto."""
    method: str
    path: str
    parameters: List[Dict]
    auth_required: bool
    response_code: int
    response_type: str
    vulnerabilities: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "method": self.method,
            "path": self.path,
            "parameters": self.parameters,
            "auth_required": self.auth_required,
            "response_code": self.response_code,
            "response_type": self.response_type,
            "vulnerabilities": self.vulnerabilities
        }


@dataclass
class APIVulnerability:
    """Vulnerabilidade de API."""
    name: str
    severity: str
    endpoint: str
    description: str
    payload: Optional[str]
    evidence: str
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "severity": self.severity,
            "endpoint": self.endpoint,
            "description": self.description,
            "payload": self.payload,
            "evidence": self.evidence
        }


class APISecurityChecker:
    """Verificador de segurança de API."""
    
    # Headers de segurança importantes
    SECURITY_HEADERS = [
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", ["DENY", "SAMEORIGIN"]),
        ("Strict-Transport-Security", ""),
        ("Content-Security-Policy", ""),
        ("X-XSS-Protection", ""),
        ("Cache-Control", "no-store"),
    ]
    
    # Payloads de teste
    INJECTION_PAYLOADS = {
        "sqli": ["'", "\"", "1 OR 1=1", "1' OR '1'='1", "1; DROP TABLE users--"],
        "nosqli": ["{'$gt': ''}", "{\"$ne\": null}", "[$ne]=1"],
        "xss": ["<script>alert(1)</script>", "javascript:alert(1)", "'\"><img src=x>"],
        "ssti": ["{{7*7}}", "${7*7}", "<%= 7*7 %>"],
        "ssrf": ["http://127.0.0.1", "http://localhost", "http://169.254.169.254"],
        "path_traversal": ["../../../etc/passwd", "..\\..\\..\\windows\\system32\\config\\sam"],
    }
    
    def __init__(self, base_url: str, auth_header: Optional[Dict] = None, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session() if requests else None
        self.auth_header = auth_header or {}
        
        if self.session:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 API-Tester/1.0',
                'Accept': 'application/json',
                **self.auth_header
            })
    
    def check_authentication(self, endpoint: str) -> Dict:
        """Testa autenticação em um endpoint."""
        results = {
            "endpoint": endpoint,
            "requires_auth": False,
            "auth_bypass_possible": False,
            "issues": []
        }
        
        full_url = urljoin(self.base_url, endpoint)
        
        try:
            # Requisição sem autenticação
            temp_session = requests.Session()
            temp_session.headers.update({'Accept': 'application/json'})
            
            r_no_auth = temp_session.get(full_url, timeout=self.timeout, verify=False)
            
            if r_no_auth.status_code == 401 or r_no_auth.status_code == 403:
                results["requires_auth"] = True
                
                # Tentar bypass
                bypass_headers = [
                    {"X-Original-URL": endpoint},
                    {"X-Rewrite-URL": endpoint},
                    {"X-Forwarded-For": "127.0.0.1"},
                    {"X-Forwarded-Host": "localhost"},
                    {"X-Custom-IP-Authorization": "127.0.0.1"},
                ]
                
                for bypass_header in bypass_headers:
                    try:
                        r_bypass = temp_session.get(
                            full_url, 
                            headers=bypass_header,
                            timeout=self.timeout,
                            verify=False
                        )
                        if r_bypass.status_code == 200:
                            results["auth_bypass_possible"] = True
                            results["issues"].append({
                                "type": "auth_bypass",
                                "header": list(bypass_header.keys())[0],
                                "severity": "critical"
                            })
                    except Exception:
                        pass
            else:
                results["requires_auth"] = False
                if r_no_auth.status_code == 200:
                    results["issues"].append({
                        "type": "no_auth_required",
                        "severity": "medium",
                        "message": "Endpoint acessível sem autenticação"
                    })
        
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def check_rate_limiting(self, endpoint: str, requests_count: int = 20) -> Dict:
        """Verifica rate limiting."""
        results = {
            "endpoint": endpoint,
            "rate_limited": False,
            "requests_before_limit": 0,
            "limit_type": None
        }
        
        full_url = urljoin(self.base_url, endpoint)
        
        try:
            for i in range(requests_count):
                r = self.session.get(full_url, timeout=self.timeout, verify=False)
                
                if r.status_code == 429:
                    results["rate_limited"] = True
                    results["requests_before_limit"] = i + 1
                    results["limit_type"] = "429 Too Many Requests"
                    break
                
                # Verificar headers de rate limit
                if "X-RateLimit-Remaining" in r.headers:
                    remaining = int(r.headers.get("X-RateLimit-Remaining", 0))
                    if remaining == 0:
                        results["rate_limited"] = True
                        results["requests_before_limit"] = i + 1
                        results["limit_type"] = "X-RateLimit-Remaining: 0"
                        break
                
                time.sleep(0.1)  # Pequeno delay
        
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def check_security_headers(self, endpoint: str = "/") -> Dict:
        """Verifica headers de segurança."""
        results = {
            "endpoint": endpoint,
            "headers_present": [],
            "headers_missing": [],
            "issues": []
        }
        
        full_url = urljoin(self.base_url, endpoint)
        
        try:
            r = self.session.get(full_url, timeout=self.timeout, verify=False)
            
            for header_name, expected_value in self.SECURITY_HEADERS:
                header_value = r.headers.get(header_name)
                
                if header_value:
                    results["headers_present"].append({
                        "name": header_name,
                        "value": header_value
                    })
                else:
                    results["headers_missing"].append(header_name)
                    results["issues"].append({
                        "type": "missing_header",
                        "header": header_name,
                        "severity": "low"
                    })
            
            # CORS
            if "Access-Control-Allow-Origin" in r.headers:
                cors_origin = r.headers["Access-Control-Allow-Origin"]
                if cors_origin == "*":
                    results["issues"].append({
                        "type": "cors_wildcard",
                        "value": cors_origin,
                        "severity": "medium"
                    })
        
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def test_injection(self, endpoint: str, method: str = "GET", 
                       param_name: str = "id") -> List[APIVulnerability]:
        """Testa injeção em um parâmetro."""
        vulnerabilities = []
        full_url = urljoin(self.base_url, endpoint)
        
        for injection_type, payloads in self.INJECTION_PAYLOADS.items():
            for payload in payloads:
                try:
                    if method.upper() == "GET":
                        test_url = f"{full_url}?{param_name}={payload}"
                        r = self.session.get(test_url, timeout=self.timeout, verify=False)
                    else:
                        r = self.session.post(
                            full_url,
                            json={param_name: payload},
                            timeout=self.timeout,
                            verify=False
                        )
                    
                    # Detectar vulnerabilidades
                    is_vulnerable = False
                    evidence = ""
                    
                    # SQL Injection
                    if injection_type == "sqli":
                        sql_errors = [
                            "sql syntax", "mysql_", "ora-", "postgresql",
                            "sqlite", "mssql", "syntax error", "unclosed quotation"
                        ]
                        for err in sql_errors:
                            if err in r.text.lower():
                                is_vulnerable = True
                                evidence = f"SQL error detectado: {err}"
                                break
                    
                    # SSTI
                    elif injection_type == "ssti":
                        if "49" in r.text and "{{7*7}}" in payload:
                            is_vulnerable = True
                            evidence = "Template injection: {{7*7}} = 49"
                    
                    # XSS (reflected)
                    elif injection_type == "xss":
                        if payload in r.text:
                            is_vulnerable = True
                            evidence = "XSS payload reflected in response"
                    
                    if is_vulnerable:
                        vulnerabilities.append(APIVulnerability(
                            name=f"{injection_type.upper()} Injection",
                            severity="high" if injection_type in ["sqli", "ssti"] else "medium",
                            endpoint=endpoint,
                            description=f"Endpoint vulnerável a {injection_type}",
                            payload=payload,
                            evidence=evidence
                        ))
                        break  # Um payload por tipo é suficiente
                
                except Exception:
                    pass
        
        return vulnerabilities
    
    def test_idor(self, endpoint_template: str, id_range: range = range(1, 10)) -> List[APIVulnerability]:
        """Testa IDOR (Insecure Direct Object Reference)."""
        vulnerabilities = []
        accessible_ids = []
        
        for test_id in id_range:
            endpoint = endpoint_template.replace("{id}", str(test_id))
            full_url = urljoin(self.base_url, endpoint)
            
            try:
                r = self.session.get(full_url, timeout=self.timeout, verify=False)
                
                if r.status_code == 200:
                    accessible_ids.append(test_id)
            except Exception:
                pass
        
        if len(accessible_ids) > 1:
            vulnerabilities.append(APIVulnerability(
                name="IDOR - Insecure Direct Object Reference",
                severity="high",
                endpoint=endpoint_template,
                description=f"Múltiplos objetos acessíveis: {accessible_ids}",
                payload=None,
                evidence=f"IDs acessíveis: {accessible_ids}"
            ))
        
        return vulnerabilities
    
    def test_http_methods(self, endpoint: str) -> Dict:
        """Testa métodos HTTP permitidos."""
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "TRACE"]
        results = {
            "endpoint": endpoint,
            "allowed_methods": [],
            "dangerous_methods": [],
            "cors_preflight": False
        }
        
        full_url = urljoin(self.base_url, endpoint)
        
        for method in methods:
            try:
                r = self.session.request(
                    method, 
                    full_url, 
                    timeout=self.timeout,
                    verify=False
                )
                
                if r.status_code not in [405, 501]:
                    results["allowed_methods"].append(method)
                    
                    if method in ["DELETE", "PUT", "PATCH", "TRACE"]:
                        results["dangerous_methods"].append(method)
                
                if method == "OPTIONS" and r.status_code == 200:
                    results["cors_preflight"] = True
            
            except Exception:
                pass
        
        return results


class GraphQLTester:
    """Testador de segurança GraphQL."""
    
    # Queries de introspection
    INTROSPECTION_QUERY = """
    query IntrospectionQuery {
        __schema {
            queryType { name }
            mutationType { name }
            types {
                name
                kind
                fields {
                    name
                    type { name }
                }
            }
        }
    }
    """
    
    def __init__(self, endpoint: str, auth_header: Optional[Dict] = None, timeout: int = 10):
        self.endpoint = endpoint
        self.timeout = timeout
        self.session = requests.Session() if requests else None
        self.auth_header = auth_header or {}
        
        if self.session:
            self.session.headers.update({
                'Content-Type': 'application/json',
                **self.auth_header
            })
    
    def test_introspection(self) -> Dict:
        """Testa se introspection está habilitada."""
        results = {
            "introspection_enabled": False,
            "schema": None,
            "severity": "medium"
        }
        
        try:
            r = self.session.post(
                self.endpoint,
                json={"query": self.INTROSPECTION_QUERY},
                timeout=self.timeout,
                verify=False
            )
            
            if r.status_code == 200:
                data = r.json()
                if "data" in data and "__schema" in data.get("data", {}):
                    results["introspection_enabled"] = True
                    results["schema"] = data["data"]["__schema"]
        
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def test_batch_queries(self) -> Dict:
        """Testa vulnerabilidade de batch queries."""
        results = {
            "batch_enabled": False,
            "severity": "low"
        }
        
        batch_query = [
            {"query": "{ __typename }"},
            {"query": "{ __typename }"},
            {"query": "{ __typename }"}
        ]
        
        try:
            r = self.session.post(
                self.endpoint,
                json=batch_query,
                timeout=self.timeout,
                verify=False
            )
            
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) == 3:
                    results["batch_enabled"] = True
                    results["severity"] = "medium"
        
        except Exception:
            pass
        
        return results
    
    def test_depth_limit(self) -> Dict:
        """Testa limite de profundidade de queries."""
        results = {
            "depth_limited": False,
            "max_depth_tested": 0
        }
        
        # Query profunda
        deep_query = "{ __typename "
        for i in range(20):
            deep_query += "{ __typename "
        for i in range(20):
            deep_query += " }"
        deep_query += " }"
        
        try:
            r = self.session.post(
                self.endpoint,
                json={"query": deep_query},
                timeout=self.timeout,
                verify=False
            )
            
            if r.status_code == 200:
                data = r.json()
                if "errors" in data:
                    results["depth_limited"] = True
            
            results["max_depth_tested"] = 20
        
        except Exception:
            pass
        
        return results


def interactive_menu():
    """Menu interativo do API Tester."""
    if not requests:
        print("❌ Módulo requests não encontrado. Instale com: pip install requests")
        input("Pressione Enter...")
        return
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║             🔌 API TESTER - Olho de Deus                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔐 Testar Autenticação                                  ║
║  [2] 🚦 Verificar Rate Limiting                              ║
║  [3] 🛡️  Verificar Headers de Segurança                      ║
║  [4] 💉 Testar Injeções                                      ║
║  [5] 🔓 Testar IDOR                                          ║
║  [6] 📋 Testar Métodos HTTP                                  ║
║  [7] 📊 GraphQL - Introspection                              ║
║  [8] 🔍 Scan Completo                                        ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Testar Autenticação ===")
            base_url = input("URL Base da API: ").strip()
            endpoint = input("Endpoint (ex: /api/users): ").strip()
            
            if not base_url or not endpoint:
                continue
            
            checker = APISecurityChecker(base_url)
            result = checker.check_authentication(endpoint)
            
            print(f"\n🔐 Resultado de autenticação para {endpoint}:")
            print(f"   Requer autenticação: {'Sim' if result['requires_auth'] else 'Não'}")
            print(f"   Bypass possível: {'⚠️ SIM' if result['auth_bypass_possible'] else 'Não'}")
            
            if result.get("issues"):
                print("\n   ⚠️ Issues encontrados:")
                for issue in result["issues"]:
                    print(f"      [{issue['severity'].upper()}] {issue['type']}")
        
        elif escolha == '2':
            print("\n=== Verificar Rate Limiting ===")
            base_url = input("URL Base da API: ").strip()
            endpoint = input("Endpoint: ").strip()
            count = input("Número de requisições (default: 20): ").strip()
            count = int(count) if count.isdigit() else 20
            
            if not base_url or not endpoint:
                continue
            
            checker = APISecurityChecker(base_url)
            print(f"\nEnviando {count} requisições...")
            result = checker.check_rate_limiting(endpoint, count)
            
            if result["rate_limited"]:
                print(f"\n✅ Rate limiting detectado")
                print(f"   Requisições antes do limite: {result['requests_before_limit']}")
                print(f"   Tipo: {result['limit_type']}")
            else:
                print(f"\n⚠️ Nenhum rate limiting detectado após {count} requisições")
        
        elif escolha == '3':
            print("\n=== Headers de Segurança ===")
            base_url = input("URL Base: ").strip()
            
            if not base_url:
                continue
            
            checker = APISecurityChecker(base_url)
            result = checker.check_security_headers()
            
            print("\n🛡️ Headers de Segurança:")
            
            if result["headers_present"]:
                print("\n   ✅ Presentes:")
                for h in result["headers_present"]:
                    print(f"      • {h['name']}: {h['value'][:50]}")
            
            if result["headers_missing"]:
                print("\n   ❌ Ausentes:")
                for h in result["headers_missing"]:
                    print(f"      • {h}")
            
            if result.get("issues"):
                print("\n   ⚠️ Issues:")
                for issue in result["issues"]:
                    print(f"      [{issue['severity'].upper()}] {issue['type']}")
        
        elif escolha == '4':
            print("\n=== Testar Injeções ===")
            base_url = input("URL Base: ").strip()
            endpoint = input("Endpoint (ex: /api/users): ").strip()
            param = input("Parâmetro a testar (default: id): ").strip() or "id"
            method = input("Método (GET/POST, default: GET): ").strip().upper() or "GET"
            
            if not base_url or not endpoint:
                continue
            
            checker = APISecurityChecker(base_url)
            print(f"\nTestando injeções em {endpoint}...")
            
            vulns = checker.test_injection(endpoint, method, param)
            
            if vulns:
                print(f"\n⚠️ {len(vulns)} vulnerabilidades encontradas:")
                for v in vulns:
                    print(f"\n   [{v.severity.upper()}] {v.name}")
                    print(f"   Payload: {v.payload}")
                    print(f"   Evidência: {v.evidence}")
            else:
                print("\n✅ Nenhuma vulnerabilidade de injeção detectada")
        
        elif escolha == '5':
            print("\n=== Testar IDOR ===")
            base_url = input("URL Base: ").strip()
            endpoint = input("Endpoint com {id} (ex: /api/users/{id}): ").strip()
            
            if not base_url or not endpoint or "{id}" not in endpoint:
                print("Endpoint deve conter {id} como placeholder")
                input("Enter para continuar...")
                continue
            
            checker = APISecurityChecker(base_url)
            print(f"\nTestando IDOR em {endpoint}...")
            
            vulns = checker.test_idor(endpoint)
            
            if vulns:
                for v in vulns:
                    print(f"\n⚠️ [{v.severity.upper()}] {v.name}")
                    print(f"   {v.evidence}")
            else:
                print("\n✅ Nenhum IDOR detectado")
        
        elif escolha == '6':
            print("\n=== Testar Métodos HTTP ===")
            base_url = input("URL Base: ").strip()
            endpoint = input("Endpoint: ").strip()
            
            if not base_url or not endpoint:
                continue
            
            checker = APISecurityChecker(base_url)
            result = checker.test_http_methods(endpoint)
            
            print(f"\n📋 Métodos HTTP para {endpoint}:")
            print(f"   Permitidos: {', '.join(result['allowed_methods'])}")
            
            if result["dangerous_methods"]:
                print(f"   ⚠️ Potencialmente perigosos: {', '.join(result['dangerous_methods'])}")
            
            print(f"   CORS Preflight: {'Sim' if result['cors_preflight'] else 'Não'}")
        
        elif escolha == '7':
            print("\n=== GraphQL Introspection ===")
            endpoint = input("Endpoint GraphQL (ex: https://api.example.com/graphql): ").strip()
            
            if not endpoint:
                continue
            
            tester = GraphQLTester(endpoint)
            
            print("\nTestando introspection...")
            result = tester.test_introspection()
            
            if result["introspection_enabled"]:
                print("\n⚠️ Introspection HABILITADA")
                
                if result.get("schema"):
                    types = result["schema"].get("types", [])
                    print(f"   Tipos encontrados: {len(types)}")
                    
                    # Mostrar alguns tipos
                    for t in types[:10]:
                        if not t["name"].startswith("_"):
                            print(f"      • {t['name']}")
            else:
                print("\n✅ Introspection desabilitada")
            
            print("\nTestando batch queries...")
            batch_result = tester.test_batch_queries()
            print(f"   Batch queries: {'Habilitado' if batch_result['batch_enabled'] else 'Desabilitado'}")
        
        elif escolha == '8':
            print("\n=== Scan Completo ===")
            base_url = input("URL Base da API: ").strip()
            endpoints = input("Endpoints (separados por vírgula): ").strip().split(",")
            
            if not base_url or not endpoints:
                continue
            
            checker = APISecurityChecker(base_url)
            
            print(f"\n🔍 Iniciando scan completo de {len(endpoints)} endpoints...\n")
            
            all_results = {
                "base_url": base_url,
                "endpoints": [],
                "vulnerabilities": [],
                "summary": {
                    "total_endpoints": len(endpoints),
                    "vulnerable": 0,
                    "secure": 0
                }
            }
            
            for ep in endpoints:
                ep = ep.strip()
                print(f"Analisando {ep}...")
                
                ep_result = {
                    "endpoint": ep,
                    "auth": checker.check_authentication(ep),
                    "headers": checker.check_security_headers(ep),
                    "methods": checker.test_http_methods(ep),
                    "issues": []
                }
                
                # Coletar issues
                if ep_result["auth"].get("auth_bypass_possible"):
                    ep_result["issues"].append("Auth Bypass")
                
                if len(ep_result["headers"].get("headers_missing", [])) > 3:
                    ep_result["issues"].append("Missing Security Headers")
                
                if ep_result["methods"].get("dangerous_methods"):
                    ep_result["issues"].append("Dangerous Methods Allowed")
                
                if ep_result["issues"]:
                    all_results["summary"]["vulnerable"] += 1
                else:
                    all_results["summary"]["secure"] += 1
                
                all_results["endpoints"].append(ep_result)
            
            print(f"\n📊 RESUMO:")
            print(f"   Total de endpoints: {all_results['summary']['total_endpoints']}")
            print(f"   Com issues: {all_results['summary']['vulnerable']}")
            print(f"   Seguros: {all_results['summary']['secure']}")
            
            save = input("\nSalvar resultados? (s/n): ").lower()
            if save == 's':
                with open("api_scan_results.json", 'w') as f:
                    json.dump(all_results, f, indent=2, default=str)
                print("✅ Salvo em api_scan_results.json")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
