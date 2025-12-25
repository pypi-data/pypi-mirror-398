#!/usr/bin/env python3
"""
ingest_categorize.py

Ingesta categorizada de arquivos de vazamento para um DB SQLite local.

Princípios de segurança embutidos:
- Por padrão, campos sensíveis (emails, senhas, nomes, CPFs) são armazenados
  como hashes (SHA256) para evitar manter PII em texto claro.
- Para armazenar plaintext é necessário passar explicitamente `--allow-plaintext`
  (o script avisará sobre o risco). Recomendado NÃO usar esse modo.
- O script não faz raspagem automática de sites públicos; aceita apenas
  arquivos locais ou URLs apontadas por você (garanta permissão legal).

Deduplicação e atualização:
- A tabela `items` tem uma constraint única em (category, item_hash).
- Re-inserções incrementam `count` e atualizam `last_seen`.

Uso básico:
python3 tools/ingest/ingest_categorize.py --source raw_data/leak.csv --db data/leaks.db --hash-salt my-secret

"""
import argparse
import csv
import hashlib
import json
import os
import sqlite3
import sys
import time
from urllib.request import Request, urlopen
import shutil


def download_to_file(url, dest_path):
    req = Request(url, headers={"User-Agent": "OlhoDeDeus-Ingest/1.0"})
    with urlopen(req) as resp, open(dest_path, "wb") as out:
        shutil.copyfileobj(resp, out)


def sha256_hex(value: str, salt: str = "") -> str:
    if value is None:
        value = ""
    h = hashlib.sha256()
    h.update(salt.encode("utf-8"))
    h.update(value.encode("utf-8", errors="ignore"))
    return h.hexdigest()


def ensure_db(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode = WAL;")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS items(
            id INTEGER PRIMARY KEY,
            category TEXT,
            item_hash TEXT,
            plaintext_sample TEXT,
            source TEXT,
            service TEXT,
            count INTEGER DEFAULT 1,
            metadata TEXT,
            first_seen INTEGER,
            last_seen INTEGER,
            UNIQUE(category,item_hash)
        )
        """
    )
    conn.commit()
    return conn


def insert_or_update(conn, category, item_hash, plaintext_sample, source, service, metadata):
    now = int(time.time())
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO items(category,item_hash,plaintext_sample,source,service,metadata,first_seen,last_seen) VALUES (?,?,?,?,?,?,?,?)",
            (category, item_hash, plaintext_sample, source, service, json.dumps(metadata or {}), now, now),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # already exists -> update count and last_seen and maybe metadata
        cur.execute("SELECT count,metadata FROM items WHERE category=? AND item_hash=?", (category, item_hash))
        row = cur.fetchone()
        if row:
            existing_count, existing_meta_json = row
            existing_meta = json.loads(existing_meta_json or "{}")
            # merge a bit of metadata
            existing_meta.update(metadata or {})
            cur.execute(
                "UPDATE items SET count=?, last_seen=?, metadata=? WHERE category=? AND item_hash=?",
                (existing_count + 1, now, json.dumps(existing_meta), category, item_hash),
            )
            conn.commit()
        return False


def parse_csv_and_ingest(path, conn, salt, allow_plaintext, default_category=None):
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # Heurística simples: tente extrair campos conhecidos
            service = row.get("service") or row.get("site") or row.get("domain") or ""
            email = row.get("email") or row.get("e-mail") or row.get("username") or ""
            password = row.get("password") or row.get("pass") or ""
            name = row.get("name") or row.get("fullname") or ""
            cpf = row.get("cpf") or row.get("document") or ""

            # Determine category: prefer provided, else service, else based on email domain
            category = default_category or (service if service else (email.split("@")[-1] if "@" in email else "unknown"))

            # Choose an item to hash as unique key: prefer email, else cpf, else name, else password hash
            if email:
                key_material = email.lower().strip()
                sample = email
            elif cpf:
                key_material = cpf.strip()
                sample = cpf
            elif name:
                key_material = name.strip()
                sample = name
            else:
                key_material = password
                sample = "(password-hidden)"

            item_hash = sha256_hex(key_material, salt)

            plaintext_sample = None
            if allow_plaintext:
                # WARNING: storing plaintext is dangerous — explicit flag required
                plaintext_sample = sample

            metadata = {"has_password": bool(password), "fields": list(k for k in row.keys() if row.get(k))}
            insert_or_update(conn, category, item_hash, plaintext_sample, os.path.basename(path), service, metadata)


def ingest_source(source, db_path, salt, allow_plaintext, default_category=None):
    conn = ensure_db(db_path)

    if source.startswith("http://") or source.startswith("https://"):
        tmp = db_path + ".tmp_src"
        print(f"Baixando {source} para {tmp} ...")
        download_to_file(source, tmp)
        source_path = tmp
    else:
        source_path = source

    # Try to detect CSV by extension or content
    lowered = source_path.lower()
    try:
        if lowered.endswith(".csv") or lowered.endswith(".txt"):
            parse_csv_and_ingest(source_path, conn, salt, allow_plaintext, default_category)
        else:
            # Fallback: try CSV
            parse_csv_and_ingest(source_path, conn, salt, allow_plaintext, default_category)
    finally:
        conn.close()
        if source.startswith("http://") or source.startswith("https://"):
            try:
                os.remove(source_path)
            except Exception:
                pass


def main():
    p = argparse.ArgumentParser(description="Ingesta categorizada segura para DB de estudos")
    p.add_argument("--source", required=True, help="Arquivo local ou URL para ingestão (CSV ou similar)")
    p.add_argument("--db", default="data/leaks.db", help="Caminho para DB SQLite de saída")
    p.add_argument("--hash-salt", default="", help="Salt para hashing determinístico (recomendado)")
    p.add_argument("--allow-plaintext", action="store_true", help="Permite armazenar plaintext em DB (risco) - use com cuidado")
    p.add_argument("--category", default=None, help="Força a categoria para todos os itens deste source")
    args = p.parse_args()

    if args.allow_plaintext:
        print("AVISO: você habilitou armazenamento de plaintext. Isso é arriscado. Continue por sua conta.")
        print("Recomendado: use um DB encriptado e não commite o arquivo no repositório.")

    ingest_source(args.source, args.db, args.hash_salt, args.allow_plaintext, args.category)


if __name__ == "__main__":
    main()
