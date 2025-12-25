#!/usr/bin/env python3
"""
pipeline.py

Simple pipeline that runs ingestion on a given source file, then optionally
encrypts the resulting DB and moves processed files to `raw_data/processed/`.

It calls existing `ingest_categorize.py` (so that we don't duplicate logic).
"""
import argparse
import os
import subprocess
import shutil


def run_ingest(source, db='data/leaks.db', salt='', allow_plaintext=False, category=None):
    cmd = ['python3', 'tools/ingest/ingest_categorize.py', '--source', source, '--db', db]
    if salt:
        cmd += ['--hash-salt', salt]
    if allow_plaintext:
        cmd += ['--allow-plaintext']
    if category:
        cmd += ['--category', category]
    subprocess.run(cmd, check=True)


def post_process(source, db, encrypt=False, cipher='AES256', processed_dir='raw_data/processed'):
    os.makedirs(processed_dir, exist_ok=True)
    if encrypt:
        print('Encriptando DB...')
        try:
            subprocess.run(['gpg','--batch','--yes','--symmetric','--cipher-algo',cipher,'-o', db + '.gpg', db], check=True)
            try:
                os.remove(db)
            except Exception:
                pass
            print(f'Arquivo encriptado: {db}.gpg')
        except FileNotFoundError:
            print('gpg não encontrado. Instale gpg para encriptação.')
        except subprocess.CalledProcessError as e:
            print('Erro durante encriptação:', e)
    # move source to processed
    try:
        shutil.move(source, os.path.join(processed_dir, os.path.basename(source)))
    except Exception as e:
        print('Aviso: falha ao mover arquivo processado:', e)


def main():
    p = argparse.ArgumentParser(description='Run ingestion pipeline for a single source file')
    p.add_argument('--source', required=True)
    p.add_argument('--db', default='data/leaks.db')
    p.add_argument('--hash-salt', default='')
    p.add_argument('--allow-plaintext', action='store_true')
    p.add_argument('--encrypt', action='store_true', help='Encrypt DB after ingestion (GPG symmetric)')
    p.add_argument('--processed-dir', default='raw_data/processed')
    args = p.parse_args()

    run_ingest(args.source, db=args.db, salt=args.hash_salt, allow_plaintext=args.allow_plaintext, category=None)
    post_process(args.source, args.db, encrypt=args.encrypt, processed_dir=args.processed_dir)


if __name__ == '__main__':
    main()
