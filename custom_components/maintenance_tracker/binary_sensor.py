# Maintenance Tracker for Home Assistant
#
# Copyright (c) 2026 David Venter (github.com/BambamNZ/maintenance-tracker)
#
# SPDX-License-Identifier: MIT

"""Binary sensor platform for maintenance_tracker.

This is the entity intended for 3rd-party automations/notifications to
trigger off - it flips on exactly when this schedule's threshold(s) are
crossed, independent of whether the built-in persistent notification is
enabled.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from .entity import MaintenanceScheduleEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import MaintenanceConfigEntry, MaintenanceScheduleManager


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: MaintenanceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the service-due binary sensor for a schedule."""
    async_add_entities([ServiceDueBinarySensor(entry.runtime_data.manager)])


class ServiceDueBinarySensor(MaintenanceScheduleEntity, BinarySensorEntity):
    """Whether this maintenance schedule has crossed its threshold(s).

    device_class stays PROBLEM so this still gets picked up correctly by
    HA's Areas/dashboard "problem" grouping and any voice-assistant
    exposure, but the displayed on/off text is overridden via
    translation_key to read "Yes"/"No" instead of the device class's
    default "Problem"/"OK" - friendlier for a dashboard glance, and the
    override lives in translations/en.json under
    entity.binary_sensor.service_due.state.
    """

    _attr_name = "Service due"
    _attr_icon = "mdi:wrench-clock"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_translation_key = "service_due"

    def __init__(self, manager: MaintenanceScheduleManager) -> None:
        """Initialize the service-due binary sensor."""
        super().__init__(manager, "service_due")

    @property
    def is_on(self) -> bool:
        """Return True when this schedule's threshold(s) have been crossed."""
        return self._manager.is_due

    @property
    def extra_state_attributes(self) -> dict[str, float | str | None]:
        """Expose the raw figures behind the due decision for dashboards/automations."""
        return {
            "hours_since_service": self._manager.hours_since_service,
            "days_since_service": self._manager.days_since_service,
            "hours_remaining": self._manager.hours_remaining,
            "days_remaining": self._manager.days_remaining,
            "threshold_hours": self._manager.threshold_hours,
            "threshold_days": self._manager.threshold_days,
            "logic": self._manager.logic,
        }
