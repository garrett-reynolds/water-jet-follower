"""Run the installer's profile selection against controlled NetworkManager data."""

import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest import mock

import pytest


def run_wifi_block(tmp_path, profiles, fail_read=None, fail_modify=None):
    script = (Path(__file__).parents[2] / 'deploy/pi/install-offline.sh').read_text()
    block = script.split('python3 - "$backup" <<\'PY\'\n', 1)[1].split('\nPY\n', 1)[0]
    modified = []

    def nmcli(command, **kwargs):
        if command == ['nmcli', '-g', 'UUID', 'connection', 'show']:
            return SimpleNamespace(stdout='\n'.join(profiles))
        if command[1] == '-g':
            field, uuid = command[2], command[-1]
            if uuid == fail_read:
                raise subprocess.CalledProcessError(1, command)
            return SimpleNamespace(stdout=profiles[uuid][field])
        assert command[:4] == ['nmcli', 'connection', 'modify', 'uuid']
        assert command[5:] == ['connection.autoconnect', 'no']
        # Every modification requires the complete original-state file first.
        saved = json.loads((tmp_path / 'wifi-autoconnect-before.json').read_text())
        assert saved == [
            {'uuid': 'wlan', 'autoconnect': 'yes'},
            {'uuid': 'unbound', 'autoconnect': 'no'},
        ]
        if command[4] == fail_modify:
            raise subprocess.CalledProcessError(1, command)
        modified.append(command[4])
        return SimpleNamespace(stdout='')

    with mock.patch.object(subprocess, 'run', nmcli), mock.patch.object(sys, 'argv', ['-', str(tmp_path)]):
        exec(compile(block, 'install-offline.sh:wifi-backup', 'exec'), {})
    return modified


@pytest.fixture
def profiles():
    def profile(kind, interface, auto):
        return {'connection.type': kind, 'connection.interface-name': interface,
                'connection.autoconnect': auto}
    return {
        'eth': profile('802-3-ethernet', 'eth0', 'yes'),
        'wlan': profile('802-11-wireless', 'wlan0', 'yes'),
        'unbound': profile('802-11-wireless', '', 'no'),
        'other-radio': profile('802-11-wireless', 'wlan1', 'yes'),
    }


def test_saves_original_states_before_disabling_only_competing_wifi(tmp_path, profiles):
    assert run_wifi_block(tmp_path, profiles) == ['wlan', 'unbound']


def test_read_failure_changes_no_profiles(tmp_path, profiles):
    with pytest.raises(subprocess.CalledProcessError):
        run_wifi_block(tmp_path, profiles, fail_read='unbound')
    assert not (tmp_path / 'wifi-autoconnect-before.json').exists()


def test_partial_modify_failure_preserves_all_original_states(tmp_path, profiles):
    with pytest.raises(subprocess.CalledProcessError):
        run_wifi_block(tmp_path, profiles, fail_modify='unbound')
    assert json.loads((tmp_path / 'wifi-autoconnect-before.json').read_text()) == [
        {'uuid': 'wlan', 'autoconnect': 'yes'},
        {'uuid': 'unbound', 'autoconnect': 'no'},
    ]


def test_repeat_cannot_overwrite_original_states(tmp_path, profiles):
    run_wifi_block(tmp_path, profiles)
    original = (tmp_path / 'wifi-autoconnect-before.json').read_bytes()
    with pytest.raises(FileExistsError):
        run_wifi_block(tmp_path, profiles)
    assert (tmp_path / 'wifi-autoconnect-before.json').read_bytes() == original
