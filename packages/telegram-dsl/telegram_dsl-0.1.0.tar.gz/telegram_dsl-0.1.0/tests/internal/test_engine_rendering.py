import pytest

from telegram_dsl.internal.engine.rendering import infer_response_type, render_response
from telegram_dsl.internal.constants import RESPONSE_TYPE
from telegram_dsl.internal.responses import matchers


class CustomType:
    def __init__(self, value):
        self.value = value


def test_infer_response_type_string():
    assert infer_response_type("hi") == RESPONSE_TYPE.TEXT


def test_infer_response_type_custom(restore_renderers):
    @matchers.register_renderer(
        request_type=CustomType, response_type=RESPONSE_TYPE.TEXT
    )
    def render_custom(content):
        return content.value

    assert infer_response_type(CustomType("ok")) == RESPONSE_TYPE.TEXT


@pytest.mark.asyncio
async def test_render_response_awaitable(restore_renderers):
    @matchers.register_renderer(
        request_type=CustomType, response_type=RESPONSE_TYPE.TEXT
    )
    def render_custom(content):
        async def _inner():
            return content.value

        return _inner()

    result = await render_response(CustomType("ok"))
    assert result == "ok"


def test_infer_response_type_unknown():
    assert infer_response_type(object()) == RESPONSE_TYPE.TEXT
