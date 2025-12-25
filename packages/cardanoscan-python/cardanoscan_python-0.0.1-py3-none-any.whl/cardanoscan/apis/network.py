from typing import Any

async def get_network_details(self) -> Any:
    return await self._do_request_async("GET", "/network/state")

def get_network_details_sync(self) -> Any:
    return self._do_request_sync("GET", "/network/state")


async def get_network_protocol_details(self) -> Any:
    return await self._do_request_async("GET", "/network/protocolParams")

def get_network_protocol_details_sync(self) -> Any:
    return self._do_request_sync("GET", "/network/protocolParams")
