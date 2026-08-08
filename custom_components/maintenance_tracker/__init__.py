# Maintenance Tracker for Home Assistant
#
# Copyright (c) 2026 David Venter (github.com/BambamNZ/maintenance-tracker)
#
# SPDX-License-Identifier: MIT

"""The maintenance_tracker integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform

from .data import MaintenanceConfigEntryRuntimeData, MaintenanceScheduleManager

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import MaintenanceConfigEntry

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: MaintenanceConfigEntry) -> bool:
    """Set up a maintenance schedule from a config entry."""
    manager = MaintenanceScheduleManager(hass=hass, entry=entry)
    await manager.async_setup()

    entry.runtime_data = MaintenanceConfigEntryRuntimeData(manager=manager)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: MaintenanceConfigEntry
) -> bool:
    """Unload a maintenance schedule config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.manager.async_unload()

    return unloaded


async def _async_update_listener(
    hass: HomeAssistant,  # noqa: ARG001
    entry: MaintenanceConfigEntry,
) -> None:
    """Re-evaluate due state when options (e.g. thresholds) change."""
    await entry.runtime_data.manager.async_refresh()
