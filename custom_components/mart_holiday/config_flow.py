"""Config flow for Mart Holiday."""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import (CONF_SCAN_INTERVAL)

from .const import DOMAIN, _MART_KIND, CONF_MART_KIND, CONF_MART_CODE, CONF_AREA, _AREA, CONF_NAME

_LOGGER = logging.getLogger(__name__)

class MartHolidayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mart Holiday."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize flow."""
        self._mart_kind: Required[str] = None
        self._mart_code: Required[str] = None
        self._name: Required[str]      = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._mart_kind = user_input[CONF_MART_KIND]
            self._mart_code = user_input[CONF_MART_CODE]
            self._name      = user_input[CONF_NAME]

            uuid = 'mart-holiday-{}-{}'.format(self._mart_kind, self._mart_code)
            await self.async_set_unique_id(uuid)

            tit = '{}({})'.format(_MART_KIND[self._mart_kind], self._name)

            return self.async_create_entry(title=tit, data=user_input)

        #if self._async_current_entries():
        #    return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self._show_user_form(errors)

    async def async_step_import(self, import_info):
        """Handle import from config file."""
        return await self.async_step_user(import_info)

    @callback
    def _show_user_form(self, errors=None):
        schema = vol.Schema(
            {
                vol.Required(CONF_MART_KIND, default=None): vol.In(_MART_KIND),
                vol.Required(CONF_MART_CODE, default=None): str,
                vol.Required(CONF_NAME,      default=None): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors or {}
        )
