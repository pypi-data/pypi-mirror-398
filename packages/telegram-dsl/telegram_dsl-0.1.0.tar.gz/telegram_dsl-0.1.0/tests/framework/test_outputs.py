from telegram import InlineKeyboardMarkup

from telegram_dsl.framework import outputs
import pytest

from telegram_dsl.framework.actions import Action
from telegram_dsl.internal.engine.rendering import render_response


def test_response_model_fields():
    resp = outputs.text("hi", reply_markup="x")
    assert resp.method == "send_message"
    assert resp.kwargs["text"] == "hi"
    assert resp.kwargs["reply_markup"] == "x"
    resp2 = outputs.text("hi", keyboard="y")
    assert resp2.kwargs["reply_markup"] == "y"
    resp3 = outputs.buttons("hi", buttons=[["Yes"]])
    assert isinstance(resp3.kwargs["reply_markup"], InlineKeyboardMarkup)
    resp4 = outputs.url_buttons("hi", buttons=[[("Docs", "https://example.com")]])
    assert isinstance(resp4.kwargs["reply_markup"], InlineKeyboardMarkup)


def test_response_model_variants():
    assert outputs.photo("p").method == "send_photo"
    assert outputs.document("d").method == "send_document"
    assert outputs.video("v").method == "send_video"
    assert outputs.audio("a").method == "send_audio"
    assert outputs.voice("v").method == "send_voice"
    assert outputs.animation("a").method == "send_animation"
    assert outputs.sticker("s").method == "send_sticker"
    assert outputs.video_note("v").method == "send_video_note"
    assert outputs.edit_message_text("x").method == "edit_message_text"
    assert outputs.edit_message_caption("x").method == "edit_message_caption"
    assert outputs.edit_message_reply_markup().method == "edit_message_reply_markup"
    assert outputs.answer_callback_query().method == "answer_callback_query"
    assert outputs.answer_inline_query().method == "answer_inline_query"


def test_response_model_extra_kwargs():
    resp = outputs.location(1.0, 2.0, horizontal_accuracy=1)
    assert resp.kwargs["horizontal_accuracy"] == 1


@pytest.mark.asyncio
async def test_response_model_renders_to_action():
    resp = outputs.text("hi")
    rendered = await render_response(resp)
    assert isinstance(rendered, Action)
    assert rendered.method == "send_message"


def test_output_required_fields():
    try:
        outputs.call("send_message")
    except ValueError as exc:
        assert "send_message" in str(exc)
    else:
        assert False


def test_output_call_and_bot_proxy():
    resp = outputs.call("send_message", text="hi")
    assert resp.method == "send_message"
    resp2 = outputs.bot.send_message(text="hi")
    assert resp2.method == "send_message"


def test_output_group():
    r1 = outputs.text("a")
    r2 = outputs.send_message(text="b")
    group = outputs.group([r1, r2])
    assert len(group.actions) == 2


def test_conversation_result():
    result = outputs.conversation(outputs.text("hi"), 2)
    assert result.message.method == "send_message"
    assert result.next_state == 2
