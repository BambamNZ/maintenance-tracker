# Maintenance Tracker for Home Assistant
#
# Copyright (c) 2026 David Venter (github.com/BambamNZ/maintenance-tracker)
#
# SPDX-License-Identifier: MIT

"""Button platform for maintenance_tracker."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity

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
    """Set up the reset button for a schedule."""
    async_add_entities([ResetServiceButton(entry.runtime_data.manager)])


class ResetServiceButton(MaintenanceScheduleEntity, ButtonEntity):
    """Press after servicing to re-baseline hours/days since service."""

    _attr_name = "Reset service"
    _attr_icon = "mdi:wrench-check"

    def __init__(self, manager: MaintenanceScheduleManager) -> None:
        """Initialize the reset button."""
        super().__init__(manager, "reset_service")

    async def async_press(self) -> None:
        """Re-baseline this schedule against the source sensor's current value."""
        await self._manager.async_reset()
