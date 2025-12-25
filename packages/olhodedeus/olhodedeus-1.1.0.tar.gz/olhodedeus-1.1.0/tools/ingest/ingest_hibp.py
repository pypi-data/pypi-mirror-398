#!/usr/bin/env python3
"""
ingest_hibp.py

Pequeno utilitário para ingerir um arquivo no formato HIBP Pwned Passwords
(SHA1:count) para um banco SQLite local. Opcionalmente encripta o DB com GPG
apos a ingestão.

Uso seguro e legal: não automatize coleta de dados de vazamentos que não sejam
explicitamente permitidos para uso. Prefira fontes públicas e com permissão
para pesquisa (ex: HIBP Pwned Passwords export, datasets do Kaggle com licença
adequada).

Este script NÃO armazena passwords em plaintext — ele trabalha com hashes
SHA1 e contagens, evitando manter senhas em texto claro em disco.
"""
import argparse
import sqlite3
import sys
import os
import gzip
import shutil
import subprocess
from urllib.request import urlopen, Request


def download_to_file(url, dest_path):
    req = Request(url, headers={"User-Agent": "OlhoDeDeus-Ingest/1.0"})
    with urlopen(req) as resp, open(dest_path, "wb") as out:
        shutil.copyfileobj(resp, out)


def open_maybe_gz(path_or_fileobj):
    # If it's a filepath that endswith .gz, open with gzip, else open normally
    if isinstance(path_or_fileobj, str):
        if path_or_fileobj.endswith(".gz"):
            return gzip.open(path_or_fileobj, "rt", encoding="utf-8", errors="ignore")
        else:
            return open(path_or_fileobj, "r", encoding="utf-8", errors="ignore")
    else:
        # file-like object already
        return path_or_fileobj


def ingest_file(src, db_path, batch=10000):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode = WAL;")
    cur.execute("CREATE TABLE IF NOT EXISTS passwords(hash TEXT PRIMARY KEY, count INTEGER)")

    # Accept either local path or file-like (e.g., downloaded stream)
    if src.startswith("http://") or src.startswith("https://"):
        # download to temp file
        tmp = db_path + ".tmp_source"
        print(f"Baixando {src} ...")
        download_to_file(src, tmp)
        src_path = tmp
    else:
        src_path = src

    inserted = 0
    with open_maybe_gz(src_path) as fh:
        batch_vals = []
        for line in fh:
            line = line.strip()
            if not line:
                continue
            # Expected format: SHA1HASH:count (HIBP export)
            if ":" in line:
                h, c = line.split(":", 1)
                h = h.strip().upper()
                try:
                    c = int(c.strip())
                except Exception:
                    c = 1
                batch_vals.append((h, c))

            if len(batch_vals) >= batch:
                cur.executemany("INSERT OR REPLACE INTO passwords(hash,count) VALUES (?,COALESCE((SELECT count FROM passwords WHERE hash=?),0)+?)",
                                [(h, h, c) for (h, c) in batch_vals])
                conn.commit()
                inserted += len(batch_vals)
                print(f"Ingeridos: {inserted}", end="\r")
                batch_vals = []

        if batch_vals:
            cur.executemany("INSERT OR REPLACE INTO passwords(hash,count) VALUES (?,COALESCE((SELECT count FROM passwords WHERE hash=?),0)+?)",
                            [(h, h, c) for (h, c) in batch_vals])
            conn.commit()
            inserted += len(batch_vals)

    print(f"\nIngestão finalizada. Total de linhas processadas (aprox): {inserted}")

    # cleanup temp
    if src.startswith("http://") or src.startswith("https://"):
        try:
            os.remove(src_path)
        except Exception:
            pass

    conn.close()


def encrypt_db_with_gpg(db_path, symmetric=True, output_path=None):
    if output_path is None:
        output_path = db_path + ".gpg"
    if symmetric:
        cmd = ["gpg", "--batch", "--yes", "--symmetric", "--cipher-algo", "AES256", "-o", output_path, db_path]
    else:
        print("Encryption with public key selected, but no recipient specified. Use symmetric for now.")
        return False

    print("Encriptando DB com GPG (pode pedir frase):")
    try:
        subprocess.run(cmd, check=True)
        # remove original
        os.remove(db_path)
        print(f"Arquivo encriptado: {output_path}")
        return True
    except FileNotFoundError:
        print("GPG não encontrado. Instale gpg para usar a função de encriptação.")
        return False
    except subprocess.CalledProcessError as e:
        print("Erro durante encriptação:", e)
        return False


def main():
    p = argparse.ArgumentParser(description="Ingest HIBP-style password file into encrypted SQLite DB (hashes only)")
    p.add_argument("source", help="Local file path or URL to the source (plain or .gz). Format: SHA1:count per line")
    p.add_argument("--db", default="data/passwords.db", help="Output SQLite DB path")
    p.add_argument("--encrypt", action="store_true", help="Encrypt resulting DB with symmetric GPG (AES256)")
    args = p.parse_args()

    if args.source.startswith("http"):
        print("Atenção: baixando arquivo remoto. Garanta que tem permissão para usá-lo.")

    ingest_file(args.source, args.db)

    if args.encrypt:
        ok = encrypt_db_with_gpg(args.db)
        if not ok:
            print("Aviso: a encriptação falhou; o DB permanece em disco em texto (hashes).")


if __name__ == "__main__":
    main()
