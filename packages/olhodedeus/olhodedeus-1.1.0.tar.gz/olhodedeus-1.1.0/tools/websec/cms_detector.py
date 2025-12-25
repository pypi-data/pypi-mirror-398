#!/usr/bin/env python3
"""
CMS Detector - Detecção de CMS e vulnerabilidades conhecidas
Parte do toolkit Olho de Deus
"""

import os
import sys
import re
import json
import hashlib
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

try:
    import requests
except ImportError:
    requests = None


@dataclass
class CMSResult:
    """Resultado da detecção de CMS."""
    name: str
    version: Optional[str]
    confidence: int  # 0-100
    detection_method: str
    vulnerabilities: List[Dict]
    admin_paths: List[str]
    plugins: List[str]
    themes: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "confidence": self.confidence,
            "detection_method": self.detection_method,
            "vulnerabilities": self.vulnerabilities,
            "admin_paths": self.admin_paths,
            "plugins": self.plugins,
            "themes": self.themes
        }


class CMSSignatures:
    """Assinaturas para detecção de CMS."""
    
    # Assinaturas de headers
    HEADERS = {
        "wordpress": [
            ("x-powered-by", "wordpress"),
            ("link", "wp-json"),
        ],
        "drupal": [
            ("x-drupal-cache", ""),
            ("x-generator", "drupal"),
            ("x-drupal-dynamic-cache", ""),
        ],
        "joomla": [
            ("x-content-encoded-by", "joomla"),
        ],
        "magento": [
            ("set-cookie", "frontend="),
            ("set-cookie", "adminhtml="),
        ],
        "shopify": [
            ("x-shopid", ""),
            ("x-shardid", ""),
        ],
        "wix": [
            ("x-wix-request-id", ""),
        ],
        "squarespace": [
            ("server", "squarespace"),
        ],
    }
    
    # Assinaturas de meta tags
    META_TAGS = {
        "wordpress": [
            r'<meta name="generator" content="WordPress[^"]*"',
        ],
        "drupal": [
            r'<meta name="Generator" content="Drupal[^"]*"',
            r'Drupal\.settings',
        ],
        "joomla": [
            r'<meta name="generator" content="Joomla[^"]*"',
        ],
        "magento": [
            r'skin/frontend/',
            r'Mage\.Cookies',
        ],
        "prestashop": [
            r'<meta name="generator" content="PrestaShop"',
            r'prestashop\.css',
        ],
        "ghost": [
            r'<meta name="generator" content="Ghost[^"]*"',
        ],
        "typo3": [
            r'<meta name="generator" content="TYPO3[^"]*"',
            r'typo3conf/',
        ],
    }
    
    # Caminhos característicos
    PATHS = {
        "wordpress": [
            "/wp-admin/",
            "/wp-content/",
            "/wp-includes/",
            "/wp-login.php",
            "/xmlrpc.php",
            "/wp-json/",
        ],
        "drupal": [
            "/sites/default/",
            "/core/",
            "/modules/",
            "/profiles/",
            "/themes/",
            "/CHANGELOG.txt",
        ],
        "joomla": [
            "/administrator/",
            "/components/",
            "/modules/",
            "/plugins/",
            "/templates/",
            "/configuration.php",
        ],
        "magento": [
            "/admin/",
            "/app/",
            "/skin/",
            "/js/mage/",
            "/media/catalog/",
        ],
        "laravel": [
            "/storage/",
            "/.env",
            "/artisan",
        ],
        "django": [
            "/admin/",
            "/static/admin/",
        ],
        "rails": [
            "/assets/",
            "/rails/",
        ],
    }
    
    # Versões por arquivos
    VERSION_FILES = {
        "wordpress": [
            ("/wp-includes/version.php", r"\$wp_version\s*=\s*['\"]([^'\"]+)['\"]"),
            ("/readme.html", r"Version\s+([\d.]+)"),
            ("/feed/", r"<generator>.*?v=([\d.]+)</generator>"),
        ],
        "drupal": [
            ("/CHANGELOG.txt", r"Drupal\s+([\d.]+)"),
            ("/core/includes/bootstrap.inc", r"VERSION\s*=\s*['\"]([^'\"]+)['\"]"),
        ],
        "joomla": [
            ("/language/en-GB/en-GB.xml", r'<version>([\d.]+)</version>'),
            ("/administrator/manifests/files/joomla.xml", r'<version>([\d.]+)</version>'),
        ],
    }
    
    # Caminhos de admin
    ADMIN_PATHS = {
        "wordpress": ["/wp-admin/", "/wp-login.php"],
        "drupal": ["/user/login", "/admin"],
        "joomla": ["/administrator/"],
        "magento": ["/admin/", "/index.php/admin/"],
        "prestashop": ["/admin/", "/adminXXXX/"],
        "opencart": ["/admin/"],
    }


class CMSVulnerabilityDB:
    """Base de dados de vulnerabilidades conhecidas por CMS."""
    
    # Vulnerabilidades conhecidas (simplificado)
    VULNERABILITIES = {
        "wordpress": {
            "4.7.0": [
                {"cve": "CVE-2017-1001000", "severity": "critical", "name": "REST API Content Injection"},
            ],
            "4.7.1": [
                {"cve": "CVE-2017-1001000", "severity": "critical", "name": "REST API Content Injection"},
            ],
            "5.0.0": [
                {"cve": "CVE-2019-8942", "severity": "high", "name": "Path Traversal via Meta Data"},
            ],
            "general": [
                {"name": "XML-RPC Amplification", "severity": "medium", "path": "/xmlrpc.php"},
                {"name": "User Enumeration", "severity": "low", "path": "/?author=1"},
            ],
        },
        "drupal": {
            "7.0": [
                {"cve": "CVE-2018-7600", "severity": "critical", "name": "Drupalgeddon 2"},
            ],
            "8.0": [
                {"cve": "CVE-2019-6340", "severity": "critical", "name": "Remote Code Execution"},
            ],
            "general": [
                {"name": "Admin Login Exposed", "severity": "info", "path": "/user/login"},
            ],
        },
        "joomla": {
            "3.4.4": [
                {"cve": "CVE-2015-8562", "severity": "critical", "name": "Object Injection RCE"},
            ],
            "general": [
                {"name": "Admin Path Exposed", "severity": "info", "path": "/administrator/"},
            ],
        },
    }
    
    @classmethod
    def get_vulnerabilities(cls, cms: str, version: Optional[str] = None) -> List[Dict]:
        """Retorna vulnerabilidades para um CMS e versão."""
        vulns = []
        cms = cms.lower()
        
        if cms not in cls.VULNERABILITIES:
            return vulns
        
        # Vulnerabilidades gerais
        vulns.extend(cls.VULNERABILITIES[cms].get("general", []))
        
        # Vulnerabilidades específicas da versão
        if version:
            # Versão exata
            vulns.extend(cls.VULNERABILITIES[cms].get(version, []))
            
            # Versões menores
            major_version = version.split('.')[0] + ".0"
            vulns.extend(cls.VULNERABILITIES[cms].get(major_version, []))
        
        return vulns


class CMSDetector:
    """Detector de CMS."""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session() if requests else None
        if self.session:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
    
    def detect(self, url: str) -> CMSResult:
        """Detecta CMS em uma URL."""
        if not self.session:
            return CMSResult(
                name="Unknown",
                version=None,
                confidence=0,
                detection_method="error",
                vulnerabilities=[],
                admin_paths=[],
                plugins=[],
                themes=[]
            )
        
        # Normalizar URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Resultados de detecção
        detections = {}  # cms: confidence
        methods = {}  # cms: method
        
        try:
            # Verificar página principal
            response = self.session.get(url, timeout=self.timeout, verify=False)
            
            # Verificar headers
            for cms, signatures in CMSSignatures.HEADERS.items():
                for header, value in signatures:
                    header_value = response.headers.get(header, '').lower()
                    if value.lower() in header_value:
                        detections[cms] = detections.get(cms, 0) + 30
                        methods[cms] = "header"
            
            # Verificar meta tags e conteúdo
            content = response.text
            for cms, patterns in CMSSignatures.META_TAGS.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        detections[cms] = detections.get(cms, 0) + 25
                        methods[cms] = "meta_tag"
            
            # Verificar caminhos
            for cms, paths in CMSSignatures.PATHS.items():
                for path in paths[:3]:  # Limitar requisições
                    try:
                        check_url = urljoin(url, path)
                        r = self.session.head(check_url, timeout=5, allow_redirects=True)
                        if r.status_code == 200:
                            detections[cms] = detections.get(cms, 0) + 15
                            methods[cms] = "path"
                    except Exception:
                        pass
            
        except Exception as e:
            pass
        
        # Determinar CMS mais provável
        if not detections:
            return CMSResult(
                name="Unknown",
                version=None,
                confidence=0,
                detection_method="none",
                vulnerabilities=[],
                admin_paths=[],
                plugins=[],
                themes=[]
            )
        
        # CMS com maior confiança
        best_cms = max(detections, key=detections.get)
        confidence = min(detections[best_cms], 100)
        
        # Detectar versão
        version = self._detect_version(url, best_cms)
        
        # Obter vulnerabilidades
        vulns = CMSVulnerabilityDB.get_vulnerabilities(best_cms, version)
        
        # Admin paths
        admin_paths = CMSSignatures.ADMIN_PATHS.get(best_cms, [])
        
        # Detectar plugins/themes
        plugins, themes = self._detect_extensions(url, best_cms)
        
        return CMSResult(
            name=best_cms.title(),
            version=version,
            confidence=confidence,
            detection_method=methods.get(best_cms, "unknown"),
            vulnerabilities=vulns,
            admin_paths=admin_paths,
            plugins=plugins,
            themes=themes
        )
    
    def _detect_version(self, url: str, cms: str) -> Optional[str]:
        """Tenta detectar a versão do CMS."""
        if cms not in CMSSignatures.VERSION_FILES:
            return None
        
        for path, pattern in CMSSignatures.VERSION_FILES[cms]:
            try:
                check_url = urljoin(url, path)
                r = self.session.get(check_url, timeout=5, verify=False)
                if r.status_code == 200:
                    match = re.search(pattern, r.text)
                    if match:
                        return match.group(1)
            except Exception:
                pass
        
        return None
    
    def _detect_extensions(self, url: str, cms: str) -> Tuple[List[str], List[str]]:
        """Detecta plugins e temas."""
        plugins = []
        themes = []
        
        if cms == "wordpress":
            # Verificar plugins comuns
            common_plugins = [
                "akismet", "contact-form-7", "yoast-seo", "woocommerce",
                "elementor", "jetpack", "wordfence", "classic-editor",
                "wpforms-lite", "really-simple-ssl"
            ]
            
            for plugin in common_plugins:
                try:
                    plugin_url = urljoin(url, f"/wp-content/plugins/{plugin}/")
                    r = self.session.head(plugin_url, timeout=3, verify=False)
                    if r.status_code in [200, 403]:
                        plugins.append(plugin)
                except Exception:
                    pass
            
            # Verificar temas comuns
            common_themes = [
                "twentytwentyone", "twentytwentytwo", "astra", "oceanwp",
                "generatepress", "neve", "hello-elementor"
            ]
            
            for theme in common_themes:
                try:
                    theme_url = urljoin(url, f"/wp-content/themes/{theme}/")
                    r = self.session.head(theme_url, timeout=3, verify=False)
                    if r.status_code in [200, 403]:
                        themes.append(theme)
                except Exception:
                    pass
        
        return plugins, themes
    
    def fingerprint(self, url: str) -> Dict:
        """Fingerprint detalhado do site."""
        if not self.session:
            return {"error": "requests não instalado"}
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        result = {
            "url": url,
            "cms": None,
            "server": None,
            "powered_by": None,
            "technologies": [],
            "headers": {},
            "cookies": [],
        }
        
        try:
            response = self.session.get(url, timeout=self.timeout, verify=False)
            
            # Headers interessantes
            result["server"] = response.headers.get("Server")
            result["powered_by"] = response.headers.get("X-Powered-By")
            
            # Tecnologias detectadas
            techs = set()
            
            # PHP
            if "php" in result.get("powered_by", "").lower():
                techs.add("PHP")
            
            # JavaScript frameworks
            content = response.text
            if "react" in content.lower() or "reactdom" in content.lower():
                techs.add("React")
            if "vue" in content.lower():
                techs.add("Vue.js")
            if "angular" in content.lower():
                techs.add("Angular")
            if "jquery" in content.lower():
                techs.add("jQuery")
            if "bootstrap" in content.lower():
                techs.add("Bootstrap")
            
            # Cookies
            for cookie in response.cookies:
                result["cookies"].append({
                    "name": cookie.name,
                    "secure": cookie.secure,
                    "httponly": cookie.has_nonstandard_attr("HttpOnly"),
                })
            
            result["technologies"] = list(techs)
            
            # Detectar CMS
            cms_result = self.detect(url)
            result["cms"] = cms_result.to_dict()
            
        except Exception as e:
            result["error"] = str(e)
        
        return result


def interactive_menu():
    """Menu interativo do CMS Detector."""
    if not requests:
        print("❌ Módulo requests não encontrado. Instale com: pip install requests")
        input("Pressione Enter...")
        return
    
    detector = CMSDetector()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║             🔍 CMS DETECTOR - Olho de Deus                   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔍 Detectar CMS                                         ║
║  [2] 🔬 Fingerprint Completo                                 ║
║  [3] 📋 Listar Vulnerabilidades por CMS                      ║
║  [4] 🌐 Scan em Múltiplos Sites                              ║
║  [5] 📊 Verificar Plugins/Temas WordPress                    ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Detectar CMS ===")
            url = input("URL: ").strip()
            
            if not url:
                continue
            
            print(f"\nAnalisando {url}...")
            result = detector.detect(url)
            
            if result.name != "Unknown":
                print(f"\n✅ CMS Detectado: {result.name}")
                print(f"   Versão: {result.version or 'Não identificada'}")
                print(f"   Confiança: {result.confidence}%")
                print(f"   Método: {result.detection_method}")
                
                if result.admin_paths:
                    print(f"\n   📂 Caminhos de Admin:")
                    for path in result.admin_paths:
                        print(f"      • {path}")
                
                if result.plugins:
                    print(f"\n   🔌 Plugins ({len(result.plugins)}):")
                    for plugin in result.plugins:
                        print(f"      • {plugin}")
                
                if result.themes:
                    print(f"\n   🎨 Temas ({len(result.themes)}):")
                    for theme in result.themes:
                        print(f"      • {theme}")
                
                if result.vulnerabilities:
                    print(f"\n   ⚠️  Vulnerabilidades ({len(result.vulnerabilities)}):")
                    for vuln in result.vulnerabilities:
                        sev = vuln.get("severity", "info")
                        cve = vuln.get("cve", "")
                        name = vuln.get("name", "")
                        print(f"      [{sev.upper()}] {name} {cve}")
            else:
                print("\n❌ Nenhum CMS detectado")
        
        elif escolha == '2':
            print("\n=== Fingerprint Completo ===")
            url = input("URL: ").strip()
            
            if not url:
                continue
            
            print(f"\nColetando informações de {url}...")
            result = detector.fingerprint(url)
            
            print(f"\n🔬 FINGERPRINT:")
            print(f"   URL: {result.get('url')}")
            print(f"   Server: {result.get('server', 'N/A')}")
            print(f"   Powered By: {result.get('powered_by', 'N/A')}")
            
            if result.get("technologies"):
                print(f"\n   🛠️ Tecnologias:")
                for tech in result["technologies"]:
                    print(f"      • {tech}")
            
            if result.get("cookies"):
                print(f"\n   🍪 Cookies:")
                for cookie in result["cookies"]:
                    secure = "🔒" if cookie.get("secure") else "⚠️"
                    http = "🛡️" if cookie.get("httponly") else "⚠️"
                    print(f"      • {cookie['name']} {secure} {http}")
            
            cms = result.get("cms", {})
            if cms and cms.get("name") != "Unknown":
                print(f"\n   📦 CMS: {cms.get('name')} v{cms.get('version', '?')}")
        
        elif escolha == '3':
            print("\n=== Vulnerabilidades por CMS ===")
            print("CMS disponíveis: wordpress, drupal, joomla")
            cms = input("CMS: ").strip().lower()
            
            vulns = CMSVulnerabilityDB.get_vulnerabilities(cms)
            
            if vulns:
                print(f"\n⚠️  Vulnerabilidades conhecidas para {cms.title()}:")
                for v in vulns:
                    print(f"\n   • {v.get('name')}")
                    print(f"     Severidade: {v.get('severity', 'N/A')}")
                    if v.get("cve"):
                        print(f"     CVE: {v.get('cve')}")
                    if v.get("path"):
                        print(f"     Path: {v.get('path')}")
            else:
                print(f"\nNenhuma vulnerabilidade listada para {cms}")
        
        elif escolha == '4':
            print("\n=== Scan Múltiplos Sites ===")
            print("Digite as URLs (uma por linha, linha vazia para terminar):")
            
            urls = []
            while True:
                u = input("  > ").strip()
                if not u:
                    break
                urls.append(u)
            
            if not urls:
                continue
            
            print(f"\nAnalisando {len(urls)} sites...\n")
            
            results = []
            for url in urls:
                print(f"Analisando {url}...", end=" ")
                try:
                    result = detector.detect(url)
                    print(f"{result.name} v{result.version or '?'} ({result.confidence}%)")
                    results.append({
                        "url": url,
                        "cms": result.name,
                        "version": result.version,
                        "vulnerabilities": len(result.vulnerabilities)
                    })
                except Exception as e:
                    print(f"Erro: {e}")
            
            save = input("\nSalvar resultados? (s/n): ").lower()
            if save == 's':
                with open("cms_scan_results.json", 'w') as f:
                    json.dump(results, f, indent=2)
                print("✅ Salvo em cms_scan_results.json")
        
        elif escolha == '5':
            print("\n=== Verificar WordPress ===")
            url = input("URL do site WordPress: ").strip()
            
            if not url:
                continue
            
            result = detector.detect(url)
            
            if result.name.lower() == "wordpress":
                print(f"\n✅ WordPress {result.version or ''} detectado")
                
                print(f"\n   🔌 Plugins detectados: {len(result.plugins)}")
                for p in result.plugins:
                    print(f"      • {p}")
                
                print(f"\n   🎨 Temas detectados: {len(result.themes)}")
                for t in result.themes:
                    print(f"      • {t}")
            else:
                print(f"\n❌ Site não parece ser WordPress (detectado: {result.name})")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
