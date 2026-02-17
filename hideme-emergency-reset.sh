#!/bin/bash
# Hide.me VPN Emergency Reset
# Stoppt alle VPN-Verbindungen und setzt Netzwerk-Einstellungen zurück

echo "=== Hide.me VPN Emergency Reset ==="
echo

# Prüfe Root-Rechte
if [ "$EUID" -ne 0 ]; then
    echo "Keine Root-Rechte. Versuche mit sudo..."
    exec sudo "$0" "$@"
fi

echo "⚠️  Dieser Befehl wird:"
echo "   • Alle hide.me VPN-Verbindungen stoppen"
echo "   • VPN-Routing zurücksetzen"
echo "   • DNS wiederherstellen"
echo "   • Optional: System neu starten"
echo

read -p "Fortfahren? (j/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
    echo "Abgebrochen."
    exit 0
fi

echo
echo "1. Stoppe alle hide.me VPN-Dienste..."

# Finde alle aktiven hide.me Services
ACTIVE_SERVICES=$(systemctl list-units --type=service --state=active 'hide.me@*' --no-legend | awk '{print $1}')

if [ -n "$ACTIVE_SERVICES" ]; then
    for service in $ACTIVE_SERVICES; do
        echo "   Stoppe $service..."
        systemctl stop "$service" 2>/dev/null
        systemctl disable "$service" 2>/dev/null
    done
    echo "   ✓ Alle Services gestoppt"
else
    echo "   • Keine aktiven Services gefunden"
fi

echo
echo "2. Entferne VPN-Routing-Regeln..."

# Standard hide.me Routing-Tabelle ist 55555
ROUTING_TABLE=55555

# Entferne IP-Regeln
ip rule del table $ROUTING_TABLE 2>/dev/null && echo "   ✓ IPv4-Regel entfernt" || echo "   • Keine IPv4-Regel gefunden"
ip -6 rule del table $ROUTING_TABLE 2>/dev/null && echo "   ✓ IPv6-Regel entfernt" || echo "   • Keine IPv6-Regel gefunden"

# Flush Routing-Tabelle
ip route flush table $ROUTING_TABLE 2>/dev/null && echo "   ✓ IPv4-Routen gelöscht" || true
ip -6 route flush table $ROUTING_TABLE 2>/dev/null && echo "   ✓ IPv6-Routen gelöscht" || true

echo
echo "3. Entferne VPN-Interface..."

# Entferne vpn-Interface falls vorhanden
if ip link show vpn &>/dev/null; then
    ip link delete vpn 2>/dev/null && echo "   ✓ VPN-Interface entfernt" || echo "   ⚠️  Konnte Interface nicht entfernen"
else
    echo "   • Kein VPN-Interface gefunden"
fi

echo
echo "4. Stelle DNS wieder her..."

# Wenn hide.me ein Backup von resolv.conf gemacht hat
if [ -f /etc/resolv.conf.hide.me.backup ]; then
    cp /etc/resolv.conf.hide.me.backup /etc/resolv.conf
    echo "   ✓ DNS aus Backup wiederhergestellt"
else
    echo "   • Kein DNS-Backup gefunden"
    echo "   → DNS wird automatisch via DHCP/NetworkManager aktualisiert"
fi

# Triggere NetworkManager DNS-Update falls verfügbar
if command -v nmcli &> /dev/null; then
    echo "   → Triggere NetworkManager DNS-Update..."
    nmcli device reapply $(nmcli -t -f DEVICE connection show --active | head -1) 2>/dev/null && echo "   ✓ NetworkManager aktualisiert"
fi

echo
echo "5. Entferne Firewall-Marks..."

# Prüfe und entferne iptables-Marks falls vorhanden
if command -v iptables &> /dev/null; then
    iptables -t mangle -F 2>/dev/null && echo "   ✓ iptables-Marks gelöscht" || echo "   • Keine iptables-Marks"
    ip6tables -t mangle -F 2>/dev/null && echo "   ✓ ip6tables-Marks gelöscht" || echo "   • Keine ip6tables-Marks"
fi

echo
echo "6. Prüfe und repariere Default-Route..."

# Hole Hauptnetzwerk-Interface
DEFAULT_IF=$(ip route | grep default | head -1 | awk '{print $5}')

if [ -z "$DEFAULT_IF" ]; then
    echo "   ⚠️  Keine Default-Route gefunden!"
    
    # Versuche Default-Route wiederherzustellen via DHCP
    if command -v dhclient &> /dev/null; then
        echo "   → Versuche DHCP-Renewal..."
        dhclient -r 2>/dev/null
        dhclient 2>/dev/null && echo "   ✓ DHCP erneuert"
    fi
    
    # Erneut via NetworkManager
    if command -v nmcli &> /dev/null; then
        echo "   → Reaktiviere Netzwerk-Interface..."
        ACTIVE_CON=$(nmcli -t -f NAME connection show --active | head -1)
        if [ -n "$ACTIVE_CON" ]; then
            nmcli connection down "$ACTIVE_CON" 2>/dev/null
            sleep 2
            nmcli connection up "$ACTIVE_CON" 2>/dev/null && echo "   ✓ Interface reaktiviert"
        fi
    fi
else
    echo "   ✓ Default-Route gefunden via $DEFAULT_IF"
fi

echo
echo "7. Diagnose: Prüfe Netzwerk-Verbindung..."

# Teste Internet-Verbindung
if ping -c 1 -W 2 8.8.8.8 &>/dev/null; then
    echo "   ✓ Internet-Verbindung funktioniert (IPv4)"
else
    echo "   ✗ Keine Internet-Verbindung (IPv4)"
fi

if ping6 -c 1 -W 2 2001:4860:4860::8888 &>/dev/null; then
    echo "   ✓ Internet-Verbindung funktioniert (IPv6)"
else
    echo "   • Keine Internet-Verbindung (IPv6)"
fi

# DNS-Test
echo
echo "8. Diagnose: Prüfe DNS-Auflösung..."
if nslookup google.com &>/dev/null; then
    echo "   ✓ DNS funktioniert"
else
    echo "   ✗ DNS funktioniert NICHT"
    echo "   → /etc/resolv.conf Inhalt:"
    cat /etc/resolv.conf | grep -v "^#" | grep -v "^$" | sed 's/^/      /'
fi

# Routing-Tabelle
echo
echo "9. Diagnose: Zeige Routing-Tabelle..."
DEFAULT_ROUTE=$(ip route | grep default)
if [ -n "$DEFAULT_ROUTE" ]; then
    echo "   ✓ Default-Route: $DEFAULT_ROUTE"
else
    echo "   ✗ KEINE Default-Route gefunden!"
fi

# Routing-Regeln
CUSTOM_RULES=$(ip rule show | grep -v "^0:" | grep -v "^32766:" | grep -v "^32767:")
if [ -n "$CUSTOM_RULES" ]; then
    echo "   ⚠️  Custom Routing-Regeln gefunden (könnten Probleme verursachen):"
    echo "$CUSTOM_RULES" | sed 's/^/      /'
else
    echo "   ✓ Keine problematischen Routing-Regeln"
fi

echo
echo "=== Reset abgeschlossen! ==="
echo

# Frage nach Neustart
read -p "System neu starten? (j/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[JjYy]$ ]]; then
    echo "Starte System in 5 Sekunden neu..."
    echo "Abbrechen mit Ctrl+C"
    sleep 5
    reboot
else
    echo "Kein Neustart. Bitte prüfe die Netzwerk-Verbindung."
    echo
    echo "Nützliche Befehle zur Diagnose:"
    echo "  ip route                    # Zeige Routen"
    echo "  ip rule                     # Zeige Routing-Regeln"
    echo "  cat /etc/resolv.conf        # Zeige DNS-Server"
    echo "  systemctl status 'hide.me@*' # Zeige VPN-Status"
fi
