from telegram_dsl.framework import outputs
from telegram_dsl.framework.handlers import command_handler
from telegram_dsl.internal.middleware.hooks import (
    register_global_middleware,
    register_middleware,
)


@register_global_middleware
async def log_update(update, context, next):
    kind = update.__class__.__name__
    print(f"[MIDDLEWARE] Update: {kind}")
    return await next(update, context)


async def add_warning_prefix(update, context, next):
    result = await next(update, context)
    if isinstance(result, outputs.Response) and result.method == "send_message":
        text = result.kwargs.get("text", "")
        return outputs.text(f"⚠️ {text}")
    return result


@register_middleware(add_warning_prefix)
@command_handler(add_to_commands=True)
async def alert(args, user):
    """Send a weather alert with middleware prefix."""
    return outputs.text("Storm warning in your area.")
