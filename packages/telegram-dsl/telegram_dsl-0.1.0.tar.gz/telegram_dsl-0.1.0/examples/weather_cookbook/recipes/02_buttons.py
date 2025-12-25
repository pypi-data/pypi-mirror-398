import os

from telegram_dsl.framework.handlers import command_handler, buttons_handler
from telegram_dsl.framework import outputs


@command_handler(add_to_commands=True)
async def buttons(args, user):
    """Show callback buttons (label == callback data)."""
    return outputs.buttons("Choose a weather:", buttons=[["Sun"], ["Rain"]])


@buttons_handler(pattern="^Sun$")
async def on_sun(args, user):
    return outputs.text("Sun selected.")


@buttons_handler(pattern="^Rain$")
async def on_rain(args, user):
    return outputs.text("Rain selected.")


@command_handler(add_to_commands=True)
async def url_button(args, user):
    """Show URL buttons."""
    return outputs.url_buttons(
        "Open radar:",
        buttons=[[("Radar", "https://example.com")]],
    )


@command_handler(add_to_commands=True)
async def login_button(args, user):
    """Show login URL buttons."""
    return outputs.login_url_buttons(
        "Login:",
        buttons=[[("Login", {"url": "https://example.com"})]],
    )


@command_handler(add_to_commands=True)
async def web_app_button(args, user):
    """Show web app buttons."""
    return outputs.web_app_buttons(
        "Open app:",
        buttons=[[("Forecast App", {"url": "https://example.com"})]],
    )


@command_handler(add_to_commands=True)
async def switch_inline(args, user):
    """Show a switch inline query button."""
    query = (args or "").strip()
    if not query:
        return outputs.text("Missing query.\nExample: /switch_inline rome")
    return outputs.switch_inline_query_buttons(
        "Search elsewhere:",
        buttons=[[("Search", query)]],
    )


@command_handler(add_to_commands=True)
async def switch_inline_current(args, user):
    """Show a switch inline query button (current chat)."""
    query = (args or "").strip()
    if not query:
        return outputs.text("Missing query.\nExample: /switch_inline_current milan")
    return outputs.switch_inline_query_current_chat_buttons(
        "Search here:",
        buttons=[[("Search", query)]],
    )


@command_handler(add_to_commands=True)
async def switch_inline_chosen(args, user):
    """Show a switch inline query button (chosen chat)."""
    return outputs.switch_inline_query_chosen_chat_buttons(
        "Search in chat:",
        buttons=[[("Search", {"allow_user_chats": True})]],
    )


@command_handler(add_to_commands=True)
async def game_button(args, user):
    """Show a game button."""
    game_short_name = os.getenv("GAME_SHORT_NAME")
    if not game_short_name:
        return outputs.text(
            "Missing GAME_SHORT_NAME env.\nSet it in docker env to test this."
        )
    return outputs.game_buttons(
        "Play:",
        buttons=[[("Play", {"game_short_name": game_short_name})]],
    )


@command_handler(add_to_commands=True)
async def pay_button(args, user):
    """Show a pay button."""
    return outputs.pay_buttons(
        "Checkout:",
        buttons=[["Pay"]],
    )
