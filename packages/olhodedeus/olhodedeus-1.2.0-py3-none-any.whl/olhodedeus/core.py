"""
Olho de Deus - Core Module
Funcionalidades principais expostas como API Python.
"""

import os
import sys
import json
from typing import Optional, Dict, Any, List
from pathlib import Path


class OlhoDeDeus:
    """
    Classe principal do Olho de Deus.
    
    Uso:
        from olhodedeus import OlhoDeDeus
        
        odd = OlhoDeDeus()
        result = odd.check_leak("email@example.com")
        print(result)
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa o Olho de Deus.
        
        Args:
            config_path: Caminho para arquivo de configuração customizado
        """
        self.base_path = Path(__file__).parent.parent
        self.config_path = config_path or self.base_path / "config"
        self.data_path = self.base_path / "data"
        
        # Garante que diretórios existam
        self.data_path.mkdir(parents=True, exist_ok=True)
        
    def check_leak(self, email: str) -> Dict[str, Any]:
        """
        Verifica se um email está em vazamentos conhecidos.
        
        Args:
            email: Email para verificar
            
        Returns:
            Dict com resultado da verificação
        """
        try:
            from tools.ingest.leak_sources import FreeLeakChecker
            checker = FreeLeakChecker()
            return checker.check_email(email)
        except ImportError:
            return {"error": "Módulo leak_sources não disponível", "email": email}
        except Exception as e:
            return {"error": str(e), "email": email}
    
    def ip_lookup(self, ip: str) -> Dict[str, Any]:
        """
        Faz geolocalização de um IP.
        
        Args:
            ip: Endereço IP
            
        Returns:
            Dict com informações de geolocalização
        """
        try:
            from tools.recon.geolocation import IPGeolocation
            geo = IPGeolocation()
            result = geo.geolocate_ip_api(ip)
            return {
                "ip": result.ip,
                "country": result.country,
                "city": result.city,
                "isp": result.isp,
                "latitude": result.latitude,
                "longitude": result.longitude,
            }
        except ImportError:
            return {"error": "Módulo geolocation não disponível", "ip": ip}
        except Exception as e:
            return {"error": str(e), "ip": ip}
    
    def username_osint(self, username: str, platforms: List[str] = None) -> Dict[str, Any]:
        """
        Verifica existência de username em diversas plataformas.
        
        Args:
            username: Nome de usuário para verificar
            platforms: Lista de plataformas (opcional)
            
        Returns:
            Dict com resultados por plataforma
        """
        import requests
        
        default_platforms = {
            'github': f'https://github.com/{username}',
            'twitter': f'https://twitter.com/{username}',
            'instagram': f'https://www.instagram.com/{username}/',
            'linkedin': f'https://www.linkedin.com/in/{username}/',
            'reddit': f'https://www.reddit.com/user/{username}',
            'tiktok': f'https://www.tiktok.com/@{username}',
        }
        
        results = {}
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        
        check_platforms = {k: v for k, v in default_platforms.items() if not platforms or k in platforms}
        
        for platform, url in check_platforms.items():
            try:
                resp = session.get(url, timeout=10, allow_redirects=False)
                results[platform] = {
                    'found': resp.status_code == 200,
                    'url': url,
                    'status': resp.status_code,
                }
            except Exception as e:
                results[platform] = {'found': None, 'url': url, 'error': str(e)}
        
        return {'username': username, 'platforms': results}
    
    def port_scan(self, target: str, ports: str = "1-1000") -> Dict[str, Any]:
        """
        Realiza scan de portas em um alvo.
        
        Args:
            target: IP ou hostname
            ports: Range de portas (ex: "1-1000", "80,443,8080")
            
        Returns:
            Dict com portas abertas
        """
        try:
            from tools.offensive.port_scanner import PortScanner
            scanner = PortScanner()
            return scanner.scan(target, ports)
        except ImportError:
            return {"error": "Módulo port_scanner não disponível", "target": target}
        except Exception as e:
            return {"error": str(e), "target": target}
    
    def subdomain_enum(self, domain: str) -> Dict[str, Any]:
        """
        Enumera subdomínios de um domínio.
        
        Args:
            domain: Domínio alvo
            
        Returns:
            Dict com subdomínios encontrados
        """
        try:
            from tools.websec.subdomain_enum import SubdomainEnumerator
            enum = SubdomainEnumerator()
            return enum.enumerate(domain)
        except ImportError:
            return {"error": "Módulo subdomain_enum não disponível", "domain": domain}
        except Exception as e:
            return {"error": str(e), "domain": domain}
    
    def start_api(self, host: str = "0.0.0.0", port: int = 8080, api_key: str = None):
        """
        Inicia o servidor API REST.
        
        Args:
            host: Host para bind (0.0.0.0 para acesso externo)
            port: Porta do servidor
            api_key: Chave de API para autenticação
        """
        try:
            from tools.api.api_server import OlhoDeDuesAPI
            api = OlhoDeDuesAPI(host=host, port=port, api_key=api_key)
            api.start()
        except ImportError as e:
            print(f"Erro ao importar módulo API: {e}")
        except Exception as e:
            print(f"Erro ao iniciar API: {e}")
