#!/usr/bin/env python3
"""
Username Checker - Olho de Deus
Verificação de disponibilidade de usernames em múltiplas plataformas
"""

import requests
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UsernameResult:
    """Resultado de verificação de username"""
    platform: str
    username: str
    url: str
    status: str  # exists, available, error, unknown
    http_code: int = 0
    response_time: float = 0.0
    error_message: str = ""


@dataclass
class CheckResult:
    """Resultado completo da verificação"""
    username: str
    total_checked: int = 0
    exists_count: int = 0
    available_count: int = 0
    error_count: int = 0
    results: List[UsernameResult] = field(default_factory=list)
    duration: float = 0.0
    similar_usernames: List[str] = field(default_factory=list)


class UsernameChecker:
    """Verificador de disponibilidade de usernames"""
    
    # Plataformas e métodos de verificação
    PLATFORMS = {
        # Redes Sociais
        'twitter': {
            'url': 'https://twitter.com/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'instagram': {
            'url': 'https://www.instagram.com/{username}/',
            'exists_codes': [200],
            'available_codes': [404],
            'exists_text': 'Profile picture',
        },
        'facebook': {
            'url': 'https://www.facebook.com/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'tiktok': {
            'url': 'https://www.tiktok.com/@{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'linkedin': {
            'url': 'https://www.linkedin.com/in/{username}/',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'pinterest': {
            'url': 'https://www.pinterest.com/{username}/',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'reddit': {
            'url': 'https://www.reddit.com/user/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'snapchat': {
            'url': 'https://www.snapchat.com/add/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'tumblr': {
            'url': 'https://{username}.tumblr.com',
            'exists_codes': [200],
            'available_codes': [404],
        },
        
        # Dev/Tech
        'github': {
            'url': 'https://github.com/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'gitlab': {
            'url': 'https://gitlab.com/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'bitbucket': {
            'url': 'https://bitbucket.org/{username}/',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'dev.to': {
            'url': 'https://dev.to/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'medium': {
            'url': 'https://medium.com/@{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'hashnode': {
            'url': 'https://hashnode.com/@{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'codepen': {
            'url': 'https://codepen.io/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'replit': {
            'url': 'https://replit.com/@{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        
        # Gaming
        'twitch': {
            'url': 'https://www.twitch.tv/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'steam': {
            'url': 'https://steamcommunity.com/id/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'xbox': {
            'url': 'https://xboxgamertag.com/search/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        
        # Mídia
        'youtube': {
            'url': 'https://www.youtube.com/@{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'spotify': {
            'url': 'https://open.spotify.com/user/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'soundcloud': {
            'url': 'https://soundcloud.com/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'vimeo': {
            'url': 'https://vimeo.com/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        
        # Comunicação
        'telegram': {
            'url': 'https://t.me/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'keybase': {
            'url': 'https://keybase.io/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        
        # Portfólio/Design
        'dribbble': {
            'url': 'https://dribbble.com/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'behance': {
            'url': 'https://www.behance.net/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'flickr': {
            'url': 'https://www.flickr.com/people/{username}/',
            'exists_codes': [200],
            'available_codes': [404],
        },
        
        # Outros
        'gravatar': {
            'url': 'https://en.gravatar.com/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'about.me': {
            'url': 'https://about.me/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'patreon': {
            'url': 'https://www.patreon.com/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'ko-fi': {
            'url': 'https://ko-fi.com/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'buymeacoffee': {
            'url': 'https://www.buymeacoffee.com/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
        'linktree': {
            'url': 'https://linktr.ee/{username}',
            'exists_codes': [200],
            'available_codes': [404],
        },
    }
    
    # Categorias de plataformas
    CATEGORIES = {
        'social': ['twitter', 'instagram', 'facebook', 'tiktok', 'linkedin', 'pinterest', 'reddit', 'snapchat', 'tumblr'],
        'dev': ['github', 'gitlab', 'bitbucket', 'dev.to', 'medium', 'hashnode', 'codepen', 'replit'],
        'gaming': ['twitch', 'steam', 'xbox'],
        'media': ['youtube', 'spotify', 'soundcloud', 'vimeo'],
        'communication': ['telegram', 'keybase'],
        'design': ['dribbble', 'behance', 'flickr'],
        'other': ['gravatar', 'about.me', 'patreon', 'ko-fi', 'buymeacoffee', 'linktree'],
    }
    
    def __init__(self, timeout: float = 10.0, threads: int = 20):
        self.timeout = timeout
        self.threads = threads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def check(self, username: str, platforms: List[str] = None, 
              category: str = None) -> CheckResult:
        """Verifica disponibilidade de username"""
        
        start_time = datetime.now()
        
        print(f"\n🔍 Username Checker: {username}")
        print("=" * 50)
        
        result = CheckResult(username=username)
        
        # Determinar plataformas a verificar
        if platforms:
            check_platforms = {k: v for k, v in self.PLATFORMS.items() if k in platforms}
        elif category and category in self.CATEGORIES:
            check_platforms = {k: v for k, v in self.PLATFORMS.items() 
                            if k in self.CATEGORIES[category]}
        else:
            check_platforms = self.PLATFORMS
        
        result.total_checked = len(check_platforms)
        
        print(f"   Verificando {result.total_checked} plataformas...")
        print("-" * 50)
        
        # Verificar em paralelo
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {}
            
            for platform, config in check_platforms.items():
                url = config['url'].format(username=username)
                futures[executor.submit(
                    self._check_platform, 
                    platform, url, config
                )] = platform
            
            for future in as_completed(futures):
                platform = futures[future]
                try:
                    platform_result = future.result()
                    result.results.append(platform_result)
                    
                    if platform_result.status == 'exists':
                        result.exists_count += 1
                        print(f"   ✅ {platform}: EXISTE - {platform_result.url}")
                    elif platform_result.status == 'available':
                        result.available_count += 1
                        print(f"   ⭕ {platform}: Disponível")
                    else:
                        result.error_count += 1
                        
                except Exception as e:
                    result.error_count += 1
        
        result.duration = (datetime.now() - start_time).total_seconds()
        
        # Gerar usernames similares
        result.similar_usernames = self._generate_similar(username)
        
        # Ordenar resultados
        result.results.sort(key=lambda x: (
            x.status != 'exists',
            x.status != 'available',
            x.platform
        ))
        
        # Resumo
        print("\n" + "=" * 50)
        print(f"📊 Resumo:")
        print(f"   ✅ Existe em: {result.exists_count} plataformas")
        print(f"   ⭕ Disponível em: {result.available_count} plataformas")
        print(f"   ❌ Erros: {result.error_count}")
        print(f"   ⏱️ Tempo: {result.duration:.1f}s")
        
        return result
    
    def _check_platform(self, platform: str, url: str, config: Dict) -> UsernameResult:
        """Verifica uma plataforma específica"""
        result = UsernameResult(
            platform=platform,
            username=url.split('/')[-1].replace('@', ''),
            url=url,
            status='unknown'
        )
        
        start = time.time()
        
        try:
            resp = self.session.get(
                url, 
                timeout=self.timeout, 
                allow_redirects=True,
                verify=False
            )
            
            result.http_code = resp.status_code
            result.response_time = time.time() - start
            
            # Verificar por código HTTP
            if resp.status_code in config.get('exists_codes', [200]):
                # Verificação adicional por texto
                if 'exists_text' in config:
                    if config['exists_text'].lower() in resp.text.lower():
                        result.status = 'exists'
                    else:
                        result.status = 'available'
                else:
                    result.status = 'exists'
            elif resp.status_code in config.get('available_codes', [404]):
                result.status = 'available'
            else:
                result.status = 'unknown'
                
        except requests.exceptions.Timeout:
            result.status = 'error'
            result.error_message = 'Timeout'
        except requests.exceptions.ConnectionError:
            result.status = 'error'
            result.error_message = 'Connection error'
        except Exception as e:
            result.status = 'error'
            result.error_message = str(e)
        
        return result
    
    def _generate_similar(self, username: str) -> List[str]:
        """Gera usernames similares"""
        similar = []
        
        # Variações
        similar.append(username + '_')
        similar.append('_' + username)
        similar.append(username + '1')
        similar.append(username + '123')
        similar.append(username + '_oficial')
        similar.append(username + '_real')
        similar.append('the' + username)
        similar.append('real' + username)
        similar.append(username.replace('_', ''))
        similar.append(username.replace('_', '.'))
        
        # Remover duplicatas e o original
        similar = list(set(similar))
        if username in similar:
            similar.remove(username)
        
        return similar[:10]
    
    def check_quick(self, username: str) -> Dict[str, str]:
        """Verificação rápida nas principais plataformas"""
        main_platforms = ['twitter', 'instagram', 'github', 'tiktok', 'youtube']
        
        result = self.check(username, platforms=main_platforms)
        
        return {
            r.platform: r.status 
            for r in result.results
        }
    
    def check_by_category(self, username: str, category: str) -> CheckResult:
        """Verifica por categoria"""
        if category not in self.CATEGORIES:
            print(f"❌ Categoria inválida. Opções: {list(self.CATEGORIES.keys())}")
            return CheckResult(username=username)
        
        return self.check(username, category=category)
    
    def get_exists_urls(self, result: CheckResult) -> List[str]:
        """Retorna URLs onde o username existe"""
        return [r.url for r in result.results if r.status == 'exists']
    
    def get_available_platforms(self, result: CheckResult) -> List[str]:
        """Retorna plataformas onde o username está disponível"""
        return [r.platform for r in result.results if r.status == 'available']
    
    def export_results(self, result: CheckResult, filepath: str):
        """Exporta resultados para JSON"""
        data = {
            'username': result.username,
            'total_checked': result.total_checked,
            'exists_count': result.exists_count,
            'available_count': result.available_count,
            'duration': result.duration,
            'results': [
                {
                    'platform': r.platform,
                    'url': r.url,
                    'status': r.status,
                    'http_code': r.http_code,
                    'response_time': r.response_time
                }
                for r in result.results
            ],
            'exists_urls': self.get_exists_urls(result),
            'available_platforms': self.get_available_platforms(result),
            'similar_usernames': result.similar_usernames,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n📄 Resultados salvos: {filepath}")
    
    def print_detailed(self, result: CheckResult):
        """Imprime resultados detalhados"""
        print(f"\n📋 Detalhes para: {result.username}")
        print("-" * 40)
        
        # Existe
        exists = [r for r in result.results if r.status == 'exists']
        if exists:
            print(f"\n✅ Existe em ({len(exists)}):")
            for r in exists:
                print(f"   • {r.platform}: {r.url}")
        
        # Disponível
        available = [r for r in result.results if r.status == 'available']
        if available:
            print(f"\n⭕ Disponível em ({len(available)}):")
            for r in available[:10]:
                print(f"   • {r.platform}")
            if len(available) > 10:
                print(f"   ... e mais {len(available) - 10}")
        
        # Sugestões
        if result.similar_usernames:
            print(f"\n💡 Usernames similares para verificar:")
            for s in result.similar_usernames[:5]:
                print(f"   • {s}")


# Suprimir warnings de SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    """Função principal"""
    import sys
    
    print("\n" + "=" * 50)
    print("🔍 Username Checker - Olho de Deus")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        username = input("\n👤 Username para verificar: ").strip()
    else:
        username = sys.argv[1]
    
    # Categoria opcional
    category = None
    if len(sys.argv) > 2:
        category = sys.argv[2]
    
    checker = UsernameChecker()
    
    if category:
        result = checker.check_by_category(username, category)
    else:
        result = checker.check(username)
    
    # Detalhes
    checker.print_detailed(result)
    
    print("\n✅ Verificação concluída!")


if __name__ == "__main__":
    main()
