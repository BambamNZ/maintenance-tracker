# Maintenance Tracker for Home Assistant
#
# Copyright (c) 2026 David Venter (github.com/BambamNZ/maintenance-tracker)
#
# SPDX-License-Identifier: MIT

"""Persistent baseline storage for a single maintenance schedule.

total_usage-style sensors climb forever and never reset themselves, so
"hours since service" has to be measured against a baseline this
integration owns and persists itself - HA's recorder/history is not
reliable long-term storage, and entity RestoreState is meant for
transient state across restarts, not an indefinitely-growing service log.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import STORAGE_KEY_PREFIX, STORAGE_VERSION

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.core import HomeAssistant


@dataclass
class ScheduleBaseline:
    """Baseline data persisted for a single maintenance schedule.

    Attributes:
        baseline_hours: The source sensor's value at the last service
            reset. None until the schedule has been reset at least once
            (or seeded during setup - see ScheduleStore.async_load).
        last_service_date: ISO 8601 timestamp of the last reset.
        notified: Whether a persistent notification has already been
            raised for the current due period, so reactive updates from
            the source sensor don't spam a fresh notification every poll.

    """

    baseline_hours: float | None = None
    last_service_date: str | None = None
    notified: bool = False

    @property
    def last_service_datetime(self) -> datetime | None:
        """Return last_service_date parsed as a datetime, if set."""
        if self.last_service_date is None:
            return None
        return dt_util.parse_datetime(self.last_service_date)


class ScheduleStore:
    """Thin wrapper around homeassistant.helpers.storage.Store.

    One store per config entry (one per maintenance schedule), keyed by
    entry_id so schedules never collide.
    """

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize the store for a given config entry."""
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}_{entry_id}"
        )
        self.data = ScheduleBaseline()

    async def async_load(self) -> ScheduleBaseline:
        """Load baseline data from disk, defaulting if nothing is stored yet."""
        raw = await self._store.async_load()
        if raw is not None:
            self.data = ScheduleBaseline(**raw)
        return self.data

    async def async_save(self) -> None:
        """Persist the current baseline data to disk."""
        await self._store.async_save(asdict(self.data))

    async def async_reset(self, current_source_value: float) -> None:
        """Reset the baseline to the source sensor's current value, now."""
        self.data = ScheduleBaseline(
            baseline_hours=current_source_value,
            last_service_date=dt_util.utcnow().isoformat(),
            notified=False,
        )
        await self.async_save()

    async def async_mark_notified(self, *, notified: bool) -> None:
        """Update and persist the notified flag."""
        self.data.notified = notified
        await self.async_save()
