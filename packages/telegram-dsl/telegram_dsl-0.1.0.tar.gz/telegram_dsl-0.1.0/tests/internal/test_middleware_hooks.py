import pytest

from telegram_dsl.internal.middleware import hooks
from telegram_dsl.framework import outputs
from telegram_dsl.framework.handlers import command_handler


def test_register_global_middleware(clean_handler_registry):
    @hooks.register_global_middleware
    async def global_mw(update, context, next):
        return await next(update, context)

    assert global_mw in hooks.get_global_middleware()


def test_register_per_handler_middleware(clean_handler_registry):
    async def middleware(update, context, next):
        return await next(update, context)

    @hooks.register_middleware(middleware)
    def handler():
        return outputs.text("ok")

    assert middleware in hooks.get_middleware(handler)


@pytest.mark.asyncio
async def test_register_middleware_works_with_dsl_wrappers(
    clean_handler_registry, dummy_update, dummy_context
):
    called = []

    async def middleware(update, context, next):
        called.append("mw")
        return await next(update, context)

    @hooks.register_middleware(middleware)
    @command_handler()
    async def ping(args, user):
        return outputs.text("ok")

    dummy_update.effective_message.text = "/ping"
    await ping(dummy_update, dummy_context)

    assert called == ["mw"]
