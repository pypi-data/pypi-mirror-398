import pytest

from telegram import Bot, Update

from telegram_dsl.framework.payloads import Payload


def _callback_update_dict(data="payload"):
    return {
        "update_id": 2,
        "callback_query": {
            "id": "cq1",
            "from": {"id": 1, "is_bot": False, "first_name": "T"},
            "chat_instance": "ci",
            "data": data,
        },
    }


def _message_update_dict(text="hi @you #tag $CASH http://x.com", chat_type="private"):
    return {
        "update_id": 1,
        "message": {
            "message_id": 10,
            "date": 1,
            "chat": {"id": 123, "type": chat_type, "title": "Test Chat"},
            "from": {
                "id": 7,
                "is_bot": False,
                "first_name": "T",
                "username": "tester",
                "language_code": "en",
            },
            "text": text,
            "entities": [
                {"type": "bot_command", "offset": 0, "length": 3},
                {"type": "mention", "offset": 3, "length": 4},
                {"type": "hashtag", "offset": 8, "length": 4},
                {"type": "cashtag", "offset": 13, "length": 5},
                {"type": "url", "offset": 19, "length": 12},
            ],
            "photo": [
                {"file_id": "p1", "file_unique_id": "u1", "width": 1, "height": 1}
            ],
        },
    }


@pytest.mark.asyncio
async def test_payload_callback_data():
    update = Update.de_json(_callback_update_dict("x"), Bot(token="123:TEST"))
    payload = Payload(update)
    assert payload.callback_data == "x"
    assert payload.message_text is None


def test_payload_basic_fields():
    update = Update.de_json(_message_update_dict(), Bot(token="123:TEST"))
    payload = Payload(update)
    assert payload.chat_id == 123
    assert payload.user_id == 7
    assert payload.message_id == 10
    assert payload.message_text == "hi @you #tag $CASH http://x.com"
    assert payload.is_private_chat is True
    assert payload.is_group_chat is False
    assert payload.has_media is True
    assert payload.chat_title == "Test Chat"
    assert payload.chat_type == "private"
    assert payload.user_username == "tester"
    assert payload.user_language_code == "en"
    assert payload.user_is_bot is False
    assert payload.photo
    assert payload.command == "hi"[:3]
    assert payload.command_args == ["@you", "#tag", "$CASH", "http://x.com"]
    assert payload.command_args_quoted == ["@you", "#tag", "$CASH", "http://x.com"]
    assert payload.mentions == ["@you"]
    assert payload.hashtags == ["#tag"]
    assert payload.cashtags == ["$CASH"]
    assert payload.urls == ["http://x.com"]
    assert payload.normalized_urls == ["http://x.com"]
    assert payload.unique_urls == ["http://x.com"]
    assert payload.unique_normalized_urls == ["http://x.com"]
    assert payload.media_items
    assert payload.media_file_ids
    assert payload.entity_spans
    assert payload.entities_by_type["bot_command"][0]["text"] == "hi"
    assert payload.media_summary["count"] == 1
    assert payload.media_summary["types"] == ["photo"]


def test_payload_group_flags():
    update = Update.de_json(
        _message_update_dict(chat_type="group"), Bot(token="123:TEST")
    )
    payload = Payload(update)
    assert payload.is_group_chat is True
    assert payload.is_private_chat is False
    assert payload.is_channel is False
    assert payload.is_supergroup is False


def test_payload_channel_flags():
    update = Update.de_json(
        _message_update_dict(chat_type="channel"), Bot(token="123:TEST")
    )
    payload = Payload(update)
    assert payload.is_channel is True
    assert payload.is_group_chat is False


def test_payload_inline_query_and_poll():
    update = Update.de_json(
        {
            "update_id": 3,
            "inline_query": {
                "id": "iq",
                "from": {"id": 7, "is_bot": False, "first_name": "T"},
                "query": "hello",
                "offset": "",
            },
            "poll": {
                "id": "poll1",
                "question": "q",
                "options": [],
                "total_voter_count": 0,
                "is_closed": False,
                "is_anonymous": True,
                "type": "regular",
                "allows_multiple_answers": False,
            },
        },
        Bot(token="123:TEST"),
    )
    payload = Payload(update)
    assert payload.inline_query_text == "hello"
    assert payload.poll_id == "poll1"


def test_payload_command_args_quoted():
    update = Update.de_json(
        _message_update_dict(text='hi "new york" city'),
        Bot(token="123:TEST"),
    )
    payload = Payload(update)
    assert payload.command == "hi"
    assert payload.command_args_quoted == ["new york", "city"]


def test_payload_unique_urls():
    update = Update.de_json(
        {
            "update_id": 9,
            "message": {
                "message_id": 10,
                "date": 1,
                "chat": {"id": 123, "type": "private", "title": "Test Chat"},
                "from": {"id": 7, "is_bot": False, "first_name": "T"},
                "text": "hi http://x.com http://x.com",
                "entities": [
                    {"type": "bot_command", "offset": 0, "length": 2},
                    {"type": "url", "offset": 3, "length": 12},
                    {"type": "url", "offset": 16, "length": 12},
                ],
            },
        },
        Bot(token="123:TEST"),
    )
    payload = Payload(update)
    assert payload.urls == ["http://x.com", "http://x.com"]
    assert payload.unique_urls == ["http://x.com"]
