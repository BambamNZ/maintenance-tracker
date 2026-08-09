# Maintenance Tracker

A generic Home Assistant custom integration for usage-based maintenance
reminders. It wraps *any* cumulative usage sensor (e.g. `ha-bambulab`'s
`sensor.<model>_<serial>_total_usage`) and tracks hours and/or days
elapsed since the item was last serviced, with a reset button and a
binary sensor other automations/notifications can trigger from.

This isn't Bambu-specific - point it at any monotonically-increasing
numeric sensor and it works the same way (pump run-hours, filter
uptime, whatever else drifts toward "needs attention").

## Status

[![Validate](https://github.com/BambamNZ/maintenance-tracker/actions/workflows/validate.yml/badge.svg)](https://github.com/BambamNZ/maintenance-tracker/actions/workflows/validate.yml)
[![Lint](https://github.com/BambamNZ/maintenance-tracker/actions/workflows/lint.yml/badge.svg)](https://github.com/BambamNZ/maintenance-tracker/actions/workflows/lint.yml)
[![Dependabot Updates](https://github.com/BambamNZ/maintenance-tracker/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/BambamNZ/maintenance-tracker/actions/workflows/dependabot/dependabot-updates)
## How it works

Each maintenance schedule (e.g. "P2S Nozzle Clean", "A1 Mini AMS Lube")
is set up as its own config entry, the same pattern HA's built-in
Threshold and Utility Meter helpers use. One printer can have several
independent schedules pointed at the same source sensor.

<img width="290" height="415" alt="182 - 08-08-2026 18_59_50 - chrome" src="https://github.com/user-attachments/assets/31f1284e-1718-4688-aba2-b3712e407fd0" />


### Entities per schedule

| Entity | Purpose |
|---|---|
| `sensor.<name>_hours_since_service` | Source sensor's current value minus the baseline set at last reset |
| `sensor.<name>_days_since_service` | Days elapsed since the last reset |
| `binary_sensor.<name>_service_due` | `on` when the configured threshold(s) are crossed - **use this as the trigger for your own automations/3rd-party notifications** |
| `button.<name>_reset_service` | Press after servicing - re-baselines hours, resets the days clock, dismisses any open notification |

### Persistent notifications

If enabled for a schedule, a `persistent_notification` is raised the
moment `service_due` flips to `on`, and dismissed automatically when you
press that schedule's reset button. It won't re-fire repeatedly while
still overdue - only on the off→on transition.

### Setup

1. Install via HACS (add this repo as a custom repository) or copy
   `custom_components/maintenance_tracker` into your HA config.
2. Restart Home Assistant.
3. Settings → Devices & Services → Add Integration → **Maintenance
   Tracker**.
4. Name the schedule, pick the source usage sensor, and set an hours
   and/or days threshold.

Thresholds, notify-on-due, and AND/OR logic can be changed later via the
integration's **Configure** option without recreating the schedule.

## AI assistance

Scaffolded with Claude (Anthropic) - design discussion and initial
implementation. Reviewed and tested by @BambamNZ 
