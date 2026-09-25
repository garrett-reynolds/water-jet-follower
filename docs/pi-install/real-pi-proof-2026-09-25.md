# Real Pi boot and recovery proof

Date: 2026-09-25. All times below are UTC.
Scope: the automated checks and the later user-observed offline boot check for [issue 46](https://github.com/garrett-reynolds/water-jet-follower/issues/46).
Issue 46 remains open.

The user confirmed that the 24 V module power switch was off.
No test enabled live water.
Tests used strict wired SSH to `pi@10.0.10.204`, with `HostKeyAlias=water-jets`.
No Wi-Fi secret was read or printed.
No Ethernet setting changed.

## Results

| Test | Result |
|---|---|
| One show-process crash | Pass. The service replaced the killed process after its configured restart delay. |
| OLA unavailable | Pass. Three show starts refused to run when the initial zero check could not connect to OLA. |
| Five starts in five minutes | Pass for the observed limit. The sixth start was blocked. The expected literal `Result=start-limit-hit` check failed: this Pi kept `Result=signal`. |
| Manual recovery | Pass. One `reset-failed` and one manual start restored the show with Lights only and verified zero. |
| Private Wi-Fi restart | Pass for Pi-side services. AP address, DHCP and DNS returned. Wired SSH, OLA and show stayed up. No client access test ran. |
| Normal reboot | Pass. A new boot ID, safe show start, AP, DHCP, DNS, LiDAR and port 8080 were observed. One OLA readiness failure recovered through the normal retry. |
| Cold power boot and isolated iPad use | Pass. The user shut the Pi down, removed Ethernet, removed and restored Pi power, joined `water-jets` from the iPad, and opened `http://10.42.0.1:8080/`. |

These checks prove software state, OLA readback and offline page access from the iPad after a cold power boot.
They do not prove physical water off.

## Before the tests

At `15:46:21`, the boot ID was `04291380-ad09-4112-bc62-094779f83c42`.
Uptime was 1 hour 45 minutes (`6324.69` seconds in the API).

| Item | State |
|---|---|
| Show | `active/running`, PID `3171`, owner `pi`, `Result=success`, `NRestarts=1` |
| Start command | `/home/pi/wj-venv/bin/python -u -m tracker.run show --baseline /home/pi/data/baseline.json --profile /home/pi/data/profile.json --lights-only` |
| Restart limits | `RestartUSec=5s`, `StartLimitIntervalUSec=5min`, `StartLimitBurst=5` |
| OLA | Active/running, process PID `3147`, generated SysV unit, enabled, not masked |
| Lock cleanup | Active/exited, result success |
| Private Wi-Fi | `water-jets-ap` on `wlan0`, `10.42.0.1/24` |
| Wired rescue | `netplan-eth0` on `eth0`, `10.0.10.204/24` |
| LiDAR | `/dev/ttyLIDAR -> ttyUSB1`; API `lidar_ok=true`, `scan_hz=16.52` |
| Enttec | `/dev/ttyENTTEC -> ttyUSB0` |
| API | `/system-data` returned `lights_only=true`, `test_mode=false`, `olad_active=true` |
| Listening ports | Web `8080`, SSH `22`, DNS TCP/UDP `10.42.0.1:53`, DHCP UDP `67` |

The show journal held its `LIGHTS ONLY` and `ALL ZERO` lines for PID 3171.
The tests also ran the existing `tracker.run zero` command before each fault.
Each pre-fault command returned `zero: sent=True slots_held=512 ALL ZERO`.
The API reported `lights_only=true` before each fault.

## Show-process crash

At `15:46:49`, fresh zero proof passed.
The main PID check and process-owner check identified PID `3171` as the `pi` show process.
Only this PID received `SIGKILL`.
The unit entered `activating/auto-restart`, with `MainPID=0` and `Result=signal`.

At `15:46:55`, systemd started PID `3720`.
This is six seconds at the journal's whole-second precision.
The configured delay remained five seconds.
The first LiDAR open had a sync-byte error.
Its built-in retry connected successfully.
At `15:46:56`, the new process logged `LIGHTS ONLY` and `ALL ZERO`.
The API returned `lights_only=true`.
At `15:47:13`, LiDAR scans had returned to `16.53` Hz.

## OLA fault and the start limit

The show unit wants OLA.
Stopping OLA alone would let a new show start bring it back.
The controller approved a temporary runtime mask for this test.
The prior OLA state was active, enabled, generated and unmasked.
`/run/systemd/system/olad.service` was absent.

The test used `sudo -n systemctl mask --runtime olad.service`.
It checked that the exact new link was `/run/systemd/system/olad.service -> /dev/null`.
It then stopped OLA and killed only the current checked show PID.
An exit trap removed that exact runtime mask and started OLA.
No disk unit file changed.
The cost of a failed cleanup would be OLA remaining down until the mask was removed or the Pi rebooted.
The 24 V power stayed off.

At `15:47:58`, fresh zero proof and Lights only passed before the first OLA fault.
PID `3720` exited after `SIGKILL` at `15:48:03`.
The next three starts had Lights only on.
Each failed in the initial zero check with `OLADNotRunningException: Failed to connect to olad`.
Their exit logs said `ZERO FAILED (atexit)` because OLA was deliberately unavailable.
No successful zero proof is claimed during this fault.

The first observation script waited only 32 seconds.
That was too short for all remaining starts.
Its expected-result check failed at `15:48:30`.
The exit trap restored OLA.
The next normal retry, PID `4085`, passed `ALL ZERO` at `15:48:35`.
No manual reset ran at this point.

All five starts in the same five-minute window were visible in the journal:

| Start time | PID | Result |
|---|---|---|
| `15:46:55` | `3720` | Safe start, then controlled kill |
| `15:48:09` | `3958` | OLA zero check failed at `15:48:14` |
| `15:48:19` | `3963` | OLA zero check failed at `15:48:22` |
| `15:48:27` | `3968` | OLA zero check failed at `15:48:30` |
| `15:48:35` | `4085` | Safe start after the trap restored OLA |

At `15:49:17`, fresh zero proof and Lights only passed for PID `4085`.
The test held OLA down again with the same runtime-only mask and exit trap.
PID `4085` received `SIGKILL` and exited at `15:49:23`.
At `15:49:28`, the journal said `Start request repeated too quickly.`
It did not start a sixth process.

The checked state at `15:49:38` was `ActiveState=failed`, `SubState=failed`, `MainPID=0`, `NRestarts=7`, `Result=signal`.
`NRestarts` includes earlier restarts; it is not the five-minute start count.
The literal `Result=start-limit-hit` assertion did not pass.
The journal and the five start times are the evidence for the rate limit.
The test did not wait five minutes to prove the failed state persists after the limit window ends.

The exit trap removed the runtime mask and restored OLA.
The show stayed failed until manual recovery.
During the failed show state, `water-jets-ap`, `10.42.0.1/24`, wired `10.0.10.204/24`, NetworkManager and SSH stayed active.
This did not test SSH from a private Wi-Fi client.

## Manual recovery

At `15:49:59`, OLA was active and the runtime mask was absent.
The show was still failed with PID zero.
Exactly one manual `sudo -n systemctl reset-failed water-jet-show.service` ran.
Exactly one manual `sudo -n systemctl start water-jet-show.service` followed it.

At `15:50:01`, PID `4542` logged `LIGHTS ONLY` and `ALL ZERO` after one LiDAR open retry.
At `15:50:10`, the unit was active/running with `Result=success` and `NRestarts=0`.
The API reported `lights_only=true`, `lidar_ok=true`, `scan_hz=16.34`, and `olad_active=true`.

## Private-network restart

At `15:50:28`, fresh zero proof and Lights only passed.
The test ran `sudo -n nmcli connection down water-jets-ap`.
At `15:50:29`, the Wi-Fi IPv4 address was absent.
Wired SSH still worked at `10.0.10.204/24`.
Show, OLA and SSH were active.

The test then ran `sudo -n nmcli connection up water-jets-ap`.
At `15:50:32`, the profile and `10.42.0.1/24` were back.
`dnsmasq` PID `4645` served `10.42.0.1` with lease range `10.42.0.10` through `10.42.0.254`.
UDP port 67 and TCP/UDP port 53 were listening.
Show PID `4542` stayed the same, with `NRestarts=0`.
No old infrastructure Wi-Fi profile was activated by the test.

The final curl in the piped test command failed with a malformed URL from the command transport.
A fresh direct SSH curl passed at `15:50:43`.
It returned both network addresses, Lights only, OLA active and LiDAR at `16.62` Hz.
No DHCP lease, DNS query or web page was tested from an external client.

## Normal reboot

At `15:50:43`, fresh zero proof and Lights only passed.
The test ran `sudo -n systemctl reboot`.
One wired SSH attempt timed out during the reboot.
Strict wired SSH returned at `15:51:01`.
The new boot ID was `c205f2d3-8dda-44bd-8ef7-2c0dc76026fb`.

The new boot journal showed:

| Time | Evidence |
|---|---|
| `15:50:49` | Lock cleanup started and finished successfully. |
| `15:50:56` | Show PID `1153` started. |
| `15:50:57` | Lights only was on. Initial zero check returned OLA `NO DATA`. The show refused to run. Its exit zero check passed. |
| `15:51:02` | Normal failure retry started PID `1223`. |
| `15:51:03` | Lights only was on. `zero: sent=True slots_held=512 ALL ZERO`. Viewer opened. |

This is an observed OLA readiness race.
The normal retry recovered it without a manual command.
No claim is made that the first start always succeeds.

At `15:51:14`, the checked final state was:

| Item | Final state |
|---|---|
| Show | Active/running, PID `1223`, `Result=success`, `NRestarts=1`, enabled |
| Safe flag | API `lights_only=true`, `test_mode=false` |
| OLA | Active/running, result success, enabled, no runtime mask |
| Lock cleanup | Active/exited, result success |
| Network | `water-jets-ap`, `10.42.0.1/24`; `netplan-eth0`, `10.0.10.204/24` |
| DNS and DHCP | TCP/UDP `10.42.0.1:53`, UDP port `67` listening |
| Page | Port `8080` listening; `/system-data` returned valid JSON |
| LiDAR | `/dev/ttyLIDAR -> ttyUSB1`; `lidar_ok=true`, `scan_hz=16.29` |
| Enttec | `/dev/ttyENTTEC -> ttyUSB0` |
| Rescue | NetworkManager, SSH and Avahi enabled |

The final `sudo -n true` returned `sudo: a password is required` after reboot.
The task stopped further Pi tests under its root-access stop rule.
The show, OLA and private Wi-Fi were already restored.
No test fault or runtime mask remained.

## User-observed cold power boot and isolated iPad use

After the automated checks, the user followed the final offline test steps.
The user kept the 24 V module power switch off.
The user shut the Pi down cleanly.
The user unplugged Ethernet.
The user removed and restored Pi power.
The user joined the `water-jets` network from the iPad with the private local Wi-Fi record.
The iPad used the private network without the site network.
The successful join and page access prove a usable private IP path.
The user opened `http://10.42.0.1:8080/` and reported, "that works great".

This proves a user-observed cold power boot, isolated iPad access and page service without Ethernet.
It does not prove the Lights only UI state, physical water-off state, output-channel state, private Wi-Fi SSH, mDNS, LiDAR reconnect, local-console rescue, rollback or password rotation.

## Final hardening update and recovery proof

Commit `9bd986a` was installed on the real Pi with 24 V module power kept off.
The prior app file and affected Wi-Fi values are in root-only folder
`/root/water-jet-before-update-20260925TTsCx0f`.

The old site Wi-Fi profile now has autoconnect off.
The private AP now has unlimited retries.
NetworkManager released and retook `wlan0` during a controlled fault.
The AP returned by itself as `water-jets-ap` at `10.42.0.1/24`.
Ethernet stayed at `10.0.10.204/24`.

The real LiDAR serial driver was unbound and rebound.
Before loss, OLA held a jet-height test value of `5`.
During loss, the API reported LiDAR unavailable and Lights only on.
OLA read back all 512 slots at zero.
After reconnect, tracking returned, the held test was clear, and Lights only stayed on.
A fresh operator action could command the test again.
The final stop read back all 512 slots at zero.

A normal reboot then passed.
The installed source hash stayed correct.
The AP and Ethernet returned.
The show recovered through its normal OLA readiness retry.
The final API state was `lights_only=true`, `test_mode=false`, `lidar_ok=true`,
LiDAR `16.72` Hz, and OLA active.
Fresh zero proof again read back all 512 slots at zero.

## User-observed private access and physical LiDAR cable proof

The user kept the 24 V module power switch off for these checks.
A laptop joined the private `water-jets` network.
`ssh pi@10.42.0.1` connected successfully.
The Pi returned `water-jets` from `hostname`.
After that session ended, `ssh pi@water-jets.local` also connected successfully.

The user then pulled the physical LiDAR USB cable from the powered USB hub.
The control page reported that LiDAR was not available.
At `13:18:58 EDT`, `/system-data` reported show PID `1205`, `lights_only=true`,
`test_mode=false`, `lidar_ok=false`, `scan_hz=0.0`, and `olad_active=true`.

The user reconnected the same cable and waited for recovery.
At `13:22:42 EDT`, `/system-data` reported the same show PID `1205`,
`lights_only=true`, `test_mode=false`, `lidar_ok=true`, `scan_hz=13.4`, and
`olad_active=true`.

This proves private-Wi-Fi SSH by address, mDNS SSH by `water-jets.local`, and physical
LiDAR cable loss and return without a show-process restart.
Lights only stayed on through the physical reconnect.
This does not prove physical water off because the 24 V module power was off.

## Open proof and recorded exceptions

- Perform a real cold power boot with the full rig and check physical water-off after faults.
  The jets are packed, so this work is blocked until the next full setup.
- Test the documented rollback path.
- Local-console rescue through micro-HDMI and a USB keyboard was not tested.
  The user chose to skip it because the installed Pi is intended to run headless.
- Password rotation was not tested.
  The user declined to change the password.

Do not call the full rig install-ready until those required checks are settled.
