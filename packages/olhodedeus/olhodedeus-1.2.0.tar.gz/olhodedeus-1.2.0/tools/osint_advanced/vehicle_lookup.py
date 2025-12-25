#!/usr/bin/env python3
"""
Vehicle Lookup - Consulta de veículos e placas
Parte do toolkit Olho de Deus
"""

import os
import sys
import re
import json
from typing import Dict, Optional, List
from dataclasses import dataclass

try:
    import requests
except ImportError:
    requests = None


@dataclass
class VehicleInfo:
    """Informações de veículo."""
    placa: str
    marca: str
    modelo: str
    ano: str
    cor: str
    municipio: str
    uf: str
    chassi: Optional[str]
    motor: Optional[str]
    combustivel: str
    situacao: str
    restricoes: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "placa": self.placa,
            "marca": self.marca,
            "modelo": self.modelo,
            "ano": self.ano,
            "cor": self.cor,
            "municipio": self.municipio,
            "uf": self.uf,
            "chassi": self.chassi,
            "motor": self.motor,
            "combustivel": self.combustivel,
            "situacao": self.situacao,
            "restricoes": self.restricoes
        }


class PlacaValidator:
    """Validador de placas brasileiras."""
    
    # Padrão antigo: ABC-1234
    PATTERN_OLD = re.compile(r'^[A-Z]{3}-?\d{4}$', re.IGNORECASE)
    
    # Padrão Mercosul: ABC1D23
    PATTERN_MERCOSUL = re.compile(r'^[A-Z]{3}\d[A-Z]\d{2}$', re.IGNORECASE)
    
    @classmethod
    def validate(cls, placa: str) -> bool:
        """Valida formato da placa."""
        placa = cls.clean(placa)
        return bool(cls.PATTERN_OLD.match(placa) or cls.PATTERN_MERCOSUL.match(placa))
    
    @classmethod
    def clean(cls, placa: str) -> str:
        """Remove formatação da placa."""
        return re.sub(r'[^A-Za-z0-9]', '', placa).upper()
    
    @classmethod
    def format(cls, placa: str) -> str:
        """Formata a placa."""
        placa = cls.clean(placa)
        if len(placa) == 7:
            if placa[4].isalpha():  # Mercosul
                return placa
            else:  # Antigo
                return f"{placa[:3]}-{placa[3:]}"
        return placa
    
    @classmethod
    def get_tipo(cls, placa: str) -> str:
        """Retorna o tipo da placa."""
        placa = cls.clean(placa)
        if cls.PATTERN_MERCOSUL.match(placa):
            return "Mercosul"
        elif cls.PATTERN_OLD.match(placa):
            return "Padrão Antigo"
        return "Inválido"
    
    @classmethod
    def convert_to_mercosul(cls, placa_antiga: str) -> str:
        """Converte placa antiga para padrão Mercosul."""
        placa = cls.clean(placa_antiga)
        if not cls.PATTERN_OLD.match(placa):
            return placa
        
        # O segundo dígito vira letra
        # 0=A, 1=B, 2=C, 3=D, 4=E, 5=F, 6=G, 7=H, 8=I, 9=J
        digit_to_letter = {
            '0': 'A', '1': 'B', '2': 'C', '3': 'D', '4': 'E',
            '5': 'F', '6': 'G', '7': 'H', '8': 'I', '9': 'J'
        }
        
        letras = placa[:3]
        num1 = placa[3]
        num2 = placa[4]
        num3 = placa[5]
        num4 = placa[6]
        
        letra_meio = digit_to_letter.get(num2, 'A')
        
        return f"{letras}{num1}{letra_meio}{num3}{num4}"


class VehicleLookup:
    """Consulta de veículos."""
    
    # APIs públicas de consulta (simuladas - em produção usar APIs reais)
    # Nota: APIs de consulta veicular geralmente são pagas
    
    # Tabela FIPE pública
    FIPE_API = "https://parallelum.com.br/fipe/api/v1"
    
    # UFs e códigos
    UF_CODES = {
        "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
        "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
        "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
        "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
        "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
        "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
        "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins"
    }
    
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session() if requests else None
        if self.session:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 VehicleLookup/1.0',
                'Accept': 'application/json'
            })
        self.validator = PlacaValidator()
    
    def lookup_placa(self, placa: str) -> Dict:
        """Consulta informações por placa."""
        placa = self.validator.clean(placa)
        
        if not self.validator.validate(placa):
            return {"error": "Placa inválida", "placa": placa}
        
        result = {
            "placa": self.validator.format(placa),
            "tipo": self.validator.get_tipo(placa),
            "uf_origem": self._get_uf_by_placa(placa),
            "dados": None,
            "note": "APIs de consulta veicular são geralmente pagas. Este é um resultado simulado."
        }
        
        # Converter para Mercosul se aplicável
        if result["tipo"] == "Padrão Antigo":
            result["mercosul"] = self.validator.convert_to_mercosul(placa)
        
        return result
    
    def _get_uf_by_placa(self, placa: str) -> Optional[str]:
        """Determina UF pela placa (range de letras)."""
        # Ranges de placas por estado (aproximado)
        placa = placa.upper()[:3]
        
        ranges = {
            ("AAA", "BEZ"): "PR",
            ("BFA", "GKI"): "SP",
            ("GKJ", "HOK"): "MG",
            ("HOL", "HQE"): "MS",
            ("HQF", "HTW"): "MT",
            ("HTX", "HZA"): "GO",
            ("HZB", "JAM"): "DF",
            ("JAN", "JDO"): "BA",
            ("JDP", "JKR"): "BA",
            ("JKS", "JTG"): "CE",
            ("JTH", "JWO"): "CE",
            ("JWP", "KAP"): "RN",
            ("KAQ", "KCG"): "PB",
            ("KCH", "KFD"): "PE",
            ("KFE", "KLM"): "PE",
            ("KLN", "KQE"): "AL",
            ("KQF", "KVH"): "SE",
            ("KVI", "LVE"): "RJ",
            ("LVF", "LWQ"): "ES",
            ("LWR", "MMM"): "RS",
            ("MMN", "MOZ"): "SC",
            ("MPA", "NPO"): "RS",
            ("NPP", "NQZ"): "PA",
            ("NRA", "NSZ"): "AM",
            ("NTA", "NTZ"): "RR",
            ("NUA", "NVZ"): "AP",
            ("NWA", "NYZ"): "AC",
            ("NZA", "OAL"): "RO",
            ("OAM", "OBZ"): "TO",
            ("OCA", "OEZ"): "MA",
            ("OFA", "OHZ"): "PI",
        }
        
        for (start, end), uf in ranges.items():
            if start <= placa <= end:
                return uf
        
        return None
    
    def get_marcas(self, tipo: str = "carros") -> List[Dict]:
        """Lista marcas da tabela FIPE."""
        if not self.session:
            return []
        
        try:
            url = f"{self.FIPE_API}/{tipo}/marcas"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        
        return []
    
    def get_modelos(self, tipo: str, marca_id: str) -> Dict:
        """Lista modelos de uma marca."""
        if not self.session:
            return {}
        
        try:
            url = f"{self.FIPE_API}/{tipo}/marcas/{marca_id}/modelos"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        
        return {}
    
    def get_anos(self, tipo: str, marca_id: str, modelo_id: str) -> List[Dict]:
        """Lista anos de um modelo."""
        if not self.session:
            return []
        
        try:
            url = f"{self.FIPE_API}/{tipo}/marcas/{marca_id}/modelos/{modelo_id}/anos"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        
        return []
    
    def get_valor_fipe(self, tipo: str, marca_id: str, 
                       modelo_id: str, ano_id: str) -> Optional[Dict]:
        """Obtém valor FIPE de um veículo."""
        if not self.session:
            return None
        
        try:
            url = f"{self.FIPE_API}/{tipo}/marcas/{marca_id}/modelos/{modelo_id}/anos/{ano_id}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        
        return None
    
    def search_valor_fipe(self, marca: str, modelo: str, ano: str, 
                          tipo: str = "carros") -> Optional[Dict]:
        """Busca valor FIPE por nome."""
        marcas = self.get_marcas(tipo)
        
        # Encontrar marca
        marca_id = None
        for m in marcas:
            if marca.lower() in m.get("nome", "").lower():
                marca_id = m.get("codigo")
                break
        
        if not marca_id:
            return {"error": f"Marca '{marca}' não encontrada"}
        
        # Encontrar modelo
        modelos_data = self.get_modelos(tipo, marca_id)
        modelos = modelos_data.get("modelos", [])
        
        modelo_id = None
        for m in modelos:
            if modelo.lower() in m.get("nome", "").lower():
                modelo_id = m.get("codigo")
                break
        
        if not modelo_id:
            return {"error": f"Modelo '{modelo}' não encontrado"}
        
        # Encontrar ano
        anos = self.get_anos(tipo, marca_id, str(modelo_id))
        
        ano_id = None
        for a in anos:
            if ano in a.get("nome", ""):
                ano_id = a.get("codigo")
                break
        
        if not ano_id:
            return {"error": f"Ano '{ano}' não encontrado", "anos_disponiveis": [a.get("nome") for a in anos]}
        
        # Obter valor
        return self.get_valor_fipe(tipo, marca_id, str(modelo_id), ano_id)


def interactive_menu():
    """Menu interativo do Vehicle Lookup."""
    if not requests:
        print("❌ Módulo requests não encontrado. Instale com: pip install requests")
        input("Pressione Enter...")
        return
    
    lookup = VehicleLookup()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║            🚗 VEHICLE LOOKUP - Olho de Deus                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🔍 Consultar Placa                                      ║
║  [2] ✅ Validar Placa                                        ║
║  [3] 🔄 Converter Placa para Mercosul                        ║
║  [4] 💰 Consultar Tabela FIPE                                ║
║  [5] 🏭 Listar Marcas (FIPE)                                 ║
║  [6] 📋 Consulta em Lote                                     ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Consultar Placa ===")
            placa = input("Placa: ").strip()
            
            if not placa:
                continue
            
            result = lookup.lookup_placa(placa)
            
            if result.get("error"):
                print(f"\n❌ {result['error']}")
            else:
                print(f"\n🚗 INFORMAÇÕES DA PLACA:")
                print(f"   Placa: {result['placa']}")
                print(f"   Tipo: {result['tipo']}")
                
                if result.get('uf_origem'):
                    uf = result['uf_origem']
                    estado = lookup.UF_CODES.get(uf, uf)
                    print(f"   UF Origem: {uf} ({estado})")
                
                if result.get('mercosul'):
                    print(f"   Mercosul: {result['mercosul']}")
                
                print(f"\n   ⚠️ {result.get('note', '')}")
        
        elif escolha == '2':
            print("\n=== Validar Placa ===")
            placa = input("Placa: ").strip()
            
            if lookup.validator.validate(placa):
                tipo = lookup.validator.get_tipo(placa)
                formatted = lookup.validator.format(placa)
                print(f"\n✅ PLACA VÁLIDA")
                print(f"   Formatada: {formatted}")
                print(f"   Tipo: {tipo}")
            else:
                print(f"\n❌ PLACA INVÁLIDA")
        
        elif escolha == '3':
            print("\n=== Converter para Mercosul ===")
            placa = input("Placa (padrão antigo): ").strip()
            
            if not placa:
                continue
            
            tipo = lookup.validator.get_tipo(placa)
            
            if tipo == "Padrão Antigo":
                mercosul = lookup.validator.convert_to_mercosul(placa)
                print(f"\n🔄 Conversão:")
                print(f"   Antigo: {lookup.validator.format(placa)}")
                print(f"   Mercosul: {mercosul}")
            elif tipo == "Mercosul":
                print(f"\n✅ Placa já está no padrão Mercosul")
            else:
                print(f"\n❌ Placa inválida")
        
        elif escolha == '4':
            print("\n=== Consultar Tabela FIPE ===")
            print("Tipo: [1] Carros [2] Motos [3] Caminhões")
            tipo_op = input("Tipo: ").strip()
            
            tipos = {"1": "carros", "2": "motos", "3": "caminhoes"}
            tipo = tipos.get(tipo_op, "carros")
            
            marca = input("Marca (ex: Volkswagen, Fiat): ").strip()
            modelo = input("Modelo (ex: Gol, Uno): ").strip()
            ano = input("Ano (ex: 2020, 2021): ").strip()
            
            if not marca or not modelo or not ano:
                continue
            
            print(f"\nConsultando FIPE...")
            result = lookup.search_valor_fipe(marca, modelo, ano, tipo)
            
            if result:
                if result.get("error"):
                    print(f"\n❌ {result['error']}")
                    if result.get("anos_disponiveis"):
                        print(f"   Anos disponíveis: {', '.join(result['anos_disponiveis'][:10])}")
                else:
                    print(f"\n💰 VALOR FIPE:")
                    print(f"   Marca: {result.get('Marca', 'N/A')}")
                    print(f"   Modelo: {result.get('Modelo', 'N/A')}")
                    print(f"   Ano: {result.get('AnoModelo', 'N/A')}")
                    print(f"   Combustível: {result.get('Combustivel', 'N/A')}")
                    print(f"   Código FIPE: {result.get('CodigoFipe', 'N/A')}")
                    print(f"   💵 Valor: {result.get('Valor', 'N/A')}")
                    print(f"   Mês Referência: {result.get('MesReferencia', 'N/A')}")
            else:
                print("\n❌ Não foi possível consultar a FIPE")
        
        elif escolha == '5':
            print("\n=== Listar Marcas ===")
            print("Tipo: [1] Carros [2] Motos [3] Caminhões")
            tipo_op = input("Tipo: ").strip()
            
            tipos = {"1": "carros", "2": "motos", "3": "caminhoes"}
            tipo = tipos.get(tipo_op, "carros")
            
            print(f"\nCarregando marcas de {tipo}...")
            marcas = lookup.get_marcas(tipo)
            
            if marcas:
                print(f"\n🏭 MARCAS ({len(marcas)}):")
                for i, m in enumerate(marcas, 1):
                    print(f"   {m.get('codigo'):>3} - {m.get('nome')}")
                    if i >= 30:
                        print(f"   ... e mais {len(marcas) - 30} marcas")
                        break
            else:
                print("❌ Não foi possível carregar marcas")
        
        elif escolha == '6':
            print("\n=== Consulta em Lote ===")
            print("Digite as placas (uma por linha, linha vazia para terminar):")
            
            placas = []
            while True:
                p = input("  > ").strip()
                if not p:
                    break
                placas.append(p)
            
            if not placas:
                continue
            
            print(f"\nValidando {len(placas)} placas...\n")
            
            results = []
            for placa in placas:
                valid = lookup.validator.validate(placa)
                tipo = lookup.validator.get_tipo(placa)
                formatted = lookup.validator.format(placa)
                
                status = "✅" if valid else "❌"
                print(f"   {status} {formatted} ({tipo})")
                
                results.append({
                    "placa": formatted,
                    "valido": valid,
                    "tipo": tipo,
                    "uf": lookup._get_uf_by_placa(placa) if valid else None
                })
            
            validas = sum(1 for r in results if r["valido"])
            print(f"\n📊 Resumo: {validas}/{len(results)} placas válidas")
            
            save = input("\nSalvar resultados? (s/n): ").lower()
            if save == 's':
                with open("placas_consulta.json", 'w') as f:
                    json.dump(results, f, indent=2)
                print("✅ Salvo em placas_consulta.json")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
