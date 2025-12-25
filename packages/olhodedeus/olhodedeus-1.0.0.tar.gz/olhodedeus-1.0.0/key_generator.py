
import random
import string

def generate_steam_key():
    """Generates a random key in the format AAAAA-BBBBB-CCCCC"""
    return '-'.join(''.join(random.choices(string.ascii_uppercase + string.digits, k=5)) for _ in range(3))

def generate_nitro_key():
    """Generates a random key in the format https://discord.gift/XXXXXXXXXXXXXXXX"""
    return "https://discord.gift/" + ''.join(random.choices(string.ascii_letters + string.digits, k=16))

def check_key(key):
    """
    Placeholder for a key checker. 
    This function does not actually validate keys with Steam or Discord.
    """
    # In a real scenario, this would involve making a request to the respective service's API.
    # For this educational example, we'll just simulate a random check.
    return random.choice([True, False])

if __name__ == "__main__":
    print("Gerador de Chaves (para fins de estudo)")

    # Generate and "check" a Steam key
    steam_key = generate_steam_key()
    print(f"\nChave Steam Gerada: {steam_key}")
    if check_key(steam_key):
        print("Status: Chave Steam parece válida (simulação)")
    else:
        print("Status: Chave Steam parece inválida (simulação)")

    # Generate and "check" a Nitro key
    nitro_key = generate_nitro_key()
    print(f"\nLink Nitro Gerado: {nitro_key}")
    if check_key(nitro_key):
        print("Status: Link Nitro parece válido (simulação)")
    else:
        print("Status: Link Nitro parece inválido (simulação)")
