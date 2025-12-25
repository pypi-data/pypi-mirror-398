from telegram_dsl.framework.handlers import command_handler
from telegram_dsl.internal.errors import register_error_handler


@register_error_handler
async def on_error(update, context):
    err = getattr(context, "error", None)
    if err:
        print(f"[ERROR] {type(err).__name__}: {err}")
    else:
        print("[ERROR] Unknown error.")
    message = getattr(update, "effective_message", None)
    if message:
        await message.reply_text("Weather bot error occurred.")


@command_handler(add_to_commands=True)
async def boom(args, user):
    """Trigger an exception to test error handling."""
    raise RuntimeError("boom")
