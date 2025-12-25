#!/usr/bin/env python3
"""
search.py

Consulta o DB criado por `ingest_categorize.py`.

Exemplos:
python3 tools/ingest/search.py --db data/leaks.db --category netflix --limit 20
python3 tools/ingest/search.py --db data/leaks.db --service gmail.com --limit 50
"""
import argparse
import sqlite3
import os
import json


def partial(hashstr, n=8):
    if not hashstr:
        return ""
    return hashstr[:n] + "..." + hashstr[-4:]


def search(db_path, category=None, service=None, limit=50):
    if not os.path.exists(db_path):
        print("DB não encontrado:", db_path)
        return
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    q = "SELECT category,item_hash,plaintext_sample,service,count,metadata,first_seen,last_seen FROM items"
    conds = []
    params = []
    if category:
        conds.append("category LIKE ?")
        params.append(f"%{category}%")
    if service:
        conds.append("service LIKE ?")
        params.append(f"%{service}%")
    if conds:
        q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY count DESC LIMIT ?"
    params.append(limit)
    cur.execute(q, params)
    rows = cur.fetchall()
    for r in rows:
        category, item_hash, plaintext, service, count, metadata_json, first_seen, last_seen = r
        metadata = json.loads(metadata_json or "{}")
        print(f"[{category}] service={service or '-'} count={count} hash={partial(item_hash)} fields={metadata.get('fields')}")
        if plaintext:
            print(f"  plaintext_sample: {plaintext}")
    conn.close()


def main():
    p = argparse.ArgumentParser(description="Procurar items no DB de ingestão")
    p.add_argument("--db", default="data/leaks.db", help="Caminho para DB SQLite")
    p.add_argument("--category", help="Categoria para filtrar (substring)")
    p.add_argument("--service", help="Filtro por service/domain (substring)")
    p.add_argument("--limit", type=int, default=50, help="Máximo de resultados")
    args = p.parse_args()

    search(args.db, args.category, args.service, args.limit)


if __name__ == "__main__":
    main()
