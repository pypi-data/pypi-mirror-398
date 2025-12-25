from typing import Any, Dict, Optional

async def get_stake_key_details(self, params: Optional[Dict] = None) -> Any:
    path = "/rewardAccount"
    return await self._do_request_async("GET", path, params=params)

def get_stake_key_details_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/rewardAccount"
    return self._do_request_sync("GET", path, params=params)


async def get_addresses_by_stake_key(self, params: Optional[Dict] = None) -> Any:
    path = "/rewardAccount/addresses"
    return await self._do_request_async("GET", path, params=params)

def get_addresses_by_stake_key_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/rewardAccount/addresses"
    return self._do_request_sync("GET", path, params=params)
