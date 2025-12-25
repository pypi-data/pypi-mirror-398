#!/usr/bin/env python3
"""
Progress Bar - Olho de Deus
Módulo de barras de progresso reutilizável para todo o projeto
"""

import sys
import os
import time
import json
import threading
from typing import Optional, Callable, Iterator, Any
from dataclasses import dataclass

# Caminho do arquivo de configuração
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'progress_bar_config.json')


def get_saved_style() -> str:
    """Retorna o estilo salvo ou 'hacker' como padrão"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('bar_style', 'hacker')
    except:
        pass
    return 'hacker'


def get_saved_spinner() -> str:
    """Retorna o spinner salvo ou 'dots' como padrão"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('spinner_style', 'dots')
    except:
        pass
    return 'dots'


def save_preferences(bar_style: str = None, spinner_style: str = None):
    """Salva as preferências do usuário"""
    try:
        # Criar diretório se não existir
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        # Carregar config existente
        config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
        
        # Atualizar valores
        if bar_style:
            config['bar_style'] = bar_style
        if spinner_style:
            config['spinner_style'] = spinner_style
        
        # Salvar
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True
    except Exception as e:
        print(f"\033[91mErro ao salvar preferências: {e}\033[0m")
        return False


@dataclass
class ProgressStyle:
    """Estilos de barra de progresso"""
    fill: str = "█"
    empty: str = "░"
    left: str = "│"
    right: str = "│"
    color_start: str = "\033[92m"  # Verde
    color_end: str = "\033[0m"
    width: int = 40


class ProgressBar:
    """Barra de progresso versátil para CLI"""
    
    # Estilos pré-definidos
    STYLES = {
        "default": ProgressStyle(),
        "minimal": ProgressStyle(fill="=", empty="-", left="[", right="]", color_start="\033[96m"),
        "blocks": ProgressStyle(fill="▓", empty="░", left="", right=""),
        "dots": ProgressStyle(fill="●", empty="○", left="", right=""),
        "arrows": ProgressStyle(fill="▶", empty="─", left="", right=""),
        "hacker": ProgressStyle(fill="█", empty="░", left="[", right="]", color_start="\033[92m"),
        "fire": ProgressStyle(fill="🔥", empty="░", left="", right="", width=20),
        "skull": ProgressStyle(fill="💀", empty="░", left="", right="", width=20),
    }
    
    def __init__(self, total: int, desc: str = "", style: str = None, 
                 show_percentage: bool = True, show_count: bool = True,
                 show_speed: bool = False, show_eta: bool = False):
        """
        Inicializa barra de progresso
        
        Args:
            total: Total de itens
            desc: Descrição/prefixo
            style: Estilo da barra (None = usa salvo, ou: default, minimal, blocks, dots, arrows, hacker, fire, skull)
            show_percentage: Mostrar porcentagem
            show_count: Mostrar contagem x/total
            show_speed: Mostrar velocidade (items/s)
            show_eta: Mostrar tempo estimado
        """
        self.total = max(total, 1)
        self.current = 0
        self.desc = desc
        # Se style for None, usa o estilo salvo
        actual_style = style if style else get_saved_style()
        self.style = self.STYLES.get(actual_style, self.STYLES["default"])
        self.show_percentage = show_percentage
        self.show_count = show_count
        self.show_speed = show_speed
        self.show_eta = show_eta
        self.start_time = time.time()
        self._lock = threading.Lock()
    
    def update(self, n: int = 1):
        """Atualiza progresso em n unidades"""
        with self._lock:
            self.current = min(self.current + n, self.total)
            self._render()
    
    def set(self, value: int):
        """Define valor absoluto do progresso"""
        with self._lock:
            self.current = min(max(value, 0), self.total)
            self._render()
    
    def _render(self):
        """Renderiza a barra de progresso"""
        s = self.style
        
        # Calcular progresso
        progress = self.current / self.total
        filled = int(s.width * progress)
        empty = s.width - filled
        
        # Construir barra
        bar = f"{s.color_start}{s.left}{s.fill * filled}{s.empty * empty}{s.right}{s.color_end}"
        
        # Construir info
        info_parts = []
        
        if self.show_percentage:
            info_parts.append(f"{progress * 100:.1f}%")
        
        if self.show_count:
            info_parts.append(f"{self.current}/{self.total}")
        
        if self.show_speed:
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                speed = self.current / elapsed
                info_parts.append(f"{speed:.1f}/s")
        
        if self.show_eta:
            elapsed = time.time() - self.start_time
            if self.current > 0:
                eta = (elapsed / self.current) * (self.total - self.current)
                if eta < 60:
                    info_parts.append(f"ETA: {eta:.0f}s")
                else:
                    info_parts.append(f"ETA: {eta/60:.1f}m")
        
        info = " ".join(info_parts)
        
        # Descrição
        desc = f"{self.desc} " if self.desc else ""
        
        # Renderizar
        line = f"\r{desc}{bar} {info}"
        sys.stdout.write(line + " " * 10)  # Padding para limpar caracteres antigos
        sys.stdout.flush()
    
    def finish(self, message: str = ""):
        """Finaliza a barra de progresso"""
        self.current = self.total
        self._render()
        
        if message:
            print(f" ✅ {message}")
        else:
            print()  # Nova linha
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.finish()


class Spinner:
    """Spinner animado para operações de duração indefinida"""
    
    SPINNERS = {
        "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
        "line": ["-", "\\", "|", "/"],
        "arrows": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
        "bounce": ["⠁", "⠂", "⠄", "⠂"],
        "clock": ["🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛"],
        "moon": ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"],
        "earth": ["🌍", "🌎", "🌏"],
        "loading": ["Loading   ", "Loading.  ", "Loading.. ", "Loading..."],
        "pulse": ["█", "▓", "▒", "░", "▒", "▓"],
        "hacker": ["[    ]", "[=   ]", "[==  ]", "[=== ]", "[====]", "[ ===]", "[  ==]", "[   =]"],
    }
    
    def __init__(self, message: str = "Carregando", spinner_type: str = None,
                 color: str = "\033[96m"):
        """
        Inicializa spinner
        
        Args:
            message: Mensagem a exibir
            spinner_type: Tipo de animação (None = usa salvo)
            color: Cor ANSI
        """
        self.message = message
        # Se spinner_type for None, usa o estilo salvo
        actual_type = spinner_type if spinner_type else get_saved_spinner()
        self.frames = self.SPINNERS.get(actual_type, self.SPINNERS["dots"])
        self.color = color
        self.reset = "\033[0m"
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.current_frame = 0
    
    def _animate(self):
        """Loop de animação"""
        while not self._stop_event.is_set():
            frame = self.frames[self.current_frame % len(self.frames)]
            sys.stdout.write(f"\r{self.color}{frame}{self.reset} {self.message}")
            sys.stdout.flush()
            self.current_frame += 1
            time.sleep(0.1)
    
    def start(self):
        """Inicia o spinner"""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        return self
    
    def stop(self, message: str = "", success: bool = True):
        """Para o spinner"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        
        # Limpar linha
        sys.stdout.write("\r" + " " * (len(self.message) + 20) + "\r")
        
        if message:
            icon = "✅" if success else "❌"
            print(f"{icon} {message}")
        sys.stdout.flush()
    
    def __enter__(self):
        return self.start()
    
    def __exit__(self, *args):
        self.stop()


class MultiProgress:
    """Múltiplas barras de progresso simultâneas"""
    
    def __init__(self):
        self.bars: dict = {}
        self._lock = threading.Lock()
    
    def add_bar(self, name: str, total: int, desc: str = "", style: str = "default"):
        """Adiciona uma nova barra"""
        self.bars[name] = {
            "total": total,
            "current": 0,
            "desc": desc or name,
            "style": ProgressBar.STYLES.get(style, ProgressBar.STYLES["default"])
        }
    
    def update(self, name: str, n: int = 1):
        """Atualiza uma barra específica"""
        with self._lock:
            if name in self.bars:
                self.bars[name]["current"] = min(
                    self.bars[name]["current"] + n,
                    self.bars[name]["total"]
                )
                self._render_all()
    
    def _render_all(self):
        """Renderiza todas as barras"""
        # Move cursor para cima e limpa
        sys.stdout.write(f"\033[{len(self.bars)}A")
        
        for name, bar in self.bars.items():
            s = bar["style"]
            progress = bar["current"] / bar["total"]
            filled = int(s.width * progress)
            empty = s.width - filled
            
            bar_str = f"{s.color_start}{s.left}{s.fill * filled}{s.empty * empty}{s.right}{s.color_end}"
            info = f"{progress * 100:.1f}% {bar['current']}/{bar['total']}"
            
            print(f"\r{bar['desc']}: {bar_str} {info}" + " " * 10)
        
        sys.stdout.flush()
    
    def finish(self):
        """Finaliza todas as barras"""
        for name in self.bars:
            self.bars[name]["current"] = self.bars[name]["total"]
        self._render_all()


def progress_iterator(iterable, desc: str = "", style: str = "default", 
                     show_speed: bool = True) -> Iterator:
    """
    Wrapper que adiciona barra de progresso a qualquer iterável
    Similar ao tqdm
    
    Uso:
        for item in progress_iterator(lista, "Processando"):
            processar(item)
    """
    # Tentar obter tamanho
    try:
        total = len(iterable)
    except TypeError:
        # Iterável sem len, converter para lista
        iterable = list(iterable)
        total = len(iterable)
    
    with ProgressBar(total, desc, style, show_speed=show_speed) as pbar:
        for item in iterable:
            yield item
            pbar.update(1)


def loading_animation(func: Callable) -> Callable:
    """
    Decorator que adiciona spinner a uma função
    
    Uso:
        @loading_animation
        def minha_funcao_lenta():
            time.sleep(3)
    """
    def wrapper(*args, **kwargs):
        with Spinner(f"Executando {func.__name__}..."):
            result = func(*args, **kwargs)
        return result
    return wrapper


# ============================================
# FUNÇÕES DE CONVENIÊNCIA
# ============================================

def show_progress(current: int, total: int, desc: str = "", style: str = "default"):
    """Função simples para mostrar progresso"""
    pbar = ProgressBar(total, desc, style)
    pbar.set(current)


def animate_loading(message: str = "Carregando", duration: float = 2.0, 
                    spinner_type: str = "dots"):
    """Mostra animação de loading por um tempo determinado"""
    spinner = Spinner(message, spinner_type)
    spinner.start()
    time.sleep(duration)
    spinner.stop("Concluído!")


def download_progress(downloaded: int, total: int, filename: str = ""):
    """Barra de progresso específica para downloads"""
    pbar = ProgressBar(
        total, 
        desc=f"📥 {filename}" if filename else "📥 Download",
        style="hacker",
        show_percentage=True,
        show_count=False,
        show_speed=True,
        show_eta=True
    )
    pbar.set(downloaded)
    
    if downloaded >= total:
        pbar.finish()


# ============================================
# DEMO E TESTES
# ============================================

def demo():
    """Demonstração de todas as funcionalidades"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("\n" + "=" * 60)
    print("🎨 DEMONSTRAÇÃO DE BARRAS DE PROGRESSO")
    print("=" * 60)
    
    # Demo estilos
    print("\n📊 Estilos de barra de progresso:\n")
    
    for style_name in ProgressBar.STYLES:
        bar = ProgressBar(100, f"  {style_name:10}", style=style_name)
        for i in range(101):
            bar.set(i)
            time.sleep(0.01)
        bar.finish()
        time.sleep(0.2)
    
    # Demo spinner
    print("\n🔄 Spinners:\n")
    
    for spinner_type in list(Spinner.SPINNERS.keys())[:5]:
        spinner = Spinner(f"Tipo: {spinner_type}", spinner_type)
        spinner.start()
        time.sleep(1.5)
        spinner.stop("OK!")
    
    # Demo com velocidade e ETA
    print("\n⏱️ Com velocidade e ETA:\n")
    
    bar = ProgressBar(
        50, 
        "  Download",
        style="hacker",
        show_speed=True,
        show_eta=True
    )
    for i in range(50):
        bar.update(1)
        time.sleep(0.05)
    bar.finish("Download completo!")
    
    print("\n" + "=" * 60)
    print("✅ Demonstração concluída!")
    print("=" * 60 + "\n")


def interactive_menu():
    """Menu interativo para demonstração e configuração"""
    import os
    
    def limpar_tela():
        os.system('cls' if os.name == 'nt' else 'clear')
    
    while True:
        limpar_tela()
        current_bar = get_saved_style()
        current_spinner = get_saved_spinner()
        
        print(f"""
\033[93m╔══════════════════════════════════════════════════════════════╗
║\033[0m              \033[1;33m📊 PROGRESS BAR - CONFIGURAÇÃO\033[0m                    \033[93m║
╠══════════════════════════════════════════════════════════════╣\033[0m
║                                                              ║
║  \033[96mEstilo atual da barra:\033[0m \033[92m{current_bar:15}\033[0m                   ║
║  \033[96mEstilo atual do spinner:\033[0m \033[92m{current_spinner:13}\033[0m                   ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  \033[93m[1]\033[0m 🎨 Selecionar estilo de barra                          ║
║  \033[93m[2]\033[0m 🔄 Selecionar estilo de spinner                        ║
║  \033[93m[3]\033[0m 📥 Testar com simulação de download                    ║
║  \033[93m[4]\033[0m 🚀 Demo completa                                       ║
║                                                              ║
║  \033[91m[0]\033[0m Voltar                                                 ║
\033[93m╚══════════════════════════════════════════════════════════════╝\033[0m
        """)
        
        escolha = input("\033[92mOpção: \033[0m").strip()
        
        if escolha == '0':
            break
        elif escolha == '1':
            select_bar_style()
        elif escolha == '2':
            select_spinner_style()
        elif escolha == '3':
            print("\n📥 Simulando download com estilo atual...\n")
            bar = ProgressBar(100, "  Baixando arquivo.zip", 
                            show_speed=True, show_eta=True)
            for i in range(100):
                bar.update(1)
                time.sleep(0.03)
            bar.finish("Download concluído!")
            input("\nPressione Enter...")
        elif escolha == '4':
            demo()
            input("\nPressione Enter...")


def select_bar_style():
    """Menu para selecionar estilo de barra"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("\n\033[93m╔══════════════════════════════════════════════════════════════╗")
    print("║\033[0m              \033[1;33m🎨 SELECIONAR ESTILO DE BARRA\033[0m                    \033[93m║")
    print("╚══════════════════════════════════════════════════════════════╝\033[0m\n")
    
    styles = list(ProgressBar.STYLES.keys())
    current = get_saved_style()
    
    for i, style_name in enumerate(styles, 1):
        marker = " \033[92m← atual\033[0m" if style_name == current else ""
        print(f"  \033[93m[{i}]\033[0m {style_name}{marker}")
        
        # Mostrar preview
        bar = ProgressBar(100, f"      Preview", style=style_name)
        for j in range(101):
            bar.set(j)
            time.sleep(0.005)
        bar.finish()
    
    print(f"\n  \033[91m[0]\033[0m Cancelar")
    
    try:
        escolha = input("\n\033[92mEscolha o estilo: \033[0m").strip()
        
        if escolha == '0':
            return
        
        idx = int(escolha) - 1
        if 0 <= idx < len(styles):
            selected = styles[idx]
            save_preferences(bar_style=selected)
            print(f"\n\033[92m✅ Estilo '{selected}' salvo com sucesso!\033[0m")
            print("\033[96mTodas as ferramentas agora usarão este estilo.\033[0m")
        else:
            print("\033[91mOpção inválida!\033[0m")
    except ValueError:
        print("\033[91mEntrada inválida!\033[0m")
    
    input("\nPressione Enter...")


def select_spinner_style():
    """Menu para selecionar estilo de spinner"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("\n\033[93m╔══════════════════════════════════════════════════════════════╗")
    print("║\033[0m              \033[1;33m🔄 SELECIONAR ESTILO DE SPINNER\033[0m                  \033[93m║")
    print("╚══════════════════════════════════════════════════════════════╝\033[0m\n")
    
    spinners = list(Spinner.SPINNERS.keys())
    current = get_saved_spinner()
    
    for i, spinner_type in enumerate(spinners, 1):
        marker = " \033[92m← atual\033[0m" if spinner_type == current else ""
        print(f"  \033[93m[{i}]\033[0m {spinner_type}{marker}")
        
        # Mostrar preview
        spinner = Spinner(f"      Preview", spinner_type)
        spinner.start()
        time.sleep(1.0)
        spinner.stop("✓")
    
    print(f"\n  \033[91m[0]\033[0m Cancelar")
    
    try:
        escolha = input("\n\033[92mEscolha o spinner: \033[0m").strip()
        
        if escolha == '0':
            return
        
        idx = int(escolha) - 1
        if 0 <= idx < len(spinners):
            selected = spinners[idx]
            save_preferences(spinner_style=selected)
            print(f"\n\033[92m✅ Spinner '{selected}' salvo com sucesso!\033[0m")
            print("\033[96mTodas as ferramentas agora usarão este spinner.\033[0m")
        else:
            print("\033[91mOpção inválida!\033[0m")
    except ValueError:
        print("\033[91mEntrada inválida!\033[0m")
    
    input("\nPressione Enter...")


if __name__ == "__main__":
    demo()
