# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-02-17

### Added
- Initial release of Hide.me VPN GUI
- System tray integration with AppIndicator3 and StatusIcon fallback
- One-click VPN connection/disconnection
- Dynamic server list fetching from hide.me website
- Server selection dialog with worldwide servers
- Live connection status display
- Desktop notifications via libnotify
- PolicyKit integration for password-free control
- Autostart support
- Emergency network reset script
- Installation and uninstallation scripts
- MIT License
- Comprehensive documentation (English and German)

### Features
- Connects via systemctl to hide.me CLI
- Caches server list at startup for instant access
- Status polling every 5 seconds
- Saves last used server preference
- Non-blocking UI through threading

### Technical
- Python 3 with GTK 3.0
- Systemd service integration
- PolicyKit rule for sudo group members
- Regex-based server parsing from website
