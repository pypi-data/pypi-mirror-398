from typing import Any, Dict, Optional

async def get_stats_daily_tx_fee(self, params: Optional[Dict] = None) -> Any:
    path = "/stats/dailyTxFee"
    return await self._do_request_async("GET", path, params=params)

def get_stats_daily_tx_fee_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/stats/dailyTxFee"
    return self._do_request_sync("GET", path, params=params)
