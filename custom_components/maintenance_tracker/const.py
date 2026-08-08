# Maintenance Tracker for Home Assistant
#
# Generic maintenance-reminder helper that wraps any cumulative usage
# sensor (e.g. Bambu Lab's sensor.<model>_<serial>_total_usage) and tracks
# hours/days elapsed since the maintenance item was last serviced.
#
# Copyright (c) 2026 David Venter (github.com/BambamNZ/maintenance-tracker)
#
# SPDX-License-Identifier: MIT

"""Constants for maintenance_tracker."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "maintenance_tracker"

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}_schedule"

# Config / options keys
CONF_SOURCE_SENSOR = "source_sensor"
CONF_THRESHOLD_HOURS = "threshold_hours"
CONF_THRESHOLD_DAYS = "threshold_days"
CONF_LOGIC = "logic"
CONF_NOTIFY = "notify"

# Threshold combination logic when both hours and days are configured
LOGIC_OR = "or"
LOGIC_AND = "and"
LOGIC_OPTIONS = [LOGIC_OR, LOGIC_AND]
DEFAULT_LOGIC = LOGIC_OR
DEFAULT_NOTIFY = True

# Notification id template - shared so the reset button can dismiss the
# exact notification this schedule raised, per config entry.
NOTIFICATION_ID_TEMPLATE = f"{DOMAIN}_{{entry_id}}_due"
