#!/usr/bin/env python3
"""
notifications.py

Sistema de notificações e alertas para o Olho de Deus.
Suporta múltiplos canais: Telegram, Discord, Email, Webhook.
"""
import os
import json
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, List, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import threading
import queue


class NotificationType(Enum):
    """Tipos de notificação."""
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"


@dataclass
class Notification:
    """Estrutura de notificação."""
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    timestamp: datetime = None
    source: str = "olho_de_deus"
    data: Dict = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.data is None:
            self.data = {}
    
    def to_dict(self) -> Dict:
        return {
            'title': self.title,
            'message': self.message,
            'type': self.type.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'data': self.data,
        }


class TelegramNotifier:
    """Notificações via Telegram."""
    
    API_URL = "https://api.telegram.org/bot{token}/{method}"
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.session = requests.Session()
    
    def _request(self, method: str, data: Dict = None) -> Dict:
        """Faz request à API do Telegram."""
        if not self.bot_token:
            return {'error': 'Bot token não configurado'}
        
        try:
            url = self.API_URL.format(token=self.bot_token, method=method)
            resp = self.session.post(url, json=data, timeout=30)
            return resp.json()
        except Exception as e:
            return {'error': str(e)}
    
    def send_message(self, text: str, chat_id: str = None, parse_mode: str = 'HTML') -> Dict:
        """Envia mensagem."""
        return self._request('sendMessage', {
            'chat_id': chat_id or self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
        })
    
    def send_notification(self, notification: Notification) -> Dict:
        """Envia notificação formatada."""
        icons = {
            NotificationType.INFO: 'ℹ️',
            NotificationType.WARNING: '⚠️',
            NotificationType.ALERT: '🚨',
            NotificationType.CRITICAL: '🔴',
        }
        
        text = f"""
{icons[notification.type]} <b>{notification.title}</b>

{notification.message}

<i>🕐 {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</i>
<i>📍 {notification.source}</i>
"""
        return self.send_message(text.strip())
    
    def get_updates(self) -> Dict:
        """Obtém atualizações (para descobrir chat_id)."""
        return self._request('getUpdates')


class DiscordNotifier:
    """Notificações via Discord Webhook."""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url
        self.session = requests.Session()
    
    def send_message(self, content: str, username: str = "Olho de Deus") -> Dict:
        """Envia mensagem simples."""
        if not self.webhook_url:
            return {'error': 'Webhook URL não configurada'}
        
        try:
            resp = self.session.post(self.webhook_url, json={
                'content': content,
                'username': username,
            }, timeout=30)
            return {'ok': resp.status_code == 204}
        except Exception as e:
            return {'error': str(e)}
    
    def send_embed(self, title: str, description: str, color: int = 0x00ff00, 
                   fields: List[Dict] = None) -> Dict:
        """Envia mensagem com embed."""
        if not self.webhook_url:
            return {'error': 'Webhook URL não configurada'}
        
        embed = {
            'title': title,
            'description': description,
            'color': color,
            'timestamp': datetime.utcnow().isoformat(),
            'footer': {'text': 'Olho de Deus'},
        }
        
        if fields:
            embed['fields'] = fields
        
        try:
            resp = self.session.post(self.webhook_url, json={
                'embeds': [embed],
                'username': 'Olho de Deus',
            }, timeout=30)
            return {'ok': resp.status_code == 204}
        except Exception as e:
            return {'error': str(e)}
    
    def send_notification(self, notification: Notification) -> Dict:
        """Envia notificação formatada."""
        colors = {
            NotificationType.INFO: 0x3498db,      # Azul
            NotificationType.WARNING: 0xf39c12,   # Amarelo
            NotificationType.ALERT: 0xe74c3c,     # Vermelho
            NotificationType.CRITICAL: 0x9b59b6,  # Roxo
        }
        
        return self.send_embed(
            title=notification.title,
            description=notification.message,
            color=colors[notification.type],
            fields=[
                {'name': 'Tipo', 'value': notification.type.value, 'inline': True},
                {'name': 'Fonte', 'value': notification.source, 'inline': True},
            ]
        )


class EmailNotifier:
    """Notificações via Email (SMTP)."""
    
    def __init__(self, smtp_server: str = None, smtp_port: int = 587,
                 username: str = None, password: str = None,
                 from_email: str = None, to_emails: List[str] = None):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails or []
    
    def send_email(self, subject: str, body: str, html: bool = False) -> Dict:
        """Envia email."""
        if not all([self.smtp_server, self.username, self.password, self.from_email]):
            return {'error': 'Configuração SMTP incompleta'}
        
        if not self.to_emails:
            return {'error': 'Nenhum destinatário configurado'}
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            content_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, content_type))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_email, self.to_emails, msg.as_string())
            
            return {'ok': True}
        except Exception as e:
            return {'error': str(e)}
    
    def send_notification(self, notification: Notification) -> Dict:
        """Envia notificação por email."""
        subject = f"[{notification.type.value.upper()}] {notification.title}"
        
        body = f"""
<html>
<body>
<h2>{notification.title}</h2>
<p>{notification.message}</p>
<hr>
<p><small>
Tipo: {notification.type.value}<br>
Fonte: {notification.source}<br>
Data: {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
</small></p>
</body>
</html>
"""
        return self.send_email(subject, body, html=True)


class WebhookNotifier:
    """Notificações via Webhook genérico."""
    
    def __init__(self, webhook_url: str = None, headers: Dict = None):
        self.webhook_url = webhook_url
        self.headers = headers or {'Content-Type': 'application/json'}
        self.session = requests.Session()
    
    def send(self, data: Dict) -> Dict:
        """Envia dados para webhook."""
        if not self.webhook_url:
            return {'error': 'Webhook URL não configurada'}
        
        try:
            resp = self.session.post(
                self.webhook_url,
                json=data,
                headers=self.headers,
                timeout=30
            )
            return {'ok': resp.status_code < 400, 'status_code': resp.status_code}
        except Exception as e:
            return {'error': str(e)}
    
    def send_notification(self, notification: Notification) -> Dict:
        """Envia notificação."""
        return self.send(notification.to_dict())


class NotificationManager:
    """Gerenciador central de notificações."""
    
    CONFIG_PATH = "config/notifications.json"
    
    def __init__(self):
        self.notifiers = {}
        self.queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        self.history = []
        
        self._load_config()
    
    def _load_config(self):
        """Carrega configuração."""
        if os.path.exists(self.CONFIG_PATH):
            with open(self.CONFIG_PATH, 'r') as f:
                config = json.load(f)
            
            # Telegram
            if config.get('telegram'):
                self.notifiers['telegram'] = TelegramNotifier(
                    bot_token=config['telegram'].get('bot_token'),
                    chat_id=config['telegram'].get('chat_id'),
                )
            
            # Discord
            if config.get('discord'):
                self.notifiers['discord'] = DiscordNotifier(
                    webhook_url=config['discord'].get('webhook_url'),
                )
            
            # Email
            if config.get('email'):
                self.notifiers['email'] = EmailNotifier(
                    smtp_server=config['email'].get('smtp_server'),
                    smtp_port=config['email'].get('smtp_port', 587),
                    username=config['email'].get('username'),
                    password=config['email'].get('password'),
                    from_email=config['email'].get('from_email'),
                    to_emails=config['email'].get('to_emails', []),
                )
            
            # Webhook
            if config.get('webhook'):
                self.notifiers['webhook'] = WebhookNotifier(
                    webhook_url=config['webhook'].get('url'),
                    headers=config['webhook'].get('headers'),
                )
    
    def save_config(self, config: Dict):
        """Salva configuração."""
        os.makedirs(os.path.dirname(self.CONFIG_PATH), exist_ok=True)
        with open(self.CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        self._load_config()
    
    def notify(self, notification: Notification, channels: List[str] = None):
        """Envia notificação para canais especificados."""
        if channels is None:
            channels = list(self.notifiers.keys())
        
        results = {}
        for channel in channels:
            if channel in self.notifiers:
                results[channel] = self.notifiers[channel].send_notification(notification)
        
        self.history.append({
            'notification': notification.to_dict(),
            'results': results,
        })
        
        return results
    
    def notify_async(self, notification: Notification, channels: List[str] = None):
        """Adiciona notificação à fila (processamento async)."""
        self.queue.put((notification, channels))
    
    def start_worker(self):
        """Inicia worker de processamento."""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
    
    def stop_worker(self):
        """Para worker."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def _process_queue(self):
        """Processa fila de notificações."""
        while self.running:
            try:
                notification, channels = self.queue.get(timeout=1)
                self.notify(notification, channels)
            except queue.Empty:
                continue
    
    def quick_notify(self, title: str, message: str, 
                     type: NotificationType = NotificationType.INFO):
        """Atalho para notificação rápida."""
        notification = Notification(title=title, message=message, type=type)
        return self.notify(notification)


def interactive_menu():
    """Menu interativo."""
    manager = NotificationManager()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Status dos canais
        channels_status = []
        for name in ['telegram', 'discord', 'email', 'webhook']:
            status = '✅' if name in manager.notifiers else '❌'
            channels_status.append(f"{name}: {status}")
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                  🔔 NOTIFICATION SYSTEM                      ║
╠══════════════════════════════════════════════════════════════╣
║  {' | '.join(channels_status)}
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ──── 📤 ENVIAR ────                                         ║
║  [1] 📨 Enviar Notificação de Teste                          ║
║  [2] 🚨 Enviar Alerta                                        ║
║                                                              ║
║  ──── ⚙️ CONFIGURAÇÃO ────                                    ║
║  [3] 📱 Configurar Telegram                                  ║
║  [4] 💬 Configurar Discord                                   ║
║  [5] 📧 Configurar Email                                     ║
║  [6] 🔗 Configurar Webhook                                   ║
║                                                              ║
║  ──── 📜 HISTÓRICO ────                                      ║
║  [7] 📜 Ver Histórico                                        ║
║                                                              ║
║  [0] Voltar                                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        choice = input("Opção: ").strip()
        
        if choice == '1':
            title = input("\n📝 Título: ").strip() or "Teste de Notificação"
            message = input("💬 Mensagem: ").strip() or "Esta é uma notificação de teste do Olho de Deus."
            
            notification = Notification(title=title, message=message, type=NotificationType.INFO)
            results = manager.notify(notification)
            
            print("\n📊 RESULTADOS:\n")
            for channel, result in results.items():
                status = '✅' if result.get('ok') or 'error' not in result else '❌'
                print(f"   {status} {channel}: {result}")
            input("\nPressione Enter...")
        
        elif choice == '2':
            print("\nTipo de alerta:")
            print("   [1] ⚠️ Warning")
            print("   [2] 🚨 Alert")
            print("   [3] 🔴 Critical")
            
            alert_type = input("\nEscolha: ").strip()
            types_map = {'1': NotificationType.WARNING, '2': NotificationType.ALERT, '3': NotificationType.CRITICAL}
            
            title = input("📝 Título: ").strip()
            message = input("💬 Mensagem: ").strip()
            
            notification = Notification(
                title=title,
                message=message,
                type=types_map.get(alert_type, NotificationType.ALERT)
            )
            results = manager.notify(notification)
            
            print("\n📊 RESULTADOS:\n")
            for channel, result in results.items():
                status = '✅' if result.get('ok') or 'error' not in result else '❌'
                print(f"   {status} {channel}: {result}")
            input("\nPressione Enter...")
        
        elif choice == '3':
            print("\n📱 CONFIGURAÇÃO DO TELEGRAM\n")
            print("1. Crie um bot com @BotFather")
            print("2. Copie o token do bot")
            print("3. Envie uma mensagem para o bot")
            print("4. Use getUpdates para obter seu chat_id")
            
            config = {}
            if os.path.exists(manager.CONFIG_PATH):
                with open(manager.CONFIG_PATH, 'r') as f:
                    config = json.load(f)
            
            token = input("\nBot Token: ").strip()
            if token:
                config.setdefault('telegram', {})['bot_token'] = token
                
                # Tenta obter updates para pegar chat_id
                temp = TelegramNotifier(bot_token=token)
                updates = temp.get_updates()
                if 'result' in updates and updates['result']:
                    chat_id = str(updates['result'][-1]['message']['chat']['id'])
                    print(f"   Chat ID detectado: {chat_id}")
                    config['telegram']['chat_id'] = chat_id
                else:
                    chat_id = input("Chat ID: ").strip()
                    if chat_id:
                        config['telegram']['chat_id'] = chat_id
                
                manager.save_config(config)
                print("✅ Salvo!")
            input("\nPressione Enter...")
        
        elif choice == '4':
            print("\n💬 CONFIGURAÇÃO DO DISCORD\n")
            print("1. Vá nas configurações do canal")
            print("2. Integrações → Webhooks → Novo Webhook")
            print("3. Copie a URL do webhook")
            
            config = {}
            if os.path.exists(manager.CONFIG_PATH):
                with open(manager.CONFIG_PATH, 'r') as f:
                    config = json.load(f)
            
            url = input("\nWebhook URL: ").strip()
            if url:
                config.setdefault('discord', {})['webhook_url'] = url
                manager.save_config(config)
                print("✅ Salvo!")
            input("\nPressione Enter...")
        
        elif choice == '5':
            print("\n📧 CONFIGURAÇÃO DE EMAIL\n")
            
            config = {}
            if os.path.exists(manager.CONFIG_PATH):
                with open(manager.CONFIG_PATH, 'r') as f:
                    config = json.load(f)
            
            config.setdefault('email', {})
            
            server = input(f"SMTP Server [{config['email'].get('smtp_server', 'smtp.gmail.com')}]: ").strip()
            if server:
                config['email']['smtp_server'] = server
            
            port = input(f"SMTP Port [{config['email'].get('smtp_port', 587)}]: ").strip()
            if port:
                config['email']['smtp_port'] = int(port)
            
            user = input("Username/Email: ").strip()
            if user:
                config['email']['username'] = user
                config['email']['from_email'] = user
            
            password = input("Password (app password): ").strip()
            if password:
                config['email']['password'] = password
            
            to = input("Destinatários (separados por vírgula): ").strip()
            if to:
                config['email']['to_emails'] = [e.strip() for e in to.split(',')]
            
            manager.save_config(config)
            print("✅ Salvo!")
            input("\nPressione Enter...")
        
        elif choice == '6':
            print("\n🔗 CONFIGURAÇÃO DE WEBHOOK\n")
            
            config = {}
            if os.path.exists(manager.CONFIG_PATH):
                with open(manager.CONFIG_PATH, 'r') as f:
                    config = json.load(f)
            
            url = input("Webhook URL: ").strip()
            if url:
                config.setdefault('webhook', {})['url'] = url
                manager.save_config(config)
                print("✅ Salvo!")
            input("\nPressione Enter...")
        
        elif choice == '7':
            print("\n📜 HISTÓRICO DE NOTIFICAÇÕES:\n")
            if manager.history:
                for i, entry in enumerate(manager.history[-10:], 1):
                    n = entry['notification']
                    print(f"   {i}. [{n['type']}] {n['title']}")
                    print(f"      {n['timestamp']}")
                    for ch, res in entry['results'].items():
                        status = '✅' if res.get('ok') or 'error' not in res else '❌'
                        print(f"      {status} {ch}")
                    print()
            else:
                print("   Nenhuma notificação enviada nesta sessão.")
            input("\nPressione Enter...")
        
        elif choice == '0':
            break


if __name__ == '__main__':
    interactive_menu()
