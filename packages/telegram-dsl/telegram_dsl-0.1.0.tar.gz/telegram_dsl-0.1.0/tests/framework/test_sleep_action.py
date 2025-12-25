import pytest

from telegram_dsl.framework import outputs, actions
from telegram_dsl.framework.responses import action_responder
from telegram_dsl.internal.engine.rendering import render_response


@pytest.mark.asyncio
async def test_outputs_sleep_action_is_noop(dummy_update, dummy_context):
    rendered = await render_response(outputs.sleep(0))
    await action_responder(dummy_update, dummy_context, rendered)
    assert dummy_context.bot.calls == []
    assert dummy_update.effective_message.calls == []


@pytest.mark.asyncio
async def test_actions_sleep_action_is_noop(dummy_update, dummy_context):
    await action_responder(dummy_update, dummy_context, actions.sleep(0))
    assert dummy_context.bot.calls == []
    assert dummy_update.effective_message.calls == []
