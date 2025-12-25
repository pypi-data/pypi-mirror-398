import pytest

from telegram_dsl.framework.handlers import buttons_handler
from telegram_dsl.framework import outputs


class _Msg:
    def __init__(self):
        self.edits = []
        self.replies = []

    async def reply_text(self, *args, **kwargs):
        self.replies.append((args, kwargs))

    async def edit_reply_markup(self, **kwargs):
        self.edits.append(kwargs)


class _CallbackQuery:
    def __init__(self, message):
        self.message = message
        self.answered = 0

    async def answer(self, *args, **kwargs):
        self.answered += 1


class _Update:
    def __init__(self, message):
        self.effective_message = message
        self.callback_query = _CallbackQuery(message)
        self.effective_user = type("U", (), {"id": 1})()


class _Context:
    def __init__(self):
        self.args = []
        self.bot = type("B", (), {})()


@pytest.mark.asyncio
async def test_callback_handler_auto_hides_buttons(clean_handler_registry):
    @buttons_handler()
    async def on_cb(args, user):
        return outputs.text("ok")

    update = _Update(_Msg())
    ctx = _Context()
    await on_cb(update, ctx)

    assert update.callback_query.answered == 1
    assert update.callback_query.message.edits == [{"reply_markup": None}]
