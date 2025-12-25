import datetime as dt
import pytest

from telegram import Update, User, Bot
from telegram.ext import ApplicationBuilder

from telegram_dsl.flow.states import register_state
from telegram_dsl.framework.handlers import text_handler
from telegram_dsl.framework import outputs
from telegram_dsl.internal.handlers import map as handler_map


class DummyBot(Bot):
    def __init__(self):
        super().__init__(token="123:TEST")
        self._calls = []

    async def initialize(self):
        if self._bot_user is None:
            self._bot_user = User(id=999, first_name="Test", is_bot=True)
        return None

    async def shutdown(self):
        return None

    async def send_message(self, *args, **kwargs):
        self._calls.append(("send_message", args, kwargs))
        return None


def _message_update_dict(text):
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


@pytest.mark.asyncio
async def test_conversation_requires_conversation_result(clean_handler_registry):
    group = "TEST_FLOW"

    @text_handler(group=group)
    @register_state(group=group, state_id=1)
    async def bad_step(args, user):
        return "not ok"

    bot = DummyBot()
    app = ApplicationBuilder().bot(bot).build()
    handler = handler_map._get_all_entries()[-1]["handler"]
    app.add_handler(handler)

    update = Update.de_json(_message_update_dict("hi"), bot)

    await app.initialize()
    with pytest.raises(ValueError):
        await handler.callback(update, None)
    await app.shutdown()


@pytest.mark.asyncio
async def test_conversation_result_renders(clean_handler_registry):
    group = "TEST_FLOW_OK"

    @text_handler(group=group)
    @register_state(group=group, state_id=1)
    async def good_step(args, user):
        return outputs.conversation(outputs.text("ok"), 2)

    bot = DummyBot()
    app = ApplicationBuilder().bot(bot).build()
    handler = handler_map._get_all_entries()[-1]["handler"]
    app.add_handler(handler)

    update = Update.de_json(_message_update_dict("hi"), bot)

    await app.initialize()
    await app.start()
    await app.process_update(update)
    await app.stop()
    await app.shutdown()

    assert bot._calls
    assert bot._calls[0][2]["text"] == "ok"


@pytest.mark.asyncio
async def test_conversation_requires_text_output(clean_handler_registry):
    group = "TEST_FLOW_TEXT"

    @text_handler(group=group)
    @register_state(group=group, state_id=1)
    async def bad_step(args, user):
        return outputs.conversation("ok", 2)

    bot = DummyBot()
    app = ApplicationBuilder().bot(bot).build()
    handler = handler_map._get_all_entries()[-1]["handler"]
    app.add_handler(handler)

    update = Update.de_json(_message_update_dict("hi"), bot)

    await app.initialize()
    with pytest.raises(ValueError):
        await handler.callback(update, None)
    await app.shutdown()
