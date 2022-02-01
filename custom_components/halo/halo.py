"""
Python module for control of Halo bluetooth dimmers
This code is released under the terms of the GPLv3 license. See the
LICENSE file for more details.
"""
import json
import logging
import requests

API_TIMEOUT = 10
_LOGGER = logging.getLogger(__name__)

class HaloDevice:
    def __init__(self, api, name, pid, is_group = False):
        self._state = {}
        self._api = api
        self._pid = pid
        self._name = name
        self._is_group = is_group

    def refresh(self):
        if self._is_group:
            self._state = self._api.get_group_state(self._pid)
        else:
            self._state = self._api.get_device_state(self._pid)

    def turn_on(self):
        self._state = self._api.turn_on(self._pid, self._is_group)

    def turn_off(self):
        self._state = self._api.turn_off(self._pid, self._is_group)

    def set_brightness(self, value):
        self._state = self._api.set_brightness(self._pid, value, self._is_group)

    def set_color_temp(self, k):
        self._state = self._api.set_color_temp(self._pid, k, self._is_group)

    @property
    def pid(self):
        return self._pid

    @property
    def name(self):
        return self._name

    @property
    def brightness(self):
        _state_obj = next((x for x in self._state if x['name'] == 'dim'), None)
        if _state_obj is None:
            return None 
        _brightness = json.loads(_state_obj['value'])[0]
        if self.is_on:
            return _brightness or 255
        return 0

    @property
    def is_on(self):
        state_obj = next((x for x in self._state if x['name'] == 'on_off'), None)
        if state_obj is None:
            return None 
        return bool(json.loads(state_obj['value'])[0])

    @property
    def color_temp(self):
        state_obj = next((x for x in self._state if x['name'] == 'white'), None)
        if state_obj is None:
            return None 
        return int(state_obj['humanized'])

class HaloGroup(HaloDevice):
    def __init__(self, api, name, pid):
        super().__init__(api, name, pid)
        self._is_group = True

class HaloApi:
    API_URL = "https://api.avi-on.com/{api}"
    API_AUTH = API_URL.format(api='sessions')
    API_LOCATION = API_URL.format(api='user/locations')
    API_GROUPS = API_URL.format(api='locations/{location}/groups')
    API_DEVICES = API_URL.format(api='locations/{location}/abstract_devices')
    API_DEVICE_STATE = API_URL.format(api='devices/{pid}/state')
    API_GROUP_STATE = API_URL.format(api='groups/{pid}/state')

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

    def get_group_state(self, pid):
        headers = {'Authorization': 'Token {}'.format(self._auth_token)}
        r = requests.get(self.API_GROUP_STATE.format(pid=pid),
                         headers=headers,
                         timeout=API_TIMEOUT)
        return r.json()['state']

    def get_device_state(self, pid):
        headers = {'Authorization': 'Token {}'.format(self._auth_token)}
        r = requests.get(self.API_DEVICE_STATE.format(pid=pid),
                         headers=headers,
                         timeout=API_TIMEOUT)
        return r.json()['state']
