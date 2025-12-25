import pytest

from telegram_dsl.framework.actions import Action, ActionGroup
from telegram_dsl.framework.responses import text_responder, action_responder
from telegram_dsl.framework.responses import (
    photo_responder,
    doc_responder,
    noop_responder,
    fallback_responder,
)


@pytest.mark.asyncio
async def test_text_responder_string(dummy_update, dummy_context):
    await text_responder(dummy_update, dummy_context, "hi")
    assert dummy_update.effective_message.calls[0][0] == "reply_text"


@pytest.mark.asyncio
async def test_text_responder_dict(dummy_update, dummy_context):
    await text_responder(dummy_update, dummy_context, {"text": "hi"})
    method, _args, kwargs = dummy_update.effective_message.calls[0]
    assert method == "reply_text"
    assert kwargs["text"] == "hi"


@pytest.mark.asyncio
async def test_action_responder_message_method(dummy_update, dummy_context):
    act = Action("reply_text", {"text": "hi"})
    await action_responder(dummy_update, dummy_context, act)
    method, _args, kwargs = dummy_update.effective_message.calls[0]
    assert method == "reply_text"
    assert kwargs["text"] == "hi"


@pytest.mark.asyncio
async def test_action_responder_bot_method(dummy_update, dummy_context):
    dummy_update = type(dummy_update)(
        message=None, chat_id=dummy_update.effective_chat.id
    )
    act = Action("send_message", {"text": "hi"})
    await action_responder(dummy_update, dummy_context, act)
    method, _args, kwargs = dummy_context.bot.calls[0]
    assert method == "send_message"
    assert kwargs["text"] == "hi"
    assert kwargs["chat_id"] == dummy_update.effective_chat.id


@pytest.mark.asyncio
async def test_action_group(dummy_update, dummy_context):
    act1 = Action("reply_text", {"text": "a"})
    act2 = Action("reply_text", {"text": "b"})
    group = ActionGroup.of([act1, act2])
    await action_responder(dummy_update, dummy_context, group)
    assert len(dummy_update.effective_message.calls) == 2


@pytest.mark.asyncio
async def test_action_noop(dummy_update, dummy_context):
    act = Action("noop", {})
    await action_responder(dummy_update, dummy_context, act)
    assert not dummy_update.effective_message.calls


@pytest.mark.asyncio
async def test_photo_responder(dummy_update, dummy_context):
    await photo_responder(dummy_update, dummy_context, "photo")
    assert dummy_update.effective_message.calls[0][0] == "reply_photo"


@pytest.mark.asyncio
async def test_doc_responder(dummy_update, dummy_context):
    await doc_responder(dummy_update, dummy_context, "doc")
    assert dummy_update.effective_message.calls[0][0] == "reply_document"


@pytest.mark.asyncio
async def test_noop_responder(dummy_update, dummy_context):
    assert await noop_responder(dummy_update, dummy_context, None) is None


@pytest.mark.asyncio
async def test_fallback_responder(dummy_update, dummy_context):
    await fallback_responder(dummy_update, dummy_context, object())
    assert dummy_update.effective_message.calls[0][0] == "reply_text"
