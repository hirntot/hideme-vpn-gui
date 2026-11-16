"""Regression tests for hide.me service discovery and kill-switch cleanup."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from test_languages import ROOT, load_gui


def completed(args, returncode=0, stdout='', stderr=''):
    return subprocess.CompletedProcess(args, returncode, stdout, stderr)


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.module = load_gui('en')

    def test_service_listing_accepts_only_hide_me_instances(self):
        output = (
            'hide.me@nl.service loaded active running Netherlands\n'
            'ssh.service loaded active running SSH\n'
            'hide.me@bad/name.service loaded active running Invalid\n'
            'hide.me@de-1.service loaded active running Germany\n'
        )
        with patch.object(self.module.subprocess, 'run',
                          return_value=completed([], stdout=output)):
            self.assertEqual(
                self.module.HideMeVPN.active_service_units(),
                ['hide.me@de-1.service', 'hide.me@nl.service']
            )

    def test_status_finds_an_active_service_other_than_saved_server(self):
        with tempfile.TemporaryDirectory() as directory:
            self.module.HideMeVPN.CONFIG_FILE = str(Path(directory) / 'config.json')
            vpn = self.module.HideMeVPN()
            vpn.current_server = 'nl'
            with patch.object(vpn, 'active_service_units',
                              return_value=['hide.me@de.service']):
                self.assertTrue(vpn.get_status())
            self.assertEqual(vpn.current_server, 'de')

    def test_disconnect_runs_single_privileged_targeted_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            self.module.HideMeVPN.CONFIG_FILE = str(Path(directory) / 'config.json')
            vpn = self.module.HideMeVPN()
            vpn.current_server = 'nl'
            calls = []

            def fake_run(command, **kwargs):
                calls.append(command)
                return completed(command)

            with patch.object(vpn, '_cleanup_program',
                                 return_value='/usr/local/bin/hideme-vpn-gui'), \
                    patch.object(self.module.subprocess, 'run', side_effect=fake_run):
                success, _ = vpn.disconnect()

            self.assertTrue(success)
            self.assertEqual(calls, [
                ['pkexec', '/usr/local/bin/hideme-vpn-gui', '--cleanup-routing']
            ])

    def test_cleanup_verifies_rules_routes_and_interface(self):
        commands = []

        def fake_run(command, **kwargs):
            commands.append(command)
            if command == ['ip', 'link', 'show', 'vpn']:
                return completed(command, returncode=1)
            if command[-2:] == ['rule', 'show']:
                return completed(command, stdout='0: from all lookup local\n')
            return completed(command)

        vpn_type = self.module.HideMeVPN
        with patch.object(self.module.os, 'geteuid', return_value=0), \
                patch.object(self.module.os.path, 'isfile', return_value=False), \
                patch.object(vpn_type, 'active_service_units', return_value=[]), \
                patch.object(vpn_type, 'enabled_service_units', return_value=[]), \
                patch.object(vpn_type, '_delete_table_rules'), \
                patch.object(self.module.subprocess, 'run', side_effect=fake_run):
            success, message = vpn_type.cleanup_system_state()

        self.assertTrue(success, message)
        self.assertFalse(any(command and command[0] in ('iptables', 'ip6tables')
                             for command in commands))
        self.assertIn(['ip', 'route', 'flush', 'table', '55555'], commands)
        self.assertIn(['ip', '-6', 'route', 'flush', 'table', '55555'], commands)

    def test_cleanup_stops_active_and_disables_enabled_instances(self):
        commands = []

        def fake_run(command, **kwargs):
            commands.append(command)
            if command == ['ip', 'link', 'show', 'vpn']:
                return completed(command, returncode=1)
            return completed(command)

        vpn_type = self.module.HideMeVPN
        with patch.object(self.module.os, 'geteuid', return_value=0), \
                patch.object(self.module.os.path, 'isfile', return_value=False), \
                patch.object(vpn_type, 'active_service_units',
                             side_effect=[['hide.me@de.service'], []]), \
                patch.object(vpn_type, 'enabled_service_units',
                             return_value=['hide.me@fr.service']), \
                patch.object(vpn_type, '_delete_table_rules'), \
                patch.object(self.module.subprocess, 'run', side_effect=fake_run):
            success, message = vpn_type.cleanup_system_state()

        self.assertTrue(success, message)
        for unit in ('hide.me@de.service', 'hide.me@fr.service'):
            self.assertIn(['systemctl', 'stop', unit], commands)
            self.assertIn(['systemctl', 'disable', unit], commands)

    def test_cleanup_fails_when_kill_switch_rule_remains(self):
        def fake_run(command, **kwargs):
            if command == ['ip', 'rule', 'show']:
                return completed(command, stdout='10: from all lookup 55555\n')
            if command == ['ip', 'link', 'show', 'vpn']:
                return completed(command, returncode=1)
            return completed(command)

        vpn_type = self.module.HideMeVPN
        with patch.object(self.module.os, 'geteuid', return_value=0), \
                patch.object(self.module.os.path, 'isfile', return_value=False), \
                patch.object(vpn_type, 'active_service_units', return_value=[]), \
                patch.object(vpn_type, 'enabled_service_units', return_value=[]), \
                patch.object(vpn_type, '_delete_table_rules'), \
                patch.object(self.module.subprocess, 'run', side_effect=fake_run):
            success, message = vpn_type.cleanup_system_state()

        self.assertFalse(success)
        self.assertIn('IPv4 rule', message)

    def test_scripts_do_not_flush_global_firewall_tables(self):
        python_source = (ROOT / 'hideme-notifiy.py').read_text()
        reset_source = (ROOT / 'hideme-emergency-reset.sh').read_text()
        uninstall_source = (ROOT / 'hideme-gui-uninstall.sh').read_text()
        for source in (python_source, reset_source):
            self.assertNotIn('iptables -t mangle -F', source)
            self.assertNotIn('ip6tables -t mangle -F', source)
        self.assertIn('while ip rule del table "$ROUTING_TABLE"', reset_source)
        self.assertIn('--cleanup-routing', uninstall_source)


if __name__ == '__main__':
    unittest.main()
