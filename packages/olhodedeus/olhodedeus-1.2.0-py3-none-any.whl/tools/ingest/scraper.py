#!/usr/bin/env python3
"""
scraper.py

Download configured allowed sources (files or pages), save raw content to
`raw_data/` and produce an extracted CSV when possible. Respects a simple
rate-limit and size limits. Only use with sources you have permission to
process.

Atualizado: Suporta download de wordlists do SecLists e outras fontes.
"""
import os
import json
import argparse
import time
import hashlib
import csv
from urllib.parse import urlparse
from typing import Optional, Dict, List, Any

# Importações locais com fallback
try:
    from tools.ingest.utils import safe_download
    from tools.ingest.extractors import extract_from_text
except ImportError:
    from utils import safe_download
    from extractors import extract_from_text


def sanitize_filename(url: str) -> str:
    """Gera um nome de arquivo seguro baseado na URL."""
    h = hashlib.sha1(url.encode('utf-8')).hexdigest()
    parsed = urlparse(url)
    name = parsed.netloc + parsed.path.replace('/', '_')
    name = name.strip('_')
    # Limpar caracteres problemáticos
    name = ''.join(c for c in name if c.isalnum() or c in '-_.')
    return f"{name[:80]}_{h[:8]}"


def process_source(url: str, out_dir: str = 'raw_data', max_bytes: int = 50_000_000) -> Optional[Dict]:
    """
    Baixa uma fonte e tenta extrair dados.
    
    Args:
        url: URL para baixar
        out_dir: Diretório de saída
        max_bytes: Limite máximo de bytes
        
    Returns:
        Dict com caminhos dos arquivos ou None se falhou
    """
    os.makedirs(out_dir, exist_ok=True)
    fname = sanitize_filename(url)
    dest = os.path.join(out_dir, fname)
    print(f"📥 Baixando {url}")
    print(f"   -> {dest}")
    
    try:
        path = safe_download(url, dest, max_bytes=max_bytes)
    except Exception as e:
        print(f"❌ Erro ao baixar: {e}")
        return None

    # Determinar tipo de arquivo
    file_size = os.path.getsize(path)
    print(f"✅ Baixado: {file_size:,} bytes")
    
    # Tentar decodificar como texto
    text = None
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
            text = fh.read()
    except Exception:
        pass

    extracted_csv_path = None
    if text:
        items = extract_from_text(text)
        if items:
            extracted_csv_path = os.path.join(out_dir, 'processed', f"{fname}_extracted.csv")
            os.makedirs(os.path.dirname(extracted_csv_path), exist_ok=True)
            
            with open(extracted_csv_path, 'w', encoding='utf-8', newline='') as csvf:
                writer = csv.DictWriter(csvf, fieldnames=['email', 'password', 'cpf', 'name', 'raw'])
                writer.writeheader()
                for it in items:
                    writer.writerow({k: it.get(k, '') for k in ['email', 'password', 'cpf', 'name', 'raw']})
            print(f"📊 Extraído: {len(items)} itens -> {extracted_csv_path}")
    
    return {'downloaded': path, 'extracted_csv': extracted_csv_path, 'size': file_size}


def download_wordlist(name: str, out_dir: str = 'raw_data/wordlists') -> Optional[str]:
    """
    Baixa uma wordlist do SecLists.
    
    Args:
        name: Nome da wordlist (ex: 'Common-Credentials/10k-most-common.txt')
        out_dir: Diretório de saída
        
    Returns:
        Caminho do arquivo baixado ou None
    """
    import requests
    
    base_url = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords"
    url = f"{base_url}/{name}"
    
    os.makedirs(out_dir, exist_ok=True)
    filename = name.replace('/', '_')
    dest = os.path.join(out_dir, filename)
    
    print(f"📥 Baixando wordlist: {name}")
    try:
        resp = requests.get(url, timeout=60, stream=True)
        if resp.status_code == 200:
            with open(dest, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            size = os.path.getsize(dest)
            print(f"✅ Salvo: {dest} ({size:,} bytes)")
            return dest
        else:
            print(f"❌ Erro HTTP {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


def list_wordlists() -> List[str]:
    """Lista wordlists disponíveis para download."""
    return [
        "Common-Credentials/10-million-password-list-top-100.txt",
        "Common-Credentials/10-million-password-list-top-1000.txt",
        "Common-Credentials/10-million-password-list-top-10000.txt",
        "Common-Credentials/10-million-password-list-top-100000.txt",
        "Common-Credentials/10k-most-common.txt",
        "Common-Credentials/100k-most-used-passwords-NCSC.txt",
        "darkweb2017-top10000.txt",
        "xato-net-10-million-passwords.txt",
    ]


def main():
    p = argparse.ArgumentParser(description='Scrape allowed sources and save to raw_data/')
    p.add_argument('--config', default='tools/ingest/allowed_sources.json', help='JSON config with array of URLs')
    p.add_argument('--out', default='raw_data', help='Output folder')
    p.add_argument('--sleep', type=float, default=1.0, help='Seconds between downloads')
    p.add_argument('--wordlist', type=str, help='Download specific wordlist from SecLists')
    p.add_argument('--list-wordlists', action='store_true', help='List available wordlists')
    args = p.parse_args()

    # Listar wordlists disponíveis
    if args.list_wordlists:
        print("\n📋 Wordlists disponíveis (SecLists):\n")
        for i, wl in enumerate(list_wordlists(), 1):
            print(f"  [{i}] {wl}")
        print("\nUse: python scraper.py --wordlist 'Common-Credentials/10k-most-common.txt'")
        return
    
    # Baixar wordlist específica
    if args.wordlist:
        download_wordlist(args.wordlist, os.path.join(args.out, 'wordlists'))
        return

    # Processar URLs do config
    if not os.path.exists(args.config):
        print(f'❌ Config não encontrado: {args.config}')
        return
    
    with open(args.config, 'r', encoding='utf-8') as fh:
        cfg = json.load(fh)

    urls = cfg.get('urls', [])
    
    if not urls:
        print("⚠️  Nenhuma URL configurada em allowed_sources.json")
        print("\n📋 Opções disponíveis:")
        print("  1. Adicione URLs ao arquivo de configuração")
        print("  2. Use --wordlist para baixar wordlists do SecLists")
        print("  3. Use --list-wordlists para ver wordlists disponíveis")
        return
    
    print(f"\n🔄 Processando {len(urls)} URLs...\n")
    results = []
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] ", end='')
        result = process_source(url, out_dir=args.out)
        if result:
            results.append(result)
        time.sleep(args.sleep)
    
    print(f"\n✅ Concluído: {len(results)}/{len(urls)} fontes processadas")


if __name__ == '__main__':
    main()
