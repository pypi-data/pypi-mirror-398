from typing import Any, Dict, Optional

async def get_utxo_list(self, params: Optional[Dict] = None) -> Any:
    path = "/utxo/list"
    return await self._do_request_async("GET", path, params=params)

def get_utxo_list_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/utxo/list"
    return self._do_request_sync("GET", path, params=params)
