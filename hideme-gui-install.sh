#!/bin/bash
# Hide.me VPN GUI Installer für RechnerLotsen

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

echo "=== Hide.me VPN GUI Installer ==="
echo

# Prüfe Root-Rechte für Installation
if [ "$EUID" -ne 0 ]; then
    echo "$(tr "Für die Installation werden Root-Rechte benötigt." \
        "Root privileges are required for installation." \
        "Les droits root sont nécessaires pour l'installation." \
        "Se requieren permisos de root para la instalación." \
        "Sono necessari i privilegi root per l'installazione." \
        "São necessários privilégios root para a instalação.")"
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

echo "$(tr "Installation für Benutzer: $REAL_USER" \
        "Installing for user: $REAL_USER" \
        "Installation pour l'utilisateur : $REAL_USER" \
        "Instalando para el usuario: $REAL_USER" \
        "Installazione per l'utente: $REAL_USER" \
        "A instalar para o utilizador: $REAL_USER")"
echo

# 1. Prüfe ob hide.me CLI installiert ist
if [ ! -f /opt/hide.me/hide.me ]; then
    echo "$(tr "❌ hide.me CLI ist nicht installiert!" \
        "❌ hide.me CLI is not installed!" \
        "❌ hide.me CLI n'est pas installé !" \
        "❌ ¡hide.me CLI no está instalado!" \
        "❌ hide.me CLI non è installato!" \
        "❌ hide.me CLI não está instalado!")"
    echo
    echo "$(tr "Soll hide.me CLI jetzt automatisch installiert werden?" \
        "Would you like to install hide.me CLI automatically now?" \
        "Installer hide.me CLI automatiquement maintenant ?" \
        "¿Instalar hide.me CLI automáticamente ahora?" \
        "Installare hide.me CLI automaticamente ora?" \
        "Instalar hide.me CLI automaticamente agora?")"
    echo "Download: https://hide.me/download/linux-amd64"
    echo
    read -p "$(tr "Hide.me CLI jetzt installieren? (j/n) " \
        "Install hide.me CLI now? (y/n) " \
        "Installer hide.me CLI maintenant ? (o/n) " \
        "¿Instalar hide.me CLI ahora? (s/n) " \
        "Installare hide.me CLI ora? (s/n) " \
        "Instalar hide.me CLI agora? (s/n) ")" -n 1 -r
    echo
    
    if is_yes "$REPLY"; then
        echo "$(tr "Lade hide.me CLI herunter und installiere..." \
        "Downloading and installing hide.me CLI..." \
        "Téléchargement et installation de hide.me CLI..." \
        "Descargando e instalando hide.me CLI..." \
        "Download e installazione di hide.me CLI..." \
        "A transferir e instalar hide.me CLI...")"
        
        # Erstelle temporäres Verzeichnis
        TEMP_DIR=$(mktemp -d)
        cd "$TEMP_DIR"
        
        # Download und Extraktion
        if curl -L https://hide.me/download/linux-amd64 | tar -xz; then
            echo "$(tr "✓ Download erfolgreich" \
        "✓ Download successful" \
        "✓ Téléchargement réussi" \
        "✓ Descarga completada" \
        "✓ Download completato" \
        "✓ Transferência concluída")"
            
            # Installiere hide.me CLI
            if [ -f ./install.sh ]; then
                chmod +x ./install.sh
                ./install.sh
                
                if [ $? -eq 0 ]; then
                    echo "$(tr "✓ hide.me CLI installiert" \
        "✓ hide.me CLI installed" \
        "✓ hide.me CLI installé" \
        "✓ hide.me CLI instalado" \
        "✓ hide.me CLI installato" \
        "✓ hide.me CLI instalado")"
                else
                    echo "$(tr "❌ Installation fehlgeschlagen" \
        "❌ Installation failed" \
        "❌ Échec de l'installation" \
        "❌ Error de instalación" \
        "❌ Installazione non riuscita" \
        "❌ Falha na instalação")"
                    cd - > /dev/null
                    rm -rf "$TEMP_DIR"
                    exit 1
                fi
            else
                echo "$(tr "❌ install.sh nicht gefunden im Archiv" \
        "❌ install.sh not found in archive" \
        "❌ install.sh introuvable dans l'archive" \
        "❌ No se encontró install.sh en el archivo" \
        "❌ install.sh non trovato nell'archivio" \
        "❌ install.sh não encontrado no arquivo")"
                cd - > /dev/null
                rm -rf "$TEMP_DIR"
                exit 1
            fi
        else
            echo "$(tr "❌ Download fehlgeschlagen" \
        "❌ Download failed" \
        "❌ Échec du téléchargement" \
        "❌ Error de descarga" \
        "❌ Download non riuscito" \
        "❌ Falha na transferência")"
            cd - > /dev/null
            rm -rf "$TEMP_DIR"
            exit 1
        fi
        
        # Zurück zum Original-Verzeichnis und aufräumen
        cd - > /dev/null
        rm -rf "$TEMP_DIR"
        
        echo
        echo "$(tr "⚠️  WICHTIG: Hide.me CLI muss noch konfiguriert werden, falls Sie nicht gerde Zugangsdaten eingegeben haben!" \
        "⚠️  IMPORTANT: Configure hide.me CLI if you have not entered your credentials yet!" \
        "⚠️  IMPORTANT : Configurez hide.me CLI si vous n'avez pas encore saisi vos identifiants !" \
        "⚠️  IMPORTANTE: ¡Configura hide.me CLI si todavía no has introducido tus credenciales!" \
        "⚠️  IMPORTANTE: Configura hide.me CLI se non hai ancora inserito le credenziali!" \
        "⚠️  IMPORTANTE: Configure hide.me CLI se ainda não introduziu as credenciais!")"
        echo "$(tr "Bitte führe aus: sudo /opt/hide.me/hide.me token free.hideservers.net" \
        "Please run: sudo /opt/hide.me/hide.me token free.hideservers.net" \
        "Exécutez : sudo /opt/hide.me/hide.me token free.hideservers.net" \
        "Ejecuta: sudo /opt/hide.me/hide.me token free.hideservers.net" \
        "Esegui: sudo /opt/hide.me/hide.me token free.hideservers.net" \
        "Execute: sudo /opt/hide.me/hide.me token free.hideservers.net")"
        echo "$(tr "Zugangsdaten eingeben, dann GUI-Installation fortsetzen." \
        "Enter your credentials, then continue the GUI installation." \
        "Saisissez vos identifiants, puis poursuivez l'installation." \
        "Introduce tus credenciales y continúa la instalación." \
        "Inserisci le credenziali, poi continua l'installazione." \
        "Introduza as credenciais e continue a instalação.")"
        echo
        read -p "$(tr "Konfiguration abgeschlossen? Enter zum Fortfahren..." \
        "Configuration complete? Press Enter to continue..." \
        "Configuration terminée ? Entrée pour continuer..." \
        "¿Configuración completada? Pulsa Intro para continuar..." \
        "Configurazione completata? Premi Invio per continuare..." \
        "Configuração concluída? Prima Enter para continuar...")"
        
    else
        echo
        echo "$(tr "Installation abgebrochen." \
        "Installation cancelled." \
        "Installation annulée." \
        "Instalación cancelada." \
        "Installazione annullata." \
        "Instalação cancelada.")"
        echo "$(tr "Bitte installiere hide.me CLI manuell:" \
        "Please install hide.me CLI manually:" \
        "Installez hide.me CLI manuellement :" \
        "Instala hide.me CLI manualmente:" \
        "Installa hide.me CLI manualmente:" \
        "Instale hide.me CLI manualmente:")"
        echo "1. Download: https://hide.me/en/software/linux"
        echo "$(tr "2. Entpacken und sudo ./install.sh ausführen" \
        "2. Extract and run sudo ./install.sh" \
        "2. Extraire et exécuter sudo ./install.sh" \
        "2. Extraer y ejecutar sudo ./install.sh" \
        "2. Estrai ed esegui sudo ./install.sh" \
        "2. Extrair e executar sudo ./install.sh")"
        echo
        exit 1
    fi
fi

echo "$(tr "✓ hide.me CLI gefunden" \
        "✓ hide.me CLI found" \
        "✓ hide.me CLI trouvé" \
        "✓ hide.me CLI encontrado" \
        "✓ hide.me CLI trovato" \
        "✓ hide.me CLI encontrado")"

# 2. Installiere Python-Abhängigkeiten (optional)
echo "$(tr "Installiere Python-Abhängigkeiten..." \
        "Installing Python dependencies..." \
        "Installation des dépendances Python..." \
        "Instalando dependencias de Python..." \
        "Installazione delle dipendenze Python..." \
        "A instalar dependências Python...")"

# Basis-Pakete (erforderlich)
REQUIRED_PKGS="python3 python3-gi gir1.2-gtk-3.0"
apt-get update -qq
apt-get install -y $REQUIRED_PKGS

if [ $? -ne 0 ]; then
    echo "$(tr "❌ Installation der Basis-Pakete fehlgeschlagen" \
        "❌ Failed to install required packages" \
        "❌ Échec de l'installation des paquets requis" \
        "❌ Error al instalar los paquetes necesarios" \
        "❌ Installazione dei pacchetti necessari non riuscita" \
        "❌ Falha ao instalar os pacotes necessários")"
    exit 1
fi

# Optionale Pakete für bessere Integration
OPTIONAL_PKGS=""
echo
echo "$(tr "Prüfe optionale Pakete..." \
        "Checking optional packages..." \
        "Vérification des paquets optionnels..." \
        "Comprobando paquetes opcionales..." \
        "Verifica dei pacchetti opzionali..." \
        "A verificar pacotes opcionais...")"

# AppIndicator3 für System-Tray (empfohlen)
if apt-cache show gir1.2-appindicator3-0.1 &>/dev/null; then
    OPTIONAL_PKGS="$OPTIONAL_PKGS gir1.2-appindicator3-0.1"
    echo "$(tr "  • gir1.2-appindicator3-0.1 verfügbar" \
        "  • gir1.2-appindicator3-0.1 available" \
        "  • gir1.2-appindicator3-0.1 disponible" \
        "  • gir1.2-appindicator3-0.1 disponible" \
        "  • gir1.2-appindicator3-0.1 disponibile" \
        "  • gir1.2-appindicator3-0.1 disponível")"
else
    echo "$(tr "  ⚠️  gir1.2-appindicator3-0.1 nicht verfügbar (Fallback auf StatusIcon)" \
        "  ⚠️  gir1.2-appindicator3-0.1 unavailable (using StatusIcon fallback)" \
        "  ⚠️  gir1.2-appindicator3-0.1 indisponible (utilisation de StatusIcon)" \
        "  ⚠️  gir1.2-appindicator3-0.1 no disponible (se usa StatusIcon)" \
        "  ⚠️  gir1.2-appindicator3-0.1 non disponibile (viene usato StatusIcon)" \
        "  ⚠️  gir1.2-appindicator3-0.1 indisponível (usando StatusIcon)")"
fi

# Notify für Desktop-Benachrichtigungen
if apt-cache show gir1.2-notify-0.7 &>/dev/null; then
    OPTIONAL_PKGS="$OPTIONAL_PKGS gir1.2-notify-0.7"
    echo "$(tr "  • gir1.2-notify-0.7 verfügbar" \
        "  • gir1.2-notify-0.7 available" \
        "  • gir1.2-notify-0.7 disponible" \
        "  • gir1.2-notify-0.7 disponible" \
        "  • gir1.2-notify-0.7 disponibile" \
        "  • gir1.2-notify-0.7 disponível")"
else
    echo "$(tr "  ⚠️  gir1.2-notify-0.7 nicht verfügbar (keine Benachrichtigungen)" \
        "  ⚠️  gir1.2-notify-0.7 unavailable (notifications disabled)" \
        "  ⚠️  gir1.2-notify-0.7 indisponible (notifications désactivées)" \
        "  ⚠️  gir1.2-notify-0.7 no disponible (notificaciones desactivadas)" \
        "  ⚠️  gir1.2-notify-0.7 non disponibile (notifiche disattivate)" \
        "  ⚠️  gir1.2-notify-0.7 indisponível (notificações desativadas)")"
fi

# PolicyKit Frontend (optional)
if apt-cache show policykit-1-gnome &>/dev/null; then
    OPTIONAL_PKGS="$OPTIONAL_PKGS policykit-1-gnome"
    echo "$(tr "  • policykit-1-gnome verfügbar" \
        "  • policykit-1-gnome available" \
        "  • policykit-1-gnome disponible" \
        "  • policykit-1-gnome disponible" \
        "  • policykit-1-gnome disponibile" \
        "  • policykit-1-gnome disponível")"
elif apt-cache show polkit-1-gnome &>/dev/null; then
    OPTIONAL_PKGS="$OPTIONAL_PKGS polkit-1-gnome"
    echo "$(tr "  • polkit-1-gnome verfügbar" \
        "  • polkit-1-gnome available" \
        "  • polkit-1-gnome disponible" \
        "  • polkit-1-gnome disponible" \
        "  • polkit-1-gnome disponibile" \
        "  • polkit-1-gnome disponível")"
else
    echo "$(tr "  ⚠️  PolicyKit-Frontend nicht verfügbar (pkexec funktioniert trotzdem)" \
        "  ⚠️  PolicyKit frontend unavailable (pkexec will still work)" \
        "  ⚠️  Interface PolicyKit indisponible (pkexec fonctionne quand même)" \
        "  ⚠️  Interfaz de PolicyKit no disponible (pkexec seguirá funcionando)" \
        "  ⚠️  Interfaccia PolicyKit non disponibile (pkexec funzionerà comunque)" \
        "  ⚠️  Interface PolicyKit indisponível (pkexec continuará a funcionar)")"
fi

# Installiere optionale Pakete falls verfügbar
if [ -n "$OPTIONAL_PKGS" ]; then
    apt-get install -y $OPTIONAL_PKGS 2>/dev/null || true
fi

echo "$(tr "✓ Abhängigkeiten installiert" \
        "✓ Dependencies installed" \
        "✓ Dépendances installées" \
        "✓ Dependencias instaladas" \
        "✓ Dipendenze installate" \
        "✓ Dependências instaladas")"

# 3. Kopiere Python-Skript nach /usr/local/bin
echo "$(tr "Installiere Hide.me GUI..." \
        "Installing Hide.me GUI..." \
        "Installation de Hide.me GUI..." \
        "Instalando Hide.me GUI..." \
        "Installazione di Hide.me GUI..." \
        "A instalar Hide.me GUI...")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prüfe ob bereits installiert (Update-Szenario)
if [ -f /usr/local/bin/hideme-vpn-gui ]; then
    echo "$(tr "⚠️  Hide.me GUI ist bereits installiert." \
        "⚠️  Hide.me GUI is already installed." \
        "⚠️  Hide.me GUI est déjà installé." \
        "⚠️  Hide.me GUI ya está instalado." \
        "⚠️  Hide.me GUI è già installato." \
        "⚠️  Hide.me GUI já está instalado.")"
    read -p "$(tr "Möchtest du die Installation überschreiben/aktualisieren? (j/n) " \
        "Overwrite/update the installation? (y/n) " \
        "Écraser/mettre à jour l'installation ? (o/n) " \
        "¿Sobrescribir/actualizar la instalación? (s/n) " \
        "Sovrascrivere/aggiornare l'installazione? (s/n) " \
        "Substituir/atualizar a instalação? (s/n) ")" -n 1 -r
    echo
    if ! is_yes "$REPLY"; then
        echo "$(tr "Installation abgebrochen." \
        "Installation cancelled." \
        "Installation annulée." \
        "Instalación cancelada." \
        "Installazione annullata." \
        "Instalação cancelada.")"
        exit 0
    fi
    
    # Stoppe laufende Instanz vor Update
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
    sleep 1
fi

cp "$SCRIPT_DIR/hideme-notifiy.py" /usr/local/bin/hideme-vpn-gui
chmod +x /usr/local/bin/hideme-vpn-gui
chown root:root /usr/local/bin/hideme-vpn-gui

echo "$(tr "✓ GUI installiert nach /usr/local/bin/hideme-vpn-gui" \
        "✓ GUI installed to /usr/local/bin/hideme-vpn-gui" \
        "✓ Interface installée dans /usr/local/bin/hideme-vpn-gui" \
        "✓ Interfaz instalada en /usr/local/bin/hideme-vpn-gui" \
        "✓ Interfaccia installata in /usr/local/bin/hideme-vpn-gui" \
        "✓ Interface instalada em /usr/local/bin/hideme-vpn-gui")"

# 4. Erstelle .desktop Datei für Anwendungsmenü
echo "$(tr "Erstelle Desktop-Integration..." \
        "Creating desktop integration..." \
        "Création de l'intégration au bureau..." \
        "Creando integración con el escritorio..." \
        "Creazione dell'integrazione desktop..." \
        "A criar integração com o ambiente de trabalho...")"
cat > /usr/share/applications/hideme-vpn-gui.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Hide.me VPN
Comment=Easy-to-use GUI for hide.me VPN
Comment[de]=Benutzerfreundliche GUI für hide.me VPN
Comment[fr]=Interface simple pour hide.me VPN
Comment[es]=Interfaz sencilla para hide.me VPN
Comment[it]=Interfaccia semplice per hide.me VPN
Comment[pt]=Interface simples para hide.me VPN
Exec=/usr/local/bin/hideme-vpn-gui
Icon=network-vpn
Terminal=false
Categories=Network;VPN;
StartupNotify=false
EOF

chmod 644 /usr/share/applications/hideme-vpn-gui.desktop

echo "$(tr "✓ Desktop-Datei erstellt" \
        "✓ Desktop file created" \
        "✓ Fichier desktop créé" \
        "✓ Archivo desktop creado" \
        "✓ File desktop creato" \
        "✓ Ficheiro desktop criado")"

# 5. Erstelle Autostart-Eintrag für den Benutzer
echo "$(tr "Richte Autostart ein..." \
        "Setting up autostart..." \
        "Configuration du démarrage automatique..." \
        "Configurando inicio automático..." \
        "Configurazione dell'avvio automatico..." \
        "A configurar o arranque automático...")"
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

echo "$(tr "✓ Autostart konfiguriert" \
        "✓ Autostart configured" \
        "✓ Démarrage automatique configuré" \
        "✓ Inicio automático configurado" \
        "✓ Avvio automatico configurato" \
        "✓ Arranque automático configurado")"

# 6. Installiere PolicyKit-Regel (VPN ohne Passwort steuern)
echo "$(tr "Installiere PolicyKit-Regel..." \
        "Installing PolicyKit rule..." \
        "Installation de la règle PolicyKit..." \
        "Instalando regla de PolicyKit..." \
        "Installazione della regola PolicyKit..." \
        "A instalar a regra PolicyKit...")"
if [ -f "$SCRIPT_DIR/50-hideme-vpn.rules" ]; then
    cp "$SCRIPT_DIR/50-hideme-vpn.rules" /etc/polkit-1/rules.d/50-hideme-vpn.rules
    chmod 644 /etc/polkit-1/rules.d/50-hideme-vpn.rules
    chown root:root /etc/polkit-1/rules.d/50-hideme-vpn.rules
    echo "$(tr "✓ PolicyKit-Regel installiert - VPN-Steuerung ohne Passwort" \
        "✓ PolicyKit rule installed - password-free VPN control" \
        "✓ Règle PolicyKit installée - contrôle VPN sans mot de passe" \
        "✓ Regla de PolicyKit instalada - control VPN sin contraseña" \
        "✓ Regola PolicyKit installata - controllo VPN senza password" \
        "✓ Regra PolicyKit instalada - controlo VPN sem palavra-passe")"
    
    # PolicyKit neu starten um Regel zu laden
    if command -v systemctl &> /dev/null; then
        systemctl restart polkit.service 2>/dev/null || true
        echo "$(tr "  PolicyKit neu gestartet" \
        "  PolicyKit restarted" \
        "  PolicyKit redémarré" \
        "  PolicyKit reiniciado" \
        "  PolicyKit riavviato" \
        "  PolicyKit reiniciado")"
    fi
else
    echo "$(tr "⚠️  PolicyKit-Regel nicht gefunden - VPN-Befehle erfordern Passwort-Eingabe" \
        "⚠️  PolicyKit rule not found - VPN commands will require a password" \
        "⚠️  Règle PolicyKit introuvable - les commandes VPN demanderont un mot de passe" \
        "⚠️  Regla de PolicyKit no encontrada - los comandos VPN requerirán contraseña" \
        "⚠️  Regola PolicyKit non trovata - i comandi VPN richiederanno una password" \
        "⚠️  Regra PolicyKit não encontrada - os comandos VPN exigirão palavra-passe")"
fi

# 7. Prüfe PolicyKit
if [ ! -f /usr/bin/pkexec ]; then
    echo "$(tr "⚠️  Warning: pkexec nicht gefunden. Systemd-Befehle benötigen evtl. manuelle sudo-Eingabe." \
        "⚠️  Warning: pkexec not found. Systemd commands may require manual sudo authentication." \
        "⚠️  Attention : pkexec introuvable. Les commandes systemd peuvent nécessiter une authentification sudo manuelle." \
        "⚠️  Aviso: pkexec no encontrado. Los comandos systemd pueden requerir autenticación manual con sudo." \
        "⚠️  Attenzione: pkexec non trovato. I comandi systemd potrebbero richiedere autenticazione manuale con sudo." \
        "⚠️  Aviso: pkexec não encontrado. Os comandos systemd podem exigir autenticação manual com sudo.")"
fi

echo
echo "$(tr "=== Installation abgeschlossen! ===" \
        "=== Installation complete! ===" \
        "=== Installation terminée ! ===" \
        "=== ¡Instalación completada! ===" \
        "=== Installazione completata! ===" \
        "=== Instalação concluída! ===")"
echo
echo "$(tr "Die Hide.me VPN GUI kann jetzt gestartet werden:" \
        "You can now start the Hide.me VPN GUI:" \
        "Vous pouvez maintenant lancer Hide.me VPN GUI :" \
        "Ya puedes iniciar Hide.me VPN GUI:" \
        "Ora puoi avviare Hide.me VPN GUI:" \
        "Pode agora iniciar Hide.me VPN GUI:")"
echo "$(tr "• Aus dem Anwendungsmenü: 'Hide.me VPN'" \
        "• From the application menu: 'Hide.me VPN'" \
        "• Depuis le menu des applications : 'Hide.me VPN'" \
        "• Desde el menú de aplicaciones: 'Hide.me VPN'" \
        "• Dal menu delle applicazioni: 'Hide.me VPN'" \
        "• No menu de aplicações: 'Hide.me VPN'")"
echo "$(tr "• Aus dem Terminal: hideme-vpn-gui" \
        "• From the terminal: hideme-vpn-gui" \
        "• Depuis le terminal : hideme-vpn-gui" \
        "• Desde el terminal: hideme-vpn-gui" \
        "• Dal terminale: hideme-vpn-gui" \
        "• No terminal: hideme-vpn-gui")"
echo "$(tr "• Automatisch beim nächsten Login" \
        "• Automatically at next login" \
        "• Automatiquement à la prochaine connexion" \
        "• Automáticamente en el próximo inicio de sesión" \
        "• Automaticamente al prossimo accesso" \
        "• Automaticamente no próximo início de sessão")"
echo
echo "$(tr "Tipp: Ein VPN-Icon erscheint im System Tray" \
        "Tip: A VPN icon will appear in the system tray" \
        "Astuce : Une icône VPN apparaîtra dans la barre système" \
        "Consejo: Aparecerá un icono VPN en la bandeja del sistema" \
        "Suggerimento: Apparirà un'icona VPN nell'area di notifica" \
        "Dica: Aparecerá um ícone VPN na área de notificação")"
echo
echo "$(tr "Hinweis: PolicyKit-Regel wurde installiert - VPN-Verbindungen" \
        "Note: The PolicyKit rule was installed - VPN connections" \
        "Note : La règle PolicyKit est installée - les connexions VPN" \
        "Nota: Se instaló la regla de PolicyKit - las conexiones VPN" \
        "Nota: La regola PolicyKit è installata - le connessioni VPN" \
        "Nota: A regra PolicyKit foi instalada - as ligações VPN")"
echo "$(tr "         können ohne Passwort-Eingabe gesteuert werden." \
        "         can be controlled without entering a password." \
        "         peuvent être contrôlées sans mot de passe." \
        "         se pueden controlar sin introducir contraseña." \
        "         possono essere controllate senza inserire la password." \
        "         podem ser controladas sem introduzir palavra-passe.")"
echo "$(tr "         Bei Problemen: Logout/Login oder System neustarten." \
        "         If you have problems, log out and back in or restart the system." \
        "         En cas de problème, reconnectez votre session ou redémarrez le système." \
        "         Si hay problemas, cierra y abre sesión o reinicia el sistema." \
        "         In caso di problemi, esci e accedi di nuovo o riavvia il sistema." \
        "         Se houver problemas, termine e reinicie a sessão ou reinicie o sistema.")"
echo

# Optional: Direkt starten
read -p "$(tr "GUI jetzt als $REAL_USER starten? (j/n) " \
        "Start the GUI as $REAL_USER now? (y/n) " \
        "Lancer l'interface comme $REAL_USER maintenant ? (o/n) " \
        "¿Iniciar la interfaz como $REAL_USER ahora? (s/n) " \
        "Avviare l'interfaccia come $REAL_USER ora? (s/n) " \
        "Iniciar a interface como $REAL_USER agora? (s/n) ")" -n 1 -r
echo
if is_yes "$REPLY"; then
    sudo -u "$REAL_USER" env HIDEME_LANG="$hideme_language" DISPLAY=:0 /usr/local/bin/hideme-vpn-gui &
    echo "$(tr "✓ GUI gestartet - siehe System Tray" \
        "✓ GUI started - check the system tray" \
        "✓ Interface lancée - voir la barre système" \
        "✓ Interfaz iniciada - mira la bandeja del sistema" \
        "✓ Interfaccia avviata - controlla l'area di notifica" \
        "✓ Interface iniciada - veja a área de notificação")"
fi

echo
echo "$(tr "Bei Problemen: Prüfe dass hide.me CLI korrekt konfiguriert ist" \
        "If you have problems, check that hide.me CLI is configured correctly" \
        "En cas de problème, vérifiez la configuration de hide.me CLI" \
        "Si hay problemas, comprueba la configuración de hide.me CLI" \
        "In caso di problemi, verifica la configurazione di hide.me CLI" \
        "Se houver problemas, verifique a configuração de hide.me CLI")"
echo "$(tr "und dass das Access Token unter /opt/hide.me/accessToken.txt existiert" \
        "and that the access token exists at /opt/hide.me/accessToken.txt" \
        "et la présence du jeton dans /opt/hide.me/accessToken.txt" \
        "y que el token exista en /opt/hide.me/accessToken.txt" \
        "e che il token esista in /opt/hide.me/accessToken.txt" \
        "e se o token existe em /opt/hide.me/accessToken.txt")"
