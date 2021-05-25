""" Mart Holiday Sensor for Home Assistant """
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_NAME, CONF_MONITORED_CONDITIONS
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, PLATFORM, CONF_MART_KIND, CONF_MART_CODE, CONF_AREA

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            vol.Schema({vol.Required(CONF_MART_KIND, default=DOMAIN): cv.string}),
            vol.Schema({vol.Required(CONF_MART_CODE): cv.string}),
            vol.Schema({vol.Required(CONF_NAME, default=None): cv.string}),
            vol.Schema({vol.Optional(CONF_AREA, default=None): cv.string}),
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up Mart Holiday from configuration.yaml."""
    conf = config.get(DOMAIN)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Mart Holiday from a config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, PLATFORM)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return await hass.config_entries.async_forward_entry_unload(entry, PLATFORM)
