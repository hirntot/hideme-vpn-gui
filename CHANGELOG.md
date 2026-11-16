# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.1.2] - 2026-11-16

### Fixed

- Stop loaded hide.me instances in every state, including `activating`, even
  when the instance is not enabled. This prevents a failed connection attempt
  from recreating the kill-switch route after emergency cleanup.
- Run verified cleanup automatically when starting a VPN connection fails or
  times out, restoring network access without a second manual reset.

## [1.1.1] - 2026-11-16

### Fixed

- Detect all active hide.me service instances instead of checking only the
  last selected server.
- Stop and disable every active or enabled hide.me instance on disconnect and
  uninstall.
- Remove and verify stale IPv4/IPv6 rules and routes for hide.me routing table
  `55555`, preventing a leftover kill switch from blocking network traffic.
- Report cleanup failures instead of claiming that reset succeeded.
- Preserve unrelated firewall rules; emergency reset no longer flushes the
  system-wide iptables/ip6tables mangle tables.

## [1.1.0] - 2026-09-13

- Fix #1: translate GUI, notifications and setup/reset/removal prompts into
  English, French, Spanish, Italian and Portuguese while retaining German.
- Detect the system language automatically, with an English fallback and
  `HIDEME_LANG` override, including regional locale variants.
- Localize confirmation keys, desktop descriptions and server names; invalidate
  cached server lists when the language changes.
- Add regression tests for locale selection, confirmations and translation data.

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
