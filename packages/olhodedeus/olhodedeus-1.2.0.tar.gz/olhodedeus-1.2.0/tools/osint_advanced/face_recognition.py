#!/usr/bin/env python3
"""
Face Recognition - Busca reversa de imagens e reconhecimento facial
Parte do toolkit Olho de Deus

NOTA: Este módulo fornece interfaces para APIs de reconhecimento facial.
Use com responsabilidade e respeite a privacidade das pessoas.
"""

import os
import sys
import json
import base64
import hashlib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, quote_plus

try:
    import requests
except ImportError:
    requests = None


@dataclass
class FaceMatch:
    """Resultado de correspondência facial."""
    source: str
    url: str
    similarity: float
    name: Optional[str]
    metadata: Dict
    
    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "url": self.url,
            "similarity": self.similarity,
            "name": self.name,
            "metadata": self.metadata
        }


@dataclass
class ImageSearchResult:
    """Resultado de busca reversa de imagem."""
    engine: str
    matches: List[Dict]
    similar_images: List[str]
    pages_with_image: List[Dict]
    
    def to_dict(self) -> Dict:
        return {
            "engine": self.engine,
            "matches": self.matches,
            "similar_images": self.similar_images,
            "pages_with_image": self.pages_with_image
        }


class ImageUtils:
    """Utilitários para processamento de imagens."""
    
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    
    @staticmethod
    def load_image(path: str) -> Optional[bytes]:
        """Carrega imagem de arquivo."""
        try:
            with open(path, 'rb') as f:
                return f.read()
        except Exception:
            return None
    
    @staticmethod
    def to_base64(image_data: bytes) -> str:
        """Converte imagem para base64."""
        return base64.b64encode(image_data).decode('utf-8')
    
    @staticmethod
    def get_image_hash(image_data: bytes) -> str:
        """Calcula hash da imagem."""
        return hashlib.sha256(image_data).hexdigest()
    
    @staticmethod
    def is_valid_image(path: str) -> bool:
        """Verifica se é uma imagem válida."""
        ext = os.path.splitext(path.lower())[1]
        return ext in ImageUtils.SUPPORTED_FORMATS
    
    @staticmethod
    def get_image_from_url(url: str, timeout: int = 10) -> Optional[bytes]:
        """Baixa imagem de URL."""
        if not requests:
            return None
        
        try:
            response = requests.get(url, timeout=timeout, verify=False)
            if response.status_code == 200:
                return response.content
        except Exception:
            pass
        
        return None


class ReverseImageSearch:
    """Busca reversa de imagens."""
    
    # URLs de engines de busca
    ENGINES = {
        "google": "https://www.google.com/searchbyimage?image_url=",
        "yandex": "https://yandex.com/images/search?rpt=imageview&url=",
        "bing": "https://www.bing.com/images/search?view=detailv2&iss=sbi&q=imgurl:",
        "tineye": "https://tineye.com/search?url=",
    }
    
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session() if requests else None
        if self.session:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
    
    def get_search_urls(self, image_url: str) -> Dict[str, str]:
        """Gera URLs de busca reversa para todas as engines."""
        encoded_url = quote_plus(image_url)
        
        return {
            engine: f"{base_url}{encoded_url}"
            for engine, base_url in self.ENGINES.items()
        }
    
    def search_google(self, image_url: str) -> ImageSearchResult:
        """Busca no Google Images (retorna URL para busca manual)."""
        search_url = f"{self.ENGINES['google']}{quote_plus(image_url)}"
        
        # Nota: Scraping do Google é complexo devido a proteções
        # Em produção, usar Google Vision API
        
        return ImageSearchResult(
            engine="google",
            matches=[],
            similar_images=[],
            pages_with_image=[{
                "note": "Abra a URL no navegador para resultados",
                "search_url": search_url
            }]
        )
    
    def search_yandex(self, image_url: str) -> ImageSearchResult:
        """Busca no Yandex Images."""
        search_url = f"{self.ENGINES['yandex']}{quote_plus(image_url)}"
        
        return ImageSearchResult(
            engine="yandex",
            matches=[],
            similar_images=[],
            pages_with_image=[{
                "note": "Yandex geralmente tem bons resultados para faces",
                "search_url": search_url
            }]
        )
    
    def search_all(self, image_url: str) -> Dict[str, ImageSearchResult]:
        """Busca em todas as engines."""
        results = {}
        
        for engine in self.ENGINES.keys():
            method = getattr(self, f"search_{engine}", None)
            if method:
                try:
                    results[engine] = method(image_url)
                except Exception:
                    pass
        
        return results


class PimEyesSearch:
    """Interface para PimEyes (requer conta)."""
    
    API_URL = "https://pimeyes.com/api/search"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session() if requests else None
    
    def search(self, image_path: str) -> Dict:
        """Busca no PimEyes (requer API key)."""
        if not self.api_key:
            return {
                "note": "PimEyes requer assinatura paga",
                "url": "https://pimeyes.com",
                "manual_search": "Faça upload manual da imagem no site"
            }
        
        # Implementação real requereria API key válida
        return {"error": "API key necessária"}


class SocialMediaImageSearch:
    """Busca de imagens em redes sociais."""
    
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session() if requests else None
        if self.session:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            })
    
    def generate_search_queries(self, name: str) -> Dict[str, str]:
        """Gera URLs de busca em redes sociais."""
        encoded_name = quote_plus(name)
        
        return {
            "linkedin": f"https://www.linkedin.com/search/results/people/?keywords={encoded_name}",
            "facebook": f"https://www.facebook.com/search/people/?q={encoded_name}",
            "twitter": f"https://twitter.com/search?q={encoded_name}&f=user",
            "instagram": f"https://www.instagram.com/explore/tags/{encoded_name.replace('+', '')}",
            "google": f"https://www.google.com/search?q={encoded_name}+site:linkedin.com+OR+site:facebook.com",
        }
    
    def search_profile_by_username(self, username: str) -> Dict[str, Dict]:
        """Verifica existência de username em redes sociais."""
        platforms = {
            "twitter": f"https://twitter.com/{username}",
            "instagram": f"https://www.instagram.com/{username}",
            "github": f"https://github.com/{username}",
            "linkedin": f"https://www.linkedin.com/in/{username}",
            "facebook": f"https://www.facebook.com/{username}",
            "tiktok": f"https://www.tiktok.com/@{username}",
            "youtube": f"https://www.youtube.com/@{username}",
        }
        
        results = {}
        
        for platform, url in platforms.items():
            try:
                response = self.session.head(url, timeout=5, allow_redirects=True)
                exists = response.status_code == 200
                results[platform] = {
                    "url": url,
                    "exists": exists,
                    "status": response.status_code
                }
            except Exception:
                results[platform] = {
                    "url": url,
                    "exists": None,
                    "error": "Não foi possível verificar"
                }
        
        return results


class FaceRecognitionTools:
    """Interface principal de ferramentas de reconhecimento facial."""
    
    def __init__(self):
        self.reverse_search = ReverseImageSearch()
        self.social_search = SocialMediaImageSearch()
        self.pimeyes = PimEyesSearch()
        self.image_utils = ImageUtils()
    
    def analyze_image(self, image_path: str) -> Dict:
        """Analisa uma imagem localmente."""
        if not os.path.exists(image_path):
            return {"error": "Arquivo não encontrado"}
        
        if not self.image_utils.is_valid_image(image_path):
            return {"error": "Formato de imagem não suportado"}
        
        image_data = self.image_utils.load_image(image_path)
        if not image_data:
            return {"error": "Não foi possível carregar a imagem"}
        
        return {
            "path": image_path,
            "size": len(image_data),
            "hash": self.image_utils.get_image_hash(image_data),
            "base64_preview": self.image_utils.to_base64(image_data)[:100] + "...",
            "format": os.path.splitext(image_path)[1].lower()
        }
    
    def reverse_search_all(self, image_url: str) -> Dict:
        """Busca reversa em todas as engines."""
        urls = self.reverse_search.get_search_urls(image_url)
        
        return {
            "image_url": image_url,
            "search_urls": urls,
            "instructions": "Abra cada URL no navegador para ver resultados"
        }
    
    def osint_username(self, username: str) -> Dict:
        """OSINT completo de um username."""
        return {
            "username": username,
            "platforms": self.social_search.search_profile_by_username(username),
            "google_dork": f'"{username}" site:linkedin.com OR site:twitter.com OR site:instagram.com'
        }


def interactive_menu():
    """Menu interativo do Face Recognition."""
    tools = FaceRecognitionTools()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║          👤 FACE RECOGNITION - Olho de Deus                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔍 Busca Reversa de Imagem (URL)                        ║
║  [2] 📁 Analisar Imagem Local                                ║
║  [3] 🌐 OSINT de Username                                    ║
║  [4] 🔗 Gerar URLs de Busca Manual                           ║
║  [5] 📱 Verificar Redes Sociais por Nome                     ║
║                                                              ║
║  ⚠️  Use com responsabilidade e respeite a privacidade       ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Busca Reversa de Imagem ===")
            image_url = input("URL da imagem: ").strip()
            
            if not image_url:
                continue
            
            print("\nGerando URLs de busca...")
            result = tools.reverse_search_all(image_url)
            
            print(f"\n🔍 BUSCA REVERSA:")
            print(f"   Imagem: {result['image_url'][:60]}...")
            print(f"\n   URLs para busca manual:")
            
            for engine, url in result['search_urls'].items():
                print(f"\n   📌 {engine.upper()}:")
                print(f"      {url[:80]}...")
            
            print(f"\n   💡 Abra cada URL no navegador para ver resultados")
            print(f"   💡 Yandex geralmente tem melhores resultados para faces")
        
        elif escolha == '2':
            print("\n=== Analisar Imagem Local ===")
            image_path = input("Caminho da imagem: ").strip()
            
            if not image_path:
                continue
            
            result = tools.analyze_image(image_path)
            
            if result.get("error"):
                print(f"\n❌ {result['error']}")
            else:
                print(f"\n📷 ANÁLISE DA IMAGEM:")
                print(f"   Arquivo: {result['path']}")
                print(f"   Tamanho: {result['size']} bytes")
                print(f"   Formato: {result['format']}")
                print(f"   Hash SHA256: {result['hash'][:32]}...")
        
        elif escolha == '3':
            print("\n=== OSINT de Username ===")
            username = input("Username: ").strip()
            
            if not username:
                continue
            
            print(f"\nVerificando {username} em múltiplas plataformas...")
            result = tools.osint_username(username)
            
            print(f"\n👤 OSINT para @{username}:")
            print(f"\n   📱 Plataformas:")
            
            for platform, data in result['platforms'].items():
                if data.get('exists') is True:
                    print(f"      ✅ {platform}: {data['url']}")
                elif data.get('exists') is False:
                    print(f"      ❌ {platform}: Não encontrado")
                else:
                    print(f"      ❓ {platform}: {data.get('error', 'Não verificado')}")
            
            print(f"\n   🔍 Google Dork:")
            print(f"      {result['google_dork']}")
        
        elif escolha == '4':
            print("\n=== Gerar URLs de Busca ===")
            image_url = input("URL da imagem: ").strip()
            
            if not image_url:
                continue
            
            urls = tools.reverse_search.get_search_urls(image_url)
            
            print(f"\n🔗 URLs GERADAS:")
            for engine, url in urls.items():
                print(f"\n   {engine.upper()}:")
                print(f"   {url}")
            
            # Copiar para arquivo
            save = input("\nSalvar URLs em arquivo? (s/n): ").lower()
            if save == 's':
                with open("image_search_urls.txt", 'w') as f:
                    for engine, url in urls.items():
                        f.write(f"{engine}: {url}\n")
                print("✅ Salvo em image_search_urls.txt")
        
        elif escolha == '5':
            print("\n=== Buscar por Nome ===")
            name = input("Nome completo: ").strip()
            
            if not name:
                continue
            
            urls = tools.social_search.generate_search_queries(name)
            
            print(f"\n🔍 URLs de Busca para '{name}':")
            for platform, url in urls.items():
                print(f"\n   📌 {platform.upper()}:")
                print(f"      {url}")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
