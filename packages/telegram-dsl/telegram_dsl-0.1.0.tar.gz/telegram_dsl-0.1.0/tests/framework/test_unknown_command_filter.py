import importlib

import pytest
from telegram import Bot, Update

from telegram_dsl.internal.handlers import map as handler_map


@pytest.mark.asyncio
async def test_unknown_command_filter_does_not_match_plain_text(clean_handler_registry):
    importlib.import_module("telegram_dsl.framework.handlers")
    from telegram_dsl.framework.handlers import unknown_command_handler
    from telegram_dsl.framework import outputs

    @unknown_command_handler()
    async def unknown_command(args, user):
        return outputs.text("unknown")

    handler = handler_map.get_handler(unknown_command)
    bot = Bot(token="123:TEST")

    plain = Update.de_json(
        {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "date": 0,
                "chat": {"id": 1, "type": "private"},
                "from": {"id": 1, "is_bot": False, "first_name": "T"},
                "text": "hello",
                "entities": [],
            },
        },
        bot,
    )
    slash = Update.de_json(
        {
            "update_id": 2,
            "message": {
                "message_id": 2,
                "date": 0,
                "chat": {"id": 1, "type": "private"},
                "from": {"id": 1, "is_bot": False, "first_name": "T"},
                "text": "/not_a_command",
                "entities": [],
            },
        },
        bot,
    )

    assert bool(handler.check_update(plain)) is False
    assert bool(handler.check_update(slash)) is True
