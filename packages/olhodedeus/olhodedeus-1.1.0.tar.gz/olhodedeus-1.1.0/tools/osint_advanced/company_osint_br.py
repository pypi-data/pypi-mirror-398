#!/usr/bin/env python3
"""
Company OSINT BR - OSINT específico para empresas brasileiras
Consulta CNPJ, Receita Federal, SINTEGRA, etc.
Parte do toolkit Olho de Deus
"""

import os
import sys
import re
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None


@dataclass
class CNPJInfo:
    """Informações de CNPJ."""
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str]
    situacao: str
    data_abertura: str
    natureza_juridica: str
    atividade_principal: str
    atividades_secundarias: List[str]
    endereco: Dict
    telefone: Optional[str]
    email: Optional[str]
    capital_social: float
    socios: List[Dict]
    
    def to_dict(self) -> Dict:
        return {
            "cnpj": self.cnpj,
            "razao_social": self.razao_social,
            "nome_fantasia": self.nome_fantasia,
            "situacao": self.situacao,
            "data_abertura": self.data_abertura,
            "natureza_juridica": self.natureza_juridica,
            "atividade_principal": self.atividade_principal,
            "atividades_secundarias": self.atividades_secundarias,
            "endereco": self.endereco,
            "telefone": self.telefone,
            "email": self.email,
            "capital_social": self.capital_social,
            "socios": self.socios
        }


class CNPJValidator:
    """Validador de CNPJ."""
    
    @staticmethod
    def clean(cnpj: str) -> str:
        """Remove formatação do CNPJ."""
        return re.sub(r'\D', '', cnpj)
    
    @staticmethod
    def format(cnpj: str) -> str:
        """Formata CNPJ."""
        cnpj = CNPJValidator.clean(cnpj)
        if len(cnpj) != 14:
            return cnpj
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    
    @staticmethod
    def validate(cnpj: str) -> bool:
        """Valida CNPJ."""
        cnpj = CNPJValidator.clean(cnpj)
        
        if len(cnpj) != 14:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            return False
        
        # Cálculo do primeiro dígito verificador
        peso1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma1 = sum(int(cnpj[i]) * peso1[i] for i in range(12))
        resto1 = soma1 % 11
        digito1 = 0 if resto1 < 2 else 11 - resto1
        
        if int(cnpj[12]) != digito1:
            return False
        
        # Cálculo do segundo dígito verificador
        peso2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma2 = sum(int(cnpj[i]) * peso2[i] for i in range(13))
        resto2 = soma2 % 11
        digito2 = 0 if resto2 < 2 else 11 - resto2
        
        return int(cnpj[13]) == digito2


class CPFValidator:
    """Validador de CPF."""
    
    @staticmethod
    def clean(cpf: str) -> str:
        """Remove formatação do CPF."""
        return re.sub(r'\D', '', cpf)
    
    @staticmethod
    def format(cpf: str) -> str:
        """Formata CPF."""
        cpf = CPFValidator.clean(cpf)
        if len(cpf) != 11:
            return cpf
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    
    @staticmethod
    def validate(cpf: str) -> bool:
        """Valida CPF."""
        cpf = CPFValidator.clean(cpf)
        
        if len(cpf) != 11:
            return False
        
        if cpf == cpf[0] * 11:
            return False
        
        # Primeiro dígito
        soma1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto1 = (soma1 * 10) % 11
        digito1 = resto1 if resto1 < 10 else 0
        
        if int(cpf[9]) != digito1:
            return False
        
        # Segundo dígito
        soma2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto2 = (soma2 * 10) % 11
        digito2 = resto2 if resto2 < 10 else 0
        
        return int(cpf[10]) == digito2


class BrazilCompanyOSINT:
    """OSINT para empresas brasileiras."""
    
    # API pública do BrasilAPI
    BRASIL_API = "https://brasilapi.com.br/api"
    
    # API ReceitaWS (gratuita com limites)
    RECEITAWS_API = "https://www.receitaws.com.br/v1/cnpj"
    
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session() if requests else None
        if self.session:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 CompanyOSINT/1.0',
                'Accept': 'application/json'
            })
        self.cnpj_validator = CNPJValidator()
        self.cpf_validator = CPFValidator()
    
    def query_cnpj(self, cnpj: str) -> Optional[CNPJInfo]:
        """Consulta informações de CNPJ."""
        if not self.session:
            return None
        
        cnpj = self.cnpj_validator.clean(cnpj)
        
        if not self.cnpj_validator.validate(cnpj):
            return None
        
        # Tentar BrasilAPI primeiro
        try:
            url = f"{self.BRASIL_API}/cnpj/v1/{cnpj}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_brasil_api(data)
        except Exception:
            pass
        
        # Fallback para ReceitaWS
        try:
            url = f"{self.RECEITAWS_API}/{cnpj}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") != "ERROR":
                    return self._parse_receitaws(data)
        except Exception:
            pass
        
        return None
    
    def _parse_brasil_api(self, data: Dict) -> CNPJInfo:
        """Parse resposta do BrasilAPI."""
        socios = []
        for socio in data.get("qsa", []):
            socios.append({
                "nome": socio.get("nome_socio", ""),
                "qualificacao": socio.get("qualificacao_socio", ""),
                "cpf_cnpj": socio.get("cnpj_cpf_do_socio", "")
            })
        
        endereco = {
            "logradouro": data.get("logradouro", ""),
            "numero": data.get("numero", ""),
            "complemento": data.get("complemento", ""),
            "bairro": data.get("bairro", ""),
            "cep": data.get("cep", ""),
            "municipio": data.get("municipio", ""),
            "uf": data.get("uf", "")
        }
        
        atividades_sec = [
            a.get("texto", "") for a in data.get("cnaes_secundarios", [])
        ]
        
        return CNPJInfo(
            cnpj=data.get("cnpj", ""),
            razao_social=data.get("razao_social", ""),
            nome_fantasia=data.get("nome_fantasia"),
            situacao=data.get("descricao_situacao_cadastral", ""),
            data_abertura=data.get("data_inicio_atividade", ""),
            natureza_juridica=data.get("natureza_juridica", ""),
            atividade_principal=data.get("cnae_fiscal_descricao", ""),
            atividades_secundarias=atividades_sec,
            endereco=endereco,
            telefone=data.get("ddd_telefone_1"),
            email=data.get("email"),
            capital_social=float(data.get("capital_social", 0)),
            socios=socios
        )
    
    def _parse_receitaws(self, data: Dict) -> CNPJInfo:
        """Parse resposta do ReceitaWS."""
        socios = []
        for socio in data.get("qsa", []):
            socios.append({
                "nome": socio.get("nome", ""),
                "qualificacao": socio.get("qual", ""),
                "cpf_cnpj": ""
            })
        
        endereco = {
            "logradouro": data.get("logradouro", ""),
            "numero": data.get("numero", ""),
            "complemento": data.get("complemento", ""),
            "bairro": data.get("bairro", ""),
            "cep": data.get("cep", ""),
            "municipio": data.get("municipio", ""),
            "uf": data.get("uf", "")
        }
        
        atividades_sec = [
            a.get("text", "") for a in data.get("atividades_secundarias", [])
        ]
        
        principal = data.get("atividade_principal", [])
        ativ_principal = principal[0].get("text", "") if principal else ""
        
        return CNPJInfo(
            cnpj=data.get("cnpj", ""),
            razao_social=data.get("nome", ""),
            nome_fantasia=data.get("fantasia"),
            situacao=data.get("situacao", ""),
            data_abertura=data.get("abertura", ""),
            natureza_juridica=data.get("natureza_juridica", ""),
            atividade_principal=ativ_principal,
            atividades_secundarias=atividades_sec,
            endereco=endereco,
            telefone=data.get("telefone"),
            email=data.get("email"),
            capital_social=float(data.get("capital_social", "0").replace(".", "").replace(",", ".")),
            socios=socios
        )
    
    def search_by_name(self, name: str) -> List[Dict]:
        """Busca empresas por nome (limitado)."""
        # Nota: APIs públicas geralmente não permitem busca por nome
        # Esta é uma implementação placeholder
        
        return [{
            "note": "Busca por nome não disponível em APIs públicas gratuitas",
            "alternatives": [
                "Consulta Receita Federal (manual)",
                "SINTEGRA (por estado)",
                "Portais de dados abertos estaduais"
            ],
            "query": name
        }]
    
    def query_cep(self, cep: str) -> Optional[Dict]:
        """Consulta informações de CEP."""
        if not self.session:
            return None
        
        cep = re.sub(r'\D', '', cep)
        
        if len(cep) != 8:
            return None
        
        try:
            url = f"{self.BRASIL_API}/cep/v2/{cep}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        
        # Fallback ViaCEP
        try:
            url = f"https://viacep.com.br/ws/{cep}/json/"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                if "erro" not in data:
                    return data
        except Exception:
            pass
        
        return None
    
    def query_bank(self, code: str) -> Optional[Dict]:
        """Consulta informações de banco pelo código."""
        if not self.session:
            return None
        
        try:
            url = f"{self.BRASIL_API}/banks/v1/{code}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        
        return None
    
    def list_banks(self) -> List[Dict]:
        """Lista todos os bancos."""
        if not self.session:
            return []
        
        try:
            url = f"{self.BRASIL_API}/banks/v1"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        
        return []
    
    def query_ddd(self, ddd: str) -> Optional[Dict]:
        """Consulta informações de DDD."""
        if not self.session:
            return None
        
        try:
            url = f"{self.BRASIL_API}/ddd/v1/{ddd}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        
        return None
    
    def query_feriados(self, ano: int) -> List[Dict]:
        """Consulta feriados nacionais."""
        if not self.session:
            return []
        
        try:
            url = f"{self.BRASIL_API}/feriados/v1/{ano}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        
        return []


def interactive_menu():
    """Menu interativo do Company OSINT BR."""
    if not requests:
        print("❌ Módulo requests não encontrado. Instale com: pip install requests")
        input("Pressione Enter...")
        return
    
    osint = BrazilCompanyOSINT()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║          🇧🇷 COMPANY OSINT BR - Olho de Deus                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] 🏢 Consultar CNPJ                                       ║
║  [2] ✅ Validar CNPJ                                         ║
║  [3] 👤 Validar CPF                                          ║
║  [4] 📍 Consultar CEP                                        ║
║  [5] 🏦 Consultar Banco                                      ║
║  [6] 📞 Consultar DDD                                        ║
║  [7] 📅 Feriados Nacionais                                   ║
║  [8] 📋 Consulta em Lote (CNPJ)                              ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Consultar CNPJ ===")
            cnpj = input("CNPJ: ").strip()
            
            if not cnpj:
                continue
            
            if not osint.cnpj_validator.validate(cnpj):
                print("❌ CNPJ inválido")
                input("Enter para continuar...")
                continue
            
            print(f"\nConsultando {osint.cnpj_validator.format(cnpj)}...")
            result = osint.query_cnpj(cnpj)
            
            if result:
                print(f"\n🏢 EMPRESA:")
                print(f"   CNPJ: {osint.cnpj_validator.format(result.cnpj)}")
                print(f"   Razão Social: {result.razao_social}")
                print(f"   Nome Fantasia: {result.nome_fantasia or 'N/A'}")
                print(f"   Situação: {result.situacao}")
                print(f"   Data Abertura: {result.data_abertura}")
                print(f"   Natureza Jurídica: {result.natureza_juridica}")
                
                print(f"\n   📍 ENDEREÇO:")
                end = result.endereco
                print(f"      {end.get('logradouro')}, {end.get('numero')}")
                print(f"      {end.get('bairro')} - {end.get('municipio')}/{end.get('uf')}")
                print(f"      CEP: {end.get('cep')}")
                
                print(f"\n   📞 CONTATO:")
                print(f"      Telefone: {result.telefone or 'N/A'}")
                print(f"      Email: {result.email or 'N/A'}")
                
                print(f"\n   💰 CAPITAL SOCIAL: R$ {result.capital_social:,.2f}")
                
                print(f"\n   🏭 ATIVIDADE PRINCIPAL:")
                print(f"      {result.atividade_principal}")
                
                if result.socios:
                    print(f"\n   👥 SÓCIOS ({len(result.socios)}):")
                    for socio in result.socios[:5]:
                        print(f"      • {socio.get('nome')} ({socio.get('qualificacao')})")
                
                save = input("\nSalvar resultado? (s/n): ").lower()
                if save == 's':
                    filename = f"cnpj_{osint.cnpj_validator.clean(cnpj)}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
                    print(f"✅ Salvo em {filename}")
            else:
                print("❌ Não foi possível obter informações do CNPJ")
        
        elif escolha == '2':
            print("\n=== Validar CNPJ ===")
            cnpj = input("CNPJ: ").strip()
            
            if osint.cnpj_validator.validate(cnpj):
                formatted = osint.cnpj_validator.format(cnpj)
                print(f"\n✅ CNPJ VÁLIDO: {formatted}")
            else:
                print(f"\n❌ CNPJ INVÁLIDO")
        
        elif escolha == '3':
            print("\n=== Validar CPF ===")
            cpf = input("CPF: ").strip()
            
            if osint.cpf_validator.validate(cpf):
                formatted = osint.cpf_validator.format(cpf)
                print(f"\n✅ CPF VÁLIDO: {formatted}")
            else:
                print(f"\n❌ CPF INVÁLIDO")
        
        elif escolha == '4':
            print("\n=== Consultar CEP ===")
            cep = input("CEP: ").strip()
            
            if not cep:
                continue
            
            result = osint.query_cep(cep)
            
            if result:
                print(f"\n📍 CEP {cep}:")
                print(f"   Logradouro: {result.get('logradouro', result.get('street', 'N/A'))}")
                print(f"   Bairro: {result.get('bairro', result.get('neighborhood', 'N/A'))}")
                print(f"   Cidade: {result.get('localidade', result.get('city', 'N/A'))}")
                print(f"   Estado: {result.get('uf', result.get('state', 'N/A'))}")
                
                if result.get('location'):
                    loc = result['location']
                    coords = loc.get('coordinates', {})
                    if coords:
                        print(f"   Coordenadas: {coords.get('latitude')}, {coords.get('longitude')}")
            else:
                print("❌ CEP não encontrado")
        
        elif escolha == '5':
            print("\n=== Consultar Banco ===")
            print("Digite o código do banco (ex: 001 para BB, 237 para Bradesco)")
            code = input("Código: ").strip()
            
            if not code:
                # Listar alguns bancos
                print("\nListando bancos principais...")
                banks = osint.list_banks()[:20]
                for bank in banks:
                    print(f"   {bank.get('code', 'N/A'):>4} - {bank.get('name', 'N/A')}")
            else:
                result = osint.query_bank(code)
                if result:
                    print(f"\n🏦 BANCO:")
                    print(f"   Código: {result.get('code')}")
                    print(f"   Nome: {result.get('name')}")
                    print(f"   Nome Completo: {result.get('fullName', 'N/A')}")
                    print(f"   ISPB: {result.get('ispb', 'N/A')}")
                else:
                    print("❌ Banco não encontrado")
        
        elif escolha == '6':
            print("\n=== Consultar DDD ===")
            ddd = input("DDD (ex: 11, 21): ").strip()
            
            if not ddd:
                continue
            
            result = osint.query_ddd(ddd)
            
            if result:
                print(f"\n📞 DDD {ddd}:")
                print(f"   Estado: {result.get('state')}")
                cities = result.get('cities', [])
                print(f"   Cidades ({len(cities)}):")
                for city in cities[:15]:
                    print(f"      • {city}")
                if len(cities) > 15:
                    print(f"      ... e mais {len(cities) - 15} cidades")
            else:
                print("❌ DDD não encontrado")
        
        elif escolha == '7':
            print("\n=== Feriados Nacionais ===")
            ano = input(f"Ano (default: {datetime.now().year}): ").strip()
            ano = int(ano) if ano.isdigit() else datetime.now().year
            
            feriados = osint.query_feriados(ano)
            
            if feriados:
                print(f"\n📅 Feriados Nacionais de {ano}:")
                for f in feriados:
                    print(f"   {f.get('date')} - {f.get('name')} ({f.get('type')})")
            else:
                print("❌ Não foi possível obter feriados")
        
        elif escolha == '8':
            print("\n=== Consulta em Lote ===")
            print("Digite os CNPJs (um por linha, linha vazia para terminar):")
            
            cnpjs = []
            while True:
                c = input("  > ").strip()
                if not c:
                    break
                cnpjs.append(c)
            
            if not cnpjs:
                continue
            
            print(f"\nConsultando {len(cnpjs)} CNPJs...\n")
            
            results = []
            for cnpj in cnpjs:
                if not osint.cnpj_validator.validate(cnpj):
                    print(f"❌ {cnpj} - INVÁLIDO")
                    continue
                
                print(f"Consultando {osint.cnpj_validator.format(cnpj)}...", end=" ")
                result = osint.query_cnpj(cnpj)
                
                if result:
                    print(f"✅ {result.razao_social[:40]}")
                    results.append(result.to_dict())
                else:
                    print("❌ Não encontrado")
            
            if results:
                save = input("\nSalvar resultados? (s/n): ").lower()
                if save == 's':
                    with open("cnpj_lote.json", 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)
                    print("✅ Salvo em cnpj_lote.json")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
