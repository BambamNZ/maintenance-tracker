# Maintenance Tracker for Home Assistant
#
# Copyright (c) 2026 David Venter (github.com/BambamNZ/maintenance-tracker)
#
# SPDX-License-Identifier: MIT

"""Sensor platform for maintenance_tracker."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfTime

from .entity import MaintenanceScheduleEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import MaintenanceConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: MaintenanceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the hours/days-since-service sensors for a schedule."""
    manager = entry.runtime_data.manager
    async_add_entities(
        [
            HoursSinceServiceSensor(manager),
            DaysSinceServiceSensor(manager),
            HoursRemainingSensor(manager),
            DaysRemainingSensor(manager),
        ]
    )


class HoursSinceServiceSensor(MaintenanceScheduleEntity, SensorEntity):
    """Hours elapsed on the source usage sensor since the last reset."""

    _attr_name = "Hours since service"
    _attr_icon = "mdi:clock-outline"
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, manager: Any) -> None:
        """Initialize the hours-since-service sensor."""
        super().__init__(manager, "hours_since_service")

    @property
    def native_value(self) -> float | None:
        """Return hours elapsed since the last service reset."""
        return self._manager.hours_since_service


class DaysSinceServiceSensor(MaintenanceScheduleEntity, SensorEntity):
    """Days elapsed since the last service reset."""

    _attr_name = "Days since service"
    _attr_icon = "mdi:calendar-clock"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, manager: Any) -> None:
        """Initialize the days-since-service sensor."""
        super().__init__(manager, "days_since_service")

    @property
    def native_value(self) -> float | None:
        """Return days elapsed since the last service reset."""
        return self._manager.days_since_service


class HoursRemainingSensor(MaintenanceScheduleEntity, SensorEntity):
    """Hours until the hours threshold is reached - negative once overdue.

    Only meaningful when an hours threshold is configured on this
    schedule; reports unavailable otherwise rather than a confusing 0.
    """

    _attr_name = "Hours remaining"
    _attr_icon = "mdi:timer-sand"
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, manager: Any) -> None:
        """Initialize the hours-remaining sensor."""
        super().__init__(manager, "hours_remaining")

    @property
    def native_value(self) -> float | None:
        """Return hours remaining until due, negative once overdue."""
        return self._manager.hours_remaining

    @property
    def available(self) -> bool:
        """Only available when this schedule has an hours threshold set."""
        return self._manager.threshold_hours is not None


class DaysRemainingSensor(MaintenanceScheduleEntity, SensorEntity):
    """Days until the days threshold is reached - negative once overdue.

    Only meaningful when a days threshold is configured on this
    schedule; reports unavailable otherwise rather than a confusing 0.
    """

    _attr_name = "Days remaining"
    _attr_icon = "mdi:timer-sand"
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, manager: Any) -> None:
        """Initialize the days-remaining sensor."""
        super().__init__(manager, "days_remaining")

    @property
    def native_value(self) -> float | None:
        """Return days remaining until due, negative once overdue."""
        return self._manager.days_remaining

    @property
    def available(self) -> bool:
        """Only available when this schedule has a days threshold set."""
        return self._manager.threshold_days is not None
