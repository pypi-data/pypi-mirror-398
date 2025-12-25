import pytest
import respx
import httpx

from cardanoscan import Cardanoscan


class TestAddressBalance:

    @pytest.fixture(autouse=True)
    def setup(self, client: Cardanoscan):
        self.client = client
        self.params = {
            "address": "addr1qxmj3a04rlp95k7428zznkq5ha4ccxwtf5gxught8ykh68l5pfacpmrk44mrauz57eak8m0aes2ywykct2puns9dzj7swe9z76",
        }
        self.mock_response = {
            "hash": "01b728f5f51fc25a5bd551c429d814bf6b8c19cb4d106e22eb392d7d1ff40a7b80ec76ad763ef054f67b63edfdcc144712d85a83c9c0ad14bd",
            "balance": 10000000,
        }

    # ---- Sync ----
    @respx.mock
    def test_get_address_balance_sync(self):
        respx.get(f"{self.client.base_url}/address/balance", params=self.params).mock(
            return_value=httpx.Response(200, json=self.mock_response)
        )

        data = self.client.get_address_balance_sync(params=self.params)
        assert data["hash"] == self.mock_response["hash"]
        assert data["balance"] == self.mock_response["balance"]

    # ---- Async ----
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_address_balance_async(self):
        respx.get(f"{self.client.base_url}/address/balance", params=self.params).mock(
            return_value=httpx.Response(200, json=self.mock_response)
        )

        data = await self.client.get_address_balance(params=self.params)
        assert data["hash"] == self.mock_response["hash"]
        assert data["balance"] == self.mock_response["balance"]
