import types
import pytest

from telegram_dsl.framework import actions
from telegram_dsl.framework.responses import action_responder


class _Message:
    def __init__(self):
        self.calls = []

    async def edit_text(self, **kwargs):
        self.calls.append(("edit_text", kwargs))


@pytest.mark.asyncio
async def test_edit_message_text_strips_message_routing_kwargs():
    msg = _Message()
    update = types.SimpleNamespace(
        effective_message=msg,
        effective_chat=types.SimpleNamespace(id=123),
    )
    context = types.SimpleNamespace(bot=types.SimpleNamespace())

    await action_responder(
        update,
        context,
        actions.edit_message_text(text="hi", chat_id=123, message_id=999),
    )

    assert msg.calls == [("edit_text", {"text": "hi"})]
