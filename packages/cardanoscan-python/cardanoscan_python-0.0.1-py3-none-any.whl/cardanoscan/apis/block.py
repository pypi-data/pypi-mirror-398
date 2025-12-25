from typing import Any, Dict, Optional

async def get_block_details(self, params: Optional[Dict] = None) -> Any:
    return await self._do_request_async("GET", "/block", params=params)

def get_block_details_sync(self, params: Optional[Dict] = None) -> Any:
    return self._do_request_sync("GET", "/block", params=params)


async def get_latest_block_details(self) -> Any:
    return await self._do_request_async("GET", "/block/latest")

def get_latest_block_details_sync(self) -> Any:
    return self._do_request_sync("GET", "/block/latest")
