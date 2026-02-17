# Hide.me VPN GUI - Benutzerfreundliche Oberfläche

## 🎯 Problem gelöst!

Das hide.me CLI ist für normale Nutzer viel zu kompliziert. Diese GUI macht es einfach:

- ✅ **System Tray Icon** - Immer sichtbar, immer erreichbar
- ✅ **Ein-Klick Verbindung** - Einfach auf "Verbinden" klicken
- ✅ **Server-Auswahl** - Aus 15 Ländern wählen
- ✅ **Desktop-Benachrichtigungen** - Wissen was passiert
- ✅ **Autostart** - Beim Login automatisch verfügbar
- ✅ **Status-Anzeige** - Sofort sehen ob VPN aktiv ist

## ⚠️ Disclaimer

Diese Software ist eine inoffizielle GUI für die hide.me VPN CLI und wird ohne jegliche Gewährleistung bereitgestellt.

- **Keine Garantie** für Funktionalität, Sicherheit oder Datenschutz
- **Keine Haftung** für Schäden, Datenverlust oder Sicherheitsprobleme
- **Benutzung auf eigene Verantwortung**
- Diese Software ist **nicht offiziell von hide.me** - nur eine Community-Erweiterung
- Systemd und PolicyKit-Integration erfordert Root-Rechte - prüfen Sie den Code vor Installation
- Bei kritischen Anwendungen empfehlen wir professionelle VPN-Lösungen

**USE AT YOUR OWN RISK**

## 📋 Voraussetzungen

1. **Hide.me CLI muss installiert sein**
   - Download: https://hide.me/en/software/linux
   - Installation: `sudo ./install.sh`
   - Konfiguration mit Zugangsdaten durchführen

2. **Linux mit GTK3 Desktop** (Ubuntu, Mint, Debian, etc.)

## 🚀 Installation

```bash
cd /pfad/zu/spezalskripte/
sudo ./hideme-gui-install.sh
```

Das Skript:
- Prüft ob hide.me CLI installiert ist
- Installiert benötigte Python-Pakete
- Kopiert die GUI nach `/usr/local/bin`
- Erstellt Desktop-Integration
- Richtet Autostart ein
- Installiert PolicyKit-Regel (VPN ohne Passwort steuern)

## 💡 Verwendung

### Starten

**Variante 1:** Aus dem Anwendungsmenü
- Suche nach "Hide.me VPN"
- Klicke darauf

**Variante 2:** Terminal
```bash
hideme-vpn-gui
```

**Variante 3:** Automatisch
- Nach Installation startet die GUI automatisch beim Login

### Bedienung

Ein VPN-Icon erscheint im System Tray (Benachrichtigungsbereich):

1. **Verbinden:**
   - Klick auf Icon → "Verbinden"
   - Warte auf Benachrichtigung "Verbunden"
   - Icon ändert sich zu ✓

2. **Server wechseln:**
   - Klick auf Icon → "Server wählen" → Land auswählen
   - Wenn verbunden: Automatische Neuverbindung
   - Wenn getrennt: Server wird gespeichert für nächste Verbindung

3. **Trennen:**
   - Klick auf Icon → "Trennen"
   - Benachrichtigung bestätigt Trennung

4. **Status prüfen:**
   - Menü zeigt "Status: Verbunden ✓" oder "Status: Getrennt"
   - Icon zeigt visuell den Status
   - Aktueller Server wird angezeigt

## 🌍 Verfügbare Server

- 🇳🇱 Niederlande (nl) - Standard
- 🇩🇪 Deutschland (de)
- 🇬🇧 Großbritannien (gb)
- 🇨🇭 Schweiz (ch)
- 🇫🇷 Frankreich (fr)
- 🇪🇸 Spanien (es)
- 🇮🇹 Italien (it)
- 🇸🇪 Schweden (se)
- 🇳🇴 Norwegen (no)
- 🇩🇰 Dänemark (dk)
- 🇺🇸 USA (us)
- 🇨🇦 Kanada (ca)
- 🇦🇺 Australien (au)
- 🇯🇵 Japan (jp)
- 🇸🇬 Singapur (sg)

## 🔧 Technische Details

### Funktionsweise

Die GUI ist ein Python-Wrapper um das hide.me CLI:
- Verwendet `systemctl` zum Starten/Stoppen der VPN-Verbindung
- Nutzt `pkexec` für Root-Rechte (sauberer als sudo)
- Speichert Einstellungen in `~/.config/hideme-gui/config.json`
- Prüft Status alle 5 Sekunden

### Dateien

```
/usr/local/bin/hideme-vpn-gui          # Hauptprogramm
/usr/share/applications/...            # Desktop-Integration
/etc/polkit-1/rules.d/50-hideme-vpn.rules  # PolicyKit-Regel (ohne Passwort)
~/.config/autostart/...                # Autostart-Eintrag
~/.config/hideme-gui/config.json       # Benutzer-Einstellungen
/opt/hide.me/                          # hide.me CLI (muss schon existieren)
```

### Berechtigungen

Die GUI benötigt Root-Rechte nur für:
- `systemctl enable/disable/start/stop hide.me@SERVER`

Dank der PolicyKit-Regel (`50-hideme-vpn.rules`) wird **kein Passwort** mehr abgefragt.
Mitglieder der `sudo`-Gruppe können hide.me VPN-Services ohne Authentifizierung steuern.

## 🐛 Fehlerbehebung

### "Hide.me CLI nicht installiert"
```bash
# Prüfe Installation
ls -la /opt/hide.me/hide.me

# Wenn nicht vorhanden: Zuerst hide.me CLI installieren
cd ~/Downloads/hideme/
sudo ./install.sh
```

### "Access Token fehlt"
```bash
# Token manuell erstellen
cd /opt/hide.me
sudo ./hide.me token free.hideservers.net
# Zugangsdaten eingeben: Rgnd2HqK33 / Passwort
```

### "Icon erscheint nicht im Tray"
```bash
# Prüfe ob AppIndicator3 unterstützt wird
dpkg -l | grep appindicator3

# Falls nicht: Installiere
sudo apt install gir1.2-appindicator3-0.1

# Manche Desktop-Umgebungen brauchen Extensions
# GNOME: "AppIndicator Support" Extension installieren
```

### "Verbindung schlägt fehl"
```bash
# Prüfe systemd-Service manuell
sudo systemctl status hide.me@nl

# Logs anschauen
sudo journalctl -u hide.me@nl -f

# Config-Datei prüfen
cat /opt/hide.me/config
```

### GUI neu starten
```bash
# Prozess beenden
pkill -f hideme-vpn-gui

# Neu starten
hideme-vpn-gui &
```

### 🚨 NOTFALL: VPN zurücksetzen (für Fernwartung)

Wenn die Internet-Verbindung nach VPN-Aktivierung nicht mehr funktioniert:

```bash
sudo ./hideme-emergency-reset.sh
```

**Was macht das Skript:**
- ✓ Stoppt alle hide.me VPN-Verbindungen
- ✓ Entfernt VPN-Routing-Regeln
- ✓ Löscht VPN-Interface
- ✓ Stellt DNS wieder her
- ✓ Testet Internet-Verbindung
- ✓ Optional: Neustart des Systems

**Wichtig für Fernwartung:** Diesen Befehl können Sie dem Benutzer per Telefon/Chat durchgeben:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/hirntot/hideme-vpn-gui/main/hideme-emergency-reset.sh)"
```

Oder lokal aus dem Verzeichnis:
```bash
cd /pfad/zu/spezalskripte/hideme/
sudo ./hideme-emergency-reset.sh
```

Das Skript fragt nach Bestätigung und ob das System neu gestartet werden soll.

**Alternativer 1-Zeiler** (ohne Skript):
```bash
sudo systemctl stop 'hide.me@*' && sudo systemctl disable 'hide.me@*' && sudo ip rule del table 55555 2>/dev/null ; sudo ip -6 rule del table 55555 2>/dev/null ; sudo reboot
```

## 📦 Deinstallation

**Empfohlen:** Mit dem Uninstall-Skript:

```bash
sudo ./hideme-gui-uninstall.sh
```

Das Skript:
- Stoppt laufende Instanzen
- Entfernt PolicyKit-Regel
- Entfernt Autostart-Eintrag
- Entfernt Desktop-Integration
- Entfernt GUI-Binary
- Optional: Löscht Benutzer-Konfiguration
- Optional: Entfernt Python-Pakete

**Manuell:**
```bash
sudo rm /usr/local/bin/hideme-vpn-gui
sudo rm /usr/share/applications/hideme-vpn-gui.desktop
sudo rm /etc/polkit-1/rules.d/50-hideme-vpn.rules
rm ~/.config/autostart/hideme-vpn-gui.desktop
rm -rf ~/.config/hideme-gui/
```

**Hinweis:** Hide.me CLI wird NICHT deinstalliert!

## 🎓 Für unbedarfte Nutzer

**Das war das Ziel!** Diese GUI macht hide.me VPN so einfach wie:

1. Icon im System Tray finden
2. Draufklicken
3. "Verbinden" wählen
4. Fertig!

Keine Kommandozeile, keine komplizierte systemctl-Befehle, keine Verwirrung.
Einfach klicken und sicher surfen.

## 📝 Für RechnerLotsen-Paket

Diese GUI kann als eigenständiges Paket `rechnerlotsen-hideme-gui` gebaut werden:

**Abhängigkeiten:**
- python3
- python3-gi
- gir1.2-gtk-3.0
- gir1.2-appindicator3-0.1
- gir1.2-notify-0.7
- polkit-1-gnome

**Empfohlen:**
- hide.me CLI (wird geprüft beim Start)

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe [LICENSE](LICENSE) Datei für Details.

**Copyright © 2025-2026 RechnerLotsen**

- Freie und offene Software
- Verwendung, Modifikation und Verteilung erlaubt (auch kommerziell)
- Keine Gewährleistung

## 🙏 Credits

**Entwickelt von:** [RechnerLotsen](https://rechnerlotsen.com)  
**Basiert auf:** [hide.me VPN CLI](https://hide.me)

---

**Erstellt für RechnerLotsen** - Weil VPN einfach sein sollte! 🛡️
