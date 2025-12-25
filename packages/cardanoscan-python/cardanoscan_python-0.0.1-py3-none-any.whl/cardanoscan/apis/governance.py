from typing import Any, Dict, Optional

async def get_cc_hot_details(self, params: Optional[Dict] = None) -> Any:
    path = "/governance/ccHot"
    return await self._do_request_async("GET", path, params=params)

def get_cc_hot_details_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/governance/ccHot"
    return self._do_request_sync("GET", path, params=params)


async def get_cc_member_details(self, params: Optional[Dict] = None) -> Any:
    path = "/governance/ccMember"
    return await self._do_request_async("GET", path, params=params)

def get_cc_member_details_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/governance/ccMember"
    return self._do_request_sync("GET", path, params=params)


async def get_committee_information(self) -> Any:
    path = "/governance/committee"
    return await self._do_request_async("GET", path)

def get_committee_information_sync(self) -> Any:
    path = "/governance/committee"
    return self._do_request_sync("GET", path)


async def get_committee_members(self, params: Optional[Dict] = None) -> Any:
    path = "/governance/committee/members"
    return await self._do_request_async("GET", path, params=params)

def get_committee_members_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/governance/committee/members"
    return self._do_request_sync("GET", path, params=params)


async def get_drep_information(self, params: Optional[Dict] = None) -> Any:
    path = "/governance/dRep"
    return await self._do_request_async("GET", path, params=params)

def get_drep_information_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/governance/dRep"
    return self._do_request_sync("GET", path, params=params)


async def get_dreps(self, params: Optional[Dict] = None) -> Any:
    path = "/governance/dRep/list"
    return await self._do_request_async("GET", path, params=params)

def get_dreps_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/governance/dRep/list"
    return self._do_request_sync("GET", path, params=params)


async def get_governance_action(self, params: Optional[Dict] = None) -> Any:
    path = "/governance/action"
    return await self._do_request_async("GET", path, params=params)

def get_governance_action_sync(self, params: Optional[Dict] = None) -> Any:
    path = "/governance/action"
    return self._do_request_sync("GET", path, params=params)
