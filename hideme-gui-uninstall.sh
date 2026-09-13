#!/bin/bash
# Hide.me VPN GUI Uninstaller für RechnerLotsen

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

echo "=== Hide.me VPN GUI Uninstaller ==="
echo

# Prüfe Root-Rechte für Deinstallation
if [ "$EUID" -ne 0 ]; then
    echo "$(tr "Für die Deinstallation werden Root-Rechte benötigt." \
        "Root privileges are required for uninstallation." \
        "Les droits root sont nécessaires pour la désinstallation." \
        "Se requieren permisos de root para la desinstalación." \
        "Sono necessari i privilegi root per la disinstallazione." \
        "São necessários privilégios root para a desinstalação.")"
    echo "$(tr "Bitte mit sudo ausführen: sudo $0" \
        "Please run with sudo: sudo $0" \
        "Exécutez avec sudo : sudo $0" \
        "Ejecuta con sudo: sudo $0" \
        "Esegui con sudo: sudo $0" \
        "Execute com sudo: sudo $0")"
    exit 1
fi

# Hole echten Benutzer (auch wenn sudo verwendet wird)
REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

echo "$(tr "Deinstallation für Benutzer: $REAL_USER" \
        "Uninstalling for user: $REAL_USER" \
        "Désinstallation pour l'utilisateur : $REAL_USER" \
        "Desinstalando para el usuario: $REAL_USER" \
        "Disinstallazione per l'utente: $REAL_USER" \
        "A desinstalar para o utilizador: $REAL_USER")"
echo

# Warnung
read -p "$(tr "Möchtest du Hide.me VPN GUI wirklich deinstallieren? (j/n) " \
        "Are you sure you want to uninstall Hide.me VPN GUI? (y/n) " \
        "Désinstaller Hide.me VPN GUI ? (o/n) " \
        "¿Desinstalar Hide.me VPN GUI? (s/n) " \
        "Disinstallare Hide.me VPN GUI? (s/n) " \
        "Desinstalar Hide.me VPN GUI? (s/n) ")" -n 1 -r
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

# 1. Stoppe laufende Instanz
echo "$(tr "Stoppe laufende Instanz..." \
        "Stopping running instance..." \
        "Arrêt de l'instance en cours..." \
        "Deteniendo la instancia en ejecución..." \
        "Arresto dell'istanza in esecuzione..." \
        "A parar a instância em execução...")"
pkill -f hideme-vpn-gui 2>/dev/null && echo "$(tr "✓ Prozess beendet" \
        "✓ Process stopped" \
        "✓ Processus arrêté" \
        "✓ Proceso detenido" \
        "✓ Processo arrestato" \
        "✓ Processo parado")" || echo "$(tr "• Keine laufende Instanz" \
        "• No running instance" \
        "• Aucune instance en cours" \
        "• Sin instancias en ejecución" \
        "• Nessuna istanza in esecuzione" \
        "• Nenhuma instância em execução")"

# 2. Entferne PolicyKit-Regel
echo "$(tr "Entferne PolicyKit-Regel..." \
        "Removing PolicyKit rule..." \
        "Suppression de la règle PolicyKit..." \
        "Eliminando regla de PolicyKit..." \
        "Rimozione della regola PolicyKit..." \
        "A remover a regra PolicyKit...")"
if [ -f /etc/polkit-1/rules.d/50-hideme-vpn.rules ]; then
    rm /etc/polkit-1/rules.d/50-hideme-vpn.rules
    echo "$(tr "✓ PolicyKit-Regel entfernt" \
        "✓ PolicyKit rule removed" \
        "✓ Règle PolicyKit supprimée" \
        "✓ Regla de PolicyKit eliminada" \
        "✓ Regola PolicyKit rimossa" \
        "✓ Regra PolicyKit removida")"
    
    # Versuche polkit neu zu laden
    if command -v systemctl &> /dev/null; then
        systemctl reload polkit.service 2>/dev/null || true
    fi
else
    echo "$(tr "• PolicyKit-Regel nicht vorhanden" \
        "• PolicyKit rule not present" \
        "• Règle PolicyKit absente" \
        "• Regla de PolicyKit ausente" \
        "• Regola PolicyKit assente" \
        "• Regra PolicyKit ausente")"
fi

# 3. Entferne Autostart-Eintrag
echo "$(tr "Entferne Autostart..." \
        "Removing autostart..." \
        "Suppression du démarrage automatique..." \
        "Eliminando inicio automático..." \
        "Rimozione dell'avvio automatico..." \
        "A remover o arranque automático...")"
AUTOSTART_FILE="$REAL_HOME/.config/autostart/hideme-vpn-gui.desktop"
if [ -f "$AUTOSTART_FILE" ]; then
    rm "$AUTOSTART_FILE"
    echo "$(tr "✓ Autostart-Eintrag entfernt" \
        "✓ Autostart entry removed" \
        "✓ Entrée de démarrage automatique supprimée" \
        "✓ Entrada de inicio automático eliminada" \
        "✓ Voce di avvio automatico rimossa" \
        "✓ Entrada de arranque automático removida")"
else
    echo "$(tr "• Autostart-Eintrag nicht vorhanden" \
        "• Autostart entry not present" \
        "• Entrée de démarrage automatique absente" \
        "• Entrada de inicio automático ausente" \
        "• Voce di avvio automatico assente" \
        "• Entrada de arranque automático ausente")"
fi

# 4. Entferne Desktop-Datei
echo "$(tr "Entferne Desktop-Integration..." \
        "Removing desktop integration..." \
        "Suppression de l'intégration au bureau..." \
        "Eliminando integración con el escritorio..." \
        "Rimozione dell'integrazione desktop..." \
        "A remover a integração com o ambiente de trabalho...")"
if [ -f /usr/share/applications/hideme-vpn-gui.desktop ]; then
    rm /usr/share/applications/hideme-vpn-gui.desktop
    echo "$(tr "✓ Desktop-Datei entfernt" \
        "✓ Desktop file removed" \
        "✓ Fichier desktop supprimé" \
        "✓ Archivo desktop eliminado" \
        "✓ File desktop rimosso" \
        "✓ Ficheiro desktop removido")"
    
    # Update desktop database wenn verfügbar
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database /usr/share/applications 2>/dev/null || true
    fi
else
    echo "$(tr "• Desktop-Datei nicht vorhanden" \
        "• Desktop file not present" \
        "• Fichier desktop absent" \
        "• Archivo desktop ausente" \
        "• File desktop assente" \
        "• Ficheiro desktop ausente")"
fi

# 5. Entferne Binary
echo "$(tr "Entferne GUI-Anwendung..." \
        "Removing GUI application..." \
        "Suppression de l'application..." \
        "Eliminando la aplicación..." \
        "Rimozione dell'applicazione..." \
        "A remover a aplicação...")"
if [ -f /usr/local/bin/hideme-vpn-gui ]; then
    rm /usr/local/bin/hideme-vpn-gui
    echo "$(tr "✓ GUI-Anwendung entfernt" \
        "✓ GUI application removed" \
        "✓ Application supprimée" \
        "✓ Aplicación eliminada" \
        "✓ Applicazione rimossa" \
        "✓ Aplicação removida")"
else
    echo "$(tr "• GUI-Anwendung nicht vorhanden" \
        "• GUI application not present" \
        "• Application absente" \
        "• Aplicación ausente" \
        "• Applicazione assente" \
        "• Aplicação ausente")"
fi

# 6. Optional: Benutzer-Konfiguration entfernen
echo
CONFIG_DIR="$REAL_HOME/.config/hideme-gui"
if [ -d "$CONFIG_DIR" ]; then
    read -p "$(tr "Benutzer-Konfiguration auch löschen? (~/.config/hideme-gui) (j/n) " \
        "Also delete user configuration? (~/.config/hideme-gui) (y/n) " \
        "Supprimer aussi la configuration ? (~/.config/hideme-gui) (o/n) " \
        "¿Eliminar también la configuración? (~/.config/hideme-gui) (s/n) " \
        "Eliminare anche la configurazione? (~/.config/hideme-gui) (s/n) " \
        "Eliminar também a configuração? (~/.config/hideme-gui) (s/n) ")" -n 1 -r
    echo
    if is_yes "$REPLY"; then
        rm -rf "$CONFIG_DIR"
        echo "$(tr "✓ Benutzer-Konfiguration entfernt" \
        "✓ User configuration removed" \
        "✓ Configuration supprimée" \
        "✓ Configuración eliminada" \
        "✓ Configurazione rimossa" \
        "✓ Configuração removida")"
    else
        echo "$(tr "• Benutzer-Konfiguration behalten" \
        "• User configuration kept" \
        "• Configuration conservée" \
        "• Configuración conservada" \
        "• Configurazione conservata" \
        "• Configuração mantida")"
    fi
fi

echo
echo "$(tr "=== Deinstallation abgeschlossen! ===" \
        "=== Uninstallation complete! ===" \
        "=== Désinstallation terminée ! ===" \
        "=== ¡Desinstalación completada! ===" \
        "=== Disinstallazione completata! ===" \
        "=== Desinstalação concluída! ===")"
echo
echo "$(tr "Hinweise:" \
        "Notes:" \
        "Remarques :" \
        "Notas:" \
        "Note:" \
        "Notas:")"
echo "$(tr "• Hide.me CLI (/opt/hide.me) wurde NICHT entfernt" \
        "• Hide.me CLI (/opt/hide.me) was NOT removed" \
        "• Hide.me CLI (/opt/hide.me) n'a PAS été supprimé" \
        "• Hide.me CLI (/opt/hide.me) NO se ha eliminado" \
        "• Hide.me CLI (/opt/hide.me) NON è stato rimosso" \
        "• Hide.me CLI (/opt/hide.me) NÃO foi removido")"
echo "$(tr "• VPN-Verbindungen müssen manuell getrennt werden falls aktiv" \
        "• Active VPN connections must be disconnected manually" \
        "• Les connexions VPN actives doivent être déconnectées manuellement" \
        "• Las conexiones VPN activas deben desconectarse manualmente" \
        "• Le connessioni VPN attive devono essere disconnesse manualmente" \
        "• As ligações VPN ativas devem ser desligadas manualmente")"
echo "$(tr "• Bei Bedarf hide.me CLI mit: sudo /opt/hide.me/uninstall.sh" \
        "• To uninstall hide.me CLI if needed: sudo /opt/hide.me/uninstall.sh" \
        "• Pour désinstaller hide.me CLI : sudo /opt/hide.me/uninstall.sh" \
        "• Para desinstalar hide.me CLI: sudo /opt/hide.me/uninstall.sh" \
        "• Per disinstallare hide.me CLI: sudo /opt/hide.me/uninstall.sh" \
        "• Para desinstalar hide.me CLI: sudo /opt/hide.me/uninstall.sh")"
echo

# Optional: Python-Pakete entfernen?
echo "$(tr "Python-Abhängigkeiten wurden NICHT entfernt." \
        "Python dependencies were NOT removed." \
        "Les dépendances Python n'ont PAS été supprimées." \
        "Las dependencias de Python NO se han eliminado." \
        "Le dipendenze Python NON sono state rimosse." \
        "As dependências Python NÃO foram removidas.")"
read -p "$(tr "Möchtest du die Python-Pakete auch deinstallieren? (j/n) " \
        "Also uninstall the Python packages? (y/n) " \
        "Désinstaller aussi les paquets Python ? (o/n) " \
        "¿Desinstalar también los paquetes de Python? (s/n) " \
        "Disinstallare anche i pacchetti Python? (s/n) " \
        "Desinstalar também os pacotes Python? (s/n) ")" -n 1 -r
echo
if is_yes "$REPLY"; then
    echo "$(tr "Entferne Python-Pakete..." \
        "Removing Python packages..." \
        "Suppression des paquets Python..." \
        "Eliminando paquetes de Python..." \
        "Rimozione dei pacchetti Python..." \
        "A remover pacotes Python...")"
    apt-get remove -y gir1.2-appindicator3-0.1 gir1.2-notify-0.7 2>/dev/null
    echo "$(tr "✓ Python-Pakete entfernt (Basis-Pakete wie python3-gi wurden behalten)" \
        "✓ Python packages removed (required packages such as python3-gi were kept)" \
        "✓ Paquets Python supprimés (paquets requis comme python3-gi conservés)" \
        "✓ Paquetes de Python eliminados (se conservaron los necesarios como python3-gi)" \
        "✓ Pacchetti Python rimossi (conservati quelli necessari come python3-gi)" \
        "✓ Pacotes Python removidos (mantidos os necessários como python3-gi)")"
fi

echo
echo "$(tr "Fertig. Hide.me VPN GUI wurde deinstalliert." \
        "Done. Hide.me VPN GUI has been uninstalled." \
        "Terminé. Hide.me VPN GUI est désinstallé." \
        "Listo. Hide.me VPN GUI se ha desinstalado." \
        "Fatto. Hide.me VPN GUI è stato disinstallato." \
        "Concluído. Hide.me VPN GUI foi desinstalado.")"
