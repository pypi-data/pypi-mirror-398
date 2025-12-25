import datetime as dt
import pytest

from telegram import Bot, Update, User
from telegram.ext import ApplicationBuilder

from telegram_dsl.framework.actions import Action
from telegram_dsl.framework import outputs
from telegram_dsl.framework.handlers import command_handler, text_handler
from telegram_dsl.internal.handlers import map as handler_map


class DummyBot(Bot):
    def __init__(self):
        super().__init__(token="123:TEST")
        self._calls = []

    async def initialize(self):
        if self._bot_user is None:
            self._bot_user = User(
                id=999, first_name="Test", is_bot=True, username="testbot"
            )
        return None

    async def shutdown(self):
        return None

    async def send_message(self, *args, **kwargs):
        self._calls.append(("send_message", args, kwargs))
        return None


def _message_update_dict(text, *, is_command=False):
    message = {
        "message_id": 1,
        "date": int(dt.datetime.now().timestamp()),
        "chat": {"id": 123, "type": "private"},
        "from": {"id": 1, "is_bot": False, "first_name": "T"},
        "text": text,
    }
    if is_command:
        message["entities"] = [
            {"type": "bot_command", "offset": 0, "length": len(text.split()[0])}
        ]
    return {"update_id": 1, "message": message}


@pytest.mark.asyncio
async def test_application_dispatch_command_action(clean_handler_registry):
    @command_handler()
    async def hello(args, user):
        return Action("send_message", {"text": "pong"})

    bot = DummyBot()
    app = ApplicationBuilder().bot(bot).build()
    handler = handler_map._get_all_entries()[-1]["handler"]
    app.add_handler(handler)

    update = Update.de_json(_message_update_dict("/hello", is_command=True), bot)

    await app.initialize()
    await app.start()
    await app.process_update(update)
    await app.stop()
    await app.shutdown()

    assert bot._calls
    assert bot._calls[0][0] == "send_message"
    assert bot._calls[0][2]["text"] == "pong"


@pytest.mark.asyncio
async def test_application_dispatch_text_reply(clean_handler_registry):
    @text_handler()
    async def echo(args, user):
        return outputs.text("hi")

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
    assert bot._calls[0][0] == "send_message"
    assert bot._calls[0][2]["text"] == "hi"
