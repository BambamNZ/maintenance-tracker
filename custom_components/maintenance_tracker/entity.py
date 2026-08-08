# Maintenance Tracker for Home Assistant
#
# Copyright (c) 2026 David Venter (github.com/BambamNZ/maintenance-tracker)
#
# SPDX-License-Identifier: MIT

"""Shared base entity for maintenance_tracker."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN

if TYPE_CHECKING:
    from .data import MaintenanceScheduleManager


class MaintenanceScheduleEntity(Entity):
    """Base entity for a single maintenance schedule.

    Each schedule (config entry) is represented as its own HA "device" -
    named after the schedule (e.g. "P2S Nozzle Clean") rather than
    grouped under the source printer's device, since one printer can have
    several independent schedules and this integration doesn't own the
    printer device itself.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, manager: MaintenanceScheduleManager, key: str) -> None:
        """Initialize the entity for a given schedule and entity key."""
        self._manager = manager
        self._attr_unique_id = f"{DOMAIN}_{manager.entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            name=manager.entry.title,
            manufacturer="Maintenance Tracker",
            model="Usage-based maintenance schedule",
            identifiers={(DOMAIN, manager.entry.entry_id)},
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to schedule updates once added to hass."""
        self.async_on_remove(
            self._manager.register_listener(self._handle_manager_update)
        )

    def _handle_manager_update(self) -> None:
        """Write new state when the manager recomputes derived values."""
        self.async_write_ha_state()
