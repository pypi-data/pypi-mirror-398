#!/usr/bin/env python3
"""
phone_lookup.py

Lookup e validação de números de telefone.
"""
import os
import re
import json
import requests
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class PhoneInfo:
    """Informações de um telefone."""
    number: str
    country_code: str = ""
    country: str = ""
    carrier: str = ""
    line_type: str = ""
    location: str = ""
    valid: bool = False
    formatted: str = ""


class PhoneLookup:
    """Lookup de números de telefone."""
    
    # Códigos de país (principais)
    COUNTRY_CODES = {
        '1': 'United States/Canada',
        '7': 'Russia',
        '20': 'Egypt',
        '27': 'South Africa',
        '30': 'Greece',
        '31': 'Netherlands',
        '32': 'Belgium',
        '33': 'France',
        '34': 'Spain',
        '36': 'Hungary',
        '39': 'Italy',
        '40': 'Romania',
        '41': 'Switzerland',
        '43': 'Austria',
        '44': 'United Kingdom',
        '45': 'Denmark',
        '46': 'Sweden',
        '47': 'Norway',
        '48': 'Poland',
        '49': 'Germany',
        '51': 'Peru',
        '52': 'Mexico',
        '53': 'Cuba',
        '54': 'Argentina',
        '55': 'Brazil',
        '56': 'Chile',
        '57': 'Colombia',
        '58': 'Venezuela',
        '60': 'Malaysia',
        '61': 'Australia',
        '62': 'Indonesia',
        '63': 'Philippines',
        '64': 'New Zealand',
        '65': 'Singapore',
        '66': 'Thailand',
        '81': 'Japan',
        '82': 'South Korea',
        '84': 'Vietnam',
        '86': 'China',
        '90': 'Turkey',
        '91': 'India',
        '92': 'Pakistan',
        '93': 'Afghanistan',
        '94': 'Sri Lanka',
        '95': 'Myanmar',
        '98': 'Iran',
        '212': 'Morocco',
        '213': 'Algeria',
        '216': 'Tunisia',
        '218': 'Libya',
        '220': 'Gambia',
        '221': 'Senegal',
        '234': 'Nigeria',
        '249': 'Sudan',
        '254': 'Kenya',
        '255': 'Tanzania',
        '256': 'Uganda',
        '258': 'Mozambique',
        '260': 'Zambia',
        '263': 'Zimbabwe',
        '351': 'Portugal',
        '352': 'Luxembourg',
        '353': 'Ireland',
        '354': 'Iceland',
        '355': 'Albania',
        '358': 'Finland',
        '359': 'Bulgaria',
        '370': 'Lithuania',
        '371': 'Latvia',
        '372': 'Estonia',
        '373': 'Moldova',
        '374': 'Armenia',
        '375': 'Belarus',
        '380': 'Ukraine',
        '381': 'Serbia',
        '385': 'Croatia',
        '386': 'Slovenia',
        '420': 'Czech Republic',
        '421': 'Slovakia',
        '504': 'Honduras',
        '505': 'Nicaragua',
        '506': 'Costa Rica',
        '507': 'Panama',
        '591': 'Bolivia',
        '593': 'Ecuador',
        '595': 'Paraguay',
        '598': 'Uruguay',
        '852': 'Hong Kong',
        '853': 'Macau',
        '855': 'Cambodia',
        '856': 'Laos',
        '880': 'Bangladesh',
        '886': 'Taiwan',
        '960': 'Maldives',
        '961': 'Lebanon',
        '962': 'Jordan',
        '963': 'Syria',
        '964': 'Iraq',
        '965': 'Kuwait',
        '966': 'Saudi Arabia',
        '967': 'Yemen',
        '968': 'Oman',
        '970': 'Palestine',
        '971': 'UAE',
        '972': 'Israel',
        '973': 'Bahrain',
        '974': 'Qatar',
        '975': 'Bhutan',
        '976': 'Mongolia',
        '977': 'Nepal',
        '992': 'Tajikistan',
        '993': 'Turkmenistan',
        '994': 'Azerbaijan',
        '995': 'Georgia',
        '996': 'Kyrgyzstan',
        '998': 'Uzbekistan',
    }
    
    # DDDs do Brasil
    BRAZIL_DDDS = {
        '11': 'São Paulo', '12': 'São José dos Campos', '13': 'Santos',
        '14': 'Bauru', '15': 'Sorocaba', '16': 'Ribeirão Preto',
        '17': 'São José do Rio Preto', '18': 'Presidente Prudente', '19': 'Campinas',
        '21': 'Rio de Janeiro', '22': 'Campos', '24': 'Volta Redonda',
        '27': 'Vitória', '28': 'Cachoeiro de Itapemirim',
        '31': 'Belo Horizonte', '32': 'Juiz de Fora', '33': 'Gov. Valadares',
        '34': 'Uberlândia', '35': 'Poços de Caldas', '37': 'Divinópolis', '38': 'Montes Claros',
        '41': 'Curitiba', '42': 'Ponta Grossa', '43': 'Londrina',
        '44': 'Maringá', '45': 'Foz do Iguaçu', '46': 'Francisco Beltrão',
        '47': 'Joinville', '48': 'Florianópolis', '49': 'Chapecó',
        '51': 'Porto Alegre', '53': 'Pelotas', '54': 'Caxias do Sul', '55': 'Santa Maria',
        '61': 'Brasília', '62': 'Goiânia', '63': 'Palmas', '64': 'Rio Verde',
        '65': 'Cuiabá', '66': 'Rondonópolis', '67': 'Campo Grande', '68': 'Rio Branco', '69': 'Porto Velho',
        '71': 'Salvador', '73': 'Ilhéus', '74': 'Juazeiro', '75': 'Feira de Santana', '77': 'Barreiras',
        '79': 'Aracaju', '81': 'Recife', '82': 'Maceió', '83': 'João Pessoa',
        '84': 'Natal', '85': 'Fortaleza', '86': 'Teresina', '87': 'Petrolina',
        '88': 'Juazeiro do Norte', '89': 'Picos',
        '91': 'Belém', '92': 'Manaus', '93': 'Santarém', '94': 'Marabá',
        '95': 'Boa Vista', '96': 'Macapá', '97': 'Coari', '98': 'São Luís', '99': 'Imperatriz',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def normalize(self, phone: str) -> str:
        """Normaliza número de telefone."""
        # Remove tudo exceto dígitos e +
        normalized = re.sub(r'[^\d+]', '', phone)
        
        # Remove + se não estiver no início
        if '+' in normalized[1:]:
            normalized = normalized[0] + normalized[1:].replace('+', '')
        
        return normalized
    
    def parse(self, phone: str) -> PhoneInfo:
        """Parse e análise de telefone."""
        normalized = self.normalize(phone)
        info = PhoneInfo(number=normalized)
        
        # Remove + inicial para análise
        number = normalized.lstrip('+')
        
        # Detecta código do país
        for code, country in sorted(self.COUNTRY_CODES.items(), key=lambda x: -len(x[0])):
            if number.startswith(code):
                info.country_code = code
                info.country = country
                break
        
        # Brasil: analisa DDD
        if info.country_code == '55':
            remaining = number[2:]  # Remove 55
            if len(remaining) >= 2:
                ddd = remaining[:2]
                if ddd in self.BRAZIL_DDDS:
                    info.location = self.BRAZIL_DDDS[ddd]
                    
                # Detecta tipo de linha
                local_number = remaining[2:]
                if local_number.startswith('9') and len(local_number) == 9:
                    info.line_type = 'Celular'
                elif len(local_number) == 8:
                    info.line_type = 'Fixo'
                else:
                    info.line_type = 'Desconhecido'
        
        # Valida comprimento
        if len(number) >= 8 and len(number) <= 15:
            info.valid = True
        
        # Formata
        if info.country_code == '55' and len(number) >= 12:
            ddd = number[2:4]
            local = number[4:]
            if len(local) == 9:
                info.formatted = f"+55 ({ddd}) {local[0]} {local[1:5]}-{local[5:]}"
            else:
                info.formatted = f"+55 ({ddd}) {local[:4]}-{local[4:]}"
        elif info.country_code:
            info.formatted = f"+{number}"
        else:
            info.formatted = number
        
        return info
    
    def lookup_numverify(self, phone: str, api_key: str) -> Dict:
        """Lookup via NumVerify API."""
        normalized = self.normalize(phone).lstrip('+')
        try:
            resp = self.session.get(
                'http://apilayer.net/api/validate',
                params={'access_key': api_key, 'number': normalized},
                timeout=10
            )
            return resp.json()
        except Exception as e:
            return {'error': str(e)}
    
    def lookup_ip_api(self, phone: str) -> Dict:
        """Lookup básico usando IP-API (para código de país)."""
        info = self.parse(phone)
        return {
            'number': info.number,
            'valid': info.valid,
            'country_code': info.country_code,
            'country': info.country,
            'location': info.location,
            'line_type': info.line_type,
            'formatted': info.formatted
        }
    
    def generate_links(self, phone: str) -> Dict:
        """Gera links para verificação."""
        normalized = self.normalize(phone).lstrip('+')
        
        return {
            'whatsapp': f'https://wa.me/{normalized}',
            'whatsapp_api': f'https://api.whatsapp.com/send?phone={normalized}',
            'telegram': f'https://t.me/+{normalized}',
            'truecaller': f'https://www.truecaller.com/search/br/{normalized}',
            'syncme': f'https://sync.me/search/?number={normalized}',
            'getcontact': f'https://getcontact.com/br/search?phone={normalized}',
            'nomorobo': f'https://www.nomorobo.com/lookup/{normalized}',
            'whitepages': f'https://www.whitepages.com/phone/{normalized}',
            'spy_dialer': f'https://www.spydialer.com/default.aspx?phone={normalized}',
            'google': f'https://www.google.com/search?q="{normalized}"',
        }
    
    def check_carrier_brazil(self, phone: str) -> str:
        """Detecta operadora brasileira pelo prefixo."""
        normalized = self.normalize(phone)
        
        # Remove código do país
        if normalized.startswith('+55'):
            normalized = normalized[3:]
        elif normalized.startswith('55'):
            normalized = normalized[2:]
        
        # Pega DDD + primeiro dígito
        if len(normalized) >= 3:
            ddd = normalized[:2]
            
            # Para celulares, remove o 9 inicial
            if len(normalized) >= 11:  # DDD + 9 dígitos
                prefix = normalized[3:7]  # 4 dígitos após o 9
            else:
                prefix = normalized[2:6]
        
        # Prefixos conhecidos (pode estar desatualizado devido à portabilidade)
        # Esses são os prefixos originais, não considera portabilidade
        carrier_prefixes = {
            # Vivo
            '9': ['96', '97', '98', '99'],
            # TIM
            '8': ['80', '81', '82', '83', '84', '85'],
            # Claro
            '7': ['73', '74', '75', '76', '77', '78', '79'],
            # Oi
            '6': ['61', '62', '63', '64', '65', '66', '67', '68', '69'],
        }
        
        return "Portabilidade ativa - operadora original indeterminável"
    
    def batch_analyze(self, phones: List[str]) -> List[Dict]:
        """Analisa múltiplos telefones."""
        results = []
        for phone in phones:
            info = self.lookup_ip_api(phone)
            info['links'] = self.generate_links(phone)
            results.append(info)
        return results


def interactive_menu():
    """Menu interativo."""
    lookup = PhoneLookup()
    
    # Configuração
    config_path = "config/phone_lookup.json"
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("""
╔══════════════════════════════════════════════════════════════╗
║                  📱 PHONE NUMBER LOOKUP                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ──── 🔍 ANÁLISE ────                                        ║
║  [1] 📱 Analisar Número                                      ║
║  [2] 🔗 Gerar Links de Verificação                           ║
║  [3] 📊 Análise em Lote                                      ║
║                                                              ║
║  ──── 🇧🇷 BRASIL ────                                         ║
║  [4] 📍 Consultar DDD                                        ║
║  [5] 🌎 Listar Códigos de País                               ║
║                                                              ║
║  ──── ⚙️ CONFIGURAÇÃO ────                                    ║
║  [6] ⚙️  Configurar APIs                                      ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            phone = input("\n📱 Número de telefone: ").strip()
            if phone:
                result = lookup.lookup_ip_api(phone)
                
                print(f"\n📊 ANÁLISE DO NÚMERO:")
                print(f"   Número: {result['number']}")
                print(f"   Formatado: {result['formatted']}")
                print(f"   Válido: {'✅' if result['valid'] else '❌'}")
                print(f"   País: {result['country']} (+{result['country_code']})")
                if result['location']:
                    print(f"   Localização: {result['location']}")
                if result['line_type']:
                    print(f"   Tipo: {result['line_type']}")
                
                # API NumVerify se configurada
                if config.get('numverify_key'):
                    nv = lookup.lookup_numverify(phone, config['numverify_key'])
                    if 'error' not in nv:
                        print(f"\n   📡 NumVerify:")
                        print(f"      Operadora: {nv.get('carrier', 'N/A')}")
                        print(f"      Tipo: {nv.get('line_type', 'N/A')}")
            input("\nPressione Enter...")
        
        elif choice == '2':
            phone = input("\n📱 Número: ").strip()
            if phone:
                links = lookup.generate_links(phone)
                print(f"\n🔗 LINKS DE VERIFICAÇÃO:\n")
                for service, url in links.items():
                    print(f"   {service.upper()}: {url}")
            input("\nPressione Enter...")
        
        elif choice == '3':
            print("\n📊 Digite os números (um por linha, vazio para terminar):")
            phones = []
            while True:
                phone = input("   ").strip()
                if not phone:
                    break
                phones.append(phone)
            
            if phones:
                results = lookup.batch_analyze(phones)
                print(f"\n📊 RESULTADOS:\n")
                for r in results:
                    print(f"   {r['formatted']}: {r['country']} - {r['location'] or 'N/A'}")
            input("\nPressione Enter...")
        
        elif choice == '4':
            print("\n🇧🇷 DDDs DO BRASIL:\n")
            for ddd, city in sorted(lookup.BRAZIL_DDDS.items()):
                print(f"   {ddd}: {city}")
            input("\nPressione Enter...")
        
        elif choice == '5':
            print("\n🌎 CÓDIGOS DE PAÍS:\n")
            for code, country in sorted(lookup.COUNTRY_CODES.items(), key=lambda x: x[1]):
                print(f"   +{code}: {country}")
            input("\nPressione Enter...")
        
        elif choice == '6':
            print("\n⚙️ CONFIGURAÇÃO DE APIs\n")
            print("NumVerify: https://numverify.com (gratuito com limites)")
            
            key = input(f"\nNumVerify API Key [{config.get('numverify_key', '')[:10]}...]: ").strip()
            if key:
                config['numverify_key'] = key
            
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print("✅ Configuração salva!")
            input("\nPressione Enter...")
        
        elif choice == '0':
            break


if __name__ == '__main__':
    interactive_menu()
