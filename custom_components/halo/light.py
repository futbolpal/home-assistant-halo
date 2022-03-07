"""Support for Halo dimmers."""
from __future__ import annotations

import logging
import importlib

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    PLATFORM_SCHEMA,
    COLOR_MODE_COLOR_TEMP,
    COLOR_MODE_BRIGHTNESS,
    LightEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.util.color import color_temperature_mired_to_kelvin, color_temperature_kelvin_to_mired
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.config_entries import ConfigEntry
from .halo import *
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up an Halo switch."""
    api = hass.data[DOMAIN]

    lights = []
    locations = await hass.async_add_executor_job(api.get_locations)
    for location in locations:
        devices = await hass.async_add_executor_job(api.get_devices, location['pid'])
        for device in devices:
            lights.append(HaloLight(device))
        groups = await hass.async_add_executor_job(api.get_groups, location['pid'])
        for group in groups:
            lights.append(HaloLight(group))
    add_entities(lights, True)


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

    async def async_turn_on(self, **kwargs):
        _LOGGER.warn("Async Turn on: %s", kwargs)
        if ATTR_BRIGHTNESS in kwargs:
            await self._device.async_set_brightness(kwargs.get(ATTR_BRIGHTNESS))
        if ATTR_COLOR_TEMP in kwargs:
            await self._device.async_set_color_temp(color_temperature_mired_to_kelvin(kwargs.get(ATTR_COLOR_TEMP)))
        if not bool(kwargs):
            await self._device.async_turn_on()
            await self._device.async_set_color_temp(5000)

    async def async_turn_off(self, **kwargs):
        await self._device.async_turn_off()

    async def async_update(self):
        await self._device.async_refresh()
 
