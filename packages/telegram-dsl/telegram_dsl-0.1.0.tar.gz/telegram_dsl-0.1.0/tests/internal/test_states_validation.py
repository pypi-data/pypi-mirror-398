import pytest

from telegram.ext import MessageHandler, filters

from telegram_dsl.internal.handlers.validation import validate_conversation


def test_validate_conversation_rejects_duplicate_handler_types():
    handlers = {
        1: [
            MessageHandler(filters.TEXT, lambda u, c: None),
            MessageHandler(filters.TEXT, lambda u, c: None),
        ]
    }
    with pytest.raises(ValueError):
        validate_conversation(
            "TEST",
            entry_points=[MessageHandler(filters.TEXT, lambda u, c: None)],
            states=handlers,
        )


def test_validate_conversation_allows_different_handler_types():
    handlers = {
        1: [
            MessageHandler(filters.TEXT, lambda u, c: None),
            MessageHandler(filters.PHOTO, lambda u, c: None),
        ]
    }
    validate_conversation(
        "TEST",
        entry_points=[MessageHandler(filters.TEXT, lambda u, c: None)],
        states=handlers,
    )


def test_validate_conversation_rejects_overlapping_filters():
    handlers = {
        1: [
            MessageHandler(filters.TEXT, lambda u, c: None),
            MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: None),
        ]
    }
    with pytest.raises(ValueError):
        validate_conversation(
            "TEST",
            entry_points=[MessageHandler(filters.TEXT, lambda u, c: None)],
            states=handlers,
        )


def test_validate_conversation_error_message_is_readable():
    handlers = {1: [MessageHandler(filters.TEXT, lambda u, c: None)]}
    with pytest.raises(ValueError) as exc:
        validate_conversation("TEST", entry_points=[], states=handlers)
    assert "Conversation" in str(exc.value)
