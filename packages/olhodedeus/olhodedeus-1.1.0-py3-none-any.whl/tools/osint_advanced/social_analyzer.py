#!/usr/bin/env python3
"""
Social Analyzer - Olho de Deus
Análise de perfis e presença em redes sociais
"""

import requests
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import quote


@dataclass
class SocialProfile:
    """Perfil em rede social"""
    platform: str
    username: str
    url: str
    exists: bool = False
    status_code: int = 0
    display_name: str = ""
    bio: str = ""
    followers: int = 0
    following: int = 0
    posts: int = 0
    verified: bool = False
    profile_image: str = ""
    extra_info: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class SocialAnalysisResult:
    """Resultado da análise social"""
    username: str
    total_platforms: int = 0
    found_count: int = 0
    profiles: List[SocialProfile] = field(default_factory=list)
    email_pattern: str = ""
    possible_emails: List[str] = field(default_factory=list)
    duration: float = 0.0


class SocialAnalyzer:
    """Analisador de presença em redes sociais"""
    
    # Plataformas e URLs de verificação
    PLATFORMS = {
        # Redes sociais principais
        'twitter': {'url': 'https://twitter.com/{username}', 'check': 200},
        'instagram': {'url': 'https://www.instagram.com/{username}/', 'check': 200},
        'facebook': {'url': 'https://www.facebook.com/{username}', 'check': 200},
        'linkedin': {'url': 'https://www.linkedin.com/in/{username}/', 'check': 200},
        'tiktok': {'url': 'https://www.tiktok.com/@{username}', 'check': 200},
        'youtube': {'url': 'https://www.youtube.com/@{username}', 'check': 200},
        'pinterest': {'url': 'https://www.pinterest.com/{username}/', 'check': 200},
        'snapchat': {'url': 'https://www.snapchat.com/add/{username}', 'check': 200},
        'twitch': {'url': 'https://www.twitch.tv/{username}', 'check': 200},
        'reddit': {'url': 'https://www.reddit.com/user/{username}', 'check': 200},
        
        # Profissional/Dev
        'github': {'url': 'https://github.com/{username}', 'check': 200},
        'gitlab': {'url': 'https://gitlab.com/{username}', 'check': 200},
        'bitbucket': {'url': 'https://bitbucket.org/{username}/', 'check': 200},
        'stackoverflow': {'url': 'https://stackoverflow.com/users/{username}', 'check': 200},
        'dev.to': {'url': 'https://dev.to/{username}', 'check': 200},
        'medium': {'url': 'https://medium.com/@{username}', 'check': 200},
        'hashnode': {'url': 'https://hashnode.com/@{username}', 'check': 200},
        
        # Música/Entretenimento
        'spotify': {'url': 'https://open.spotify.com/user/{username}', 'check': 200},
        'soundcloud': {'url': 'https://soundcloud.com/{username}', 'check': 200},
        'vimeo': {'url': 'https://vimeo.com/{username}', 'check': 200},
        'dailymotion': {'url': 'https://www.dailymotion.com/{username}', 'check': 200},
        
        # Gaming
        'steam': {'url': 'https://steamcommunity.com/id/{username}', 'check': 200},
        'xbox': {'url': 'https://account.xbox.com/profile?gamertag={username}', 'check': 200},
        'roblox': {'url': 'https://www.roblox.com/users/profile?username={username}', 'check': 200},
        
        # Comunicação
        'telegram': {'url': 'https://t.me/{username}', 'check': 200},
        'keybase': {'url': 'https://keybase.io/{username}', 'check': 200},
        
        # Design/Portfolio
        'dribbble': {'url': 'https://dribbble.com/{username}', 'check': 200},
        'behance': {'url': 'https://www.behance.net/{username}', 'check': 200},
        'flickr': {'url': 'https://www.flickr.com/people/{username}/', 'check': 200},
        'deviantart': {'url': 'https://{username}.deviantart.com', 'check': 200},
        
        # Outros
        'gravatar': {'url': 'https://en.gravatar.com/{username}', 'check': 200},
        'about.me': {'url': 'https://about.me/{username}', 'check': 200},
        'patreon': {'url': 'https://www.patreon.com/{username}', 'check': 200},
        'ko-fi': {'url': 'https://ko-fi.com/{username}', 'check': 200},
        'buymeacoffee': {'url': 'https://www.buymeacoffee.com/{username}', 'check': 200},
        'producthunt': {'url': 'https://www.producthunt.com/@{username}', 'check': 200},
        'quora': {'url': 'https://www.quora.com/profile/{username}', 'check': 200},
        'slideshare': {'url': 'https://www.slideshare.net/{username}', 'check': 200},
        'goodreads': {'url': 'https://www.goodreads.com/{username}', 'check': 200},
        'tumblr': {'url': 'https://{username}.tumblr.com', 'check': 200},
        'wordpress': {'url': 'https://{username}.wordpress.com', 'check': 200},
        'blogger': {'url': 'https://{username}.blogspot.com', 'check': 200},
    }
    
    # Domínios comuns para geração de emails
    EMAIL_DOMAINS = [
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'protonmail.com', 'icloud.com', 'mail.com'
    ]
    
    def __init__(self, timeout: float = 10.0, threads: int = 20):
        self.timeout = timeout
        self.threads = threads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def analyze(self, username: str, platforms: List[str] = None) -> SocialAnalysisResult:
        """Analisa presença de um username em redes sociais"""
        
        start_time = datetime.now()
        
        print(f"\n🔍 Social Analyzer: {username}")
        print("=" * 50)
        
        result = SocialAnalysisResult(username=username)
        
        # Plataformas a verificar
        if platforms:
            check_platforms = {k: v for k, v in self.PLATFORMS.items() if k in platforms}
        else:
            check_platforms = self.PLATFORMS
        
        result.total_platforms = len(check_platforms)
        
        print(f"   Verificando {result.total_platforms} plataformas...")
        print("-" * 50)
        
        # Verificar em paralelo
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {}
            
            for platform, config in check_platforms.items():
                url = config['url'].format(username=username)
                futures[executor.submit(self._check_profile, platform, url, config['check'])] = platform
            
            for future in as_completed(futures):
                platform = futures[future]
                try:
                    profile = future.result()
                    result.profiles.append(profile)
                    
                    if profile.exists:
                        result.found_count += 1
                        print(f"   ✅ {platform}: {profile.url}")
                except Exception as e:
                    print(f"   ❌ {platform}: Erro - {e}")
        
        # Gerar possíveis emails
        result.possible_emails = self._generate_possible_emails(username)
        
        result.duration = (datetime.now() - start_time).total_seconds()
        
        # Ordenar por existência
        result.profiles.sort(key=lambda x: (not x.exists, x.platform))
        
        # Resumo
        print("\n" + "=" * 50)
        print(f"📊 Resumo:")
        print(f"   Encontrados: {result.found_count}/{result.total_platforms}")
        print(f"   Tempo: {result.duration:.1f}s")
        
        return result
    
    def _check_profile(self, platform: str, url: str, expected_status: int) -> SocialProfile:
        """Verifica se um perfil existe"""
        profile = SocialProfile(
            platform=platform,
            username=url.split('/')[-1].replace('@', ''),
            url=url
        )
        
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            profile.status_code = resp.status_code
            
            # Verificar existência
            if resp.status_code == expected_status:
                # Verificações adicionais por plataforma
                if platform == 'instagram':
                    profile.exists = 'page not found' not in resp.text.lower()
                elif platform == 'twitter':
                    profile.exists = 'this account doesn' not in resp.text.lower()
                elif platform == 'github':
                    profile.exists = resp.status_code == 200
                    self._extract_github_info(profile, resp.text)
                else:
                    # Verificação genérica
                    profile.exists = resp.status_code == 200
                
                # Tentar extrair informações
                if profile.exists:
                    self._extract_basic_info(profile, resp.text)
            
        except requests.exceptions.Timeout:
            profile.status_code = 0
        except Exception:
            profile.status_code = -1
        
        return profile
    
    def _extract_basic_info(self, profile: SocialProfile, html: str):
        """Extrai informações básicas do perfil"""
        # Display name
        name_patterns = [
            r'<title>([^<|]+)',
            r'"name"\s*:\s*"([^"]+)"',
            r'class="[^"]*name[^"]*">([^<]+)<',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                profile.display_name = match.group(1).strip()[:50]
                break
        
        # Bio/Description
        bio_patterns = [
            r'"description"\s*:\s*"([^"]+)"',
            r'<meta name="description" content="([^"]+)"',
        ]
        for pattern in bio_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                profile.bio = match.group(1).strip()[:200]
                break
        
        # Profile image
        img_patterns = [
            r'"image"\s*:\s*"([^"]+)"',
            r'og:image["\s]*content="([^"]+)"',
        ]
        for pattern in img_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                profile.profile_image = match.group(1)
                break
    
    def _extract_github_info(self, profile: SocialProfile, html: str):
        """Extrai informações específicas do GitHub"""
        # Followers
        followers_match = re.search(r'(\d+)\s*followers', html, re.IGNORECASE)
        if followers_match:
            profile.followers = int(followers_match.group(1))
        
        # Following
        following_match = re.search(r'(\d+)\s*following', html, re.IGNORECASE)
        if following_match:
            profile.following = int(following_match.group(1))
        
        # Repos
        repos_match = re.search(r'Repositories.*?(\d+)', html, re.IGNORECASE | re.DOTALL)
        if repos_match:
            profile.posts = int(repos_match.group(1))
    
    def _generate_possible_emails(self, username: str) -> List[str]:
        """Gera possíveis endereços de email"""
        emails = []
        
        # Variações do username
        variations = [
            username,
            username.lower(),
            username.replace('_', '.'),
            username.replace('-', '.'),
        ]
        
        for var in variations:
            for domain in self.EMAIL_DOMAINS[:4]:  # Top 4 domínios
                emails.append(f"{var}@{domain}")
        
        return list(set(emails))
    
    def quick_check(self, username: str) -> Dict[str, bool]:
        """Verificação rápida de existência"""
        top_platforms = ['twitter', 'instagram', 'github', 'linkedin', 'tiktok']
        
        result = {}
        for platform in top_platforms:
            if platform in self.PLATFORMS:
                config = self.PLATFORMS[platform]
                url = config['url'].format(username=username)
                profile = self._check_profile(platform, url, config['check'])
                result[platform] = profile.exists
        
        return result
    
    def analyze_correlation(self, result: SocialAnalysisResult) -> Dict:
        """Analisa correlação entre perfis encontrados"""
        correlation = {
            'consistent_name': False,
            'consistent_image': False,
            'display_names': [],
            'bios': [],
        }
        
        names = [p.display_name for p in result.profiles if p.exists and p.display_name]
        bios = [p.bio for p in result.profiles if p.exists and p.bio]
        
        correlation['display_names'] = list(set(names))
        correlation['bios'] = bios
        
        # Verificar consistência
        if len(set(names)) == 1 and names:
            correlation['consistent_name'] = True
        
        return correlation
    
    def export_results(self, result: SocialAnalysisResult, filepath: str):
        """Exporta resultados para JSON"""
        data = {
            'username': result.username,
            'total_platforms': result.total_platforms,
            'found_count': result.found_count,
            'duration': result.duration,
            'profiles': [
                {
                    'platform': p.platform,
                    'url': p.url,
                    'exists': p.exists,
                    'display_name': p.display_name,
                    'bio': p.bio,
                    'followers': p.followers,
                    'following': p.following,
                }
                for p in result.profiles if p.exists
            ],
            'possible_emails': result.possible_emails,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n📄 Resultados salvos: {filepath}")
    
    def print_summary(self, result: SocialAnalysisResult):
        """Imprime resumo detalhado"""
        found = [p for p in result.profiles if p.exists]
        
        print(f"\n📋 Perfis encontrados ({len(found)}):")
        print("-" * 40)
        
        for p in found:
            print(f"\n🔹 {p.platform.upper()}")
            print(f"   URL: {p.url}")
            if p.display_name:
                print(f"   Nome: {p.display_name}")
            if p.bio:
                print(f"   Bio: {p.bio[:100]}...")
            if p.followers:
                print(f"   Followers: {p.followers}")


def main():
    """Função principal"""
    import sys
    
    print("\n" + "=" * 50)
    print("🔍 Social Analyzer - Olho de Deus")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        username = input("\n👤 Username para analisar: ").strip()
    else:
        username = sys.argv[1]
    
    analyzer = SocialAnalyzer()
    result = analyzer.analyze(username)
    
    # Mostrar possíveis emails
    if result.possible_emails:
        print(f"\n📧 Possíveis emails:")
        for email in result.possible_emails[:5]:
            print(f"   • {email}")
    
    # Análise de correlação
    correlation = analyzer.analyze_correlation(result)
    if correlation['display_names']:
        print(f"\n👤 Nomes encontrados: {', '.join(correlation['display_names'][:3])}")
    
    print("\n✅ Análise concluída!")


if __name__ == "__main__":
    main()
