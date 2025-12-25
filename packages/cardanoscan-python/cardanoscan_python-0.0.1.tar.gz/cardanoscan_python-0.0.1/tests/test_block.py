import pytest
import respx
import httpx

from cardanoscan import Cardanoscan


@pytest.fixture(autouse=True)
def setup(client: Cardanoscan):
    return client


@respx.mock
def test_get_block_details(client):
    params = {"block_hash": "abcd1234"}
    mock_response = {"hash": "abcd1234", "blockHeight": 999999, "epoch": 410}

    respx.get(f"{client.base_url}/block", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_block_details_sync(params=params)
    assert data["hash"] == mock_response["hash"]
    assert data["blockHeight"] == mock_response["blockHeight"]


@respx.mock
def test_get_latest_block_details(client):
    mock_response = {"hash": "latest123", "blockHeight": 1200000}

    respx.get(f"{client.base_url}/block/latest").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_latest_block_details_sync()
    assert data["hash"] == mock_response["hash"]
    assert data["blockHeight"] == mock_response["blockHeight"]
