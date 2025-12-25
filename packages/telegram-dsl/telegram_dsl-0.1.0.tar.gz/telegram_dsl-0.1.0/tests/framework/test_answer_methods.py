import types
import pytest

from telegram_dsl.framework import actions
from telegram_dsl.framework.responses import action_responder


class _Bot:
    def __init__(self):
        self.calls = []

    async def answer_callback_query(self, **kwargs):
        self.calls.append(("answer_callback_query", kwargs))

    async def answer_inline_query(self, **kwargs):
        self.calls.append(("answer_inline_query", kwargs))


@pytest.mark.asyncio
async def test_answer_callback_query_does_not_inject_chat_id(dummy_message):
    update = types.SimpleNamespace(
        effective_message=dummy_message,
        effective_chat=types.SimpleNamespace(id=123),
    )
    bot = _Bot()
    context = types.SimpleNamespace(bot=bot)

    await action_responder(
        update, context, actions.answer_callback_query(callback_query_id="1")
    )

    assert bot.calls == [("answer_callback_query", {"callback_query_id": "1"})]


@pytest.mark.asyncio
async def test_answer_inline_query_does_not_inject_chat_id(dummy_message):
    update = types.SimpleNamespace(
        effective_message=dummy_message,
        effective_chat=types.SimpleNamespace(id=123),
    )
    bot = _Bot()
    context = types.SimpleNamespace(bot=bot)

    await action_responder(
        update, context, actions.answer_inline_query(inline_query_id="q", results=[])
    )

    assert bot.calls == [
        ("answer_inline_query", {"inline_query_id": "q", "results": []})
    ]
