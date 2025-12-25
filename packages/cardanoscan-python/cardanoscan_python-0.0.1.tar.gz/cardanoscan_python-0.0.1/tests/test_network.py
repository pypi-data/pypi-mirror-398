import pytest
import respx
import httpx

from cardanoscan import Cardanoscan


@pytest.fixture(autouse=True)
def setup(client: Cardanoscan):
    return client


@respx.mock
def test_get_network_details(client):
    mock_response = {
        "circulatingSupply": "34500000000000000",
        "reserves": "10000000000000000",
        "treasury": "500000000000000",
        "liveCirculatingSupply": "34000000000000000",
    }

    respx.get(f"{client.base_url}/network/state").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_network_details_sync()
    assert data["circulatingSupply"] == mock_response["circulatingSupply"]
    assert data["reserves"] == mock_response["reserves"]
    assert data["treasury"] == mock_response["treasury"]
    assert data["liveCirculatingSupply"] == mock_response["liveCirculatingSupply"]


@respx.mock
def test_get_network_protocol_details(client):
    mock_response = {
        "minFeeA": "44",
        "minFeeB": "155381",
        "maxTxSize": "16384",
        "networkMagic": 764824073,
    }

    respx.get(f"{client.base_url}/network/protocolParams").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    data = client.get_network_protocol_details_sync()

    assert data["minFeeA"] == mock_response["minFeeA"]
    assert data["minFeeB"] == mock_response["minFeeB"]
    assert data["networkMagic"] == mock_response["networkMagic"]
