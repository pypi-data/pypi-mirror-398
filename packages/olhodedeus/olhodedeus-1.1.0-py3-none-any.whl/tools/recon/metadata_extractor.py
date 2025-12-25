#!/usr/bin/env python3
"""
Metadata Extractor - Olho de Deus
Extração de metadados de arquivos e documentos
"""

import os
import re
import json
import struct
import hashlib
from typing import Dict, List, Optional, Any, BinaryIO
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class FileMetadata:
    """Metadados de um arquivo"""
    filename: str
    filepath: str
    size: int = 0
    mime_type: str = ""
    file_type: str = ""
    created: str = ""
    modified: str = ""
    accessed: str = ""
    md5: str = ""
    sha256: str = ""
    
    # Metadados específicos
    author: str = ""
    creator: str = ""
    producer: str = ""
    title: str = ""
    subject: str = ""
    keywords: List[str] = field(default_factory=list)
    creation_date: str = ""
    modification_date: str = ""
    
    # Metadados de imagem
    width: int = 0
    height: int = 0
    color_depth: int = 0
    compression: str = ""
    
    # EXIF
    camera_make: str = ""
    camera_model: str = ""
    gps_latitude: float = 0.0
    gps_longitude: float = 0.0
    gps_location: str = ""
    datetime_original: str = ""
    software: str = ""
    
    # Extra
    extra: Dict[str, Any] = field(default_factory=dict)


class MetadataExtractor:
    """Extrator de metadados de arquivos"""
    
    # Magic bytes para identificação de tipos
    MAGIC_BYTES = {
        b'\x89PNG': 'image/png',
        b'\xff\xd8\xff': 'image/jpeg',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
        b'%PDF': 'application/pdf',
        b'PK\x03\x04': 'application/zip',
        b'\x50\x4b\x03\x04': 'application/zip',  # Pode ser docx, xlsx, etc
        b'\xd0\xcf\x11\xe0': 'application/msword',  # DOC antigo
        b'Rar!': 'application/x-rar',
        b'\x1f\x8b': 'application/gzip',
        b'BZh': 'application/x-bzip2',
        b'\x7fELF': 'application/x-executable',
        b'MZ': 'application/x-executable',  # Windows exe
        b'ID3': 'audio/mpeg',
        b'\xff\xfb': 'audio/mpeg',
        b'OggS': 'audio/ogg',
        b'ftyp': 'video/mp4',
        b'\x00\x00\x00\x1c': 'video/mp4',
    }
    
    def __init__(self):
        self.results: List[FileMetadata] = []
    
    def extract(self, filepath: str) -> FileMetadata:
        """Extrai metadados de um arquivo"""
        filepath = os.path.abspath(filepath)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        
        meta = FileMetadata(
            filename=os.path.basename(filepath),
            filepath=filepath
        )
        
        # Informações básicas do sistema
        stat = os.stat(filepath)
        meta.size = stat.st_size
        meta.modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
        meta.accessed = datetime.fromtimestamp(stat.st_atime).isoformat()
        meta.created = datetime.fromtimestamp(stat.st_ctime).isoformat()
        
        # Calcular hashes
        meta.md5, meta.sha256 = self._calculate_hashes(filepath)
        
        # Identificar tipo
        meta.mime_type = self._identify_type(filepath)
        meta.file_type = meta.mime_type.split('/')[-1].upper()
        
        # Extrair metadados específicos por tipo
        if 'image' in meta.mime_type:
            self._extract_image_metadata(filepath, meta)
        elif 'pdf' in meta.mime_type:
            self._extract_pdf_metadata(filepath, meta)
        elif meta.mime_type == 'application/zip':
            self._extract_office_metadata(filepath, meta)
        
        return meta
    
    def _calculate_hashes(self, filepath: str) -> tuple:
        """Calcula hashes MD5 e SHA256"""
        md5 = hashlib.md5()
        sha256 = hashlib.sha256()
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
                sha256.update(chunk)
        
        return md5.hexdigest(), sha256.hexdigest()
    
    def _identify_type(self, filepath: str) -> str:
        """Identifica tipo de arquivo por magic bytes"""
        with open(filepath, 'rb') as f:
            header = f.read(16)
        
        for magic, mime in self.MAGIC_BYTES.items():
            if header.startswith(magic):
                return mime
        
        # Fallback por extensão
        ext = Path(filepath).suffix.lower()
        ext_map = {
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.htm': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.csv': 'text/csv',
            '.md': 'text/markdown',
            '.py': 'text/x-python',
            '.java': 'text/x-java',
            '.c': 'text/x-c',
            '.cpp': 'text/x-c++',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        }
        
        return ext_map.get(ext, 'application/octet-stream')
    
    def _extract_image_metadata(self, filepath: str, meta: FileMetadata):
        """Extrai metadados de imagem"""
        with open(filepath, 'rb') as f:
            header = f.read(32)
            
            # PNG
            if header.startswith(b'\x89PNG'):
                f.seek(16)
                width_bytes = f.read(4)
                height_bytes = f.read(4)
                meta.width = struct.unpack('>I', width_bytes)[0]
                meta.height = struct.unpack('>I', height_bytes)[0]
            
            # JPEG
            elif header.startswith(b'\xff\xd8\xff'):
                self._extract_jpeg_metadata(f, meta)
            
            # GIF
            elif header.startswith(b'GIF'):
                f.seek(6)
                meta.width = struct.unpack('<H', f.read(2))[0]
                meta.height = struct.unpack('<H', f.read(2))[0]
    
    def _extract_jpeg_metadata(self, f: BinaryIO, meta: FileMetadata):
        """Extrai metadados de JPEG incluindo EXIF"""
        f.seek(0)
        
        # Procurar marcadores
        while True:
            marker = f.read(2)
            if len(marker) < 2:
                break
            
            if marker[0] != 0xff:
                continue
            
            # SOF0 ou SOF2 - contém dimensões
            if marker[1] in [0xc0, 0xc2]:
                f.read(3)  # Skip length and precision
                meta.height = struct.unpack('>H', f.read(2))[0]
                meta.width = struct.unpack('>H', f.read(2))[0]
            
            # APP1 - EXIF
            elif marker[1] == 0xe1:
                length = struct.unpack('>H', f.read(2))[0]
                exif_data = f.read(length - 2)
                self._parse_exif(exif_data, meta)
                break
            
            # Outro marcador
            elif marker[1] >= 0xe0:
                length = struct.unpack('>H', f.read(2))[0]
                f.seek(f.tell() + length - 2)
            
            # SOS - fim dos metadados
            elif marker[1] == 0xda:
                break
    
    def _parse_exif(self, data: bytes, meta: FileMetadata):
        """Parse básico de dados EXIF"""
        if not data.startswith(b'Exif\x00\x00'):
            return
        
        # Procurar strings de texto nos dados EXIF
        text = data.decode('latin-1', errors='ignore')
        
        # Make/Model da câmera
        patterns = {
            'camera_make': r'(Canon|Nikon|Sony|Apple|Samsung|Huawei|Xiaomi|Google|OnePlus)',
            'camera_model': r'(iPhone\s*\d+|Pixel\s*\d+|Galaxy\s*[A-Z]\d+|D\d{4}|EOS\s*\d+)',
            'software': r'(Adobe\s*[^\x00]+|GIMP|Photoshop|Lightroom)',
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                setattr(meta, field, match.group(0).strip())
        
        # GPS (simplificado - busca por padrões de coordenadas)
        gps_pattern = r'(\d{1,3})[°\s]+(\d{1,2})[\'\']+\s*(\d{1,2}(?:\.\d+)?)[""]*\s*([NSEW])'
        gps_matches = re.findall(gps_pattern, text)
        
        if len(gps_matches) >= 2:
            try:
                lat = self._dms_to_decimal(*gps_matches[0])
                lon = self._dms_to_decimal(*gps_matches[1])
                meta.gps_latitude = lat
                meta.gps_longitude = lon
                meta.gps_location = f"{lat:.6f}, {lon:.6f}"
            except:
                pass
    
    def _dms_to_decimal(self, deg: str, min: str, sec: str, direction: str) -> float:
        """Converte graus/minutos/segundos para decimal"""
        decimal = float(deg) + float(min)/60 + float(sec)/3600
        if direction.upper() in ['S', 'W']:
            decimal = -decimal
        return decimal
    
    def _extract_pdf_metadata(self, filepath: str, meta: FileMetadata):
        """Extrai metadados de PDF"""
        with open(filepath, 'rb') as f:
            content = f.read(4096)  # Ler início do arquivo
        
        text = content.decode('latin-1', errors='ignore')
        
        # Procurar metadados no dicionário Info
        patterns = {
            'author': r'/Author\s*\(([^)]+)\)',
            'creator': r'/Creator\s*\(([^)]+)\)',
            'producer': r'/Producer\s*\(([^)]+)\)',
            'title': r'/Title\s*\(([^)]+)\)',
            'subject': r'/Subject\s*\(([^)]+)\)',
            'creation_date': r'/CreationDate\s*\(([^)]+)\)',
            'modification_date': r'/ModDate\s*\(([^)]+)\)',
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                value = match.group(1).strip()
                setattr(meta, field, value)
        
        # Keywords
        kw_match = re.search(r'/Keywords\s*\(([^)]+)\)', text)
        if kw_match:
            meta.keywords = [k.strip() for k in kw_match.group(1).split(',')]
    
    def _extract_office_metadata(self, filepath: str, meta: FileMetadata):
        """Extrai metadados de documentos Office (OOXML)"""
        import zipfile
        
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                # Verificar tipo de documento
                if 'word/document.xml' in zf.namelist():
                    meta.file_type = 'DOCX'
                elif 'xl/workbook.xml' in zf.namelist():
                    meta.file_type = 'XLSX'
                elif 'ppt/presentation.xml' in zf.namelist():
                    meta.file_type = 'PPTX'
                
                # Ler core.xml para metadados
                if 'docProps/core.xml' in zf.namelist():
                    core = zf.read('docProps/core.xml').decode('utf-8', errors='ignore')
                    
                    patterns = {
                        'author': r'<dc:creator>([^<]+)</dc:creator>',
                        'title': r'<dc:title>([^<]+)</dc:title>',
                        'subject': r'<dc:subject>([^<]+)</dc:subject>',
                        'creation_date': r'<dcterms:created[^>]*>([^<]+)</dcterms:created>',
                        'modification_date': r'<dcterms:modified[^>]*>([^<]+)</dcterms:modified>',
                    }
                    
                    for field, pattern in patterns.items():
                        match = re.search(pattern, core)
                        if match:
                            setattr(meta, field, match.group(1))
                
                # Ler app.xml para informações adicionais
                if 'docProps/app.xml' in zf.namelist():
                    app = zf.read('docProps/app.xml').decode('utf-8', errors='ignore')
                    
                    app_match = re.search(r'<Application>([^<]+)</Application>', app)
                    if app_match:
                        meta.software = app_match.group(1)
        except:
            pass
    
    def extract_batch(self, directory: str, recursive: bool = True) -> List[FileMetadata]:
        """Extrai metadados de múltiplos arquivos"""
        results = []
        
        if recursive:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    filepath = os.path.join(root, file)
                    try:
                        meta = self.extract(filepath)
                        results.append(meta)
                    except Exception as e:
                        print(f"   ⚠️ Erro em {file}: {e}")
        else:
            for file in os.listdir(directory):
                filepath = os.path.join(directory, file)
                if os.path.isfile(filepath):
                    try:
                        meta = self.extract(filepath)
                        results.append(meta)
                    except Exception as e:
                        print(f"   ⚠️ Erro em {file}: {e}")
        
        self.results = results
        return results
    
    def print_metadata(self, meta: FileMetadata):
        """Imprime metadados formatados"""
        print(f"\n📄 {meta.filename}")
        print("=" * 50)
        print(f"   Tipo: {meta.file_type}")
        print(f"   Tamanho: {self._format_size(meta.size)}")
        print(f"   MIME: {meta.mime_type}")
        print(f"   MD5: {meta.md5}")
        print(f"   SHA256: {meta.sha256[:32]}...")
        
        if meta.author:
            print(f"\n   👤 Autor: {meta.author}")
        if meta.creator:
            print(f"   🛠️ Criador: {meta.creator}")
        if meta.software:
            print(f"   💻 Software: {meta.software}")
        if meta.title:
            print(f"   📌 Título: {meta.title}")
        
        if meta.width and meta.height:
            print(f"\n   📐 Dimensões: {meta.width}x{meta.height}")
        
        if meta.camera_make or meta.camera_model:
            print(f"\n   📷 Câmera: {meta.camera_make} {meta.camera_model}")
        
        if meta.gps_location:
            print(f"   📍 GPS: {meta.gps_location}")
        
        print(f"\n   📅 Modificado: {meta.modified}")
    
    def _format_size(self, size: int) -> str:
        """Formata tamanho em bytes"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def export_results(self, filepath: str):
        """Exporta resultados para JSON"""
        data = []
        for meta in self.results:
            data.append({
                'filename': meta.filename,
                'filepath': meta.filepath,
                'size': meta.size,
                'mime_type': meta.mime_type,
                'md5': meta.md5,
                'sha256': meta.sha256,
                'author': meta.author,
                'creator': meta.creator,
                'software': meta.software,
                'title': meta.title,
                'dimensions': f"{meta.width}x{meta.height}" if meta.width else "",
                'camera': f"{meta.camera_make} {meta.camera_model}".strip(),
                'gps': meta.gps_location,
                'modified': meta.modified,
            })
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n📄 Resultados salvos: {filepath}")


def main():
    """Função principal"""
    import sys
    
    print("\n" + "=" * 50)
    print("📋 Metadata Extractor - Olho de Deus")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        path = input("\n📁 Arquivo ou diretório: ").strip()
    else:
        path = sys.argv[1]
    
    extractor = MetadataExtractor()
    
    if os.path.isfile(path):
        meta = extractor.extract(path)
        extractor.print_metadata(meta)
    elif os.path.isdir(path):
        print(f"\n🔍 Extraindo metadados de: {path}")
        results = extractor.extract_batch(path)
        print(f"\n📊 Total: {len(results)} arquivos processados")
        
        for meta in results[:10]:
            extractor.print_metadata(meta)
        
        if len(results) > 10:
            print(f"\n... e mais {len(results) - 10} arquivos")
    else:
        print(f"❌ Caminho não encontrado: {path}")
    
    print("\n✅ Extração concluída!")


if __name__ == "__main__":
    main()
