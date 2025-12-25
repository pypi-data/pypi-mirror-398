#!/usr/bin/env python3
"""
Encoding Hub - Central de codificação e decodificação
Parte do toolkit Olho de Deus
"""

import os
import sys
import base64
import urllib.parse
import binascii
import html
import codecs
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class EncodingResult:
    """Resultado de operação de encoding."""
    input_text: str
    output_text: str
    encoding_type: str
    operation: str  # encode ou decode
    success: bool
    error: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "input": self.input_text[:100],
            "output": self.output_text[:100],
            "encoding": self.encoding_type,
            "operation": self.operation,
            "success": self.success,
            "error": self.error
        }


class Base64Encoder:
    """Codificador Base64."""
    
    @staticmethod
    def encode(text: str) -> str:
        return base64.b64encode(text.encode()).decode()
    
    @staticmethod
    def decode(text: str) -> str:
        return base64.b64decode(text).decode()
    
    @staticmethod
    def encode_url_safe(text: str) -> str:
        return base64.urlsafe_b64encode(text.encode()).decode()
    
    @staticmethod
    def decode_url_safe(text: str) -> str:
        return base64.urlsafe_b64decode(text).decode()


class Base32Encoder:
    """Codificador Base32."""
    
    @staticmethod
    def encode(text: str) -> str:
        return base64.b32encode(text.encode()).decode()
    
    @staticmethod
    def decode(text: str) -> str:
        return base64.b32decode(text).decode()


class Base16Encoder:
    """Codificador Base16/Hex."""
    
    @staticmethod
    def encode(text: str) -> str:
        return base64.b16encode(text.encode()).decode()
    
    @staticmethod
    def decode(text: str) -> str:
        return base64.b16decode(text.upper()).decode()


class URLEncoder:
    """Codificador URL."""
    
    @staticmethod
    def encode(text: str) -> str:
        return urllib.parse.quote(text, safe='')
    
    @staticmethod
    def decode(text: str) -> str:
        return urllib.parse.unquote(text)
    
    @staticmethod
    def encode_plus(text: str) -> str:
        return urllib.parse.quote_plus(text)
    
    @staticmethod
    def decode_plus(text: str) -> str:
        return urllib.parse.unquote_plus(text)


class HTMLEncoder:
    """Codificador HTML."""
    
    @staticmethod
    def encode(text: str) -> str:
        return html.escape(text)
    
    @staticmethod
    def decode(text: str) -> str:
        return html.unescape(text)
    
    @staticmethod
    def encode_named(text: str) -> str:
        """Codifica para named entities."""
        result = ""
        for char in text:
            if char.isalnum() or char in ' \n\t':
                result += char
            else:
                result += f"&#{ord(char)};"
        return result


class HexEncoder:
    """Codificador Hexadecimal."""
    
    @staticmethod
    def encode(text: str) -> str:
        return text.encode().hex()
    
    @staticmethod
    def decode(text: str) -> str:
        return bytes.fromhex(text).decode()
    
    @staticmethod
    def encode_with_prefix(text: str) -> str:
        return "0x" + text.encode().hex()
    
    @staticmethod
    def encode_spaced(text: str) -> str:
        hex_str = text.encode().hex()
        return ' '.join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))


class BinaryEncoder:
    """Codificador Binário."""
    
    @staticmethod
    def encode(text: str) -> str:
        return ' '.join(format(b, '08b') for b in text.encode())
    
    @staticmethod
    def decode(text: str) -> str:
        binary_values = text.split()
        return ''.join(chr(int(b, 2)) for b in binary_values)


class OctalEncoder:
    """Codificador Octal."""
    
    @staticmethod
    def encode(text: str) -> str:
        return ' '.join(format(b, '03o') for b in text.encode())
    
    @staticmethod
    def decode(text: str) -> str:
        octal_values = text.split()
        return ''.join(chr(int(o, 8)) for o in octal_values)


class ASCIIEncoder:
    """Codificador ASCII (decimal)."""
    
    @staticmethod
    def encode(text: str) -> str:
        return ' '.join(str(ord(c)) for c in text)
    
    @staticmethod
    def decode(text: str) -> str:
        ascii_values = text.split()
        return ''.join(chr(int(v)) for v in ascii_values)


class ROT13Encoder:
    """Codificador ROT13."""
    
    @staticmethod
    def encode(text: str) -> str:
        return codecs.encode(text, 'rot_13')
    
    @staticmethod
    def decode(text: str) -> str:
        return codecs.decode(text, 'rot_13')


class UnicodeEncoder:
    """Codificador Unicode."""
    
    @staticmethod
    def encode(text: str) -> str:
        return ' '.join(f'U+{ord(c):04X}' for c in text)
    
    @staticmethod
    def decode(text: str) -> str:
        codes = text.replace('U+', '').replace('u+', '').split()
        return ''.join(chr(int(c, 16)) for c in codes)
    
    @staticmethod
    def encode_escape(text: str) -> str:
        return text.encode('unicode_escape').decode()
    
    @staticmethod
    def decode_escape(text: str) -> str:
        return text.encode().decode('unicode_escape')


class JSONEncoder:
    """Codificador JSON."""
    
    @staticmethod
    def encode(text: str) -> str:
        return json.dumps(text)
    
    @staticmethod
    def decode(text: str) -> str:
        return json.loads(text)
    
    @staticmethod
    def pretty_print(text: str) -> str:
        try:
            obj = json.loads(text)
            return json.dumps(obj, indent=2, ensure_ascii=False)
        except:
            return text


class MorseEncoder:
    """Codificador Morse."""
    
    MORSE_CODE = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
        'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
        'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
        'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
        'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
        'Z': '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--',
        '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..',
        '9': '----.', ' ': '/'
    }
    
    REVERSE_MORSE = {v: k for k, v in MORSE_CODE.items()}
    
    @classmethod
    def encode(cls, text: str) -> str:
        return ' '.join(cls.MORSE_CODE.get(c.upper(), '') for c in text)
    
    @classmethod
    def decode(cls, text: str) -> str:
        words = text.split(' / ')
        result = []
        for word in words:
            chars = word.split()
            result.append(''.join(cls.REVERSE_MORSE.get(c, '') for c in chars))
        return ' '.join(result)


class EncodingHub:
    """Hub central de encoding/decoding."""
    
    ENCODERS = {
        "base64": Base64Encoder,
        "base32": Base32Encoder,
        "base16": Base16Encoder,
        "url": URLEncoder,
        "html": HTMLEncoder,
        "hex": HexEncoder,
        "binary": BinaryEncoder,
        "octal": OctalEncoder,
        "ascii": ASCIIEncoder,
        "rot13": ROT13Encoder,
        "unicode": UnicodeEncoder,
        "json": JSONEncoder,
        "morse": MorseEncoder,
    }
    
    @classmethod
    def encode(cls, text: str, encoding: str) -> EncodingResult:
        """Codifica texto."""
        encoding = encoding.lower()
        
        if encoding not in cls.ENCODERS:
            return EncodingResult(
                input_text=text,
                output_text="",
                encoding_type=encoding,
                operation="encode",
                success=False,
                error=f"Encoding '{encoding}' não suportado"
            )
        
        try:
            encoder = cls.ENCODERS[encoding]
            output = encoder.encode(text)
            
            return EncodingResult(
                input_text=text,
                output_text=output,
                encoding_type=encoding,
                operation="encode",
                success=True
            )
        except Exception as e:
            return EncodingResult(
                input_text=text,
                output_text="",
                encoding_type=encoding,
                operation="encode",
                success=False,
                error=str(e)
            )
    
    @classmethod
    def decode(cls, text: str, encoding: str) -> EncodingResult:
        """Decodifica texto."""
        encoding = encoding.lower()
        
        if encoding not in cls.ENCODERS:
            return EncodingResult(
                input_text=text,
                output_text="",
                encoding_type=encoding,
                operation="decode",
                success=False,
                error=f"Encoding '{encoding}' não suportado"
            )
        
        try:
            encoder = cls.ENCODERS[encoding]
            output = encoder.decode(text)
            
            return EncodingResult(
                input_text=text,
                output_text=output,
                encoding_type=encoding,
                operation="decode",
                success=True
            )
        except Exception as e:
            return EncodingResult(
                input_text=text,
                output_text="",
                encoding_type=encoding,
                operation="decode",
                success=False,
                error=str(e)
            )
    
    @classmethod
    def detect_encoding(cls, text: str) -> List[str]:
        """Tenta detectar o encoding do texto."""
        possible = []
        
        # Base64
        try:
            if len(text) % 4 == 0 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in text):
                base64.b64decode(text)
                possible.append("base64")
        except:
            pass
        
        # Hex
        try:
            if all(c in '0123456789abcdefABCDEF' for c in text.replace(' ', '')):
                possible.append("hex")
        except:
            pass
        
        # Binary
        if all(c in '01 ' for c in text):
            possible.append("binary")
        
        # URL encoded
        if '%' in text:
            possible.append("url")
        
        # HTML entities
        if '&' in text and ';' in text:
            possible.append("html")
        
        # Morse
        if all(c in '.-/ ' for c in text):
            possible.append("morse")
        
        return possible
    
    @classmethod
    def chain_encode(cls, text: str, encodings: List[str]) -> str:
        """Aplica múltiplos encodings em cadeia."""
        result = text
        for encoding in encodings:
            enc_result = cls.encode(result, encoding)
            if enc_result.success:
                result = enc_result.output_text
            else:
                raise ValueError(f"Erro em {encoding}: {enc_result.error}")
        return result
    
    @classmethod
    def chain_decode(cls, text: str, encodings: List[str]) -> str:
        """Aplica múltiplos decodings em cadeia (ordem reversa)."""
        result = text
        for encoding in reversed(encodings):
            dec_result = cls.decode(result, encoding)
            if dec_result.success:
                result = dec_result.output_text
            else:
                raise ValueError(f"Erro em {encoding}: {dec_result.error}")
        return result


def interactive_menu():
    """Menu interativo do Encoding Hub."""
    hub = EncodingHub()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║            🔄 ENCODING HUB - Olho de Deus                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔒 Encode (Codificar)                                   ║
║  [2] 🔓 Decode (Decodificar)                                 ║
║  [3] 🔍 Detectar Encoding                                    ║
║  [4] 🔗 Encoding em Cadeia                                   ║
║  [5] 📋 Listar Encodings Suportados                          ║
║  [6] 🛠️  Ferramentas Especiais                                ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Encode ===")
            print(f"Encodings: {', '.join(hub.ENCODERS.keys())}")
            
            encoding = input("\nEncoding: ").strip().lower()
            text = input("Texto: ").strip()
            
            if not text:
                continue
            
            result = hub.encode(text, encoding)
            
            if result.success:
                print(f"\n✅ Resultado ({encoding}):")
                print(result.output_text)
            else:
                print(f"\n❌ Erro: {result.error}")
        
        elif escolha == '2':
            print("\n=== Decode ===")
            print(f"Encodings: {', '.join(hub.ENCODERS.keys())}")
            
            encoding = input("\nEncoding: ").strip().lower()
            text = input("Texto codificado: ").strip()
            
            if not text:
                continue
            
            result = hub.decode(text, encoding)
            
            if result.success:
                print(f"\n✅ Resultado ({encoding}):")
                print(result.output_text)
            else:
                print(f"\n❌ Erro: {result.error}")
        
        elif escolha == '3':
            print("\n=== Detectar Encoding ===")
            text = input("Texto: ").strip()
            
            if not text:
                continue
            
            possible = hub.detect_encoding(text)
            
            if possible:
                print(f"\n🔍 Possíveis encodings: {', '.join(possible)}")
                
                print("\nTentando decodificar:")
                for enc in possible:
                    result = hub.decode(text, enc)
                    if result.success:
                        output = result.output_text[:50]
                        print(f"   {enc}: {output}...")
            else:
                print("\n❌ Não foi possível detectar o encoding")
        
        elif escolha == '4':
            print("\n=== Encoding em Cadeia ===")
            print("Exemplo: base64,hex aplica Base64 e depois Hex\n")
            
            print("1. Encode em cadeia")
            print("2. Decode em cadeia")
            op = input("Operação: ").strip()
            
            encodings_str = input("Encodings (separados por vírgula): ").strip()
            encodings = [e.strip().lower() for e in encodings_str.split(",")]
            
            text = input("Texto: ").strip()
            
            if not text or not encodings:
                continue
            
            try:
                if op == '1':
                    result = hub.chain_encode(text, encodings)
                    print(f"\n✅ Resultado ({' -> '.join(encodings)}):")
                else:
                    result = hub.chain_decode(text, encodings)
                    print(f"\n✅ Resultado ({' <- '.join(reversed(encodings))}):")
                
                print(result)
            except Exception as e:
                print(f"\n❌ Erro: {e}")
        
        elif escolha == '5':
            print("\n=== Encodings Suportados ===\n")
            
            descriptions = {
                "base64": "Base64 - Codificação binário para texto (email, web)",
                "base32": "Base32 - Similar ao Base64, mas com menos caracteres",
                "base16": "Base16 - Hexadecimal (hex)",
                "url": "URL Encoding - Caracteres especiais em URLs",
                "html": "HTML Entities - Escape de caracteres HTML",
                "hex": "Hexadecimal - Representação em base 16",
                "binary": "Binário - Representação em bits (0 e 1)",
                "octal": "Octal - Representação em base 8",
                "ascii": "ASCII Decimal - Valores numéricos ASCII",
                "rot13": "ROT13 - Rotação de 13 posições (cifra simples)",
                "unicode": "Unicode - Pontos de código Unicode (U+XXXX)",
                "json": "JSON - Escape de strings JSON",
                "morse": "Código Morse - Pontos e traços",
            }
            
            for name, desc in descriptions.items():
                print(f"   📦 {name}")
                print(f"      {desc}\n")
        
        elif escolha == '6':
            print("\n=== Ferramentas Especiais ===")
            print("1. Base64 URL-safe")
            print("2. URL+ encoding (espaços como +)")
            print("3. Hex com espaços")
            print("4. Unicode escape")
            print("5. JSON pretty print")
            
            tool = input("\nFerramenta: ").strip()
            text = input("Texto: ").strip()
            
            if not text:
                continue
            
            try:
                if tool == '1':
                    print("\n1. Encode  2. Decode")
                    op = input("Operação: ").strip()
                    if op == '1':
                        result = Base64Encoder.encode_url_safe(text)
                    else:
                        result = Base64Encoder.decode_url_safe(text)
                    print(f"\n✅ Resultado: {result}")
                
                elif tool == '2':
                    print("\n1. Encode  2. Decode")
                    op = input("Operação: ").strip()
                    if op == '1':
                        result = URLEncoder.encode_plus(text)
                    else:
                        result = URLEncoder.decode_plus(text)
                    print(f"\n✅ Resultado: {result}")
                
                elif tool == '3':
                    result = HexEncoder.encode_spaced(text)
                    print(f"\n✅ Resultado: {result}")
                
                elif tool == '4':
                    print("\n1. Encode  2. Decode")
                    op = input("Operação: ").strip()
                    if op == '1':
                        result = UnicodeEncoder.encode_escape(text)
                    else:
                        result = UnicodeEncoder.decode_escape(text)
                    print(f"\n✅ Resultado: {result}")
                
                elif tool == '5':
                    result = JSONEncoder.pretty_print(text)
                    print(f"\n✅ Resultado:\n{result}")
                
            except Exception as e:
                print(f"\n❌ Erro: {e}")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
