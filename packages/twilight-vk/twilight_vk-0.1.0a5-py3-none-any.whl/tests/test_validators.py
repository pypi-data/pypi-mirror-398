import pytest
import pytest_asyncio
import pytest_httpbin
from http import HTTPStatus

from twilight_vk.http.async_http import Http
from twilight_vk.framework.validators.http_validator import HttpValidator
from twilight_vk.framework.validators.event_validator import EventValidator
from twilight_vk.framework.exceptions import (
    HttpValidationError,
    EventValidationError,
    LongPollError,
    VkApiError
)

@pytest_asyncio.fixture
async def http_client():
    httpClient = Http(headers={"X-Test": "test"}, timeout=10)
    yield httpClient
    await httpClient.close()

@pytest.fixture
def httpValidator():
    validator = HttpValidator()
    yield validator

@pytest.fixture
def eventValidator():
    validator = EventValidator()
    yield validator

class MockFakeResponse():

    def __init__(self):
        self.status = HTTPStatus.OK
        self.method = "GET"
        self.url = "https://example.com/"

@pytest.fixture
def fake_events():
    return {
        "polling_success": {
            "ts": 0,
            "updates": []
        },
        "polling_failed": {
            "failed": 3,
        },
        "request_success": {
            "response": {
                "test": 1
            }
        },
        "request_failed": {
            "error": {
                        "error_code": 1,
                        "error_msg": "Unknown error, try again later",
                        "request_params": [
                            {
                                "key": "v",
                                "value": "1.234"
                            }
                        ]
                    }
        }
    }

@pytest.mark.asyncio
async def test_httpValidator(caplog, httpbin, http_client: Http, httpValidator: HttpValidator):
    raw = await http_client.get(
        url = f"{httpbin.url}/get",
        params = {
            "key": "value"
        },
        raw=True
    )
    assert await httpValidator.__isValid__(raw) == True
    assert await httpValidator.__isSuccess__(raw) == True

    invalid_response = MockFakeResponse()
    assert await httpValidator.__isValid__(invalid_response) == False
    assert await httpValidator.__isSuccess__(invalid_response) == True
    
    notsuccess_response = raw
    notsuccess_response.status = HTTPStatus.NOT_FOUND
    assert await httpValidator.__isValid__(notsuccess_response) == True
    assert await httpValidator.__isSuccess__(notsuccess_response) == False

@pytest.mark.asyncio
async def test_eventValidator(caplog, httpbin, http_client: Http, eventValidator: EventValidator, fake_events: dict):
    success_raw = await http_client.post(
        url = f"{httpbin.url}/post",
        data = fake_events.get("polling_success"),
        raw=True
    )
    assert await eventValidator.__isJsonValid__(success_raw) == True
    assert await eventValidator.__fieldsAreValid__((await success_raw.json())["json"], eventValidator.__pollingRequiredFileds__) == True
    assert await eventValidator.__haveErrors__((await success_raw.json())["json"]) == False

    failed_raw = await http_client.post(
        url = f"{httpbin.url}/post",
        data = fake_events.get("polling_failed"),
        raw=True
    )
    assert await eventValidator.__isJsonValid__(failed_raw) == True
    assert await eventValidator.__fieldsAreValid__((await failed_raw.json())["json"], eventValidator.__pollingRequiredFileds__) == True
    with pytest.raises(LongPollError, match=f"3"):
        await eventValidator.__haveErrors__((await failed_raw.json())["json"])

    invalid_raw = await http_client.post(
        url = f"{httpbin.url}/post",
        data = {"key": "value"},
        raw=True
    )
    assert await eventValidator.__isJsonValid__(invalid_raw) == True
    assert await eventValidator.__fieldsAreValid__((await invalid_raw.json())["json"], eventValidator.__pollingRequiredFileds__) == False
    assert await eventValidator.__haveErrors__((await invalid_raw.json())["json"]) == False

    success_raw = await http_client.post(
        url = f"{httpbin.url}/post",
        data = fake_events.get("request_success"),
        raw=True
    )
    assert await eventValidator.__isJsonValid__(success_raw) == True
    assert await eventValidator.__fieldsAreValid__((await success_raw.json())["json"], eventValidator.__requiredFields__) == True
    assert await eventValidator.__haveErrors__((await success_raw.json())["json"]) == False

    failed_raw = await http_client.post(
        url = f"{httpbin.url}/post",
        data = fake_events.get("request_failed"),
        raw=True
    )
    assert await eventValidator.__isJsonValid__(failed_raw) == True
    assert await eventValidator.__fieldsAreValid__((await failed_raw.json())["json"], eventValidator.__requiredFields__) == True
    with pytest.raises(VkApiError, match="1"):
        await eventValidator.__haveErrors__((await failed_raw.json())["json"])

    invalid_raw = await http_client.post(
        url = f"{httpbin.url}/post",
        data = {"key": "value"},
        raw=True
    )
    assert await eventValidator.__isJsonValid__(invalid_raw) == True
    assert await eventValidator.__fieldsAreValid__((await invalid_raw.json())["json"], eventValidator.__requiredFields__) == False
    assert await eventValidator.__haveErrors__((await invalid_raw.json())["json"]) == False