import pytest

from telegram_dsl.framework import outputs
from telegram_dsl.framework.responses import action_responder


@pytest.mark.asyncio
async def test_long_text_splits_and_sends_multiple_messages(
    dummy_update, dummy_context
):
    text = ("a" * 5000) + "\n" + ("b" * 5000)
    action_group = outputs.long_text(text, chunk_size=3800)

    await action_responder(dummy_update, dummy_context, action_group)

    calls = dummy_update.effective_message.calls
    assert len(calls) >= 3
    for name, _args, kwargs in calls:
        assert name == "reply_text"
        assert len(kwargs.get("text", "")) <= 3800
