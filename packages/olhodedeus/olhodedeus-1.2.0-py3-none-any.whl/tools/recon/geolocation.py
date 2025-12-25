#!/usr/bin/env python3
"""
geolocation.py

Ferramentas de geolocalização para IPs, coordenadas e endereços.
"""
import os
import re
import json
import requests
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from math import radians, sin, cos, sqrt, atan2


@dataclass
class GeoLocation:
    """Dados de geolocalização."""
    ip: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    country: str = ""
    country_code: str = ""
    region: str = ""
    city: str = ""
    zip_code: str = ""
    timezone: str = ""
    isp: str = ""
    org: str = ""
    asn: str = ""


class IPGeolocation:
    """Geolocalização de IPs."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_my_ip(self) -> str:
        """Obtém IP público atual."""
        apis = [
            'https://api.ipify.org?format=json',
            'https://api.my-ip.io/ip.json',
            'https://ip.seeip.org/json',
        ]
        
        for api in apis:
            try:
                resp = self.session.get(api, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get('ip', data.get('IP', ''))
            except:
                continue
        return ''
    
    def geolocate_ip_api(self, ip: str) -> GeoLocation:
        """Geolocaliza usando ip-api.com (grátis, 45/min)."""
        try:
            resp = self.session.get(
                f'http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as',
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == 'success':
                    return GeoLocation(
                        ip=ip,
                        latitude=data.get('lat', 0),
                        longitude=data.get('lon', 0),
                        country=data.get('country', ''),
                        country_code=data.get('countryCode', ''),
                        region=data.get('regionName', ''),
                        city=data.get('city', ''),
                        zip_code=data.get('zip', ''),
                        timezone=data.get('timezone', ''),
                        isp=data.get('isp', ''),
                        org=data.get('org', ''),
                        asn=data.get('as', ''),
                    )
        except:
            pass
        return GeoLocation(ip=ip)
    
    def geolocate_ipinfo(self, ip: str, token: str = None) -> GeoLocation:
        """Geolocaliza usando ipinfo.io."""
        try:
            url = f'https://ipinfo.io/{ip}/json'
            if token:
                url += f'?token={token}'
            
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                loc = data.get('loc', '0,0').split(',')
                return GeoLocation(
                    ip=ip,
                    latitude=float(loc[0]) if len(loc) > 0 else 0,
                    longitude=float(loc[1]) if len(loc) > 1 else 0,
                    country=data.get('country', ''),
                    region=data.get('region', ''),
                    city=data.get('city', ''),
                    zip_code=data.get('postal', ''),
                    timezone=data.get('timezone', ''),
                    org=data.get('org', ''),
                )
        except:
            pass
        return GeoLocation(ip=ip)
    
    def geolocate_multiple(self, ip: str) -> Dict[str, GeoLocation]:
        """Geolocaliza usando múltiplas APIs."""
        results = {}
        
        results['ip-api'] = self.geolocate_ip_api(ip)
        results['ipinfo'] = self.geolocate_ipinfo(ip)
        
        return results
    
    def batch_geolocate(self, ips: List[str]) -> List[GeoLocation]:
        """Geolocaliza múltiplos IPs."""
        # ip-api suporta batch (max 100)
        try:
            resp = self.session.post(
                'http://ip-api.com/batch',
                json=[{'query': ip} for ip in ips[:100]],
                timeout=30
            )
            if resp.status_code == 200:
                results = []
                for data in resp.json():
                    if data.get('status') == 'success':
                        results.append(GeoLocation(
                            ip=data.get('query', ''),
                            latitude=data.get('lat', 0),
                            longitude=data.get('lon', 0),
                            country=data.get('country', ''),
                            country_code=data.get('countryCode', ''),
                            region=data.get('regionName', ''),
                            city=data.get('city', ''),
                            isp=data.get('isp', ''),
                        ))
                return results
        except:
            pass
        return []


class CoordinateTools:
    """Ferramentas para coordenadas."""
    
    @staticmethod
    def parse_coordinates(coord_string: str) -> Tuple[float, float]:
        """Parse de coordenadas em vários formatos."""
        # Formato: "lat, lon" ou "lat lon"
        match = re.match(r'(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)', coord_string)
        if match:
            return float(match.group(1)), float(match.group(2))
        
        # Formato DMS: 40°26'46"N 79°58'56"W
        dms_pattern = r"(\d+)°(\d+)'(\d+(?:\.\d+)?)\"([NSEW])"
        matches = re.findall(dms_pattern, coord_string.upper())
        if len(matches) >= 2:
            lat = CoordinateTools._dms_to_decimal(*matches[0])
            lon = CoordinateTools._dms_to_decimal(*matches[1])
            return lat, lon
        
        return 0, 0
    
    @staticmethod
    def _dms_to_decimal(degrees: str, minutes: str, seconds: str, direction: str) -> float:
        """Converte DMS para decimal."""
        decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
        if direction in ['S', 'W']:
            decimal = -decimal
        return decimal
    
    @staticmethod
    def decimal_to_dms(lat: float, lon: float) -> str:
        """Converte decimal para DMS."""
        def to_dms(coord: float, is_lat: bool) -> str:
            direction = ('N' if coord >= 0 else 'S') if is_lat else ('E' if coord >= 0 else 'W')
            coord = abs(coord)
            degrees = int(coord)
            minutes = int((coord - degrees) * 60)
            seconds = (coord - degrees - minutes / 60) * 3600
            return f"{degrees}°{minutes}'{seconds:.2f}\"{direction}"
        
        return f"{to_dms(lat, True)} {to_dms(lon, False)}"
    
    @staticmethod
    def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distância entre duas coordenadas em km (Haversine)."""
        R = 6371  # Raio da Terra em km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
    
    @staticmethod
    def generate_map_urls(lat: float, lon: float) -> Dict[str, str]:
        """Gera URLs de mapas para coordenadas."""
        return {
            'google_maps': f'https://www.google.com/maps?q={lat},{lon}',
            'google_earth': f'https://earth.google.com/web/@{lat},{lon},1000a,35y,0h,0t,0r',
            'openstreetmap': f'https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=15',
            'bing_maps': f'https://www.bing.com/maps?cp={lat}~{lon}&lvl=15',
            'yandex_maps': f'https://yandex.com/maps/?pt={lon},{lat}&z=15',
            'apple_maps': f'https://maps.apple.com/?ll={lat},{lon}&z=15',
        }


class GeoCoding:
    """Geocodificação (endereço <-> coordenadas)."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def geocode_nominatim(self, address: str) -> Dict:
        """Geocodifica endereço usando Nominatim (OpenStreetMap)."""
        try:
            resp = self.session.get(
                'https://nominatim.openstreetmap.org/search',
                params={'q': address, 'format': 'json', 'limit': 5},
                timeout=10
            )
            if resp.status_code == 200:
                results = resp.json()
                if results:
                    return {
                        'results': [
                            {
                                'display_name': r.get('display_name'),
                                'lat': float(r.get('lat', 0)),
                                'lon': float(r.get('lon', 0)),
                                'type': r.get('type'),
                            }
                            for r in results
                        ]
                    }
        except:
            pass
        return {'error': 'Não encontrado'}
    
    def reverse_geocode(self, lat: float, lon: float) -> Dict:
        """Geocodificação reversa (coordenadas -> endereço)."""
        try:
            resp = self.session.get(
                'https://nominatim.openstreetmap.org/reverse',
                params={'lat': lat, 'lon': lon, 'format': 'json'},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    'display_name': data.get('display_name'),
                    'address': data.get('address', {}),
                }
        except:
            pass
        return {'error': 'Não encontrado'}


class WifiGeolocation:
    """Geolocalização por BSSID de WiFi."""
    
    def __init__(self):
        self.session = requests.Session()
    
    def lookup_wigle(self, bssid: str, api_token: str = None) -> Dict:
        """Busca localização de BSSID no WiGLE."""
        if not api_token:
            return {'error': 'API token WiGLE necessário', 'signup': 'https://wigle.net/'}
        
        try:
            resp = self.session.get(
                'https://api.wigle.net/api/v2/network/search',
                params={'netid': bssid},
                headers={'Authorization': f'Basic {api_token}'},
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return {'error': 'Não encontrado'}


def interactive_menu():
    """Menu interativo."""
    ip_geo = IPGeolocation()
    coord_tools = CoordinateTools()
    geocoding = GeoCoding()
    
    # Config
    config_path = "config/geolocation.json"
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("""
╔══════════════════════════════════════════════════════════════╗
║                  📍 GEOLOCATION TOOLS                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ──── 🌐 IP GEOLOCATION ────                                 ║
║  [1] 🔍 Meu IP Público                                       ║
║  [2] 📍 Geolocalizar IP                                      ║
║  [3] 📋 Geolocalização em Lote                               ║
║                                                              ║
║  ──── 🗺️ COORDENADAS ────                                    ║
║  [4] 📍 Converter Coordenadas (Decimal ↔ DMS)                ║
║  [5] 📏 Calcular Distância                                   ║
║  [6] 🗺️  Gerar Links de Mapas                                ║
║                                                              ║
║  ──── 🏠 GEOCODING ────                                      ║
║  [7] 🔍 Endereço → Coordenadas                               ║
║  [8] 🔍 Coordenadas → Endereço                               ║
║                                                              ║
║  ──── ⚙️ CONFIG ────                                          ║
║  [9] ⚙️  Configurar APIs                                      ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            print("\n🔍 Obtendo IP público...")
            ip = ip_geo.get_my_ip()
            if ip:
                print(f"\n   📍 Seu IP: {ip}")
                
                geo = ip_geo.geolocate_ip_api(ip)
                print(f"\n   🌍 Localização:")
                print(f"      País: {geo.country} ({geo.country_code})")
                print(f"      Região: {geo.region}")
                print(f"      Cidade: {geo.city}")
                print(f"      Coordenadas: {geo.latitude}, {geo.longitude}")
                print(f"      ISP: {geo.isp}")
                print(f"      Timezone: {geo.timezone}")
            else:
                print("❌ Não foi possível obter IP")
            input("\nPressione Enter...")
        
        elif choice == '2':
            ip = input("\n🌐 IP: ").strip()
            if ip:
                geo = ip_geo.geolocate_ip_api(ip)
                
                print(f"\n📍 GEOLOCALIZAÇÃO DE {ip}:\n")
                print(f"   País: {geo.country} ({geo.country_code})")
                print(f"   Região: {geo.region}")
                print(f"   Cidade: {geo.city}")
                print(f"   CEP: {geo.zip_code}")
                print(f"   Coordenadas: {geo.latitude}, {geo.longitude}")
                print(f"   ISP: {geo.isp}")
                print(f"   Org: {geo.org}")
                print(f"   ASN: {geo.asn}")
                print(f"   Timezone: {geo.timezone}")
                
                urls = coord_tools.generate_map_urls(geo.latitude, geo.longitude)
                print(f"\n   🗺️ Ver no mapa:")
                print(f"      {urls['google_maps']}")
            input("\nPressione Enter...")
        
        elif choice == '3':
            print("\n📋 Digite os IPs (um por linha, vazio para terminar):")
            ips = []
            while True:
                ip = input("   ").strip()
                if not ip:
                    break
                ips.append(ip)
            
            if ips:
                results = ip_geo.batch_geolocate(ips)
                print(f"\n📍 RESULTADOS:\n")
                for geo in results:
                    print(f"   {geo.ip}: {geo.city}, {geo.country} ({geo.latitude}, {geo.longitude})")
            input("\nPressione Enter...")
        
        elif choice == '4':
            coord = input("\nCoordenadas (ex: -23.5505, -46.6333 ou 23°33'N 46°38'W): ").strip()
            if coord:
                lat, lon = coord_tools.parse_coordinates(coord)
                if lat or lon:
                    print(f"\n   Decimal: {lat}, {lon}")
                    print(f"   DMS: {coord_tools.decimal_to_dms(lat, lon)}")
                else:
                    print("❌ Formato não reconhecido")
            input("\nPressione Enter...")
        
        elif choice == '5':
            print("\nPonto 1:")
            lat1 = float(input("   Latitude: ") or 0)
            lon1 = float(input("   Longitude: ") or 0)
            print("Ponto 2:")
            lat2 = float(input("   Latitude: ") or 0)
            lon2 = float(input("   Longitude: ") or 0)
            
            dist = coord_tools.distance_km(lat1, lon1, lat2, lon2)
            print(f"\n   📏 Distância: {dist:.2f} km ({dist * 0.621371:.2f} milhas)")
            input("\nPressione Enter...")
        
        elif choice == '6':
            lat = float(input("\nLatitude: ") or 0)
            lon = float(input("Longitude: ") or 0)
            
            urls = coord_tools.generate_map_urls(lat, lon)
            print(f"\n🗺️ LINKS DE MAPAS:\n")
            for service, url in urls.items():
                print(f"   {service}: {url}")
            input("\nPressione Enter...")
        
        elif choice == '7':
            address = input("\n🏠 Endereço: ").strip()
            if address:
                result = geocoding.geocode_nominatim(address)
                if 'results' in result:
                    print(f"\n📍 RESULTADOS:\n")
                    for r in result['results']:
                        print(f"   {r['display_name']}")
                        print(f"      Coordenadas: {r['lat']}, {r['lon']}")
                        print()
                else:
                    print("❌ Não encontrado")
            input("\nPressione Enter...")
        
        elif choice == '8':
            lat = float(input("\nLatitude: ") or 0)
            lon = float(input("Longitude: ") or 0)
            
            result = geocoding.reverse_geocode(lat, lon)
            if 'display_name' in result:
                print(f"\n🏠 ENDEREÇO:\n")
                print(f"   {result['display_name']}")
                
                addr = result.get('address', {})
                if addr:
                    print(f"\n   Detalhes:")
                    for k, v in addr.items():
                        print(f"      {k}: {v}")
            else:
                print("❌ Não encontrado")
            input("\nPressione Enter...")
        
        elif choice == '9':
            print("\n⚙️ CONFIGURAÇÃO DE APIs\n")
            print("WiGLE: https://wigle.net/ (para BSSID lookup)")
            print("IPinfo: https://ipinfo.io/ (token opcional)")
            
            wigle = input(f"\nWiGLE API Token: ").strip()
            if wigle:
                config['wigle_token'] = wigle
            
            ipinfo = input(f"IPinfo Token: ").strip()
            if ipinfo:
                config['ipinfo_token'] = ipinfo
            
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print("✅ Salvo!")
            input("\nPressione Enter...")
        
        elif choice == '0':
            break


if __name__ == '__main__':
    interactive_menu()
