import pytest

from telegram_dsl.framework.errors import default_error_handler


@pytest.mark.asyncio
async def test_default_error_handler(dummy_update, dummy_context):
    await default_error_handler(dummy_update, dummy_context)
    assert dummy_update.effective_message.calls[0][0] == "reply_text"
