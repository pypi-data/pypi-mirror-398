import pytest
import respx
import httpx

from cardanoscan import Cardanoscan


@pytest.fixture(autouse=True)
def setup(client: Cardanoscan):
    return client


@respx.mock
def test_get_transaction_details(client):
    params = {"hash": "txhash123"}
    mock_response = {
        "hash": "txhash123",
        "blockHash": "blockhash123",
        "fees": "200000",
        "status": True,
    }

    respx.get(f"{client.base_url}/transaction", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_transaction_details_sync(params=params)
    assert data["hash"] == mock_response["hash"]
    assert data["blockHash"] == mock_response["blockHash"]
    assert data["fees"] == mock_response["fees"]


@respx.mock
def test_get_transaction_list_by_address(client):
    params = {"address": "addr_test1xyz", "pageNo": 1, "limit": 5}
    mock_response = {
        "pageNo": 1,
        "limit": 5,
        "count": 2,
        "transactions": [
            {
                "hash": "tx1",
                "blockHash": "block1",
                "fees": "1000",
                "slot": 12345,
                "epoch": 210,
                "blockHeight": 400000,
                "index": 0,
            },
            {
                "hash": "tx2",
                "blockHash": "block2",
                "fees": "2000",
                "slot": 12346,
                "epoch": 210,
                "blockHeight": 400001,
                "index": 1,
            },
        ],
    }

    respx.get(f"{client.base_url}/transaction/list", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_transaction_list_by_address_sync(params=params)
    assert data["count"] == 2
    assert data["transactions"][0]["hash"] == "tx1"
    assert data["transactions"][1]["fees"] == "2000"


@respx.mock
def test_post_submit_transaction(client):
    params = {"tx": "01020304"}  
    respx.post(f"{client.base_url}/transaction/submit").mock(
        return_value=httpx.Response(200)
    )

    data = client.post_submit_transaction_sync(params=params)
    assert data in (None, "")


@respx.mock
def test_get_transaction_summary(client):
    params = {"hash": "txhash123"}
    mock_response = {
        "hash": "txhash123",
        "summary": [
            {
                "wallet": "wallet1",
                "amount": "1000000",
                "sentTokens": [],
                "receivedTokens": [],
            }
        ],
    }

    respx.get(f"{client.base_url}/transaction/summary", params=params).mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_transaction_summary_sync(params=params)
    assert data["hash"] == mock_response["hash"]
    assert isinstance(data["summary"], list)
    assert data["summary"][0]["wallet"] == "wallet1"
