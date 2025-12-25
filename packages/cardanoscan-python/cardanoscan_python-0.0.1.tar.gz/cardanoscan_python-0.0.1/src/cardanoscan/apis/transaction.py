from typing import Any, Dict, Optional

async def get_transaction_details(self, params: Optional[Dict] = None) -> Any:
    path = "/transaction"
    return await self._do_request_async("GET", path, params=params)

def get_transaction_details_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/transaction"
    return self._do_request_sync("GET", path, params=params)


async def get_transaction_list_by_address(self, params: Optional[Dict] = None) -> Any:
    path = "/transaction/list"
    return await self._do_request_async("GET", path, params=params)

def get_transaction_list_by_address_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/transaction/list"
    return self._do_request_sync("GET", path, params=params)


async def post_submit_transaction(self, params: Optional[Dict] = None) -> Any:
    path = "/transaction/submit"
    tx_body = params.get("tx") if params else None
    headers = {"Content-Type": "application/cbor"}
    return await self._do_request_async("POST", path, json=tx_body, headers=headers)

def post_submit_transaction_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/transaction/submit"
    tx_body = params.get("tx") if params else None
    headers = {"Content-Type": "application/cbor"}
    return self._do_request_sync("POST", path, json=tx_body, headers=headers)


async def get_transaction_summary(self, params: Optional[Dict] = None) -> Any:
    path = "/transaction/summary"
    return await self._do_request_async("GET", path, params=params)

def get_transaction_summary_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/transaction/summary"
    return self._do_request_sync("GET", path, params=params)
