"""Support for Halo dimmers."""
from __future__ import annotations

import logging
import importlib
import time
import voluptuous as vol

from .halo import *
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    PLATFORM_SCHEMA,
    COLOR_MODE_COLOR_TEMP,
    COLOR_MODE_BRIGHTNESS,
    LightEntity,
)
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.util.color import color_temperature_mired_to_kelvin, color_temperature_kelvin_to_mired
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import homeassistant.helpers.config_validation as cv

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)

_LOGGER = logging.getLogger(__name__)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up an Halo switch."""
    lights = []
    api = HaloApi(config[CONF_USERNAME], config[CONF_PASSWORD])
    api.authenticate()
    locations = api.get_locations()
    for location in locations:
        devices = api.get_devices(location['pid'])
        for device in devices:
            lights.append(HaloLight(device))
        groups = api.get_groups(location['pid'])
        for group in groups:
            lights.append(HaloLight(group))
    add_entities(lights)


class HaloLight(LightEntity):
    def __init__(self, device):
        """Initialize the light."""
        self._device = device
        self._unique_id = device.pid
        self._name = device.name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def brightness(self):
        return self._device.brightness

    @property
    def color_temp(self):
        return self._device.color_temp

    @property
    def is_on(self):
        return self._device.is_on

    @property
    def max_mireds(self):
        return color_temperature_kelvin_to_mired(2700)

    @property
    def min_mireds(self):
        return color_temperature_kelvin_to_mired(5000)

    @property
    def color_mode(self):
        return COLOR_MODE_COLOR_TEMP

    @property
    def supported_color_modes(self):
        return {COLOR_MODE_COLOR_TEMP}

    def turn_on(self, **kwargs):
        _LOGGER.warn("Turn on: %s", kwargs)
        if ATTR_BRIGHTNESS in kwargs:
            self._device.set_brightness(kwargs.get(ATTR_BRIGHTNESS))
        if ATTR_COLOR_TEMP in kwargs:
            self._device.set_color_temp(color_temperature_mired_to_kelvin(kwargs.get(ATTR_COLOR_TEMP)))
        if not bool(kwargs):
            self._device.turn_on()
            self._device.set_color_temp(5000)

    def turn_off(self, **kwargs):
        self._device.turn_off()

    async def async_update(self):
        await self._device.async_refresh()
 
