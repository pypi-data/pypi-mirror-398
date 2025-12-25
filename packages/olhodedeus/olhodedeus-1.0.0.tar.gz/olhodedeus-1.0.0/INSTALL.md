# 👁️ Olho de Deus - Instalação

## 🚀 Instalação via pip (Recomendado)

### Windows (PowerShell/CMD)

```powershell
# Opção 1: Instalar do repositório local
cd C:\caminho\para\Olhodedeus
pip install -e .

# Opção 2: Instalar do GitHub (quando publicado)
pip install olhodedeus

# Opção 3: Instalar do GitHub diretamente
pip install git+https://github.com/seu-usuario/olhodedeus.git
```

### Linux/macOS

```bash
# Opção 1: Instalar do repositório local
cd /caminho/para/Olhodedeus
pip install -e .

# Opção 2: Instalar do PyPI (quando publicado)
pip install olhodedeus

# Opção 3: Instalar do GitHub diretamente
pip install git+https://github.com/seu-usuario/olhodedeus.git
```

---

## 📦 Verificar Instalação

Após instalar, os seguintes comandos estarão disponíveis em qualquer terminal:

```bash
# Verificar versão
olhodedeus --version

# Menu interativo
olhodedeus

# Atalhos
odd --help
olho --help
```

---

## 🔧 Comandos Disponíveis

```bash
# Menu interativo completo
olhodedeus

# Verificar vazamento de email
olhodedeus leak email@exemplo.com

# Geolocalização de IP
olhodedeus ip 8.8.8.8

# OSINT de username em redes sociais
olhodedeus user johndoe

# Port scan
olhodedeus scan 192.168.1.1 -p 1-1000

# Enumerar subdomínios
olhodedeus sub exemplo.com

# Iniciar servidor API REST
olhodedeus api --port 8080 --api-key MINHA_CHAVE_SECRETA
```

---

## 🌐 Acesso Remoto via API

Inicie o servidor em uma máquina:

```bash
olhodedeus api --host 0.0.0.0 --port 8080 --api-key SUA_CHAVE
```

Acesse de qualquer outro computador:

```bash
# Health check
curl http://SEU_IP:8080/api/health

# Verificar leak
curl "http://SEU_IP:8080/api/leaks/check?email=teste@email.com&api_key=SUA_CHAVE"

# Geolocalização
curl "http://SEU_IP:8080/api/ip/lookup?ip=8.8.8.8&api_key=SUA_CHAVE"
```

---

## 🐍 Uso como Biblioteca Python

```python
from olhodedeus import OlhoDeDeus

odd = OlhoDeDeus()

# Verificar vazamento
result = odd.check_leak("email@exemplo.com")
print(result)

# Geolocalização de IP
geo = odd.ip_lookup("8.8.8.8")
print(geo)

# OSINT de username
user_info = odd.username_osint("johndoe")
print(user_info)

# Iniciar API programaticamente
odd.start_api(host="0.0.0.0", port=8080, api_key="minha_chave")
```

---

## 📋 Requisitos do Sistema

- **Python**: 3.10 ou superior
- **Sistemas**: Windows 10/11, Linux, macOS
- **Opcional**: GPG (para encriptação), Nmap (para scans avançados)

---

## 🔄 Atualização

```bash
# Via pip
pip install --upgrade olhodedeus

# Via repositório local
cd /caminho/para/Olhodedeus
git pull
pip install -e . --upgrade
```

---

## ❌ Desinstalação

```bash
pip uninstall olhodedeus
```
