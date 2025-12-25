from typing import Any, Dict, Optional

async def get_pool_details(self, params: Optional[Dict] = None) -> Any:
    path = "/pool"
    return await self._do_request_async("GET", path, params=params)

def get_pool_details_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/pool"
    return self._do_request_sync("GET", path, params=params)


async def get_pool_stats(self, params: Optional[Dict] = None) -> Any:
    path = "/pool/stats"
    return await self._do_request_async("GET", path, params=params)

def get_pool_stats_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/pool/stats"
    return self._do_request_sync("GET", path, params=params)


async def get_pools(self, params: Optional[Dict] = None) -> Any:
    path = "/pool/list"
    return await self._do_request_async("GET", path, params=params)

def get_pools_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/pool/list"
    return self._do_request_sync("GET", path, params=params)


async def get_expiring_pools(self, params: Optional[Dict] = None) -> Any:
    path = "/pool/list/expiring"
    return await self._do_request_async("GET", path, params=params)

def get_expiring_pools_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/pool/list/expiring"
    return self._do_request_sync("GET", path, params=params)


async def get_expired_pools(self, params: Optional[Dict] = None) -> Any:
    path = "/pool/list/expired"
    return await self._do_request_async("GET", path, params=params)

def get_expired_pools_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/pool/list/expired"
    return self._do_request_sync("GET", path, params=params)
