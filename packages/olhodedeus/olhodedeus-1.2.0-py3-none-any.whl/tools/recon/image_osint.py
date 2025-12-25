#!/usr/bin/env python3
"""
image_osint.py

OSINT para imagens e documentos - análise de metadados, hashes, etc.
"""
import os
import re
import json
import hashlib
import struct
from typing import Optional, Dict, List, BinaryIO
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
import requests


class ImageAnalyzer:
    """Analisador de imagens e metadados."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_file_hashes(self, filepath: str) -> Dict:
        """Calcula múltiplos hashes de um arquivo."""
        hashes = {
            'md5': hashlib.md5(),
            'sha1': hashlib.sha1(),
            'sha256': hashlib.sha256(),
        }
        
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    for h in hashes.values():
                        h.update(chunk)
            
            return {k: v.hexdigest() for k, v in hashes.items()}
        except Exception as e:
            return {'error': str(e)}
    
    def get_file_info(self, filepath: str) -> Dict:
        """Informações básicas do arquivo."""
        try:
            stat = os.stat(filepath)
            return {
                'path': filepath,
                'name': os.path.basename(filepath),
                'size': stat.st_size,
                'size_human': self._human_size(stat.st_size),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'accessed': datetime.fromtimestamp(stat.st_atime).isoformat(),
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _human_size(self, size: int) -> str:
        """Converte tamanho para formato legível."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
    
    def extract_exif_basic(self, filepath: str) -> Dict:
        """Extrai EXIF básico sem dependências externas."""
        exif_data = {}
        
        try:
            with open(filepath, 'rb') as f:
                # Verifica se é JPEG
                if f.read(2) != b'\xff\xd8':
                    return {'error': 'Não é um JPEG válido'}
                
                # Procura por marcadores EXIF
                while True:
                    marker = f.read(2)
                    if not marker or len(marker) < 2:
                        break
                    
                    if marker == b'\xff\xe1':  # APP1 (EXIF)
                        length = struct.unpack('>H', f.read(2))[0]
                        data = f.read(length - 2)
                        
                        # Procura por strings comuns no EXIF
                        text = data.decode('latin-1', errors='ignore')
                        
                        # Camera make/model
                        patterns = {
                            'make': rb'Make\x00([^\x00]+)',
                            'model': rb'Model\x00([^\x00]+)',
                            'software': rb'Software\x00([^\x00]+)',
                            'datetime': rb'DateTime\x00([^\x00]+)',
                            'artist': rb'Artist\x00([^\x00]+)',
                            'copyright': rb'Copyright\x00([^\x00]+)',
                        }
                        
                        for key, pattern in patterns.items():
                            match = re.search(pattern, data)
                            if match:
                                try:
                                    exif_data[key] = match.group(1).decode('utf-8', errors='ignore').strip()
                                except:
                                    pass
                        
                        # GPS data (simplificado)
                        if b'GPS' in data:
                            exif_data['has_gps'] = True
                        
                        break
                    elif marker[0:1] == b'\xff':
                        try:
                            length = struct.unpack('>H', f.read(2))[0]
                            f.seek(length - 2, 1)
                        except:
                            break
                    else:
                        break
        except Exception as e:
            exif_data['error'] = str(e)
        
        return exif_data
    
    def extract_png_metadata(self, filepath: str) -> Dict:
        """Extrai metadados de PNG."""
        metadata = {}
        
        try:
            with open(filepath, 'rb') as f:
                # Verifica assinatura PNG
                sig = f.read(8)
                if sig != b'\x89PNG\r\n\x1a\n':
                    return {'error': 'Não é um PNG válido'}
                
                # Lê chunks
                while True:
                    chunk_header = f.read(8)
                    if len(chunk_header) < 8:
                        break
                    
                    length, chunk_type = struct.unpack('>I4s', chunk_header)
                    chunk_type = chunk_type.decode('latin-1')
                    
                    if chunk_type == 'IHDR':
                        data = f.read(length)
                        width, height, depth, color_type = struct.unpack('>IIBB', data[:10])
                        metadata['width'] = width
                        metadata['height'] = height
                        metadata['bit_depth'] = depth
                        f.seek(4, 1)  # Skip CRC
                    elif chunk_type in ['tEXt', 'iTXt', 'zTXt']:
                        data = f.read(length)
                        try:
                            # tEXt: keyword\0text
                            if b'\x00' in data:
                                keyword, text = data.split(b'\x00', 1)
                                metadata[keyword.decode('latin-1')] = text.decode('utf-8', errors='ignore')
                        except:
                            pass
                        f.seek(4, 1)  # Skip CRC
                    elif chunk_type == 'IEND':
                        break
                    else:
                        f.seek(length + 4, 1)
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata
    
    def get_image_dimensions(self, filepath: str) -> Dict:
        """Obtém dimensões da imagem."""
        try:
            with open(filepath, 'rb') as f:
                header = f.read(32)
                
                # JPEG
                if header[:2] == b'\xff\xd8':
                    f.seek(0)
                    f.read(2)
                    while True:
                        marker = f.read(2)
                        if marker[0:1] != b'\xff':
                            break
                        if marker[1:2] in [b'\xc0', b'\xc1', b'\xc2']:
                            f.read(3)
                            h, w = struct.unpack('>HH', f.read(4))
                            return {'width': w, 'height': h, 'format': 'JPEG'}
                        else:
                            length = struct.unpack('>H', f.read(2))[0]
                            f.seek(length - 2, 1)
                
                # PNG
                if header[:8] == b'\x89PNG\r\n\x1a\n':
                    w, h = struct.unpack('>II', header[16:24])
                    return {'width': w, 'height': h, 'format': 'PNG'}
                
                # GIF
                if header[:6] in [b'GIF87a', b'GIF89a']:
                    w, h = struct.unpack('<HH', header[6:10])
                    return {'width': w, 'height': h, 'format': 'GIF'}
                
                # BMP
                if header[:2] == b'BM':
                    w, h = struct.unpack('<II', header[18:26])
                    return {'width': w, 'height': h, 'format': 'BMP'}
                
                # WebP
                if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
                    return {'format': 'WebP'}
                
        except Exception as e:
            return {'error': str(e)}
        
        return {'format': 'Unknown'}
    
    def reverse_image_search_urls(self, image_url: str = None, filepath: str = None) -> Dict:
        """Gera URLs para busca reversa."""
        urls = {}
        
        if image_url:
            encoded = quote(image_url, safe='')
            urls['google'] = f'https://www.google.com/searchbyimage?image_url={encoded}'
            urls['yandex'] = f'https://yandex.com/images/search?rpt=imageview&url={encoded}'
            urls['tineye'] = f'https://tineye.com/search?url={encoded}'
            urls['bing'] = f'https://www.bing.com/images/search?view=detailv2&iss=sbi&q=imgurl:{encoded}'
        
        # Para upload local
        urls['google_upload'] = 'https://images.google.com/'
        urls['yandex_upload'] = 'https://yandex.com/images/'
        urls['tineye_upload'] = 'https://tineye.com/'
        urls['pimeyes'] = 'https://pimeyes.com/en'  # Reconhecimento facial
        
        return urls
    
    def analyze_image(self, filepath: str) -> Dict:
        """Análise completa de uma imagem."""
        result = {
            'file_info': self.get_file_info(filepath),
            'hashes': self.get_file_hashes(filepath),
            'dimensions': self.get_image_dimensions(filepath),
        }
        
        # EXIF para JPEG
        if filepath.lower().endswith(('.jpg', '.jpeg')):
            result['exif'] = self.extract_exif_basic(filepath)
        elif filepath.lower().endswith('.png'):
            result['metadata'] = self.extract_png_metadata(filepath)
        
        return result


class DocumentAnalyzer:
    """Analisador de documentos."""
    
    def __init__(self):
        pass
    
    def extract_pdf_metadata(self, filepath: str) -> Dict:
        """Extrai metadados de PDF."""
        metadata = {}
        
        try:
            with open(filepath, 'rb') as f:
                content = f.read(8192)  # Lê início do arquivo
                
                # Verifica se é PDF
                if not content.startswith(b'%PDF'):
                    return {'error': 'Não é um PDF válido'}
                
                # Versão do PDF
                version_match = re.match(rb'%PDF-(\d\.\d)', content)
                if version_match:
                    metadata['pdf_version'] = version_match.group(1).decode()
                
                # Procura por Info dictionary
                text = content.decode('latin-1', errors='ignore')
                
                patterns = {
                    'title': r'/Title\s*\(([^)]*)\)',
                    'author': r'/Author\s*\(([^)]*)\)',
                    'subject': r'/Subject\s*\(([^)]*)\)',
                    'creator': r'/Creator\s*\(([^)]*)\)',
                    'producer': r'/Producer\s*\(([^)]*)\)',
                    'creation_date': r'/CreationDate\s*\(([^)]*)\)',
                    'mod_date': r'/ModDate\s*\(([^)]*)\)',
                }
                
                for key, pattern in patterns.items():
                    match = re.search(pattern, text)
                    if match:
                        metadata[key] = match.group(1)
                
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata
    
    def extract_office_metadata(self, filepath: str) -> Dict:
        """Extrai metadados de documentos Office (docx, xlsx, pptx)."""
        metadata = {}
        
        try:
            import zipfile
            
            with zipfile.ZipFile(filepath, 'r') as z:
                # Procura por core.xml (metadados)
                if 'docProps/core.xml' in z.namelist():
                    core = z.read('docProps/core.xml').decode('utf-8', errors='ignore')
                    
                    patterns = {
                        'title': r'<dc:title>([^<]*)</dc:title>',
                        'creator': r'<dc:creator>([^<]*)</dc:creator>',
                        'last_modified_by': r'<cp:lastModifiedBy>([^<]*)</cp:lastModifiedBy>',
                        'created': r'<dcterms:created[^>]*>([^<]*)</dcterms:created>',
                        'modified': r'<dcterms:modified[^>]*>([^<]*)</dcterms:modified>',
                        'revision': r'<cp:revision>([^<]*)</cp:revision>',
                    }
                    
                    for key, pattern in patterns.items():
                        match = re.search(pattern, core)
                        if match:
                            metadata[key] = match.group(1)
                
                # App properties
                if 'docProps/app.xml' in z.namelist():
                    app = z.read('docProps/app.xml').decode('utf-8', errors='ignore')
                    
                    patterns = {
                        'application': r'<Application>([^<]*)</Application>',
                        'app_version': r'<AppVersion>([^<]*)</AppVersion>',
                        'company': r'<Company>([^<]*)</Company>',
                        'pages': r'<Pages>([^<]*)</Pages>',
                        'words': r'<Words>([^<]*)</Words>',
                    }
                    
                    for key, pattern in patterns.items():
                        match = re.search(pattern, app)
                        if match:
                            metadata[key] = match.group(1)
        
        except zipfile.BadZipFile:
            metadata['error'] = 'Não é um arquivo Office válido'
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata
    
    def analyze_document(self, filepath: str) -> Dict:
        """Análise completa de documento."""
        result = {
            'path': filepath,
            'name': os.path.basename(filepath),
            'size': os.path.getsize(filepath),
        }
        
        # Hashes
        img_analyzer = ImageAnalyzer()
        result['hashes'] = img_analyzer.get_file_hashes(filepath)
        
        # Metadados por tipo
        lower = filepath.lower()
        if lower.endswith('.pdf'):
            result['metadata'] = self.extract_pdf_metadata(filepath)
        elif lower.endswith(('.docx', '.xlsx', '.pptx')):
            result['metadata'] = self.extract_office_metadata(filepath)
        
        return result


def interactive_menu():
    """Menu interativo."""
    img_analyzer = ImageAnalyzer()
    doc_analyzer = DocumentAnalyzer()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("""
╔══════════════════════════════════════════════════════════════╗
║              🖼️ IMAGE & DOCUMENT OSINT                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ──── 🖼️ IMAGENS ────                                         ║
║  [1] 📷 Analisar Imagem (EXIF, hashes, etc)                  ║
║  [2] 🔍 Busca Reversa de Imagem (URLs)                       ║
║  [3] 📊 Calcular Hashes de Arquivo                           ║
║                                                              ║
║  ──── 📄 DOCUMENTOS ────                                     ║
║  [4] 📄 Analisar PDF                                         ║
║  [5] 📝 Analisar Office (docx/xlsx/pptx)                     ║
║                                                              ║
║  ──── 📁 BATCH ────                                          ║
║  [6] 📁 Analisar Diretório                                   ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            path = input("\n📷 Caminho da imagem: ").strip().strip('"')
            if path and os.path.exists(path):
                result = img_analyzer.analyze_image(path)
                
                print(f"\n📊 ANÁLISE DA IMAGEM:\n")
                
                # Info básica
                info = result.get('file_info', {})
                print(f"   Nome: {info.get('name')}")
                print(f"   Tamanho: {info.get('size_human')}")
                print(f"   Modificado: {info.get('modified')}")
                
                # Dimensões
                dims = result.get('dimensions', {})
                if dims.get('width'):
                    print(f"\n   Dimensões: {dims['width']}x{dims['height']}")
                    print(f"   Formato: {dims.get('format')}")
                
                # Hashes
                hashes = result.get('hashes', {})
                print(f"\n   Hashes:")
                for h, v in hashes.items():
                    if h != 'error':
                        print(f"      {h.upper()}: {v}")
                
                # EXIF
                exif = result.get('exif', {})
                if exif and 'error' not in exif:
                    print(f"\n   📷 EXIF:")
                    for k, v in exif.items():
                        print(f"      {k}: {v}")
                
                # PNG metadata
                meta = result.get('metadata', {})
                if meta and 'error' not in meta:
                    print(f"\n   📷 Metadados:")
                    for k, v in meta.items():
                        if k not in ['width', 'height', 'bit_depth']:
                            print(f"      {k}: {v[:50]}...")
            else:
                print("❌ Arquivo não encontrado")
            input("\nPressione Enter...")
        
        elif choice == '2':
            url = input("\n🔗 URL da imagem (ou Enter para upload local): ").strip()
            
            urls = img_analyzer.reverse_image_search_urls(url if url else None)
            print(f"\n🔍 LINKS PARA BUSCA REVERSA:\n")
            
            if url:
                print("   Com URL:")
                for service, link in urls.items():
                    if not service.endswith('_upload'):
                        print(f"      {service.upper()}: {link}")
            
            print("\n   Para upload local:")
            for service, link in urls.items():
                if service.endswith('_upload') or service == 'pimeyes':
                    name = service.replace('_upload', '').upper()
                    print(f"      {name}: {link}")
            input("\nPressione Enter...")
        
        elif choice == '3':
            path = input("\n📁 Caminho do arquivo: ").strip().strip('"')
            if path and os.path.exists(path):
                hashes = img_analyzer.get_file_hashes(path)
                print(f"\n📊 HASHES:\n")
                for h, v in hashes.items():
                    print(f"   {h.upper()}: {v}")
                
                # VirusTotal link
                print(f"\n🔍 Verificar no VirusTotal:")
                print(f"   https://www.virustotal.com/gui/file/{hashes.get('sha256', '')}")
            else:
                print("❌ Arquivo não encontrado")
            input("\nPressione Enter...")
        
        elif choice == '4':
            path = input("\n📄 Caminho do PDF: ").strip().strip('"')
            if path and os.path.exists(path):
                result = doc_analyzer.analyze_document(path)
                
                print(f"\n📊 ANÁLISE DO PDF:\n")
                print(f"   Nome: {result.get('name')}")
                print(f"   Tamanho: {result.get('size')} bytes")
                
                meta = result.get('metadata', {})
                if meta and 'error' not in meta:
                    print(f"\n   📄 Metadados:")
                    for k, v in meta.items():
                        print(f"      {k}: {v}")
            else:
                print("❌ Arquivo não encontrado")
            input("\nPressione Enter...")
        
        elif choice == '5':
            path = input("\n📝 Caminho do documento Office: ").strip().strip('"')
            if path and os.path.exists(path):
                result = doc_analyzer.analyze_document(path)
                
                print(f"\n📊 ANÁLISE DO DOCUMENTO:\n")
                print(f"   Nome: {result.get('name')}")
                
                meta = result.get('metadata', {})
                if meta and 'error' not in meta:
                    print(f"\n   📝 Metadados:")
                    for k, v in meta.items():
                        print(f"      {k}: {v}")
                else:
                    print(f"   ❌ {meta.get('error', 'Sem metadados')}")
            else:
                print("❌ Arquivo não encontrado")
            input("\nPressione Enter...")
        
        elif choice == '6':
            path = input("\n📁 Caminho do diretório: ").strip().strip('"')
            if path and os.path.isdir(path):
                extensions = input("Extensões (ex: jpg,png,pdf ou Enter para todas): ").strip()
                
                exts = tuple(f'.{e.strip()}' for e in extensions.split(',')) if extensions else None
                
                print(f"\n📊 ANALISANDO...\n")
                
                for root, dirs, files in os.walk(path):
                    for f in files:
                        if exts is None or f.lower().endswith(exts):
                            fpath = os.path.join(root, f)
                            hashes = img_analyzer.get_file_hashes(fpath)
                            print(f"   {f}: {hashes.get('md5', 'erro')[:16]}...")
            else:
                print("❌ Diretório não encontrado")
            input("\nPressione Enter...")
        
        elif choice == '0':
            break


if __name__ == '__main__':
    interactive_menu()
