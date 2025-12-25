#!/usr/bin/env python3
"""
search.py

Consulta o DB criado por `ingest_categorize.py`.
Também busca em arquivos CSV extraídos e wordlists locais.

Exemplos:
python3 tools/ingest/search.py --db data/leaks.db --category netflix --limit 20
python3 tools/ingest/search.py --db data/leaks.db --service gmail.com --limit 50
python3 tools/ingest/search.py --email user@example.com
python3 tools/ingest/search.py --password "senha123"
"""
import argparse
import sqlite3
import os
import json
import csv
import glob
from typing import List, Dict, Optional, Any


def partial(hashstr: str, n: int = 8) -> str:
    """Mostra hash parcial para privacidade."""
    if not hashstr:
        return ""
    return hashstr[:n] + "..." + hashstr[-4:]


def mask_sensitive(text: str, show_chars: int = 3) -> str:
    """Mascara texto sensível mostrando apenas alguns caracteres."""
    if not text or len(text) <= show_chars:
        return text
    return text[:show_chars] + "*" * (len(text) - show_chars)


def search_db(db_path: str, category: str = None, service: str = None, 
              email: str = None, limit: int = 50) -> List[Dict]:
    """Busca no banco de dados SQLite."""
    results = []
    
    if not os.path.exists(db_path):
        return results
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    q = "SELECT category, item_hash, plaintext_sample, service, count, metadata, first_seen, last_seen FROM items"
    conds = []
    params = []
    
    if category:
        conds.append("category LIKE ?")
        params.append(f"%{category}%")
    if service:
        conds.append("service LIKE ?")
        params.append(f"%{service}%")
    if email:
        conds.append("(plaintext_sample LIKE ? OR metadata LIKE ?)")
        params.extend([f"%{email}%", f"%{email}%"])
    
    if conds:
        q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY count DESC LIMIT ?"
    params.append(limit)
    
    cur.execute(q, params)
    rows = cur.fetchall()
    
    for r in rows:
        category, item_hash, plaintext, service, count, metadata_json, first_seen, last_seen = r
        metadata = json.loads(metadata_json or "{}")
        results.append({
            'source': 'database',
            'category': category,
            'service': service,
            'count': count,
            'hash': item_hash,
            'plaintext': plaintext,
            'metadata': metadata,
            'first_seen': first_seen,
            'last_seen': last_seen
        })
    
    conn.close()
    return results


def search_csv_files(search_term: str, field: str = 'email', 
                     data_dir: str = 'raw_data', limit: int = 50) -> List[Dict]:
    """Busca em arquivos CSV extraídos."""
    results = []
    
    # Procurar em todos os CSVs
    csv_patterns = [
        os.path.join(data_dir, '**', '*_extracted.csv'),
        os.path.join(data_dir, 'processed', '*.csv'),
    ]
    
    csv_files = []
    for pattern in csv_patterns:
        csv_files.extend(glob.glob(pattern, recursive=True))
    
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Verificar campo específico ou todos
                    match = False
                    if field and field in row:
                        if search_term.lower() in str(row[field]).lower():
                            match = True
                    else:
                        # Buscar em todos os campos
                        for val in row.values():
                            if search_term.lower() in str(val).lower():
                                match = True
                                break
                    
                    if match:
                        results.append({
                            'source': 'csv',
                            'file': os.path.basename(csv_file),
                            'email': row.get('email', ''),
                            'password': mask_sensitive(row.get('password', '')),
                            'cpf': mask_sensitive(row.get('cpf', '')),
                            'name': row.get('name', ''),
                            'raw': row.get('raw', '')[:100]
                        })
                        
                        if len(results) >= limit:
                            return results
        except Exception as e:
            continue
    
    return results


def search_wordlist(password: str, wordlist_dir: str = 'raw_data/wordlists') -> Dict:
    """Verifica se uma senha está em wordlists locais."""
    result = {
        'found': False,
        'in_files': [],
        'total_checked': 0
    }
    
    if not os.path.exists(wordlist_dir):
        return result
    
    wordlists = glob.glob(os.path.join(wordlist_dir, '*.txt'))
    
    for wl in wordlists:
        try:
            with open(wl, 'r', encoding='utf-8', errors='ignore') as f:
                result['total_checked'] += 1
                for line in f:
                    if line.strip() == password:
                        result['found'] = True
                        result['in_files'].append(os.path.basename(wl))
                        break
        except Exception:
            continue
    
    return result


def print_results(results: List[Dict], show_sensitive: bool = False):
    """Exibe resultados formatados."""
    if not results:
        print("❌ Nenhum resultado encontrado.")
        return
    
    print(f"\n✅ Encontrados {len(results)} resultados:\n")
    
    for i, r in enumerate(results, 1):
        source = r.get('source', 'unknown')
        
        if source == 'database':
            print(f"[{i}] 📊 DB: [{r['category']}] service={r['service'] or '-'}")
            print(f"    Count: {r['count']} | Hash: {partial(r['hash'])}")
            if r.get('plaintext'):
                print(f"    Sample: {r['plaintext'][:50]}...")
        
        elif source == 'csv':
            print(f"[{i}] 📄 CSV: {r['file']}")
            if r.get('email'):
                print(f"    Email: {r['email']}")
            if r.get('password'):
                pwd = r['password'] if show_sensitive else mask_sensitive(r['password'])
                print(f"    Password: {pwd}")
            if r.get('name'):
                print(f"    Name: {r['name']}")
        
        print()


def interactive_search():
    """Menu interativo de busca."""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║              🔍 BUSCA LOCAL DE DADOS                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] Buscar por EMAIL                                        ║
║  [2] Buscar por DOMÍNIO/SERVIÇO                              ║
║  [3] Verificar SENHA em wordlists locais                     ║
║  [4] Buscar por CATEGORIA                                    ║
║  [5] Busca livre (todos os campos)                           ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            email = input("\nDigite o email: ").strip()
            if email:
                print("\n🔍 Buscando...")
                # Buscar no DB
                db_results = search_db('data/leaks.db', email=email)
                # Buscar nos CSVs
                csv_results = search_csv_files(email, 'email')
                all_results = db_results + csv_results
                print_results(all_results)
            input("\nPressione Enter para continuar...")
        
        elif choice == '2':
            domain = input("\nDigite o domínio (ex: gmail.com): ").strip()
            if domain:
                print("\n🔍 Buscando...")
                db_results = search_db('data/leaks.db', service=domain)
                csv_results = search_csv_files(domain)
                all_results = db_results + csv_results
                print_results(all_results)
            input("\nPressione Enter para continuar...")
        
        elif choice == '3':
            password = input("\nDigite a senha para verificar: ").strip()
            if password:
                print("\n🔍 Verificando em wordlists locais...")
                result = search_wordlist(password)
                if result['found']:
                    print(f"⚠️  SENHA ENCONTRADA em: {', '.join(result['in_files'])}")
                else:
                    print(f"✅ Senha não encontrada em {result['total_checked']} wordlists locais")
                print("\n💡 Dica: Use também a verificação HIBP online para mais abrangência.")
            input("\nPressione Enter para continuar...")
        
        elif choice == '4':
            category = input("\nDigite a categoria (ex: netflix, spotify): ").strip()
            if category:
                print("\n🔍 Buscando...")
                results = search_db('data/leaks.db', category=category)
                print_results(results)
            input("\nPressione Enter para continuar...")
        
        elif choice == '5':
            termo = input("\nDigite o termo de busca: ").strip()
            if termo:
                print("\n🔍 Buscando...")
                db_results = search_db('data/leaks.db', category=termo)
                csv_results = search_csv_files(termo)
                all_results = db_results + csv_results
                print_results(all_results)
            input("\nPressione Enter para continuar...")
        
        elif choice == '0':
            break


def export_results(results: List[Dict], output_path: str, format: str = 'json') -> bool:
    """
    Exporta resultados para arquivo.
    
    Args:
        results: Lista de resultados
        output_path: Caminho do arquivo de saída
        format: 'json' ou 'csv'
        
    Returns:
        True se exportou com sucesso
    """
    if not results:
        print("❌ Nenhum resultado para exportar.")
        return False
    
    try:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        if format.lower() == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        elif format.lower() == 'csv':
            # Determinar todas as colunas
            all_keys = set()
            for r in results:
                all_keys.update(r.keys())
            
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
                writer.writeheader()
                for r in results:
                    # Converter dicts aninhados para string
                    row = {}
                    for k, v in r.items():
                        if isinstance(v, (dict, list)):
                            row[k] = json.dumps(v, ensure_ascii=False)
                        else:
                            row[k] = v
                    writer.writerow(row)
        
        print(f"✅ Exportado {len(results)} resultados para: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao exportar: {e}")
        return False


def main():
    p = argparse.ArgumentParser(description="Procurar dados no DB e arquivos locais")
    p.add_argument("--db", default="data/leaks.db", help="Caminho para DB SQLite")
    p.add_argument("--category", help="Categoria para filtrar")
    p.add_argument("--service", help="Filtro por service/domain")
    p.add_argument("--email", help="Buscar por email específico")
    p.add_argument("--password", help="Verificar senha em wordlists")
    p.add_argument("--limit", type=int, default=50, help="Máximo de resultados")
    p.add_argument("--interactive", "-i", action="store_true", help="Modo interativo")
    p.add_argument("--export", help="Exportar resultados para arquivo (JSON ou CSV)")
    p.add_argument("--format", choices=['json', 'csv'], default='json', help="Formato de exportação")
    args = p.parse_args()

    # Modo interativo
    if args.interactive:
        interactive_search()
        return

    # Verificar senha em wordlists
    if args.password:
        result = search_wordlist(args.password)
        if result['found']:
            print(f"⚠️  SENHA ENCONTRADA em: {', '.join(result['in_files'])}")
        else:
            print(f"✅ Senha não encontrada em {result['total_checked']} wordlists")
        return

    # Busca geral
    results = search_db(args.db, args.category, args.service, args.email, args.limit)
    
    if args.email:
        csv_results = search_csv_files(args.email, 'email', limit=args.limit)
        results.extend(csv_results)
    
    # Exportar se solicitado
    if args.export:
        export_results(results, args.export, args.format)
    else:
        print_results(results)


if __name__ == "__main__":
    main()
