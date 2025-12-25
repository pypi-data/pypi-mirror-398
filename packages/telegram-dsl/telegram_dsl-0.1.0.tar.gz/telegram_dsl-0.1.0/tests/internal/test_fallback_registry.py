from telegram_dsl.internal.handlers import fallback
from telegram_dsl.framework import outputs


def test_fallback_default(clean_handler_registry):
    assert fallback.get_fallback() is None


def test_fallback_group(clean_handler_registry):
    @fallback.register_fallback(group="G")
    def handler():
        return outputs.text("ok")

    assert fallback.get_fallback("G") is handler
    assert fallback.get_fallback("missing") is None
