from telegram_dsl.flow.states import register_entry_point, register_state
from telegram_dsl.framework import outputs
from telegram_dsl.internal.handlers import map as handler_map
from telegram_dsl.internal.handlers import states as state_registry


class DummyHandler:
    def __init__(self, callback):
        self.callback = callback


def test_register_state_immediate(clean_handler_registry):
    def func():
        return outputs.text("ok")

    handler = DummyHandler(func)
    handler_map.add_handler_entry(func, func, handler, {})
    register_state("G", 1)(func)

    handlers = state_registry.get_state_handlers("G")[1]
    assert handlers == [handler]


def test_register_state_lazy(clean_handler_registry):
    def func():
        return outputs.text("ok")

    register_state("G", 2)(func)
    assert state_registry._lazy_state_registrations

    handler = DummyHandler(func)
    handler_map.add_handler_entry(func, func, handler, {})
    state_registry.trigger_lazy_state_registrations()

    handlers = state_registry.get_state_handlers("G")[2]
    assert handlers == [handler]


def test_register_entry_point(clean_handler_registry):
    def func():
        return outputs.text("ok")

    handler = DummyHandler(func)
    handler_map.add_handler_entry(func, func, handler, {})
    register_entry_point("G")(func)

    entry_points = state_registry.get_conversation_entry_points("G")
    assert entry_points == [handler]


def test_get_conversation_states_excludes_entry(clean_handler_registry):
    def func0():
        return outputs.text("ok")

    def func1():
        return outputs.text("ok")

    handler0 = DummyHandler(func0)
    handler1 = DummyHandler(func1)
    handler_map.add_handler_entry(func0, func0, handler0, {})
    handler_map.add_handler_entry(func1, func1, handler1, {})
    register_entry_point("G")(func0)
    register_state("G", 1)(func1)

    states = state_registry.get_conversation_states("G")
    assert 0 not in states
    assert states[1] == [handler1]
