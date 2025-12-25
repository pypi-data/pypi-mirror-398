from examples.weather_cookbook.shared import weather_service
from telegram_dsl.flow.states import register_entry_point, register_state
from telegram_dsl.framework.handlers import (
    command_handler,
    conversation_handler,
    text_handler,
    buttons_handler,
    location_handler,
)
from telegram_dsl.framework import outputs
from telegram_dsl.internal.handlers.fallback import register_fallback

GROUP = "ONBOARD"


@command_handler(add_to_commands=True)
@register_entry_point(group=GROUP)
async def onboard(args, user):
    """Start onboarding and ask for city."""
    return outputs.conversation(
        outputs.text("Send a city name (e.g. Rome) or share your location."),
        1,
    )


@text_handler(group=GROUP)
@register_state(group=GROUP, state_id=1)
async def ask_city(args, user, payload):
    """Accept a city name and then ask for units."""
    city = (args or "").strip()
    if not city:
        return outputs.conversation(outputs.text("Missing city.\nExample: Rome"), 1)
    if not weather_service.is_supported_city(city):
        examples = ", ".join(c.title() for c in weather_service.SUPPORTED_CITIES)
        return outputs.conversation(
            outputs.text(f"Unknown city.\nExamples: {examples}"), 1
        )
    if payload.context and hasattr(payload.context, "user_data"):
        payload.context.user_data[f"{GROUP}.city"] = city.title()
        payload.context.user_data.pop(f"{GROUP}.coords", None)
    return outputs.conversation(
        outputs.buttons(
            "Choose units:",
            buttons=[["Celsius"], ["Fahrenheit"]],
        ),
        2,
    )


@location_handler(group=GROUP)
@register_state(group=GROUP, state_id=1)
async def ask_location(args, user, payload):
    """Accept a Telegram location instead of a city name."""
    loc = payload.location
    if not loc:
        return outputs.conversation(outputs.text("No location found. Try again."), 1)
    if payload.context and hasattr(payload.context, "user_data"):
        payload.context.user_data[f"{GROUP}.coords"] = (loc.latitude, loc.longitude)
        payload.context.user_data.pop(f"{GROUP}.city", None)
    return outputs.conversation(
        outputs.buttons(
            "Choose units:",
            buttons=[["Celsius"], ["Fahrenheit"]],
        ),
        2,
    )


@buttons_handler(pattern="^(Celsius|Fahrenheit)$", group=GROUP)
@register_state(group=GROUP, state_id=2)
async def choose_units(args, user, payload):
    """Accept units from inline buttons and finish onboarding."""
    units = "C" if (payload.callback_data or "").strip() == "Celsius" else "F"
    city = None
    coords = None
    if payload.context and hasattr(payload.context, "user_data"):
        city = payload.context.user_data.get(f"{GROUP}.city")
        coords = payload.context.user_data.get(f"{GROUP}.coords")

    if city:
        label = city
    elif coords:
        lat, lon = coords
        label = f"your location ({lat:.3f}, {lon:.3f})"
    else:
        return outputs.conversation(
            outputs.text("Missing data.\nRestart with /onboard"), -1
        )

    return outputs.conversation(outputs.text(f"Saved: {label}, units={units}."), -1)


@conversation_handler(group=GROUP)
async def onboarding_flow(args, user):
    pass


@register_fallback(group=GROUP)
async def onboarding_fallback(args, user):
    return outputs.text("Please send text or a photo to continue.")
