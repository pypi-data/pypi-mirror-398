import os

from telegram.constants import ChatAction
from telegram import InputMediaDocument, LabeledPrice

from examples.weather_cookbook.shared import weather_service, sample_png
from telegram_dsl.framework import actions, outputs, buttons as buttons_lib
from telegram_dsl.framework.handlers import command_handler, buttons_handler


@command_handler(add_to_commands=True)
async def forecast(args, user):
    """Send a forecast image (as a document) with caption.

    Telegram's Bot API requires JPEG for sendPhoto; to keep the cookbook fully
    offline and deterministic, we send a generated PNG as a document instead.
    """
    city = (args or "").strip()
    if not city:
        return outputs.text("Missing city.\nExample: /forecast Rome")
    if not weather_service.is_supported_city(city):
        examples = ", ".join(c.title() for c in weather_service.SUPPORTED_CITIES)
        return outputs.text(f"Unknown city.\nExamples: {examples}")
    current = weather_service.get_current(city)
    if not current:
        return outputs.text("Weather service error.")
    caption = f"{city.title()}: {current['summary']} {current['temp_c']}C"
    return outputs.document(document=sample_png(), caption=caption)


@command_handler(add_to_commands=True)
async def location(args, user):
    """Send a sample location."""
    return outputs.location(latitude=41.9028, longitude=12.4964)


@command_handler(add_to_commands=True)
async def venue(args, user):
    """Send a sample venue."""
    return outputs.venue(
        latitude=41.9028,
        longitude=12.4964,
        title="Weather HQ",
        address="Main Street 1",
    )


@command_handler(add_to_commands=True)
async def contact(args, user):
    """Send a sample contact."""
    return outputs.contact(phone_number="+123456789", first_name="Weather Bot")


@command_handler(add_to_commands=True)
async def dice(args, user):
    """Send a dice animation."""
    return outputs.dice()


@command_handler(add_to_commands=True)
async def poll(args, user):
    """Send a poll."""
    return outputs.poll(question="Rain today?", options=["Yes", "No"])


@command_handler(add_to_commands=True)
async def media_group(args, user):
    """Send a media group."""
    media = [
        InputMediaDocument(sample_png()),
        InputMediaDocument(sample_png()),
    ]
    return outputs.media_group(media=media)


@command_handler(add_to_commands=True)
async def chat_action(args, user):
    """Send a chat action (typing)."""
    return outputs.group(
        [
            outputs.chat_action(action=ChatAction.TYPING),
            outputs.sleep(1.0),
            outputs.text("Typing indicator demo (sent after 1s)."),
        ]
    )


@command_handler(add_to_commands=True)
async def silent(args, user):
    """No response."""
    return outputs.none()


@command_handler(add_to_commands=True)
async def raw_call(args, user):
    """Call a raw bot method via outputs.call."""
    return outputs.call("send_message", text="Raw call works.")


@command_handler(add_to_commands=True)
async def bot_send(args, user):
    """Call a bot method via outputs.bot."""
    return outputs.bot.send_message(text="Bot proxy works.")


@command_handler(add_to_commands=True)
async def actions_multi(args, user):
    """Send multiple actions via actions.group."""
    return actions.group(
        actions.send_message(text="Action 1"),
        actions.send_message(text="Action 2"),
    )


@command_handler(add_to_commands=True)
async def outputs_multi(args, user):
    """Send multiple outputs via outputs.group."""
    return outputs.group([outputs.text("Output 1"), outputs.text("Output 2")])


@command_handler(add_to_commands=True)
async def actions_reply(args, user):
    """Reply using actions.reply_text."""
    return actions.reply_text(text="Reply from actions.reply_text.")


@command_handler(add_to_commands=True)
async def actions_call(args, user):
    """Call a raw bot method via actions.call."""
    return actions.call("send_message", text="actions.call works.")


@command_handler(add_to_commands=True)
async def actions_bot(args, user):
    """Call a bot method via actions.bot."""
    return actions.bot.send_message(text="actions.bot works.")


@command_handler(add_to_commands=True)
async def edit_demo(args, user):
    """Send a message that can be edited via buttons."""
    return outputs.buttons(
        "Edit this message:",
        buttons=[["Update text"], ["Clear buttons"]],
    )


@buttons_handler(pattern="^Update text$")
async def edit_text_callback(args, user, update):
    msg = update.callback_query.message
    return outputs.group(
        [
            outputs.answer_callback_query(
                callback_query_id=update.callback_query.id, text="Updated"
            ),
            outputs.edit_message_text(
                text="Text updated.",
                chat_id=msg.chat_id,
                message_id=msg.message_id,
            ),
        ]
    )


@buttons_handler(pattern="^Clear buttons$")
async def clear_buttons_callback(args, user, update):
    msg = update.callback_query.message
    return outputs.group(
        [
            outputs.answer_callback_query(
                callback_query_id=update.callback_query.id, text="Cleared"
            ),
            outputs.edit_message_reply_markup(
                chat_id=msg.chat_id,
                message_id=msg.message_id,
                reply_markup=None,
            ),
        ]
    )


@command_handler(add_to_commands=True)
async def edit_caption_demo(args, user):
    """Send a media message with buttons to edit its caption."""
    markup = buttons_lib.inline_buttons([["Update caption"]])
    return outputs.document(
        document=sample_png(),
        caption="Caption demo.",
        reply_markup=markup,
    )


@buttons_handler(pattern="^Update caption$")
async def edit_caption_callback(args, user, update):
    msg = update.callback_query.message
    return outputs.group(
        [
            outputs.answer_callback_query(
                callback_query_id=update.callback_query.id, text="Caption updated"
            ),
            outputs.edit_message_caption(
                caption="Caption updated.",
                chat_id=msg.chat_id,
                message_id=msg.message_id,
            ),
        ]
    )


@command_handler(add_to_commands=True)
async def invoice(args, user):
    """Send an invoice if PROVIDER_TOKEN is configured."""
    token = os.getenv("PROVIDER_TOKEN")
    if not token:
        return outputs.text("Set PROVIDER_TOKEN to test invoices.")
    prices = [LabeledPrice(label="Weather Pro", amount=100)]
    return outputs.invoice(
        title="Weather Pro",
        description="Unlock premium forecasts.",
        payload="weather-pro",
        provider_token=token,
        currency="EUR",
        prices=prices,
    )
