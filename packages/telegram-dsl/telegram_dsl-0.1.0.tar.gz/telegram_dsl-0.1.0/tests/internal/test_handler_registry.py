from telegram_dsl.internal.handlers import map as handler_map


class DummyHandler:
    def __init__(self, callback):
        self.callback = callback


def test_add_get_handler(clean_handler_registry):
    def original():
        return "original"

    def wrapped():
        return "wrapped"

    handler = DummyHandler(wrapped)
    handler_map.add_handler_entry(original, wrapped, handler, {})

    assert handler_map.get_handler(original) is handler
    assert handler_map.get_handler(wrapped) is handler
    assert len(handler_map._get_all_entries()) == 1


def test_clear_registry(clean_handler_registry):
    def original():
        return "original"

    def wrapped():
        return "wrapped"

    handler_map.add_handler_entry(original, wrapped, DummyHandler(wrapped), {})
    handler_map.clear_registry()
    assert handler_map._get_all_entries() == []
