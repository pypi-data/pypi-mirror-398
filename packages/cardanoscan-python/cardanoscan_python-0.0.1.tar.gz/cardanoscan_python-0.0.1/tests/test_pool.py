import pytest
import respx
import httpx

from cardanoscan import Cardanoscan


@pytest.fixture(autouse=True)
def setup(client: Cardanoscan):
    return client


@respx.mock
def test_get_pool_details(client):
    params = {"pool_id": "pool123"}
    mock_response = {"poolId": "pool123", "status": True, "ticker": "POOL"}

    respx.get(f"{client.base_url}/pool", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_pool_details_sync(params=params)

    assert data["poolId"] == mock_response["poolId"]
    assert data["status"] == mock_response["status"]


@respx.mock
def test_get_pool_stats(client):
    params = {"pool_id": "pool123"}
    mock_response = {
        "poolId": "pool123",
        "lifetimeBlocks": 1000,
        "currentEpochBlocks": 20,
    }

    respx.get(f"{client.base_url}/pool/stats", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_pool_stats_sync(params=params)

    assert data["poolId"] == "pool123"
    assert data["lifetimeBlocks"] == 1000


@respx.mock
def test_get_pools(client):
    params = {"page_no": 1, "limit": 10}
    mock_response = {
        "pageNo": 1,
        "limit": 10,
        "count": 1,
        "pools": [{"poolId": "pool123"}],
    }

    respx.get(f"{client.base_url}/pool/list", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_pools_sync(params=params)

    assert data["count"] == 1
    assert data["pools"][0]["poolId"] == "pool123"


@respx.mock
def test_get_expiring_pools(client):
    params = {"epoch": 450}
    mock_response = {
        "count": 1,
        "pageNo": 1,
        "limit": 10,
        "pools": [{"poolId": "pool123", "epoch": 450}],
    }

    respx.get(f"{client.base_url}/pool/list/expiring", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_expiring_pools_sync(params=params)

    assert data["pools"][0]["epoch"] == 450


@respx.mock
def test_get_expired_pools(client):
    params = {"epoch": 400}
    mock_response = {
        "count": 1,
        "pageNo": 1,
        "limit": 10,
        "pools": [{"poolId": "poolXYZ", "epoch": 400}],
    }

    respx.get(f"{client.base_url}/pool/list/expired", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_expired_pools_sync(params=params)

    assert data["pools"][0]["poolId"] == "poolXYZ"
    assert data["pools"][0]["epoch"] == 400
