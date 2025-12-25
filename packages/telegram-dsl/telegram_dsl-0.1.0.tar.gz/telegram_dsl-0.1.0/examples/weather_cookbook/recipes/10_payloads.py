from telegram_dsl.framework.handlers import command_handler
from telegram_dsl.framework import outputs


@command_handler(add_to_commands=True)
async def payload(args, user, payload):
    """Show common payload accessors."""
    parts = [
        f"chat_id={payload.chat_id}",
        f"chat_type={payload.chat_type}",
        f"user_id={payload.user_id}",
        f"username={payload.user_username}",
        f"command={payload.command}",
        f"args={payload.command_args}",
        f"urls={payload.urls}",
        f"hashtags={payload.hashtags}",
    ]
    return outputs.text("\n".join(parts))
