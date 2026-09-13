#!/usr/bin/env python3
"""
Hide.me VPN Notification Bar / System Tray GUI
Benutzerfreundliche GUI für hide.me CLI VPN
"""

__version__ = "1.1.0"
GITHUB_REPO = "hirntot/hideme-vpn-gui"

import os


def detect_language(environ=None):
    """Select a supported system language, with English as the fallback."""
    env = os.environ if environ is None else environ
    for key in ("HIDEME_LANG", "LC_ALL", "LC_MESSAGES", "LANGUAGE", "LANG"):
        value = env.get(key)
        if value:
            language = value.split(":", 1)[0].split("_", 1)[0].split("-", 1)[0]
            language = language.split(".", 1)[0].split("@", 1)[0].lower()
            return language if language in ("de", "en", "fr", "es", "it", "pt") else "en"
    return "en"


LANGUAGE = detect_language()
# GTK's built-in dialog labels should use the same language as the application.
os.environ["LANGUAGE"] = LANGUAGE


def tr(german, english, french, spanish, italian, portuguese):
    """Translations are ordered de/en/fr/es/it/pt at every call site."""
    return {"de": german, "en": english, "fr": french, "es": spanish,
            "it": italian, "pt": portuguese}.get(LANGUAGE, english)


import gi
gi.require_version('Gtk', '3.0')

# Versuche AppIndicator3 zu laden, sonst Fallback auf StatusIcon
try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3
    HAS_APPINDICATOR = True
except (ValueError, ImportError):
    HAS_APPINDICATOR = False
    print(tr(
        "AppIndicator3 nicht verfügbar - verwende GTK StatusIcon Fallback",
        'AppIndicator3 unavailable - using GTK StatusIcon fallback',
        'AppIndicator3 indisponible - utilisation de GTK StatusIcon',
        'AppIndicator3 no disponible - se usa GTK StatusIcon',
        'AppIndicator3 non disponibile - viene usato GTK StatusIcon',
        'AppIndicator3 indisponível - usando GTK StatusIcon'
    ))
    print(tr(
        "Für bessere Integration installiere: sudo apt install gir1.2-appindicator3-0.1",
        'For better integration install: sudo apt install gir1.2-appindicator3-0.1',
        'Pour une meilleure intégration : sudo apt install gir1.2-appindicator3-0.1',
        'Para una mejor integración: sudo apt install gir1.2-appindicator3-0.1',
        'Per una migliore integrazione: sudo apt install gir1.2-appindicator3-0.1',
        'Para melhor integração: sudo apt install gir1.2-appindicator3-0.1'
    ))

# Versuche Notify zu laden
try:
    gi.require_version('Notify', '0.7')
    from gi.repository import Notify
    HAS_NOTIFY = True
except (ValueError, ImportError):
    HAS_NOTIFY = False
    print(tr(
        "Notify nicht verfügbar - keine Desktop-Benachrichtigungen",
        'Notify unavailable - desktop notifications disabled',
        'Notify indisponible - notifications désactivées',
        'Notify no disponible - notificaciones desactivadas',
        'Notify non disponibile - notifiche disattivate',
        'Notify indisponível - notificações desativadas'
    ))
    print(tr(
        "Für Benachrichtigungen installiere: sudo apt install gir1.2-notify-0.7",
        'For notifications install: sudo apt install gir1.2-notify-0.7',
        'Pour les notifications : sudo apt install gir1.2-notify-0.7',
        'Para las notificaciones: sudo apt install gir1.2-notify-0.7',
        'Per le notifiche: sudo apt install gir1.2-notify-0.7',
        'Para notificações: sudo apt install gir1.2-notify-0.7'
    ))

from gi.repository import Gtk, GLib, GdkPixbuf
import subprocess
import sys
import json
import argparse
import threading
import time
import urllib.request
import urllib.error
import re
from html.parser import HTMLParser

class HideMeVPN:
    """Wrapper für hide.me CLI Befehle"""
    
    HIDEME_DIR = "/opt/hide.me"
    HIDEME_BIN = "/opt/hide.me/hide.me"
    CONFIG_FILE = os.path.expanduser("~/.config/hideme-gui/config.json")
    
    def __init__(self):
        self.connected = False
        self.current_server = None
        self.favorite_servers = []
        self.cached_servers = []
        self.load_config()
    
    def load_config(self):
        """Lädt gespeicherte Konfiguration"""
        os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.current_server = config.get('last_server', 'nl')
                    self.favorite_servers = config.get('favorite_servers', [])
                    if not isinstance(self.favorite_servers, list):
                        self.favorite_servers = []
                    self.cached_servers = (config.get('cached_servers', [])
                                           if config.get('cached_servers_language', 'de') == LANGUAGE
                                           else [])
                    if not isinstance(self.cached_servers, list):
                        self.cached_servers = []
        except Exception as e:
            print(tr(
                f"Config laden fehlgeschlagen: {e}",
                f'Failed to load configuration: {e}',
                f'Échec du chargement de la configuration : {e}',
                f'Error al cargar la configuración: {e}',
                f'Caricamento della configurazione non riuscito: {e}',
                f'Falha ao carregar a configuração: {e}'
            ))
            self.current_server = 'nl'
            self.favorite_servers = []
            self.cached_servers = []
    
    def save_config(self):
        """Speichert aktuelle Konfiguration"""
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump({
                    'last_server': self.current_server,
                    'favorite_servers': self.favorite_servers,
                    'cached_servers': self.cached_servers,
                    'cached_servers_language': LANGUAGE
                }, f)
        except Exception as e:
            print(tr(
                f"Config speichern fehlgeschlagen: {e}",
                f'Failed to save configuration: {e}',
                f"Échec de l'enregistrement de la configuration : {e}",
                f'Error al guardar la configuración: {e}',
                f'Salvataggio della configurazione non riuscito: {e}',
                f'Falha ao guardar a configuração: {e}'
            ))
    
    def is_installed(self):
        """Prüft ob hide.me CLI installiert ist"""
        return os.path.exists(self.HIDEME_BIN)
    
    def get_status(self):
        """Prüft VPN-Status via systemctl"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', f'hide.me@{self.current_server}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.connected = (result.stdout.strip() == 'active')
            return self.connected
        except Exception as e:
            print(tr(
                f"Status-Check fehlgeschlagen: {e}",
                f'Status check failed: {e}',
                f"Échec de la vérification de l'état : {e}",
                f'Error al comprobar el estado: {e}',
                f'Verifica dello stato non riuscita: {e}',
                f'Falha ao verificar o estado: {e}'
            ))
            return False
    
    def connect(self, server=None):
        """Verbindet zu hide.me VPN"""
        if server:
            self.current_server = server
            self.save_config()
        
        try:
            # Service enablen und starten
            subprocess.run(
                ['pkexec', 'systemctl', 'enable', f'hide.me@{self.current_server}'],
                check=True,
                timeout=30
            )
            subprocess.run(
                ['pkexec', 'systemctl', 'start', f'hide.me@{self.current_server}'],
                check=True,
                timeout=30
            )
            self.connected = True
            return True, tr(
                f"Verbunden mit {self.current_server}",
                f'Connected to {self.current_server}',
                f'Connecté à {self.current_server}',
                f'Conectado a {self.current_server}',
                f'Connesso a {self.current_server}',
                f'Ligado a {self.current_server}'
            )
        except subprocess.CalledProcessError as e:
            return False, tr(
                f"Verbindung fehlgeschlagen: {e}",
                f'Connection failed: {e}',
                f'Échec de la connexion : {e}',
                f'Error de conexión: {e}',
                f'Connessione non riuscita: {e}',
                f'Falha na ligação: {e}'
            )
        except Exception as e:
            return False, tr(
                f"Fehler: {e}",
                f'Error: {e}',
                f'Erreur : {e}',
                f'Error: {e}',
                f'Errore: {e}',
                f'Erro: {e}'
            )
    
    def disconnect(self):
        """Trennt VPN-Verbindung"""
        try:
            subprocess.run(
                ['pkexec', 'systemctl', 'stop', f'hide.me@{self.current_server}'],
                check=True,
                timeout=30
            )
            subprocess.run(
                ['pkexec', 'systemctl', 'disable', f'hide.me@{self.current_server}'],
                check=True,
                timeout=30
            )
            self.connected = False
            return True, tr(
                "VPN getrennt",
                'VPN disconnected',
                'VPN déconnecté',
                'VPN desconectada',
                'VPN disconnessa',
                'VPN desligada'
            )
        except subprocess.CalledProcessError as e:
            return False, tr(
                f"Trennung fehlgeschlagen: {e}",
                f'Disconnect failed: {e}',
                f'Échec de la déconnexion : {e}',
                f'Error al desconectar: {e}',
                f'Disconnessione non riuscita: {e}',
                f'Falha ao desligar: {e}'
            )
        except Exception as e:
            return False, tr(
                f"Fehler: {e}",
                f'Error: {e}',
                f'Erreur : {e}',
                f'Error: {e}',
                f'Errore: {e}',
                f'Erro: {e}'
            )

    def emergency_reset(self):
        """Setzt hide.me VPN-Reste im System zurück (Notfall-Reset)."""
        reset_script = r'''
set +e
ACTIVE_SERVICES=$(systemctl list-units --type=service --state=active 'hide.me@*' --no-legend | awk '{print $1}')
if [ -n "$ACTIVE_SERVICES" ]; then
    for service in $ACTIVE_SERVICES; do
        systemctl stop "$service" 2>/dev/null
        systemctl disable "$service" 2>/dev/null
    done
fi
ip rule del table 55555 2>/dev/null
ip -6 rule del table 55555 2>/dev/null
ip route flush table 55555 2>/dev/null
ip -6 route flush table 55555 2>/dev/null
if ip link show vpn >/dev/null 2>&1; then
    ip link delete vpn 2>/dev/null
fi
if [ -f /etc/resolv.conf.hide.me.backup ]; then
    cp /etc/resolv.conf.hide.me.backup /etc/resolv.conf 2>/dev/null
fi
if command -v iptables >/dev/null 2>&1; then
    iptables -t mangle -F 2>/dev/null
fi
if command -v ip6tables >/dev/null 2>&1; then
    ip6tables -t mangle -F 2>/dev/null
fi
'''
        try:
            subprocess.run(
                ['pkexec', 'bash', '-c', reset_script],
                check=True,
                timeout=90
            )
            self.connected = False
            return True, tr(
                "Notfall-Reset abgeschlossen. Netzwerk wurde zurückgesetzt.",
                'Emergency reset complete. Network settings have been reset.',
                "Réinitialisation d'urgence terminée. Paramètres réseau réinitialisés.",
                'Restablecimiento de emergencia completado. Se ha restablecido la configuración de red.',
                'Ripristino di emergenza completato. Impostazioni di rete ripristinate.',
                'Reposição de emergência concluída. As definições de rede foram repostas.'
            )
        except subprocess.CalledProcessError as e:
            return False, tr(
                f"Notfall-Reset fehlgeschlagen: {e}",
                f'Emergency reset failed: {e}',
                f"Échec de la réinitialisation d'urgence : {e}",
                f'Error en el restablecimiento de emergencia: {e}',
                f'Ripristino di emergenza non riuscito: {e}',
                f'Falha na reposição de emergência: {e}'
            )
        except Exception as e:
            return False, tr(
                f"Fehler beim Notfall-Reset: {e}",
                f'Emergency reset error: {e}',
                f"Erreur de réinitialisation d'urgence : {e}",
                f'Error de restablecimiento de emergencia: {e}',
                f'Errore nel ripristino di emergenza: {e}',
                f'Erro na reposição de emergência: {e}'
            )
    
    def get_servers(self):
        """Liste verfügbarer Server/Regionen (Fallback)"""
        return {
            'nl': tr(
                'Niederlande',
                'Netherlands',
                'Pays-Bas',
                'Países Bajos',
                'Paesi Bassi',
                'Países Baixos'
            ),
            'de': tr(
                'Deutschland',
                'Germany',
                'Allemagne',
                'Alemania',
                'Germania',
                'Alemanha'
            ),
            'us': tr('USA', 'USA', 'États-Unis', 'Estados Unidos', 'Stati Uniti', 'Estados Unidos'),
            'gb': tr(
                'Großbritannien',
                'United Kingdom',
                'Royaume-Uni',
                'Reino Unido',
                'Regno Unito',
                'Reino Unido'
            ),
            'ch': tr(
                'Schweiz',
                'Switzerland',
                'Suisse',
                'Suiza',
                'Svizzera',
                'Suíça'
            ),
            'fr': tr(
                'Frankreich',
                'France',
                'France',
                'Francia',
                'Francia',
                'França'
            ),
            'es': tr(
                'Spanien',
                'Spain',
                'Espagne',
                'España',
                'Spagna',
                'Espanha'
            ),
            'it': tr(
                'Italien',
                'Italy',
                'Italie',
                'Italia',
                'Italia',
                'Itália'
            ),
            'se': tr(
                'Schweden',
                'Sweden',
                'Suède',
                'Suecia',
                'Svezia',
                'Suécia'
            ),
            'no': tr(
                'Norwegen',
                'Norway',
                'Norvège',
                'Noruega',
                'Norvegia',
                'Noruega'
            ),
            'dk': tr(
                'Dänemark',
                'Denmark',
                'Danemark',
                'Dinamarca',
                'Danimarca',
                'Dinamarca'
            ),
            'ca': tr(
                'Kanada',
                'Canada',
                'Canada',
                'Canadá',
                'Canada',
                'Canadá'
            ),
            'au': tr(
                'Australien',
                'Australia',
                'Australie',
                'Australia',
                'Australia',
                'Austrália'
            ),
            'jp': tr('Japan', 'Japan', 'Japon', 'Japón', 'Giappone', 'Japão'),
            'sg': tr(
                'Singapur',
                'Singapore',
                'Singapour',
                'Singapur',
                'Singapore',
                'Singapura'
            ),
        }

    def add_favorite_server(self, server_code):
        """Fügt Server zu Favoriten hinzu."""
        if server_code not in self.get_servers():
            return False, tr(
                f"Unbekannter Server: {server_code}",
                f'Unknown server: {server_code}',
                f'Serveur inconnu : {server_code}',
                f'Servidor desconocido: {server_code}',
                f'Server sconosciuto: {server_code}',
                f'Servidor desconhecido: {server_code}'
            )
        if server_code in self.favorite_servers:
            return False, tr(
                f"{server_code} ist bereits in den Favoriten",
                f'{server_code} is already in favorites',
                f'{server_code} est déjà dans les favoris',
                f'{server_code} ya está en favoritos',
                f'{server_code} è già nei preferiti',
                f'{server_code} já está nos favoritos'
            )
        self.favorite_servers.append(server_code)
        self.save_config()
        return True, tr(
            f"{server_code} zu Favoriten hinzugefügt",
            f'{server_code} added to favorites',
            f'{server_code} ajouté aux favoris',
            f'{server_code} añadido a favoritos',
            f'{server_code} aggiunto ai preferiti',
            f'{server_code} adicionado aos favoritos'
        )

    def remove_favorite_server(self, server_code):
        """Entfernt Server aus Favoriten."""
        if server_code not in self.favorite_servers:
            return False, tr(
                f"{server_code} ist nicht in den Favoriten",
                f'{server_code} is not in favorites',
                f"{server_code} n'est pas dans les favoris",
                f'{server_code} no está en favoritos',
                f'{server_code} non è nei preferiti',
                f'{server_code} não está nos favoritos'
            )
        self.favorite_servers.remove(server_code)
        self.save_config()
        return True, tr(
            f"{server_code} aus Favoriten entfernt",
            f'{server_code} removed from favorites',
            f'{server_code} retiré des favoris',
            f'{server_code} eliminado de favoritos',
            f'{server_code} rimosso dai preferiti',
            f'{server_code} removido dos favoritos'
        )

    def set_cached_servers(self, servers):
        """Speichert online geladene Serverliste dauerhaft für Offline-Fallback."""
        if not isinstance(servers, list):
            return
        self.cached_servers = servers
        self.save_config()
    
    def fetch_servers_from_website(self):
        """Lädt aktuelle Server-Liste von hide.me Website"""
        try:
            url = f'https://hide.me/{LANGUAGE}/network'
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
            
            # Parse Server aus HTML - nutze Flag-Image für korrekten Ländercode
            servers = []
            # Regex: Extrahiere Flag-Code aus Image (z.B. nz.png → nz) + Stadt + Land
            pattern = r'<img[^>]+src="[^"]+/flags/png/([a-z]+)\.png"[^>]*>.*?<span[^>]*class="ml-1 u-bold">([^<,]+),</span>\s*<span>\s*([^<]+)</span>'
            
            matches = re.finditer(pattern, html, re.DOTALL)
            for match in matches:
                code = match.group(1).strip()      # z.B. "nz" aus nz.png
                city = match.group(2).strip()      # z.B. "Auckland"
                country = match.group(3).strip()   # z.B. "Neuseeland"
                
                servers.append({
                    'code': code,
                    'city': city,
                    'country': country,
                    'display': f"{city}, {country}"
                })
            
            return servers if servers else None
        except Exception as e:
            print(tr(
                f"Fehler beim Laden der Server-Liste: {e}",
                f'Failed to load server list: {e}',
                f'Échec du chargement des serveurs : {e}',
                f'Error al cargar los servidores: {e}',
                f'Caricamento dei server non riuscito: {e}',
                f'Falha ao carregar os servidores: {e}'
            ))
            return None


class HideMeIndicator:
    """System Tray Indicator für Hide.me VPN"""
    
    def __init__(self):
        self.vpn = HideMeVPN()
        self.cached_servers = self.vpn.cached_servers or []  # Persistenter Cache
        self.server_ping_cache = {}
        self.status_dialog = None
        
        # Prüfe Installation
        if not self.vpn.is_installed():
            self.show_error_dialog(
                tr(
                    "Hide.me CLI nicht installiert",
                    'Hide.me CLI is not installed',
                    "Hide.me CLI n'est pas installé",
                    'Hide.me CLI no está instalado',
                    'Hide.me CLI non è installato',
                    'Hide.me CLI não está instalado'
                ),
                tr(
                    "Bitte installiere zuerst hide.me CLI:\n"
                "sudo ./install.sh im hide.me Verzeichnis",
                    'Please install hide.me CLI first:\nsudo ./install.sh in the hide.me directory',
                    "Installez d'abord hide.me CLI :\nsudo ./install.sh dans le dossier hide.me",
                    'Instala primero hide.me CLI:\nsudo ./install.sh en la carpeta de hide.me',
                    'Installa prima hide.me CLI:\nsudo ./install.sh nella cartella hide.me',
                    'Instale primeiro hide.me CLI:\nsudo ./install.sh na pasta hide.me'
                )
            )
            sys.exit(1)
        
        # Initialisiere Notify wenn verfügbar
        if HAS_NOTIFY:
            Notify.init("Hide.me VPN")
        
        # Erstelle Indicator (AppIndicator oder StatusIcon)
        if HAS_APPINDICATOR:
            self._init_appindicator()
        else:
            self._init_statusicon()
        
        # Erstelle Menü
        self.build_menu()
        
        # Starte Status-Überwachung
        self.update_status()
        GLib.timeout_add_seconds(5, self.update_status)
        
        # Lade Server-Liste im Hintergrund (einmalig beim Start)
        self._load_servers_background()
        # Prüfe im Hintergrund auf neuere Version auf GitHub
        self._check_updates_background()
    
    def _init_appindicator(self):
        """Initialisiert AppIndicator3"""
        self.use_appindicator = True
        self.indicator = AppIndicator3.Indicator.new(
            "hideme-vpn-indicator",
            "network-vpn-disconnected",
            AppIndicator3.IndicatorCategory.SYSTEM_SERVICES
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
    
    def _init_statusicon(self):
        """Initialisiert GTK StatusIcon (Fallback)"""
        self.use_appindicator = False
        self.status_icon = Gtk.StatusIcon()
        self.status_icon.set_from_icon_name("network-vpn-disconnected")
        self.status_icon.set_tooltip_text("Hide.me VPN")
        self.status_icon.set_visible(True)
        self.status_icon.connect("popup-menu", self.on_statusicon_popup)
        self.status_icon.connect("activate", self.on_statusicon_activate)
    
    def _load_servers_background(self):
        """Lädt Server-Liste im Hintergrund beim Start"""
        def load():
            print(tr(
                "Lade Server-Liste von hide.me Website...",
                'Loading server list from the hide.me website...',
                'Chargement des serveurs depuis le site hide.me...',
                'Cargando servidores desde el sitio web de hide.me...',
                'Caricamento dei server dal sito hide.me...',
                'A carregar servidores do site hide.me...'
            ))
            servers = self.vpn.fetch_servers_from_website()
            if servers:
                self.cached_servers = servers
                self.vpn.set_cached_servers(servers)
                print(tr(
                    f"✓ {len(servers)} Server geladen",
                    f'✓ Loaded {len(servers)} servers',
                    f'✓ {len(servers)} serveurs chargés',
                    f'✓ {len(servers)} servidores cargados',
                    f'✓ {len(servers)} server caricati',
                    f'✓ {len(servers)} servidores carregados'
                ))
            else:
                print(tr(
                    "⚠️  Server-Liste konnte nicht geladen werden - verwende Fallback",
                    '⚠️  Could not load server list - using fallback',
                    '⚠️  Impossible de charger les serveurs - utilisation de la liste de secours',
                    '⚠️  No se pudieron cargar los servidores - usando la lista de respaldo',
                    '⚠️  Impossibile caricare i server - uso della lista di riserva',
                    '⚠️  Não foi possível carregar os servidores - a usar a lista alternativa'
                ))
        
        thread = threading.Thread(target=load)
        thread.daemon = True
        thread.start()

    def _parse_version_tuple(self, version_text):
        """Extrahiert numerische Teile einer Version für Vergleich."""
        nums = re.findall(r'\d+', (version_text or "").strip())
        if not nums:
            return (0,)
        return tuple(int(n) for n in nums)

    def _is_remote_version_newer(self, remote_version, local_version):
        """Vergleicht zwei Versions-Strings tolerant."""
        remote = self._parse_version_tuple(remote_version)
        local = self._parse_version_tuple(local_version)
        max_len = max(len(remote), len(local))
        remote += (0,) * (max_len - len(remote))
        local += (0,) * (max_len - len(local))
        return remote > local

    def _fetch_latest_github_version(self):
        """Holt neueste Version (Release/Tag) von GitHub."""
        headers = {'User-Agent': 'hideme-vpn-gui-update-check'}

        # 1) Bevorzugt Releases
        release_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        try:
            req = urllib.request.Request(release_url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                tag = data.get('tag_name')
                if tag:
                    return tag
        except urllib.error.HTTPError as e:
            # 404 ist ok: Repo nutzt evtl. keine Releases
            if e.code != 404:
                raise

        # 2) Fallback auf Tags
        tags_url = f"https://api.github.com/repos/{GITHUB_REPO}/tags?per_page=1"
        req = urllib.request.Request(tags_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            tags = json.loads(response.read().decode('utf-8'))
            if tags and isinstance(tags, list):
                return tags[0].get('name')
        return None

    def _check_updates_background(self):
        """Prüft beim Start asynchron, ob eine neuere Version verfügbar ist."""
        def run():
            try:
                latest = self._fetch_latest_github_version()
                if not latest:
                    return
                if self._is_remote_version_newer(latest, __version__):
                    GLib.idle_add(
                        self.show_notification,
                        tr(
                            "Hide.me VPN Update verfügbar",
                            'Hide.me VPN update available',
                            'Mise à jour Hide.me VPN disponible',
                            'Actualización de Hide.me VPN disponible',
                            'Aggiornamento Hide.me VPN disponibile',
                            'Atualização do Hide.me VPN disponível'
                        ),
                        tr(
                            f"Neue Version gefunden: {latest} (installiert: {__version__})",
                            f'New version found: {latest} (installed: {__version__})',
                            f'Nouvelle version : {latest} (installée : {__version__})',
                            f'Nueva versión: {latest} (instalada: {__version__})',
                            f'Nuova versione: {latest} (installata: {__version__})',
                            f'Nova versão: {latest} (instalada: {__version__})'
                        ),
                        "system-software-update"
                    )
            except Exception as e:
                # Update-Check darf niemals die App-Funktion beeinträchtigen.
                print(tr(
                    f"Update-Check übersprungen: {e}",
                    f'Update check skipped: {e}',
                    f'Vérification des mises à jour ignorée : {e}',
                    f'Comprobación de actualizaciones omitida: {e}',
                    f'Verifica aggiornamenti saltata: {e}',
                    f'Verificação de atualizações ignorada: {e}'
                ))

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()
    
    def build_menu(self):
        """Erstellt das Indicator-Menü"""
        menu = Gtk.Menu()
        
        # Status & Server Dialog öffnen
        status_dialog_item = Gtk.MenuItem(label=tr(
            "Status & Server...",
            'Status & Servers...',
            'État et serveurs...',
            'Estado y servidores...',
            'Stato e server...',
            'Estado e servidores...'
        ))
        status_dialog_item.connect("activate", lambda w: self.show_status_dialog())
        menu.append(status_dialog_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Status-Item (nicht klickbar)
        self.status_item = Gtk.MenuItem(label=tr(
            "Status: Getrennt",
            'Status: Disconnected',
            'État : Déconnecté',
            'Estado: Desconectado',
            'Stato: Disconnesso',
            'Estado: Desligado'
        ))
        self.status_item.set_sensitive(False)
        menu.append(self.status_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Verbinden/Trennen Button
        self.toggle_item = Gtk.MenuItem(label=tr(
            "Verbinden",
            'Connect',
            'Se connecter',
            'Conectar',
            'Connetti',
            'Ligar'
        ))
        self.toggle_item.connect("activate", self.on_toggle_connection)
        menu.append(self.toggle_item)

        # Best Location
        best_item = Gtk.MenuItem(label=tr(
            "Mit bestem Server verbinden",
            'Connect to best server',
            'Se connecter au meilleur serveur',
            'Conectar al mejor servidor',
            'Connetti al server migliore',
            'Ligar ao melhor servidor'
        ))
        best_item.connect("activate", lambda w: self.on_connect_best_server())
        menu.append(best_item)
        
        # Notfall-Reset (immer verfügbar)
        self.reset_item = Gtk.MenuItem(label=tr(
            "Verbindung zurücksetzen (Notfall)",
            'Reset connection (emergency)',
            'Réinitialiser la connexion (urgence)',
            'Restablecer conexión (emergencia)',
            'Ripristina connessione (emergenza)',
            'Repor ligação (emergência)'
        ))
        self.reset_item.connect("activate", lambda w: self.confirm_and_reset())
        menu.append(self.reset_item)

        menu.append(Gtk.SeparatorMenuItem())
        
        # Server-Auswahl Untermenü
        server_item = Gtk.MenuItem(label=tr(
            "Server wählen",
            'Choose server',
            'Choisir un serveur',
            'Elegir servidor',
            'Scegli server',
            'Escolher servidor'
        ))
        server_menu = Gtk.Menu()
        
        for code, name in self.vpn.get_servers().items():
            item = Gtk.MenuItem(label=f"{name} ({code})")
            item.connect("activate", self.on_select_server, code)
            server_menu.append(item)
        
        server_item.set_submenu(server_menu)
        menu.append(server_item)

        # Favoriten-Untermenü
        favorites_item = Gtk.MenuItem(label=tr(
            "Favoriten",
            'Favorites',
            'Favoris',
            'Favoritos',
            'Preferiti',
            'Favoritos'
        ))
        favorites_menu = Gtk.Menu()

        if self.vpn.favorite_servers:
            for code in self.vpn.favorite_servers:
                name = self.vpn.get_servers().get(code, code)
                item = Gtk.MenuItem(label=f"{name} ({code})")
                item.connect("activate", self.on_select_server, code)
                favorites_menu.append(item)
        else:
            no_fav_item = Gtk.MenuItem(label=tr(
                "(keine Favoriten)",
                '(no favorites)',
                '(aucun favori)',
                '(sin favoritos)',
                '(nessun preferito)',
                '(sem favoritos)'
            ))
            no_fav_item.set_sensitive(False)
            favorites_menu.append(no_fav_item)

        favorites_menu.append(Gtk.SeparatorMenuItem())

        add_current_item = Gtk.MenuItem(label=tr(
            "Aktuellen Server zu Favoriten",
            'Add current server to favorites',
            'Ajouter le serveur actuel aux favoris',
            'Añadir el servidor actual a favoritos',
            'Aggiungi il server attuale ai preferiti',
            'Adicionar o servidor atual aos favoritos'
        ))
        add_current_item.connect("activate", lambda w: self.on_add_current_favorite())
        favorites_menu.append(add_current_item)

        remove_current_item = Gtk.MenuItem(label=tr(
            "Aktuellen Server aus Favoriten",
            'Remove current server from favorites',
            'Retirer le serveur actuel des favoris',
            'Eliminar el servidor actual de favoritos',
            'Rimuovi il server attuale dai preferiti',
            'Remover o servidor atual dos favoritos'
        ))
        remove_current_item.connect("activate", lambda w: self.on_remove_current_favorite())
        favorites_menu.append(remove_current_item)

        favorites_item.set_submenu(favorites_menu)
        menu.append(favorites_item)
        
        # Aktueller Server
        self.current_server_item = Gtk.MenuItem(
            label=tr(
                f"Aktuell: {self.vpn.current_server}",
                f'Current: {self.vpn.current_server}',
                f'Actuel : {self.vpn.current_server}',
                f'Actual: {self.vpn.current_server}',
                f'Attuale: {self.vpn.current_server}',
                f'Atual: {self.vpn.current_server}'
            )
        )
        self.current_server_item.set_sensitive(False)
        menu.append(self.current_server_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Info
        info_item = Gtk.MenuItem(label=tr(
            "Über",
            'About',
            'À propos',
            'Acerca de',
            'Informazioni',
            'Sobre'
        ))
        info_item.connect("activate", self.show_about)
        menu.append(info_item)
        
        # Beenden
        quit_item = Gtk.MenuItem(label=tr(
            "Beenden",
            'Quit',
            'Quitter',
            'Salir',
            'Esci',
            'Sair'
        ))
        quit_item.connect("activate", self.on_quit)
        menu.append(quit_item)
        
        menu.show_all()
        
        if self.use_appindicator:
            self.indicator.set_menu(menu)
        else:
            self.menu = menu

    def refresh_menu(self):
        """Baut Menü neu auf, z.B. nach Favoriten-Änderung."""
        self.build_menu()
        self.update_status()
    
    def on_statusicon_popup(self, icon, button, time):
        """Zeigt Menü bei Rechtsklick auf StatusIcon"""
        self.menu.popup(None, None, None, None, button, time)
    
    def on_statusicon_activate(self, icon):
        """Linksklick auf StatusIcon - Zeigt Status und Server-Auswahl"""
        self.show_status_dialog()
    
    def update_status(self):
        """Aktualisiert Status-Anzeige"""
        try:
            connected = self.vpn.get_status()
            
            # Icon und Labels aktualisieren
            if connected:
                icon_name = "network-vpn"
                status_text = tr(
                    "Status: Verbunden ✓",
                    'Status: Connected ✓',
                    'État : Connecté ✓',
                    'Estado: Conectado ✓',
                    'Stato: Connesso ✓',
                    'Estado: Ligado ✓'
                )
                toggle_text = tr(
                    "Trennen",
                    'Disconnect',
                    'Se déconnecter',
                    'Desconectar',
                    'Disconnetti',
                    'Desligar'
                )
                tooltip = tr(
                    f"Hide.me VPN - Verbunden mit {self.vpn.current_server}",
                    f'Hide.me VPN - Connected to {self.vpn.current_server}',
                    f'Hide.me VPN - Connecté à {self.vpn.current_server}',
                    f'Hide.me VPN - Conectado a {self.vpn.current_server}',
                    f'Hide.me VPN - Connesso a {self.vpn.current_server}',
                    f'Hide.me VPN - Ligado a {self.vpn.current_server}'
                )
            else:
                icon_name = "network-vpn-disconnected"
                status_text = tr(
                    "Status: Getrennt",
                    'Status: Disconnected',
                    'État : Déconnecté',
                    'Estado: Desconectado',
                    'Stato: Disconnesso',
                    'Estado: Desligado'
                )
                toggle_text = tr(
                    "Verbinden",
                    'Connect',
                    'Se connecter',
                    'Conectar',
                    'Connetti',
                    'Ligar'
                )
                tooltip = tr(
                    "Hide.me VPN - Getrennt",
                    'Hide.me VPN - Disconnected',
                    'Hide.me VPN - Déconnecté',
                    'Hide.me VPN - Desconectado',
                    'Hide.me VPN - Disconnesso',
                    'Hide.me VPN - Desligado'
                )
            
            # Icon aktualisieren (je nach Modus)
            if self.use_appindicator:
                self.indicator.set_icon(icon_name)
            else:
                self.status_icon.set_from_icon_name(icon_name)
                self.status_icon.set_tooltip_text(tooltip)
            
            # Menu-Items aktualisieren
            self.status_item.set_label(status_text)
            self.toggle_item.set_label(toggle_text)
            
            # Server-Info
            self.current_server_item.set_label(
                tr(
                    f"Aktuell: {self.vpn.current_server}",
                    f'Current: {self.vpn.current_server}',
                    f'Actuel : {self.vpn.current_server}',
                    f'Actual: {self.vpn.current_server}',
                    f'Attuale: {self.vpn.current_server}',
                    f'Atual: {self.vpn.current_server}'
                )
            )
        except Exception as e:
            print(tr(
                f"Status-Update fehlgeschlagen: {e}",
                f'Status update failed: {e}',
                f"Échec de la mise à jour de l'état : {e}",
                f'Error al actualizar el estado: {e}',
                f'Aggiornamento dello stato non riuscito: {e}',
                f'Falha ao atualizar o estado: {e}'
            ))
        
        return True  # Weiter ausführen
    
    def on_toggle_connection(self, widget):
        """Verbindet oder trennt VPN"""
        def do_toggle():
            if self.vpn.connected:
                success, message = self.vpn.disconnect()
            else:
                success, message = self.vpn.connect()
            
            GLib.idle_add(self.show_notification, 
                         "Hide.me VPN", 
                         message,
                         "network-vpn" if success else "dialog-error")
            GLib.idle_add(self.update_status)
        
        # In Thread ausführen um UI nicht zu blockieren
        thread = threading.Thread(target=do_toggle)
        thread.daemon = True
        thread.start()

    def ping_server_ms(self, server_code):
        """Misst Ping für hide.me Server und gibt ms zurück."""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '1', f'{server_code}.hideservers.net'],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode != 0:
                return None
            match = re.search(r'time=([\d\.]+)\s*ms', result.stdout)
            if not match:
                return None
            return float(match.group(1))
        except Exception:
            return None

    def ping_servers_background(self, servers, update_callback=None):
        """Misst Pings für gegebene Server im Hintergrund."""
        def run():
            for server in servers:
                code = server.get('code')
                if not code:
                    continue
                ping = self.ping_server_ms(code)
                if ping is not None:
                    self.server_ping_cache[code] = ping
                if update_callback:
                    GLib.idle_add(update_callback, code, ping)

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def find_best_server(self):
        """Findet Server mit bestem Ping."""
        best_code = None
        best_ping = None
        for code in self.vpn.get_servers().keys():
            ping = self.ping_server_ms(code)
            if ping is None:
                continue
            if best_ping is None or ping < best_ping:
                best_ping = ping
                best_code = code
        return best_code, best_ping

    def on_connect_best_server(self):
        """Verbindet mit dem Server mit dem besten Ping."""
        def connect_best():
            best_code, best_ping = self.find_best_server()
            if not best_code:
                GLib.idle_add(
                    self.show_notification,
                    "Hide.me VPN",
                    tr(
                        "Kein erreichbarer Server für Best Location gefunden",
                        'No reachable server found for Best Location',
                        'Aucun serveur accessible trouvé pour Best Location',
                        'No se encontró ningún servidor accesible para Best Location',
                        'Nessun server raggiungibile trovato per Best Location',
                        'Nenhum servidor acessível encontrado para Best Location'
                    ),
                    "dialog-error"
                )
                return

            if self.vpn.connected:
                self.vpn.disconnect()
                time.sleep(1)

            success, message = self.vpn.connect(best_code)
            if success:
                message = f"{message} (Ping {best_ping:.0f} ms)"

            GLib.idle_add(
                self.show_notification,
                "Hide.me VPN",
                message,
                "network-vpn" if success else "dialog-error"
            )
            GLib.idle_add(self.update_status)

        thread = threading.Thread(target=connect_best)
        thread.daemon = True
        thread.start()
    
    def on_select_server(self, widget, server_code):
        """Wählt einen Server aus"""
        if self.vpn.connected:
            # Wenn verbunden, trennen und neu verbinden
            def reconnect():
                self.vpn.disconnect()
                time.sleep(1)
                success, message = self.vpn.connect(server_code)
                GLib.idle_add(self.show_notification, 
                             "Hide.me VPN",
                             message,
                             "network-vpn" if success else "dialog-error")
                GLib.idle_add(self.update_status)
            
            thread = threading.Thread(target=reconnect)
            thread.daemon = True
            thread.start()
        else:
            # Nur Server speichern
            self.vpn.current_server = server_code
            self.vpn.save_config()
            self.update_status()
            self.show_notification(
                "Hide.me VPN",
                tr(
                    f"Server gewechselt zu {server_code}",
                    f'Server changed to {server_code}',
                    f'Serveur changé pour {server_code}',
                    f'Servidor cambiado a {server_code}',
                    f'Server cambiato in {server_code}',
                    f'Servidor alterado para {server_code}'
                ),
                "network-vpn"
            )

    def on_add_current_favorite(self):
        """Fügt aktuellen Server zu Favoriten hinzu."""
        success, message = self.vpn.add_favorite_server(self.vpn.current_server)
        self.show_notification(
            "Hide.me VPN",
            message,
            "network-vpn" if success else "dialog-warning"
        )
        if success:
            self.refresh_menu()

    def on_remove_current_favorite(self):
        """Entfernt aktuellen Server aus Favoriten."""
        success, message = self.vpn.remove_favorite_server(self.vpn.current_server)
        self.show_notification(
            "Hide.me VPN",
            message,
            "network-vpn" if success else "dialog-warning"
        )
        if success:
            self.refresh_menu()

    def confirm_and_reset(self, parent_dialog=None):
        """Fragt Bestätigung ab und führt Notfall-Reset aus."""
        confirm_dialog = Gtk.MessageDialog(
            transient_for=parent_dialog,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text=tr(
                "Verbindung wirklich zurücksetzen?",
                'Reset the connection?',
                'Réinitialiser la connexion ?',
                '¿Restablecer la conexión?',
                'Ripristinare la connessione?',
                'Repor a ligação?'
            )
        )
        confirm_dialog.format_secondary_text(
            tr(
                "Der Notfall-Reset stoppt alle hide.me Dienste und setzt Routing/DNS zurück.",
                'The emergency reset stops all hide.me services and resets routing/DNS.',
                "La réinitialisation d'urgence arrête tous les services hide.me et réinitialise le routage/DNS.",
                'El restablecimiento de emergencia detiene todos los servicios hide.me y restablece las rutas y el DNS.',
                'Il ripristino di emergenza arresta tutti i servizi hide.me e ripristina routing/DNS.',
                'A reposição de emergência para todos os serviços hide.me e repõe o encaminhamento/DNS.'
            )
        )
        confirm_dialog.add_button(tr(
            "Nein",
            "No",
            'Non',
            'No',
            'No',
            'Não'
        ), Gtk.ResponseType.NO)
        confirm_dialog.add_button(tr(
            "Ja",
            "Yes",
            'Oui',
            'Sí',
            'Sì',
            'Sim'
        ), Gtk.ResponseType.YES)
        response = confirm_dialog.run()
        confirm_dialog.destroy()

        if response != Gtk.ResponseType.YES:
            return

        if parent_dialog:
            parent_dialog.destroy()

        def do_reset():
            success, message = self.vpn.emergency_reset()
            GLib.idle_add(
                self.show_notification,
                "Hide.me VPN",
                message,
                "network-vpn" if success else "dialog-error"
            )
            GLib.idle_add(self.update_status)

        thread = threading.Thread(target=do_reset)
        thread.daemon = True
        thread.start()
    
    def show_notification(self, title, message, icon="network-vpn"):
        """Zeigt Desktop-Benachrichtigung"""
        if not HAS_NOTIFY:
            print(tr(
                f"[Benachrichtigung] {title}: {message}",
                f'[Notification] {title}: {message}',
                f'[Notification] {title} : {message}',
                f'[Notificación] {title}: {message}',
                f'[Notifica] {title}: {message}',
                f'[Notificação] {title}: {message}'
            ))
            return
        
        try:
            notification = Notify.Notification.new(title, message, icon)
            notification.show()
        except Exception as e:
            print(tr(
                f"Benachrichtigung fehlgeschlagen: {e}",
                f'Notification failed: {e}',
                f'Échec de la notification : {e}',
                f'Error de notificación: {e}',
                f'Notifica non riuscita: {e}',
                f'Falha na notificação: {e}'
            ))
    
    def show_about(self, widget):
        """Zeigt Info-Dialog"""
        dialog = Gtk.AboutDialog()
        dialog.set_program_name("Hide.me VPN GUI")
        dialog.set_version(__version__)
        dialog.set_comments(
            tr(
                "Benutzerfreundliche GUI für hide.me CLI\n\n"
            "Funktionen:\n"
            "• Einfaches Verbinden/Trennen\n"
            "• Server-Auswahl\n"
            "• Status-Anzeige im System Tray\n"
            "• Desktop-Benachrichtigungen",
                'Easy-to-use GUI for hide.me CLI\n\nFeatures:\n• Connect/disconnect easily\n• Server selection\n• System tray status\n• Desktop notifications',
                'Interface simple pour hide.me CLI\n\nFonctionnalités :\n• Connexion/déconnexion facile\n• Sélection du serveur\n• État dans la barre système\n• Notifications',
                'Interfaz sencilla para hide.me CLI\n\nFunciones:\n• Conexión/desconexión sencilla\n• Selección de servidor\n• Estado en la bandeja del sistema\n• Notificaciones',
                "Interfaccia semplice per hide.me CLI\n\nFunzioni:\n• Connessione/disconnessione semplice\n• Selezione del server\n• Stato nell'area di notifica\n• Notifiche desktop",
                'Interface simples para hide.me CLI\n\nFuncionalidades:\n• Ligar/desligar facilmente\n• Seleção de servidor\n• Estado na área de notificação\n• Notificações'
            )
        )
        dialog.set_website(f"https://github.com/{GITHUB_REPO}")
        dialog.set_website_label(tr(
            "GitHub-Projekt öffnen",
            'Open GitHub project',
            'Ouvrir le projet GitHub',
            'Abrir el proyecto en GitHub',
            'Apri il progetto GitHub',
            'Abrir o projeto no GitHub'
        ))
        dialog.set_authors(["RechnerLotsen"])
        dialog.set_copyright("RechnerLotsen 2025-2026")
        dialog.run()
        dialog.destroy()
    
    def show_error_dialog(self, title, message):
        """Zeigt Fehler-Dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def show_status_dialog(self):
        """Zeigt VPN-Status und Server-Auswahl Dialog"""
        # Nur ein Status-Fenster gleichzeitig erlauben
        if self.status_dialog is not None and self.status_dialog.get_visible():
            self.status_dialog.present()
            return

        # Status prüfen
        connected = self.vpn.get_status()
        
        dialog = Gtk.Dialog(
            title=tr("Hide.me VPN Status", "Hide.me VPN Status", "État de Hide.me VPN",
                     "Estado de Hide.me VPN", "Stato di Hide.me VPN", "Estado do Hide.me VPN"),
            parent=None,
            flags=0
        )
        dialog.set_default_size(400, 500)
        dialog.connect("destroy", self.on_status_dialog_destroy)
        self.status_dialog = dialog
        
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        # Status-Anzeige
        if connected:
            status_label = Gtk.Label()
            status_label.set_markup(
                tr(
                    f"<b>✓ Verbunden</b>\n"
                f"Server: {self.vpn.current_server}",
                    f'<b>✓ Connected</b>\nServer: {self.vpn.current_server}',
                    f'<b>✓ Connecté</b>\nServeur : {self.vpn.current_server}',
                    f'<b>✓ Conectado</b>\nServidor: {self.vpn.current_server}',
                    f'<b>✓ Connesso</b>\nServer: {self.vpn.current_server}',
                    f'<b>✓ Ligado</b>\nServidor: {self.vpn.current_server}'
                )
            )
            box.pack_start(status_label, False, False, 0)
            
            # Trennen-Button
            disconnect_btn = Gtk.Button(label=tr(
                "Verbindung trennen",
                'Disconnect',
                'Se déconnecter',
                'Desconectar',
                'Disconnetti',
                'Desligar'
            ))
            disconnect_btn.connect("clicked", lambda w: self.disconnect_and_close(dialog))
            box.pack_start(disconnect_btn, False, False, 0)

            # Notfall-Reset
            reset_btn = Gtk.Button(label=tr(
                "Verbindung zurücksetzen (Notfall)",
                'Reset connection (emergency)',
                'Réinitialiser la connexion (urgence)',
                'Restablecer conexión (emergencia)',
                'Ripristina connessione (emergenza)',
                'Repor ligação (emergência)'
            ))
            reset_btn.connect("clicked", lambda w: self.confirm_and_reset(dialog))
            box.pack_start(reset_btn, False, False, 0)
        else:
            status_label = Gtk.Label()
            status_label.set_markup(tr(
                "<b>✗ Nicht verbunden</b>",
                '<b>✗ Not connected</b>',
                '<b>✗ Non connecté</b>',
                '<b>✗ No conectado</b>',
                '<b>✗ Non connesso</b>',
                '<b>✗ Não ligado</b>'
            ))
            box.pack_start(status_label, False, False, 0)

            best_btn = Gtk.Button(label=tr(
                "Mit bestem Server verbinden",
                'Connect to best server',
                'Se connecter au meilleur serveur',
                'Conectar al mejor servidor',
                'Connetti al server migliore',
                'Ligar ao melhor servidor'
            ))
            best_btn.connect("clicked", lambda w: (dialog.destroy(), self.on_connect_best_server()))
            box.pack_start(best_btn, False, False, 0)

            # Notfall-Reset auch ohne bestehende Verbindung
            reset_btn = Gtk.Button(label=tr(
                "Verbindung zurücksetzen (Notfall)",
                'Reset connection (emergency)',
                'Réinitialiser la connexion (urgence)',
                'Restablecer conexión (emergencia)',
                'Ripristina connessione (emergenza)',
                'Repor ligação (emergência)'
            ))
            reset_btn.connect("clicked", lambda w: self.confirm_and_reset(dialog))
            box.pack_start(reset_btn, False, False, 0)

        # Server-Liste immer anzeigen (auch wenn bereits verbunden).
        self.populate_server_list(dialog, box, None, self.cached_servers)
        
        dialog.add_button(tr(
            "Schließen",
            'Close',
            'Fermer',
            'Cerrar',
            'Chiudi',
            'Fechar'
        ), Gtk.ResponseType.CLOSE)
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def on_status_dialog_destroy(self, dialog):
        """Setzt Referenz beim Schließen des Status-Dialogs zurück."""
        if self.status_dialog is dialog:
            self.status_dialog = None
    
    def populate_server_list(self, dialog, box, loading_label, servers):
        """Füllt Dialog mit Server-Liste"""
        if loading_label:
            box.remove(loading_label)
        
        if not servers:
            # Fallback auf statische Liste
            error_label = Gtk.Label()
            error_label.set_markup(
                tr(
                    "<i>Server-Liste konnte nicht geladen werden.\n"
                "Verwende Fallback-Liste...</i>",
                    '<i>Could not load server list.\nUsing fallback list...</i>',
                    '<i>Impossible de charger les serveurs.\nUtilisation de la liste de secours...</i>',
                    '<i>No se pudieron cargar los servidores.\nUsando la lista de respaldo...</i>',
                    '<i>Impossibile caricare i server.\nUso della lista di riserva...</i>',
                    '<i>Não foi possível carregar os servidores.\nA usar a lista alternativa...</i>'
                )
            )
            box.pack_start(error_label, False, False, 0)
            
            servers = []
            for code, country in self.vpn.get_servers().items():
                servers.append({
                    'code': code,
                    'display': country,
                    'city': '',
                    'country': country
                })
        
        # Server-Auswahl Label
        select_label = Gtk.Label()
        select_label.set_markup(tr(
            "<b>Server auswählen:</b>",
            '<b>Select a server:</b>',
            '<b>Sélectionnez un serveur :</b>',
            '<b>Selecciona un servidor:</b>',
            '<b>Seleziona un server:</b>',
            '<b>Selecione um servidor:</b>'
        ))
        box.pack_start(select_label, False, False, 0)
        
        # Scrollbare Liste
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(300)
        
        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        
        for server in servers:
            row = Gtk.ListBoxRow()
            code = server.get('code', '')
            ping = self.server_ping_cache.get(code)
            ping_text = f" ({int(ping)} ms)" if ping is not None else " (… ms)"
            label = Gtk.Label(label=f"{server['display']}{ping_text}", xalign=0)
            label.set_margin_start(10)
            label.set_margin_end(10)
            label.set_margin_top(5)
            label.set_margin_bottom(5)
            row.add(label)
            row.server_data = server
            row.server_label = label
            listbox.add(row)
        
        scrolled.add(listbox)
        box.pack_start(scrolled, True, True, 0)
        
        # Verbinden-Button
        connect_btn = Gtk.Button(label=tr(
            "Verbinden",
            'Connect',
            'Se connecter',
            'Conectar',
            'Connetti',
            'Ligar'
        ))
        connect_btn.connect("clicked", lambda w: self.connect_selected_server(dialog, listbox))
        box.pack_start(connect_btn, False, False, 0)
        
        dialog.add_button(tr(
            "Abbrechen",
            'Cancel',
            'Annuler',
            'Cancelar',
            'Annulla',
            'Cancelar'
        ), Gtk.ResponseType.CANCEL)
        dialog.show_all()

        def update_ping_label(server_code, ping):
            if ping is None:
                return False
            for row in listbox.get_children():
                row_code = row.server_data.get('code')
                if row_code == server_code:
                    display = row.server_data.get('display', row_code)
                    row.server_label.set_text(f"{display} ({int(ping)} ms)")
                    break
            return False

        # Ping-Messung live nachladen, damit Latenz neben jedem Server erscheint.
        self.ping_servers_background(servers, update_callback=update_ping_label)
    
    def connect_selected_server(self, dialog, listbox):
        """Verbindet mit ausgewähltem Server"""
        selected_row = listbox.get_selected_row()
        if not selected_row:
            self.show_notification(
                tr(
                    "Keine Auswahl",
                    'No selection',
                    'Aucune sélection',
                    'Sin selección',
                    'Nessuna selezione',
                    'Nenhuma seleção'
                ),
                tr(
                    "Bitte wähle einen Server aus",
                    'Please select a server',
                    'Veuillez sélectionner un serveur',
                    'Selecciona un servidor',
                    'Seleziona un server',
                    'Selecione um servidor'
                ),
                "dialog-warning"
            )
            return
        
        server = selected_row.server_data
        dialog.destroy()
        
        # Verbinde in Thread
        def connect():
            selected_code = server['code']

            if self.vpn.connected:
                if selected_code == self.vpn.current_server:
                    success, message = True, tr(
                        f"Bereits verbunden mit {selected_code}",
                        f'Already connected to {selected_code}',
                        f'Déjà connecté à {selected_code}',
                        f'Ya conectado a {selected_code}',
                        f'Già connesso a {selected_code}',
                        f'Já ligado a {selected_code}'
                    )
                else:
                    self.vpn.disconnect()
                    time.sleep(1)
                    success, message = self.vpn.connect(selected_code)
            else:
                success, message = self.vpn.connect(selected_code)

            GLib.idle_add(self.show_notification,
                         "Hide.me VPN",
                         message,
                         "network-vpn" if success else "dialog-error")
            GLib.idle_add(self.update_status)
        
        thread = threading.Thread(target=connect)
        thread.daemon = True
        thread.start()
    
    def disconnect_and_close(self, dialog):
        """Trennt VPN und schließt Dialog"""
        dialog.destroy()
        
        def disconnect():
            success, message = self.vpn.disconnect()
            GLib.idle_add(self.show_notification,
                         "Hide.me VPN",
                         message,
                         "network-vpn" if success else "dialog-error")
            GLib.idle_add(self.update_status)
        
        thread = threading.Thread(target=disconnect)
        thread.daemon = True
        thread.start()
    
    def on_quit(self, widget):
        """Beendet Anwendung"""
        if HAS_NOTIFY:
            Notify.uninit()
        Gtk.main_quit()


def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(description=tr(
        "Hide.me VPN GUI und CLI-Helfer",
        'Hide.me VPN GUI and CLI helpers',
        'Interface hide.me VPN et outils CLI',
        'Interfaz de hide.me VPN y herramientas CLI',
        'Interfaccia hide.me VPN e strumenti CLI',
        'Interface hide.me VPN e ferramentas CLI'
    ))
    parser.add_argument(
        "--emergency-reset",
        action="store_true",
        help=tr(
            "Führt Notfall-Reset (Routing/DNS/VPN) per pkexec aus",
            'Run emergency reset (routing/DNS/VPN) via pkexec',
            "Réinitialisation d'urgence (routage/DNS/VPN) via pkexec",
            'Restablecimiento de emergencia (rutas/DNS/VPN) mediante pkexec',
            'Ripristino di emergenza (routing/DNS/VPN) tramite pkexec',
            'Reposição de emergência (encaminhamento/DNS/VPN) via pkexec'
        )
    )
    args = parser.parse_args()

    if args.emergency_reset:
        vpn = HideMeVPN()
        if not vpn.is_installed():
            print(tr(
                "Hide.me CLI nicht installiert.",
                'Hide.me CLI is not installed.',
                "Hide.me CLI n'est pas installé.",
                'Hide.me CLI no está instalado.',
                'Hide.me CLI non è installato.',
                'Hide.me CLI não está instalado.'
            ))
            sys.exit(1)
        success, message = vpn.emergency_reset()
        print(message)
        sys.exit(0 if success else 1)

    # Prüfe benötigte Pakete
    missing = []
    if not HAS_APPINDICATOR:
        missing.append(tr(
            "gir1.2-appindicator3-0.1 (empfohlen)",
            'gir1.2-appindicator3-0.1 (recommended)',
            'gir1.2-appindicator3-0.1 (recommandé)',
            'gir1.2-appindicator3-0.1 (recomendado)',
            'gir1.2-appindicator3-0.1 (consigliato)',
            'gir1.2-appindicator3-0.1 (recomendado)'
        ))
    if not HAS_NOTIFY:
        missing.append(tr(
            "gir1.2-notify-0.7 (empfohlen)",
            'gir1.2-notify-0.7 (recommended)',
            'gir1.2-notify-0.7 (recommandé)',
            'gir1.2-notify-0.7 (recomendado)',
            'gir1.2-notify-0.7 (consigliato)',
            'gir1.2-notify-0.7 (recomendado)'
        ))
    
    if missing:
        print(tr(
            "\n⚠️  Optionale Pakete fehlen:",
            '\n⚠️  Optional packages missing:',
            '\n⚠️  Paquets optionnels manquants :',
            '\n⚠️  Faltan paquetes opcionales:',
            '\n⚠️  Pacchetti opzionali mancanti:',
            '\n⚠️  Pacotes opcionais em falta:'
        ))
        for pkg in missing:
            print(f"   - {pkg}")
        print(tr(
            "\nInstalliere mit: sudo apt install ",
            '\nInstall with: sudo apt install ',
            '\nInstallez avec : sudo apt install ',
            '\nInstala con: sudo apt install ',
            '\nInstalla con: sudo apt install ',
            '\nInstale com: sudo apt install '
        ) + " ".join(p.split()[0] for p in missing))
        print(tr(
            "\nDie GUI funktioniert auch ohne diese Pakete, aber mit eingeschränkten Features.\n",
            '\nThe GUI also works without these packages, but with limited features.\n',
            "\nL'interface fonctionne sans ces paquets, mais avec des fonctionnalités limitées.\n",
            '\nLa interfaz funciona sin estos paquetes, pero con funciones limitadas.\n',
            "\nL'interfaccia funziona senza questi pacchetti, ma con funzionalità limitate.\n",
            '\nA interface funciona sem estes pacotes, mas com funcionalidades limitadas.\n'
        ))
    
    indicator = HideMeIndicator()
    Gtk.main()


if __name__ == "__main__":
    main()
