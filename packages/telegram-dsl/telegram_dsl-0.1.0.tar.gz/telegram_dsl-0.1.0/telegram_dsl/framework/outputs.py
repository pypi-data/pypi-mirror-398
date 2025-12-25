from dataclasses import dataclass, field
from typing import Any, Dict, Iterable

from telegram import InlineKeyboardMarkup

from telegram_dsl.framework.actions import Action, ActionGroup
from telegram_dsl.framework import buttons as buttons_lib
from telegram_dsl.internal.telegram_methods import BOT_METHODS


REQUIRED_FIELDS = {
    "send_message": ("text",),
    "send_photo": ("photo",),
    "send_document": ("document",),
    "send_video": ("video",),
    "send_audio": ("audio",),
    "send_voice": ("voice",),
    "send_animation": ("animation",),
    "send_sticker": ("sticker",),
    "send_video_note": ("video_note",),
    "send_location": ("latitude", "longitude"),
    "send_venue": ("latitude", "longitude", "title", "address"),
    "send_contact": ("phone_number", "first_name"),
    "send_poll": ("question", "options"),
    "send_media_group": ("media",),
    "edit_message_text": ("text",),
    "edit_message_caption": ("caption",),
    "sleep": ("seconds",),
}


@dataclass(frozen=True)
class Response:
    method: str
    kwargs: Dict[str, Any] = field(default_factory=dict)

    def action_kwargs(self):
        return dict(self.kwargs)

    def __post_init__(self):
        required = REQUIRED_FIELDS.get(self.method, ())
        missing = [key for key in required if key not in self.kwargs]
        if missing:
            raise ValueError(f"Missing required fields for {self.method}: {missing}")


@dataclass(frozen=True)
class ConversationResult:
    message: Any
    next_state: int


def text(value: str, **kwargs) -> Response:
    if "keyboard" in kwargs and "reply_markup" not in kwargs:
        kwargs["reply_markup"] = kwargs.pop("keyboard")
    return Response("send_message", {"text": value, **kwargs})


def long_text(value: str, *, chunk_size: int = 3800, **kwargs) -> ActionGroup:
    """Send text split across multiple messages to avoid Telegram's length limit."""
    parts = _split_text(value, chunk_size=chunk_size)
    return group(text(part, **kwargs) for part in parts)


def _split_text(value: str, *, chunk_size: int) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    text_value = value or ""
    if len(text_value) <= chunk_size:
        return [text_value]

    parts: list[str] = []
    remaining = text_value
    while remaining:
        if len(remaining) <= chunk_size:
            parts.append(remaining)
            break

        window = remaining[:chunk_size]
        cut = window.rfind("\n")
        if cut <= 0:
            cut = chunk_size
        parts.append(remaining[:cut].rstrip("\n"))
        remaining = remaining[cut:].lstrip("\n")

    return [p for p in parts if p != ""]


def conversation(message: Any, next_state: int) -> ConversationResult:
    """Conversation step; message should be outputs.text(...) or another output."""
    return ConversationResult(message=message, next_state=next_state)


def buttons(message: str, *, buttons, **kwargs) -> Response:
    """Send a message with inline callback buttons (label == callback data)."""
    if isinstance(buttons, InlineKeyboardMarkup):
        return text(message, keyboard=buttons, **kwargs)
    return text(message, keyboard=buttons_lib.inline_buttons(buttons), **kwargs)


def url_buttons(message: str, *, buttons, **kwargs) -> Response:
    """Send a message with URL buttons that open a browser."""
    if isinstance(buttons, InlineKeyboardMarkup):
        return text(message, keyboard=buttons, **kwargs)
    return text(message, keyboard=buttons_lib.url_buttons(buttons), **kwargs)


def login_url_buttons(message: str, *, buttons, **kwargs) -> Response:
    """Send a message with login URL buttons for Telegram login flow."""
    if isinstance(buttons, InlineKeyboardMarkup):
        return text(message, keyboard=buttons, **kwargs)
    return text(message, keyboard=buttons_lib.login_url_buttons(buttons), **kwargs)


def web_app_buttons(message: str, *, buttons, **kwargs) -> Response:
    """Send a message with web app buttons that open a Telegram Web App."""
    if isinstance(buttons, InlineKeyboardMarkup):
        return text(message, keyboard=buttons, **kwargs)
    return text(message, keyboard=buttons_lib.web_app_buttons(buttons), **kwargs)


def switch_inline_query_buttons(message: str, *, buttons, **kwargs) -> Response:
    """Send a message with buttons that open inline mode in another chat."""
    if isinstance(buttons, InlineKeyboardMarkup):
        return text(message, keyboard=buttons, **kwargs)
    return text(
        message, keyboard=buttons_lib.switch_inline_query_buttons(buttons), **kwargs
    )


def switch_inline_query_current_chat_buttons(
    message: str, *, buttons, **kwargs
) -> Response:
    """Send a message with buttons that open inline mode in the current chat."""
    if isinstance(buttons, InlineKeyboardMarkup):
        return text(message, keyboard=buttons, **kwargs)
    return text(
        message,
        keyboard=buttons_lib.switch_inline_query_current_chat_buttons(buttons),
        **kwargs,
    )


def switch_inline_query_chosen_chat_buttons(
    message: str, *, buttons, **kwargs
) -> Response:
    """Send a message with buttons that open inline mode with chat selection."""
    if isinstance(buttons, InlineKeyboardMarkup):
        return text(message, keyboard=buttons, **kwargs)
    return text(
        message,
        keyboard=buttons_lib.switch_inline_query_chosen_chat_buttons(buttons),
        **kwargs,
    )


def game_buttons(message: str, *, buttons, **kwargs) -> Response:
    """Send a message with game buttons that launch a Telegram game."""
    if isinstance(buttons, InlineKeyboardMarkup):
        return text(message, keyboard=buttons, **kwargs)
    return text(message, keyboard=buttons_lib.game_buttons(buttons), **kwargs)


def pay_buttons(message: str, *, buttons, **kwargs) -> Response:
    """Send a message with pay buttons for invoice checkout."""
    if isinstance(buttons, InlineKeyboardMarkup):
        return text(message, keyboard=buttons, **kwargs)
    return text(message, keyboard=buttons_lib.pay_buttons(buttons), **kwargs)


def photo(photo, **kwargs) -> Response:
    return Response("send_photo", {"photo": photo, **kwargs})


def document(document, **kwargs) -> Response:
    return Response("send_document", {"document": document, **kwargs})


def video(video, **kwargs) -> Response:
    return Response("send_video", {"video": video, **kwargs})


def audio(audio, **kwargs) -> Response:
    return Response("send_audio", {"audio": audio, **kwargs})


def voice(voice, **kwargs) -> Response:
    return Response("send_voice", {"voice": voice, **kwargs})


def animation(animation, **kwargs) -> Response:
    return Response("send_animation", {"animation": animation, **kwargs})


def sticker(sticker, **kwargs) -> Response:
    return Response("send_sticker", {"sticker": sticker, **kwargs})


def video_note(video_note, **kwargs) -> Response:
    return Response("send_video_note", {"video_note": video_note, **kwargs})


def location(latitude, longitude, **kwargs) -> Response:
    return Response(
        "send_location", {"latitude": latitude, "longitude": longitude, **kwargs}
    )


def venue(latitude, longitude, title, address, **kwargs) -> Response:
    return Response(
        "send_venue",
        {
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "address": address,
            **kwargs,
        },
    )


def contact(phone_number, first_name, **kwargs) -> Response:
    return Response(
        "send_contact",
        {"phone_number": phone_number, "first_name": first_name, **kwargs},
    )


def dice(**kwargs) -> Response:
    return Response("send_dice", {**kwargs})


def poll(question, options, **kwargs) -> Response:
    return Response("send_poll", {"question": question, "options": options, **kwargs})


def invoice(**kwargs) -> Response:
    return Response("send_invoice", {**kwargs})


def media_group(media, **kwargs) -> Response:
    return Response("send_media_group", {"media": media, **kwargs})


def chat_action(action, **kwargs) -> Response:
    return Response("send_chat_action", {"action": action, **kwargs})


def sleep(seconds: float) -> Response:
    """Delay within an outputs.group(...) sequence (no Telegram API call)."""
    return Response("sleep", {"seconds": seconds})


def edit_message_text(text, **kwargs) -> Response:
    return Response("edit_message_text", {"text": text, **kwargs})


def edit_message_caption(caption, **kwargs) -> Response:
    return Response("edit_message_caption", {"caption": caption, **kwargs})


def edit_message_reply_markup(**kwargs) -> Response:
    return Response("edit_message_reply_markup", {**kwargs})


def answer_callback_query(**kwargs) -> Response:
    return Response("answer_callback_query", {**kwargs})


def answer_inline_query(**kwargs) -> Response:
    return Response("answer_inline_query", {**kwargs})


def none() -> Response:
    return Response("noop", {})


def call(method: str, **kwargs) -> Response:
    return Response(method, kwargs)


class BotOutputs:
    def __getattr__(self, name: str):
        def _method(**kwargs):
            return Response(name, kwargs)

        return _method


bot = BotOutputs()


def group(items: Iterable[Any]) -> ActionGroup:
    actions = []
    for item in items:
        if isinstance(item, Action):
            actions.append(item)
        elif isinstance(item, Response):
            actions.append(Action(item.method, item.action_kwargs()))
        else:
            raise TypeError(f"Unsupported item for group: {type(item)}")
    return ActionGroup.of(actions)


def _make_output_func(name: str):
    def _func(**kwargs):
        return Response(name, kwargs)

    _func.__name__ = name
    return _func


for _name in BOT_METHODS:
    if _name not in globals():
        globals()[_name] = _make_output_func(_name)


__all__ = [
    "Response",
    "text",
    "photo",
    "document",
    "video",
    "audio",
    "voice",
    "animation",
    "sticker",
    "video_note",
    "location",
    "venue",
    "contact",
    "dice",
    "poll",
    "invoice",
    "media_group",
    "chat_action",
    "edit_message_text",
    "edit_message_caption",
    "edit_message_reply_markup",
    "answer_callback_query",
    "answer_inline_query",
    "none",
    "call",
    "bot",
    "group",
    *BOT_METHODS,
]
