import pytest
import pytest_asyncio
import pytest_httpbin
from aiohttp import ClientResponse

from twilight_vk.http.async_http import Http

@pytest_asyncio.fixture
async def http_client():
    httpClient = Http(headers={"X-Test": "test"}, timeout=10)
    yield httpClient
    await httpClient.close()

@pytest.mark.asyncio
async def test_init_session(http_client):
    assert http_client.headers == {"X-Test": "test"}
    assert http_client.timeout == 10
    assert http_client.session is None

@pytest.mark.asyncio
async def test_http_get_raw(http_client: Http, httpbin):
    response = await http_client.get(
        url = f"{httpbin.url}/get",
        params = {
            "key": "value"
        },
        raw=True
    )
    assert isinstance(response, ClientResponse)
    assert response.status == 200
    assert (await response.json())["args"] == {"key": "value"}

@pytest.mark.asyncio
async def test_http_get_json(http_client: Http, httpbin):
    response = await http_client.get(
        url = f"{httpbin.url}/get",
        params = {
            "key": "value"
        },
        raw=False
    )
    assert isinstance(response, dict)
    assert response["args"] == {"key": "value"}
    assert response["headers"]["X-Test"] == "test"

@pytest.mark.asyncio
async def test_http_post_raw(http_client: Http, httpbin):
    response = await http_client.post(
        url = f"{httpbin.url}/post",
        data = {
            "key": "value"
        },
        params = {
            "test": "123"
        },
        raw=True
    )
    assert isinstance(response, ClientResponse)
    assert response.status == 200
    assert (await response.json())["json"] == {"key": "value"}
    assert (await response.json())["args"] == {"test": "123"}

@pytest.mark.asyncio
async def test_http_post_json(http_client: Http, httpbin):
    response = await http_client.post(
        url = f"{httpbin.url}/post",
        data = {
            "key": "value"
        },
        params = {
            "test": "123"
        },
        raw=False
    )
    assert isinstance(response, dict)
    assert response["json"] == {"key": "value"}
    assert response["args"] == {"test": "123"}
    assert response["headers"]["X-Test"] == "test"

@pytest.mark.asyncio
async def test_close_session(http_client: Http):
    await http_client.__getSession__()
    assert http_client.session is not None
    assert not http_client.session.closed
    await http_client.close()
    assert http_client.session is None