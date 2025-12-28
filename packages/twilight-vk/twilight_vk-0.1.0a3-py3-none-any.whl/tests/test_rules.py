import pytest

from twilight_vk.framework.rules import *
from twilight_vk.framework.handlers.event_handlers import DEFAULT_HANDLER

@pytest.fixture()
def fake_event():
    return {
        "group_id": 123,
        "type": "message_new",
        "object": {
            "client_info": {},
            "message": {
                "from_id": 1234,
                "id": 1,
                "fwd_messages": [],
                "attachments": [],
                "conversation_message_id": 1,
                "text": "",
                "peer_id": 2000000001
            }
        }
    }

@pytest.fixture()
def messages_list():
    return {
        "messages": [
            "test",
            "test darky",
            "test test",
            "test [club123|@club123]",
            "[club123|@club123]",
            "[club123|@club123] test",
            "test [id1234|@id1234]",
            "[id1234|@id1234]",
            "[id1234|@id1234] test",
            "darky",
            "test [club123|@club123] [id1234|@id1234] darky"
        ],
        "replies": [
            None,
            {"test": "message"},
            None,
            None,
            {"test": "message"},
            None,
            None,
            {"test": "message"},
            None,
            None,
            {"test": "message"}
        ],
        "fwds": [
            [],
            [],
            [{"test": "message"}],
            [],
            [],
            [{"test": "message"}],
            [],
            [],
            [{"test": "message"}],
            [],
            []
        ],
        "actions": [
            None,
            {"type": "chat_invite_user", "member_id": 1234},
            {"type": "chat_invite_user", "member_id": -123},
            None,
            {"type": "chat_invite_user", "member_id": 1234},
            {"type": "chat_invite_user", "member_id": -123},
            None,
            {"type": "chat_invite_user", "member_id": 123},
            {"type": "chat_invite_user", "member_id": -123},
            None,
            {"type": "chat_invite_user", "member_id": 123}
        ]
    }

@pytest.fixture()
def results():
    return [
        [True, False, {"triggers": ["test"]}, True, False, False, False, False, False, False, True, False, False],
        [True, False, {"triggers": ["test", "darky"]}, True, {"variable": "darky"}, False, False, True, False, False, True, True, False],
        [True, False, {"triggers": ["test"]}, False, {"variable": "test"}, False, False, False, True, False, True, True, True],
        [True, False, {"triggers": ["test"]}, False, {"variable": "[club123|@club123]"}, {"mentions": [{"type": "club", "id": 123, "screen_name": "club123", "text": "@club123"}]}, True, False, False, False, True, False, False],
        [True, False, False, False, False, {"mentions": [{"type": "club", "id": 123, "screen_name": "club123", "text": "@club123"}]}, True, True, False, False, True, True, False],
        [True, False, {"triggers": ["test"]}, False, False, {"mentions": [{"type": "club", "id": 123, "screen_name": "club123", "text": "@club123"}]}, True, False, True, False, True, True, True],
        [True, False, {"triggers": ["test"]}, False, {"variable": "[id1234|@id1234]"}, {"mentions": [{"type": "id", "id": 1234, "screen_name": "id1234", "text": "@id1234"}]}, False, False, False, False, True, False, False],
        [True, False, False, False, False, {"mentions": [{"type": "id", "id": 1234, "screen_name": "id1234", "text": "@id1234"}]}, False, True, False, False, True, True, False],
        [True, False, {"triggers": ["test"]}, False, False, {"mentions": [{"type": "id", "id": 1234, "screen_name": "id1234", "text": "@id1234"}]}, False, False, True, False, True, True, True],
        [True, False, {"triggers": ["darky"]}, False, False, False, False, False, False, False, True, False, False],
        [True, False, {"triggers": ["test", "darky"]}, False, {"variable": "[club123|@club123] [id1234|@id1234] darky"}, {"mentions": [{"type": "club", "id": 123, "screen_name": "club123", "text": "@club123"}, {"type": "id", "id": 1234, "screen_name": "id1234", "text": "@id1234"}]}, True, True, False, False, True, True, False]
    ]

@pytest.fixture
def handler_results():
    return [
        {"triggers": ["test"]},
        {
            "triggers": ["test", "darky"],
            "variable": "darky"
        },
        {
            "triggers": ["test"],
            "variable": "test"
        },
        {
            "triggers": ["test"],
            "variable": "[club123|@club123]",
            "mentions": [{"type": "club", "id": 123, "screen_name": "club123", "text": "@club123"}]
        },
        {"mentions": [{"type": "club", "id": 123, "screen_name": "club123", "text": "@club123"}]},
        {
            "triggers": ["test"],
            "mentions": [{"type": "club", "id": 123, "screen_name": "club123", "text": "@club123"}]
        },
        {
            "triggers": ["test"],
            "variable": "[id1234|@id1234]",
            "mentions": [{"type": "id", "id": 1234, "screen_name": "id1234", "text": "@id1234"}]
        },
        {"mentions": [{"type": "id", "id": 1234, "screen_name": "id1234", "text": "@id1234"}]},
        {
            "triggers": ["test"],
            "mentions": [{"type": "id", "id": 1234, "screen_name": "id1234", "text": "@id1234"}]
        },
        {"triggers": ["darky"]},
        {
            "triggers": ["test", "darky"],
            "variable": "[club123|@club123] [id1234|@id1234] darky",
            "mentions": [{"type": "club", "id": 123, "screen_name": "club123", "text": "@club123"}, 
                         {"type": "id", "id": 1234, "screen_name": "id1234", "text": "@id1234"}]
        }
    ]

class MockVkMethods:

    def __init__(self):
        pass
    
    class messages():
        async def getConversationMembers(peer_id):
            return {
                "response": {
                    "items": [
                        {
                            "member_id": 1234
                        },
                        {
                            "member_id": -123,
                            "is_admin": True
                        }
                    ]
                }
            }
        
@pytest.fixture()
def rules_list():
    rules_lst: list[BaseRule] = [
        TrueRule(),
        FalseRule(),
        ContainsRule(triggers=["test", "darky"], ignore_case=True),
        TextRule(value=["test", "test darky"], ignore_case=True),
        TwiMLRule(value=["test <variable>"], ignore_case=True),
        MentionRule(),
        IsMentionedRule(),
        ReplyRule(),
        ForwardRule(),
        AdminRule(),
        IsAdminRule(),
        InvitedRule(),
        IsInvitedRule()
    ]
    all_rules = []
    for rule in rules_lst:
        rule.methods = MockVkMethods()
        all_rules.append(rule)
    return all_rules

@pytest.mark.asyncio
async def test_rules(fake_event: dict, messages_list: list, results: list, rules_list: list[BaseRule]):
    for test in range(len(messages_list["messages"])):
        fake_event["object"]["message"]["text"] = messages_list["messages"][test]
        fake_event["object"]["message"]["reply_message"] = messages_list["replies"][test]
        if fake_event["object"]["message"]["reply_message"] == None:
            fake_event["object"]["message"].__delitem__("reply_message")
        fake_event["object"]["message"]["fwd_messages"] = messages_list["fwds"][test]
        fake_event["object"]["message"]["action"] = messages_list["actions"][test]
        if fake_event["object"]["message"]["action"] == None:
            fake_event["object"]["message"].__delitem__("action")
        rule_results = [await rule.__check__(fake_event) for rule in rules_list]
        assert rule_results == results[test]

@pytest.mark.asyncio
async def test_handlerinput(fake_event: dict, messages_list: list, results: list, rules_list: list[BaseRule], handler_results: list):
    for test in range(len(messages_list["messages"])):
        fake_event["object"]["message"]["text"] = messages_list["messages"][test]
        rule_results = [await rule.__check__(fake_event) for rule in rules_list]
        handler_result = await DEFAULT_HANDLER(MockVkMethods()).__extractArgs__(rule_results)
        assert handler_result == handler_results[test]