# Maintenance Tracker for Home Assistant
#
# Copyright (c) 2026 David Venter (github.com/BambamNZ/maintenance-tracker)
#
# SPDX-License-Identifier: MIT

"""Config flow for maintenance_tracker.

Each config entry is one maintenance schedule (e.g. "P2S Nozzle Clean"),
matching the "helper" pattern used by HA's own Threshold/Utility Meter
integrations rather than a single entry covering every printer.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from .const import (
    CONF_LOGIC,
    CONF_NOTIFY,
    CONF_SOURCE_SENSOR,
    CONF_THRESHOLD_DAYS,
    CONF_THRESHOLD_HOURS,
    DEFAULT_LOGIC,
    DEFAULT_NOTIFY,
    DOMAIN,
    LOGIC_OPTIONS,
)


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the shared user/options form schema, pre-filled from defaults.

    Thresholds are deliberately NOT wrapped in vol.Any(None, selector(...)).
    HA's frontend reads the selector straight off the schema value to
    decide which widget to render - burying it inside vol.Any hides that
    from the form generator and the field renders with no input control
    at all. vol.Optional (no default forcing a value) is enough on its
    own to make the field skippable: if the person leaves it blank, the
    key is simply absent from user_input and .get() downstream treats it
    as "not configured".
    """
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Optional(
                CONF_THRESHOLD_HOURS,
                description={"suggested_value": defaults.get(CONF_THRESHOLD_HOURS)},
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    step=0.5,
                    unit_of_measurement="h",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(
                CONF_THRESHOLD_DAYS,
                description={"suggested_value": defaults.get(CONF_THRESHOLD_DAYS)},
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    step=1,
                    unit_of_measurement="d",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(
                CONF_LOGIC, default=defaults.get(CONF_LOGIC, DEFAULT_LOGIC)
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=LOGIC_OPTIONS, translation_key=CONF_LOGIC
                )
            ),
            vol.Optional(
                CONF_NOTIFY, default=defaults.get(CONF_NOTIFY, DEFAULT_NOTIFY)
            ): selector.BooleanSelector(),
        }
    )


class MaintenanceTrackerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for a single maintenance schedule."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """First step - name the schedule and pick its source sensor."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if (
                user_input.get(CONF_THRESHOLD_HOURS) is None
                and user_input.get(CONF_THRESHOLD_DAYS) is None
            ):
                errors["base"] = "threshold_required"
            else:
                await self.async_set_unique_id(
                    f"{user_input[CONF_SOURCE_SENSOR]}_{user_input[CONF_NAME]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): selector.TextSelector(),
                vol.Required(CONF_SOURCE_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
            }
        ).extend(_schema().schema)

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> MaintenanceTrackerOptionsFlow:
        """Return the options flow for adjusting thresholds after setup."""
        return MaintenanceTrackerOptionsFlow(config_entry)


class MaintenanceTrackerOptionsFlow(OptionsFlow):
    """Adjust thresholds/logic/notify on an existing schedule without recreating it."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the options flow for a given config entry."""
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show and process the options form."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = {**self._entry.data, **self._entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_schema(defaults=current)
        )
