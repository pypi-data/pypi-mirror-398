from telegram_dsl.framework.actions import (
    Action,
    ActionGroup,
    action,
    send_message,
    call,
    bot,
    send_photo,
    edit_message_text,
)


def test_action_with_kwargs():
    base = Action("send_message", {"text": "hi"})
    updated = base.with_kwargs(chat_id=1)
    assert updated.kwargs["chat_id"] == 1
    assert base.kwargs.get("chat_id") is None


def test_action_group():
    a1 = action("send_message", text="a")
    a2 = action("send_message", text="b")
    group = ActionGroup.of([a1, a2])
    assert group.actions == (a1, a2)


def test_send_message_helper():
    act = send_message("hello", chat_id=1)
    assert act.method == "send_message"
    assert act.kwargs["text"] == "hello"


def test_call_helper():
    act = call("send_message", text="hi")
    assert act.method == "send_message"


def test_bot_proxy():
    act = bot.send_message(text="hi")
    assert act.method == "send_message"


def test_generated_helper():
    act = send_photo(photo="x")
    assert act.method == "send_photo"


def test_edit_message_text_helper():
    act = edit_message_text(text="updated", message_id=1)
    assert act.method == "edit_message_text"
