"""Support for Halo dimmers."""
from __future__ import annotations

import logging
import importlib

from homeassistant.components.switch import (
    SwitchEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
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

    switches = []
    locations = await hass.async_add_executor_job(api.get_locations)
    for location in locations:
        scenes = await hass.async_add_executor_job(api.get_scenes, location['pid'])
        for scene in scenes:
            switches.append(HaloSwitch(scene))
    add_entities(switches, True)


class HaloSwitch(SwitchEntity):
    def __init__(self, device):
        """Initialize the switch."""
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
    def is_on(self):
        return self._device.is_on

    async def async_turn_on(self, **kwargs):
        _LOGGER.warn("Async Turn on: %s", kwargs)
        await self._device.async_turn_on()

    async def async_turn_off(self, **kwargs):
        await self._device.async_turn_off()

    async def async_update(self):
        await self._device.async_refresh()
 
