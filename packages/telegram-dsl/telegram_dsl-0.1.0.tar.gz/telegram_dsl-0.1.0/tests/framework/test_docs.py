from telegram_dsl.framework.docs import generate_reference
from telegram_dsl.framework.handlers import command_handler
from telegram_dsl.framework import outputs


def test_generate_reference(clean_handler_registry):
    @command_handler(add_to_commands=True)
    async def hello(args, user):
        return outputs.text("ok")

    ref = generate_reference()
    assert ref["commands"]
    assert ref["handlers"]
