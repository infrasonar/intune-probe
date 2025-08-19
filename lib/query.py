import asyncio
import aiohttp
import logging
from typing import Any
from libprobe.exceptions import CheckException
from .connector import get_connector
from .version import __version__


USER_AGENT = f'InfraSonarIntuneProbe/{__version__}'


async def _get_data(resp: aiohttp.ClientResponse) -> dict[str, Any]:
    try:
        # check to unpack, no matter status
        data = await resp.json()
        error = data.get('error')
        if error:
            logging.error(data)
            description = data.get('error_description') or 'no details'
            raise CheckException(f'{error}: {description}')
    except CheckException:
        raise  # re-raise check exception
    except Exception as e:
        # other exception, try raise for status first
        resp.raise_for_status()

        # success, something else...
        msg = str(e) or type(e).__name__
        raise CheckException(f'request failed: {msg}')
    else:
        return data


async def query_devices(asset_config: dict,
                        timeout: float | None = None) -> list[dict[str, Any]]:
    tenant_id = asset_config.get('tenantId')
    client_id = asset_config.get('clientId')
    client_secret = asset_config.get('secret')

    if not isinstance(tenant_id, str) or not tenant_id:
        raise CheckException('missing or invalid `tenantId` in asset config')
    if not isinstance(client_id, str) or not client_id:
        raise CheckException('missing or invalid `clientId` in asset config')
    if not isinstance(client_secret, str) or not client_secret:
        raise CheckException('missing or invalid `secret` in asset config')

    loop = asyncio.get_running_loop()
    aiohttp_timeout = aiohttp.ClientTimeout(total=timeout)

    body = {
        'grant_type': 'client_credentials',
        'scope': 'https://graph.microsoft.com/.default',
        'client_id': client_id,
        'client_secret': client_secret,
    }
    headers = {
        'User-Agent': USER_AGENT,
    }
    uri = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    async with aiohttp.ClientSession(
            timeout=aiohttp_timeout,
            connector=get_connector(loop=loop),
            headers={'User-Agent': USER_AGENT}) as session:
        async with session.post(
                uri,
                headers=headers,
                data=body,
                ssl=True) as resp:
            data = await _get_data(resp)
            access_token = data['access_token']

    devices = []
    headers['Authorization'] = f'Bearer {access_token}'
    uri = "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices"
    while uri:
        async with aiohttp.ClientSession(
                timeout=aiohttp_timeout,
                connector=get_connector(loop=loop)) as session:
            async with session.get(uri, headers=headers, ssl=True) as resp:
                data = await _get_data(resp)
                devices.extend(data['value'])
                uri = data.get('@odata.nextLink')

    return devices
