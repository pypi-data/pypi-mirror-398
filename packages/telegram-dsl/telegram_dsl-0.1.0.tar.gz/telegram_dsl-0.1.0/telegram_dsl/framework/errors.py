from telegram_dsl.internal.errors import register_error_handler


@register_error_handler
async def default_error_handler(update, context):
    message = getattr(update, "effective_message", None)
    if message:
        await message.reply_text("Something went wrong.")
