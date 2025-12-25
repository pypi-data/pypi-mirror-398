# client.py
from typing import Any, Dict, Optional
import httpx
import asyncio
import logging

from .config import BaseConfig
from .exceptions import (
    TransportError,
    HTTPStatusError,
    AuthenticationError,
    RateLimitError,
    TimeoutError,
)
from .utils import safe_json, build_url


logger = logging.getLogger(__name__)


class Cardanoscan:
    def __init__(self, api_key: str):
        self._config = BaseConfig(api_key=api_key)
        self._async_client = httpx.AsyncClient(
            base_url=self._config.base_url, timeout=self._config.timeout
        )
        self._sync_client = httpx.Client(
            base_url=self._config.base_url, timeout=self._config.timeout
        )
        self._closed = False

    # lifecycle helpers
    async def aclose(self) -> None:
        if not self._closed:
            await self._async_client.aclose()
            self._sync_client.close()
            self._closed = True

    async def __aenter__(self) -> "Cardanoscan":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()

    def close(self) -> None:
        """Close both transports synchronously. Best-effort closes the async client."""
        if not self._closed:
            try:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop and loop.is_running():
                    loop.create_task(self._async_client.aclose())
                else:
                    asyncio.run(self._async_client.aclose())
            except Exception:
                logger.debug(
                    "Failed to synchronously close async client", exc_info=True
                )
            try:
                self._sync_client.close()
            except Exception:
                logger.debug("Failed to close sync client", exc_info=True)

            self._closed = True

    def __enter__(self) -> "Cardanoscan":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    @property
    def base_url(self) -> str:
        return self._config.base_url

    # core request implementations
    async def _do_request_async(
        self,
        method: str,
        path: str,
        *,
        path_params: Optional[Dict[str, str]] = None,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        path_params = path_params or {}
        url = build_url(self.base_url, path, **path_params)
        merged_headers = self._config.auth_headers()
        if headers:
            merged_headers.update(headers)
        try:
            resp = await self._async_client.request(
                method,
                url,
                params=params,
                json=json,
                headers=merged_headers,
                timeout=timeout or self._config.timeout,
            )
        except httpx.ReadTimeout:
            raise TimeoutError("Request timed out")
        except httpx.HTTPError as e:
            raise TransportError(str(e))

        if resp.status_code >= 400:
            body = safe_json(resp)
            if resp.status_code in (401, 403):
                raise AuthenticationError(body or resp.text)
            if resp.status_code == 429:
                raise RateLimitError(body or resp.text)
            raise HTTPStatusError(resp.status_code, resp.text, body)
        return safe_json(resp)

    def _do_request_sync(
        self,
        method: str,
        path: str,
        *,
        path_params: Optional[Dict[str, str]] = None,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        path_params = path_params or {}
        url = build_url(self.base_url, path, **path_params)
        merged_headers = self._config.auth_headers()
        if headers:
            merged_headers.update(headers)
        try:
            resp = self._sync_client.request(
                method,
                url,
                params=params,
                json=json,
                headers=merged_headers,
                timeout=timeout or self._config.timeout,
            )
        except httpx.ReadTimeout:
            raise TimeoutError("Request timed out")
        except httpx.HTTPError as e:
            raise TransportError(str(e))

        if resp.status_code >= 400:
            body = safe_json(resp)
            if resp.status_code in (401, 403):
                raise AuthenticationError(body or resp.text)
            if resp.status_code == 429:
                raise RateLimitError(body or resp.text)
            raise HTTPStatusError(resp.status_code, resp.text, body)
        return safe_json(resp)

    # import endpoint functions
    from .apis.address import get_address_balance, get_address_balance_sync

    from .apis.assets import (
        get_asset_details,
        get_asset_details_sync,
        get_assets_by_policy_id,
        get_assets_by_policy_id_sync,
        get_assets_by_address,
        get_assets_by_address_sync,
        get_asset_holders_by_policy_id,
        get_asset_holders_by_policy_id_sync,
        get_asset_holders_by_asset_id,
        get_asset_holders_by_asset_id_sync,
        get_assets_metadata,
        get_assets_metadata_sync,
    )

    from .apis.block import (
        get_block_details,
        get_block_details_sync,
        get_latest_block_details,
        get_latest_block_details_sync,
    )

    from .apis.governance import (
        get_cc_hot_details,
        get_cc_hot_details_sync,
        get_cc_member_details,
        get_cc_member_details_sync,
        get_committee_information,
        get_committee_information_sync,
        get_committee_members,
        get_committee_members_sync,
        get_drep_information,
        get_drep_information_sync,
        get_dreps,
        get_dreps_sync,
        get_governance_action,
        get_governance_action_sync,
    )

    from .apis.network import (
        get_network_details,
        get_network_details_sync,
        get_network_protocol_details,
        get_network_protocol_details_sync,
    )

    from .apis.pool import (
        get_pool_details,
        get_pool_details_sync,
        get_pool_stats,
        get_pool_stats_sync,
        get_pools,
        get_pools_sync,
        get_expiring_pools,
        get_expiring_pools_sync,
        get_expired_pools,
        get_expired_pools_sync,
    )

    from .apis.reward_account import (
        get_stake_key_details,
        get_stake_key_details_sync,
        get_addresses_by_stake_key,
        get_addresses_by_stake_key_sync,
    )

    from .apis.stats import (
        get_stats_daily_tx_fee,
        get_stats_daily_tx_fee_sync,
    )

    from .apis.transaction import (
        get_transaction_details,
        get_transaction_details_sync,
        get_transaction_list_by_address,
        get_transaction_list_by_address_sync,
        post_submit_transaction,
        post_submit_transaction_sync,
        get_transaction_summary,
        get_transaction_summary_sync,
    )

    from .apis.utxo import get_utxo_list, get_utxo_list_sync

    from .apis.votes import (
        get_votes_by_voter,
        get_votes_by_voter_sync,
        get_votes_by_action,
        get_votes_by_action_sync,
    )
