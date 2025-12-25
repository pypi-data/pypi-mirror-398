import pytest

from telegram_dsl.framework.handlers import command_handler
from telegram_dsl.framework import outputs
from telegram_dsl.internal.handlers import map as handler_map


@pytest.mark.asyncio
async def test_handler_wrapper_returns_state(
    clean_handler_registry, dummy_update, dummy_context
):
    @command_handler(add_to_commands=True)
    async def greet(args, user):
        return outputs.conversation(outputs.text("hello"), 2)

    handler = handler_map._get_all_entries()[-1]["handler"]
    result = await handler.callback(dummy_update, dummy_context)
    assert result == 2


@pytest.mark.asyncio
async def test_handler_wrapper_rejects_raw_string(
    clean_handler_registry, dummy_update, dummy_context
):
    @command_handler(add_to_commands=True)
    async def greet(args, user):
        return "hello"

    handler = handler_map._get_all_entries()[-1]["handler"]
    with pytest.raises(ValueError):
        await handler.callback(dummy_update, dummy_context)
