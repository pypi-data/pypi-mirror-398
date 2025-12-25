import re

from telegram.ext import (
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    InlineQueryHandler,
    ChosenInlineResultHandler,
    BusinessConnectionHandler,
    BusinessMessagesDeletedHandler,
    ChatBoostHandler,
    ChatJoinRequestHandler,
    ChatMemberHandler,
    MessageReactionHandler,
    PaidMediaPurchasedHandler,
    PollAnswerHandler,
    PollHandler,
    PreCheckoutQueryHandler,
    ShippingQueryHandler,
    PrefixHandler,
    TypeHandler,
    filters,
)
from telegram_dsl.framework.decorators import register_handler
from telegram_dsl.diagnostics.map_view import dump_state_handlers
from telegram_dsl.internal.handlers.fallback import get_fallback
from telegram_dsl.internal.handlers.states import (
    get_conversation_entry_points,
    get_conversation_states,
)
from telegram_dsl.internal.handlers.validation import validate_conversation


def text_handler(**kwargs):
    return register_handler(
        MessageHandler,
        filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^/"),
        **kwargs,
    )


def photo_handler(**kwargs):
    return register_handler(MessageHandler, filters.PHOTO, **kwargs)


def video_handler(**kwargs):
    return register_handler(MessageHandler, filters.VIDEO, **kwargs)


def audio_handler(**kwargs):
    return register_handler(MessageHandler, filters.AUDIO, **kwargs)


def voice_handler(**kwargs):
    return register_handler(MessageHandler, filters.VOICE, **kwargs)


def video_note_handler(**kwargs):
    return register_handler(MessageHandler, filters.VIDEO_NOTE, **kwargs)


def document_handler(**kwargs):
    return register_handler(MessageHandler, filters.Document.ALL, **kwargs)


def location_handler(**kwargs):
    return register_handler(MessageHandler, filters.LOCATION, **kwargs)


def any_command(**kwargs):
    return register_handler(MessageHandler, filters.COMMAND, **kwargs)


def customfilter_text_handler(filter_obj, **kwargs):
    """Handle text messages with a custom PTB filter expression."""
    return register_handler(MessageHandler, filter_obj, **kwargs)


def sticker_handler(**kwargs):
    return register_handler(MessageHandler, filters.Sticker.ALL, **kwargs)


def animation_handler(**kwargs):
    return register_handler(MessageHandler, filters.ANIMATION, **kwargs)


class _UnknownCommandFilter(filters.BaseFilter):
    def check_update(self, update) -> bool:
        message = getattr(update, "effective_message", None) or getattr(
            update, "message", None
        )
        text = getattr(message, "text", None) if message else None
        if not text or not text.startswith("/"):
            return False

        command_token = text[1:].split(None, 1)[0] if len(text) > 1 else ""
        command_name = command_token.split("@", 1)[0].strip().lower()
        if not command_name:
            return True

        from telegram_dsl.internal.handlers.map import get_all_metadata

        known = {
            (meta.get("name") or "").strip().lower()
            for meta in get_all_metadata()
            if meta.get("handler_cls") == "CommandHandler" and meta.get("name")
        }
        return command_name not in known


def unknown_command_handler(**kwargs):
    """Handle unknown "/commands".

    Implemented as a MessageHandler filter that matches command-like text ("/..."),
    and dynamically excludes any command registered via @command_handler.
    """
    return register_handler(MessageHandler, _UnknownCommandFilter(), **kwargs)


def command_handler(**kwargs):
    def wrapper(func):
        return register_handler(CommandHandler, func.__name__, **kwargs)(func)

    return wrapper


def buttons_handler(*, auto_hide_buttons: bool = True, **kwargs):
    """Handle inline button presses (Telegram callback queries).

    By default, the inline keyboard is removed after a click (auto_hide_buttons=True).
    """
    return register_handler(
        CallbackQueryHandler, auto_hide_buttons=auto_hide_buttons, **kwargs
    )


def callback_handler(*, auto_hide_buttons: bool = True, **kwargs):
    """Deprecated alias for buttons_handler()."""
    return buttons_handler(auto_hide_buttons=auto_hide_buttons, **kwargs)


def conversation_handler(*, group, **kwargs):
    def wrapper(func):
        fallback = get_fallback(group)
        kwargs.setdefault("per_chat", True)
        kwargs.setdefault("per_user", True)

        entry_points = get_conversation_entry_points(group)
        states = get_conversation_states(group)
        fallbacks = [fallback] if fallback else []

        all_handlers = [
            *entry_points,
            *[h for hs in states.values() for h in hs],
            *fallbacks,
        ]
        has_callback = any(
            h.__class__.__name__ == "CallbackQueryHandler" for h in all_handlers
        )
        all_callback = bool(all_handlers) and all(
            h.__class__.__name__ == "CallbackQueryHandler" for h in all_handlers
        )
        if "per_message" not in kwargs:
            kwargs["per_message"] = all_callback
        kwargs_with_states = {
            "group": group,
            "entry_points": entry_points,
            "states": states,
            "fallbacks": fallbacks,
            **kwargs,
        }

        validate_conversation(
            group, kwargs_with_states["entry_points"], kwargs_with_states["states"]
        )
        dump_state_handlers(kwargs_with_states.get("states", {}))

        # For mixed conversations (message handlers + callback handlers), PTB requires
        # per_message=False. We'll enforce that to avoid misconfiguration.
        if has_callback and not all_callback:
            kwargs_with_states["per_message"] = False
        return register_handler(ConversationHandler, **kwargs_with_states)(func)

    return wrapper


def inline_query_handler(**kwargs):
    return register_handler(InlineQueryHandler, **kwargs)


def chosen_inline_result_handler(**kwargs):
    return register_handler(ChosenInlineResultHandler, **kwargs)


def edited_message_handler(**kwargs):
    return register_handler(MessageHandler, filters.UpdateType.EDITED_MESSAGE, **kwargs)


def channel_post_handler(**kwargs):
    return register_handler(MessageHandler, filters.UpdateType.CHANNEL_POST, **kwargs)


def edited_channel_post_handler(**kwargs):
    return register_handler(
        MessageHandler, filters.UpdateType.EDITED_CHANNEL_POST, **kwargs
    )


def business_message_handler(**kwargs):
    return register_handler(
        MessageHandler, filters.UpdateType.BUSINESS_MESSAGE, **kwargs
    )


def edited_business_message_handler(**kwargs):
    return register_handler(
        MessageHandler, filters.UpdateType.EDITED_BUSINESS_MESSAGE, **kwargs
    )


def business_connection_handler(**kwargs):
    return register_handler(BusinessConnectionHandler, **kwargs)


def business_messages_deleted_handler(**kwargs):
    return register_handler(BusinessMessagesDeletedHandler, **kwargs)


def chat_boost_handler(**kwargs):
    return register_handler(ChatBoostHandler, **kwargs)


def chat_join_request_handler(**kwargs):
    return register_handler(ChatJoinRequestHandler, **kwargs)


def my_chat_member_handler(**kwargs):
    return register_handler(
        ChatMemberHandler, ChatMemberHandler.MY_CHAT_MEMBER, **kwargs
    )


def chat_member_handler(**kwargs):
    return register_handler(ChatMemberHandler, ChatMemberHandler.CHAT_MEMBER, **kwargs)


def any_chat_member_handler(**kwargs):
    return register_handler(
        ChatMemberHandler, ChatMemberHandler.ANY_CHAT_MEMBER, **kwargs
    )


def message_reaction_handler(**kwargs):
    return register_handler(MessageReactionHandler, **kwargs)


def message_reaction_updated_handler(**kwargs):
    return register_handler(
        MessageReactionHandler,
        message_reaction_types=MessageReactionHandler.MESSAGE_REACTION_UPDATED,
        **kwargs,
    )


def message_reaction_count_handler(**kwargs):
    return register_handler(
        MessageReactionHandler,
        message_reaction_types=MessageReactionHandler.MESSAGE_REACTION_COUNT_UPDATED,
        **kwargs,
    )


def paid_media_purchased_handler(**kwargs):
    return register_handler(PaidMediaPurchasedHandler, **kwargs)


def poll_handler(**kwargs):
    return register_handler(PollHandler, **kwargs)


def poll_answer_handler(**kwargs):
    return register_handler(PollAnswerHandler, **kwargs)


def shipping_query_handler(**kwargs):
    return register_handler(ShippingQueryHandler, **kwargs)


def pre_checkout_query_handler(**kwargs):
    return register_handler(PreCheckoutQueryHandler, **kwargs)


def prefix_handler(prefix, command, **kwargs):
    return register_handler(PrefixHandler, prefix, command, **kwargs)


def string_command_handler(commands, **kwargs):
    if isinstance(commands, str):
        commands = [commands]
    commands = [c for c in (commands or []) if isinstance(c, str) and c.strip()]
    if not commands:
        raise ValueError(
            "string_command_handler(commands=...) expects a non-empty list of strings."
        )
    pattern = r"^\s*(?:%s)\s*$" % "|".join(re.escape(c.strip()) for c in commands)
    return register_handler(
        MessageHandler,
        filters.TEXT
        & ~filters.COMMAND
        & ~filters.Regex(r"^/")
        & filters.Regex(re.compile(pattern)),
        **kwargs,
    )


def string_regex_handler(pattern, **kwargs):
    if not isinstance(pattern, str) or not pattern.strip():
        raise ValueError(
            "string_regex_handler(pattern=...) expects a non-empty regex string."
        )
    compiled = re.compile(pattern)
    return register_handler(
        MessageHandler,
        filters.TEXT
        & ~filters.COMMAND
        & ~filters.Regex(r"^/")
        & filters.Regex(compiled),
        **kwargs,
    )


def type_handler(update_type, **kwargs):
    return register_handler(TypeHandler, update_type, **kwargs)
