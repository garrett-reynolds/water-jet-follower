# Pi service and recovery design

Date: 2026-09-25. Decision: [issue 43](https://github.com/garrett-reynolds/water-jet-follower/issues/43).
The design is installed on the Pi. The final hardening update was checked on the real Pi.
Use the [checked Pi state](current-state-2026-09-25.md) and the [source note](../research/2026-09-25-pi-offline-wifi-systemd.md).

## Owners and start order

NetworkManager owns the private Wi-Fi connection profile.
The show service does not create, stop, or restart that profile.
Wi-Fi stays available if the show fails.
The AP uses unlimited autoconnect retries (`0`).
The installer saves and then disables competing `wlan0` Wi-Fi autoconnect states.
The installed Pi has these values. AP recovery passed after NetworkManager released and retook `wlan0`.
The private network address and passphrase belong to Tasks 3 and 4.

The boot order is lock cleanup, then OLA, then the show.
NetworkManager also starts before the show.
The show has `Wants=NetworkManager.service olad.service`.
It has `After=NetworkManager.service olad.service network.target`.
`Wants=` asks for a start.
`After=` sets the order.
Neither proves that DMX works.
The app must pass its existing full zero-frame send and readback check.
[Unit rules](https://manpages.debian.org/trixie/systemd/systemd.unit.5.en.html).

Do not add `network-online.target` to the show unit.
The viewer binds to `0.0.0.0:8080`.
It can start before a client joins.
Network loss alone does not cause a show restart.
[Network start rules](https://systemd.io/NETWORK_ONLINE/).

## One show service

Use `/etc/systemd/system/water-jet-show.service`.
Use these fields when the install task builds the unit:

```ini
[Unit]
Wants=NetworkManager.service olad.service
After=NetworkManager.service olad.service network.target
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
Type=exec
User=pi
WorkingDirectory=/home/pi
ExecStart=/home/pi/wj-venv/bin/python -u -m tracker.run show --baseline /home/pi/data/baseline.json --profile /home/pi/data/profile.json --lights-only
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

The `-u` option sends Python output without a buffer delay.
Do not run a second show with `nohup`, a login script, or a user service.
Check other boot paths before enabling this unit.

Every boot, manual service start, and automatic restart uses `--lights-only`.
This keeps every fountain-height channel at zero.
The saved profile cannot turn this start flag off.
An operator must turn Lights only off in the control page to allow live water.
The app checks a full zero frame before the show loop starts.
Its exit path tries zero again.
These paths already exist in [run.py](../../tracker/run.py) and [dmx.py](../../tracker/dmx.py).
Do not add an untested stop helper or hide a failed zero check.

`Restart=on-failure` restarts a failed process after five seconds.
A clean exit or a requested stop does not cause a restart.
Five start attempts are allowed in five minutes, including the first start.
A further start in that window fails with `start-limit-hit`.
No timer restarts the service when the window expires.
Leave it failed until a person fixes the cause and resets it.
The failed state stops show output attempts.
It must not restore live water by itself.
[Service rules](https://manpages.debian.org/trixie/systemd/systemd.service.5.en.html), [start limits](https://manpages.debian.org/trixie/systemd/systemd.unit.5.en.html).

The five-minute limit is a rate limit.
Faults spaced outside that window can cause more than five starts in total.
Each of those starts still forces Lights only on.

## Stale OLA locks

Use a separate root oneshot service named `water-jet-ola-lock-cleanup.service`.
Its file is `/etc/systemd/system/water-jet-ola-lock-cleanup.service`.
Use `Type=oneshot`, `User=root`, and `RemainAfterExit=yes`.
Use `Before=olad.service`.
Keep its output and errors in the journal.

Use `/etc/systemd/system/olad.service.d/water-jet-lock-cleanup.conf`.
This drop-in adds `Requires=water-jet-ola-lock-cleanup.service`.
It also adds `After=water-jet-ola-lock-cleanup.service`.
Do not edit the generated SysV unit or replace OLA's start command.

Run cleanup once during boot, before OLA can own a lock.
The oneshot remains active after success.
An OLA restart must not repeat cleanup while the Pi is running.
Do not attach cleanup to the show restart path.
For first installation, stop the show and OLA before starting cleanup.
The install task must refuse cleanup if OLA or another serial owner is running.

Only remove stale regular lock files directly under `/var/lock` with names that match `LCK..ttyUSB*`.
Do not follow a lock-file link or remove a directory.
Do not use recursive deletion or remove other lock names.
Do not remove a lock held by a live process.
No matches is a valid success.
A read, owner-check, or deletion error must fail the unit.
Do not use a leading `-` on its command or `|| true`.
The OLA dependency must expose a failed cleanup.
The show must still pass the app's zero check if OLA cannot start.
The install task must verify these rules on the real generated OLA unit.

## Logs and health

Use the system journal for output and errors.
Keep the Pi's existing journal retention policy for this install.
Do not add a `journald.conf` drop-in or a second show log file.
The system journal rotates logs under its size and free-space limits.
Persistent logs across boot are not promised until the install check proves them.
Save the fault log before reboot if the journal uses memory only.
[Journal storage rules](https://manpages.debian.org/trixie/systemd/journald.conf.5.en.html).

Run these read-only checks from PowerShell on Windows:

```powershell
ssh pi@10.42.0.1 'systemctl status water-jet-show.service olad.service water-jet-ola-lock-cleanup.service NetworkManager.service --no-pager --lines=20'
ssh pi@10.42.0.1 'systemctl show water-jet-show.service -p ActiveState -p SubState -p MainPID -p Result -p NRestarts -p ExecMainStatus -p Restart -p RestartUSec -p StartLimitIntervalUSec -p StartLimitBurst'
ssh pi@10.42.0.1 'systemctl cat water-jet-show.service water-jet-ola-lock-cleanup.service olad.service'
ssh -t pi@10.42.0.1 'sudo journalctl -b -u water-jet-show.service -u olad.service -u water-jet-ola-lock-cleanup.service --no-pager -n 200'
ssh -t pi@10.42.0.1 'sudo journalctl --disk-usage; sudo journalctl --list-boots; systemd-analyze cat-config systemd/journald.conf'
ssh pi@10.42.0.1 'curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8080/system-data'
```

Use process state and fresh `/system-data` responses as health evidence.
Check the control page for Lights only on after each new start.
Check the actual fountain-height channels in the real rig test.
An active process or HTTP reply alone does not prove water off.
The page lives inside the show process.
It will be unavailable while the show is stopped or failed.
Wi-Fi and SSH stay separate for recovery.

Do not set `WatchdogSec=` or `Type=notify`.
The app does not send systemd watchdog messages.
A hung process needs a person to detect and handle it with this design.

## Fault recovery and safety limit

Keep water power off while investigating an uncertain output state.
Read the status and journal first.
Fix the cause before these commands.
Run them from PowerShell on Windows:

```powershell
ssh -t pi@10.42.0.1 'sudo systemctl reset-failed water-jet-show.service'
ssh -t pi@10.42.0.1 'sudo systemctl start water-jet-show.service'
```

Run the health checks again.
Keep Lights only on until the operator permits water.
An OLA fault needs its own repair before the show can pass zero proof.
Do not reset the start limit in a loop.

The intended recovery state is water-off.
Software cannot prove physical water off after DMX, OLA, Enttec, or Pi power loss.
A jet may hold its last received value.
A killed or hung process can also prevent a zero send.
The external 24 V watchdog contactor is outside this plan.
This design does not replace that physical stop.

## Rollback rules

Before installation, save each existing target file and its owner and mode.
Record each target that did not exist.
Record each unit's enabled and active state.
Store the backup path in the install record.

| Proposed file | Rollback rule |
|---|---|
| `/etc/systemd/system/water-jet-show.service` | Stop and disable the new show unit first. Restore its prior file, or remove only this file if it was new. Restore its prior enabled state. Do not start live water. |
| `/etc/systemd/system/olad.service.d/water-jet-lock-cleanup.conf` | Stop OLA before changing its dependency. Restore this exact file, or remove it if new. Keep all other OLA drop-ins. |
| `/etc/systemd/system/water-jet-ola-lock-cleanup.service` | Remove the new OLA dependency first. Stop the completed oneshot. Restore its prior file, or remove only this file if new. Never run cleanup as a rollback action. |

After all file restores, run `sudo systemctl daemon-reload` on `pi@water-jets`.
Restore OLA's prior enabled and active state only after checking the device locks.
Do not restore stale lock files that cleanup removed.
Check OLA status and the journal for visible errors.
The recorded prior setup has no show service.
Return to that stopped show state if the new install is removed.
Keep the NetworkManager profile independent of this service rollback.
Tasks 3 and 4 must record its own backup and rollback steps.

## Proof still required

The install task must check unit syntax and the merged dependency order.
It must prove cold boot, app failure, five-start failure, and manual recovery.
It must prove the page works without the site network.
It must prove each restart has Lights only on.
It must test rollback with water power off.
The LiDAR was absent in the latest Pi check.
No hardware proof is claimed by this document.
