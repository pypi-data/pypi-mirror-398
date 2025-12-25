import asyncio

from telegram_dsl.internal.responses.send import register_responder
from telegram_dsl.internal.constants import RESPONSE_TYPE
from telegram_dsl.framework.actions import Action, ActionGroup


@register_responder(match=lambda r: r == RESPONSE_TYPE.TEXT)
async def text_responder(update, context, content):
    message = update.effective_message
    if isinstance(content, dict):
        await message.reply_text(**content)
        return
    await message.reply_text(content)


@register_responder(match=lambda r: r == RESPONSE_TYPE.PHOTO)
async def photo_responder(update, context, content):
    await update.effective_message.reply_photo(photo=content)


@register_responder(match=lambda r: r == RESPONSE_TYPE.DOCUMENT)
async def doc_responder(update, context, content):
    await update.effective_message.reply_document(document=content)


@register_responder(match=lambda r: r == RESPONSE_TYPE.NONE)
async def noop_responder(update, context, content):
    return None


@register_responder(match=lambda r: r == RESPONSE_TYPE.ACTION)
async def action_responder(update, context, content):
    actions = content.actions if isinstance(content, ActionGroup) else (content,)
    for action in actions:
        if not isinstance(action, Action):
            message = getattr(update, "effective_message", None)
            if message:
                await message.reply_text(f"[Unsupported action] {str(action)}")
            continue
        await _dispatch_action(update, context, action)


@register_responder(match=lambda _: True)
async def fallback_responder(update, context, content):
    await update.effective_message.reply_text(f"[Unsupported type] {str(content)}")


async def _dispatch_action(update, context, action: Action):
    method = action.method
    if method == "noop":
        return None
    if method == "sleep":
        seconds = float(action.kwargs.get("seconds", 0) or 0)
        if seconds > 0:
            await asyncio.sleep(seconds)
        return None
    message = getattr(update, "effective_message", None)
    kwargs = dict(action.kwargs)

    reply_method = {
        "send_message": "reply_text",
        "send_photo": "reply_photo",
        "send_document": "reply_document",
        "send_video": "reply_video",
        "send_audio": "reply_audio",
        "send_voice": "reply_voice",
        "send_animation": "reply_animation",
        "send_sticker": "reply_sticker",
        "send_video_note": "reply_video_note",
        "send_location": "reply_location",
        "send_venue": "reply_venue",
        "send_contact": "reply_contact",
        "send_poll": "reply_poll",
        "send_dice": "reply_dice",
        "send_media_group": "reply_media_group",
        "edit_message_text": "edit_text",
        "edit_message_caption": "edit_caption",
    }.get(method)

    if message and reply_method and hasattr(message, reply_method):
        # Message methods don't accept routing parameters that bot methods do.
        kwargs.pop("chat_id", None)
        kwargs.pop("message_id", None)
        kwargs.pop("inline_message_id", None)
        await getattr(message, reply_method)(**kwargs)
        return

    no_chat_id_methods = {"answer_callback_query", "answer_inline_query"}
    message_method = message and hasattr(message, method)
    if (
        not message_method
        and method not in no_chat_id_methods
        and "chat_id" not in kwargs
    ):
        chat = getattr(update, "effective_chat", None)
        if chat:
            kwargs["chat_id"] = chat.id
    if (
        not message_method
        and method not in no_chat_id_methods
        and "chat_id" not in kwargs
    ):
        raise ValueError(
            f"Cannot call bot method '{method}' without chat_id (no effective_chat found). "
            f"Provide chat_id explicitly in outputs.{method}(..., chat_id=...)."
        )
    if message_method:
        await getattr(message, method)(**kwargs)
        return
    await getattr(context.bot, method)(**kwargs)
