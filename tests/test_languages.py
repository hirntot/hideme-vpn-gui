"""Language regressions; no installation, VPN commands or network access."""
import ast
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ('de', 'en', 'fr', 'es', 'it', 'pt')
LOCALE_KEYS = ('HIDEME_LANG', 'LC_ALL', 'LC_MESSAGES', 'LANGUAGE', 'LANG')


def load_gui(language):
    # Mock GTK imports only; execute the full application module and its real logic.
    gi = types.ModuleType('gi')
    gi.require_version = lambda *args: None
    repository = types.ModuleType('gi.repository')
    for name in ('Gtk', 'GLib', 'GdkPixbuf', 'AppIndicator3', 'Notify'):
        setattr(repository, name, types.SimpleNamespace())
    spec = importlib.util.spec_from_file_location('hideme_gui_test', ROOT / 'hideme-notifiy.py')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'gi': gi, 'gi.repository': repository}), \
            patch.dict(os.environ, {'HIDEME_LANG': language}), \
            contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(module)
    return module


def shell_header(path):
    return path.read_text().split('\necho "===', 1)[0]


def shell_run(header, command, locale):
    env = {k: v for k, v in os.environ.items() if k not in LOCALE_KEYS}
    env.update(locale)
    return subprocess.run(['bash', '-c', header + '\n' + command],
                          env=env, text=True, capture_output=True, check=True).stdout


class LanguageTests(unittest.TestCase):
    def test_locale_detection_matches_shell(self):
        module = load_gui('en')
        cases = [({}, 'en'), ({'LANG': 'C.UTF-8'}, 'en'),
                 ({'LANG': 'ja_JP.UTF-8'}, 'en'),
                 ({'LANG': 'de_AT.UTF-8'}, 'de'),
                 ({'LANG': 'pt_BR.UTF-8'}, 'pt'),
                 ({'LANG': 'FR-fr'}, 'fr'),
                 ({'LANG': 'de_DE', 'LC_MESSAGES': 'it_IT'}, 'it'),
                 ({'LANG': 'de_DE', 'LC_ALL': 'es_ES'}, 'es'),
                 ({'LANGUAGE': 'fr:en', 'LANG': 'de_DE'}, 'fr'),
                 ({'HIDEME_LANG': 'pt', 'LC_ALL': 'C'}, 'pt'),
                 ({'HIDEME_LANG': 'unknown', 'LANG': 'de_DE'}, 'en')]
        cases += [({'HIDEME_LANG': language}, language) for language in LANGUAGES]
        for locale, expected in cases:
            with self.subTest(locale=locale):
                self.assertEqual(module.detect_language(locale), expected)
                for path in ROOT.glob('*.sh'):
                    self.assertEqual(shell_run(shell_header(path),
                                               'printf %s "$hideme_language"', locale), expected)

    def test_all_python_translations_have_matching_expressions(self):
        tree = ast.parse((ROOT / 'hideme-notifiy.py').read_text())
        count = 0
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == 'tr'):
                continue
            count += 1
            self.assertEqual(len(node.args), 6, node.lineno)
            expressions = []
            for arg in node.args:
                expressions.append(sorted(ast.dump(part.value) for part in ast.walk(arg)
                                          if isinstance(part, ast.FormattedValue)))
            self.assertTrue(all(value == expressions[0] for value in expressions), node.lineno)
        self.assertGreater(count, 90)

    def test_shell_translations_preserve_variables_and_select_all_languages(self):
        for path in ROOT.glob('*.sh'):
            source = path.read_text()
            calls = re.findall(r'\$\(tr ((?:"[^"\n]*"\s*(?:\\\n\s*)?){6})\)', source)
            self.assertEqual(len(calls), source.count('$(tr '), path.name)
            for call in calls:
                args = shlex.split(call.replace('\\\n', ''))
                self.assertEqual(len(args), 6)
                variables = [sorted(re.findall(r'\$[A-Za-z_0-9]+', arg)) for arg in args]
                self.assertTrue(all(value == variables[0] for value in variables), args)
            for i, lang in enumerate(LANGUAGES):
                # Feed the real text as literal arguments: no interpolation or system actions.
                command = '\n'.join('tr ' + ' '.join(shlex.quote(arg) for arg in
                                      shlex.split(call.replace('\\\n', ''))) + "; printf '\\0'"
                                      for call in calls)
                output = shell_run(shell_header(path), command, {'HIDEME_LANG': lang}).split('\0')[:-1]
                expected = [shlex.split(call.replace('\\\n', ''))[i] for call in calls]
                self.assertEqual(output, expected)

    def test_local_confirmation_keys_and_default_rejection(self):
        for path in ROOT.glob('*.sh'):
            for language, yes in zip(LANGUAGES, 'jyosss'):
                for answer, expected in [(yes, 'yes'), (yes.upper(), 'yes'),
                                         ('y', 'yes'), ('n', 'no'), ('', 'no'), ('?', 'no')]:
                    with self.subTest(script=path.name, language=language, answer=answer):
                        command = 'if is_yes ' + shlex.quote(answer) + '; then echo yes; else echo no; fi'
                        self.assertEqual(shell_run(shell_header(path), command,
                                                   {'HIDEME_LANG': language}).strip(), expected)

    def test_country_names_and_formatted_messages(self):
        countries = ['Deutschland', 'Germany', 'Allemagne', 'Alemania', 'Germania', 'Alemanha']
        for language, country in zip(LANGUAGES, countries):
            module = load_gui(language)
            with tempfile.TemporaryDirectory() as directory:
                module.HideMeVPN.CONFIG_FILE = str(Path(directory) / 'config.json')
                vpn = module.HideMeVPN()
                self.assertEqual(vpn.get_servers()['de'], country)
                success, message = vpn.add_favorite_server('de')
                self.assertTrue(success)
                self.assertIn('de', message)
                self.assertNotIn('{', message)
                if language != 'de':
                    self.assertNotIn('hinzugefügt', message)

    def test_cache_is_language_specific_and_preserves_preferences(self):
        server = {'code': 'de', 'display': 'Berlin, Deutschland'}
        for language in LANGUAGES:
            module = load_gui(language)
            with tempfile.TemporaryDirectory() as directory:
                config = Path(directory) / 'config.json'
                module.HideMeVPN.CONFIG_FILE = str(config)
                # Legacy caches were always German.
                config.write_text(json.dumps({'last_server': 'de', 'favorite_servers': ['de'],
                                              'cached_servers': [server]}))
                vpn = module.HideMeVPN()
                self.assertEqual(vpn.current_server, 'de')
                self.assertEqual(vpn.favorite_servers, ['de'])
                self.assertEqual(vpn.cached_servers, [server] if language == 'de' else [])
                vpn.set_cached_servers([server])
                self.assertEqual(json.loads(config.read_text())['cached_servers_language'], language)
                self.assertEqual(module.HideMeVPN().cached_servers, [server])

    def test_server_fetch_uses_selected_language(self):
        for language in LANGUAGES:
            module = load_gui(language)
            with tempfile.TemporaryDirectory() as directory:
                module.HideMeVPN.CONFIG_FILE = str(Path(directory) / 'config.json')
                vpn = module.HideMeVPN()
                response = io.BytesIO(b'<img src="https://hide.me/images/flags/png/de.png"><span class="ml-1 u-bold">Berlin,</span><span>Germany</span>')
                with patch.object(module.urllib.request, 'urlopen', return_value=response) as fetch:
                    self.assertEqual(vpn.fetch_servers_from_website()[0]['code'], 'de')
                    self.assertEqual(fetch.call_args[0][0].full_url,
                                     'https://hide.me/' + language + '/network')

    @unittest.skipIf(os.geteuid() == 0, 'Only exercise the unprivileged early-exit path')
    def test_installer_exits_without_root_in_every_language(self):
        for language in LANGUAGES:
            env = dict(os.environ, HIDEME_LANG=language)
            result = subprocess.run(['bash', str(ROOT / 'hideme-gui-install.sh')],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('sudo', result.stdout)
            if language != 'de':
                self.assertNotIn('benötigt', result.stdout)


if __name__ == '__main__':
    unittest.main()
