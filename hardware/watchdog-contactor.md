# Watchdog contactor

Status: design only.

No part is ordered.

No wire is installed.

No fault test has run.

## Requirement

The HB-Laser supply is 24 VDC at 21 A.

The modules hold their last water height when DMX stops.

The hardware stop must remove 24 V when the show heartbeat stops.

## Selected parts

Use a Siemens `3UG5651-1CW30` pulse monitoring relay.

Use a Siemens `3RT2026-1BB40` contactor with a 24 VDC coil.

Use one channel of a BDMICRO `OPTO-4` between the Pi and the 24 V watchdog input.

Siemens rates one contactor main path for 35 A at 24 VDC under DC-1.

The 21 A supply rating is 14 A below this limit.

## Power wiring

Mount all parts in a closed DIN rail panel.

Put the watchdog power before the contactor.

Put the contactor in the positive 24 V module feed.

Use the three normally open main poles in series.

Wire the path in this order:

```text
24 V supply positive
  -> branch fuse
  -> contactor pole 1
  -> contactor pole 2
  -> contactor pole 3
  -> HB-Laser module positive

24 V supply negative
  -> HB-Laser module negative
```

Use 10 ft of two-conductor 14 AWG copper cable for the module feed.

Use an Eaton Bussmann `LP-CC-10` 10 A time-delay fuse.

Mount the fuse in an Eaton Bussmann `CHCC1DU` DIN rail holder.

The two modules can draw 6.4 A in total.

Do not use 18 AWG for the final two-module feed.

A 10 ft run has a 20 ft power loop.

At 6.4 A, a 20 ft loop of the checked 18 AWG cable loses about 0.85 V at 25 C.

This loss is about 3.6 percent of 24 V.

A panel electrician must confirm the cable method and local code before the build.

## Control wiring

Power the watchdog from the unswitched 24 V supply.

Set the watchdog to closed-circuit operation.

Use its normally open output to feed the contactor coil.

Wire the coil return to the unswitched 24 V negative.

Set one `OPTO-4` channel for 3.3 V input and 24 V output.

Connect Pi GPIO17, header pin 11, to the isolated input.

Connect the isolated 24 V output to the watchdog pulse input.

The Pi reported GPIO17 as unused on 2026-09-19.

The exact watchdog terminals and settings must come from the delivered part manual.

## Heartbeat rule

The show must toggle the GPIO only after a successful DMX send.

The current DMX resend time is 0.5 seconds.

Use a watchdog loss time longer than one missed send and shorter than a harmful water hold.

The first bench setting is 1.5 seconds.

This setting is not verified.

Start the show with the watchdog output enabled:

```sh
ssh pi@water-jets "cd ~ && ~/wj-venv/bin/python -m tracker.run show --baseline ~/data/baseline.json --watchdog-gpio 17"
```

Do not use this option before the isolated input is wired.

## Fault test

Use a low water value.

Keep the manual 24 V switch in reach.

Run these tests one at a time:

1. Stop the tracker process.
2. Stop the Pi.
3. Stop OLA.
4. Disconnect the Enttec.
5. Disconnect the heartbeat wire.

For each test, measure the time until 24 V leaves the module feed.

Each test passes only if the contactor opens without a DMX zero command.

Idle water stays off until all five tests pass.

## Sources

- [Eaton LP-CC-10 product page](https://www.eaton.com/us/en-us/skuPage.LP-CC-10.html)
- [Eaton CHCC1DU product page](https://www.eaton.com/us/en-us/skuPage.CHCC1DU.html)
- [LAPP 601402 cable listing](https://www.digikey.ca/en/products/detail/lapp/601402/18879339)
- [Southwire 18 AWG cable data](https://www.southwire.com/wire-cable/low-voltage-cable/multi-conductor-cl3r-fplr-cmr-cmg-non-shielded/p/R40048-1A)

- [Siemens watchdog data](https://mall.industry.siemens.com/mall/ww/en/Catalog/Product/?mlfb=3UG5651-1CW30)
- [Siemens contactor data](https://mall.industry.siemens.com/goos/catalog/Pages/mmpdata.ashx?MLFB1=3RT2026-4AR60&MLFB2=3RT2026-1AR60&lang=en)
- [BDMICRO OPTO-4 data](https://bdmicro.com/products/opto-4)
- [Bank of Canada exchange rate](https://www.bankofcanada.ca/rates/exchange/daily-exchange-rates-lookup/?dF=2026-09-12&dT=2026-09-19&lP=lookup_daily_exchange_rates_2017.php&se=FXEURCAD-FXUSDCAD)
