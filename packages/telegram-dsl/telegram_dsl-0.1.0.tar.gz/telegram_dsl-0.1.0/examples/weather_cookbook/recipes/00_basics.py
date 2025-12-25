from telegram_dsl.framework.handlers import (
    command_handler,
    prefix_handler,
    string_command_handler,
    string_regex_handler,
    unknown_command_handler,
)
from telegram_dsl.framework import outputs
from examples.weather_cookbook.shared import weather_service


@command_handler(add_to_commands=True)
async def start(args, user):
    """Welcome message and quick hints."""
    return outputs.text("Welcome to the Weather Cookbook. Try /help.")


@command_handler(add_to_commands=True)
async def help(args, user):
    """List common demo commands."""
    return outputs.text(
        "Try /forecast, /buttons, /onboard, /payload, /commands, /handlers."
    )


@command_handler(add_to_commands=True)
async def ping(args, user):
    """Simple reply to confirm the bot is alive."""
    return outputs.text("Weather bot is online.")


@command_handler(add_to_commands=True)
async def weather(args, user):
    """Weather command example."""
    city = (args or "").strip()
    if not city:
        return outputs.text("Missing city.\nExample: /weather Rome")
    if not weather_service.is_supported_city(city):
        examples = ", ".join(c.title() for c in weather_service.SUPPORTED_CITIES)
        return outputs.text(f"Unknown city.\nExamples: {examples}")
    return outputs.text(f"Command forecast for {city}.")


@command_handler(add_to_commands=True)
async def temp(args, user):
    """Temperature command example."""
    city = (args or "").strip()
    if not city:
        return outputs.text("Missing city.\nExample: /temp Rome")
    if not weather_service.is_supported_city(city):
        examples = ", ".join(c.title() for c in weather_service.SUPPORTED_CITIES)
        return outputs.text(f"Unknown city.\nExamples: {examples}")
    return outputs.text(f"Command temperature for {city}.")


@unknown_command_handler()
async def unknown_command(args, user, payload):
    return outputs.text(f"Unknown command: {payload.command}")


@prefix_handler("!", "forecast")
async def prefix_forecast(args, user):
    city = (args or "").strip()
    if not city:
        return outputs.text("Missing city.\nExample: !forecast Zurich")
    if not weather_service.is_supported_city(city):
        examples = ", ".join(c.title() for c in weather_service.SUPPORTED_CITIES)
        return outputs.text(f"Unknown city.\nExamples: {examples}")
    return outputs.text(f"Prefix forecast requested: {city}")


@string_command_handler(["weather"])
async def string_match(args, user):
    return outputs.text("String match: sending quick forecast.")


@string_regex_handler(r"^temp\s+\w+$")
async def regex_match(args, user):
    return outputs.text(f"Regex match: {args}")
