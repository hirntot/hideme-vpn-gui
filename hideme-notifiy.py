#!/usr/bin/env python3
"""
Hide.me VPN Notification Bar / System Tray GUI
Benutzerfreundliche GUI für hide.me CLI VPN
"""

__version__ = "1.0.0"
GITHUB_REPO = "hirntot/hideme-vpn-gui"

import gi
gi.require_version('Gtk', '3.0')

# Versuche AppIndicator3 zu laden, sonst Fallback auf StatusIcon
try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3
    HAS_APPINDICATOR = True
except (ValueError, ImportError):
    HAS_APPINDICATOR = False
    print("AppIndicator3 nicht verfügbar - verwende GTK StatusIcon Fallback")
    print("Für bessere Integration installiere: sudo apt install gir1.2-appindicator3-0.1")

# Versuche Notify zu laden
try:
    gi.require_version('Notify', '0.7')
    from gi.repository import Notify
    HAS_NOTIFY = True
except (ValueError, ImportError):
    HAS_NOTIFY = False
    print("Notify nicht verfügbar - keine Desktop-Benachrichtigungen")
    print("Für Benachrichtigungen installiere: sudo apt install gir1.2-notify-0.7")

from gi.repository import Gtk, GLib, GdkPixbuf
import subprocess
import os
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
                    self.cached_servers = config.get('cached_servers', [])
                    if not isinstance(self.cached_servers, list):
                        self.cached_servers = []
        except Exception as e:
            print(f"Config laden fehlgeschlagen: {e}")
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
                    'cached_servers': self.cached_servers
                }, f)
        except Exception as e:
            print(f"Config speichern fehlgeschlagen: {e}")
    
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
            print(f"Status-Check fehlgeschlagen: {e}")
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
            return True, f"Verbunden mit {self.current_server}"
        except subprocess.CalledProcessError as e:
            return False, f"Verbindung fehlgeschlagen: {e}"
        except Exception as e:
            return False, f"Fehler: {e}"
    
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
            return True, "VPN getrennt"
        except subprocess.CalledProcessError as e:
            return False, f"Trennung fehlgeschlagen: {e}"
        except Exception as e:
            return False, f"Fehler: {e}"

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
            return True, "Notfall-Reset abgeschlossen. Netzwerk wurde zurückgesetzt."
        except subprocess.CalledProcessError as e:
            return False, f"Notfall-Reset fehlgeschlagen: {e}"
        except Exception as e:
            return False, f"Fehler beim Notfall-Reset: {e}"
    
    def get_servers(self):
        """Liste verfügbarer Server/Regionen (Fallback)"""
        return {
            'nl': 'Niederlande',
            'de': 'Deutschland', 
            'us': 'USA',
            'gb': 'Großbritannien',
            'ch': 'Schweiz',
            'fr': 'Frankreich',
            'es': 'Spanien',
            'it': 'Italien',
            'se': 'Schweden',
            'no': 'Norwegen',
            'dk': 'Dänemark',
            'ca': 'Kanada',
            'au': 'Australien',
            'jp': 'Japan',
            'sg': 'Singapur',
        }

    def add_favorite_server(self, server_code):
        """Fügt Server zu Favoriten hinzu."""
        if server_code not in self.get_servers():
            return False, f"Unbekannter Server: {server_code}"
        if server_code in self.favorite_servers:
            return False, f"{server_code} ist bereits in den Favoriten"
        self.favorite_servers.append(server_code)
        self.save_config()
        return True, f"{server_code} zu Favoriten hinzugefügt"

    def remove_favorite_server(self, server_code):
        """Entfernt Server aus Favoriten."""
        if server_code not in self.favorite_servers:
            return False, f"{server_code} ist nicht in den Favoriten"
        self.favorite_servers.remove(server_code)
        self.save_config()
        return True, f"{server_code} aus Favoriten entfernt"

    def set_cached_servers(self, servers):
        """Speichert online geladene Serverliste dauerhaft für Offline-Fallback."""
        if not isinstance(servers, list):
            return
        self.cached_servers = servers
        self.save_config()
    
    def fetch_servers_from_website(self):
        """Lädt aktuelle Server-Liste von hide.me Website"""
        try:
            url = 'https://hide.me/de/network'
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
            print(f"Fehler beim Laden der Server-Liste: {e}")
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
                "Hide.me CLI nicht installiert",
                "Bitte installiere zuerst hide.me CLI:\n"
                "sudo ./install.sh im hide.me Verzeichnis"
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
            print("Lade Server-Liste von hide.me Website...")
            servers = self.vpn.fetch_servers_from_website()
            if servers:
                self.cached_servers = servers
                self.vpn.set_cached_servers(servers)
                print(f"✓ {len(servers)} Server geladen")
            else:
                print("⚠️  Server-Liste konnte nicht geladen werden - verwende Fallback")
        
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
                        "Hide.me VPN Update verfügbar",
                        f"Neue Version gefunden: {latest} (installiert: {__version__})",
                        "system-software-update"
                    )
            except Exception as e:
                # Update-Check darf niemals die App-Funktion beeinträchtigen.
                print(f"Update-Check übersprungen: {e}")

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()
    
    def build_menu(self):
        """Erstellt das Indicator-Menü"""
        menu = Gtk.Menu()
        
        # Status & Server Dialog öffnen
        status_dialog_item = Gtk.MenuItem(label="Status & Server...")
        status_dialog_item.connect("activate", lambda w: self.show_status_dialog())
        menu.append(status_dialog_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Status-Item (nicht klickbar)
        self.status_item = Gtk.MenuItem(label="Status: Getrennt")
        self.status_item.set_sensitive(False)
        menu.append(self.status_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Verbinden/Trennen Button
        self.toggle_item = Gtk.MenuItem(label="Verbinden")
        self.toggle_item.connect("activate", self.on_toggle_connection)
        menu.append(self.toggle_item)

        # Best Location
        best_item = Gtk.MenuItem(label="Mit bestem Server verbinden")
        best_item.connect("activate", lambda w: self.on_connect_best_server())
        menu.append(best_item)
        
        # Notfall-Reset (immer verfügbar)
        self.reset_item = Gtk.MenuItem(label="Verbindung zurücksetzen (Notfall)")
        self.reset_item.connect("activate", lambda w: self.confirm_and_reset())
        menu.append(self.reset_item)

        menu.append(Gtk.SeparatorMenuItem())
        
        # Server-Auswahl Untermenü
        server_item = Gtk.MenuItem(label="Server wählen")
        server_menu = Gtk.Menu()
        
        for code, name in self.vpn.get_servers().items():
            item = Gtk.MenuItem(label=f"{name} ({code})")
            item.connect("activate", self.on_select_server, code)
            server_menu.append(item)
        
        server_item.set_submenu(server_menu)
        menu.append(server_item)

        # Favoriten-Untermenü
        favorites_item = Gtk.MenuItem(label="Favoriten")
        favorites_menu = Gtk.Menu()

        if self.vpn.favorite_servers:
            for code in self.vpn.favorite_servers:
                name = self.vpn.get_servers().get(code, code)
                item = Gtk.MenuItem(label=f"{name} ({code})")
                item.connect("activate", self.on_select_server, code)
                favorites_menu.append(item)
        else:
            no_fav_item = Gtk.MenuItem(label="(keine Favoriten)")
            no_fav_item.set_sensitive(False)
            favorites_menu.append(no_fav_item)

        favorites_menu.append(Gtk.SeparatorMenuItem())

        add_current_item = Gtk.MenuItem(label="Aktuellen Server zu Favoriten")
        add_current_item.connect("activate", lambda w: self.on_add_current_favorite())
        favorites_menu.append(add_current_item)

        remove_current_item = Gtk.MenuItem(label="Aktuellen Server aus Favoriten")
        remove_current_item.connect("activate", lambda w: self.on_remove_current_favorite())
        favorites_menu.append(remove_current_item)

        favorites_item.set_submenu(favorites_menu)
        menu.append(favorites_item)
        
        # Aktueller Server
        self.current_server_item = Gtk.MenuItem(
            label=f"Aktuell: {self.vpn.current_server}"
        )
        self.current_server_item.set_sensitive(False)
        menu.append(self.current_server_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Info
        info_item = Gtk.MenuItem(label="Über")
        info_item.connect("activate", self.show_about)
        menu.append(info_item)
        
        # Beenden
        quit_item = Gtk.MenuItem(label="Beenden")
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
                status_text = "Status: Verbunden ✓"
                toggle_text = "Trennen"
                tooltip = f"Hide.me VPN - Verbunden mit {self.vpn.current_server}"
            else:
                icon_name = "network-vpn-disconnected"
                status_text = "Status: Getrennt"
                toggle_text = "Verbinden"
                tooltip = "Hide.me VPN - Getrennt"
            
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
                f"Aktuell: {self.vpn.current_server}"
            )
        except Exception as e:
            print(f"Status-Update fehlgeschlagen: {e}")
        
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
                    "Kein erreichbarer Server für Best Location gefunden",
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
                f"Server gewechselt zu {server_code}",
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
            buttons=Gtk.ButtonsType.YES_NO,
            text="Verbindung wirklich zurücksetzen?"
        )
        confirm_dialog.format_secondary_text(
            "Der Notfall-Reset stoppt alle hide.me Dienste und setzt Routing/DNS zurück."
        )
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
            print(f"[Benachrichtigung] {title}: {message}")
            return
        
        try:
            notification = Notify.Notification.new(title, message, icon)
            notification.show()
        except Exception as e:
            print(f"Benachrichtigung fehlgeschlagen: {e}")
    
    def show_about(self, widget):
        """Zeigt Info-Dialog"""
        dialog = Gtk.AboutDialog()
        dialog.set_program_name("Hide.me VPN GUI")
        dialog.set_version(__version__)
        dialog.set_comments(
            "Benutzerfreundliche GUI für hide.me CLI\n\n"
            "Funktionen:\n"
            "• Einfaches Verbinden/Trennen\n"
            "• Server-Auswahl\n"
            "• Status-Anzeige im System Tray\n"
            "• Desktop-Benachrichtigungen"
        )
        dialog.set_website(f"https://github.com/{GITHUB_REPO}")
        dialog.set_website_label("GitHub-Projekt öffnen")
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
            title="Hide.me VPN Status",
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
                f"<b>✓ Verbunden</b>\n"
                f"Server: {self.vpn.current_server}"
            )
            box.pack_start(status_label, False, False, 0)
            
            # Trennen-Button
            disconnect_btn = Gtk.Button(label="Verbindung trennen")
            disconnect_btn.connect("clicked", lambda w: self.disconnect_and_close(dialog))
            box.pack_start(disconnect_btn, False, False, 0)

            # Notfall-Reset
            reset_btn = Gtk.Button(label="Verbindung zurücksetzen (Notfall)")
            reset_btn.connect("clicked", lambda w: self.confirm_and_reset(dialog))
            box.pack_start(reset_btn, False, False, 0)
        else:
            status_label = Gtk.Label()
            status_label.set_markup("<b>✗ Nicht verbunden</b>")
            box.pack_start(status_label, False, False, 0)

            best_btn = Gtk.Button(label="Mit bestem Server verbinden")
            best_btn.connect("clicked", lambda w: (dialog.destroy(), self.on_connect_best_server()))
            box.pack_start(best_btn, False, False, 0)

            # Notfall-Reset auch ohne bestehende Verbindung
            reset_btn = Gtk.Button(label="Verbindung zurücksetzen (Notfall)")
            reset_btn.connect("clicked", lambda w: self.confirm_and_reset(dialog))
            box.pack_start(reset_btn, False, False, 0)

        # Server-Liste immer anzeigen (auch wenn bereits verbunden).
        self.populate_server_list(dialog, box, None, self.cached_servers)
        
        dialog.add_button("Schließen", Gtk.ResponseType.CLOSE)
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
                "<i>Server-Liste konnte nicht geladen werden.\n"
                "Verwende Fallback-Liste...</i>"
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
        select_label.set_markup("<b>Server auswählen:</b>")
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
        connect_btn = Gtk.Button(label="Verbinden")
        connect_btn.connect("clicked", lambda w: self.connect_selected_server(dialog, listbox))
        box.pack_start(connect_btn, False, False, 0)
        
        dialog.add_button("Abbrechen", Gtk.ResponseType.CANCEL)
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
                "Keine Auswahl",
                "Bitte wähle einen Server aus",
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
                    success, message = True, f"Bereits verbunden mit {selected_code}"
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
    parser = argparse.ArgumentParser(description="Hide.me VPN GUI und CLI-Helfer")
    parser.add_argument(
        "--emergency-reset",
        action="store_true",
        help="Führt Notfall-Reset (Routing/DNS/VPN) per pkexec aus"
    )
    args = parser.parse_args()

    if args.emergency_reset:
        vpn = HideMeVPN()
        if not vpn.is_installed():
            print("Hide.me CLI nicht installiert.")
            sys.exit(1)
        success, message = vpn.emergency_reset()
        print(message)
        sys.exit(0 if success else 1)

    # Prüfe benötigte Pakete
    missing = []
    if not HAS_APPINDICATOR:
        missing.append("gir1.2-appindicator3-0.1 (empfohlen)")
    if not HAS_NOTIFY:
        missing.append("gir1.2-notify-0.7 (empfohlen)")
    
    if missing:
        print("\n⚠️  Optionale Pakete fehlen:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nInstalliere mit: sudo apt install " + " ".join(p.split()[0] for p in missing))
        print("\nDie GUI funktioniert auch ohne diese Pakete, aber mit eingeschränkten Features.\n")
    
    indicator = HideMeIndicator()
    Gtk.main()


if __name__ == "__main__":
    main()
