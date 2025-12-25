import pytest
import respx
import httpx

from cardanoscan import Cardanoscan


@pytest.fixture(autouse=True)
def setup(client: Cardanoscan):
    return client


@respx.mock
def test_get_stake_key_details(client):
    params = {"reward_address": "stake1u..."}
    mock_response = {
        "poolId": "pool1xyz",
        "rewardAddress": "stake1u...",
        "stake": "123456789",
        "status": True,
        "rewardsAvailable": "1000000",
        "rewardsWithdrawn": "500000",
    }

    respx.get(f"{client.base_url}/rewardAccount", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_stake_key_details_sync(params=params)
    assert data["rewardAddress"] == mock_response["rewardAddress"]
    assert data["poolId"] == mock_response["poolId"]
    assert data["rewardsAvailable"] == mock_response["rewardsAvailable"]


@respx.mock
def test_get_addresses_by_stake_key(client):
    params = {"reward_address": "stake1u..."}
    mock_response = {
        "addresses": [
            {"hash": "addr1...", "balance": "1000"},
            {"hash": "addr2...", "balance": "2500"},
        ],
        "count": 2,
        "pageNo": 1,
        "limit": 50,
    }

    respx.get(f"{client.base_url}/rewardAccount/addresses", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_addresses_by_stake_key_sync(params=params)
    assert data["count"] == 2
    assert data["addresses"][0]["hash"] == "addr1..."
    assert data["addresses"][0]["balance"] == "1000"
