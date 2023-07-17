"""The halo component."""
import logging
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
)
from .const import DATA_HALO_CONFIG, DOMAIN, PLATFORMS
from .halo import HaloApi

CONFIG = vol.Schema({ 
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    })
})

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Setup of the component"""
    config = config.get(DOMAIN, {})

    hass.async_create_task(
	hass.config_entries.flow.async_init(
	    DOMAIN,
	    context={"source": SOURCE_IMPORT},
	    data={
		CONF_USERNAME: config[CONF_USERNAME],
		CONF_PASSWORD: config[CONF_PASSWORD],
	    },
	)
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    api = HaloApi(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    await api.async_authenticate()

    hass.data[DOMAIN] = api
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the config entry and platforms."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(DOMAIN)
    return unload_ok
