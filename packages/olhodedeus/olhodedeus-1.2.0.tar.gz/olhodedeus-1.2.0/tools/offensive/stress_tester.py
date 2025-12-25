#!/usr/bin/env python3
"""
Stress Tester - Olho de Deus
Ferramenta de teste de carga para aplicações web
USO APENAS EM APLICAÇÕES PRÓPRIAS OU COM AUTORIZAÇÃO
"""

import socket
import threading
import requests
import time
import statistics
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse

# Adicionar path para imports locais
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from tools.utilities.progress_bar import ProgressBar, Spinner
except ImportError:
    # Fallback caso não encontre o módulo
    ProgressBar = None
    Spinner = None


@dataclass
class RequestResult:
    """Resultado de uma requisição"""
    status_code: int
    response_time: float  # em ms
    success: bool
    error: str = ""
    size: int = 0


@dataclass
class StressTestResult:
    """Resultado do teste de stress"""
    target: str
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    total_time: float = 0.0
    requests_per_second: float = 0.0
    avg_response_time: float = 0.0
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    p50_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    status_codes: Dict[int, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class StressTester:
    """Testador de stress/carga para aplicações web"""
    
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'StressTester/1.0 (Load Testing Tool)'
        })
        self._stop_event = threading.Event()
        self.results: List[RequestResult] = []
        self._lock = threading.Lock()
    
    def test(self, url: str, requests_count: int = 100, 
             threads: int = 10, method: str = "GET",
             data: Dict = None, headers: Dict = None) -> StressTestResult:
        """
        Executa teste de carga
        
        Args:
            url: URL alvo (sua aplicação)
            requests_count: Número total de requisições
            threads: Número de threads paralelas
            method: Método HTTP (GET, POST, etc)
            data: Dados para POST/PUT
            headers: Headers customizados
        """
        
        # Validação
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            print("❌ URL inválida")
            return StressTestResult(target=url)
        
        # Confirmação de segurança
        print("\n" + "=" * 50)
        print("⚠️  STRESS TESTER - AVISO LEGAL")
        print("=" * 50)
        print(f"Alvo: {url}")
        print(f"Requisições: {requests_count}")
        print(f"Threads: {threads}")
        print("\n⚠️  Use APENAS em aplicações que você possui")
        print("   ou tem autorização explícita para testar!")
        print("=" * 50)
        
        confirm = input("\nDigite 'CONFIRMO' para continuar: ").strip()
        if confirm != "CONFIRMO":
            print("❌ Teste cancelado")
            return StressTestResult(target=url)
        
        print(f"\n🚀 Iniciando teste de carga: {url}")
        print(f"   Requisições: {requests_count}")
        print(f"   Threads: {threads}")
        print("-" * 50)
        
        self.results = []
        self._stop_event.clear()
        
        start_time = time.time()
        
        # Criar barra de progresso (usa estilo configurado pelo usuário)
        if ProgressBar:
            pbar = ProgressBar(
                requests_count, 
                "   Progresso",
                show_percentage=True,
                show_speed=True,
                show_eta=True
            )
        
        # Executar requisições em paralelo
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = []
            
            for i in range(requests_count):
                if self._stop_event.is_set():
                    break
                    
                futures.append(
                    executor.submit(
                        self._make_request, 
                        url, method, data, headers
                    )
                )
            
            # Coletar resultados
            completed = 0
            for future in as_completed(futures):
                if self._stop_event.is_set():
                    break
                    
                try:
                    result = future.result()
                    with self._lock:
                        self.results.append(result)
                    
                    completed += 1
                    
                    # Atualizar progresso
                    if ProgressBar:
                        pbar.set(completed)
                    else:
                        if completed % 10 == 0:
                            print(f"\r   Progresso: {completed}/{requests_count}", end="", flush=True)
                        
                except Exception as e:
                    with self._lock:
                        self.results.append(RequestResult(
                            status_code=0,
                            response_time=0,
                            success=False,
                            error=str(e)
                        ))
        
        total_time = time.time() - start_time
        
        # Finalizar barra de progresso
        if ProgressBar:
            pbar.finish("Teste concluído!")
        else:
            print(f"\r   Progresso: {len(self.results)}/{requests_count} ✅")
        
        # Calcular estatísticas
        result = self._calculate_stats(url, total_time)
        
        # Mostrar resultados
        self._print_results(result)
        
        return result
    
    def _make_request(self, url: str, method: str, 
                      data: Dict, headers: Dict) -> RequestResult:
        """Faz uma requisição individual"""
        start = time.time()
        
        try:
            if headers:
                self.session.headers.update(headers)
            
            if method.upper() == "GET":
                resp = self.session.get(url, timeout=self.timeout)
            elif method.upper() == "POST":
                resp = self.session.post(url, json=data, timeout=self.timeout)
            elif method.upper() == "PUT":
                resp = self.session.put(url, json=data, timeout=self.timeout)
            elif method.upper() == "DELETE":
                resp = self.session.delete(url, timeout=self.timeout)
            else:
                resp = self.session.get(url, timeout=self.timeout)
            
            elapsed = (time.time() - start) * 1000  # ms
            
            return RequestResult(
                status_code=resp.status_code,
                response_time=elapsed,
                success=200 <= resp.status_code < 400,
                size=len(resp.content)
            )
            
        except requests.exceptions.Timeout:
            return RequestResult(
                status_code=0,
                response_time=(time.time() - start) * 1000,
                success=False,
                error="Timeout"
            )
        except requests.exceptions.ConnectionError:
            return RequestResult(
                status_code=0,
                response_time=(time.time() - start) * 1000,
                success=False,
                error="Connection Error"
            )
        except Exception as e:
            return RequestResult(
                status_code=0,
                response_time=(time.time() - start) * 1000,
                success=False,
                error=str(e)
            )
    
    def _calculate_stats(self, url: str, total_time: float) -> StressTestResult:
        """Calcula estatísticas do teste"""
        result = StressTestResult(target=url)
        
        result.total_requests = len(self.results)
        result.total_time = total_time
        
        if not self.results:
            return result
        
        # Contadores
        result.successful = sum(1 for r in self.results if r.success)
        result.failed = result.total_requests - result.successful
        
        # RPS
        if total_time > 0:
            result.requests_per_second = result.total_requests / total_time
        
        # Tempos de resposta (apenas sucesso)
        success_times = [r.response_time for r in self.results if r.success]
        
        if success_times:
            result.avg_response_time = statistics.mean(success_times)
            result.min_response_time = min(success_times)
            result.max_response_time = max(success_times)
            
            sorted_times = sorted(success_times)
            n = len(sorted_times)
            result.p50_response_time = sorted_times[int(n * 0.50)]
            result.p95_response_time = sorted_times[int(n * 0.95)]
            result.p99_response_time = sorted_times[min(int(n * 0.99), n - 1)]
        
        # Status codes
        for r in self.results:
            if r.status_code > 0:
                result.status_codes[r.status_code] = result.status_codes.get(r.status_code, 0) + 1
        
        # Erros
        result.errors = list(set(r.error for r in self.results if r.error))
        
        return result
    
    def _print_results(self, result: StressTestResult):
        """Imprime resultados formatados"""
        print("\n" + "=" * 50)
        print("📊 RESULTADOS DO TESTE")
        print("=" * 50)
        
        success_rate = (result.successful / result.total_requests * 100) if result.total_requests > 0 else 0
        
        print(f"\n📈 Resumo:")
        print(f"   Total de requisições: {result.total_requests}")
        print(f"   Sucesso: {result.successful} ({success_rate:.1f}%)")
        print(f"   Falhas: {result.failed}")
        print(f"   Tempo total: {result.total_time:.2f}s")
        print(f"   Req/segundo: {result.requests_per_second:.2f}")
        
        print(f"\n⏱️  Tempos de Resposta:")
        print(f"   Mínimo: {result.min_response_time:.2f}ms")
        print(f"   Máximo: {result.max_response_time:.2f}ms")
        print(f"   Média: {result.avg_response_time:.2f}ms")
        print(f"   P50: {result.p50_response_time:.2f}ms")
        print(f"   P95: {result.p95_response_time:.2f}ms")
        print(f"   P99: {result.p99_response_time:.2f}ms")
        
        if result.status_codes:
            print(f"\n📋 Status Codes:")
            for code, count in sorted(result.status_codes.items()):
                desc = self._get_status_description(code)
                print(f"   {code}: {count} {desc}")
        
        if result.errors:
            print(f"\n❌ Erros encontrados:")
            for error in result.errors[:5]:
                print(f"   • {error}")
        
        # Análise
        print(f"\n💡 Análise:")
        
        # Verificar se há problemas específicos de método HTTP
        if 405 in result.status_codes:
            print("   ⚠️  405 Method Not Allowed - O servidor não aceita este método HTTP")
            print("      💡 Tente usar POST ao invés de GET, ou vice-versa")
        if 401 in result.status_codes or 403 in result.status_codes:
            print("   🔒 Autenticação necessária - O endpoint requer login/API key")
        if 404 in result.status_codes:
            print("   ❌ 404 Not Found - URL incorreta ou recurso não existe")
        if 500 in result.status_codes or 502 in result.status_codes or 503 in result.status_codes:
            print("   💥 Erros de servidor - O servidor está tendo problemas sob carga")
        
        # Análise geral apenas se não houver erros específicos acima
        if not any(code in result.status_codes for code in [405, 401, 403, 404]):
            if success_rate >= 99:
                print("   ✅ Aplicação muito estável")
            elif success_rate >= 95:
                print("   ✅ Aplicação estável")
            elif success_rate >= 90:
                print("   ⚠️ Algumas falhas sob carga")
            else:
                print("   ❌ Aplicação instável sob carga")
        
        if result.avg_response_time < 100:
            print("   ✅ Tempo de resposta excelente")
    
    def _get_status_description(self, code: int) -> str:
        """Retorna descrição do status code"""
        descriptions = {
            200: "(OK)",
            201: "(Created)",
            204: "(No Content)",
            301: "(Moved Permanently)",
            302: "(Found/Redirect)",
            304: "(Not Modified)",
            400: "(Bad Request)",
            401: "(Unauthorized - Requer autenticação)",
            403: "(Forbidden - Sem permissão)",
            404: "(Not Found - URL não existe)",
            405: "(Method Not Allowed - Método HTTP errado)",
            408: "(Request Timeout)",
            429: "(Too Many Requests - Rate Limited)",
            500: "(Internal Server Error)",
            502: "(Bad Gateway)",
            503: "(Service Unavailable)",
            504: "(Gateway Timeout)",
        }
        return descriptions.get(code, "")
    
    def stop(self):
        """Para o teste"""
        self._stop_event.set()
    
    def ramp_up_test(self, url: str, max_threads: int = 50, 
                     step: int = 10, duration_per_step: int = 10) -> List[StressTestResult]:
        """
        Teste de rampa - aumenta carga gradualmente
        
        Args:
            url: URL alvo
            max_threads: Máximo de threads
            step: Incremento de threads por etapa
            duration_per_step: Segundos por etapa
        """
        print("\n🔄 Teste de Rampa")
        print(f"   Aumentando de 1 até {max_threads} threads")
        print(f"   Step: {step} threads")
        print(f"   Duração por step: {duration_per_step}s")
        
        confirm = input("\nDigite 'CONFIRMO' para continuar: ").strip()
        if confirm != "CONFIRMO":
            print("❌ Teste cancelado")
            return []
        
        results = []
        
        for threads in range(step, max_threads + 1, step):
            print(f"\n--- {threads} threads ---")
            
            # Calcular requisições baseado em tempo e threads
            requests_count = threads * duration_per_step
            
            # Teste simplificado sem confirmação
            self.results = []
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=threads) as executor:
                futures = [
                    executor.submit(self._make_request, url, "GET", None, None)
                    for _ in range(requests_count)
                ]
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        self.results.append(result)
                    except:
                        pass
            
            total_time = time.time() - start_time
            result = self._calculate_stats(url, total_time)
            results.append(result)
            
            print(f"   RPS: {result.requests_per_second:.1f}")
            print(f"   Avg: {result.avg_response_time:.1f}ms")
            print(f"   Success: {result.successful}/{result.total_requests}")
            
            # Verificar se aplicação está falhando
            if result.successful / result.total_requests < 0.5:
                print("   ⚠️ Taxa de sucesso baixa, parando rampa")
                break
        
        return results


def interactive_menu():
    """Menu interativo para integração com Olho de Deus"""
    import os
    
    def limpar_tela():
        os.system('cls' if os.name == 'nt' else 'clear')
    
    while True:
        limpar_tela()
        print("""
\033[91m╔══════════════════════════════════════════════════════════════╗
║\033[0m              \033[1;31m🔥 STRESS TESTER\033[0m                                \033[91m║
╠══════════════════════════════════════════════════════════════╣\033[0m
║                                                              ║
║  \033[93m[1]\033[0m 🚀 Teste de Carga (GET)                                 ║
║  \033[93m[2]\033[0m 📤 Teste de Carga (POST)                                ║
║  \033[93m[3]\033[0m 🔄 Teste com Método Customizado                         ║
║  \033[93m[4]\033[0m 📈 Teste de Rampa (Ramp-Up)                             ║
║  \033[93m[5]\033[0m 📝 Teste POST com Dados JSON                            ║
║                                                              ║
║  \033[91m[0]\033[0m Voltar                                                  ║
\033[91m╚══════════════════════════════════════════════════════════════╝\033[0m

\033[93m⚠️  USE APENAS EM APLICAÇÕES PRÓPRIAS OU COM AUTORIZAÇÃO!\033[0m
        """)
        
        escolha = input("\033[92mOpção: \033[0m").strip()
        
        if escolha == '0':
            break
        elif escolha == '1':
            # Teste GET
            url = input("\n🌐 URL para testar (GET): ").strip()
            if not url:
                continue
            
            try:
                requests_count = int(input("📊 Número de requisições [100]: ").strip() or "100")
                threads = int(input("🔀 Número de threads [10]: ").strip() or "10")
            except ValueError:
                requests_count = 100
                threads = 10
            
            requests_count = min(requests_count, 1000)
            threads = min(threads, 50)
            
            tester = StressTester()
            try:
                tester.test(url, requests_count, threads, method="GET")
            except KeyboardInterrupt:
                print("\n⚠️ Teste interrompido!")
            
            input("\nPressione Enter para continuar...")
            
        elif escolha == '2':
            # Teste POST
            url = input("\n🌐 URL para testar (POST): ").strip()
            if not url:
                continue
            
            try:
                requests_count = int(input("📊 Número de requisições [100]: ").strip() or "100")
                threads = int(input("🔀 Número de threads [10]: ").strip() or "10")
            except ValueError:
                requests_count = 100
                threads = 10
            
            requests_count = min(requests_count, 1000)
            threads = min(threads, 50)
            
            tester = StressTester()
            try:
                tester.test(url, requests_count, threads, method="POST")
            except KeyboardInterrupt:
                print("\n⚠️ Teste interrompido!")
            
            input("\nPressione Enter para continuar...")
            
        elif escolha == '3':
            # Método customizado
            url = input("\n🌐 URL para testar: ").strip()
            if not url:
                continue
            
            print("\n📋 Métodos disponíveis: GET, POST, PUT, DELETE, HEAD, OPTIONS")
            method = input("🔧 Método HTTP [GET]: ").strip().upper() or "GET"
            
            try:
                requests_count = int(input("📊 Número de requisições [100]: ").strip() or "100")
                threads = int(input("🔀 Número de threads [10]: ").strip() or "10")
            except ValueError:
                requests_count = 100
                threads = 10
            
            requests_count = min(requests_count, 1000)
            threads = min(threads, 50)
            
            tester = StressTester()
            try:
                tester.test(url, requests_count, threads, method=method)
            except KeyboardInterrupt:
                print("\n⚠️ Teste interrompido!")
            
            input("\nPressione Enter para continuar...")
            
        elif escolha == '4':
            # Teste de rampa
            url = input("\n🌐 URL para testar: ").strip()
            if not url:
                continue
            
            try:
                max_threads = int(input("🔀 Máximo de threads [50]: ").strip() or "50")
                step = int(input("📈 Step de incremento [10]: ").strip() or "10")
            except ValueError:
                max_threads = 50
                step = 10
            
            max_threads = min(max_threads, 100)
            
            tester = StressTester()
            try:
                tester.ramp_up_test(url, max_threads, step)
            except KeyboardInterrupt:
                print("\n⚠️ Teste interrompido!")
            
            input("\nPressione Enter para continuar...")
            
        elif escolha == '5':
            # Teste POST com dados
            url = input("\n🌐 URL para testar (POST): ").strip()
            if not url:
                continue
            
            print("📝 Digite os dados JSON (ex: {\"key\": \"value\"}):")
            data_str = input().strip()
            
            try:
                import json
                data = json.loads(data_str) if data_str else {}
            except:
                print("❌ JSON inválido, usando dados vazios")
                data = {}
            
            try:
                requests_count = int(input("📊 Número de requisições [100]: ").strip() or "100")
                threads = int(input("🔀 Número de threads [10]: ").strip() or "10")
            except ValueError:
                requests_count = 100
                threads = 10
            
            requests_count = min(requests_count, 1000)
            threads = min(threads, 50)
            
            tester = StressTester()
            try:
                tester.test(url, requests_count, threads, method="POST", data=data)
            except KeyboardInterrupt:
                print("\n⚠️ Teste interrompido!")
            
            input("\nPressione Enter para continuar...")
        else:
            input("Opção inválida. Pressione Enter...")


def main():
    """Função principal"""
    print("\n" + "=" * 50)
    print("🔧 Stress Tester - Olho de Deus")
    print("=" * 50)
    print("\n⚠️  APENAS PARA TESTES EM APLICAÇÕES PRÓPRIAS")
    
    if len(sys.argv) < 2:
        url = input("\n🌐 URL para testar: ").strip()
    else:
        url = sys.argv[1]
    
    # Parâmetros
    try:
        requests_count = int(input("📊 Número de requisições [100]: ").strip() or "100")
        threads = int(input("🔀 Número de threads [10]: ").strip() or "10")
    except ValueError:
        requests_count = 100
        threads = 10
    
    # Limites de segurança
    requests_count = min(requests_count, 1000)
    threads = min(threads, 50)
    
    tester = StressTester()
    
    try:
        result = tester.test(url, requests_count, threads)
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido!")
        tester.stop()
    
    print("\n✅ Teste concluído!")


if __name__ == "__main__":
    main()
