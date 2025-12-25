#!/usr/bin/env python3
"""
analyze.py

Ferramenta simples para consultar o DB criado pelo `ingest_hibp.py`.
Mostra top N hashes por ocorrencia e estatísticas básicas.

Não mostra senhas em plaintext. Trabalha apenas com hashes e contagens.
"""
import argparse
import sqlite3
import os


def top_n(db_path, n=20):
    if not os.path.exists(db_path):
        print("DB não encontrado:", db_path)
        return
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT count FROM passwords ORDER BY count DESC LIMIT ?", (n,))
    rows = cur.fetchall()
    total = 0
    for i, (c,) in enumerate(rows, start=1):
        print(f"#{i}: {c} ocorrências (hash oculto)")
        total += c
    print(f"\nSoma das top {n}: {total}")
    conn.close()


def summary(db_path):
    if not os.path.exists(db_path):
        print("DB não encontrado:", db_path)
        return
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), SUM(count) FROM passwords")
    rows = cur.fetchone()
    print(f"Linhas (hashes) no DB: {rows[0]}")
    print(f"Total de ocorrências acumuladas: {rows[1]}")
    conn.close()


def main():
    p = argparse.ArgumentParser(description="Analisar DB de senhas vazadas (hashes)")
    p.add_argument("--db", default="data/passwords.db", help="Caminho para o DB SQLite")
    p.add_argument("--top", type=int, default=20, help="Exibir top N hashes por contagem")
    p.add_argument("--summary", action="store_true", help="Mostrar sumário do DB")
    args = p.parse_args()

    if args.summary:
        summary(args.db)
    top_n(args.db, args.top)


if __name__ == "__main__":
    main()
