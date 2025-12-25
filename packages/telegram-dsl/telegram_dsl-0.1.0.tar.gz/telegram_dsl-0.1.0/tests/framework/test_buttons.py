import pytest

from telegram import InlineKeyboardMarkup

from telegram_dsl.framework import buttons


def test_inline_buttons_from_strings():
    markup = buttons.inline_buttons([["Yes"], ["No"]])
    assert isinstance(markup, InlineKeyboardMarkup)
    assert markup.inline_keyboard[0][0].text == "Yes"
    assert markup.inline_keyboard[0][0].callback_data == "Yes"


def test_inline_buttons_rejects_invalid():
    with pytest.raises(TypeError):
        buttons.inline_buttons([[123]])


def test_url_buttons():
    markup = buttons.url_buttons([[("Docs", "https://example.com")]])
    assert markup.inline_keyboard[0][0].url == "https://example.com"


def test_login_url_buttons():
    markup = buttons.login_url_buttons([[("Login", {"url": "https://example.com"})]])
    assert markup.inline_keyboard[0][0].login_url["url"] == "https://example.com"


def test_web_app_buttons():
    markup = buttons.web_app_buttons([[("Open", {"url": "https://example.com"})]])
    assert markup.inline_keyboard[0][0].web_app["url"] == "https://example.com"


def test_switch_inline_query_buttons():
    markup = buttons.switch_inline_query_buttons([[("Search", "cats")]])
    assert markup.inline_keyboard[0][0].switch_inline_query == "cats"


def test_switch_inline_query_current_chat_buttons():
    markup = buttons.switch_inline_query_current_chat_buttons([[("Search", "cats")]])
    assert markup.inline_keyboard[0][0].switch_inline_query_current_chat == "cats"


def test_switch_inline_query_chosen_chat_buttons():
    markup = buttons.switch_inline_query_chosen_chat_buttons(
        [[("Search", {"allow_user_chats": True})]]
    )
    assert markup.inline_keyboard[0][0].switch_inline_query_chosen_chat[
        "allow_user_chats"
    ]


def test_game_buttons():
    markup = buttons.game_buttons([[("Play", {"game_short_name": "demo"})]])
    assert markup.inline_keyboard[0][0].callback_game["game_short_name"] == "demo"


def test_pay_buttons():
    markup = buttons.pay_buttons([["Pay"]])
    assert markup.inline_keyboard[0][0].pay is True
