# endpoints/block.py
from typing import Any, Dict, Optional

# these functions are defined once and will be assigned as methods on the client class.
# The first argument is `self` (client instance).

async def get_address_balance(self, params: Optional[Dict] = None) -> Any:
    """
    Async method to fetch address balance
    """
    path = "/address/balance"
    return await self._do_request_async("GET", path, params=params)

def get_address_balance_sync(self, params: Optional[Dict] = None) -> Any:
    """
    Sync method to fetch address balance
    """
    path = "/address/balance"
    return self._do_request_sync("GET", path, params=params)
