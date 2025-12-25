from typing import Any, Dict, Optional

async def get_votes_by_voter(self, params: Optional[Dict] = None) -> Any:
    path = "/votes/byVoter"
    return await self._do_request_async("GET", path, params=params)

def get_votes_by_voter_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/votes/byVoter"
    return self._do_request_sync("GET", path, params=params)


async def get_votes_by_action(self, params: Optional[Dict] = None) -> Any:
    path = "/votes/byAction"
    return await self._do_request_async("GET", path, params=params)

def get_votes_by_action_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/votes/byAction"
    return self._do_request_sync("GET", path, params=params)
