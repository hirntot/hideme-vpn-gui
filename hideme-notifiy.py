#!/usr/bin/env python3
"""
Hide.me VPN Notification Bar / System Tray GUI
Benutzerfreundliche GUI für hide.me CLI VPN
"""

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
import threading
import time
import urllib.request
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
        self.load_config()
    
    def load_config(self):
        """Lädt gespeicherte Konfiguration"""
        os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.current_server = config.get('last_server', 'nl')
        except Exception as e:
            print(f"Config laden fehlgeschlagen: {e}")
            self.current_server = 'nl'
    
    def save_config(self):
        """Speichert aktuelle Konfiguration"""
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump({'last_server': self.current_server}, f)
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
        self.cached_servers = None  # Cache für Server-Liste
        
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
                print(f"✓ {len(servers)} Server geladen")
            else:
                print("⚠️  Server-Liste konnte nicht geladen werden - verwende Fallback")
        
        thread = threading.Thread(target=load)
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
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Hide.me VPN GUI"
        )
        dialog.format_secondary_text(
            "Benutzerfreundliche GUI für hide.me CLI\n\n"
            "Funktionen:\n"
            "• Einfaches Verbinden/Trennen\n"
            "• Server-Auswahl\n"
            "• Status-Anzeige im System Tray\n"
            "• Desktop-Benachrichtigungen\n\n"
            "RechnerLotsen 2025"
        )
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
        # Status prüfen
        connected = self.vpn.get_status()
        
        dialog = Gtk.Dialog(
            title="Hide.me VPN Status",
            parent=None,
            flags=0
        )
        dialog.set_default_size(400, 500)
        
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
        else:
            status_label = Gtk.Label()
            status_label.set_markup("<b>✗ Nicht verbunden</b>")
            box.pack_start(status_label, False, False, 0)
            
            # Verwende gecachte Server-Liste (beim Start geladen)
            self.populate_server_list(dialog, box, None, self.cached_servers)
            
            dialog.run()
            dialog.destroy()
            return
        
        dialog.add_button("Schließen", Gtk.ResponseType.CLOSE)
        dialog.show_all()
        dialog.run()
        dialog.destroy()
    
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
            label = Gtk.Label(label=server['display'], xalign=0)
            label.set_margin_start(10)
            label.set_margin_end(10)
            label.set_margin_top(5)
            label.set_margin_bottom(5)
            row.add(label)
            row.server_data = server
            listbox.add(row)
        
        scrolled.add(listbox)
        box.pack_start(scrolled, True, True, 0)
        
        # Verbinden-Button
        connect_btn = Gtk.Button(label="Verbinden")
        connect_btn.connect("clicked", lambda w: self.connect_selected_server(dialog, listbox))
        box.pack_start(connect_btn, False, False, 0)
        
        dialog.add_button("Abbrechen", Gtk.ResponseType.CANCEL)
        dialog.show_all()
    
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
            success, message = self.vpn.connect(server['code'])
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
