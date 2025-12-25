import pytest

from telegram_dsl.framework.handlers import (
    command_handler,
    conversation_handler,
    buttons_handler,
    text_handler,
)
from telegram_dsl.flow.states import register_entry_point, register_state
from telegram_dsl.framework import outputs
from telegram_dsl.internal.handlers.map import clear_registry


@pytest.fixture(autouse=True)
def _clear_registry():
    clear_registry()
    yield
    clear_registry()


def test_mixed_conversation_forces_per_message_false():
    group = "TEST_CONVO"

    @command_handler()
    @register_entry_point(group=group)
    async def start(args, user):
        return outputs.conversation(outputs.text("hi"), 1)

    @text_handler(group=group)
    @register_state(group=group, state_id=1)
    async def ask(args, user, payload):
        return outputs.conversation(
            outputs.buttons("pick", buttons=[["A"]]),
            2,
        )

    @buttons_handler(group=group, pattern="^A$")
    @register_state(group=group, state_id=2)
    async def choose(args, user, payload):
        return outputs.conversation(outputs.text("done"), -1)

    # Create the ConversationHandler instance via the DSL.
    @conversation_handler(group=group)
    async def flow(args, user):
        pass

    handler_instance = getattr(flow, "__wrapped_handler__", None)
    assert callable(handler_instance)

    from telegram_dsl.internal.handlers.map import get_handler

    convo = get_handler(flow)
    assert convo.__class__.__name__ == "ConversationHandler"
    assert getattr(convo, "per_message", None) is False
