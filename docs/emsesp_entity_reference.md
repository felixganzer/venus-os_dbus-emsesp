# EMS-ESP Entity Reference

This repository treats the entity names published on the official EMS-ESP reference at https://emsesp.org/de/All-Entities as the canonical source of truth.

The runtime mapper in [config/config.json](../config/config.json) uses those names as lookup candidates, while [dbus_emsesp/model.py](../dbus_emsesp/model.py) normalizes and resolves them into the internal heat-pump state model.

## Core entity groups

The most relevant groups for this bridge are:

- `boiler.*`
- `heatpump.*`
- `thermostat.*`
- `boiler.dhw.*`

## Important examples

- `boiler.outdoortemp` / `heatpump.outdoortemp`
- `boiler.curflowtemp` / `heatpump.curflowtemp`
- `boiler.rettemp` / `heatpump.rettemp`
- `boiler.dhw.curtemp` / `boiler.dhw.curtemp2`
- `boiler.hpactivity` / `heatpump.hpactivity`
- `boiler.heatingactive`
- `boiler.tapwateractive`
- `boiler.hpcompon` / `heatpump.hpcompon`
- `boiler.hpcurrpower` / `heatpump.hpcurrpower`
- `boiler.hppower` / `heatpump.hppower`
- `boiler.auxheaterpower`
- `boiler.uptimetotal`

## Project rule

If a value is not available in the current device payload, the app should keep trying the alternate official entity candidates in order until one resolves successfully. This keeps compatibility with firmware variants and different boiler families.

The relevant project mapping is:

- [config/config.json](../config/config.json)
- [dbus_emsesp/model.py](../dbus_emsesp/model.py)
