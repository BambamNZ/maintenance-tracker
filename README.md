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

🚧 Scaffold, not yet tested against real hardware. See
[Testing checklist](#testing-checklist) below before relying on this.

## How it works

Each maintenance schedule (e.g. "P2S Nozzle Clean", "A1 Mini AMS Lube")
is set up as its own config entry, the same pattern HA's built-in
Threshold and Utility Meter helpers use. One printer can have several
independent schedules pointed at the same source sensor.

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

## Testing checklist

- [ ] Confirm `hours_since_service` tracks correctly against a real
      `ha-bambulab` `total_usage` sensor across several print cycles.
- [ ] Confirm `service_due` flips `on` at the configured threshold and
      stays `on` until reset.
- [ ] Confirm the reset button re-baselines correctly and dismisses the
      notification.
- [ ] Confirm behaviour when the source sensor is `unavailable` (printer
      offline) - derived sensors should also go `unavailable`, not freeze
      at a stale value.
- [ ] Confirm a HA restart doesn't lose the baseline (storage survives
      restart).
- [ ] Lint clean with `ruff format .` / `ruff check .`.

## AI assistance

Scaffolded with Claude (Anthropic) - design discussion and initial
implementation. Not yet reviewed or verified against physical hardware.
