# Raspberry Pi install state — 2026-09-25

Read-only check of `pi@water-jets` at about 10:41 EDT. This records the installed state. It does not prove a cold boot, an offline access point, or safe water operation. No Pi setting or file was changed.

## Current state

| Area | Result |
|---|---|
| OS | `/etc/os-release` says Debian GNU/Linux 13 (trixie), full version 13.6. |
| Network | NetworkManager 1.52.1 is enabled and active. `eth0` uses `netplan-eth0` at `10.0.10.204/24`. `wlan0` uses `netplan-wlan0-wM` at `10.0.10.202/24`. Both connections have autoconnect `yes`. Wi-Fi mode is `infrastructure`. No access point connection is shown. |
| Names | Static host name is `water-jets`. On the Pi, `getent hosts water-jets` returns `127.0.1.1`; `getent hosts water-jets.local` returns `10.0.10.202`. On the Windows client, `Resolve-DnsName water-jets.local -Type A` returned `10.0.10.204`. Avahi is enabled and active. These results show local name resolution on the present site network; they do not prove resolution when offline. |
| App and data | App files exist at `/home/pi/tracker/`, including `run.py`, `viewer.py`, and `config.py`. Data is at `/home/pi/data/`. `baseline.json` and `profile.json` exist. The profile contents were not read. |
| Python | System and venv Python are 3.13.5. Venv path is `/home/pi/wj-venv`. `include-system-site-packages = true`. The venv has `pyrplidar` 0.1.2. `ola` and `ola-python` apt packages are both `0.10.9.nojsmin-7.1`. |
| OLA | `olad` is enabled and active through its generated SysV service. OLA sees the Enttec USB Pro. DMX1 output is patched to universe 1. `/etc/ola/ola-usbserial.conf` has `enabled = true` and `device_prefix = ttyENTTEC`. Other checked OLA plugin files have `enabled = false`. |
| USB rules and devices | `/etc/udev/rules.d/99-water-jets.rules` exists. Enttec rule matches its USB serial and makes `/dev/ttyENTTEC`, now linked to `ttyUSB0`. LiDAR rule makes `/dev/ttyLIDAR` from vendor and product IDs, with no serial match. `/dev/ttyLIDAR` was absent during this check. A live LiDAR check was therefore not possible. |
| Services and show | NetworkManager, `olad`, `ssh`, and `avahi-daemon` are enabled and active. The system and user unit lists contain no show or tracker service. No `tracker.run` process or listener on port 8080 was found. OLA listens on port 9090. The show does not start on boot in the current setup. |
| Start and log | No show start command is running now. `NEXT_STEPS.md` gives the last manual start command: `ssh pi@water-jets "cd ~ && setsid nohup ~/wj-venv/bin/python -m tracker.run show --baseline data/baseline.json > ~/show.log 2>&1 < /dev/null & disown"`. The log path is `/home/pi/show.log`; its last file update was 2026-09-21 11:35 EDT. This is a recorded command, not a command run for this check. |
| Space | Root and `/home/pi` share `/dev/mmcblk0p2`: 59G total, 4.2G used, 52G free (8% used). 3,622,827 inodes are free. |

## Mismatches and limits

- `README.md` Setup lists `pyrplidar` 0.10.9. The Pi has 0.1.2. The 0.10.9 number matches the installed OLA package version, not the installed `pyrplidar` version.
- `README.md` Setup says both USB rules match on serial number. The installed LiDAR rule matches only vendor and product IDs. The Enttec rule does match on serial.
- `README.md` wiring expects `/dev/ttyLIDAR`. That name is absent now. This can mean the LiDAR is unplugged; this read-only check did not test the hardware.
- `NEXT_STEPS.md` says the Pi was powered off at close on 2026-09-21. It is powered on and reachable now. Its other claim that no show starts after boot agrees with this check.
- The repo describes `http://water-jets:8080/` and `http://water-jets.local:8080/` while the show runs. Port 8080 is closed now because the show is stopped.

## Exact read-only checks

These commands ran from PowerShell in the repo worktree. They did not print Wi-Fi passwords, private keys, or profile contents.

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=8 pi@water-jets 'hostname; cat /etc/os-release; nmcli --version'
ssh -o BatchMode=yes pi@water-jets 'hostnamectl --static; hostname -f; getent hosts water-jets; getent hosts water-jets.local; nmcli -f DEVICE,TYPE,STATE,CONNECTION device status; nmcli -f NAME,TYPE,DEVICE,AUTOCONNECT connection show; ip -br link'
ssh -o BatchMode=yes pi@water-jets 'systemctl is-enabled NetworkManager olad ssh avahi-daemon 2>&1; systemctl is-active NetworkManager olad ssh avahi-daemon 2>&1; systemctl list-unit-files --state=enabled --no-pager; systemctl --user list-unit-files --state=enabled --no-pager'
ssh -o BatchMode=yes pi@water-jets 'pwd; ls -ld ~/tracker ~/data ~/wj-venv ~/show.log 2>&1; ls -1 ~/data 2>&1; df -h / /home/pi; df -i / /home/pi'
ssh -o BatchMode=yes pi@water-jets 'pgrep -af tracker.run; pgrep -af olad; ss -ltnp; systemctl status olad --no-pager --lines=3'
ssh -o BatchMode=yes pi@water-jets 'python3 --version; ~/wj-venv/bin/python --version; cat ~/wj-venv/pyvenv.cfg; ~/wj-venv/bin/python -m pip show pyrplidar; dpkg-query -W ola ola-python'
ssh -o BatchMode=yes pi@water-jets 'ls -l /etc/udev/rules.d/99-water-jets.rules /dev/ttyLIDAR /dev/ttyENTTEC 2>&1; cat /etc/udev/rules.d/99-water-jets.rules; readlink -f /dev/ttyLIDAR /dev/ttyENTTEC'
ssh -o BatchMode=yes pi@water-jets 'ola_dev_info'
ssh -o BatchMode=yes pi@water-jets 'grep -H -e ^enabled -e ^device_prefix /etc/ola/*.conf'
ssh -o BatchMode=yes pi@water-jets 'systemctl list-unit-files --all --no-pager'
ssh -o BatchMode=yes pi@water-jets 'date -Is; ls -l ~/tracker/run.py ~/tracker/viewer.py ~/tracker/config.py ~/data/profile.json ~/data/baseline.json; test -e /dev/ttyLIDAR; printf lidar_present_exit=%s\n $?; test -e /dev/ttyENTTEC; printf enttec_present_exit=%s\n $?'
ssh -o BatchMode=yes pi@water-jets '~/wj-venv/bin/python -m pip list --format=freeze'
ssh -o BatchMode=yes pi@water-jets 'systemctl is-enabled olad; systemctl is-active olad; systemctl list-units --type=service --all --no-pager'
ssh -o BatchMode=yes pi@water-jets 'ls -l ~/show.log; stat -c %y ~/show.log; ls -l ~/data/profile.json ~/data/baseline.json; ls -l /var/lock/LCK..ttyUSB* 2>&1'
Resolve-DnsName water-jets.local -Type A
```

Repo checks: `rg -n -i -m 3 'water-jets|networkmanager|ola|udev|profile.json|systemd|8080|venv|log' README.md docs CONTEXT.md DECISIONS.md`, `rg -n -C 2 'setsid nohup|show.log|current start|show --baseline' NEXT_STEPS.md README.md`, and direct reads of `README.md`, `tracker/README.md`, `data/README.md`, `docs/BUILD_SPEC.md`, and `NEXT_STEPS.md`.

Some initial grouped SSH commands failed because PowerShell stripped nested quotes in remote Python and grep text. The later checks above gave the needed results. A `readlink -f` on the absent LiDAR path printed that path even though `ls` and `test -e` showed no device; this document uses the `ls` and `test` result. The Wi-Fi check that also tried to grep unit names failed on shell pipe parsing; its successful `nmcli` mode and `ip` output were confirmed by separate unit-list checks.
