import pytest

from telegram_dsl.framework.actions import Action
from telegram_dsl.framework.responses import action_responder


class BotWithAny:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        async def _method(**kwargs):
            self.calls.append((name, kwargs))

        return _method


class MessageWithAny:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        async def _method(**kwargs):
            self.calls.append((name, kwargs))

        return _method


class Update:
    def __init__(self, message=True):
        self.effective_message = MessageWithAny() if message else None
        self.effective_chat = type("C", (), {"id": 42})()


class Context:
    def __init__(self):
        self.bot = BotWithAny()


@pytest.mark.asyncio
async def test_action_dispatches_to_message_method():
    update = Update(message=True)
    context = Context()
    act = Action("edit_message_text", {"text": "hi"})
    await action_responder(update, context, act)
    assert update.effective_message.calls[0][0] == "edit_text"


@pytest.mark.asyncio
async def test_action_dispatches_to_bot_method_and_injects_chat_id():
    update = Update(message=False)
    context = Context()
    act = Action("send_message", {"text": "hi"})
    await action_responder(update, context, act)
    name, kwargs = context.bot.calls[0]
    assert name == "send_message"
    assert kwargs["chat_id"] == 42
