import pytest

from telegram_dsl.internal.engine.middleware import apply_middleware_stack
from telegram_dsl.framework import outputs
from telegram_dsl.internal.middleware import hooks


@pytest.mark.asyncio
async def test_middleware_order(clean_handler_registry):
    calls = []

    @hooks.register_global_middleware
    async def mw1(update, context, next):
        calls.append("mw1")
        return await next(update, context)

    @hooks.register_global_middleware
    async def mw2(update, context, next):
        calls.append("mw2")
        return await next(update, context)

    async def handler(args, user):
        calls.append(f"handler:{args}")
        return outputs.text("ok")

    update = type(
        "U",
        (),
        {
            "effective_user": type("U2", (), {"id": 1})(),
            "effective_message": type("M", (), {"text": "hi"})(),
        },
    )()
    context = type("C", (), {"args": []})()

    result = await apply_middleware_stack(handler, update, context)
    assert result.method == "send_message"
    assert calls == ["mw1", "mw2", "handler:hi"]


@pytest.mark.asyncio
async def test_extract_args_from_context(clean_handler_registry):
    async def handler(args, user):
        return outputs.text(args)

    entity = type("E", (), {"type": "bot_command", "offset": 0, "length": 5})()
    message = type("M", (), {"text": "/test one two", "entities": [entity]})()
    update = type(
        "U",
        (),
        {"effective_user": type("U2", (), {"id": 1})(), "effective_message": message},
    )()
    context = type("C", (), {"args": ["one", "two"]})()

    result = await apply_middleware_stack(handler, update, context)
    assert result.kwargs["text"] == "one two"


@pytest.mark.asyncio
async def test_extract_args_from_prefix_context(clean_handler_registry):
    async def handler(args, user):
        return outputs.text(args)

    message = type("M", (), {"text": "!forecast Rome", "entities": []})()
    update = type(
        "U",
        (),
        {"effective_user": type("U2", (), {"id": 1})(), "effective_message": message},
    )()
    context = type("C", (), {"args": ["Rome"]})()

    result = await apply_middleware_stack(handler, update, context)
    assert result.kwargs["text"] == "Rome"


@pytest.mark.asyncio
async def test_extract_args_from_callback(clean_handler_registry):
    async def handler(args, user):
        return outputs.text(args)

    update = type(
        "U",
        (),
        {
            "effective_user": type("U2", (), {"id": 1})(),
            "effective_message": None,
            "callback_query": type("Cq", (), {"data": "payload"})(),
        },
    )()
    context = type("C", (), {"args": []})()

    result = await apply_middleware_stack(handler, update, context)
    assert result.kwargs["text"] == "payload"


@pytest.mark.asyncio
async def test_middleware_short_circuit(clean_handler_registry):
    calls = []

    @hooks.register_global_middleware
    async def mw1(update, context, next):
        calls.append("mw1")
        return outputs.text("stopped")

    async def handler(args, user):
        calls.append("handler")
        return outputs.text("ok")

    update = type(
        "U",
        (),
        {"effective_user": type("U2", (), {"id": 1})(), "effective_message": None},
    )()
    context = type("C", (), {"args": []})()

    result = await apply_middleware_stack(handler, update, context)
    assert result.kwargs["text"] == "stopped"
    assert calls == ["mw1"]


@pytest.mark.asyncio
async def test_handler_receives_update_context(clean_handler_registry):
    async def handler(args, user, payload, update, context):
        return (
            args,
            user.id,
            payload.message_text,
            update.effective_chat.id,
            bool(context),
        )

    update = type(
        "U",
        (),
        {
            "effective_user": type("U2", (), {"id": 7})(),
            "effective_chat": type("C", (), {"id": 55})(),
            "effective_message": type("M", (), {"text": "hi"})(),
        },
    )()
    context = type("C", (), {"args": []})()

    result = await apply_middleware_stack(handler, update, context)
    assert result == ("hi", 7, "hi", 55, True)
