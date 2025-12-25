import datetime as dt
import pytest

from telegram import Bot, Update

from telegram_dsl.internal.engine.middleware import apply_middleware_stack


def _make_bot():
    return Bot(token="123:TEST")


def _message_update_dict(text="hi"):
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": int(dt.datetime.now().timestamp()),
            "chat": {"id": 123, "type": "private"},
            "from": {"id": 1, "is_bot": False, "first_name": "T"},
            "text": text,
        },
    }


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


@pytest.mark.asyncio
async def test_extract_args_from_real_message_update(dummy_context):
    async def greet(args, user):
        return args

    update = Update.de_json(_message_update_dict("hello"), _make_bot())
    result = await apply_middleware_stack(greet, update, dummy_context)
    assert result == "hello"


@pytest.mark.asyncio
async def test_extract_args_from_real_callback_update(dummy_context):
    async def greet(args, user):
        return args

    update = Update.de_json(_callback_update_dict("payload"), _make_bot())
    result = await apply_middleware_stack(greet, update, dummy_context)
    assert result == "payload"
