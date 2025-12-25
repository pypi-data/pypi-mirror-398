from typing import Any, Dict, Optional

async def get_asset_details(self, params: Optional[Dict] = None) -> Any:
    return await self._do_request_async("GET", "/asset", params=params)

def get_asset_details_sync(self, params: Optional[Dict] = None) -> Any:
    return self._do_request_sync("GET", "/asset", params=params)


async def get_assets_by_policy_id(self, params: Optional[Dict] = None) -> Any:
    return await self._do_request_async("GET", "/asset/list/byPolicyId", params=params)

def get_assets_by_policy_id_sync(self, params: Optional[Dict] = None) -> Any:
    return self._do_request_sync("GET", "/asset/list/byPolicyId", params=params)


async def get_assets_by_address(self, params: Optional[Dict] = None) -> Any:
    return await self._do_request_async("GET", "/asset/list/byAddress", params=params)

def get_assets_by_address_sync(self, params: Optional[Dict] = None) -> Any:
    return self._do_request_sync("GET", "/asset/list/byAddress", params=params)


async def get_asset_holders_by_policy_id(self, params: Optional[Dict] = None) -> Any:
    return await self._do_request_async("GET", "/asset/holders/byPolicyId", params=params)

def get_asset_holders_by_policy_id_sync(self, params: Optional[Dict] = None) -> Any:
    return self._do_request_sync("GET", "/asset/holders/byPolicyId", params=params)


async def get_asset_holders_by_asset_id(self, params: Optional[Dict] = None) -> Any:
    return await self._do_request_async("GET", "/asset/holders/byAssetId", params=params)

def get_asset_holders_by_asset_id_sync(self, params: Optional[Dict] = None) -> Any:
    return self._do_request_sync("GET", "/asset/holders/byAssetId", params=params)


async def get_assets_metadata(self, params: Optional[Dict] = None) -> Any:
    return await self._do_request_async("GET", "/asset/metadata", params=params)

def get_assets_metadata_sync(self, params: Optional[Dict] = None) -> Any:
    return self._do_request_sync("GET", "/asset/metadata", params=params)