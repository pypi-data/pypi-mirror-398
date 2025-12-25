import types
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import telegram_dsl.framework.rendering  # noqa: F401
import telegram_dsl.framework.responses  # noqa: F401

from telegram_dsl.internal.handlers import map as handler_map
from telegram_dsl.internal.handlers import states as state_registry
from telegram_dsl.internal.handlers import fallback as fallback_registry
from telegram_dsl.internal.middleware import hooks as middleware_hooks
from telegram_dsl.internal.responses import send as responder_registry
from telegram_dsl.internal.responses import matchers as renderer_registry
from telegram_dsl.internal import errors as error_registry
from telegram_dsl.internal import lifecycle as lifecycle_registry


class DummyMessage:
    def __init__(self):
        self.calls = []

    async def reply_text(self, *args, **kwargs):
        self.calls.append(("reply_text", args, kwargs))

    async def reply_photo(self, *args, **kwargs):
        self.calls.append(("reply_photo", args, kwargs))

    async def reply_document(self, *args, **kwargs):
        self.calls.append(("reply_document", args, kwargs))

    async def edit_message_text(self, *args, **kwargs):
        self.calls.append(("edit_message_text", args, kwargs))


class DummyBot:
    def __init__(self):
        self.calls = []

    async def send_message(self, *args, **kwargs):
        self.calls.append(("send_message", args, kwargs))

    async def set_my_commands(self, *args, **kwargs):
        self.calls.append(("set_my_commands", args, kwargs))


class DummyContext:
    def __init__(self, bot=None, args=None):
        self.bot = bot or DummyBot()
        self.args = args or []


class DummyUpdate:
    def __init__(self, message=None, user_id=1, chat_id=123, callback_data=None):
        self.effective_message = message
        self.effective_user = types.SimpleNamespace(id=user_id, username="tester")
        self.effective_chat = types.SimpleNamespace(id=chat_id)
        self.callback_query = (
            types.SimpleNamespace(data=callback_data) if callback_data else None
        )


@pytest.fixture
def dummy_message():
    return DummyMessage()


@pytest.fixture
def dummy_context():
    return DummyContext()


@pytest.fixture
def dummy_update(dummy_message):
    return DummyUpdate(message=dummy_message)


@pytest.fixture
def clean_handler_registry():
    handler_map.clear_registry()
    state_registry._state_registry.clear()
    state_registry._lazy_state_registrations.clear()
    fallback_registry._fallbacks.clear()
    fallback_registry._fallbacks["__global__"] = None
    middleware_hooks._global_middleware.clear()
    middleware_hooks._per_handler_middleware.clear()
    error_registry.clear_error_handlers()
    lifecycle_registry._entries.clear()
    yield
    handler_map.clear_registry()
    state_registry._state_registry.clear()
    state_registry._lazy_state_registrations.clear()
    fallback_registry._fallbacks.clear()
    fallback_registry._fallbacks["__global__"] = None
    middleware_hooks._global_middleware.clear()
    middleware_hooks._per_handler_middleware.clear()
    error_registry.clear_error_handlers()
    lifecycle_registry._entries.clear()


@pytest.fixture
def restore_renderers():
    original = list(renderer_registry._renderer_entries)
    yield
    renderer_registry._renderer_entries[:] = original


@pytest.fixture
def restore_responders():
    original = list(responder_registry._responder_entries)
    yield
    responder_registry._responder_entries[:] = original
