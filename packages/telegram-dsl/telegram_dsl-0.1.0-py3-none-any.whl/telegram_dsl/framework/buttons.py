from typing import Iterable, Sequence, Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def _build_markup(rows: Iterable[Sequence[Any]], builder) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[builder(item) for item in row] for row in rows])


def inline_buttons(rows: Iterable[Sequence[Any]]) -> InlineKeyboardMarkup:
    """Callback buttons where label == callback data."""

    def _button(item: Any) -> InlineKeyboardButton:
        if isinstance(item, str):
            return InlineKeyboardButton(item, callback_data=item)
        raise TypeError(f"Unsupported button spec: {item!r}")

    return _build_markup(rows, _button)


def url_buttons(rows: Iterable[Sequence[Any]]) -> InlineKeyboardMarkup:
    """URL buttons; items are (text, url) or {'text': ..., 'url': ...}."""

    def _button(item: Any) -> InlineKeyboardButton:
        if isinstance(item, dict):
            return InlineKeyboardButton(item["text"], url=item["url"])
        if isinstance(item, (tuple, list)) and len(item) == 2:
            text, url = item
            return InlineKeyboardButton(str(text), url=str(url))
        raise TypeError(f"Unsupported button spec: {item!r}")

    return _build_markup(rows, _button)


def login_url_buttons(rows: Iterable[Sequence[Any]]) -> InlineKeyboardMarkup:
    """Login URL buttons; items are (text, login_url) or {'text': ..., 'login_url': ...}."""

    def _button(item: Any) -> InlineKeyboardButton:
        if isinstance(item, dict):
            return InlineKeyboardButton(item["text"], login_url=item["login_url"])
        if isinstance(item, (tuple, list)) and len(item) == 2:
            text, login_url = item
            return InlineKeyboardButton(str(text), login_url=login_url)
        raise TypeError(f"Unsupported button spec: {item!r}")

    return _build_markup(rows, _button)


def web_app_buttons(rows: Iterable[Sequence[Any]]) -> InlineKeyboardMarkup:
    """Web app buttons; items are (text, web_app) or {'text': ..., 'web_app': ...}."""

    def _button(item: Any) -> InlineKeyboardButton:
        if isinstance(item, dict):
            return InlineKeyboardButton(item["text"], web_app=item["web_app"])
        if isinstance(item, (tuple, list)) and len(item) == 2:
            text, web_app = item
            return InlineKeyboardButton(str(text), web_app=web_app)
        raise TypeError(f"Unsupported button spec: {item!r}")

    return _build_markup(rows, _button)


def switch_inline_query_buttons(rows: Iterable[Sequence[Any]]) -> InlineKeyboardMarkup:
    """Buttons that open inline mode in another chat; items are (text, query)."""

    def _button(item: Any) -> InlineKeyboardButton:
        if isinstance(item, dict):
            return InlineKeyboardButton(
                item["text"], switch_inline_query=item["switch_inline_query"]
            )
        if isinstance(item, (tuple, list)) and len(item) == 2:
            text, query = item
            return InlineKeyboardButton(str(text), switch_inline_query=str(query))
        raise TypeError(f"Unsupported button spec: {item!r}")

    return _build_markup(rows, _button)


def switch_inline_query_current_chat_buttons(
    rows: Iterable[Sequence[Any]],
) -> InlineKeyboardMarkup:
    """Buttons that open inline mode in the current chat; items are (text, query)."""

    def _button(item: Any) -> InlineKeyboardButton:
        if isinstance(item, dict):
            return InlineKeyboardButton(
                item["text"],
                switch_inline_query_current_chat=item[
                    "switch_inline_query_current_chat"
                ],
            )
        if isinstance(item, (tuple, list)) and len(item) == 2:
            text, query = item
            return InlineKeyboardButton(
                str(text), switch_inline_query_current_chat=str(query)
            )
        raise TypeError(f"Unsupported button spec: {item!r}")

    return _build_markup(rows, _button)


def switch_inline_query_chosen_chat_buttons(
    rows: Iterable[Sequence[Any]],
) -> InlineKeyboardMarkup:
    """Buttons that open inline mode with chat selection; items are (text, chosen_chat)."""

    def _button(item: Any) -> InlineKeyboardButton:
        if isinstance(item, dict):
            return InlineKeyboardButton(
                item["text"],
                switch_inline_query_chosen_chat=item["switch_inline_query_chosen_chat"],
            )
        if isinstance(item, (tuple, list)) and len(item) == 2:
            text, chosen_chat = item
            return InlineKeyboardButton(
                str(text), switch_inline_query_chosen_chat=chosen_chat
            )
        raise TypeError(f"Unsupported button spec: {item!r}")

    return _build_markup(rows, _button)


def game_buttons(rows: Iterable[Sequence[Any]]) -> InlineKeyboardMarkup:
    """Game buttons; items are (text, callback_game) or {'text': ..., 'callback_game': ...}."""

    def _button(item: Any) -> InlineKeyboardButton:
        if isinstance(item, dict):
            return InlineKeyboardButton(
                item["text"], callback_game=item["callback_game"]
            )
        if isinstance(item, (tuple, list)) and len(item) == 2:
            text, callback_game = item
            return InlineKeyboardButton(str(text), callback_game=callback_game)
        raise TypeError(f"Unsupported button spec: {item!r}")

    return _build_markup(rows, _button)


def pay_buttons(rows: Iterable[Sequence[Any]]) -> InlineKeyboardMarkup:
    """Pay buttons; each item is a text label."""

    def _button(item: Any) -> InlineKeyboardButton:
        if isinstance(item, str):
            return InlineKeyboardButton(item, pay=True)
        raise TypeError(f"Unsupported button spec: {item!r}")

    return _build_markup(rows, _button)
