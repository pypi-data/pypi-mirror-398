
import ctypes
import string
import os
import time
import random

try:
    from discord_webhook import DiscordWebhook
    USE_WEBHOOK = True
except ImportError:
    USE_WEBHOOK = False

try:
    import requests
except ImportError:
    print("Module requests not installed, to install run 'pip install requests'")
    exit()

try:
    import numpy
except ImportError:
    print("Module numpy not installed, to install run 'pip install numpy'")
    exit()

class GenAndCheckers:
    def __init__(self):
        self.nitro_file_name = "Nitro Codes.txt"
        self.steam_file_name = "Steam Keys.txt"

    def slow_type(self, text: str, speed: float, new_line=True):
        for i in text:
            print(i, end="", flush=True)
            time.sleep(speed)
        if new_line:
            print()

    def main_menu(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        if os.name == "nt":
            ctypes.windll.kernel32.SetConsoleTitleW("Gen And Checkers - Olho de Deus")
        else:
            print(f'\33]0;Gen And Checkers - Olho de Deus\a', end='', flush=True)

        self.slow_type("Gen And Checkers - Olho de Deus", 0.02)
        print("\nSelecione uma opção:")
        print("1. Gerador e Verificador de Nitro")
        print("2. Gerador de Chaves Steam (Em breve)")
        print("3. Sair")

        choice = input("Opção: ")
        return choice

    def run(self):
        while True:
            choice = self.main_menu()
            if choice == '1':
                self.nitro_generator()
            elif choice == '2':
                self.steam_key_generator()
            elif choice == '3':
                break
            else:
                print("Opção inválida. Tente novamente.")
                time.sleep(1)

    # --- Nitro Generator ---
    def nitro_generator(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        if os.name == "nt":
            ctypes.windll.kernel32.SetConsoleTitleW("Nitro Generator and Checker - Made by Nin")
        else:
            print(f'\33]0;Nitro Generator and Checker - Made by Nin\a', end='', flush=True)

        print("""
███╗   ██╗██╗███╗   ██╗
████╗  ██║██║████╗  ██║
██╔██╗ ██║██║██╔██╗ ██║
██║╚██╗██║██║██║╚██╗██║
██║ ╚████║██║██║ ╚████║
╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝
                                                        """)
        self.slow_type("Made by: Nin\n", .02)
        self.slow_type("\nQuantos códigos para gerar e verificar: ", .02, new_line=False)

        try:
            num = int(input(''))
        except ValueError:
            input("A entrada especificada não era um número.\nPressione Enter para sair")
            return

        webhook_url = None
        if USE_WEBHOOK:
            self.slow_type("Se você quiser usar um webhook do Discord, digite-o aqui ou pressione Enter para ignorar: ", .02, new_line=False)
            webhook_url = input('')
            if webhook_url == "":
                webhook_url = None
            elif webhook_url is not None:
                try:
                    DiscordWebhook(url=webhook_url, content="```Verificação de URLs iniciada\nEnviarei quaisquer códigos válidos aqui```").execute()
                except Exception as e:
                    print(f"Webhook inválido: {e}")
                    webhook_url = None


        valid_codes = []
        invalid_codes = 0
        chars = list(string.ascii_letters + string.digits)

        c = numpy.random.choice(chars, size=[num, 16])
        for s in c:
            try:
                code = ''.join(x for x in s)
                url = f"https://discord.gift/{code}"
                result = self.quick_nitro_checker(url, webhook_url)
                if result:
                    valid_codes.append(url)
                else:
                    invalid_codes += 1
            except KeyboardInterrupt:
                print("\nInterrompido pelo usuário")
                break
            except Exception as e:
                print(f" Erro | {url} | {e}")

            if os.name == "nt":
                ctypes.windll.kernel32.SetConsoleTitleW(f"Nitro Generator and Checker - {len(valid_codes)} Válidos | {invalid_codes} Inválidos")
            else:
                print(f'\33]0;Nitro Generator and Checker - {len(valid_codes)} Válidos | {invalid_codes} Inválidos\a', end='', flush=True)

        print(f"\nResultados:\n Válidos: {len(valid_codes)}\n Inválidos: {invalid_codes}\n Códigos Válidos: {', '.join(valid_codes)}")
        with open(self.nitro_file_name, "w") as file:
            for code in valid_codes:
                file.write(f"{code}\n")
        print(f"Códigos válidos salvos em {self.nitro_file_name}")
        input("\nO fim! Pressione Enter para voltar ao menu principal.")

    def quick_nitro_checker(self, nitro, notify=None):
        url = f"https://discordapp.com/api/v9/entitlements/gift-codes/{nitro.split('/')[-1]}?with_application=false&with_subscription_plan=true"
        response = requests.get(url)
        if response.status_code == 200:
            print(f" Válido | {nitro} ", flush=True, end="" if os.name == 'nt' else "\n")
            if notify is not None:
                try:
                    DiscordWebhook(url=notify, content=f"Código Nitro Válido detectado! @everyone \n{nitro}").execute()
                except Exception as e:
                    print(f"Falha ao enviar webhook: {e}")
            return True
        else:
            print(f" Inválido | {nitro} ", flush=True, end="" if os.name == 'nt' else "\n")
            return False

    # --- Steam Key Generator ---
    def steam_key_generator(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        if os.name == "nt":
            ctypes.windll.kernel32.SetConsoleTitleW("Steam Key Generator")
        else:
            print(f'\33]0;Steam Key Generator\a', end='', flush=True)
        
        self.slow_type("Gerador de Chaves Steam", 0.02)
        print("\nEsta funcionalidade estará disponível em breve.")
        input("\nPressione Enter para voltar ao menu principal.")

    def generate_steam_key(self):
        return '-'.join(''.join(random.choices(string.ascii_uppercase + string.digits, k=5)) for _ in range(3))


if __name__ == '__main__':
    # Check for internet connection
    try:
        response = requests.get("https://github.com", timeout=5)
        print("Verificação de Internet OK")
        time.sleep(.4)
    except requests.exceptions.ConnectionError:
        input("Você não está conectado à internet, verifique sua conexão e tente novamente.\nPressione Enter para sair")
        exit()

    app = GenAndCheckers()
    app.run()
