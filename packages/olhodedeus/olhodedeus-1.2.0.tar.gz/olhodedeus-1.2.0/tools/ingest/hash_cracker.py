#!/usr/bin/env python3
"""
hash_cracker.py

Ferramenta para crackear hashes usando wordlists locais.
Suporta MD5, SHA1, SHA256 e NTLM.

Uso:
  python hash_cracker.py --hash "5f4dcc3b5aa765d61d8327deb882cf99"
  python hash_cracker.py --hash-file hashes.txt --wordlist wordlist.txt
  python hash_cracker.py --interactive
"""
import os
import sys
import argparse
import hashlib
import binascii
import glob
import time
from typing import Optional, List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed


class HashCracker:
    """Cracker de hashes usando wordlists."""
    
    HASH_TYPES = {
        'md5': (32, hashlib.md5),
        'sha1': (40, hashlib.sha1),
        'sha256': (64, hashlib.sha256),
        'sha512': (128, hashlib.sha512),
        'ntlm': (32, None),  # NTLM precisa de tratamento especial
    }
    
    def __init__(self, wordlist_dir: str = 'raw_data/wordlists'):
        self.wordlist_dir = wordlist_dir
        self.stats = {
            'hashes_tested': 0,
            'passwords_tried': 0,
            'cracked': 0,
            'time_elapsed': 0
        }
    
    def detect_hash_type(self, hash_str: str) -> List[str]:
        """Detecta possíveis tipos de hash baseado no tamanho."""
        hash_str = hash_str.strip().lower()
        length = len(hash_str)
        
        possible = []
        for name, (expected_len, _) in self.HASH_TYPES.items():
            if length == expected_len:
                possible.append(name)
        
        return possible if possible else ['unknown']
    
    def hash_password(self, password: str, hash_type: str) -> str:
        """Gera hash de uma senha."""
        if hash_type == 'ntlm':
            # NTLM = MD4(UTF-16LE(password))
            try:
                import hashlib
                # Python não tem MD4 nativo, usar fallback
                return hashlib.new('md4', password.encode('utf-16-le')).hexdigest()
            except ValueError:
                # MD4 não disponível
                return ''
        
        if hash_type not in self.HASH_TYPES:
            return ''
        
        _, hash_func = self.HASH_TYPES[hash_type]
        if hash_func:
            return hash_func(password.encode('utf-8')).hexdigest()
        return ''
    
    def crack_single(self, target_hash: str, wordlist_path: str, 
                     hash_type: str = None) -> Optional[str]:
        """
        Tenta crackear um único hash usando uma wordlist.
        
        Args:
            target_hash: Hash para crackear
            wordlist_path: Caminho para wordlist
            hash_type: Tipo de hash (md5, sha1, etc.) ou None para auto-detectar
            
        Returns:
            Senha encontrada ou None
        """
        target_hash = target_hash.strip().lower()
        
        # Auto-detectar tipo de hash
        if not hash_type:
            possible_types = self.detect_hash_type(target_hash)
            if 'unknown' in possible_types:
                print(f"⚠️  Tipo de hash desconhecido para: {target_hash[:16]}...")
                return None
            hash_type = possible_types[0]  # Usar primeiro tipo possível
        
        if not os.path.exists(wordlist_path):
            print(f"❌ Wordlist não encontrada: {wordlist_path}")
            return None
        
        try:
            with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    password = line.strip()
                    if not password:
                        continue
                    
                    self.stats['passwords_tried'] += 1
                    
                    # Tentar todos os tipos possíveis
                    for ht in self.detect_hash_type(target_hash):
                        computed = self.hash_password(password, ht)
                        if computed == target_hash:
                            self.stats['cracked'] += 1
                            return password
        except Exception as e:
            print(f"❌ Erro ao ler wordlist: {e}")
        
        return None
    
    def crack_with_all_wordlists(self, target_hash: str, 
                                  hash_type: str = None) -> Optional[str]:
        """Tenta crackear usando todas as wordlists disponíveis."""
        wordlists = self.get_available_wordlists()
        
        if not wordlists:
            print("❌ Nenhuma wordlist encontrada.")
            print(f"   Diretório: {self.wordlist_dir}")
            print("   Use o menu de Scraping para baixar wordlists.")
            return None
        
        print(f"🔍 Testando contra {len(wordlists)} wordlists...")
        
        for i, wl in enumerate(wordlists, 1):
            wl_name = os.path.basename(wl)
            print(f"   [{i}/{len(wordlists)}] {wl_name}...", end=' ', flush=True)
            
            result = self.crack_single(target_hash, wl, hash_type)
            if result:
                print(f"✅ ENCONTRADO!")
                return result
            print("❌")
        
        return None
    
    def get_available_wordlists(self) -> List[str]:
        """Lista wordlists disponíveis."""
        if not os.path.exists(self.wordlist_dir):
            return []
        
        patterns = ['*.txt', '*.lst', '*.dic']
        wordlists = []
        for pattern in patterns:
            wordlists.extend(glob.glob(os.path.join(self.wordlist_dir, pattern)))
        
        # Ordenar por tamanho (menores primeiro para resultados mais rápidos)
        wordlists.sort(key=lambda x: os.path.getsize(x))
        return wordlists
    
    def crack_batch(self, hashes: List[str], wordlist_path: str = None,
                    hash_type: str = None) -> Dict[str, str]:
        """
        Crackeia múltiplos hashes.
        
        Args:
            hashes: Lista de hashes
            wordlist_path: Wordlist específica ou None para todas
            hash_type: Tipo de hash ou None para auto-detectar
            
        Returns:
            Dict de {hash: senha} para os crackeados
        """
        results = {}
        total = len(hashes)
        
        print(f"\n🔓 Crackeando {total} hashes...\n")
        
        start_time = time.time()
        
        for i, h in enumerate(hashes, 1):
            h = h.strip()
            if not h:
                continue
            
            self.stats['hashes_tested'] += 1
            print(f"[{i}/{total}] {h[:16]}...", end=' ')
            
            if wordlist_path:
                result = self.crack_single(h, wordlist_path, hash_type)
            else:
                result = self.crack_with_all_wordlists(h, hash_type)
            
            if result:
                results[h] = result
                print(f"✅ {result}")
            else:
                print("❌ Não encontrado")
        
        self.stats['time_elapsed'] = time.time() - start_time
        
        return results
    
    def print_stats(self):
        """Exibe estatísticas do cracking."""
        print(f"\n📊 Estatísticas:")
        print(f"   Hashes testados: {self.stats['hashes_tested']}")
        print(f"   Senhas tentadas: {self.stats['passwords_tried']:,}")
        print(f"   Crackeados: {self.stats['cracked']}")
        print(f"   Tempo: {self.stats['time_elapsed']:.2f}s")
        if self.stats['time_elapsed'] > 0:
            rate = self.stats['passwords_tried'] / self.stats['time_elapsed']
            print(f"   Velocidade: {rate:,.0f} senhas/segundo")


def interactive_menu():
    """Menu interativo do hash cracker."""
    cracker = HashCracker()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║              🔓 HASH CRACKER                                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] Crackear HASH único                                     ║
║  [2] Crackear arquivo de hashes                              ║
║  [3] Identificar tipo de hash                                ║
║  [4] Gerar hash de senha                                     ║
║  [5] Listar wordlists disponíveis                            ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            print("\n=== Crackear Hash Único ===\n")
            target = input("Digite o hash: ").strip()
            if target:
                types = cracker.detect_hash_type(target)
                print(f"Tipo detectado: {', '.join(types)}")
                
                print("\n🔍 Buscando senha...")
                start = time.time()
                result = cracker.crack_with_all_wordlists(target)
                elapsed = time.time() - start
                
                if result:
                    print(f"\n✅ SENHA ENCONTRADA: {result}")
                else:
                    print(f"\n❌ Senha não encontrada nas wordlists locais.")
                    print("   💡 Dica: Baixe mais wordlists ou use HIBP online.")
                
                print(f"\n⏱️  Tempo: {elapsed:.2f}s")
            input("\nPressione Enter para continuar...")
        
        elif choice == '2':
            print("\n=== Crackear Arquivo de Hashes ===\n")
            filepath = input("Caminho do arquivo (um hash por linha): ").strip()
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    hashes = [line.strip() for line in f if line.strip()]
                
                results = cracker.crack_batch(hashes)
                
                print(f"\n=== RESULTADOS ===")
                print(f"Crackeados: {len(results)}/{len(hashes)}")
                
                if results:
                    print("\nSenhas encontradas:")
                    for h, pwd in results.items():
                        print(f"  {h[:16]}... = {pwd}")
                
                cracker.print_stats()
                
                # Salvar resultados
                if results:
                    save = input("\nSalvar resultados? (s/n): ").strip().lower()
                    if save == 's':
                        out_file = filepath + '.cracked.txt'
                        with open(out_file, 'w') as f:
                            for h, pwd in results.items():
                                f.write(f"{h}:{pwd}\n")
                        print(f"✅ Salvo em: {out_file}")
            else:
                print(f"❌ Arquivo não encontrado: {filepath}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '3':
            print("\n=== Identificar Tipo de Hash ===\n")
            target = input("Digite o hash: ").strip()
            if target:
                types = cracker.detect_hash_type(target)
                print(f"\nTamanho: {len(target)} caracteres")
                print(f"Possíveis tipos: {', '.join(types)}")
                
                # Mostrar exemplos
                print("\n📋 Referência de tamanhos:")
                print("   MD5:    32 caracteres")
                print("   SHA1:   40 caracteres")
                print("   SHA256: 64 caracteres")
                print("   SHA512: 128 caracteres")
                print("   NTLM:   32 caracteres")
            input("\nPressione Enter para continuar...")
        
        elif choice == '4':
            print("\n=== Gerar Hash de Senha ===\n")
            password = input("Digite a senha: ").strip()
            if password:
                print(f"\nHashes para '{password}':")
                print(f"  MD5:    {hashlib.md5(password.encode()).hexdigest()}")
                print(f"  SHA1:   {hashlib.sha1(password.encode()).hexdigest()}")
                print(f"  SHA256: {hashlib.sha256(password.encode()).hexdigest()}")
            input("\nPressione Enter para continuar...")
        
        elif choice == '5':
            print("\n=== Wordlists Disponíveis ===\n")
            wordlists = cracker.get_available_wordlists()
            if wordlists:
                total_size = 0
                for wl in wordlists:
                    size = os.path.getsize(wl)
                    total_size += size
                    print(f"  📄 {os.path.basename(wl)} ({size:,} bytes)")
                print(f"\n  Total: {len(wordlists)} arquivos, {total_size:,} bytes")
            else:
                print("  ❌ Nenhuma wordlist encontrada.")
                print(f"     Diretório: {cracker.wordlist_dir}")
                print("     Use o menu de Scraping para baixar.")
            input("\nPressione Enter para continuar...")
        
        elif choice == '0':
            break


def main():
    p = argparse.ArgumentParser(description='Hash Cracker com wordlists')
    p.add_argument('--hash', help='Hash único para crackear')
    p.add_argument('--hash-file', help='Arquivo com hashes (um por linha)')
    p.add_argument('--wordlist', help='Wordlist específica')
    p.add_argument('--wordlist-dir', default='raw_data/wordlists', help='Diretório de wordlists')
    p.add_argument('--type', choices=['md5', 'sha1', 'sha256', 'sha512', 'ntlm'], 
                   help='Tipo de hash (auto-detecta se omitido)')
    p.add_argument('--interactive', '-i', action='store_true', help='Modo interativo')
    args = p.parse_args()

    if args.interactive:
        interactive_menu()
        return

    cracker = HashCracker(args.wordlist_dir)

    if args.hash:
        print(f"🔍 Crackeando: {args.hash[:16]}...")
        types = cracker.detect_hash_type(args.hash)
        print(f"   Tipo detectado: {', '.join(types)}")
        
        if args.wordlist:
            result = cracker.crack_single(args.hash, args.wordlist, args.type)
        else:
            result = cracker.crack_with_all_wordlists(args.hash, args.type)
        
        if result:
            print(f"\n✅ SENHA: {result}")
        else:
            print(f"\n❌ Não encontrado")
        
        cracker.print_stats()

    elif args.hash_file:
        if not os.path.exists(args.hash_file):
            print(f"❌ Arquivo não encontrado: {args.hash_file}")
            return
        
        with open(args.hash_file, 'r') as f:
            hashes = [line.strip() for line in f if line.strip()]
        
        results = cracker.crack_batch(hashes, args.wordlist, args.type)
        
        print(f"\n=== RESULTADOS ===")
        for h, pwd in results.items():
            print(f"{h}:{pwd}")
        
        cracker.print_stats()

    else:
        p.print_help()


if __name__ == '__main__':
    main()
