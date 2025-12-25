#!/usr/bin/env python3
"""
decrypt_and_search.py

Decrypt a GPG-encrypted DB to a temporary file, run `search.py` against it,
then remove the temporary file. This avoids keeping plaintext DB on disk.
"""
import argparse
import subprocess
import tempfile
import os


def main():
    import sys
    p = argparse.ArgumentParser(description='Decrypt DB.gpg and run search')
    p.add_argument('--db-gpg', default='data/leaks.db.gpg')
    # Parse known args, remaining go to search.py
    args, remaining = p.parse_known_args()

    if not os.path.exists(args.db_gpg):
        print('Arquivo não encontrado:', args.db_gpg)
        return

    with tempfile.NamedTemporaryFile(prefix='leaks-', suffix='.db', delete=False) as tmp:
        tmpname = tmp.name
    try:
        subprocess.run(['gpg','--batch','--yes','-o', tmpname, '-d', args.db_gpg], check=True)
        cmd = ['python3','tools/ingest/search.py','--db', tmpname] + remaining
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print('Erro:', e)
    finally:
        try:
            os.remove(tmpname)
        except Exception:
            pass


if __name__ == '__main__':
    main()
