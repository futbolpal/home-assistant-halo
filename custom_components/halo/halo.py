"""
Python module for control of Halo bluetooth dimmers
This code is released under the terms of the GPLv3 license. See the
LICENSE file for more details.
"""
import json
import logging
import requests
import httpx
import time

REFRESH_CACHE_TTL_SECONDS = 15
API_TIMEOUT = 10
_LOGGER = logging.getLogger(__name__)

class HaloDevice:
    def __init__(self, api, name, pid, is_group = False):
        self._state = {}
        self._api = api
        self._pid = pid
        self._name = name
        self._is_group = is_group
        self._last_updated = None

    async def async_refresh(self):
        if self._is_group:
            self._state = await self._api.async_get_group_state(self._pid)
            _LOGGER.warn(self._state)
        else:
            self._state = await self._api.async_get_device_state(self._pid)

    async def async_turn_on(self):
        await self._api.async_turn_on(self._pid, self._is_group)
        self._last_updated = time.time()

    async def async_turn_off(self):
        await self._api.async_turn_off(self._pid, self._is_group)
        self._last_updated = time.time()

    async def async_set_brightness(self, value):
        self._state = await self._api.async_set_brightness(self._pid, value, self._is_group)
        self._last_updated = time.time()

    async def async_set_color_temp(self, value):
        self._state = await self._api.async_set_color_temp(self._pid, value, self._is_group)
        self._last_updated = time.time()

    @property
    def pid(self):
        return self._pid

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._is_on()

    @property
    def brightness(self):
        if not self._is_on():
            return 0

        _state_obj = self._state_brightness()
        if _state_obj is None:
            return None

        _brightness = json.loads(_state_obj['value'])[0]
        return _brightness or 255

    @property
    def color_temp(self):
        _state_obj = self._state_color_temp()
        if _state_obj is None:
            return None
        return int(_state_obj['humanized'])

    def _is_on(self):
        _state_obj = self._state_on_off()
        if _state_obj is None:
            return None
        return bool(json.loads(_state_obj['value'])[0])

    def _state_on_off(self):
        return next((x for x in self._state if x['name'] == 'on_off'), None)

    def _state_brightness(self):
        return next((x for x in self._state if x['name'] == 'dim'), None)

    def _state_color_temp(self):
        return next((x for x in self._state if x['name'] == 'white'), None)


class HaloGroup(HaloDevice):
    def __init__(self, api, name, pid):
        super().__init__(api, name, pid)
        self._is_group = True

class HaloScene:
    def __init__(self, api, name, pid, location_id):
        self._state = None
        self._api = api
        self._pid = pid
        self._location_id = location_id
        self._name = name
        self._last_updated = None

    @property
    def pid(self):
        return self._pid

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._is_on()

    async def async_turn_on(self):
        await self._api.async_set_scene_state(self._pid, 'action', 'on')

    async def async_turn_off(self):
        await self._api.async_set_scene_state(self._pid, 'action', 'on')
 
    async def async_refresh(self):
        self._state = await self._api.async_get_scene_state(self._pid, self._location_id)

    def _state_on_off(self):
        return next((x for x in self._state if x['name'] == 'action'), None)

    def _is_on(self):
        _state_obj = self._state_on_off()
        if _state_obj is None:
            return None
        return bool(json.loads(_state_obj['value'])[0])


class HaloApi:
    API_URL = "https://api.avi-on.com/{api}"
    API_AUTH = API_URL.format(api='sessions')
    API_LOCATION = API_URL.format(api='user/locations')
    API_GROUPS = API_URL.format(api='locations/{location}/groups')
    API_DEVICES = API_URL.format(api='locations/{location}/abstract_devices')
    API_SCENES = API_URL.format(api='locations/{location}/scenes')
    API_DEVICE_STATE = API_URL.format(api='devices/{pid}/state')
    API_GROUP_STATE = API_URL.format(api='groups/{pid}/state')
    API_SCENE_STATE = API_URL.format(api='scenes/{pid}/state')

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def authenticate(self):
        """Authenticate with the API and get a token."""
        auth_data = {'email': self.username, 'password': self.password}
        r = requests.post(self.API_AUTH, json=auth_data, timeout=API_TIMEOUT)
        self._auth_token = r.json()['credentials']['auth_token']
        try:
            return self._auth_token
        except KeyError:
            raise(HaloException('API authentication failed'))

    def get_locations(self):
        """Get a list of locations from the API."""
        headers = {'Authorization': 'Token {}'.format(self._auth_token)}
        r = requests.get(self.API_LOCATION, headers=headers, timeout=API_TIMEOUT)
        return r.json()['locations']

    def get_groups(self, location_id):
        """Get a list of groups for a particular location."""
        headers = {'Authorization': 'Token {}'.format(self._auth_token)}
        r = requests.get(self.API_GROUPS.format(location=location_id),
                headers=headers, timeout=API_TIMEOUT)
        return list(map(lambda g: HaloGroup(self, g['name'], g['pid']), r.json()['groups']))

    def get_devices(self, location_id):
        """Get a list of devices for a particular location."""
        headers = {'Authorization': 'Token {}'.format(self._auth_token)}
        r = requests.get(self.API_DEVICES.format(location=location_id),
                headers=headers, timeout=API_TIMEOUT)
        return list(map(lambda d: HaloDevice(self, d['name'], d['pid']), [d for d in r.json()['abstract_devices'] if d['product_id'] == 162]))

    def get_scenes(self, location_id):
        """Get a list of scenes for a particular location."""
        headers = {'Authorization': 'Token {}'.format(self._auth_token)}
        r = requests.get(self.API_SCENES.format(location=location_id),
                headers=headers, timeout=API_TIMEOUT)
        return list(map(lambda g: HaloScene(self, g['name'], g['pid'], location_id), r.json()['scenes']))

    def turn_on(self, pid, is_group = False):
        """Turns on a device or group"""
        if is_group:
            return self.set_group_state(pid, 'on_off', '[1]')
        return self.set_device_state(pid, 'on_off', '[1]')

    def turn_off(self, pid, is_group = False):
        """Turns off a device or group"""
        if is_group:
            return self.set_group_state(pid, 'on_off', '[0]')
        return self.set_device_state(pid, 'on_off', '[0]')

    def set_brightness(self, pid, value, is_group = False):
        """Dim a device or group"""
        if is_group:
            return self.set_group_state(pid, 'dim', '[{}]'.format(value))
        return self.set_device_state(pid, 'dim', '[{}]'.format(value))

    def set_color_temp(self, pid, k, is_group = False):
        if is_group:
            return self.set_group_state(pid, 'white', k)
        return self.set_device_state(pid, 'white', k)

    def set_group_state(self, pid, name, value):
        headers = {'Authorization': 'Token {}'.format(self._auth_token)}
        data =  { 'state' : {'name': name, 'value': value}}

        r = requests.post(self.API_GROUP_STATE.format(pid=pid),
                headers=headers,
                json=data,
                timeout=API_TIMEOUT)
        return r.json()['states']

    def set_device_state(self, pid, name, value):
        headers = {'Authorization': 'Token {}'.format(self._auth_token)}
        data =  { 'state' : {'name': name, 'value': value}}

        r = requests.post(self.API_DEVICE_STATE.format(pid=pid),
                headers=headers,
                json=data,
                timeout=API_TIMEOUT)
        return r.json()['states']

    def set_scene_state(self, pid, name, value):
        headers = {'Authorization': 'Token {}'.format(self._auth_token)}
        data =  { 'state' : {'name': name, 'value': value}}

        r = requests.post(self.API_SCENE_STATE.format(pid=pid),
                headers=headers,
                json=data,
                timeout=API_TIMEOUT)
        return r.json()['states']

    async def async_authenticate(self):
        """Authenticate with the API and get a token."""
        auth_data = {'email': self.username, 'password': self.password}

        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(self.API_AUTH, json=auth_data, timeout=API_TIMEOUT)
                self._auth_token = r.json()['credentials']['auth_token']
                return self._auth_token
        except (httpx.ReadTimeout):
            _LOGGER.error("Failed to authenticate: Timeout")
            raise(HaloException('API authentication failed'))

    async def async_turn_on(self, pid, is_group = False):
        """Turns on a device or group"""
        if is_group:
            return await self.async_set_group_state(pid, 'on_off', '[1]')
        return await self.async_set_device_state(pid, 'on_off', '[1]')

    async def async_turn_off(self, pid, is_group = False):
        """Turns off a device or group"""
        if is_group:
            return await self.async_set_group_state(pid, 'on_off', '[0]')
        return await self.async_set_device_state(pid, 'on_off', '[0]')

    async def async_set_brightness(self, pid, value, is_group = False):
        """Dim a device or group"""
        if is_group:
            return await self.async_set_group_state(pid, 'dim', '[{}]'.format(value))
        return await self.async_set_device_state(pid, 'dim', '[{}]'.format(value))

    async def async_set_color_temp(self, pid, k, is_group = False):
        if is_group:
            return await self.async_set_group_state(pid, 'white', k)
        return await self.async_set_device_state(pid, 'white', k)

    async def async_set_group_state(self, pid, name, value):
        headers = {'Authorization': 'Token {}'.format(self._auth_token)}
        data =  { 'state' : {'name': name, 'value': value}}

        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(self.API_GROUP_STATE.format(pid=pid),
                        headers=headers,
                        json=data,
                        timeout=API_TIMEOUT)
                return r.json()['states']
        except (httpx.ReadTimeout):
            _LOGGER.error("Failed to set group state due to timeout")

    async def async_set_device_state(self, pid, name, value):
        headers = {'Authorization': 'Token {}'.format(self._auth_token)}
        data =  { 'state' : {'name': name, 'value': value}}

        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(self.API_DEVICE_STATE.format(pid=pid),
                        headers=headers,
                        json=data,
                        timeout=API_TIMEOUT)
                return r.json()['states']
        except (httpx.ReadTimeout):
            _LOGGER.error("Failed to set device state due to timeout")

    async def async_set_scene_state(self, pid, name, value):
        headers = {'Authorization': 'Token {}'.format(self._auth_token)}
        data =  { 'state' : {'name': name, 'value': value}}

        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(self.API_SCENE_STATE.format(pid=pid),
                        headers=headers,
                        json=data,
                        timeout=API_TIMEOUT)
                return r.json()['states']
        except (httpx.ReadTimeout):
            _LOGGER.error("Failed to set scene state due to timeout")

    async def async_get_group_state(self, pid):
        headers = {'Authorization': 'Token {}'.format(self._auth_token)}
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(self.API_GROUP_STATE.format(pid=pid),
                        headers=headers,
                        timeout=API_TIMEOUT)
                return r.json()['state']
        except (httpx.ReadTimeout):
            _LOGGER.error("Failed to get group state due to timeout")

    async def async_get_scene_state(self, pid, location_id):
        headers = {'Authorization': 'Token {}'.format(self._auth_token)}
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(self.API_SCENES.format(location=location_id),
                        headers=headers,
                        timeout=API_TIMEOUT)
                return [scene for scene in r.json()['scenes'] if scene['pid'] == pid][0]['properties']
        except (httpx.ReadTimeout):
            _LOGGER.error("Failed to get scene state due to timeout")


    async def async_get_device_state(self, pid):
        headers = {'Authorization': 'Token {}'.format(self._auth_token)}
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(self.API_DEVICE_STATE.format(pid=pid),
                        headers=headers,
                        timeout=API_TIMEOUT)
                return r.json()['state']
        except (httpx.ReadTimeout):
            _LOGGER.error("Failed to get device state due to timeout")
