#!/bin/bash
# Hide.me VPN GUI Uninstaller für RechnerLotsen

echo "=== Hide.me VPN GUI Uninstaller ==="
echo

# Prüfe Root-Rechte für Deinstallation
if [ "$EUID" -ne 0 ]; then
    echo "Für die Deinstallation werden Root-Rechte benötigt."
    echo "Bitte mit sudo ausführen: sudo $0"
    exit 1
fi

# Hole echten Benutzer (auch wenn sudo verwendet wird)
REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

echo "Deinstallation für Benutzer: $REAL_USER"
echo

# Warnung
read -p "Möchtest du Hide.me VPN GUI wirklich deinstallieren? (j/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
    echo "Abgebrochen."
    exit 0
fi

# 1. Stoppe laufende Instanz
echo "Stoppe laufende Instanz..."
pkill -f hideme-vpn-gui 2>/dev/null && echo "✓ Prozess beendet" || echo "• Keine laufende Instanz"

# 2. Entferne PolicyKit-Regel
echo "Entferne PolicyKit-Regel..."
if [ -f /etc/polkit-1/rules.d/50-hideme-vpn.rules ]; then
    rm /etc/polkit-1/rules.d/50-hideme-vpn.rules
    echo "✓ PolicyKit-Regel entfernt"
    
    # Versuche polkit neu zu laden
    if command -v systemctl &> /dev/null; then
        systemctl reload polkit.service 2>/dev/null || true
    fi
else
    echo "• PolicyKit-Regel nicht vorhanden"
fi

# 3. Entferne Autostart-Eintrag
echo "Entferne Autostart..."
AUTOSTART_FILE="$REAL_HOME/.config/autostart/hideme-vpn-gui.desktop"
if [ -f "$AUTOSTART_FILE" ]; then
    rm "$AUTOSTART_FILE"
    echo "✓ Autostart-Eintrag entfernt"
else
    echo "• Autostart-Eintrag nicht vorhanden"
fi

# 4. Entferne Desktop-Datei
echo "Entferne Desktop-Integration..."
if [ -f /usr/share/applications/hideme-vpn-gui.desktop ]; then
    rm /usr/share/applications/hideme-vpn-gui.desktop
    echo "✓ Desktop-Datei entfernt"
    
    # Update desktop database wenn verfügbar
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database /usr/share/applications 2>/dev/null || true
    fi
else
    echo "• Desktop-Datei nicht vorhanden"
fi

# 5. Entferne Binary
echo "Entferne GUI-Anwendung..."
if [ -f /usr/local/bin/hideme-vpn-gui ]; then
    rm /usr/local/bin/hideme-vpn-gui
    echo "✓ GUI-Anwendung entfernt"
else
    echo "• GUI-Anwendung nicht vorhanden"
fi

# 6. Optional: Benutzer-Konfiguration entfernen
echo
CONFIG_DIR="$REAL_HOME/.config/hideme-gui"
if [ -d "$CONFIG_DIR" ]; then
    read -p "Benutzer-Konfiguration auch löschen? (~/.config/hideme-gui) (j/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[JjYy]$ ]]; then
        rm -rf "$CONFIG_DIR"
        echo "✓ Benutzer-Konfiguration entfernt"
    else
        echo "• Benutzer-Konfiguration behalten"
    fi
fi

echo
echo "=== Deinstallation abgeschlossen! ==="
echo
echo "Hinweise:"
echo "• Hide.me CLI (/opt/hide.me) wurde NICHT entfernt"
echo "• VPN-Verbindungen müssen manuell getrennt werden falls aktiv"
echo "• Bei Bedarf hide.me CLI mit: sudo /opt/hide.me/uninstall.sh"
echo

# Optional: Python-Pakete entfernen?
echo "Python-Abhängigkeiten wurden NICHT entfernt."
read -p "Möchtest du die Python-Pakete auch deinstallieren? (j/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[JjYy]$ ]]; then
    echo "Entferne Python-Pakete..."
    apt-get remove -y gir1.2-appindicator3-0.1 gir1.2-notify-0.7 2>/dev/null
    echo "✓ Python-Pakete entfernt (Basis-Pakete wie python3-gi wurden behalten)"
fi

echo
echo "Fertig. Hide.me VPN GUI wurde deinstalliert."
