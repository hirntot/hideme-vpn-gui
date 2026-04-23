#!/bin/bash
# Hide.me VPN GUI Installer für RechnerLotsen

echo "=== Hide.me VPN GUI Installer ==="
echo

# Prüfe Root-Rechte für Installation
if [ "$EUID" -ne 0 ]; then
    echo "Für die Installation werden Root-Rechte benötigt."
    echo "Bitte mit sudo ausführen: sudo $0"
    exit 1
fi

# Hole echten Benutzer (auch wenn sudo verwendet wird)
REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

echo "Installation für Benutzer: $REAL_USER"
echo

# 1. Prüfe ob hide.me CLI installiert ist
if [ ! -f /opt/hide.me/hide.me ]; then
    echo "❌ hide.me CLI ist nicht installiert!"
    echo
    echo "Soll hide.me CLI jetzt automatisch installiert werden?"
    echo "Download: https://hide.me/download/linux-amd64"
    echo
    read -p "Hide.me CLI jetzt installieren? (j/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[JjYy]$ ]]; then
        echo "Lade hide.me CLI herunter und installiere..."
        
        # Erstelle temporäres Verzeichnis
        TEMP_DIR=$(mktemp -d)
        cd "$TEMP_DIR"
        
        # Download und Extraktion
        if curl -L https://hide.me/download/linux-amd64 | tar -xz; then
            echo "✓ Download erfolgreich"
            
            # Installiere hide.me CLI
            if [ -f ./install.sh ]; then
                chmod +x ./install.sh
                ./install.sh
                
                if [ $? -eq 0 ]; then
                    echo "✓ hide.me CLI installiert"
                else
                    echo "❌ Installation fehlgeschlagen"
                    cd - > /dev/null
                    rm -rf "$TEMP_DIR"
                    exit 1
                fi
            else
                echo "❌ install.sh nicht gefunden im Archiv"
                cd - > /dev/null
                rm -rf "$TEMP_DIR"
                exit 1
            fi
        else
            echo "❌ Download fehlgeschlagen"
            cd - > /dev/null
            rm -rf "$TEMP_DIR"
            exit 1
        fi
        
        # Zurück zum Original-Verzeichnis und aufräumen
        cd - > /dev/null
        rm -rf "$TEMP_DIR"
        
        echo
        echo "⚠️  WICHTIG: Hide.me CLI muss noch konfiguriert werden, falls Sie nicht gerde Zugangsdaten eingegeben haben!"
        echo "Bitte führe aus: sudo /opt/hide.me/hide.me token free.hideservers.net"
        echo "Zugangsdaten eingeben, dann GUI-Installation fortsetzen."
        echo
        read -p "Konfiguration abgeschlossen? Enter zum Fortfahren..."
        
    else
        echo
        echo "Installation abgebrochen."
        echo "Bitte installiere hide.me CLI manuell:"
        echo "1. Download: https://hide.me/en/software/linux"
        echo "2. Entpacken und sudo ./install.sh ausführen"
        echo
        exit 1
    fi
fi

echo "✓ hide.me CLI gefunden"

# 2. Installiere Python-Abhängigkeiten (optional)
echo "Installiere Python-Abhängigkeiten..."

# Basis-Pakete (erforderlich)
REQUIRED_PKGS="python3 python3-gi gir1.2-gtk-3.0"
apt-get update -qq
apt-get install -y $REQUIRED_PKGS

if [ $? -ne 0 ]; then
    echo "❌ Installation der Basis-Pakete fehlgeschlagen"
    exit 1
fi

# Optionale Pakete für bessere Integration
OPTIONAL_PKGS=""
echo
echo "Prüfe optionale Pakete..."

# AppIndicator3 für System-Tray (empfohlen)
if apt-cache show gir1.2-appindicator3-0.1 &>/dev/null; then
    OPTIONAL_PKGS="$OPTIONAL_PKGS gir1.2-appindicator3-0.1"
    echo "  • gir1.2-appindicator3-0.1 verfügbar"
else
    echo "  ⚠️  gir1.2-appindicator3-0.1 nicht verfügbar (Fallback auf StatusIcon)"
fi

# Notify für Desktop-Benachrichtigungen
if apt-cache show gir1.2-notify-0.7 &>/dev/null; then
    OPTIONAL_PKGS="$OPTIONAL_PKGS gir1.2-notify-0.7"
    echo "  • gir1.2-notify-0.7 verfügbar"
else
    echo "  ⚠️  gir1.2-notify-0.7 nicht verfügbar (keine Benachrichtigungen)"
fi

# PolicyKit Frontend (optional)
if apt-cache show policykit-1-gnome &>/dev/null; then
    OPTIONAL_PKGS="$OPTIONAL_PKGS policykit-1-gnome"
    echo "  • policykit-1-gnome verfügbar"
elif apt-cache show polkit-1-gnome &>/dev/null; then
    OPTIONAL_PKGS="$OPTIONAL_PKGS polkit-1-gnome"
    echo "  • polkit-1-gnome verfügbar"
else
    echo "  ⚠️  PolicyKit-Frontend nicht verfügbar (pkexec funktioniert trotzdem)"
fi

# Installiere optionale Pakete falls verfügbar
if [ -n "$OPTIONAL_PKGS" ]; then
    apt-get install -y $OPTIONAL_PKGS 2>/dev/null || true
fi

echo "✓ Abhängigkeiten installiert"

# 3. Kopiere Python-Skript nach /usr/local/bin
echo "Installiere Hide.me GUI..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prüfe ob bereits installiert (Update-Szenario)
if [ -f /usr/local/bin/hideme-vpn-gui ]; then
    echo "⚠️  Hide.me GUI ist bereits installiert."
    read -p "Möchtest du die Installation überschreiben/aktualisieren? (j/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
        echo "Installation abgebrochen."
        exit 0
    fi
    
    # Stoppe laufende Instanz vor Update
    echo "Stoppe laufende Instanz..."
    pkill -f hideme-vpn-gui 2>/dev/null && echo "✓ Prozess beendet" || echo "• Keine laufende Instanz"
    sleep 1
fi

cp "$SCRIPT_DIR/hideme-notifiy.py" /usr/local/bin/hideme-vpn-gui
chmod +x /usr/local/bin/hideme-vpn-gui
chown root:root /usr/local/bin/hideme-vpn-gui

echo "✓ GUI installiert nach /usr/local/bin/hideme-vpn-gui"

# 4. Erstelle .desktop Datei für Anwendungsmenü
echo "Erstelle Desktop-Integration..."
cat > /usr/share/applications/hideme-vpn-gui.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Hide.me VPN
Comment=Benutzerfreundliche GUI für hide.me VPN
Exec=/usr/local/bin/hideme-vpn-gui
Icon=network-vpn
Terminal=false
Categories=Network;VPN;
StartupNotify=false
EOF

chmod 644 /usr/share/applications/hideme-vpn-gui.desktop

echo "✓ Desktop-Datei erstellt"

# 5. Erstelle Autostart-Eintrag für den Benutzer
echo "Richte Autostart ein..."
AUTOSTART_DIR="$REAL_HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_DIR/hideme-vpn-gui.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=Hide.me VPN GUI
Comment=Hide.me VPN Notification Bar
Exec=/usr/local/bin/hideme-vpn-gui
Icon=network-vpn
Terminal=false
Categories=Network;VPN;
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

chown -R "$REAL_USER:$REAL_USER" "$AUTOSTART_DIR"
chmod 644 "$AUTOSTART_DIR/hideme-vpn-gui.desktop"

echo "✓ Autostart konfiguriert"

# 6. Installiere PolicyKit-Regel (VPN ohne Passwort steuern)
echo "Installiere PolicyKit-Regel..."
if [ -f "$SCRIPT_DIR/50-hideme-vpn.rules" ]; then
    cp "$SCRIPT_DIR/50-hideme-vpn.rules" /etc/polkit-1/rules.d/50-hideme-vpn.rules
    chmod 644 /etc/polkit-1/rules.d/50-hideme-vpn.rules
    chown root:root /etc/polkit-1/rules.d/50-hideme-vpn.rules
    echo "✓ PolicyKit-Regel installiert - VPN-Steuerung ohne Passwort"
    
    # PolicyKit neu starten um Regel zu laden
    if command -v systemctl &> /dev/null; then
        systemctl restart polkit.service 2>/dev/null || true
        echo "  PolicyKit neu gestartet"
    fi
else
    echo "⚠️  PolicyKit-Regel nicht gefunden - VPN-Befehle erfordern Passwort-Eingabe"
fi

# 7. Prüfe PolicyKit
if [ ! -f /usr/bin/pkexec ]; then
    echo "⚠️  Warning: pkexec nicht gefunden. Systemd-Befehle benötigen evtl. manuelle sudo-Eingabe."
fi

echo
echo "=== Installation abgeschlossen! ==="
echo
echo "Die Hide.me VPN GUI kann jetzt gestartet werden:"
echo "• Aus dem Anwendungsmenü: 'Hide.me VPN'"
echo "• Aus dem Terminal: hideme-vpn-gui"
echo "• Automatisch beim nächsten Login"
echo
echo "Tipp: Ein VPN-Icon erscheint im System Tray"
echo
echo "Hinweis: PolicyKit-Regel wurde installiert - VPN-Verbindungen"
echo "         können ohne Passwort-Eingabe gesteuert werden."
echo "         Bei Problemen: Logout/Login oder System neustarten."
echo

# Optional: Direkt starten
read -p "GUI jetzt als $REAL_USER starten? (j/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[JjYy]$ ]]; then
    sudo -u "$REAL_USER" DISPLAY=:0 /usr/local/bin/hideme-vpn-gui &
    echo "✓ GUI gestartet - siehe System Tray"
fi

echo
echo "Bei Problemen: Prüfe dass hide.me CLI korrekt konfiguriert ist"
echo "und dass das Access Token unter /opt/hide.me/accessToken.txt existiert"
