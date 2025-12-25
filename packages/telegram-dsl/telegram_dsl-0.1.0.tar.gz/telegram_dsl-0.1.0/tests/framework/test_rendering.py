from telegram import InlineKeyboardMarkup, InlineKeyboardButton, InputFile

from telegram_dsl.framework import rendering
from telegram_dsl.framework.actions import Action, ActionGroup
from telegram_dsl.internal.constants import RESPONSE_TYPE
from telegram_dsl.internal.engine.rendering import infer_response_type


def test_render_dict():
    assert rendering.render_dict({"a": 1, "b": 2}) == "a: 1\nb: 2"


def test_render_string():
    assert rendering.render_string("hi") == "hi"


def test_render_markup():
    markup = InlineKeyboardMarkup([[InlineKeyboardButton("Ok", callback_data="ok")]])
    rendered = rendering.render_markup(markup)
    assert rendered["reply_markup"] is markup


def test_render_list():
    assert rendering.render_list(["a", "b"]) == "a\nb"


def test_render_error():
    err = ValueError("nope")
    assert rendering.render_error(err) == "Error: nope"


def test_render_none():
    assert rendering.render_none(None) == "No content."


def test_render_bytes():
    rendered = rendering.render_bytes(b"data")
    assert isinstance(rendered, InputFile)


def test_render_number():
    assert rendering.render_number(7) == "7"


def test_action_rendering_type():
    act = Action("send_message", {"text": "hi"})
    group = ActionGroup.of([act])
    assert infer_response_type(act) == RESPONSE_TYPE.ACTION
    assert infer_response_type(group) == RESPONSE_TYPE.ACTION
