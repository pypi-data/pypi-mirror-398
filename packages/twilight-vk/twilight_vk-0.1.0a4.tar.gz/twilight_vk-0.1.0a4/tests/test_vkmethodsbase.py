import pytest

from twilight_vk import TwilightVK

class MockFakeApiResponse:
    
    def get():
        return {
            "response": {
                "status": "ok"
            }
        }
    
@pytest.mark.asyncio
async def test_base_api_get(monkeypatch):
    bot = TwilightVK(
        ACCESS_TOKEN="123",
        GROUP_ID=123
    )

    async def fake_base_get_method(
            api_method: str,
            values: dict = {},
            headers: dict = {}
    ):
        return MockFakeApiResponse.get()
    
    monkeypatch.setattr(bot.__bot__.base_methods, "base_get_method", fake_base_get_method)
    
    assert await bot.__bot__.base_methods.base_get_method("testmethod/",
                                                          {"key": "value"},
                                                          headers={"Content-Type": "application/json"}) == MockFakeApiResponse.get()