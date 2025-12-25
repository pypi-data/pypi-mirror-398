#!/usr/bin/env python3
"""
apk_reverse.py

Ferramenta de engenharia reversa para APKs Android.
Decompila, extrai e analisa APKs.
"""
import os
import re
import json
import zipfile
import hashlib
import subprocess
import shutil
import struct
import xml.etree.ElementTree as ET
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from pathlib import Path
import urllib.request


class APKAnalyzer:
    """Analisador básico de APK (sem dependências externas)."""
    
    DANGEROUS_PERMISSIONS = [
        'READ_CONTACTS', 'WRITE_CONTACTS', 'READ_CALL_LOG', 'WRITE_CALL_LOG',
        'READ_CALENDAR', 'WRITE_CALENDAR', 'CAMERA', 'RECORD_AUDIO',
        'READ_PHONE_STATE', 'READ_PHONE_NUMBERS', 'CALL_PHONE', 'ANSWER_PHONE_CALLS',
        'READ_SMS', 'RECEIVE_SMS', 'SEND_SMS', 'RECEIVE_MMS',
        'ACCESS_FINE_LOCATION', 'ACCESS_COARSE_LOCATION', 'ACCESS_BACKGROUND_LOCATION',
        'READ_EXTERNAL_STORAGE', 'WRITE_EXTERNAL_STORAGE', 'MANAGE_EXTERNAL_STORAGE',
        'GET_ACCOUNTS', 'AUTHENTICATE_ACCOUNTS',
        'SYSTEM_ALERT_WINDOW', 'REQUEST_INSTALL_PACKAGES',
        'BIND_ACCESSIBILITY_SERVICE', 'BIND_DEVICE_ADMIN',
        'READ_LOGS', 'DUMP',
    ]
    
    SUSPICIOUS_STRINGS = [
        # URLs suspeitas
        r'http://[^\s"\'<>]+',
        r'https?://\d+\.\d+\.\d+\.\d+',
        # Comandos shell
        r'Runtime\.getRuntime\(\)\.exec',
        r'/system/bin/su',
        r'/system/xbin/su',
        r'Superuser\.apk',
        r'busybox',
        # Crypto/keylogging
        r'KeyLogger',
        r'keylogger',
        r'getClipboard',
        r'ClipboardManager',
        # Reflexão maliciosa
        r'DexClassLoader',
        r'PathClassLoader',
        r'dalvik\.system',
        # Anti-análise
        r'android\.os\.Debug',
        r'isDebuggerConnected',
        r'android/os/Debug',
        # Rede
        r'socket\.',
        r'ServerSocket',
        r'DatagramSocket',
        # SMS/Call
        r'SmsManager',
        r'TelephonyManager',
        r'DevicePolicyManager',
    ]
    
    def __init__(self, tools_dir: str = None):
        self.tools_dir = tools_dir or os.path.join(os.path.dirname(__file__), 'apk_tools')
        self.apktool_path = os.path.join(self.tools_dir, 'apktool.jar')
        self.jadx_path = os.path.join(self.tools_dir, 'jadx', 'bin', 'jadx.bat' if os.name == 'nt' else 'jadx')
        self.dex2jar_path = os.path.join(self.tools_dir, 'dex2jar', 'd2j-dex2jar.bat' if os.name == 'nt' else 'd2j-dex2jar.sh')
    
    def check_tools(self) -> Dict[str, bool]:
        """Verifica ferramentas disponíveis."""
        return {
            'apktool': os.path.exists(self.apktool_path),
            'jadx': os.path.exists(self.jadx_path),
            'dex2jar': os.path.exists(self.dex2jar_path),
            'java': shutil.which('java') is not None,
        }
    
    def download_tools(self) -> Dict[str, str]:
        """Baixa ferramentas necessárias."""
        os.makedirs(self.tools_dir, exist_ok=True)
        results = {}
        
        # APKTool
        if not os.path.exists(self.apktool_path):
            print("📥 Baixando APKTool...")
            try:
                url = "https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar"
                urllib.request.urlretrieve(url, self.apktool_path)
                results['apktool'] = 'downloaded'
            except Exception as e:
                results['apktool'] = f'error: {e}'
        else:
            results['apktool'] = 'exists'
        
        # JADX
        jadx_dir = os.path.join(self.tools_dir, 'jadx')
        if not os.path.exists(self.jadx_path):
            print("📥 Baixando JADX...")
            try:
                url = "https://github.com/skylot/jadx/releases/download/v1.4.7/jadx-1.4.7.zip"
                zip_path = os.path.join(self.tools_dir, 'jadx.zip')
                urllib.request.urlretrieve(url, zip_path)
                
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(jadx_dir)
                os.remove(zip_path)
                
                # Torna executável em Linux/Mac
                if os.name != 'nt':
                    os.chmod(self.jadx_path, 0o755)
                
                results['jadx'] = 'downloaded'
            except Exception as e:
                results['jadx'] = f'error: {e}'
        else:
            results['jadx'] = 'exists'
        
        return results
    
    def get_apk_info(self, apk_path: str) -> Dict:
        """Extrai informações básicas do APK."""
        info = {
            'path': apk_path,
            'name': os.path.basename(apk_path),
            'size': os.path.getsize(apk_path),
            'hashes': {},
            'package': None,
            'version_name': None,
            'version_code': None,
            'min_sdk': None,
            'target_sdk': None,
            'permissions': [],
            'activities': [],
            'services': [],
            'receivers': [],
            'providers': [],
            'files': [],
        }
        
        # Calcula hashes
        with open(apk_path, 'rb') as f:
            data = f.read()
            info['hashes']['md5'] = hashlib.md5(data).hexdigest()
            info['hashes']['sha1'] = hashlib.sha1(data).hexdigest()
            info['hashes']['sha256'] = hashlib.sha256(data).hexdigest()
        
        # Abre como ZIP
        try:
            with zipfile.ZipFile(apk_path, 'r') as z:
                info['files'] = z.namelist()
                
                # Procura AndroidManifest.xml (binário)
                if 'AndroidManifest.xml' in z.namelist():
                    manifest_data = z.read('AndroidManifest.xml')
                    # Parse do manifest binário
                    manifest_info = self._parse_binary_xml(manifest_data)
                    info.update(manifest_info)
                
                # Procura classes.dex
                dex_files = [f for f in z.namelist() if f.endswith('.dex')]
                info['dex_files'] = dex_files
                
                # Procura libs nativas
                so_files = [f for f in z.namelist() if f.endswith('.so')]
                info['native_libs'] = so_files
                
                # Procura assets
                assets = [f for f in z.namelist() if f.startswith('assets/')]
                info['assets'] = assets
                
        except zipfile.BadZipFile:
            info['error'] = 'APK inválido (não é um ZIP válido)'
        
        return info
    
    def _parse_binary_xml(self, data: bytes) -> Dict:
        """Parse básico de AndroidManifest.xml binário."""
        result = {
            'permissions': [],
            'activities': [],
            'services': [],
            'receivers': [],
        }
        
        # Extrai strings do XML binário
        try:
            # Procura por padrões de texto no XML
            text = data.decode('utf-16-le', errors='ignore')
            
            # Package name
            pkg_match = re.search(r'([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+)', text)
            if pkg_match:
                result['package'] = pkg_match.group(1)
            
            # Permissions
            perms = re.findall(r'android\.permission\.([A-Z_]+)', text)
            result['permissions'] = list(set(perms))
            
        except Exception:
            pass
        
        return result
    
    def extract_apk(self, apk_path: str, output_dir: str) -> str:
        """Extrai APK como ZIP."""
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(apk_path, 'r') as z:
                z.extractall(output_dir)
            return output_dir
        except Exception as e:
            return f'error: {e}'
    
    def decompile_apktool(self, apk_path: str, output_dir: str) -> str:
        """Decompila APK usando APKTool."""
        if not os.path.exists(self.apktool_path):
            return 'error: APKTool não encontrado. Use download_tools() primeiro.'
        
        if not shutil.which('java'):
            return 'error: Java não encontrado no PATH.'
        
        try:
            cmd = ['java', '-jar', self.apktool_path, 'd', '-f', apk_path, '-o', output_dir]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return output_dir
            else:
                return f'error: {result.stderr}'
        except subprocess.TimeoutExpired:
            return 'error: Timeout na decompilação'
        except Exception as e:
            return f'error: {e}'
    
    def decompile_jadx(self, apk_path: str, output_dir: str) -> str:
        """Decompila APK para Java usando JADX."""
        if not os.path.exists(self.jadx_path):
            return 'error: JADX não encontrado. Use download_tools() primeiro.'
        
        try:
            cmd = [self.jadx_path, '-d', output_dir, apk_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0 or os.path.exists(output_dir):
                return output_dir
            else:
                return f'error: {result.stderr}'
        except subprocess.TimeoutExpired:
            return 'error: Timeout na decompilação'
        except Exception as e:
            return f'error: {e}'
    
    def extract_strings(self, apk_path: str) -> List[str]:
        """Extrai todas as strings do APK."""
        strings = set()
        
        try:
            with zipfile.ZipFile(apk_path, 'r') as z:
                for name in z.namelist():
                    if name.endswith('.dex'):
                        data = z.read(name)
                        # Extrai strings ASCII/UTF-8
                        ascii_strings = re.findall(rb'[\x20-\x7e]{4,}', data)
                        for s in ascii_strings:
                            try:
                                strings.add(s.decode('utf-8'))
                            except:
                                pass
        except Exception:
            pass
        
        return sorted(strings)
    
    def find_suspicious_strings(self, apk_path: str) -> Dict[str, List[str]]:
        """Encontra strings suspeitas no APK."""
        all_strings = self.extract_strings(apk_path)
        suspicious = {}
        
        for pattern in self.SUSPICIOUS_STRINGS:
            matches = []
            regex = re.compile(pattern, re.IGNORECASE)
            for s in all_strings:
                if regex.search(s):
                    matches.append(s)
            if matches:
                suspicious[pattern] = matches[:10]  # Limita a 10 por padrão
        
        return suspicious
    
    def analyze_permissions(self, permissions: List[str]) -> Dict:
        """Analisa permissões do APK."""
        dangerous = []
        normal = []
        
        for perm in permissions:
            if perm in self.DANGEROUS_PERMISSIONS:
                dangerous.append(perm)
            else:
                normal.append(perm)
        
        risk_level = 'LOW'
        if len(dangerous) > 5:
            risk_level = 'HIGH'
        elif len(dangerous) > 2:
            risk_level = 'MEDIUM'
        
        return {
            'total': len(permissions),
            'dangerous': dangerous,
            'normal': normal,
            'dangerous_count': len(dangerous),
            'risk_level': risk_level,
        }
    
    def full_analysis(self, apk_path: str) -> Dict:
        """Análise completa do APK."""
        print(f"🔍 Analisando: {apk_path}\n")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'basic_info': self.get_apk_info(apk_path),
        }
        
        # Análise de permissões
        perms = result['basic_info'].get('permissions', [])
        result['permission_analysis'] = self.analyze_permissions(perms)
        
        # Strings suspeitas
        print("🔍 Procurando strings suspeitas...")
        result['suspicious_strings'] = self.find_suspicious_strings(apk_path)
        
        # VirusTotal link
        sha256 = result['basic_info']['hashes']['sha256']
        result['virustotal_url'] = f"https://www.virustotal.com/gui/file/{sha256}"
        
        return result


class APKReverseEngineer:
    """Engenharia reversa completa de APK."""
    
    def __init__(self, output_base: str = None):
        self.analyzer = APKAnalyzer()
        self.output_base = output_base or os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'apk_analysis')
        os.makedirs(self.output_base, exist_ok=True)
    
    def setup_tools(self) -> Dict:
        """Configura ferramentas."""
        print("⚙️ Verificando ferramentas...\n")
        
        status = self.analyzer.check_tools()
        
        for tool, available in status.items():
            icon = "✅" if available else "❌"
            print(f"   {icon} {tool}")
        
        if not all(status.values()):
            print("\n📥 Baixando ferramentas faltantes...")
            download_result = self.analyzer.download_tools()
            for tool, result in download_result.items():
                print(f"   {tool}: {result}")
        
        return self.analyzer.check_tools()
    
    def reverse_engineer(self, apk_path: str, output_name: str = None) -> Dict:
        """Engenharia reversa completa."""
        if not os.path.exists(apk_path):
            return {'error': 'APK não encontrado'}
        
        # Cria diretório de saída
        name = output_name or os.path.splitext(os.path.basename(apk_path))[0]
        output_dir = os.path.join(self.output_base, name)
        os.makedirs(output_dir, exist_ok=True)
        
        result = {
            'apk_path': apk_path,
            'output_dir': output_dir,
            'steps': {},
        }
        
        # 1. Análise básica
        print("\n📊 [1/4] Análise básica...")
        analysis = self.analyzer.full_analysis(apk_path)
        result['analysis'] = analysis
        
        # Salva análise
        with open(os.path.join(output_dir, 'analysis.json'), 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        result['steps']['analysis'] = 'ok'
        
        # 2. Extração simples
        print("📦 [2/4] Extração de arquivos...")
        extract_dir = os.path.join(output_dir, 'extracted')
        extract_result = self.analyzer.extract_apk(apk_path, extract_dir)
        result['steps']['extraction'] = 'ok' if not str(extract_result).startswith('error') else extract_result
        
        # 3. Decompilação com APKTool
        tools = self.analyzer.check_tools()
        if tools.get('apktool') and tools.get('java'):
            print("🔧 [3/4] Decompilação (APKTool)...")
            apktool_dir = os.path.join(output_dir, 'apktool')
            apktool_result = self.analyzer.decompile_apktool(apk_path, apktool_dir)
            result['steps']['apktool'] = 'ok' if not str(apktool_result).startswith('error') else apktool_result
        else:
            result['steps']['apktool'] = 'skipped - tool not available'
        
        # 4. Decompilação com JADX
        if tools.get('jadx'):
            print("☕ [4/4] Decompilação para Java (JADX)...")
            jadx_dir = os.path.join(output_dir, 'jadx')
            jadx_result = self.analyzer.decompile_jadx(apk_path, jadx_dir)
            result['steps']['jadx'] = 'ok' if not str(jadx_result).startswith('error') else jadx_result
        else:
            result['steps']['jadx'] = 'skipped - tool not available'
        
        # 5. Extração de strings
        print("📝 Extraindo strings...")
        strings = self.analyzer.extract_strings(apk_path)
        with open(os.path.join(output_dir, 'strings.txt'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(strings))
        result['steps']['strings'] = f'{len(strings)} strings extraídas'
        
        print(f"\n✅ Concluído! Saída em: {output_dir}")
        
        return result


def interactive_menu():
    """Menu interativo."""
    engineer = APKReverseEngineer()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        tools = engineer.analyzer.check_tools()
        apktool_ok = "✅" if tools['apktool'] else "❌"
        jadx_ok = "✅" if tools['jadx'] else "❌"
        java_ok = "✅" if tools['java'] else "❌"
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║               📱 APK REVERSE ENGINEERING                     ║
╠══════════════════════════════════════════════════════════════╣
║  APKTool: {apktool_ok}  |  JADX: {jadx_ok}  |  Java: {java_ok}                  
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ──── 🔍 ANÁLISE ────                                        ║
║  [1] 📊 Análise Rápida (info, permissões, hashes)            ║
║  [2] 🔎 Buscar Strings Suspeitas                             ║
║  [3] 📋 Listar Arquivos do APK                               ║
║                                                              ║
║  ──── 🔧 DECOMPILAÇÃO ────                                   ║
║  [4] 📦 Extrair APK (como ZIP)                               ║
║  [5] 🔧 Decompilação Completa (APKTool + JADX)               ║
║  [6] ☕ Apenas JADX (código Java)                            ║
║                                                              ║
║  ──── ⚙️ FERRAMENTAS ────                                     ║
║  [7] ⚙️  Instalar/Atualizar Ferramentas                       ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            apk_path = input("\n📱 Caminho do APK: ").strip().strip('"')
            if apk_path and os.path.exists(apk_path):
                info = engineer.analyzer.get_apk_info(apk_path)
                
                print(f"\n📊 INFORMAÇÕES DO APK:\n")
                print(f"   Nome: {info['name']}")
                print(f"   Tamanho: {info['size'] / 1024 / 1024:.2f} MB")
                print(f"   Package: {info.get('package', 'N/A')}")
                
                print(f"\n   🔐 Hashes:")
                for h, v in info.get('hashes', {}).items():
                    print(f"      {h.upper()}: {v}")
                
                print(f"\n   📄 Arquivos:")
                print(f"      DEX: {len(info.get('dex_files', []))}")
                print(f"      Libs nativas: {len(info.get('native_libs', []))}")
                print(f"      Assets: {len(info.get('assets', []))}")
                
                perms = info.get('permissions', [])
                perm_analysis = engineer.analyzer.analyze_permissions(perms)
                print(f"\n   🔓 Permissões ({perm_analysis['total']}):")
                print(f"      Perigosas: {perm_analysis['dangerous_count']}")
                print(f"      Nível de risco: {perm_analysis['risk_level']}")
                
                if perm_analysis['dangerous']:
                    print(f"\n   ⚠️ Permissões perigosas:")
                    for p in perm_analysis['dangerous'][:10]:
                        print(f"      • {p}")
                
                print(f"\n   🔍 VirusTotal:")
                print(f"      https://www.virustotal.com/gui/file/{info['hashes']['sha256']}")
            else:
                print("❌ APK não encontrado")
            input("\nPressione Enter...")
        
        elif choice == '2':
            apk_path = input("\n📱 Caminho do APK: ").strip().strip('"')
            if apk_path and os.path.exists(apk_path):
                print("\n🔍 Buscando strings suspeitas...\n")
                suspicious = engineer.analyzer.find_suspicious_strings(apk_path)
                
                if suspicious:
                    for pattern, matches in suspicious.items():
                        print(f"   ⚠️ {pattern}:")
                        for m in matches[:5]:
                            print(f"      • {m[:80]}...")
                        print()
                else:
                    print("   ✅ Nenhuma string suspeita encontrada")
            else:
                print("❌ APK não encontrado")
            input("\nPressione Enter...")
        
        elif choice == '3':
            apk_path = input("\n📱 Caminho do APK: ").strip().strip('"')
            if apk_path and os.path.exists(apk_path):
                info = engineer.analyzer.get_apk_info(apk_path)
                
                print(f"\n📋 ARQUIVOS ({len(info.get('files', []))}):\n")
                for f in sorted(info.get('files', []))[:50]:
                    print(f"   {f}")
                
                if len(info.get('files', [])) > 50:
                    print(f"\n   ... e mais {len(info['files']) - 50} arquivos")
            else:
                print("❌ APK não encontrado")
            input("\nPressione Enter...")
        
        elif choice == '4':
            apk_path = input("\n📱 Caminho do APK: ").strip().strip('"')
            if apk_path and os.path.exists(apk_path):
                output = input("📁 Diretório de saída: ").strip().strip('"')
                if output:
                    result = engineer.analyzer.extract_apk(apk_path, output)
                    if not str(result).startswith('error'):
                        print(f"\n✅ Extraído para: {result}")
                    else:
                        print(f"\n❌ {result}")
            else:
                print("❌ APK não encontrado")
            input("\nPressione Enter...")
        
        elif choice == '5':
            apk_path = input("\n📱 Caminho do APK: ").strip().strip('"')
            if apk_path and os.path.exists(apk_path):
                result = engineer.reverse_engineer(apk_path)
                
                print(f"\n📊 RESULTADOS:")
                for step, status in result.get('steps', {}).items():
                    icon = "✅" if status == 'ok' or not str(status).startswith('error') else "❌"
                    print(f"   {icon} {step}: {status}")
                
                print(f"\n📁 Saída: {result.get('output_dir')}")
            else:
                print("❌ APK não encontrado")
            input("\nPressione Enter...")
        
        elif choice == '6':
            apk_path = input("\n📱 Caminho do APK: ").strip().strip('"')
            if apk_path and os.path.exists(apk_path):
                output = input("📁 Diretório de saída: ").strip().strip('"')
                if output:
                    print("\n☕ Decompilando com JADX...\n")
                    result = engineer.analyzer.decompile_jadx(apk_path, output)
                    if not str(result).startswith('error'):
                        print(f"\n✅ Decompilado para: {result}")
                    else:
                        print(f"\n❌ {result}")
            else:
                print("❌ APK não encontrado")
            input("\nPressione Enter...")
        
        elif choice == '7':
            engineer.setup_tools()
            input("\nPressione Enter...")
        
        elif choice == '0':
            break


if __name__ == '__main__':
    interactive_menu()
