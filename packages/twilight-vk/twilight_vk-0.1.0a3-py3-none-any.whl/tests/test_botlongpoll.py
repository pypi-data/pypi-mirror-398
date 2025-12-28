import pytest

import asyncio
from aiohttp import ClientResponse

from twilight_vk import *
from twilight_vk.http.async_http import Http

@pytest.fixture
def bot():
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    testBot = TwilightVK(
        ACCESS_TOKEN="123",
        GROUP_ID=123
    )
    yield testBot

class MockGetLongPollServer():

    def __init__(self, isSuccess=True):
        self.method = "GET"
        self.url = "https://fakeauth"
        self.headers = {"Content-Type": "application/json"}
        self.is_success = isSuccess

    async def json(self):
        if self.is_success:
            return {
                "response": {
                                "server": "https://fakeserverurl",
                                "key": "fakekey",
                                "ts": 123
                            }
            }
        return {
                    "error": {
                        "error_code": 5,
                        "error_msg": "User authorization failed: invalid access_token (4).",
                        "request_params": [
                            {
                                "key": "access_token",
                                "value": "123"
                            },
                            {
                                "key": "group_id",
                                "value": 123
                            },
                            {
                                "key": "v",
                                "value": "1.234"
                            }
                        ]
                    }
            }

class MockPollingEvent():

    def __init__(self,
                 event_type: str):
        self.method = "GET"
        self.url = "https://fakeapiserver"
        self.headers = {"Content-Type": "application/json"}
        self.status = 200
        self.event_type = event_type

    async def json(self):
        match self.event_type:
            case "message_typing_state":
                return {
                    "ts": 123,
                    "updates": [
                        {
                            "group_id": 123,
                            "type": "message_typing_state",
                            "event_id": "abc123",
                            "v": "1.234",
                            "object": {
                                "from_id": 123,
                                "to_id": -123,
                                "state": "typing"
                            }
                        }
                    ]
                }
            case "message_new":
                return {
                    "ts": 123,
                    "updates": [
                        {
                            "group_id": 123,
                            "type": "message_new",
                            "event_id": "abc123",
                            "v": "1.234",
                            "object": {
                                "client_info": {},
                                "message": {
                                    "date": 1000000000,
                                    "from_id": 123,
                                    "id": 1,
                                    "fwd_messages": [],
                                    "attachments": [],
                                    "conversation_message_id": 1,
                                    "text": "a",
                                    "peer_id": 2000000001,
                                    "random_id": 0
                                }
                            }
                        }
                    ]
                }
            case "failed 1":
                return {"failed": 1,
                        "ts": 30}
            case "failed 2":
                return {"failed": 2}
            case "failed 3":
                return {"failed": 3}

async def mock_polling(bot: TwilightVK, type: str, monkeypatch):
    async def fake_GetHttpEvent(
            url: str,
            params: dict = {},
            headers: dict = {},
            raw: bool = True
    ):
        fake_response = MockPollingEvent(type)
        return fake_response
    
    async def fake_typeMatch(response: ClientResponse,
                             self = bot.__bot__.httpValidator):
        return True

    monkeypatch.setattr(bot.__bot__.httpValidator, "__isValid__", fake_typeMatch)
    monkeypatch.setattr(bot.__bot__.httpClient, "get", fake_GetHttpEvent)

    return bot

@pytest.mark.asyncio
async def test_authorization(bot: TwilightVK, caplog, monkeypatch):

    async def fake_getBotLongPollServer():
        fake_response = MockGetLongPollServer(False)
        return await bot.__bot__.eventValidator.validate(fake_response)
    
    monkeypatch.setattr(bot.__bot__.vk_methods.groups, "getLongPollServer", fake_getBotLongPollServer)

    await bot.__bot__.auth()
    assert bot.__bot__.__server__ is None
    assert bot.__bot__.__key__ is None
    assert bot.__bot__.__ts__ is None
    assert "Authrization error: [5] User authorization failed: invalid access_token (4)." in caplog.text

    async def fake_getBotLongPollServer():
        fake_response = MockGetLongPollServer(True)
        return await bot.__bot__.eventValidator.validate(fake_response)
    
    monkeypatch.setattr(bot.__bot__.vk_methods.groups, "getLongPollServer", fake_getBotLongPollServer)

    await bot.__bot__.auth()
    assert bot.__bot__.__server__ is not None
    assert bot.__bot__.__key__ is not None
    assert bot.__bot__.__ts__ is not None
    assert "Authorized" in caplog.text

@pytest.mark.asyncio
async def test_polling_check_event(bot: TwilightVK, caplog, monkeypatch):
    bot = await mock_polling(bot, "message_typing_state", monkeypatch)
    assert await bot.__bot__.check_event() == await MockPollingEvent("message_typing_state").json()
    
@pytest.mark.asyncio
async def test_polling_listen(bot: TwilightVK, caplog, monkeypatch):
    bot = await mock_polling(bot, "message_new", monkeypatch)
    async for event in bot.__bot__.listen():
        assert event == await MockPollingEvent("message_new").json()
        break

@pytest.mark.asyncio
async def test_polling_failed(bot: TwilightVK, caplog, monkeypatch):

    bot._state = "ready"

    bot.should_stop()

    async def fake_getBotLongPollServer():
        fake_response = MockGetLongPollServer(True)
        return await bot.__bot__.eventValidator.validate(fake_response)
    
    monkeypatch.setattr(bot.__bot__.vk_methods.groups, "getLongPollServer", fake_getBotLongPollServer)

    failed_codes = ["1", "2", "3"]

    for code in failed_codes:
        bot = await mock_polling(bot, f"failed {code}", monkeypatch)

        await bot.__bot__.check_event()

        if code == "1":
            assert bot.__bot__.__ts__ == 30
        
    assert "The event history is outdated or has been partially lost. The application can receive events further using the new \"ts\" value from the response." in caplog.text
    assert "The key is expired. Getting new one..." in caplog.text
    assert "The information is lost. Reauthorizing..." in caplog.text

@pytest.mark.asyncio
async def test_polling_stop(bot: TwilightVK, caplog, monkeypatch):

    bot._state = "ready"
    
    bot.should_stop()
    assert "Polling will be stopped as soon as the current request will be done. Please wait" in caplog.text