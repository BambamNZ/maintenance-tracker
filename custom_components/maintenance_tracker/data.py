# Maintenance Tracker for Home Assistant
#
# Copyright (c) 2026 David Venter (github.com/BambamNZ/maintenance-tracker)
#
# SPDX-License-Identifier: MIT

"""Runtime manager for a single maintenance schedule.

No DataUpdateCoordinator here deliberately - this integration has nothing
to poll. It reacts to state changes on the source usage sensor via
async_track_state_change_event, so derived entities update the instant
the source ticks over rather than on a fixed interval.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    CONF_LOGIC,
    CONF_NOTIFY,
    CONF_SOURCE_SENSOR,
    CONF_THRESHOLD_DAYS,
    CONF_THRESHOLD_HOURS,
    DEFAULT_LOGIC,
    LOGGER,
    LOGIC_AND,
    NOTIFICATION_ID_TEMPLATE,
)
from .store import ScheduleStore

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import Event, EventStateChangedData, HomeAssistant


@dataclass
class MaintenanceScheduleManager:
    """Owns the baseline, the source-sensor listener, and due/notify logic.

    Shared via entry.runtime_data - every entity for this config entry
    (both sensors, the binary sensor, and the button) holds a reference to
    the same instance rather than each independently tracking state.
    """

    hass: HomeAssistant
    entry: ConfigEntry
    store: ScheduleStore = field(init=False)
    _listeners: list[Callable[[], None]] = field(default_factory=list, init=False)
    _unsub_state_change: Callable[[], None] | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Initialize the store for this config entry."""
        self.store = ScheduleStore(self.hass, self.entry.entry_id)

    @property
    def source_entity_id(self) -> str:
        """Return the configured source usage sensor's entity_id."""
        return self.entry.data[CONF_SOURCE_SENSOR]

    @property
    def threshold_hours(self) -> float | None:
        """Return the configured hours threshold, if any."""
        return self.entry.options.get(
            CONF_THRESHOLD_HOURS, self.entry.data.get(CONF_THRESHOLD_HOURS)
        )

    @property
    def threshold_days(self) -> float | None:
        """Return the configured days threshold, if any."""
        return self.entry.options.get(
            CONF_THRESHOLD_DAYS, self.entry.data.get(CONF_THRESHOLD_DAYS)
        )

    @property
    def logic(self) -> str:
        """Return AND/OR combination logic when both thresholds are set."""
        return self.entry.options.get(
            CONF_LOGIC, self.entry.data.get(CONF_LOGIC, DEFAULT_LOGIC)
        )

    @property
    def notify_enabled(self) -> bool:
        """Return whether persistent notifications are enabled for this schedule."""
        return self.entry.options.get(
            CONF_NOTIFY, self.entry.data.get(CONF_NOTIFY, True)
        )

    @property
    def notification_id(self) -> str:
        """Return this schedule's persistent notification id."""
        return NOTIFICATION_ID_TEMPLATE.format(entry_id=self.entry.entry_id)

    def _current_source_value(self) -> float | None:
        """Read and parse the source sensor's current numeric state."""
        state = self.hass.states.get(self.source_entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        try:
            return float(state.state)
        except (TypeError, ValueError):
            LOGGER.warning(
                "Source sensor %s has a non-numeric state %r",
                self.source_entity_id,
                state.state,
            )
            return None

    @property
    def hours_since_service(self) -> float | None:
        """Return hours elapsed since the last service reset.

        Returns None (unavailable) when either the source sensor or the
        baseline hasn't been established yet, rather than reporting 0 -
        which would misleadingly read as "just serviced".
        """
        current = self._current_source_value()
        baseline = self.store.data.baseline_hours
        if current is None or baseline is None:
            return None

        # total_usage is a running *estimate* per the ha-bambulab docs and
        # can drift backwards after a manual correction. Clamp rather than
        # surface a negative "hours since service".
        return max(current - baseline, 0.0)

    @property
    def days_since_service(self) -> float | None:
        """Return days elapsed since the last service reset."""
        last_service = self.store.data.last_service_datetime
        if last_service is None:
            return None
        delta = dt_util.utcnow() - last_service
        return round(delta.total_seconds() / 86400, 2)

    @property
    def hours_remaining(self) -> float | None:
        """Return hours until the hours threshold is reached.

        None when no hours threshold is configured or hours_since_service
        isn't available yet. Goes negative once overdue - e.g. -3.5 means
        3.5 hours past the threshold - rather than clamping at 0, so it
        actually answers "by how much" once a schedule is overdue.
        """
        if self.threshold_hours is None or self.hours_since_service is None:
            return None
        return round(self.threshold_hours - self.hours_since_service, 2)

    @property
    def days_remaining(self) -> float | None:
        """Return days until the days threshold is reached, negative once overdue."""
        if self.threshold_days is None or self.days_since_service is None:
            return None
        return round(self.threshold_days - self.days_since_service, 2)

    @property
    def is_due(self) -> bool:
        """Return whether this schedule is currently due for service."""
        hours_due = (
            self.threshold_hours is not None
            and self.hours_since_service is not None
            and self.hours_since_service >= self.threshold_hours
        )
        days_due = (
            self.threshold_days is not None
            and self.days_since_service is not None
            and self.days_since_service >= self.threshold_days
        )

        if self.threshold_hours is not None and self.threshold_days is not None:
            if self.logic == LOGIC_AND:
                return hours_due and days_due
            return hours_due or days_due

        return hours_due or days_due

    async def async_setup(self) -> None:
        """Load persisted state and start listening to the source sensor.

        If this is the very first setup and no reset has happened yet,
        seed the baseline from the source sensor's current value so
        hours_since_service starts at 0 rather than staying unavailable
        indefinitely until the user manually presses reset.
        """
        await self.store.async_load()

        if self.store.data.baseline_hours is None:
            current = self._current_source_value()
            if current is not None:
                await self.store.async_reset(current)

        self._unsub_state_change = async_track_state_change_event(
            self.hass, [self.source_entity_id], self._async_handle_source_update
        )

    async def async_unload(self) -> None:
        """Tear down the state listener."""
        if self._unsub_state_change is not None:
            self._unsub_state_change()
            self._unsub_state_change = None

    @callback
    def _async_handle_source_update(
        self,
        event: Event[EventStateChangedData],  # noqa: ARG002
    ) -> None:
        """React to the source sensor changing - recompute and notify entities."""
        self.hass.async_create_task(self._async_evaluate())

    async def async_refresh(self) -> None:
        """Re-evaluate due state on demand (e.g. after options change)."""
        await self._async_evaluate()

    async def _async_evaluate(self) -> None:
        """Recompute due state, fire/clear notifications, and refresh entities."""
        due = self.is_due

        if due and self.notify_enabled and not self.store.data.notified:
            await self._async_send_notification()
            await self.store.async_mark_notified(notified=True)
        elif not due and self.store.data.notified:
            # Threshold-based schedules don't un-trigger on their own in
            # normal use (usage hours don't go down), but this keeps
            # things consistent if a source sensor value is corrected
            # downward, or a threshold is raised in the options flow.
            await self.store.async_mark_notified(notified=False)

        self._notify_listeners()

    async def _async_send_notification(self) -> None:
        """Raise a persistent notification that this schedule is due."""
        name = self.entry.title
        parts = []
        if self.threshold_hours is not None and self.hours_remaining is not None:
            parts.append(f"{-self.hours_remaining:.1f}h overdue")
        if self.threshold_days is not None and self.days_remaining is not None:
            parts.append(f"{-self.days_remaining:.0f} days overdue")
        detail = " / ".join(parts) or "Service threshold reached."

        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": f"Maintenance due: {name}",
                "message": f"{detail}\n\nPress the {name} reset button once serviced.",
                "notification_id": self.notification_id,
            },
            blocking=False,
        )

    async def async_reset(self) -> None:
        """Reset this schedule's baseline - called by the reset button."""
        current = self._current_source_value()
        if current is None:
            LOGGER.warning(
                "Cannot reset %s - source sensor %s is unavailable",
                self.entry.title,
                self.source_entity_id,
            )
            return

        await self.store.async_reset(current)
        await self.hass.services.async_call(
            "persistent_notification",
            "dismiss",
            {"notification_id": self.notification_id},
            blocking=False,
        )

        if self.hass.services.has_service("logbook", "log"):
            await self.hass.services.async_call(
                "logbook",
                "log",
                {
                    "name": self.entry.title,
                    "message": f"was serviced at {current:.1f}h",
                },
                blocking=False,
            )

        self._notify_listeners()

    def register_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register an entity callback for when derived values change.

        Returns an unsubscribe callable, matching the convention used by
        HA's own listener-registration helpers (e.g.
        async_track_state_change_event) so entities can use it directly
        in async_on_remove.
        """
        self._listeners.append(listener)

        def _unsub() -> None:
            self._listeners.remove(listener)

        return _unsub

    def _notify_listeners(self) -> None:
        """Tell every registered entity to re-read state and write it."""
        for listener in list(self._listeners):
            listener()


@dataclass
class MaintenanceConfigEntryRuntimeData:
    """Runtime data stashed on the config entry, per HA's typed-entry pattern."""

    manager: MaintenanceScheduleManager


# Typed alias mirroring the PandaStatusConfigEntry pattern - keeps
# entry.runtime_data type-checked as MaintenanceConfigEntryRuntimeData
# throughout the integration instead of Any.
type MaintenanceConfigEntry = ConfigEntry[MaintenanceConfigEntryRuntimeData]
