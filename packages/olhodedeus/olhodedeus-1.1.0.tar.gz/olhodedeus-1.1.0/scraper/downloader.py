#!/usr/bin/env python3
"""
scraper.py

Download configured allowed sources (files or pages), save raw content to
`raw_data/` and produce an extracted CSV when possible. Respects a simple
rate-limit and size limits. Only use with sources you have permission to
process.
"""
import os
import json
import argparse
import time
import hashlib
from urllib.parse import urlparse
from tools.ingest.utils import safe_download
from tools.ingest.extractors import extract_from_text


def sanitize_filename(url):
    h = hashlib.sha1(url.encode('utf-8')).hexdigest()
    parsed = urlparse(url)
    name = parsed.netloc + parsed.path.replace('/', '_')
    name = name.strip('_')
    return f"{name[:80]}_{h[:8]}"


def process_source(url, out_dir='raw_data', max_bytes=50_000_000):
    os.makedirs(out_dir, exist_ok=True)
    fname = sanitize_filename(url)
    dest = os.path.join(out_dir, fname)
    print(f"Baixando {url} -> {dest} ...")
    try:
        path = safe_download(url, dest, max_bytes=max_bytes)
    except Exception as e:
        print(f"Erro ao baixar {url}: {e}")
        return None

    # Try to decode as text
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
            text = fh.read()
    except Exception:
        text = None

    extracted_csv_path = None
    if text:
        items = extract_from_text(text)
        if items:
            # write CSV
            import csv
            extracted_csv_path = os.path.join(out_dir, f"{fname}_extracted.csv")
            with open(extracted_csv_path, 'w', encoding='utf-8', newline='') as csvf:
                writer = csv.DictWriter(csvf, fieldnames=['email','password','cpf','name','raw'])
                writer.writeheader()
                for it in items:
                    writer.writerow({k: it.get(k, '') for k in ['email','password','cpf','name','raw']})
            print(f"Extraído: {extracted_csv_path} ({len(items)} itens)")
    return {'downloaded': path, 'extracted_csv': extracted_csv_path}


def main():
    p = argparse.ArgumentParser(description='Scrape allowed sources and save to raw_data/')
    p.add_argument('--config', default='tools/ingest/allowed_sources.json', help='JSON config with array of URLs')
    p.add_argument('--out', default='raw_data', help='Output folder')
    p.add_argument('--sleep', type=float, default=1.0, help='Seconds between downloads')
    args = p.parse_args()

    if not os.path.exists(args.config):
        print('Config not found:', args.config)
        return
    with open(args.config, 'r', encoding='utf-8') as fh:
        cfg = json.load(fh)

    urls = cfg.get('urls', [])
    for url in urls:
        process_source(url, out_dir=args.out)
        time.sleep(args.sleep)


if __name__ == '__main__':
    main()
