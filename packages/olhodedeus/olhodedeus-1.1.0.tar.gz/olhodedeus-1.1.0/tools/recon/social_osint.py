#!/usr/bin/env python3
"""
social_osint.py

OSINT para redes sociais - coleta de informações públicas.
"""
import os
import re
import json
import requests
from typing import Optional, Dict, List
from datetime import datetime
from urllib.parse import quote


class SocialMediaOSINT:
    """OSINT para redes sociais."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def check_username_availability(self, username: str) -> Dict[str, Dict]:
        """Verifica disponibilidade de username em várias plataformas."""
        platforms = {
            'twitter': f'https://twitter.com/{username}',
            'instagram': f'https://www.instagram.com/{username}/',
            'github': f'https://github.com/{username}',
            'reddit': f'https://www.reddit.com/user/{username}',
            'tiktok': f'https://www.tiktok.com/@{username}',
            'youtube': f'https://www.youtube.com/@{username}',
            'pinterest': f'https://www.pinterest.com/{username}/',
            'linkedin': f'https://www.linkedin.com/in/{username}/',
            'snapchat': f'https://www.snapchat.com/add/{username}',
            'twitch': f'https://www.twitch.tv/{username}',
            'spotify': f'https://open.spotify.com/user/{username}',
            'soundcloud': f'https://soundcloud.com/{username}',
            'medium': f'https://medium.com/@{username}',
            'devto': f'https://dev.to/{username}',
            'gitlab': f'https://gitlab.com/{username}',
            'bitbucket': f'https://bitbucket.org/{username}/',
            'hackerone': f'https://hackerone.com/{username}',
            'bugcrowd': f'https://bugcrowd.com/{username}',
            'keybase': f'https://keybase.io/{username}',
            'telegram': f'https://t.me/{username}',
            'discord': f'https://discord.com/users/{username}',  # Precisa ID
            'steam': f'https://steamcommunity.com/id/{username}',
            'xbox': f'https://xboxgamertag.com/search/{username}',
            'playstation': f'https://psnprofiles.com/{username}',
            'roblox': f'https://www.roblox.com/users/profile?username={username}',
            'minecraft': f'https://namemc.com/profile/{username}',
            'patreon': f'https://www.patreon.com/{username}',
            'paypal': f'https://www.paypal.me/{username}',
            'venmo': f'https://venmo.com/{username}',
            'cashapp': f'https://cash.app/${username}',
            'onlyfans': f'https://onlyfans.com/{username}',
            'flickr': f'https://www.flickr.com/people/{username}/',
            'vimeo': f'https://vimeo.com/{username}',
            'dailymotion': f'https://www.dailymotion.com/{username}',
            'imgur': f'https://imgur.com/user/{username}',
            'tumblr': f'https://{username}.tumblr.com',
            'wordpress': f'https://{username}.wordpress.com',
            'blogger': f'https://{username}.blogspot.com',
            'about.me': f'https://about.me/{username}',
            'gravatar': f'https://en.gravatar.com/{username}',
            'slideshare': f'https://www.slideshare.net/{username}',
            'scribd': f'https://www.scribd.com/{username}',
            'goodreads': f'https://www.goodreads.com/{username}',
            'quora': f'https://www.quora.com/profile/{username}',
            'producthunt': f'https://www.producthunt.com/@{username}',
            'crunchbase': f'https://www.crunchbase.com/person/{username}',
            'angellist': f'https://angel.co/u/{username}',
            'dribbble': f'https://dribbble.com/{username}',
            'behance': f'https://www.behance.net/{username}',
            'fiverr': f'https://www.fiverr.com/{username}',
            'upwork': f'https://www.upwork.com/freelancers/~{username}',
        }
        
        results = {}
        print(f"\n🔍 Verificando username: {username}\n")
        
        for platform, url in platforms.items():
            try:
                resp = self.session.get(url, timeout=10, allow_redirects=False)
                if resp.status_code == 200:
                    results[platform] = {'status': 'exists', 'url': url}
                    print(f"  ✅ {platform}: EXISTE")
                elif resp.status_code == 404:
                    results[platform] = {'status': 'available', 'url': url}
                    print(f"  ❌ {platform}: Disponível")
                else:
                    results[platform] = {'status': 'unknown', 'code': resp.status_code}
                    print(f"  ❓ {platform}: {resp.status_code}")
            except Exception as e:
                results[platform] = {'status': 'error', 'error': str(e)}
                print(f"  ⚠️ {platform}: Erro")
        
        return results
    
    def search_github_user(self, username: str) -> Dict:
        """Busca informações de usuário no GitHub."""
        try:
            resp = self.session.get(f'https://api.github.com/users/{username}', timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                
                # Buscar repos
                repos_resp = self.session.get(f'https://api.github.com/users/{username}/repos?per_page=100', timeout=10)
                repos = repos_resp.json() if repos_resp.status_code == 200 else []
                
                # Emails de commits públicos
                emails = set()
                for repo in repos[:10]:
                    try:
                        commits = self.session.get(
                            f'https://api.github.com/repos/{username}/{repo["name"]}/commits?per_page=5',
                            timeout=10
                        ).json()
                        for c in commits[:5]:
                            if 'commit' in c and 'author' in c['commit']:
                                emails.add(c['commit']['author'].get('email', ''))
                    except:
                        pass
                
                return {
                    'username': data.get('login'),
                    'name': data.get('name'),
                    'bio': data.get('bio'),
                    'company': data.get('company'),
                    'location': data.get('location'),
                    'email': data.get('email'),
                    'blog': data.get('blog'),
                    'twitter': data.get('twitter_username'),
                    'followers': data.get('followers'),
                    'following': data.get('following'),
                    'public_repos': data.get('public_repos'),
                    'created_at': data.get('created_at'),
                    'avatar_url': data.get('avatar_url'),
                    'commit_emails': list(emails - {None, ''})
                }
        except Exception as e:
            return {'error': str(e)}
        return {}
    
    def search_by_email(self, email: str) -> Dict:
        """Busca informações por email."""
        results = {}
        
        # Gravatar
        import hashlib
        email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        gravatar_url = f'https://www.gravatar.com/{email_hash}.json'
        try:
            resp = self.session.get(gravatar_url, timeout=10)
            if resp.status_code == 200:
                results['gravatar'] = resp.json()
        except:
            pass
        
        # GitHub search (pode ter rate limit)
        try:
            resp = self.session.get(f'https://api.github.com/search/users?q={email}+in:email', timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('total_count', 0) > 0:
                    results['github'] = data['items']
        except:
            pass
        
        return results
    
    def search_by_phone(self, phone: str) -> Dict:
        """Busca informações por número de telefone."""
        results = {
            'phone': phone,
            'possible_platforms': []
        }
        
        # Formatar número
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # WhatsApp check (precisa de API)
        results['whatsapp'] = f'https://wa.me/{clean_phone}'
        
        # Telegram check
        results['telegram_search'] = f'https://t.me/{clean_phone}'
        
        # True Caller
        results['truecaller'] = f'https://www.truecaller.com/search/br/{clean_phone}'
        
        # Sync.me
        results['syncme'] = f'https://sync.me/search/?number={clean_phone}'
        
        return results
    
    def reverse_image_urls(self, image_url: str) -> Dict:
        """Gera URLs para busca reversa de imagem."""
        encoded_url = quote(image_url, safe='')
        return {
            'google': f'https://www.google.com/searchbyimage?image_url={encoded_url}',
            'yandex': f'https://yandex.com/images/search?rpt=imageview&url={encoded_url}',
            'tineye': f'https://tineye.com/search?url={encoded_url}',
            'bing': f'https://www.bing.com/images/search?view=detailv2&iss=sbi&q=imgurl:{encoded_url}'
        }
    
    def dorking_queries(self, target: str) -> List[str]:
        """Gera Google dorks para um alvo."""
        dorks = [
            f'"{target}"',
            f'site:linkedin.com "{target}"',
            f'site:facebook.com "{target}"',
            f'site:twitter.com "{target}"',
            f'site:instagram.com "{target}"',
            f'site:github.com "{target}"',
            f'site:pastebin.com "{target}"',
            f'site:reddit.com "{target}"',
            f'"{target}" email OR phone OR address',
            f'"{target}" filetype:pdf',
            f'"{target}" filetype:doc',
            f'"{target}" filetype:xls',
            f'"{target}" password OR leaked',
            f'inurl:"{target}"',
            f'intitle:"{target}"',
        ]
        return dorks


class EmailValidator:
    """Validação e verificação de emails."""
    
    def __init__(self):
        self.session = requests.Session()
    
    def validate_format(self, email: str) -> bool:
        """Valida formato do email."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def check_mx_records(self, domain: str) -> List[str]:
        """Verifica MX records."""
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, 'MX')
            return [str(r.exchange) for r in answers]
        except:
            return []
    
    def check_email_rep(self, email: str) -> Dict:
        """Verifica reputação do email via EmailRep.io."""
        try:
            resp = self.session.get(f'https://emailrep.io/{email}', timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return {}


def interactive_menu():
    """Menu interativo."""
    osint = SocialMediaOSINT()
    email_validator = EmailValidator()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("""
╔══════════════════════════════════════════════════════════════╗
║                🌐 SOCIAL MEDIA OSINT                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ──── 👤 USERNAME ────                                       ║
║  [1] 🔍 Verificar username em +50 plataformas                ║
║  [2] 🐙 GitHub Profile Deep Search                           ║
║                                                              ║
║  ──── 📧 EMAIL ────                                          ║
║  [3] 📧 Buscar por Email                                     ║
║  [4] ✅ Validar Email                                        ║
║                                                              ║
║  ──── 📱 TELEFONE ────                                       ║
║  [5] 📱 Buscar por Telefone                                  ║
║                                                              ║
║  ──── 🔍 OUTROS ────                                         ║
║  [6] 🖼️  Busca Reversa de Imagem                              ║
║  [7] 🔎 Gerar Google Dorks                                   ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            username = input("\n👤 Username: ").strip()
            if username:
                results = osint.check_username_availability(username)
                
                exists = [k for k, v in results.items() if v.get('status') == 'exists']
                print(f"\n📊 Encontrado em {len(exists)} plataformas:")
                for p in exists[:20]:
                    print(f"   • {p}: {results[p]['url']}")
            input("\nPressione Enter...")
        
        elif choice == '2':
            username = input("\n🐙 GitHub Username: ").strip()
            if username:
                result = osint.search_github_user(username)
                if 'error' not in result and result:
                    print(f"\n📊 GITHUB PROFILE:")
                    print(f"   Nome: {result.get('name', 'N/A')}")
                    print(f"   Bio: {result.get('bio', 'N/A')}")
                    print(f"   Empresa: {result.get('company', 'N/A')}")
                    print(f"   Local: {result.get('location', 'N/A')}")
                    print(f"   Email: {result.get('email', 'N/A')}")
                    print(f"   Blog: {result.get('blog', 'N/A')}")
                    print(f"   Twitter: @{result.get('twitter', 'N/A')}")
                    print(f"   Followers: {result.get('followers', 0)}")
                    print(f"   Repos: {result.get('public_repos', 0)}")
                    print(f"   Criado: {result.get('created_at', 'N/A')}")
                    if result.get('commit_emails'):
                        print(f"\n   📧 Emails de commits:")
                        for e in result['commit_emails'][:5]:
                            print(f"      • {e}")
                else:
                    print("❌ Usuário não encontrado")
            input("\nPressione Enter...")
        
        elif choice == '3':
            email = input("\n📧 Email: ").strip()
            if email:
                results = osint.search_by_email(email)
                if results:
                    print(f"\n📊 Resultados:")
                    if 'gravatar' in results:
                        g = results['gravatar'].get('entry', [{}])[0]
                        print(f"   Gravatar: {g.get('displayName', 'N/A')}")
                    if 'github' in results:
                        for u in results['github'][:5]:
                            print(f"   GitHub: {u.get('login')}")
                else:
                    print("❌ Nenhum resultado")
            input("\nPressione Enter...")
        
        elif choice == '4':
            email = input("\n📧 Email: ").strip()
            if email:
                # Formato
                valid = email_validator.validate_format(email)
                print(f"\n   Formato válido: {'✅' if valid else '❌'}")
                
                # MX
                domain = email.split('@')[-1]
                mx = email_validator.check_mx_records(domain)
                print(f"   MX Records: {'✅' if mx else '❌'}")
                for m in mx[:3]:
                    print(f"      • {m}")
                
                # EmailRep
                rep = email_validator.check_email_rep(email)
                if rep:
                    print(f"\n   📊 Reputação (EmailRep):")
                    print(f"      Score: {rep.get('reputation', 'N/A')}")
                    print(f"      Suspicious: {rep.get('suspicious', 'N/A')}")
                    if rep.get('details'):
                        d = rep['details']
                        print(f"      Spam: {d.get('spam', 'N/A')}")
                        print(f"      Leaked: {d.get('credentials_leaked', 'N/A')}")
            input("\nPressione Enter...")
        
        elif choice == '5':
            phone = input("\n📱 Telefone (com DDD/DDI): ").strip()
            if phone:
                results = osint.search_by_phone(phone)
                print(f"\n📊 Links para busca:")
                print(f"   WhatsApp: {results['whatsapp']}")
                print(f"   TrueCaller: {results['truecaller']}")
                print(f"   Sync.me: {results['syncme']}")
            input("\nPressione Enter...")
        
        elif choice == '6':
            url = input("\n🖼️ URL da imagem: ").strip()
            if url:
                urls = osint.reverse_image_urls(url)
                print(f"\n📊 Links para busca reversa:")
                for service, link in urls.items():
                    print(f"   {service}: {link}")
            input("\nPressione Enter...")
        
        elif choice == '7':
            target = input("\n🔎 Alvo (nome, email, etc): ").strip()
            if target:
                dorks = osint.dorking_queries(target)
                print(f"\n📊 Google Dorks:")
                for d in dorks:
                    print(f"   • {d}")
            input("\nPressione Enter...")
        
        elif choice == '0':
            break


if __name__ == '__main__':
    interactive_menu()
