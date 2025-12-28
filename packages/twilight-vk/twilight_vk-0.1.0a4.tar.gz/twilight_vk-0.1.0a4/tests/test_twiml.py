import pytest

from twilight_vk.utils.twiml import TwiML

@pytest.fixture
def twiml():
    twimlInstance = TwiML()
    yield twimlInstance

@pytest.fixture
def parse_dataset():
    return {
        "messages": [
            "",
            "test",
            "test 123",
            "test darky",
            "test darky 21",
            "test darky darky",
            "test darky abc efg"
        ],
        "templates": [
            "test",
            "test <user>",
            "test <user:int>",
            "test <user:word>",
            "test <user:word> <age:int>",
            "test <user> <testword:word>"
        ],
        "results": [
            [None, {}, {}, {}, {}, {}, {}],
            [None, None, {"user": "123"}, {"user": "darky"}, {"user": "darky 21"}, {"user": "darky darky"}, {"user": "darky abc efg"}],
            [None, None, {"user": 123}, None, None, None, None],
            [None, None, {"user": "123"}, {"user": "darky"}, {"user": "darky"}, {"user": "darky"}, {"user": "darky"}],
            [None, None, None, None, {"user": "darky", "age": 21}, None, None],
            [None, None, None, None, {"user": "darky", "testword": "21"}, {"user": "darky", "testword": "darky"}, {"user": "darky abc", "testword": "efg"}]
        ]
    }

@pytest.mark.asyncio
async def test_parse(twiml: TwiML, parse_dataset: dict):
    for _temp in range(6):
        twiml.update_template(parse_dataset.get("templates")[_temp])
        for _msg in range(7):
            result = await twiml.parse(parse_dataset.get("messages")[_msg])
            assert result == parse_dataset.get("results")[_temp][_msg]

@pytest.fixture
def mentions_dataset():
    return {
        "messages": [
            "",
            "test",
            "[id1|@durov]",
            "[id123|UserTest]",
            "test [id1|UserTest]",
            "[id1|UserTest] test",
            "[id1|UserTest1] [id2|UserTest2]",
            "[club1|@club1]",
            "[club123|GroupTest]",
            "test [club1|GroupTest]",
            "[club1|GroupTest] test",
            "[club1|GroupTest1] [club1|GroupTest2]",
            "[id1|User1] [club2|Group2] [id2|User2] [club1|Group1]"
        ],
        "results": [
            {"mentions": []},
            {"mentions": []},
            {"mentions": [{"type": "id", "id": 1, "screen_name": "id1", "text": "@durov"}]},
            {"mentions": [{"type": "id", "id": 123, "screen_name": "id123", "text": "UserTest"}]},
            {"mentions": [{"type": "id", "id": 1, "screen_name": "id1", "text": "UserTest"}]},
            {"mentions": [{"type": "id", "id": 1, "screen_name": "id1", "text": "UserTest"}]},
            {"mentions": [{"type": "id", "id": 1, "screen_name": "id1", "text": "UserTest1"}, {"type": "id", "id": 2, "screen_name": "id2", "text": "UserTest2"}]},
            {"mentions": [{"type": "club", "id": 1, "screen_name": "club1", "text": "@club1"}]},
            {"mentions": [{"type": "club", "id": 123, "screen_name": "club123", "text": "GroupTest"}]},
            {"mentions": [{"type": "club", "id": 1, "screen_name": "club1", "text": "GroupTest"}]},
            {"mentions": [{"type": "club", "id": 1, "screen_name": "club1", "text": "GroupTest"}]},
            {"mentions": [{"type": "club", "id": 1, "screen_name": "club1", "text": "GroupTest1"}, {"type": "club", "id": 1, "screen_name": "club1", "text": "GroupTest2"}]},
            {"mentions": [
                {"type": "id", "id": 1, "screen_name": "id1", "text": "User1"},
                {"type": "club", "id": 2, "screen_name": "club2", "text": "Group2"},
                {"type": "id", "id": 2, "screen_name": "id2", "text": "User2"},
                {"type": "club", "id": 1, "screen_name": "club1", "text": "Group1"}
            ]}
        ]
    }

@pytest.mark.asyncio
async def test_extract_mentions(twiml: TwiML, mentions_dataset: dict):
    for _msg in range(13):
        mentions = await twiml.extract_mentions(mentions_dataset.get("messages")[_msg])
        assert mentions == mentions_dataset.get("results")[_msg]