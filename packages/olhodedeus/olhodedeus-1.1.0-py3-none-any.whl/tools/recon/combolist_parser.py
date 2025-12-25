#!/usr/bin/env python3
"""
combolist_parser.py

Parser e buscador de combolists (email:password)
Suporta múltiplos formatos e busca eficiente.
"""
import os
import re
import json
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Generator
from pathlib import Path


class CombolistParser:
    """Parser de combolists com múltiplos formatos."""
    
    # Padrões de formatos comuns
    PATTERNS = {
        "email:pass": re.compile(r'^([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)[:\|;](.+)$'),
        "user:pass": re.compile(r'^([a-zA-Z0-9_.+-]+)[:\|;](.+)$'),
        "url:email:pass": re.compile(r'^(https?://[^\s:]+)[:\|;]([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)[:\|;](.+)$'),
        "email:hash": re.compile(r'^([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)[:\|;]([a-fA-F0-9]{32,128})$'),
    }
    
    def __init__(self, db_path: str = "data/combolists.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializa banco de dados."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                username TEXT,
                password TEXT,
                password_hash TEXT,
                url TEXT,
                source_file TEXT,
                line_number INTEGER,
                imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(email, password, url)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_email ON entries(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_username ON entries(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_domain ON entries(email)')
        
        conn.commit()
        conn.close()
    
    def parse_line(self, line: str) -> Optional[Dict]:
        """Parse uma linha de combolist."""
        line = line.strip()
        if not line or line.startswith('#'):
            return None
        
        # Tentar cada padrão
        for format_name, pattern in self.PATTERNS.items():
            match = pattern.match(line)
            if match:
                groups = match.groups()
                
                if format_name == "url:email:pass":
                    return {
                        "url": groups[0],
                        "email": groups[1],
                        "password": groups[2],
                        "format": format_name
                    }
                elif format_name == "email:pass":
                    return {
                        "email": groups[0],
                        "password": groups[1],
                        "format": format_name
                    }
                elif format_name == "email:hash":
                    return {
                        "email": groups[0],
                        "password_hash": groups[1],
                        "format": format_name
                    }
                elif format_name == "user:pass":
                    return {
                        "username": groups[0],
                        "password": groups[1],
                        "format": format_name
                    }
        
        return None
    
    def import_file(self, filepath: str, batch_size: int = 10000) -> Dict:
        """Importa combolist para o banco."""
        stats = {"total": 0, "imported": 0, "errors": 0, "duplicates": 0}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        source = os.path.basename(filepath)
        batch = []
        
        print(f"📂 Importando: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    stats["total"] += 1
                    
                    parsed = self.parse_line(line)
                    if parsed:
                        batch.append((
                            parsed.get("email"),
                            parsed.get("username"),
                            parsed.get("password"),
                            parsed.get("password_hash"),
                            parsed.get("url"),
                            source,
                            line_num
                        ))
                        
                        if len(batch) >= batch_size:
                            imported, dupes = self._insert_batch(cursor, batch)
                            stats["imported"] += imported
                            stats["duplicates"] += dupes
                            batch = []
                            print(f"\r   Processadas: {stats['total']:,} linhas", end="", flush=True)
                    else:
                        stats["errors"] += 1
            
            # Inserir batch restante
            if batch:
                imported, dupes = self._insert_batch(cursor, batch)
                stats["imported"] += imported
                stats["duplicates"] += dupes
            
            conn.commit()
            print(f"\n✅ Importação concluída!")
            
        except Exception as e:
            stats["error"] = str(e)
            print(f"\n❌ Erro: {e}")
        finally:
            conn.close()
        
        return stats
    
    def _insert_batch(self, cursor, batch: List) -> tuple:
        """Insere batch no banco."""
        imported = 0
        duplicates = 0
        
        for entry in batch:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO entries 
                    (email, username, password, password_hash, url, source_file, line_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', entry)
                if cursor.rowcount > 0:
                    imported += 1
                else:
                    duplicates += 1
            except Exception:
                duplicates += 1
        
        return imported, duplicates
    
    def search_email(self, email: str, exact: bool = True) -> List[Dict]:
        """Busca por email."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if exact:
            cursor.execute(
                'SELECT email, password, url, source_file FROM entries WHERE email = ?',
                (email,)
            )
        else:
            cursor.execute(
                'SELECT email, password, url, source_file FROM entries WHERE email LIKE ?',
                (f'%{email}%',)
            )
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "email": row[0],
                "password": row[1],
                "url": row[2],
                "source": row[3]
            })
        
        conn.close()
        return results
    
    def search_domain(self, domain: str) -> List[Dict]:
        """Busca por domínio."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT email, password, url, source_file FROM entries WHERE email LIKE ?',
            (f'%@{domain}',)
        )
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "email": row[0],
                "password": row[1],
                "url": row[2],
                "source": row[3]
            })
        
        conn.close()
        return results
    
    def search_password(self, password: str) -> List[Dict]:
        """Busca por senha (encontrar reutilização)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT email, password, url, source_file FROM entries WHERE password = ?',
            (password,)
        )
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "email": row[0],
                "password": row[1],
                "url": row[2],
                "source": row[3]
            })
        
        conn.close()
        return results
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do banco."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM entries')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT email) FROM entries WHERE email IS NOT NULL')
        unique_emails = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT source_file) FROM entries')
        sources = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT source_file, COUNT(*) as cnt 
            FROM entries 
            GROUP BY source_file 
            ORDER BY cnt DESC 
            LIMIT 10
        ''')
        top_sources = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_entries": total,
            "unique_emails": unique_emails,
            "source_files": sources,
            "top_sources": top_sources
        }


def interactive_menu():
    """Menu interativo do parser."""
    parser = CombolistParser()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        stats = parser.get_stats()
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║              📋 COMBOLIST PARSER                             ║
╠══════════════════════════════════════════════════════════════╣
║  Entries: {stats['total_entries']:,}  |  Emails únicos: {stats['unique_emails']:,}          
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 📥 Importar Combolist (arquivo)                         ║
║  [2] 📂 Importar pasta inteira                               ║
║  [3] 🔍 Buscar por EMAIL                                     ║
║  [4] 🌐 Buscar por DOMÍNIO                                   ║
║  [5] 🔐 Buscar por SENHA                                     ║
║  [6] 📊 Ver estatísticas                                     ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            filepath = input("\n📂 Caminho do arquivo: ").strip()
            if os.path.exists(filepath):
                stats = parser.import_file(filepath)
                print(f"\n📊 Resultado:")
                print(f"   Total: {stats['total']:,}")
                print(f"   Importados: {stats['imported']:,}")
                print(f"   Duplicados: {stats['duplicates']:,}")
                print(f"   Erros: {stats['errors']:,}")
            else:
                print("❌ Arquivo não encontrado!")
            input("\nPressione Enter...")
        
        elif choice == '2':
            folder = input("\n📂 Caminho da pasta: ").strip()
            if os.path.isdir(folder):
                for f in os.listdir(folder):
                    if f.endswith(('.txt', '.csv', '.combo')):
                        filepath = os.path.join(folder, f)
                        parser.import_file(filepath)
            else:
                print("❌ Pasta não encontrada!")
            input("\nPressione Enter...")
        
        elif choice == '3':
            email = input("\n📧 Email para buscar: ").strip()
            if email:
                results = parser.search_email(email, exact=False)
                print(f"\n🔍 {len(results)} resultado(s):\n")
                for r in results[:50]:
                    pwd = r['password'][:20] + "..." if len(r['password']) > 20 else r['password']
                    print(f"  {r['email']} : {pwd}")
            input("\nPressione Enter...")
        
        elif choice == '4':
            domain = input("\n🌐 Domínio para buscar: ").strip()
            if domain:
                results = parser.search_domain(domain)
                print(f"\n🔍 {len(results)} resultado(s):\n")
                for r in results[:50]:
                    pwd = r['password'][:20] + "..." if len(r['password']) > 20 else r['password']
                    print(f"  {r['email']} : {pwd}")
            input("\nPressione Enter...")
        
        elif choice == '5':
            password = input("\n🔐 Senha para buscar: ").strip()
            if password:
                results = parser.search_password(password)
                print(f"\n🔍 {len(results)} conta(s) usando esta senha:\n")
                for r in results[:50]:
                    print(f"  {r['email']}")
            input("\nPressione Enter...")
        
        elif choice == '6':
            stats = parser.get_stats()
            print(f"\n📊 ESTATÍSTICAS:\n")
            print(f"  Total de entries: {stats['total_entries']:,}")
            print(f"  Emails únicos: {stats['unique_emails']:,}")
            print(f"  Arquivos fonte: {stats['source_files']}")
            print(f"\n  Top fontes:")
            for src, cnt in stats['top_sources']:
                print(f"    {src}: {cnt:,}")
            input("\nPressione Enter...")
        
        elif choice == '0':
            break


if __name__ == '__main__':
    interactive_menu()
