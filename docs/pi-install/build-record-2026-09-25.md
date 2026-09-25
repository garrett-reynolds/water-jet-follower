# Pi offline install record

Date: 2026-09-25. Initial install checked at 15:39 UTC. Final update checked at 16:57 UTC.

The user confirmed that the 24 V module power was off before installation.
The private Wi-Fi is active.
The show is enabled for boot and running with Lights only on.
This is software evidence. It does not prove physical water off.

## Installed state

Commit `9bd986a` is installed on the real Pi.
LiDAR loss now turns Lights only on and clears a held water test.
The old site Wi-Fi profile has autoconnect off.
The private AP has unlimited autoconnect retries.
Ethernet stayed unchanged.

| Item | Checked result |
|---|---|
| Host and wired rescue | `water-jets`, `eth0` at `10.0.10.204/24`, profile `netplan-eth0` |
| Wired settings | Saved before/after NetworkManager output matches byte for byte |
| AP profile | `water-jets-ap`, autoconnect yes, priority `100` versus infrastructure priority `0` |
| AP radio | `wlan0`, AP mode, SSID `water-jets`, 2.4 GHz channel 6 |
| AP security | WPA2 Personal: `wpa-psk`, RSN only, pairwise/group CCMP only |
| AP address | `10.42.0.1/24`, IPv4 shared mode, IPv6 disabled |
| DHCP and DNS | UDP port 67 listening; TCP and UDP port 53 at `10.42.0.1` |
| Private Pi profile | `/etc/NetworkManager/system-connections/water-jets-ap.nmconnection`, `root:root`, mode `0600` |
| Private Windows record | `C:\Users\garrett.reynolds\.water-jets\wifi-passphrase.txt`; only Garrett and SYSTEM have access |
| Show | `water-jet-show.service`, enabled, active/running, PID 3171 at the check |
| OLA | Enabled and active |
| Cleanup | Static unit, active/exited, result success; required before OLA |
| Restart settings | Failure restart, 5-second delay, five starts in five minutes |
| LiDAR | `/dev/ttyLIDAR -> ttyUSB1`; API `lidar_ok=true`, `scan_hz=16.24` |
| Enttec | `/dev/ttyENTTEC -> ttyUSB0` |
| Viewer | Port 8080 listening on all IPv4 interfaces; `/system-data` returns JSON |
| Safe start flag | Unit always passes `--lights-only`; API says `lights_only=true` |
| Other rescue services | NetworkManager, SSH, and Avahi enabled and active |

## Final hardening update

The update saved the prior state in root-only folder
`/root/water-jet-before-update-20260925TTsCx0f`, mode `0700`.
It contains the old `run.py`, its hash and mode, the AP values, each competing Wi-Fi
autoconnect value by UUID, and Ethernet before/after records.

The installed `/home/pi/tracker/run.py` SHA-256 is
`35f4d2ec745ca277fdfec8f441daf40bfeb5f0568a95e0c0e17dfd086224182e`.
The old site Wi-Fi profile changed from autoconnect `yes` to `no`.
`water-jets-ap` changed from retry value `-1` to `0`.
The Ethernet record matched before and after.

The checked real-Pi results were:

- The AP returned to `water-jets-ap` at `10.42.0.1/24` after NetworkManager released and retook `wlan0`.
- A held jet command at DMX `5` was present before LiDAR driver loss.
- LiDAR driver loss turned Lights only on, cleared the held test, and read back all 512 slots at zero.
- LiDAR driver return restored tracking but did not restore water.
- A fresh operator action could command the held test again.
- The final stop read back all 512 slots at zero.
- A normal reboot restored the AP, Ethernet, OLA, LiDAR, web page, and show.
- After reboot, `lights_only=true`, `test_mode=false`, `lidar_ok=true`, and OLA was active.

The private file contains the SSID, password, URL, and SSH command.
No password is stored in this repo or this record.
The temporary Pi secret file was removed after the root profile was installed and compared.
The private Windows directory and file both disable ACL inheritance.
Their only access entries are Garrett's Windows account and SYSTEM.
The machine ledger records the local change and its revert commands.

## Before-copy

The root-only folder is `/root/water-jet-before-20260925T153515Z`, mode `0700`.
It holds `unit-states.txt`, `files.txt`, `connections-before.txt`, `ethernet-before.txt`, and `ethernet-after.txt`.
All five exact install targets were absent before installation.
No prior target file needed a copy.
OLA, NetworkManager, SSH, and Avahi were enabled and active.
The two water-jet units did not exist.

## Install checks and one recovered fault

Strict wired SSH used the saved `water-jets` host key with `HostKeyAlias=water-jets`.
The installer checked the host, wired address, app/data paths, and profile before changes.
It checked the bounded root cron, user-unit, and startup paths for another show launch.
It would stop on a matching launch or a read error.
It passed those checks and made the before-copy folder.

The user ran the root command through an interactive SSH terminal.
`systemctl show` opened `less` and paused the install.
The controller loaded and started the AP before it found the waiting installer.
The checked pager was PID 2744, child of `systemctl` PID 2742, child of installer PID 2565.
Only that pager received TERM.
The original installer then finished.
No installer or service process was killed.
The source now exports `SYSTEMD_PAGER=cat` and `PAGER=cat` to prevent this pause.

At 15:38:42 UTC, the first show start refused to run because OLA had no universe data yet.
The log recorded a failed initial zero check and a successful zero send on exit.
The service retried once at 15:38:48 UTC under its normal failure policy.
That start logged `LIGHTS ONLY` and `zero: sent=True slots_held=512 ALL ZERO`.
The show then opened port 8080.
The checked restart count is `1`.
No start-limit reset ran.
This is observed automatic failure recovery, not the full fault test.

The install left all four public service/program files with the expected owner and mode.
Each installed SHA-256 matches the repo file:

| Source | Installed file | SHA-256 |
|---|---|---|
| `deploy/pi/clear_ola_locks.py` | `/usr/local/sbin/water-jet-clear-ola-locks` | `65f43cb3d821cfd719afff46a2d58e998eafe28ac49269f03ed0eda458b1ea9f` |
| `deploy/systemd/water-jet-show.service` | `/etc/systemd/system/water-jet-show.service` | `4c6fd2a11c7e7c773af18cefdeadd1fce7fc580d4e8c49bef671b8e4af37fa6d` |
| `deploy/systemd/water-jet-ola-lock-cleanup.service` | `/etc/systemd/system/water-jet-ola-lock-cleanup.service` | `9569999da73bd950d696cbabe9d58e9d5b8e56d66d5075803adb359e217d1e4b` |
| `deploy/systemd/olad-water-jet-lock-cleanup.conf` | `/etc/systemd/system/olad.service.d/water-jet-lock-cleanup.conf` | `a98e9262418e2f63428913576c96b71dbeb5dfabe9267ac3a05cd86f22a07826` |

The program is mode `0755`.
The service files and OLA drop-in are mode `0644`.
All four are owned by `root:root`.
`systemd-analyze verify` passed on the real Pi.
The merged OLA unit requires and starts after the cleanup unit.
The show wants and starts after OLA and NetworkManager.

## Repeat the read-only checks

From Windows PowerShell:

```powershell
ssh -o StrictHostKeyChecking=yes -o HostKeyAlias=water-jets pi@10.0.10.204
```

Then run in the Pi shell:

```bash
ip -4 -br addr
nmcli -f DEVICE,TYPE,STATE,CONNECTION device status
nmcli -f connection.id,connection.autoconnect,connection.autoconnect-priority,802-11-wireless.ssid,802-11-wireless.mode,802-11-wireless-security.key-mgmt,802-11-wireless-security.proto,802-11-wireless-security.pairwise,802-11-wireless-security.group,ipv4.method,ipv4.addresses connection show water-jets-ap
systemctl is-enabled water-jet-show olad NetworkManager ssh avahi-daemon
systemctl is-active water-jet-show olad water-jet-ola-lock-cleanup
systemctl --no-pager show water-jet-show -p ActiveState -p SubState -p Result -p NRestarts -p ExecStart -p Restart -p RestartUSec -p StartLimitIntervalUSec -p StartLimitBurst
systemctl --no-pager show olad -p Requires -p After
systemd-analyze verify /etc/systemd/system/water-jet-show.service /etc/systemd/system/water-jet-ola-lock-cleanup.service
ss -ltnu
curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8080/system-data
journalctl -b -u water-jet-show -u water-jet-ola-lock-cleanup --no-pager -n 100
sudo cmp --silent /root/water-jet-before-20260925T153515Z/ethernet-before.txt /root/water-jet-before-20260925T153515Z/ethernet-after.txt
```

The final `cmp` returns success with no output for equal files.
Do not use `nmcli --show-secrets` or print the private files.

## Exact rollback for this install

Keep 24 V module power off.
Use the wired SSH address above or the local Pi console.
These Bash commands apply to this recorded install, whose five target files were all absent before it.
Do not use them if another deployment has since replaced the files.

```bash
sudo systemctl disable --now water-jet-show.service
sudo systemctl stop olad.service
sudo nmcli connection down water-jets-ap
sudo nmcli connection delete water-jets-ap
sudo nmcli connection modify netplan-wlan0-wM connection.autoconnect yes
sudo nmcli connection up netplan-wlan0-wM
sudo rm -- /etc/systemd/system/olad.service.d/water-jet-lock-cleanup.conf
sudo systemctl daemon-reload
sudo systemctl stop water-jet-ola-lock-cleanup.service
sudo rm -- /etc/systemd/system/water-jet-show.service /etc/systemd/system/water-jet-ola-lock-cleanup.service /usr/local/sbin/water-jet-clear-ola-locks
sudo systemctl daemon-reload
sudo systemctl start olad.service
systemctl --no-pager status olad.service
```

Do not restore stale lock files.
Do not restart the show during rollback.
The backup and private Windows record remain for recovery.
Do not remove the private record while the AP still needs its password.
Rollback commands are documented but have not been run.

## Source installer repeat and failure rules

The updated installer refuses to run if the AP profile already exists or a show runs.
Do not rerun it on this installed Pi to apply the final-review fixes.
Before an update, save `/home/pi/tracker/run.py` and all affected Wi-Fi autoconnect settings.
Deploy the reviewed `tracker/run.py`, disable competing Wi-Fi autoconnect, and set
`water-jets-ap` autoconnect retries to `0` through a separate checked update.
That checked update is complete. Do not rerun the fresh installer on this Pi.

For a fresh install, the new root-only backup contains `wifi-autoconnect-before.json`.
It records all competing profile UUIDs and their original `yes` or `no` states.
The installer writes and flushes the full file before changing any profile.
An error stops the installer without automatic rollback.
Some profiles or service files can already be changed when it stops.
Keep 24 V power off and use Ethernet or the local console to restore the saved states.
Do not delete the backup or repeat the install until the partial state is checked.
The saved file must not be overwritten by a retry.

For this recorded install, `netplan-wlan0-wM` originally had autoconnect `yes`.
The exact rollback above restores that value after this update.
For a later fresh install, restore every UUID and value from its own backup instead.
The earlier backup does not contain the new JSON file.

## Open proof and recorded exceptions

Private-Wi-Fi SSH by address and `water-jets.local` passed from a laptop.
A physical LiDAR cable pull and reconnect also passed with Lights only held on.
See [the proof record](real-pi-proof-2026-09-25.md).

- Cold boot and physical water-off checks with the full rig wait until the packed jets are set up again.
- The documented rollback path is not tested.
- Local-console rescue is not tested. The user chose to skip it.
- Password rotation is not tested. The user declined to change the password.

The web page runs inside the show process.
It is down while that process is failed or stopped.
The Wi-Fi and SSH rescue paths remain separate.
The current design does not detect every hung process.
It cannot guarantee physical water off after power or DMX loss.
