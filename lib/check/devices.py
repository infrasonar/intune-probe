import re
from datetime import datetime
from libprobe.asset import Asset
from libprobe.exceptions import CheckException
from ..query import query_devices


_NULLABLE = ('emailAddress', 'userPrincipalName', 'wiFiMacAddress')
_MAX_ITEMS = 2000
_MAX_DEVICE_BATCHES = 1
_MAX_DEVICES = _MAX_ITEMS * _MAX_DEVICE_BATCHES
_METRICS = set((
    'deviceName',  # str
    'deviceRegistrationState',  # str
    'lastSyncDateTime',  # int
    'complianceState',  # str
    'id', 'name',  # str
    'isEncrypted',  # bool
    'operatingSystem',  # str
    'jailBroken',  # str
    'osVersion',  # str
    'emailAddress',  # str?
    'azureADDeviceId',  # str
    'userPrincipalName',  # str?
    'model',  # str
    'manufacturer',  # str
    'serialNumber',  # str
    'wiFiMacAddress',  # str?
))


def to_ts(time_str: str) -> int:
    time_str = re.sub(r'(\.\d+)', '', time_str)
    time_str = time_str.replace('Z', '+00:00')
    dt = datetime.fromisoformat(time_str)
    return int(dt.timestamp())


async def check_devices(
        asset: Asset,
        asset_config: dict,
        config: dict) -> dict:
    devices = await query_devices(asset_config)

    for device in devices:
        to_remove = set(device.keys()) - _METRICS
        for key in to_remove:
            device.pop(key)

        for key in _NULLABLE:
            if device[key] == "":
                device.pop(key)

        device['lastSyncDateTime'] = to_ts(device['lastSyncDateTime'])
        device['name'] = device.pop('id')

    if len(devices) > _MAX_DEVICES:
        raise CheckException(
            f'maximum number of devices ({_MAX_DEVICES}) reached, '
            'please contact InfraSonar support')

    state = {}
    index = 0
    while index < _MAX_DEVICE_BATCHES:
        start = index * _MAX_ITEMS
        state[f'devices{index}'] = devices[start:start + _MAX_ITEMS]
        index += 1

    return state
