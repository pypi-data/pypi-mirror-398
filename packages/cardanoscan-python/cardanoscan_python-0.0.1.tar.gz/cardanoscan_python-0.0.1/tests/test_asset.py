import pytest
import respx
import httpx

from cardanoscan import Cardanoscan


@pytest.fixture(autouse=True)
def setup(client: Cardanoscan):
    return client


@respx.mock
def test_get_asset_details(client):
    params = {"asset": "policyid.assetname"}
    mock_response = {
        "policyId": "policyid",
        "assetName": "assetname",
        "fingerprint": "asset1xyz",
        "assetId": "policyid.assetname",
        "totalSupply": "50000000",
        "txCount": 12,
        "mintedOn": "2021-01-01T00:00:00Z",
    }

    respx.get(f"{client.base_url}/asset", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_asset_details_sync(params=params)

    assert data["assetId"] == mock_response["assetId"]
    assert data["totalSupply"] == mock_response["totalSupply"]


@respx.mock
def test_get_assets_by_policy_id(client):
    params = {"policy_id": "abcd1234"}
    mock_response = {
        "pageNo": 1,
        "limit": 10,
        "count": 2,
        "tokens": [
            {
                "policyId": "abcd1234",
                "assetName": "token1",
                "assetId": "abcd1234.token1",
                "fingerprint": "asset1aaa",
                "totalSupply": "1000",
                "txCount": 1,
                "mintedOn": "2024-01-01",
            },
            {
                "policyId": "abcd1234",
                "assetName": "token2",
                "assetId": "abcd1234.token2",
                "fingerprint": "asset1bbb",
                "totalSupply": "3000",
                "txCount": 2,
                "mintedOn": "2024-01-02",
            },
        ],
    }

    respx.get(f"{client.base_url}/asset/list/byPolicyId", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_assets_by_policy_id_sync(params=params)

    assert data["count"] == 2
    assert data["tokens"][0]["assetId"] == "abcd1234.token1"


@respx.mock
def test_get_assets_by_address(client):
    params = {"address": "addr_test1xyz"}
    mock_response = {
        "tokens": [
            {"unit": "token1", "quantity": "10"},
            {"unit": "token2", "quantity": "5"},
        ],
        "count": 2,
        "pageNo": 1,
        "limit": 10,
    }

    respx.get(f"{client.base_url}/asset/list/byAddress", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_assets_by_address_sync(params=params)

    assert data["count"] == 2
    assert data["tokens"][0]["unit"] == "token1"


@respx.mock
def test_get_asset_holders_by_policy_id(client):
    params = {"policy_id": "abcd1234"}
    mock_response = {
        "holders": [
            {"address": "addr1", "balance": "10"},
            {"address": "addr2", "balance": "20"},
        ],
        "count": 2,
        "pageNo": 1,
        "limit": 50,
    }

    respx.get(f"{client.base_url}/asset/holders/byPolicyId", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_asset_holders_by_policy_id_sync(params=params)

    assert data["count"] == 2
    assert data["holders"][0]["address"] == "addr1"


@respx.mock
def test_get_asset_holders_by_asset_id(client):
    params = {"asset_id": "policyid.token123"}
    mock_response = {
        "holders": [
            {"address": "addr1", "balance": "100"},
            {"address": "addr2", "balance": "50"},
        ],
        "count": 2,
        "pageNo": 1,
        "limit": 100,
    }

    respx.get(f"{client.base_url}/asset/holders/byAssetId", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_asset_holders_by_asset_id_sync(params=params)

    assert data["count"] == 2
    assert data["holders"][1]["balance"] == "50"
