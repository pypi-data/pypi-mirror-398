from telegram_dsl.framework.handlers import command_handler
from telegram_dsl.framework import outputs
from telegram_dsl.internal.inspect import list_commands, list_handlers


def test_list_commands(clean_handler_registry):
    @command_handler(add_to_commands=True)
    async def hello(args, user):
        """Say hello"""
        return outputs.text("ok")

    commands = list_commands()
    assert ("hello", "Say hello") in commands


def test_list_handlers_by_group(clean_handler_registry):
    @command_handler(group="admin")
    async def admin_cmd(args, user):
        return outputs.text("ok")

    handlers = list_handlers(group="admin")
    assert handlers
    assert handlers[0]["group"] == "admin"
