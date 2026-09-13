#!/bin/bash
# Hide.me VPN Emergency Reset
# Stoppt alle VPN-Verbindungen und setzt Netzwerk-Einstellungen zurück

# Language selection is self-contained so this script can run on its own.
# Explicit override: sudo env HIDEME_LANG=en ./hideme-gui-install.sh
hideme_language=${HIDEME_LANG:-${LC_ALL:-${LC_MESSAGES:-${LANGUAGE:-${LANG:-en}}}}}
hideme_language=${hideme_language%%:*}
hideme_language=${hideme_language%%_*}
hideme_language=${hideme_language%%-*}
hideme_language=${hideme_language%%.*}
hideme_language=${hideme_language%%@*}
case "${hideme_language,,}" in
    de|en|fr|es|it|pt) hideme_language=${hideme_language,,} ;;
    *) hideme_language=en ;;
esac

tr() {
    # Argument order: de/en/fr/es/it/pt. No eval: translations are plain text.
    case "$hideme_language" in
        de) printf '%s' "$1" ;;
        fr) printf '%s' "$3" ;;
        es) printf '%s' "$4" ;;
        it) printf '%s' "$5" ;;
        pt) printf '%s' "$6" ;;
        *) printf '%s' "$2" ;;
    esac
}

is_yes() {
    case "$hideme_language:$1" in
        *:[Yy]|de:[Jj]|fr:[Oo]|es:[Ss]|it:[Ss]|pt:[Ss]) return 0 ;;
        *) return 1 ;;
    esac
}

echo "=== Hide.me VPN Emergency Reset ==="
echo

# Prüfe Root-Rechte
if [ "$EUID" -ne 0 ]; then
    echo "$(tr "Keine Root-Rechte. Versuche mit sudo..." \
        "Root privileges required. Trying sudo..." \
        "Droits root requis. Tentative avec sudo..." \
        "Se requieren permisos de root. Intentando con sudo..." \
        "Sono necessari i privilegi root. Tentativo con sudo..." \
        "São necessários privilégios root. A tentar com sudo...")"
    exec sudo env HIDEME_LANG="$hideme_language" "$0" "$@"
fi

echo "$(tr "⚠️  Dieser Befehl wird:" \
        "⚠️  This command will:" \
        "⚠️  Cette commande va :" \
        "⚠️  Este comando va a:" \
        "⚠️  Questo comando eseguirà:" \
        "⚠️  Este comando irá:")"
echo "$(tr "   • Alle hide.me VPN-Verbindungen stoppen" \
        "   • Stop all hide.me VPN connections" \
        "   • Arrêter toutes les connexions VPN hide.me" \
        "   • Detener todas las conexiones VPN de hide.me" \
        "   • Arrestare tutte le connessioni VPN hide.me" \
        "   • Parar todas as ligações VPN hide.me")"
echo "$(tr "   • VPN-Routing zurücksetzen" \
        "   • Reset VPN routing" \
        "   • Réinitialiser le routage VPN" \
        "   • Restablecer las rutas VPN" \
        "   • Ripristinare il routing VPN" \
        "   • Repor o encaminhamento VPN")"
echo "$(tr "   • DNS wiederherstellen" \
        "   • Restore DNS" \
        "   • Restaurer le DNS" \
        "   • Restaurar el DNS" \
        "   • Ripristinare il DNS" \
        "   • Restaurar o DNS")"
echo "$(tr "   • Optional: System neu starten" \
        "   • Optionally restart the system" \
        "   • Redémarrer le système en option" \
        "   • Reiniciar el sistema opcionalmente" \
        "   • Riavviare il sistema facoltativamente" \
        "   • Reiniciar o sistema opcionalmente")"
echo

read -p "$(tr "Fortfahren? (j/n) " \
        "Continue? (y/n) " \
        "Continuer ? (o/n) " \
        "¿Continuar? (s/n) " \
        "Continuare? (s/n) " \
        "Continuar? (s/n) ")" -n 1 -r
echo
if ! is_yes "$REPLY"; then
    echo "$(tr "Abgebrochen." \
        "Cancelled." \
        "Annulé." \
        "Cancelado." \
        "Annullato." \
        "Cancelado.")"
    exit 0
fi

echo
echo "$(tr "1. Stoppe alle hide.me VPN-Dienste..." \
        "1. Stopping all hide.me VPN services..." \
        "1. Arrêt de tous les services VPN hide.me..." \
        "1. Deteniendo todos los servicios VPN de hide.me..." \
        "1. Arresto di tutti i servizi VPN hide.me..." \
        "1. A parar todos os serviços VPN hide.me...")"

# Finde alle aktiven hide.me Services
ACTIVE_SERVICES=$(systemctl list-units --type=service --state=active 'hide.me@*' --no-legend | awk '{print $1}')

if [ -n "$ACTIVE_SERVICES" ]; then
    for service in $ACTIVE_SERVICES; do
        echo "$(tr "   Stoppe $service..." \
        "   Stopping $service..." \
        "   Arrêt de $service..." \
        "   Deteniendo $service..." \
        "   Arresto di $service..." \
        "   A parar $service...")"
        systemctl stop "$service" 2>/dev/null
        systemctl disable "$service" 2>/dev/null
    done
    echo "$(tr "   ✓ Alle Services gestoppt" \
        "   ✓ All services stopped" \
        "   ✓ Tous les services arrêtés" \
        "   ✓ Todos los servicios detenidos" \
        "   ✓ Tutti i servizi arrestati" \
        "   ✓ Todos os serviços parados")"
else
    echo "$(tr "   • Keine aktiven Services gefunden" \
        "   • No active services found" \
        "   • Aucun service actif trouvé" \
        "   • No se encontraron servicios activos" \
        "   • Nessun servizio attivo trovato" \
        "   • Nenhum serviço ativo encontrado")"
fi

echo
echo "$(tr "2. Entferne VPN-Routing-Regeln..." \
        "2. Removing VPN routing rules..." \
        "2. Suppression des règles de routage VPN..." \
        "2. Eliminando las reglas de rutas VPN..." \
        "2. Rimozione delle regole di routing VPN..." \
        "2. A remover regras de encaminhamento VPN...")"

# Standard hide.me Routing-Tabelle ist 55555
ROUTING_TABLE=55555

# Entferne IP-Regeln
ip rule del table $ROUTING_TABLE 2>/dev/null && echo "$(tr "   ✓ IPv4-Regel entfernt" \
        "   ✓ IPv4 rule removed" \
        "   ✓ Règle IPv4 supprimée" \
        "   ✓ Regla IPv4 eliminada" \
        "   ✓ Regola IPv4 rimossa" \
        "   ✓ Regra IPv4 removida")" || echo "$(tr "   • Keine IPv4-Regel gefunden" \
        "   • No IPv4 rule found" \
        "   • Aucune règle IPv4 trouvée" \
        "   • No se encontró ninguna regla IPv4" \
        "   • Nessuna regola IPv4 trovata" \
        "   • Nenhuma regra IPv4 encontrada")"
ip -6 rule del table $ROUTING_TABLE 2>/dev/null && echo "$(tr "   ✓ IPv6-Regel entfernt" \
        "   ✓ IPv6 rule removed" \
        "   ✓ Règle IPv6 supprimée" \
        "   ✓ Regla IPv6 eliminada" \
        "   ✓ Regola IPv6 rimossa" \
        "   ✓ Regra IPv6 removida")" || echo "$(tr "   • Keine IPv6-Regel gefunden" \
        "   • No IPv6 rule found" \
        "   • Aucune règle IPv6 trouvée" \
        "   • No se encontró ninguna regla IPv6" \
        "   • Nessuna regola IPv6 trovata" \
        "   • Nenhuma regra IPv6 encontrada")"

# Flush Routing-Tabelle
ip route flush table $ROUTING_TABLE 2>/dev/null && echo "$(tr "   ✓ IPv4-Routen gelöscht" \
        "   ✓ IPv4 routes cleared" \
        "   ✓ Routes IPv4 effacées" \
        "   ✓ Rutas IPv4 borradas" \
        "   ✓ Route IPv4 cancellate" \
        "   ✓ Rotas IPv4 limpas")" || true
ip -6 route flush table $ROUTING_TABLE 2>/dev/null && echo "$(tr "   ✓ IPv6-Routen gelöscht" \
        "   ✓ IPv6 routes cleared" \
        "   ✓ Routes IPv6 effacées" \
        "   ✓ Rutas IPv6 borradas" \
        "   ✓ Route IPv6 cancellate" \
        "   ✓ Rotas IPv6 limpas")" || true

echo
echo "$(tr "3. Entferne VPN-Interface..." \
        "3. Removing VPN interface..." \
        "3. Suppression de l'interface VPN..." \
        "3. Eliminando la interfaz VPN..." \
        "3. Rimozione dell'interfaccia VPN..." \
        "3. A remover a interface VPN...")"

# Entferne vpn-Interface falls vorhanden
if ip link show vpn &>/dev/null; then
    ip link delete vpn 2>/dev/null && echo "$(tr "   ✓ VPN-Interface entfernt" \
        "   ✓ VPN interface removed" \
        "   ✓ Interface VPN supprimée" \
        "   ✓ Interfaz VPN eliminada" \
        "   ✓ Interfaccia VPN rimossa" \
        "   ✓ Interface VPN removida")" || echo "$(tr "   ⚠️  Konnte Interface nicht entfernen" \
        "   ⚠️  Could not remove interface" \
        "   ⚠️  Impossible de supprimer l'interface" \
        "   ⚠️  No se pudo eliminar la interfaz" \
        "   ⚠️  Impossibile rimuovere l'interfaccia" \
        "   ⚠️  Não foi possível remover a interface")"
else
    echo "$(tr "   • Kein VPN-Interface gefunden" \
        "   • No VPN interface found" \
        "   • Aucune interface VPN trouvée" \
        "   • No se encontró ninguna interfaz VPN" \
        "   • Nessuna interfaccia VPN trovata" \
        "   • Nenhuma interface VPN encontrada")"
fi

echo
echo "$(tr "4. Stelle DNS wieder her..." \
        "4. Restoring DNS..." \
        "4. Restauration du DNS..." \
        "4. Restaurando el DNS..." \
        "4. Ripristino del DNS..." \
        "4. A restaurar o DNS...")"

# Wenn hide.me ein Backup von resolv.conf gemacht hat
if [ -f /etc/resolv.conf.hide.me.backup ]; then
    cp /etc/resolv.conf.hide.me.backup /etc/resolv.conf
    echo "$(tr "   ✓ DNS aus Backup wiederhergestellt" \
        "   ✓ DNS restored from backup" \
        "   ✓ DNS restauré depuis la sauvegarde" \
        "   ✓ DNS restaurado desde la copia de seguridad" \
        "   ✓ DNS ripristinato dal backup" \
        "   ✓ DNS restaurado da cópia de segurança")"
else
    echo "$(tr "   • Kein DNS-Backup gefunden" \
        "   • No DNS backup found" \
        "   • Aucune sauvegarde DNS trouvée" \
        "   • No se encontró copia de seguridad del DNS" \
        "   • Nessun backup DNS trovato" \
        "   • Nenhuma cópia de segurança DNS encontrada")"
    echo "$(tr "   → DNS wird automatisch via DHCP/NetworkManager aktualisiert" \
        "   → DNS will be updated automatically via DHCP/NetworkManager" \
        "   → Le DNS sera actualisé automatiquement via DHCP/NetworkManager" \
        "   → El DNS se actualizará automáticamente mediante DHCP/NetworkManager" \
        "   → Il DNS verrà aggiornato automaticamente tramite DHCP/NetworkManager" \
        "   → O DNS será atualizado automaticamente via DHCP/NetworkManager")"
fi

# Triggere NetworkManager DNS-Update falls verfügbar
if command -v nmcli &> /dev/null; then
    echo "$(tr "   → Triggere NetworkManager DNS-Update..." \
        "   → Triggering NetworkManager DNS update..." \
        "   → Mise à jour DNS via NetworkManager..." \
        "   → Actualizando el DNS mediante NetworkManager..." \
        "   → Aggiornamento DNS tramite NetworkManager..." \
        "   → A atualizar o DNS via NetworkManager...")"
    nmcli device reapply $(nmcli -t -f DEVICE connection show --active | head -1) 2>/dev/null && echo "$(tr "   ✓ NetworkManager aktualisiert" \
        "   ✓ NetworkManager updated" \
        "   ✓ NetworkManager actualisé" \
        "   ✓ NetworkManager actualizado" \
        "   ✓ NetworkManager aggiornato" \
        "   ✓ NetworkManager atualizado")"
fi

echo
echo "$(tr "5. Entferne Firewall-Marks..." \
        "5. Removing firewall marks..." \
        "5. Suppression des marques du pare-feu..." \
        "5. Eliminando las marcas del cortafuegos..." \
        "5. Rimozione dei contrassegni del firewall..." \
        "5. A remover marcas da firewall...")"

# Prüfe und entferne iptables-Marks falls vorhanden
if command -v iptables &> /dev/null; then
    iptables -t mangle -F 2>/dev/null && echo "$(tr "   ✓ iptables-Marks gelöscht" \
        "   ✓ iptables marks cleared" \
        "   ✓ Marques iptables effacées" \
        "   ✓ Marcas iptables borradas" \
        "   ✓ Contrassegni iptables cancellati" \
        "   ✓ Marcas iptables limpas")" || echo "$(tr "   • Keine iptables-Marks" \
        "   • No iptables marks" \
        "   • Aucune marque iptables" \
        "   • Sin marcas iptables" \
        "   • Nessun contrassegno iptables" \
        "   • Sem marcas iptables")"
    ip6tables -t mangle -F 2>/dev/null && echo "$(tr "   ✓ ip6tables-Marks gelöscht" \
        "   ✓ ip6tables marks cleared" \
        "   ✓ Marques ip6tables effacées" \
        "   ✓ Marcas ip6tables borradas" \
        "   ✓ Contrassegni ip6tables cancellati" \
        "   ✓ Marcas ip6tables limpas")" || echo "$(tr "   • Keine ip6tables-Marks" \
        "   • No ip6tables marks" \
        "   • Aucune marque ip6tables" \
        "   • Sin marcas ip6tables" \
        "   • Nessun contrassegno ip6tables" \
        "   • Sem marcas ip6tables")"
fi

echo
echo "$(tr "6. Prüfe und repariere Default-Route..." \
        "6. Checking and repairing default route..." \
        "6. Vérification et réparation de la route par défaut..." \
        "6. Comprobando y reparando la ruta predeterminada..." \
        "6. Verifica e riparazione della route predefinita..." \
        "6. A verificar e reparar a rota predefinida...")"

# Hole Hauptnetzwerk-Interface
DEFAULT_IF=$(ip route | grep default | head -1 | awk '{print $5}')

if [ -z "$DEFAULT_IF" ]; then
    echo "$(tr "   ⚠️  Keine Default-Route gefunden!" \
        "   ⚠️  No default route found!" \
        "   ⚠️  Aucune route par défaut trouvée !" \
        "   ⚠️  ¡No se encontró ninguna ruta predeterminada!" \
        "   ⚠️  Nessuna route predefinita trovata!" \
        "   ⚠️  Nenhuma rota predefinida encontrada!")"
    
    # Versuche Default-Route wiederherzustellen via DHCP
    if command -v dhclient &> /dev/null; then
        echo "$(tr "   → Versuche DHCP-Renewal..." \
        "   → Trying DHCP renewal..." \
        "   → Tentative de renouvellement DHCP..." \
        "   → Intentando renovar DHCP..." \
        "   → Tentativo di rinnovo DHCP..." \
        "   → A tentar renovar DHCP...")"
        dhclient -r 2>/dev/null
        dhclient 2>/dev/null && echo "$(tr "   ✓ DHCP erneuert" \
        "   ✓ DHCP renewed" \
        "   ✓ DHCP renouvelé" \
        "   ✓ DHCP renovado" \
        "   ✓ DHCP rinnovato" \
        "   ✓ DHCP renovado")"
    fi
    
    # Erneut via NetworkManager
    if command -v nmcli &> /dev/null; then
        echo "$(tr "   → Reaktiviere Netzwerk-Interface..." \
        "   → Reactivating network interface..." \
        "   → Réactivation de l'interface réseau..." \
        "   → Reactivando la interfaz de red..." \
        "   → Riattivazione dell'interfaccia di rete..." \
        "   → A reativar a interface de rede...")"
        ACTIVE_CON=$(nmcli -t -f NAME connection show --active | head -1)
        if [ -n "$ACTIVE_CON" ]; then
            nmcli connection down "$ACTIVE_CON" 2>/dev/null
            sleep 2
            nmcli connection up "$ACTIVE_CON" 2>/dev/null && echo "$(tr "   ✓ Interface reaktiviert" \
        "   ✓ Interface reactivated" \
        "   ✓ Interface réactivée" \
        "   ✓ Interfaz reactivada" \
        "   ✓ Interfaccia riattivata" \
        "   ✓ Interface reativada")"
        fi
    fi
else
    echo "$(tr "   ✓ Default-Route gefunden via $DEFAULT_IF" \
        "   ✓ Default route found via $DEFAULT_IF" \
        "   ✓ Route par défaut trouvée via $DEFAULT_IF" \
        "   ✓ Ruta predeterminada encontrada mediante $DEFAULT_IF" \
        "   ✓ Route predefinita trovata tramite $DEFAULT_IF" \
        "   ✓ Rota predefinida encontrada via $DEFAULT_IF")"
fi

echo
echo "$(tr "7. Diagnose: Prüfe Netzwerk-Verbindung..." \
        "7. Diagnostics: Checking network connection..." \
        "7. Diagnostic : Vérification de la connexion réseau..." \
        "7. Diagnóstico: Comprobando la conexión de red..." \
        "7. Diagnostica: Verifica della connessione di rete..." \
        "7. Diagnóstico: A verificar a ligação de rede...")"

# Teste Internet-Verbindung
if ping -c 1 -W 2 8.8.8.8 &>/dev/null; then
    echo "$(tr "   ✓ Internet-Verbindung funktioniert (IPv4)" \
        "   ✓ Internet connection works (IPv4)" \
        "   ✓ La connexion Internet fonctionne (IPv4)" \
        "   ✓ La conexión a Internet funciona (IPv4)" \
        "   ✓ La connessione Internet funziona (IPv4)" \
        "   ✓ A ligação à Internet funciona (IPv4)")"
else
    echo "$(tr "   ✗ Keine Internet-Verbindung (IPv4)" \
        "   ✗ No Internet connection (IPv4)" \
        "   ✗ Pas de connexion Internet (IPv4)" \
        "   ✗ Sin conexión a Internet (IPv4)" \
        "   ✗ Nessuna connessione Internet (IPv4)" \
        "   ✗ Sem ligação à Internet (IPv4)")"
fi

if ping6 -c 1 -W 2 2001:4860:4860::8888 &>/dev/null; then
    echo "$(tr "   ✓ Internet-Verbindung funktioniert (IPv6)" \
        "   ✓ Internet connection works (IPv6)" \
        "   ✓ La connexion Internet fonctionne (IPv6)" \
        "   ✓ La conexión a Internet funciona (IPv6)" \
        "   ✓ La connessione Internet funziona (IPv6)" \
        "   ✓ A ligação à Internet funciona (IPv6)")"
else
    echo "$(tr "   • Keine Internet-Verbindung (IPv6)" \
        "   • No Internet connection (IPv6)" \
        "   • Pas de connexion Internet (IPv6)" \
        "   • Sin conexión a Internet (IPv6)" \
        "   • Nessuna connessione Internet (IPv6)" \
        "   • Sem ligação à Internet (IPv6)")"
fi

# DNS-Test
echo
echo "$(tr "8. Diagnose: Prüfe DNS-Auflösung..." \
        "8. Diagnostics: Checking DNS resolution..." \
        "8. Diagnostic : Vérification de la résolution DNS..." \
        "8. Diagnóstico: Comprobando la resolución DNS..." \
        "8. Diagnostica: Verifica della risoluzione DNS..." \
        "8. Diagnóstico: A verificar a resolução DNS...")"
if nslookup google.com &>/dev/null; then
    echo "$(tr "   ✓ DNS funktioniert" \
        "   ✓ DNS is working" \
        "   ✓ Le DNS fonctionne" \
        "   ✓ El DNS funciona" \
        "   ✓ Il DNS funziona" \
        "   ✓ O DNS funciona")"
else
    echo "$(tr "   ✗ DNS funktioniert NICHT" \
        "   ✗ DNS is NOT working" \
        "   ✗ Le DNS ne fonctionne PAS" \
        "   ✗ El DNS NO funciona" \
        "   ✗ Il DNS NON funziona" \
        "   ✗ O DNS NÃO funciona")"
    echo "$(tr "   → /etc/resolv.conf Inhalt:" \
        "   → /etc/resolv.conf contents:" \
        "   → Contenu de /etc/resolv.conf :" \
        "   → Contenido de /etc/resolv.conf:" \
        "   → Contenuto di /etc/resolv.conf:" \
        "   → Conteúdo de /etc/resolv.conf:")"
    cat /etc/resolv.conf | grep -v "^#" | grep -v "^$" | sed 's/^/      /'
fi

# Routing-Tabelle
echo
echo "$(tr "9. Diagnose: Zeige Routing-Tabelle..." \
        "9. Diagnostics: Displaying routing table..." \
        "9. Diagnostic : Affichage de la table de routage..." \
        "9. Diagnóstico: Mostrando la tabla de rutas..." \
        "9. Diagnostica: Visualizzazione della tabella di routing..." \
        "9. Diagnóstico: A mostrar a tabela de encaminhamento...")"
DEFAULT_ROUTE=$(ip route | grep default)
if [ -n "$DEFAULT_ROUTE" ]; then
    echo "$(tr "   ✓ Default-Route: $DEFAULT_ROUTE" \
        "   ✓ Default route: $DEFAULT_ROUTE" \
        "   ✓ Route par défaut : $DEFAULT_ROUTE" \
        "   ✓ Ruta predeterminada: $DEFAULT_ROUTE" \
        "   ✓ Route predefinita: $DEFAULT_ROUTE" \
        "   ✓ Rota predefinida: $DEFAULT_ROUTE")"
else
    echo "$(tr "   ✗ KEINE Default-Route gefunden!" \
        "   ✗ NO default route found!" \
        "   ✗ AUCUNE route par défaut trouvée !" \
        "   ✗ ¡NO se encontró ninguna ruta predeterminada!" \
        "   ✗ NESSUNA route predefinita trovata!" \
        "   ✗ NENHUMA rota predefinida encontrada!")"
fi

# Routing-Regeln
CUSTOM_RULES=$(ip rule show | grep -v "^0:" | grep -v "^32766:" | grep -v "^32767:")
if [ -n "$CUSTOM_RULES" ]; then
    echo "$(tr "   ⚠️  Custom Routing-Regeln gefunden (könnten Probleme verursachen):" \
        "   ⚠️  Custom routing rules found (may cause problems):" \
        "   ⚠️  Règles de routage personnalisées trouvées (problèmes possibles) :" \
        "   ⚠️  Se encontraron reglas de rutas personalizadas (pueden causar problemas):" \
        "   ⚠️  Trovate regole di routing personalizzate (possibili problemi):" \
        "   ⚠️  Encontradas regras de encaminhamento personalizadas (podem causar problemas):")"
    echo "$CUSTOM_RULES" | sed 's/^/      /'
else
    echo "$(tr "   ✓ Keine problematischen Routing-Regeln" \
        "   ✓ No problematic routing rules" \
        "   ✓ Aucune règle de routage problématique" \
        "   ✓ Sin reglas de rutas problemáticas" \
        "   ✓ Nessuna regola di routing problematica" \
        "   ✓ Sem regras de encaminhamento problemáticas")"
fi

echo
echo "$(tr "=== Reset abgeschlossen! ===" \
        "=== Reset complete! ===" \
        "=== Réinitialisation terminée ! ===" \
        "=== ¡Restablecimiento completado! ===" \
        "=== Ripristino completato! ===" \
        "=== Reposição concluída! ===")"
echo

# Frage nach Neustart
read -p "$(tr "System neu starten? (j/n) " \
        "Restart the system? (y/n) " \
        "Redémarrer le système ? (o/n) " \
        "¿Reiniciar el sistema? (s/n) " \
        "Riavviare il sistema? (s/n) " \
        "Reiniciar o sistema? (s/n) ")" -n 1 -r
echo
if is_yes "$REPLY"; then
    echo "$(tr "Starte System in 5 Sekunden neu..." \
        "Restarting the system in 5 seconds..." \
        "Redémarrage du système dans 5 secondes..." \
        "Reiniciando el sistema en 5 segundos..." \
        "Riavvio del sistema tra 5 secondi..." \
        "A reiniciar o sistema em 5 segundos...")"
    echo "$(tr "Abbrechen mit Ctrl+C" \
        "Press Ctrl+C to cancel" \
        "Ctrl+C pour annuler" \
        "Pulsa Ctrl+C para cancelar" \
        "Premi Ctrl+C per annullare" \
        "Prima Ctrl+C para cancelar")"
    sleep 5
    reboot
else
    echo "$(tr "Kein Neustart. Bitte prüfe die Netzwerk-Verbindung." \
        "No restart. Please check the network connection." \
        "Pas de redémarrage. Vérifiez la connexion réseau." \
        "Sin reinicio. Comprueba la conexión de red." \
        "Nessun riavvio. Verifica la connessione di rete." \
        "Sem reinício. Verifique a ligação de rede.")"
    echo
    echo "$(tr "Nützliche Befehle zur Diagnose:" \
        "Useful diagnostic commands:" \
        "Commandes utiles pour le diagnostic :" \
        "Comandos útiles para el diagnóstico:" \
        "Comandi utili per la diagnostica:" \
        "Comandos úteis para diagnóstico:")"
    echo "$(tr "  ip route                    # Zeige Routen" \
        "  ip route                    # Show routes" \
        "  ip route                    # Afficher les routes" \
        "  ip route                    # Mostrar rutas" \
        "  ip route                    # Mostra route" \
        "  ip route                    # Mostrar rotas")"
    echo "$(tr "  ip rule                     # Zeige Routing-Regeln" \
        "  ip rule                     # Show routing rules" \
        "  ip rule                     # Afficher les règles de routage" \
        "  ip rule                     # Mostrar reglas de rutas" \
        "  ip rule                     # Mostra regole di routing" \
        "  ip rule                     # Mostrar regras de encaminhamento")"
    echo "$(tr "  cat /etc/resolv.conf        # Zeige DNS-Server" \
        "  cat /etc/resolv.conf        # Show DNS servers" \
        "  cat /etc/resolv.conf        # Afficher les serveurs DNS" \
        "  cat /etc/resolv.conf        # Mostrar servidores DNS" \
        "  cat /etc/resolv.conf        # Mostra server DNS" \
        "  cat /etc/resolv.conf        # Mostrar servidores DNS")"
    echo "$(tr "  systemctl status 'hide.me@*' # Zeige VPN-Status" \
        "  systemctl status 'hide.me@*' # Show VPN status" \
        "  systemctl status 'hide.me@*' # Afficher l'état du VPN" \
        "  systemctl status 'hide.me@*' # Mostrar estado de la VPN" \
        "  systemctl status 'hide.me@*' # Mostra stato VPN" \
        "  systemctl status 'hide.me@*' # Mostrar estado da VPN")"
fi
