#!/bin/bash
# Run only from the staged directory on water-jets, with 24 V module power off.
set -euo pipefail
export SYSTEMD_PAGER=cat
export PAGER=cat
umask 077
trap 'printf "Install stopped at line %s. Keep 24 V power off.\n" "$LINENO" >&2' ERR
stage=/home/pi/water-jet-install-20260925
profile=/etc/NetworkManager/system-connections/water-jets-ap.nmconnection
[[ $EUID -eq 0 ]]
[[ $(hostname) == water-jets ]]
ip -4 -o addr show dev eth0 | grep -Fq ' 10.0.10.204/24 '
[[ -d /home/pi/tracker && -d /home/pi/wj-venv ]]
[[ -f /home/pi/data/baseline.json && -f /home/pi/data/profile.json ]]
[[ -f "$stage/water-jets-ap.nmconnection" && ! -L "$stage/water-jets-ap.nmconnection" ]]
[[ $(stat -c %a "$stage/water-jets-ap.nmconnection") == 600 ]]
[[ $(stat -c %U "$stage/water-jets-ap.nmconnection") == pi ]]
if pgrep -f '[p]ython.*-m tracker.run' >/dev/null; then
    printf 'A show is already running. Stop before install.\n' >&2
    exit 1
fi
if nmcli -g connection.id connection show water-jets-ap >/dev/null 2>&1; then
    printf 'The AP profile already exists. Stop before install.\n' >&2
    exit 1
fi
python3 - <<'PY'
import configparser
from pathlib import Path
import re
import subprocess
import sys

# Never print profile values or an exception that can contain a secret.
try:
    config = configparser.ConfigParser(interpolation=None, strict=True)
    with Path('/home/pi/water-jet-install-20260925/water-jets-ap.nmconnection').open() as stream:
        config.read_file(stream)
    expected = {
        ('connection', 'id'): 'water-jets-ap',
        ('connection', 'type'): 'wifi',
        ('connection', 'interface-name'): 'wlan0',
        ('wifi', 'mode'): 'ap',
        ('wifi', 'ssid'): 'water-jets',
        ('wifi', 'band'): 'bg',
        ('wifi', 'channel'): '6',
        ('wifi-security', 'key-mgmt'): 'wpa-psk',
        ('ipv4', 'method'): 'shared',
        ('ipv4', 'address1'): '10.42.0.1/24',
        ('ipv6', 'method'): 'disabled',
    }
    if any(config.get(section, key) != value for (section, key), value in expected.items()):
        raise ValueError()
    if not config.getboolean('connection', 'autoconnect'):
        raise ValueError()
    for key, value in [('proto', 'rsn'), ('pairwise', 'ccmp'), ('group', 'ccmp')]:
        if [item for item in config.get('wifi-security', key).split(';') if item] != [value]:
            raise ValueError()
    secret = config.get('wifi-security', 'psk')
    if len(secret) != 16 or not re.fullmatch(r'[ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789]+', secret):
        raise ValueError()
    if not all(re.search(pattern, secret) for pattern in (r'[A-Z]', r'[a-z]', r'[2-9]')):
        raise ValueError()
    result = subprocess.run(
        ['nmcli', '-g', 'connection.autoconnect-priority', 'connection', 'show', 'netplan-wlan0-wM'],
        check=True, capture_output=True, text=True,
    )
    if config.getint('connection', 'autoconnect-priority') <= int(result.stdout.strip()):
        raise ValueError()
except Exception:
    print('Private AP profile validation failed. No install change ran.', file=sys.stderr)
    raise SystemExit(1)

# Read only known root launch files and unit paths. Print matching paths, never content.
paths = [Path(name) for name in (
    '/var/spool/cron/crontabs/root', '/etc/crontab', '/etc/rc.local',
    '/root/.profile', '/root/.bash_profile', '/root/.bash_login', '/root/.bashrc',
    '/root/.config/autostart/water-jets.desktop',
)]
paths.extend(Path('/etc/cron.d').glob('*'))
for unit_dir in (Path('/root/.config/systemd/user'), Path('/etc/systemd/user')):
    for pattern in ('*.service', '*.timer', '*.service.d/*.conf', '*.target.wants/*.service', '*.target.requires/*.service'):
        paths.extend(unit_dir.glob(pattern))
launch = re.compile(r'tracker(?:\.|/)run|water[-_]jet[-_]show|python[^\n]*tracker|\bshow\b[^\n]*--(?:baseline|profile)', re.I)
matched = False
for path in sorted(set(paths)):
    try:
        if not path.exists() and not path.is_symlink():
            continue
        if path.is_dir():
            continue
        for line in path.read_text().splitlines():
            if line.lstrip().startswith('#'):
                continue
            if launch.search(line):
                print(path, file=sys.stderr)
                matched = True
                break
    except Exception:
        print(path, file=sys.stderr)
        raise SystemExit(1)
if matched:
    raise SystemExit(1)
print('Private AP profile and root launch preflight passed.')
PY
cd "$stage"
sha256sum --check reviewed-files.sha256
backup=/root/water-jet-before-$(date -u +%Y%m%dT%H%M%SZ)
mkdir -m 0700 "$backup"
printf '%s\n' "$backup" > "$stage/backup-path.txt"
chmod 0644 "$stage/backup-path.txt"
for unit in NetworkManager olad ssh avahi-daemon water-jet-show water-jet-ola-lock-cleanup; do
    printf '%s enabled=' "$unit" >> "$backup/unit-states.txt"
    systemctl is-enabled "$unit" >> "$backup/unit-states.txt" 2>&1 || :
    printf '%s active=' "$unit" >> "$backup/unit-states.txt"
    systemctl is-active "$unit" >> "$backup/unit-states.txt" 2>&1 || :
done
nmcli -f all connection show netplan-eth0 > "$backup/ethernet-before.txt"
nmcli -f NAME,UUID,TYPE,DEVICE,AUTOCONNECT connection show > "$backup/connections-before.txt"
for target in /etc/systemd/system/water-jet-show.service /etc/systemd/system/water-jet-ola-lock-cleanup.service /etc/systemd/system/olad.service.d/water-jet-lock-cleanup.conf /usr/local/sbin/water-jet-clear-ola-locks "$profile"; do
    if [[ -e "$target" || -L "$target" ]]; then
        [[ -f "$target" && ! -L "$target" ]]
        cp --preserve=all --parents "$target" "$backup/"
        stat -c '%n %U:%G %a' "$target" >> "$backup/files.txt"
    else
        printf 'ABSENT %s\n' "$target" >> "$backup/files.txt"
    fi
done
python3 - "$backup" <<'PY'
import json
import os
from pathlib import Path
import subprocess
import sys

def read_field(uuid, field):
    return subprocess.run(
        ['nmcli', '-g', field, 'connection', 'show', 'uuid', uuid],
        check=True, capture_output=True, text=True,
    ).stdout.strip()

# Save all original states before the first NetworkManager target change.
# Unbound Wi-Fi profiles can also claim wlan0. Other interfaces stay unchanged.
uuids = subprocess.run(
    ['nmcli', '-g', 'UUID', 'connection', 'show'],
    check=True, capture_output=True, text=True,
).stdout.splitlines()
competing = []
for uuid in uuids:
    if read_field(uuid, 'connection.type') not in ('802-11-wireless', 'wifi'):
        continue
    if read_field(uuid, 'connection.interface-name') not in ('', '--', 'wlan0'):
        continue
    autoconnect = read_field(uuid, 'connection.autoconnect')
    if autoconnect not in ('yes', 'no'):
        raise SystemExit('Unknown Wi-Fi autoconnect state. No network change ran.')
    competing.append({'uuid': uuid, 'autoconnect': autoconnect})
with (Path(sys.argv[1]) / 'wifi-autoconnect-before.json').open('x') as stream:
    json.dump(competing, stream)
    stream.flush()
    os.fsync(stream.fileno())
for item in competing:
    subprocess.run(
        ['nmcli', 'connection', 'modify', 'uuid', item['uuid'],
         'connection.autoconnect', 'no'], check=True,
    )
PY
install -o root -g root -m 0600 "$stage/water-jets-ap.nmconnection" "$profile"
cmp --silent "$stage/water-jets-ap.nmconnection" "$profile"
rm -- "$stage/water-jets-ap.nmconnection"
install -o root -g root -m 0755 clear_ola_locks.py /usr/local/sbin/water-jet-clear-ola-locks
install -o root -g root -m 0644 water-jet-show.service /etc/systemd/system/water-jet-show.service
install -o root -g root -m 0644 water-jet-ola-lock-cleanup.service /etc/systemd/system/water-jet-ola-lock-cleanup.service
install -d -o root -g root -m 0755 /etc/systemd/system/olad.service.d
install -o root -g root -m 0644 olad-water-jet-lock-cleanup.conf /etc/systemd/system/olad.service.d/water-jet-lock-cleanup.conf
systemctl stop olad
if pgrep -x olad >/dev/null; then
    printf 'OLA is still running. Cleanup is blocked.\n' >&2
    exit 1
fi
python3 - <<'PY'
import os
from pathlib import Path
for proc in Path('/proc').iterdir():
    if not proc.name.isdecimal():
        continue
    try:
        for fd in (proc / 'fd').iterdir():
            try:
                target = os.readlink(fd)
            except FileNotFoundError:
                continue
            if target.startswith('/dev/ttyUSB') or target in ('/dev/ttyENTTEC', '/dev/ttyLIDAR'):
                raise SystemExit('A serial device is open. Cleanup is blocked.')
    except FileNotFoundError:
        continue
PY
systemctl daemon-reload
systemd-analyze verify /etc/systemd/system/water-jet-show.service /etc/systemd/system/water-jet-ola-lock-cleanup.service
systemctl show olad -p Requires -p After
systemctl show water-jet-show -p ExecStart -p Restart -p RestartUSec -p StartLimitIntervalUSec -p StartLimitBurst
nmcli connection load "$profile"
nmcli connection modify water-jets-ap connection.autoconnect-retries 0
nmcli connection up water-jets-ap
ip -4 -o addr show dev eth0 | grep -Fq ' 10.0.10.204/24 '
nmcli -f all connection show netplan-eth0 > "$backup/ethernet-after.txt"
cmp --silent "$backup/ethernet-before.txt" "$backup/ethernet-after.txt"
systemctl enable water-jet-show
systemctl start olad
systemctl start water-jet-show
stat -c '%n %U:%G %a' "$profile" /usr/local/sbin/water-jet-clear-ola-locks /etc/systemd/system/water-jet-show.service /etc/systemd/system/water-jet-ola-lock-cleanup.service /etc/systemd/system/olad.service.d/water-jet-lock-cleanup.conf
nmcli -f connection.id,connection.autoconnect,802-11-wireless.ssid,802-11-wireless.mode,802-11-wireless-security.key-mgmt,802-11-wireless-security.proto,ipv4.method,ipv4.addresses connection show water-jets-ap
ip -4 -br addr
systemctl show water-jet-show -p ActiveState -p SubState -p Result -p NRestarts
printf 'Install commands finished. Backup: %s\n' "$backup"
printf 'Keep 24 V power off. Boot, offline, and restart checks remain.\n'
