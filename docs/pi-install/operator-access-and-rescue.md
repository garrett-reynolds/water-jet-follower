# Operator access and rescue

Date: 2026-09-25.
Decision: [issue 44](https://github.com/garrett-reynolds/water-jet-follower/issues/44).
The private Wi-Fi and Windows password record are installed.
The password stays outside this repo.

## Fixed access choices

| Item | Choice |
|---|---|
| NetworkManager connection profile name | `water-jets-ap` |
| Wi-Fi network name | `water-jets` |
| Wi-Fi security | WPA2 Personal with a strong passphrase |
| Fixed Pi address on the private Wi-Fi | `10.42.0.1/24` |
| Primary control URL | `http://10.42.0.1:8080/` |
| Primary SSH command on the private Wi-Fi | `ssh pi@10.42.0.1` |
| Friendly URL | `http://water-jets.local:8080/` |

NetworkManager owns the Wi-Fi profile.
The AP uses `connection.autoconnect-retries=0` for unlimited start retries.
Before changing any NetworkManager target, the installer saves each competing
`wlan0` Wi-Fi profile's autoconnect state by UUID in the root-only backup.
Unbound Wi-Fi profiles also count because they can claim `wlan0`.
The installer then disables their autoconnect setting.
It leaves profiles bound to other interfaces and Ethernet unchanged.
Priority alone does not stop an old Wi-Fi profile from taking the radio after AP failure.
The real Pi now has these final-review changes.
The AP returned by itself after NetworkManager released and retook `wlan0`.
The show service must not control that profile.
Use the fixed URL first.
Use the friendly URL only as a secondary address after the real iPad proves offline mDNS name resolution.
mDNS lets a device find a local name without a site name server.
The site-network name checks do not prove this offline path.

Keep the current Ethernet connection unchanged.
Its profile is `netplan-eth0`.
Use it for SSH rescue when a known LAN is present.
LAN means the local wired network.
The checked Ethernet address was `10.0.10.204/24`.
That address is not a fixed promise for another LAN.

## Private passphrase record

Task 4 will generate a 16-character random passphrase.
Use an unambiguous upper-case, lower-case, and digit alphabet.
The passphrase must contain all three character types.
Use a secure random source.
Do not make or place a real secret in this design.

Save the passphrase only at `C:\Users\garrett.reynolds\.water-jets\wifi-passphrase.txt` on the Windows laptop and in NetworkManager's root-owned connection file on the Pi.
Restrict the Windows directory and file to Garrett's Windows account and `SYSTEM`.
Task 4 must check both sets of access rights.
The Pi connection file must allow access only to root.
Task 4 must record its exact path without showing its secret.

The private file must include the network name, passphrase, primary URL, and SSH command.
This gives the operator one local record.
Do not store the secret in GitHub, the repo, SDD files, commands printed to chat, or logs.
SDD files are the local task work files.
Do not use `nmcli --show-secrets` in shared checks.
Do not print or copy the private file into a report.

## iPad access

1. Join `water-jets` on the iPad.
2. Use the passphrase from the private local record.
3. Open `http://10.42.0.1:8080/`.
4. Check that Lights only is on after each show start.

If the iPad shows No Internet, check that it is still joined to `water-jets`.
Then open the fixed local URL.
This notice does not mean the Pi page is down.
The private network does not need internet access.
The page runs inside the show process.
The page will be down if that process stops or fails.
Wi-Fi and SSH remain separate rescue paths.

## SSH and physical rescue

Run this from PowerShell on the Windows laptop while joined to `water-jets`:

```powershell
ssh pi@10.42.0.1
```

For Ethernet rescue on the checked site LAN, run this from PowerShell:

```powershell
ssh pi@10.0.10.204
```

On another LAN, obtain the Pi's actual wired address from the local console or the LAN address list.
Do not change the Ethernet profile to make it match the old address.

With no working network, connect a local micro-HDMI display and USB keyboard to the Pi.
Log in locally as `pi`.
Keep these items available at the install.
Keep the local login details available to the operator.

Run these read-only checks in the Pi's Bash shell.
They also work after an SSH login.
They do not depend on the current directory.

```bash
systemctl status water-jet-show.service olad.service water-jet-ola-lock-cleanup.service NetworkManager.service ssh.service avahi-daemon.service --no-pager --lines=20
systemctl show water-jet-show.service -p ActiveState -p SubState -p Result -p NRestarts -p ExecMainStatus
sudo journalctl -b -u water-jet-show.service -u olad.service -u water-jet-ola-lock-cleanup.service --no-pager -n 200
nmcli -f DEVICE,TYPE,STATE,CONNECTION device status
nmcli -f NAME,TYPE,DEVICE,AUTOCONNECT connection show
nmcli -f connection.id,connection.autoconnect,802-11-wireless.ssid,802-11-wireless.mode,802-11-wireless-security.key-mgmt,802-11-wireless-security.proto,ipv4.method,ipv4.addresses connection show water-jets-ap
ip -4 -br addr
ss -ltn
curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8080/system-data
```

Check for `water-jets-ap` on the Wi-Fi device.
Check for `10.42.0.1/24` on that device.
Check for port 8080 and a fresh `/system-data` reply.
A missing profile or service is an install fault after Task 4.
These files do not exist yet in the checked pre-install state.
Keep error output visible.
Do not print NetworkManager's connection file.

After the cause of a Wi-Fi fault is fixed, use this at the local Pi console:

```bash
sudo nmcli connection up water-jets-ap
```

Run the network checks again.
Join the iPad again.
Check the primary page and SSH access again.
Use the [service and recovery design](service-and-recovery-design.md) for a show or OLA fault.
Do not reset the show start limit in a loop.

## Passphrase rotation

Task 4 must provide a secret-safe rotation method.
Secret-safe means that commands and logs do not show the passphrase.
Keep the current private record until the new access checks pass.
Use the same private path and access limits on the Windows laptop.
Keep any temporary old record only in that protected directory.
Remove it only after proof.

1. Generate a new private file with a new passphrase under the same rules.
2. Apply the new secret to NetworkManager without printing it.
3. Reconnect the iPad with the new passphrase.
4. Prove access to `http://10.42.0.1:8080/`.
5. Prove `ssh pi@10.42.0.1` from the Windows laptop on `water-jets`.
6. Remove the old private record only after both checks pass.

Keep Ethernet or the local console available during rotation.
If a check fails, keep the old record for recovery.
Do not remove the old record on a failed check.
Do not keep secret copies in the repo or a task report.

## Stop and proof limits

The 24 V power switch remains the physical water stop.
Network rescue is not a water stop.
Keep water power off while the output state is uncertain.
A page reply or SSH login does not prove water is off.

Task 4 must save the prior network settings in a protected backup before changes.
It must record exact restore steps without copying secrets into the repo.
It must keep Ethernet unchanged.
It must prove iPad page access with no site network or internet.
It must prove SSH access on the private Wi-Fi.
It must prove the local console rescue path.
It must check the private file access rights.
No live access, rotation, or hardware proof is claimed here.
